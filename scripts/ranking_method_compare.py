#!/usr/bin/env python3
"""
排名方法比較：avg_rank vs 買超佔比

比較三種法人排名方式的選股準確率：
1. avg_rank（現行）= (張數排名 + 金額排名) / 2
2. buy_ratio = 法人買超 / 日均成交量
3. buy_pct_cap = 法人買超金額 / 市值（如果有資料的話）

用 T86 + Yahoo Finance 回測
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import requests

os.environ['PYTHONUTF8'] = '1'

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"


def load_all_t86():
    all_data = {}
    for fp in sorted(CACHE_DIR.glob("twse_t86_*.json")):
        date_str = fp.stem.replace("twse_t86_", "")
        with open(fp, 'r', encoding='utf-8') as f:
            day_data = json.load(f)
        filtered = {}
        for code, info in day_data.items():
            if code.startswith("00") or not code.isdigit() or len(code) != 4:
                continue
            filtered[code] = {
                'foreign': info.get('foreign', 0),
                'trust': info.get('trust', 0),
                'total': info.get('total', 0),
            }
        all_data[date_str] = filtered
    return all_data


_price_cache = {}
_volume_cache = {}

def fetch_price_volume(stock_code, days=120):
    if stock_code in _price_cache:
        return
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW"
    params = {"interval": "1d", "range": f"{days}d"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        prices = {}
        volumes = {}
        for ts, close, vol in zip(timestamps, quote['close'], quote['volume']):
            if close is not None and vol is not None:
                dt = datetime.fromtimestamp(ts)
                d = dt.strftime("%Y%m%d")
                prices[d] = close
                volumes[d] = vol
        _price_cache[stock_code] = prices
        _volume_cache[stock_code] = volumes
    except Exception:
        _price_cache[stock_code] = {}
        _volume_cache[stock_code] = {}


def avg_volume(stock_code, date, trading_dates, lookback=20):
    """計算過去 N 天平均成交量"""
    volumes = _volume_cache.get(stock_code, {})
    if not volumes:
        return None
    sorted_dates = sorted(volumes.keys())
    # 找 date 之前的交易日
    past_vols = []
    for d in sorted_dates:
        if d < date:
            past_vols.append(volumes[d])
    if len(past_vols) < 5:
        return None
    # 取最後 lookback 天
    recent = past_vols[-lookback:]
    return sum(recent) / len(recent)


def forward_return(stock_code, buy_date, trading_dates, horizon=5):
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return None
    bp = prices.get(buy_date)
    if not bp:
        return None
    try:
        idx = trading_dates.index(buy_date)
    except ValueError:
        return None
    ti = idx + horizon
    if ti >= len(trading_dates):
        return None
    sp = prices.get(trading_dates[ti])
    if not sp:
        return None
    return (sp - bp) / bp * 100


def main():
    print("=" * 70)
    print("  排名方法比較：avg_rank vs 買超佔比")
    print("=" * 70)
    print()

    all_data = load_all_t86()
    trading_dates = sorted(all_data.keys())
    print(f"交易日: {len(trading_dates)} 天 ({trading_dates[0]}~{trading_dates[-1]})")

    # 收集所有出現在 TOP30 的股票
    all_codes = set()
    for date in trading_dates:
        items = sorted(all_data[date].items(), key=lambda x: x[1]['total'], reverse=True)
        for code, info in items[:50]:
            if info['total'] > 0:
                all_codes.add(code)

    print(f"股票數: {len(all_codes)}")
    print("取得股價+成交量...")
    code_list = list(all_codes)
    for i, code in enumerate(code_list):
        fetch_price_volume(code)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(code_list)}", flush=True)
            time.sleep(0.5)
    print()

    # ===== 每天計算三種排名，比較 TOP10/TOP20/TOP30 的報酬 =====

    results = {
        'avg_rank': {10: [], 20: [], 30: []},
        'buy_ratio': {10: [], 20: [], 30: []},
        'volume_rank': {10: [], 20: [], 30: []},
        'amount_rank': {10: [], 20: [], 30: []},
    }

    for date in trading_dates:
        day_data = all_data[date]

        # 方法 1: avg_rank（現行）
        vol_sorted = sorted(day_data.items(), key=lambda x: x[1]['total'], reverse=True)
        vol_rank = {code: i+1 for i, (code, _) in enumerate(vol_sorted)}

        # 金額排名（用 買超張數 × 股價 近似）
        amount_items = []
        for code, info in day_data.items():
            if info['total'] <= 0:
                continue
            price = (_price_cache.get(code, {}) or {}).get(date)
            if price:
                amount = info['total'] * price  # 張 × 元 = 近似金額
                amount_items.append((code, amount, info['total']))

        amount_sorted = sorted(amount_items, key=lambda x: x[1], reverse=True)
        amt_rank = {code: i+1 for i, (code, _, _) in enumerate(amount_sorted)}

        avg_rank_items = []
        for code, amount, total in amount_items:
            vr = vol_rank.get(code, 999)
            ar = amt_rank.get(code, 999)
            avg = (vr + ar) / 2
            avg_rank_items.append((code, avg, total))
        avg_rank_items.sort(key=lambda x: x[1])

        # 方法 2: buy_ratio（買超佔日均量）
        ratio_items = []
        for code, info in day_data.items():
            if info['total'] <= 0:
                continue
            avg_vol = avg_volume(code, date, trading_dates, 20)
            if avg_vol and avg_vol > 0:
                # 注意：T86 的 total 是千張，volume 是股。統一單位
                ratio = (info['total'] * 1000) / avg_vol * 100
                ratio_items.append((code, ratio, info['total']))

        ratio_items.sort(key=lambda x: x[1], reverse=True)

        # 計算各方法 TOP N 的 5 日報酬
        for method_name, ranked_list in [
            ('avg_rank', avg_rank_items),
            ('buy_ratio', ratio_items),
            ('volume_rank', [(c, info['total'], info['total']) for c, info in vol_sorted if info['total'] > 0][:50]),
            ('amount_rank', [(c, a, t) for c, a, t in amount_sorted]),
        ]:
            for top_n in [10, 20, 30]:
                for code, _, _ in ranked_list[:top_n]:
                    ret = forward_return(code, date, trading_dates, 5)
                    if ret is not None:
                        results[method_name][top_n].append(ret)

    # ===== 輸出比較 =====

    print("=" * 60)
    print("  TOP N 選股 → 5 日報酬比較")
    print("=" * 60)
    print()

    print(f"{'方法':<16} | {'TOP10':>20} | {'TOP20':>20} | {'TOP30':>20}")
    print(f"{'':16} | {'報酬    勝率  樣本':>20} | {'報酬    勝率  樣本':>20} | {'報酬    勝率  樣本':>20}")
    print("-" * 85)

    for method in ['avg_rank', 'buy_ratio', 'volume_rank', 'amount_rank']:
        row = f"{method:<16}"
        for top_n in [10, 20, 30]:
            rets = results[method][top_n]
            if rets:
                avg = sum(rets) / len(rets)
                wr = sum(1 for r in rets if r > 0) / len(rets) * 100
                row += f" | {avg:>+6.2f}% {wr:>5.1f}% {len(rets):>4}"
            else:
                row += f" | {'N/A':>20}"
        print(row)

    print()

    # ===== buy_ratio 分級分析 =====

    print("=" * 60)
    print("  buy_ratio（買超佔日均量%）分級 → 5 日報酬")
    print("=" * 60)
    print()

    ratio_buckets = defaultdict(list)

    for date in trading_dates:
        day_data = all_data[date]
        for code, info in day_data.items():
            if info['total'] <= 0:
                continue
            avg_vol = avg_volume(code, date, trading_dates, 20)
            if not avg_vol or avg_vol <= 0:
                continue
            ratio = (info['total'] * 1000) / avg_vol * 100

            ret = forward_return(code, date, trading_dates, 5)
            if ret is None:
                continue

            if ratio >= 50:
                ratio_buckets['佔比≥50%（超大手筆）'].append(ret)
            elif ratio >= 20:
                ratio_buckets['佔比20-50%（大手筆）'].append(ret)
            elif ratio >= 10:
                ratio_buckets['佔比10-20%（中等）'].append(ret)
            elif ratio >= 5:
                ratio_buckets['佔比5-10%（小量）'].append(ret)
            else:
                ratio_buckets['佔比<5%（微量）'].append(ret)

    print(f"{'佔比分級':<24} | {'平均報酬':>10} | {'勝率':>8} | {'樣本':>6}")
    print("-" * 55)
    for label in ['佔比≥50%（超大手筆）', '佔比20-50%（大手筆）', '佔比10-20%（中等）', '佔比5-10%（小量）', '佔比<5%（微量）']:
        rets = ratio_buckets.get(label, [])
        if rets:
            avg = sum(rets) / len(rets)
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            print(f"{label:<24} | {avg:>+9.2f}% | {wr:>6.1f}% | {len(rets):>6}")
    print()

    # ===== 最佳方法判定 =====

    print("=" * 60)
    print("  結論")
    print("=" * 60)
    print()

    # 比較 TOP20 的勝率
    for method in ['avg_rank', 'buy_ratio', 'volume_rank', 'amount_rank']:
        rets = results[method][20]
        if rets:
            avg = sum(rets) / len(rets)
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            print(f"  {method:<16} TOP20: {avg:+.2f}%, 勝率 {wr:.1f}%")

    # 找最佳
    best_method = max(
        ['avg_rank', 'buy_ratio', 'volume_rank', 'amount_rank'],
        key=lambda m: sum(1 for r in results[m][20] if r > 0) / len(results[m][20]) * 100 if results[m][20] else 0
    )
    print()
    print(f"  TOP20 勝率最高: {best_method}")

    # avg_rank vs buy_ratio 直接對比
    ar = results['avg_rank'][20]
    br = results['buy_ratio'][20]
    if ar and br:
        ar_wr = sum(1 for r in ar if r > 0) / len(ar) * 100
        br_wr = sum(1 for r in br if r > 0) / len(br) * 100
        diff = br_wr - ar_wr
        print()
        if diff > 2:
            print(f"  buy_ratio 勝率比 avg_rank 高 {diff:+.1f}% → 建議改用 buy_ratio")
        elif diff < -2:
            print(f"  avg_rank 勝率比 buy_ratio 高 {-diff:+.1f}% → 維持現行 avg_rank")
        else:
            print(f"  兩者差距 {diff:+.1f}%，差不多 → 可考慮並用")


if __name__ == "__main__":
    main()
