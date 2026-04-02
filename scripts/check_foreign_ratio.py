#!/usr/bin/env python3
"""
查詢外資持股比例週變化（供 Step 7 評分使用）

用法：
    python scripts/check_foreign_ratio.py 2330 2303 3037
    python scripts/check_foreign_ratio.py --update-cache    # 更新快取

數據來源：FinMind API (TaiwanStockShareholding) → 快取於 data/cache/foreign_ratio_cache.json
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
CACHE_FILE = CACHE_DIR / "foreign_ratio_cache.json"


def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(data):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def fetch_shareholding(stock_id):
    """從 FinMind 取得外資持股比例"""
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanStockShareholding',
        'data_id': stock_id,
        'start_date': '2026-02-01',
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


def get_ratio_change(stock_id, cache):
    """計算最近一週外資持股比變化"""
    if stock_id not in cache:
        return None, None, None

    rows = cache[stock_id]
    if len(rows) < 2:
        return None, None, None

    # 最近兩期
    latest = rows[-1]
    prev = rows[-2]

    current_ratio = latest.get('ForeignInvestmentSharesRatio', 0)
    prev_ratio = prev.get('ForeignInvestmentSharesRatio', 0)
    change = round(current_ratio - prev_ratio, 2)

    return current_ratio, change, latest.get('date', '')


def update_cache(stock_codes=None):
    """更新快取"""
    cache = load_cache()

    if stock_codes:
        targets = stock_codes
    else:
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

    print(f"更新 {len(targets)} 檔持股數據...")
    for i, code in enumerate(targets):
        rows = fetch_shareholding(code)
        if rows:
            cache[code] = rows
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
        print("用法: python scripts/check_foreign_ratio.py 2330 2303 3037")
        print("      python scripts/check_foreign_ratio.py --update-cache")
        return

    cache = load_cache()

    # 抓缺少的
    missing = [c for c in stock_codes if c not in cache]
    if missing:
        print(f"抓取 {len(missing)} 檔持股數據...", flush=True)
        for code in missing:
            rows = fetch_shareholding(code)
            if rows:
                cache[code] = rows
            time.sleep(0.3)
        save_cache(cache)

    # 輸出結果
    print()
    print(f"{'股票':>6} | {'數據日期':>12} | {'外資持股比':>10} | {'週變化':>8} | {'評分建議':>12}")
    print("-" * 65)

    results = []
    for code in stock_codes:
        ratio, change, date = get_ratio_change(code, cache)

        suggestion = ""
        if change is not None:
            if change > 0.5:
                suggestion = "+5分（大增>0.5%）"
            elif change > 0:
                suggestion = "不調整（小增）"
            elif change <= -0.1:
                suggestion = "-3分（週減≥0.1%）"
            else:
                suggestion = "不調整（微減<0.1%）"
        else:
            suggestion = "無數據"

        ratio_str = f"{ratio:.2f}%" if ratio is not None else "N/A"
        change_str = f"{change:+.2f}%" if change is not None else "N/A"
        date_str = date if date else "N/A"
        print(f"{code:>6} | {date_str:>12} | {ratio_str:>10} | {change_str:>8} | {suggestion}")

        results.append({
            'code': code,
            'date': date,
            'foreign_ratio': ratio,
            'ratio_change': change,
        })

    # 輸出 JSON
    json_path = PROJECT_DIR / "data" / datetime.now().strftime("%Y-%m-%d") / "foreign_ratio_check.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果已存: {json_path}")


if __name__ == "__main__":
    main()
