#!/usr/bin/env python3
"""
停損/結算天數優化 — 找出最佳組合

用歷史 tracking 資料回測：
1. 不同停損幅度（-3%, -5%, -8%, -10%, -12%）的準確率和平均報酬
2. 不同結算天數（3, 5, 7, 10, 14 天）的準確率和平均報酬
3. 最佳組合
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

_price_cache = {}

def fetch_daily_prices(stock_code, days=200):
    if stock_code in _price_cache:
        return _price_cache[stock_code]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW"
    params = {"interval": "1d", "range": f"{days}d"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        closes = result['indicators']['quote'][0]['close']
        highs = result['indicators']['quote'][0]['high']
        lows = result['indicators']['quote'][0]['low']
        prices = []
        for ts, close, high, low in zip(timestamps, closes, highs, lows):
            if close is not None:
                dt = datetime.fromtimestamp(ts)
                prices.append({
                    'date': dt.strftime("%Y-%m-%d"),
                    'close': close,
                    'high': high or close,
                    'low': low or close,
                })
        _price_cache[stock_code] = prices
        return prices
    except Exception:
        _price_cache[stock_code] = []
        return []


def simulate_trade(stock_code, rec_price, target_price, rec_date, stop_pct, max_days):
    """模擬一筆交易，回傳結果"""
    prices = _price_cache.get(stock_code, [])
    if not prices:
        return None

    stop_price = rec_price * (1 + stop_pct / 100)

    # 找到推薦日之後的價格
    start_idx = None
    for i, p in enumerate(prices):
        if p['date'] >= rec_date:
            start_idx = i
            break

    if start_idx is None:
        return None

    # 逐日檢查
    trading_days = 0
    for i in range(start_idx, min(start_idx + max_days + 5, len(prices))):
        trading_days += 1
        p = prices[i]

        # 觸及目標（用盤中最高價）
        if p['high'] >= target_price:
            return {
                'result': 'success',
                'days': trading_days,
                'exit_price': target_price,
                'return_pct': (target_price - rec_price) / rec_price * 100,
            }

        # 觸及停損（用盤中最低價）
        if p['low'] <= stop_price:
            return {
                'result': 'fail',
                'days': trading_days,
                'exit_price': stop_price,
                'return_pct': stop_pct,
            }

        # 到期結算
        if trading_days >= max_days:
            close = p['close']
            return {
                'result': 'success' if close > rec_price else 'fail',
                'days': trading_days,
                'exit_price': close,
                'return_pct': (close - rec_price) / rec_price * 100,
            }

    return None


def load_all_recommendations():
    """載入所有推薦"""
    all_recs = []
    for fp in sorted(TRACKING_DIR.glob("tracking_202*.json")):
        if 'example' in fp.name:
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        date_str = data.get('date', '')
        for rec in data.get('recommendations', []):
            code = rec.get('stock_code') or rec.get('symbol', '')
            rec_price = rec.get('recommend_price', 0)
            target = rec.get('target_price', 0)
            score = rec.get('score', 0)

            try:
                rec_price = float(rec_price)
                target = float(target)
            except (ValueError, TypeError):
                continue
            if not code or rec_price <= 0 or target <= 0:
                continue

            all_recs.append({
                'date': date_str,
                'code': code,
                'name': rec.get('stock_name', ''),
                'rec_price': rec_price,
                'target_price': target,
                'score': score,
            })
    return all_recs


def main():
    print("=" * 70)
    print("  停損/結算天數優化")
    print("=" * 70)
    print()

    recs = load_all_recommendations()
    print(f"歷史推薦: {len(recs)} 筆")

    # 去重（同一檔續推的只算第一次）
    seen = set()
    unique_recs = []
    for r in recs:
        key = f"{r['code']}_{r['date']}"
        if key not in seen:
            seen.add(key)
            unique_recs.append(r)
    recs = unique_recs
    print(f"去重後: {len(recs)} 筆")

    # 收集需要的股票
    codes = list(set(r['code'] for r in recs))
    print(f"股票數: {len(codes)}")

    print("取得股價...")
    for i, code in enumerate(codes):
        fetch_daily_prices(code)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(codes)}", flush=True)
            time.sleep(0.5)
    print()

    # ===== 測試不同停損幅度 =====
    stop_levels = [-3, -5, -8, -10, -12]
    day_levels = [3, 5, 7, 10, 14]

    print("=" * 60)
    print("  分析 1: 不同停損幅度（固定 7 天結算）")
    print("=" * 60)
    print()

    print(f"{'停損':>6} | {'成功':>4} {'失敗':>4} {'無結果':>4} | {'準確率':>8} | {'平均報酬':>10} | {'平均天數':>8}")
    print("-" * 65)

    for stop in stop_levels:
        results = []
        for r in recs:
            res = simulate_trade(r['code'], r['rec_price'], r['target_price'], r['date'], stop, 7)
            if res:
                results.append(res)

        success = sum(1 for r in results if r['result'] == 'success')
        fail = len(results) - success
        acc = success / len(results) * 100 if results else 0
        avg_ret = sum(r['return_pct'] for r in results) / len(results) if results else 0
        avg_days = sum(r['days'] for r in results) / len(results) if results else 0
        no_result = len(recs) - len(results)

        print(f"{stop:>+5}% | {success:>4} {fail:>4} {no_result:>4} | {acc:>6.1f}% | {avg_ret:>+9.2f}% | {avg_days:>6.1f}天")

    print()

    # ===== 測試不同結算天數 =====
    print("=" * 60)
    print("  分析 2: 不同結算天數（固定 -8% 停損）")
    print("=" * 60)
    print()

    print(f"{'天數':>6} | {'成功':>4} {'失敗':>4} {'無結果':>4} | {'準確率':>8} | {'平均報酬':>10} | {'平均天數':>8}")
    print("-" * 65)

    for days in day_levels:
        results = []
        for r in recs:
            res = simulate_trade(r['code'], r['rec_price'], r['target_price'], r['date'], -8, days)
            if res:
                results.append(res)

        success = sum(1 for r in results if r['result'] == 'success')
        fail = len(results) - success
        acc = success / len(results) * 100 if results else 0
        avg_ret = sum(r['return_pct'] for r in results) / len(results) if results else 0
        avg_days = sum(r['days'] for r in results) / len(results) if results else 0
        no_result = len(recs) - len(results)

        print(f"{days:>5}天 | {success:>4} {fail:>4} {no_result:>4} | {acc:>6.1f}% | {avg_ret:>+9.2f}% | {avg_days:>6.1f}天")

    print()

    # ===== 交叉測試 =====
    print("=" * 60)
    print("  分析 3: 停損 × 結算天數 完整交叉（準確率 / 平均報酬）")
    print("=" * 60)
    print()

    # 表頭
    header = f"{'':>8}"
    for days in day_levels:
        header += f" | {days:>5}天"
    print(header)
    print("-" * (10 + len(day_levels) * 10))

    best_acc = 0
    best_combo = ""
    best_ret = -999
    best_ret_combo = ""

    for stop in stop_levels:
        row_acc = f"{stop:>+5}% 準"
        row_ret = f"{stop:>+5}% 報"
        for days in day_levels:
            results = []
            for r in recs:
                res = simulate_trade(r['code'], r['rec_price'], r['target_price'], r['date'], stop, days)
                if res:
                    results.append(res)

            if results:
                success = sum(1 for r in results if r['result'] == 'success')
                acc = success / len(results) * 100
                avg_ret = sum(r['return_pct'] for r in results) / len(results)
                row_acc += f" | {acc:>5.1f}%"
                row_ret += f" | {avg_ret:>+5.1f}%"

                if acc > best_acc:
                    best_acc = acc
                    best_combo = f"停損{stop}% + {days}天"
                if avg_ret > best_ret:
                    best_ret = avg_ret
                    best_ret_combo = f"停損{stop}% + {days}天"
            else:
                row_acc += f" | {'N/A':>6}"
                row_ret += f" | {'N/A':>6}"

        print(row_acc)
        print(row_ret)
        print()

    print()
    print("=" * 60)
    print("  結論")
    print("=" * 60)
    print()
    print(f"  最高準確率: {best_combo} = {best_acc:.1f}%")
    print(f"  最高報酬:   {best_ret_combo} = {best_ret:+.2f}%")
    print()

    # 跟現行比較
    current_results = []
    for r in recs:
        res = simulate_trade(r['code'], r['rec_price'], r['target_price'], r['date'], -8, 7)
        if res:
            current_results.append(res)

    if current_results:
        cur_acc = sum(1 for r in current_results if r['result'] == 'success') / len(current_results) * 100
        cur_ret = sum(r['return_pct'] for r in current_results) / len(current_results)
        print(f"  現行（-8%, 7天）: 準確率 {cur_acc:.1f}%, 報酬 {cur_ret:+.2f}%")
        print(f"  最佳準確率組合比現行: {best_acc - cur_acc:+.1f}%")
        print(f"  最佳報酬組合比現行:   {best_ret - cur_ret:+.2f}%")


if __name__ == "__main__":
    main()
