#!/usr/bin/env python3
"""
季報 EPS + 毛利率分析（供 Step 7 評分使用）

用法：
    python scripts/check_eps_quarterly.py 2330 2303 3037
    python scripts/check_eps_quarterly.py --update-cache 2330 2303   # 強制重抓指定股票

數據來源：FinMind TaiwanStockFinancialStatements → 快取於 data/cache/eps_cache.json

評分規則：
  EPS YoY（同季比）
    ≥ +50%           → +5 分
    +20% ~ +49%      → +3 分
    -20% ~ +19%      →  0 分
    ≤ -20%           → -3 分
    連續 2 季 YoY 負成長 → -5 分（覆蓋上述）

  毛利率 QoQ（環比）
    上升 ≥ +2pp      → +2 分
    下降 ≥ -3pp      → -2 分

  防護：單檔合計 [-5, +5]
"""

import sys
import os
import io
import json
import time
from pathlib import Path
from datetime import datetime
import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"
CACHE_FILE = CACHE_DIR / "eps_cache.json"

FINMIND_URL = 'https://api.finmindtrade.com/api/v4/data'


# ── 快取 ────────────────────────────────────────────────────────────────────

def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(data):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 抓取 ────────────────────────────────────────────────────────────────────

def fetch_financials(stock_id):
    """從 FinMind 抓季報損益表"""
    params = {
        'dataset': 'TaiwanStockFinancialStatements',
        'data_id': stock_id,
        'start_date': '2023-01-01',
        'end_date': datetime.now().strftime('%Y-%m-%d'),
    }
    try:
        r = requests.get(FINMIND_URL, params=params, timeout=15)
        data = r.json()
        if data.get('status') == 200 and data.get('data'):
            return data['data']
    except Exception as e:
        print(f"  [{stock_id}] 抓取失敗: {e}", file=sys.stderr)
    return []


# ── 計算 ────────────────────────────────────────────────────────────────────

def build_quarterly(rows):
    """
    整理成 {date: {EPS, GrossMarginPct, Revenue}} 結構
    date 為季末日期字串 (YYYY-MM-DD)
    """
    by_date = {}
    for row in rows:
        d = row['date']
        t = row['type']
        v = row['value']
        if d not in by_date:
            by_date[d] = {}
        by_date[d][t] = v

    result = {}
    for d, fields in by_date.items():
        eps = fields.get('EPS')
        rev = fields.get('Revenue')
        gp = fields.get('GrossProfit')
        gm = round(gp / rev * 100, 2) if rev and gp else None
        if eps is not None or gm is not None:
            result[d] = {'eps': eps, 'gross_margin_pct': gm, 'revenue': rev}
    return result


def same_quarter_last_year(date_str):
    """回傳同季上年日期，e.g. 2025-03-31 → 2024-03-31"""
    y, m, d = date_str.split('-')
    return f"{int(y)-1}-{m}-{d}"


def calc_eps_yoy(quarterly):
    """計算每季 EPS YoY%，回傳 {date: yoy%}"""
    yoy = {}
    for date, vals in quarterly.items():
        prev = same_quarter_last_year(date)
        if prev in quarterly:
            cur_eps = vals.get('eps')
            prev_eps = quarterly[prev].get('eps')
            if cur_eps is not None and prev_eps is not None and prev_eps != 0:
                yoy[date] = round((cur_eps - prev_eps) / abs(prev_eps) * 100, 1)
    return yoy


def calc_gm_qoq(quarterly):
    """計算最新一季毛利率 QoQ 變化（pp），回傳 (latest_date, delta_pp)"""
    dates = sorted(quarterly.keys())
    for i in range(len(dates) - 1, 0, -1):
        cur = quarterly[dates[i]].get('gross_margin_pct')
        prev = quarterly[dates[i - 1]].get('gross_margin_pct')
        if cur is not None and prev is not None:
            return dates[i], round(cur - prev, 2)
    return None, None


# ── 評分 ────────────────────────────────────────────────────────────────────

