#!/usr/bin/env python3
"""
每週規則有效性驗證（週五盤後自動執行）

檢查項目：
1. 整體準確率趨勢
2. 新規則（營收/持股比/過量買超）的加分股 vs 扣分股準確率
3. 如果扣分股準確率 ≥ 無變化股 → 規則可能失效，發警告

輸出：data/reports/weekly_rule_check_YYYY-MM-DD.txt（LINE 推送用）
"""

import sys
import os
import io
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"
CACHE_DIR = PROJECT_DIR / "data" / "cache"
REPORTS_DIR = PROJECT_DIR / "data" / "reports"


def load_settled():
    all_recs = []
    for fp in sorted(TRACKING_DIR.glob("tracking_202*.json")):
        if 'example' in fp.name:
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        date_str = data.get('date', '')
        for rec in data.get('recommendations', []):
            result = rec.get('result', '')
            if result not in ('success', 'fail'):
                continue
            industry = rec.get('industry', '')
            if isinstance(industry, dict):
                industry = industry.get('sector', '')
            if not industry:
                industry = '未分類'
            all_recs.append({
                'date': date_str,
                'code': rec.get('stock_code') or rec.get('symbol', ''),
                'name': rec.get('stock_name') or rec.get('name', ''),
                'score': rec.get('score', 0),
                'result': result,
                'industry': industry,
            })
    return all_recs


def load_revenue_cache():
    fp = CACHE_DIR / "revenue_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_ratio_cache():
    fp = CACHE_DIR / "foreign_ratio_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_revenue_yoy(code, date, cache):
    if code not in cache:
        return None, 0
    revenues = cache[code]
    monthly = {}
    for r in revenues:
        monthly[(r['revenue_year'], r['revenue_month'])] = r['revenue']
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return None, 0
    m, y = dt.month - 1, dt.year
    if m == 0:
        m, y = 12, y - 1
    cur = monthly.get((y, m))
    prev = monthly.get((y - 1, m))
    if cur and prev and prev > 0:
        yoy = (cur - prev) / prev * 100
    else:
        return None, 0
    # decline streak
    streak = 0
    cy, cm = y, m
    while True:
        c = monthly.get((cy, cm))
        p = monthly.get((cy - 1, cm))
        if c and p and p > 0 and (c - p) / p * 100 < 0:
            streak += 1
            cm -= 1
            if cm == 0:
                cm, cy = 12, cy - 1
        else:
            break
    return yoy, streak


