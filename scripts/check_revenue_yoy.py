#!/usr/bin/env python3
"""
查詢個股營收年增率（供 Step 7 評分使用）

用法：
    python scripts/check_revenue_yoy.py 2330 2303 3037
    python scripts/check_revenue_yoy.py --update-cache    # 更新快取（每月跑一次即可）

數據來源：FinMind API → 快取於 data/cache/revenue_cache.json
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
CACHE_FILE = CACHE_DIR / "revenue_cache.json"


def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(data):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def fetch_revenue(stock_id):
    """從 FinMind 取得月營收"""
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanStockMonthRevenue',
        'data_id': stock_id,
        'start_date': '2024-06-01',
        'end_date': datetime.now().strftime('%Y-%m-%d'),
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('status') == 200 and data.get('data'):
            return data['data']
    except Exception:
        pass
    return []


def calc_yoy(revenues):
    """計算每月 YoY%"""
    monthly = {}
    for r in revenues:
        key = f"{r['revenue_year']}-{r['revenue_month']:02d}"
        monthly[key] = r['revenue']

    yoy = {}
    for key, rev in monthly.items():
        year, month = key.split('-')
        prev_key = f"{int(year)-1}-{month}"
        if prev_key in monthly and monthly[prev_key] > 0:
            yoy[key] = round((rev - monthly[prev_key]) / monthly[prev_key] * 100, 1)
    return yoy


def get_latest_yoy(stock_id, cache):
    """取得最新一期營收 YoY"""
    if stock_id not in cache:
        return None, None

    yoy = calc_yoy(cache[stock_id])
    if not yoy:
        return None, None

    latest_key = sorted(yoy.keys())[-1]
    return latest_key, yoy[latest_key]


def get_streak(stock_id, cache):
    """計算連續營收成長月數"""
    if stock_id not in cache:
        return 0

    yoy = calc_yoy(cache[stock_id])
    if not yoy:
        return 0

    streak = 0
    for key in sorted(yoy.keys(), reverse=True):
        if yoy[key] > 0:
            streak += 1
        else:
            break
    return streak


def get_decline_streak(stock_id, cache):
    """計算連續營收衰退月數"""
    if stock_id not in cache:
        return 0

    yoy = calc_yoy(cache[stock_id])
    if not yoy:
        return 0

    streak = 0
    for key in sorted(yoy.keys(), reverse=True):
        if yoy[key] < 0:
            streak += 1
        else:
            break
    return streak


def get_5d_pullback(stock_id):
    """查詢近5日股價回檔幅度（%），負值=回檔"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW"
        r = requests.get(url, params={"interval": "1d", "range": "10d"},
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        data = r.json()
        closes = [c for c in data['chart']['result'][0]['indicators']['quote'][0]['close'] if c]
        if len(closes) >= 6:
            return (closes[-1] - closes[-6]) / closes[-6] * 100
    except Exception:
        pass
    return None


def update_cache(stock_codes=None):
    """更新快取"""
    cache = load_cache()

    if stock_codes:
        targets = stock_codes
    else:
        # 從 T86 找常見股票
        from collections import defaultdict
        freq = defaultdict(int)
        for fp in CACHE_DIR.glob("twse_t86_*.json"):
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for code in data:
                if code.isdigit() and len(code) == 4 and not code.startswith('00'):
                    if abs(data[code].get('total', 0)) > 500:
                        freq[code] += 1
        targets = [c for c, f in freq.items() if f >= 5 and c not in cache]

    print(f"更新 {len(targets)} 檔營收數據...")
    for i, code in enumerate(targets):
        revs = fetch_revenue(code)
        if revs:
            cache[code] = revs
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(targets)}")
            time.sleep(1)
        else:
            time.sleep(0.3)

    save_cache(cache)
    print(f"快取已更新: {len(cache)} 檔")
    return cache


def main():
    if '--update-cache' in sys.argv:
        update_cache()
        return

    stock_codes = [s for s in sys.argv[1:] if s.isdigit()]
    if not stock_codes:
        print("用法: python scripts/check_revenue_yoy.py 2330 2303 3037")
        print("      python scripts/check_revenue_yoy.py --update-cache")
        return

    cache = load_cache()

    # 抓缺少的
    missing = [c for c in stock_codes if c not in cache]
    if missing:
        print(f"抓取 {len(missing)} 檔營收...", flush=True)
        for code in missing:
            revs = fetch_revenue(code)
            if revs:
                cache[code] = revs
            time.sleep(0.3)
        save_cache(cache)

    # 輸出結果
    print()
    print(f"{'股票':>6} | {'最新營收月':>10} | {'YoY%':>8} | {'5日回檔':>8} | {'評分建議'}")
    print("-" * 70)

    # 批次查回檔
    print("查詢近5日回檔...", flush=True)
    pullbacks = {}
    for code in stock_codes:
        pullbacks[code] = get_5d_pullback(code)
        time.sleep(0.2)

    results = []
    for code in stock_codes:
        month, yoy = get_latest_yoy(code, cache)
        growth_streak = get_streak(code, cache)
        decline_streak = get_decline_streak(code, cache)
        pullback = pullbacks.get(code)

        # 評分建議（腳本直接判定，不交給 Claude）
        suggestion = ""
        adj = 0
        if yoy is not None:
            if yoy >= 30 and pullback is not None and pullback <= -2:
                suggestion = f"+5分（年增{yoy:+.0f}%+回檔{pullback:.1f}%）"
                adj = 5
            elif yoy >= 10 and pullback is not None and pullback <= -5:
                suggestion = f"+5分（年增{yoy:+.0f}%+回檔{pullback:.1f}%）"
                adj = 5
            elif yoy >= 30:
                suggestion = f"不加分（年增{yoy:+.0f}%但回檔僅{pullback:.1f}%，未達-2%）" if pullback is not None else "不加分（無回檔數據）"
            elif yoy >= 10:
                suggestion = f"不加分（年增{yoy:+.0f}%但回檔僅{pullback:.1f}%，未達-5%）" if pullback is not None else "不加分（無回檔數據）"
            elif decline_streak >= 3:
                suggestion = f"-5分（連續衰退{decline_streak}個月）"
                adj = -5
            else:
                suggestion = "不調整"
        else:
            suggestion = "無數據"

        yoy_str = f"{yoy:+.1f}%" if yoy is not None else "N/A"
        pullback_str = f"{pullback:+.1f}%" if pullback is not None else "N/A"
        month_str = month if month else "N/A"
        print(f"{code:>6} | {month_str:>10} | {yoy_str:>8} | {pullback_str:>8} | {suggestion}")

        results.append({
            'code': code,
            'month': month,
            'yoy': yoy,
            'pullback_5d': round(pullback, 2) if pullback is not None else None,
            'growth_streak': growth_streak,
            'decline_streak': decline_streak,
            'adj': adj,
            'suggestion': suggestion,
        })

    # 輸出 JSON 供其他腳本使用
    json_path = PROJECT_DIR / "data" / datetime.now().strftime("%Y-%m-%d") / "revenue_check.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果已存: {json_path}")


if __name__ == "__main__":
    main()