def score(eps_yoy_series, gm_qoq_delta, latest_eps_date):
    """
    eps_yoy_series: {date: yoy%}（所有季度）
    gm_qoq_delta:  float or None（最新一季毛利率 QoQ pp）
    latest_eps_date: 最新 EPS 日期

    回傳 (adj, notes[])
    """
    notes = []
    adj = 0

    # ── EPS YoY ────────────────────────────────
    if eps_yoy_series and latest_eps_date:
        dates = sorted(eps_yoy_series.keys())
        latest_yoy = eps_yoy_series.get(latest_eps_date)

        # 連續負成長季數
        neg_streak = 0
        for d in reversed(dates):
            if eps_yoy_series[d] < 0:
                neg_streak += 1
            else:
                break

        if neg_streak >= 2:
            adj += -5
            notes.append(f"EPS連續{neg_streak}季YoY負成長 -5")
        elif latest_yoy is not None:
            if latest_yoy >= 50:
                adj += 5
                notes.append(f"EPS YoY+{latest_yoy:.0f}% +5")
            elif latest_yoy >= 20:
                adj += 3
                notes.append(f"EPS YoY+{latest_yoy:.0f}% +3")
            elif latest_yoy <= -20:
                adj += -3
                notes.append(f"EPS YoY{latest_yoy:.0f}% -3")
            else:
                notes.append(f"EPS YoY{latest_yoy:+.0f}% 不調整")

    # ── 毛利率 QoQ ─────────────────────────────
    if gm_qoq_delta is not None:
        if gm_qoq_delta >= 2:
            adj += 2
            notes.append(f"毛利率QoQ+{gm_qoq_delta:.1f}pp +2")
        elif gm_qoq_delta <= -3:
            adj += -2
            notes.append(f"毛利率QoQ{gm_qoq_delta:.1f}pp -2")
        else:
            notes.append(f"毛利率QoQ{gm_qoq_delta:+.1f}pp 不調整")

    # 防護 [-5, +5]
    adj = max(-5, min(5, adj))
    return adj, notes


# ── 主流程 ───────────────────────────────────────────────────────────────────

def analyze(stock_id, cache):
    rows = cache.get(stock_id)
    if not rows:
        return None

    quarterly = build_quarterly(rows)
    if not quarterly:
        return None

    dates = sorted(quarterly.keys())
    latest_date = dates[-1]
    latest_q = quarterly[latest_date]

    eps_yoy = calc_eps_yoy(quarterly)
    gm_date, gm_delta = calc_gm_qoq(quarterly)

    latest_eps_yoy = eps_yoy.get(latest_date)
    adj, notes = score(eps_yoy, gm_delta, latest_date)

    return {
        'code': stock_id,
        'latest_quarter': latest_date,
        'eps': latest_q.get('eps'),
        'eps_yoy_pct': latest_eps_yoy,
        'gross_margin_pct': latest_q.get('gross_margin_pct'),
        'gm_qoq_delta': gm_delta,
        'adj': adj,
        'notes': ' | '.join(notes),
        'suggestion': f"+{adj}分" if adj > 0 else (f"{adj}分" if adj < 0 else "不調整"),
    }


def main():
    force_update = '--update-cache' in sys.argv
    stock_codes = [s for s in sys.argv[1:] if s.isdigit()]

    if not stock_codes:
        print("用法: python scripts/check_eps_quarterly.py 2330 2303 3037")
        print("      python scripts/check_eps_quarterly.py --update-cache 2330 2303")
        return

    cache = load_cache()

    # 抓取缺少或強制更新的股票
    targets = stock_codes if force_update else [c for c in stock_codes if c not in cache]
    if targets:
        print(f"抓取 {len(targets)} 檔季報...", flush=True)
        for code in targets:
            rows = fetch_financials(code)
            if rows:
                cache[code] = rows
            else:
                print(f"  [{code}] 無數據", flush=True)
            time.sleep(0.5)
        save_cache(cache)

    # 分析並輸出
    print()
    header = f"{'股票':>6} | {'最新季':>10} | {'EPS':>7} | {'EPS YoY':>9} | {'毛利率':>7} | {'QoQ':>6} | {'評分'}"
    print(header)
    print("-" * 80)

    results = []
    for code in stock_codes:
        r = analyze(code, cache)
        if r is None:
            print(f"{code:>6} | {'N/A':>10} | {'N/A':>7} | {'N/A':>9} | {'N/A':>7} | {'N/A':>6} | 無數據")
            results.append({'code': code, 'adj': 0, 'suggestion': '無數據', 'notes': '無數據'})
            continue

        eps_str = f"{r['eps']:.2f}" if r['eps'] is not None else "N/A"
        yoy_str = f"{r['eps_yoy_pct']:+.1f}%" if r['eps_yoy_pct'] is not None else "N/A"
        gm_str = f"{r['gross_margin_pct']:.1f}%" if r['gross_margin_pct'] is not None else "N/A"
        gm_qoq_str = f"{r['gm_qoq_delta']:+.1f}pp" if r['gm_qoq_delta'] is not None else "N/A"

        print(f"{code:>6} | {r['latest_quarter']:>10} | {eps_str:>7} | {yoy_str:>9} | {gm_str:>7} | {gm_qoq_str:>6} | {r['suggestion']}（{r['notes']}）")
        results.append(r)

    # 存 JSON
    out_path = PROJECT_DIR / "data" / datetime.now().strftime("%Y-%m-%d") / "eps_check.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果已存: {out_path}")


if __name__ == "__main__":
    main()