def get_ratio_change(code, date, cache):
    if code not in cache:
        return None
    rows = cache[code]
    if len(rows) < 2:
        return None
    current, prev = None, None
    for row in rows:
        rd = row['date'].replace('-', '')
        dd = date.replace('-', '')
        if rd <= dd:
            prev = current
            current = row
    if current is None or prev is None:
        return None
    return current.get('ForeignInvestmentSharesRatio', 0) - prev.get('ForeignInvestmentSharesRatio', 0)


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    recs = load_settled()
    if not recs:
        print("無結算資料")
        return

    rev_cache = load_revenue_cache()
    ratio_cache = load_ratio_cache()

    total = len(recs)
    success = sum(1 for r in recs if r['result'] == 'success')
    overall_acc = success / total * 100

    # 逐檔分類 + 記錄每條規則觸發
    up, down, neutral = [], [], []

    # 各規則獨立統計
    rule_stats = {
        'rev_decline': {'success': 0, 'fail': 0, 'stocks': []},   # 營收連續衰退 -5
        'ratio_up': {'success': 0, 'fail': 0, 'stocks': []},      # 持股比大增 +5
        'ratio_down': {'success': 0, 'fail': 0, 'stocks': []},    # 持股比週減 -3
    }

    # 產業統計
    industry_stats = defaultdict(lambda: {'success': 0, 'fail': 0})

    for rec in recs:
        code, date = rec['code'], rec['date']
        adj = 0
        triggers = []

        # 產業
        industry = rec.get('industry', '未分類')
        industry_stats[industry][rec['result']] += 1

        # 營收
        yoy, decline = get_revenue_yoy(code, date, rev_cache)
        rec['yoy'] = yoy
        rec['decline_streak'] = decline

        if decline >= 3:
            adj -= 5
            triggers.append(f"衰退{decline}月-5")
            rule_stats['rev_decline'][rec['result']] += 1
            rule_stats['rev_decline']['stocks'].append(rec)

        # 持股比
        ratio_chg = get_ratio_change(code, date, ratio_cache)
        rec['ratio_change'] = ratio_chg

        if ratio_chg is not None:
            if ratio_chg > 0.5:
                adj += 5
                triggers.append(f"持股+{ratio_chg:.1f}%+5")
                rule_stats['ratio_up'][rec['result']] += 1
                rule_stats['ratio_up']['stocks'].append(rec)
            elif ratio_chg <= -0.1:
                adj -= 3
                triggers.append(f"持股{ratio_chg:.1f}%-3")
                rule_stats['ratio_down'][rec['result']] += 1
                rule_stats['ratio_down']['stocks'].append(rec)

        rec['adj'] = adj
        rec['triggers'] = triggers

        if adj > 0:
            up.append(rec)
        elif adj < 0:
            down.append(rec)
        else:
            neutral.append(rec)

    def acc(lst):
        if not lst:
            return 0, 0
        s = sum(1 for r in lst if r['result'] == 'success')
        return s / len(lst) * 100, len(lst)

    def rule_acc(stat):
        t = stat['success'] + stat['fail']
        if t == 0:
            return 0, 0
        return stat['success'] / t * 100, t

    up_acc, up_n = acc(up)
    down_acc, down_n = acc(down)
    neutral_acc, neutral_n = acc(neutral)

    # 近2週 vs 全期
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    recent = [r for r in recs if r['date'] >= two_weeks_ago]
    recent_s = sum(1 for r in recent if r['result'] == 'success')
    recent_acc = recent_s / len(recent) * 100 if recent else 0

    # 近4週
    four_weeks_ago = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
    month = [r for r in recs if r['date'] >= four_weeks_ago]
    month_s = sum(1 for r in month if r['result'] == 'success')
    month_acc = month_s / len(month) * 100 if month else 0

    rule_ok = down_acc < neutral_acc - 3

    # ===== 產出 =====
    lines = []
    lines.append(f"[週報] 規則驗證 {today}")
    lines.append("")

    # 1. 整體趨勢
    lines.append(f"== 準確率趨勢 ==")
    lines.append(f"全期: {success}/{total} = {overall_acc:.1f}%")
    if month:
        lines.append(f"近4週: {month_s}/{len(month)} = {month_acc:.1f}%")
    if recent:
        lines.append(f"近2週: {recent_s}/{len(recent)} = {recent_acc:.1f}%")
    # 趨勢判斷
    if recent and month and len(recent) >= 3 and len(month) >= 10:
        if recent_acc > month_acc + 5:
            lines.append(f"趨勢: 上升中")
        elif recent_acc < month_acc - 5:
            lines.append(f"趨勢: 下降中!!")
        else:
            lines.append(f"趨勢: 持平")
    lines.append("")

    # 2. 新規則區分力
    lines.append(f"== 新規則區分力 ==")
    lines.append(f"加分股: {up_acc:.0f}% ({up_n}檔)")
    lines.append(f"扣分股: {down_acc:.0f}% ({down_n}檔)")
    lines.append(f"無變化: {neutral_acc:.0f}% ({neutral_n}檔)")
    lines.append("")

    # 3. 各規則拆解
    lines.append(f"== 各規則準確率 ==")
    for rule_name, display in [
        ('rev_decline', '營收連續衰退≥3月(-5分)'),
        ('ratio_up', '外資持股比大增>0.5%(+5分)'),
        ('ratio_down', '外資持股比週減≥0.1%(-3分)'),
    ]:
        a, n = rule_acc(rule_stats[rule_name])
        s = rule_stats[rule_name]['success']
        f = rule_stats[rule_name]['fail']
        if n > 0:
            lines.append(f"{display}: {s}成/{f}敗 = {a:.0f}% ({n}檔)")
        else:
            lines.append(f"{display}: 尚無觸發")
    lines.append("")

    # 4. 加分股明細（最多5檔）
    if up:
        lines.append(f"== 加分股明細 ==")
        for r in up[:5]:
            triggers = "+".join(r['triggers'])
            lines.append(f"{r['date'][-5:]} {r['code']}{r['name']} {r['result']} ({triggers})")
        if len(up) > 5:
            lines.append(f"...共{len(up)}檔")
        lines.append("")

    # 5. 扣分股 fail 明細（警示用，最多8檔）
    down_fails = [r for r in down if r['result'] == 'fail']
    down_success = [r for r in down if r['result'] == 'success']
    if down_fails:
        lines.append(f"== 扣分股(fail)前8檔 ==")
        for r in down_fails[:8]:
            triggers = "+".join(r['triggers'])
            lines.append(f"{r['date'][-5:]} {r['code']}{r['name']} FAIL ({triggers})")
        if len(down_fails) > 8:
            lines.append(f"...共{len(down_fails)}檔fail")
        lines.append("")

    # 6. 扣分股中的 success（被誤殺的）
    if down_success:
        lines.append(f"== 扣分但成功(誤殺){len(down_success)}檔 ==")
        for r in down_success[:5]:
            triggers = "+".join(r['triggers'])
            lines.append(f"{r['date'][-5:]} {r['code']}{r['name']} SUCCESS ({triggers})")
        if len(down_success) > 5:
            lines.append(f"...共{len(down_success)}檔")
        lines.append("")

    # 7. 產業準確率 TOP5/WORST5
    ind_list = [(k, v['success'], v['fail']) for k, v in industry_stats.items()
                if v['success'] + v['fail'] >= 3]
    if ind_list:
        ind_list.sort(key=lambda x: x[1]/(x[1]+x[2]), reverse=True)
        lines.append(f"== 產業TOP5 ==")
        for name, s, f in ind_list[:5]:
            lines.append(f"{name}: {s}/{s+f}={s/(s+f)*100:.0f}%")
        lines.append("")
        lines.append(f"== 產業WORST5 ==")
        for name, s, f in ind_list[-5:]:
            lines.append(f"{name}: {s}/{s+f}={s/(s+f)*100:.0f}%")
        lines.append("")

    # 8. 結論
    lines.append(f"== 結論 ==")
    if rule_ok:
        lines.append(f"規則有效 (扣分{down_acc:.0f}% < 無變化{neutral_acc:.0f}%)")
    else:
        lines.append(f"!! 規則可能失效 !!")
        lines.append(f"扣分{down_acc:.0f}% vs 無變化{neutral_acc:.0f}%")
        lines.append(f"建議檢查是否調整或移除")

    output = "\n".join(lines)

    # LINE 上限 5000 字元
    if len(output) > 4900:
        output = output[:4900] + "\n...(截斷)"

    print(output)

    # 存檔
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"weekly_rule_check_{today}.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\n已存: {out_path}")


if __name__ == "__main__":
    main()
