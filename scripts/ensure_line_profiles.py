#!/usr/bin/env python3
"""LINE 摘要推薦股「公司簡介」機械式插入（不依賴模型抄寫）

背景：LINE 盤前摘要每檔推薦只有分數與法人數據，使用者沒空查公司背景，無法判斷能不能買。
簡介來源：data/company_profiles.json（新推薦股須先查證寫入，禁止編造）。

行為：
    - 掃描 LINE 檔中以 1️⃣2️⃣… 開頭的推薦行，其下插入 🏢簡介、📈基本面（revenue_check／eps_check）、⚖️賺賠比（tracking 的進場／目標／停損）、📊系統歷史勝率（data/tracking 已結算推薦）
    - 已有簡介（下一行以 🏢 開頭）→ 不動
    - 找不到簡介的代號 → 列出並 exit 2（此時應先查證該公司並寫入 company_profiles.json，不得硬補）
    - --dry-run 只印結果不寫檔

用法：
    python3 scripts/ensure_line_profiles.py --date 2026-10-16
    python3 scripts/ensure_line_profiles.py --date 2026-10-16 --file before_market_line.txt --dry-run
"""
import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

MAX_LINE_CHARS = 5000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC_RE = re.compile(r'^\s*[0-9]️?⃣\s*(\d{4,6})\b')


def _load_list(date, name):
    path = os.path.join(ROOT, 'data', date, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    items = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
    return {str(x.get('code') or x.get('stock_code')): x for x in items if isinstance(x, dict)}


def _load_recs(date):
    path = os.path.join(ROOT, 'data', 'tracking', f'tracking_{date}.json')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    return {str(r.get('stock_code')): r for r in d.get('recommendations', [])}


def fundamentals_line(rev, eps):
    """📈 基本面一行：100% 取自 revenue_check.json／eps_check.json，缺資料的欄位略過。"""
    parts = []
    if rev and rev.get('yoy') is not None:
        m = str(rev.get('month', ''))[-2:].lstrip('0')
        s = f"{m}月營收年增{rev['yoy']:+.1f}%" if m else f"營收年增{rev['yoy']:+.1f}%"
        if rev.get('growth_streak', 0) >= 2:
            s += f"（連{rev['growth_streak']}月成長）"
        elif rev.get('decline_streak', 0) >= 2:
            s += f"（連{rev['decline_streak']}月衰退）"
        parts.append(s)
    if eps and eps.get('eps') is not None:
        q = str(eps.get('latest_quarter', ''))
        qn = {'03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4'}.get(q[5:7], '最新季')
        s = f"{qn} EPS {eps['eps']}元"
        if eps.get('eps_yoy_pct') is not None:
            s += f"（年增{eps['eps_yoy_pct']:+.0f}%）"
        if eps.get('gross_margin_pct') is not None:
            s += f"、毛利率{eps['gross_margin_pct']:.1f}%"
            if eps.get('gm_qoq_delta') is not None:
                s += f"（較上季{eps['gm_qoq_delta']:+.1f}pp）"
        parts.append(s)
    return '   📈 ' + '｜'.join(parts) if parts else None


def load_track_history():
    """已結算推薦（success/fail）：[(推薦日, 分數, 是否成功)]，同 (代號,推薦日) 去重。"""
    import glob
    seen = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'tracking', 'tracking_2*.json'))):
        try:
            with open(f, encoding='utf-8') as fh:
                d = json.load(fh)
        except Exception:
            continue
        for r in d.get('recommendations', []):
            k = (r.get('stock_code'), r.get('recommend_date') or d.get('date'))
            if k not in seen or r.get('result') in ('success', 'fail'):
                seen[k] = (k[1], r.get('score'), r.get('result'))
    return [(d, sc, res == 'success') for d, sc, res in seen.values() if res in ('success', 'fail')]


def history_line(hist, score, today):
    if len(hist) < 30:
        return None

    def rate(g):
        return sum(1 for x in g if x[2]) / len(g) * 100 if g else None

    parts = [f"已結算{len(hist)}筆勝率{rate(hist):.0f}%"]
    cutoff = f"{today[:4]}-{int(today[5:7]) - 2:02d}-01" if int(today[5:7]) > 2 else None
    recent = [x for x in hist if cutoff and x[0] >= cutoff]
    if len(recent) >= 20:
        parts.append(f"近2個月{rate(recent):.0f}%（{len(recent)}筆）")
    if score is not None:
        lo = int(score // 10 * 10)
        band = [x for x in hist if x[1] is not None and lo <= x[1] < lo + 10]
        if len(band) >= 20:
            parts.append(f"同{lo}分段{rate(band):.0f}%（{len(band)}筆）")
    return '   📊 系統歷史：' + '｜'.join(parts) + '（勝＝10日內達目標或第10日收盤高於進場價）'


def reward_risk_line(rec):
    try:
        entry, target, stop = float(rec['recommend_price']), float(rec['target_price']), float(rec['stop_loss'])
    except (KeyError, TypeError, ValueError):
        return None
    up, down = (target / entry - 1) * 100, (1 - stop / entry) * 100
    chase = (target / (entry * 1.03) - 1) * 100
    return (f"   ⚖️ 達標賺+{up:.1f}%／停損賠-{down:.1f}%（賺賠比{up / down:.1f}:1）；"
            f"若開盤高3%才買，達標只剩+{chase:.1f}%")


def insert_profiles(lines, profiles, revs=None, epss=None, recs=None, hist=None, today=''):
    revs, epss, recs = revs or {}, epss or {}, recs or {}
    out, missing = [], []
    for i, line in enumerate(lines):
        out.append(line)
        m = REC_RE.match(line)
        if not m:
            continue
        code = m.group(1)
        following = ''.join(lines[i + 1:i + 7])
        p = profiles.get(code)
        rec = recs.get(code, {})
        extras = []
        if '🏢' not in following:
            if p and p.get('business'):
                extras.append(f"   🏢 {p['business']}")
            else:
                missing.append(code)
        if '📈' not in following:
            extras.append(fundamentals_line(revs.get(code), epss.get(code)))
        if '⚖️' not in following:
            extras.append(reward_risk_line(rec) if rec else None)
        if '📊' not in following:
            extras.append(history_line(hist, rec.get('score'), today) if hist else None)
        out.extend(x for x in extras if x)
    return out, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--file', default='before_market_line.txt')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    path = os.path.join(ROOT, 'data', a.date, a.file)
    if not os.path.exists(path):
        print(f'檔案不存在：{path}')
        return 1
    with open(os.path.join(ROOT, 'data', 'company_profiles.json'), encoding='utf-8') as f:
        profiles = json.load(f)
    with open(path, encoding='utf-8-sig') as f:
        content = f.read()

    out, missing = insert_profiles(content.split('\n'), profiles,
                                   _load_list(a.date, 'revenue_check.json'),
                                   _load_list(a.date, 'eps_check.json'),
                                   recs=_load_recs(a.date), hist=load_track_history(), today=a.date)
    new = '\n'.join(out)
    if len(new) > MAX_LINE_CHARS:
        print(f'⚠️ 插入簡介後 {len(new)} 字元超過 {MAX_LINE_CHARS}，未寫入')
        return 1
    if a.dry_run:
        print(new)
    elif new != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        print('✅ 已插入公司簡介')
    else:
        print('✅ 簡介已齊全，無需變更')
    if missing:
        print(f'❌ 缺公司簡介：{", ".join(sorted(set(missing)))}（請查證後寫入 data/company_profiles.json）')
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
