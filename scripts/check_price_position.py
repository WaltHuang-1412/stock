#!/usr/bin/env python3
"""
個股價格位置判斷（供 Step 7 評分使用）

判斷每檔候選股現在是在便宜還是貴的位置。

用法：
    python scripts/check_price_position.py 2330 2303 3702 00929

輸出：
    每檔股票的價格位置 + 評分建議
    JSON 存入 data/YYYY-MM-DD/price_position_check.json
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


def fetch_stock_data(code, days=300):
    """取得股價歷史"""
    suffix = ".TW"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suffix}"
    params = {"interval": "1d", "range": f"{days}d"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        closes = [c for c in result['indicators']['quote'][0]['close'] if c is not None]
        highs = [h for h in result['indicators']['quote'][0]['high'] if h is not None]
        lows = [l for l in result['indicators']['quote'][0]['low'] if l is not None]
        return closes, highs, lows
    except Exception:
        return [], [], []


def analyze_position(code):
    """分析一檔股票的價格位置（月線判斷）"""
    closes, highs, lows = fetch_stock_data(code)

    if len(closes) < 20:
        return None

    current = closes[-1]

    # 均線
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
    ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else None

    vs_ma20 = (current - ma20) / ma20 * 100 if ma20 else 0
    vs_ma60 = (current - ma60) / ma60 * 100 if ma60 else 0
    above_ma20 = current > ma20 if ma20 else None

    # 判定：只看月線
    if above_ma20 is None:
        position = "無資料"
        adj = 0
        suggestion = "不調整（資料不足）"
    elif not above_ma20:
        position = "月線下"
        adj = -3
        suggestion = f"-3分（跌破月線，現價vs MA20 {vs_ma20:+.1f}%）"
    else:
        position = "月線上"
        adj = 0
        suggestion = f"不調整（月線上 {vs_ma20:+.1f}%）"

    return {
        'code': code,
        'current': current,
        'ma20': round(ma20, 2) if ma20 else None,
        'ma60': round(ma60, 2) if ma60 else None,
        'vs_ma20': round(vs_ma20, 2),
        'vs_ma60': round(vs_ma60, 2) if ma60 else None,
        'above_ma20': above_ma20,
        'position': position,
        'adj': adj,
        'suggestion': suggestion,
    }


def main():
    stock_codes = [s for s in sys.argv[1:] if s[0].isdigit()]
    if not stock_codes:
        print("用法: python scripts/check_price_position.py 2330 2303 3702")
        return

    print("查詢價格位置...", flush=True)
    print()

    results = []
    print(f"{'股票':>6} | {'現價':>8} | {'MA20':>8} | {'vs MA20':>8} | {'判斷':>6} | {'評分建議'}")
    print("-" * 70)

    for code in stock_codes:
        result = analyze_position(code)
        if result:
            results.append(result)
            ma20_str = f"{result['ma20']:.1f}" if result['ma20'] else "N/A"
            print(f"{code:>6} | {result['current']:>8.1f} | {ma20_str:>8} | {result['vs_ma20']:>+7.1f}% | {result['position']:>6} | {result['suggestion']}")
        else:
            print(f"{code:>6} | 無資料")
        time.sleep(0.3)

    # 存 JSON
    today = datetime.now().strftime("%Y-%m-%d")
    json_path = PROJECT_DIR / "data" / today / "price_position_check.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果已存: {json_path}")


if __name__ == "__main__":
    main()
