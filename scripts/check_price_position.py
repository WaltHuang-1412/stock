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

    # 判定：MA20 位置 → 基礎分（0-14）
    above_ma60 = (current > ma60) if ma60 else None

    if above_ma20 is None:
        position = "無資料"
        base_score = 10
        ma60_mod = 0
        suggestion = "10分（資料不足，給中性分）"
    elif vs_ma20 > 15:
        position = "月線上強勢"
        base_score = 14
    elif vs_ma20 > 5:
        position = "月線上"
        base_score = 12
    elif vs_ma20 > 0:
        position = "月線上（貼近）"
        base_score = 10
    elif vs_ma20 > -5:
        position = "月線下（剛跌破）"
        base_score = 7
    elif vs_ma20 > -10:
        position = "月線下"
        base_score = 4
    else:
        position = "月線下（深度）"
        base_score = 2

    # MA60 修正（-1 ~ +1）
    if above_ma20 is not None:
        if above_ma20 and above_ma60:
            ma60_mod = 1   # 月線+季線雙確認
        elif not above_ma20 and above_ma60:
            ma60_mod = 1   # 月線下但季線仍支撐，短線回調非趨勢反轉
        elif above_ma20 and not above_ma60:
            ma60_mod = 0   # 月線上但季線壓頂，偏弱反彈
        else:
            ma60_mod = -1  # 月線+季線雙破，趨勢惡化

        final_score = max(0, min(15, base_score + ma60_mod))
        ma60_label = (
            "+1（月季雙線上）" if (above_ma20 and above_ma60) else
            "+1（月線下但季線撐）" if (not above_ma20 and above_ma60) else
            "0（月線上但季線壓）" if (above_ma20 and not above_ma60) else
            "-1（月季雙線下）"
        )
        suggestion = f"{final_score}分（MA20 {vs_ma20:+.1f}% 基礎{base_score} | MA60 {ma60_label}）"
    else:
        ma60_mod = 0
        final_score = base_score

    adj = final_score

    return {
        'code': code,
        'current': current,
        'ma20': round(ma20, 2) if ma20 else None,
        'ma60': round(ma60, 2) if ma60 else None,
        'vs_ma20': round(vs_ma20, 2),
        'vs_ma60': round(vs_ma60, 2) if ma60 else None,
        'above_ma20': above_ma20,
        'above_ma60': above_ma60,
        'position': position,
        'base_score': base_score,
        'ma60_mod': ma60_mod,
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
    print(f"{'股票':>6} | {'現價':>8} | {'MA20':>8} | {'vs MA20':>8} | {'MA60':>8} | {'vs MA60':>8} | {'得分':>4} | {'評分建議'}")
    print("-" * 95)

    for code in stock_codes:
        result = analyze_position(code)
        if result:
            results.append(result)
            ma20_str = f"{result['ma20']:.1f}" if result['ma20'] else "N/A"
            ma60_str = f"{result['ma60']:.1f}" if result['ma60'] else "N/A"
            vs60_str = f"{result['vs_ma60']:+.1f}%" if result['vs_ma60'] is not None else "N/A"
            print(f"{code:>6} | {result['current']:>8.1f} | {ma20_str:>8} | {result['vs_ma20']:>+7.1f}% | {ma60_str:>8} | {vs60_str:>8} | {result['adj']:>4} | {result['suggestion']}")
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
