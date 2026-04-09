#!/usr/bin/env python3
"""
回測價格位置規則：歷史推薦加上52週位置加減分，準確率有沒有提升
"""

import sys
import os
import io
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"

_price_cache = {}

def fetch_stock_data(code, days=400):
    if code in _price_cache:
        return _price_cache[code]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
    params = {"interval": "1d", "range": f"{days}d"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        data = r.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        prices = []
        for ts, close, high, low in zip(timestamps, quote['close'], quote['high'], quote['low']):
            if close is not None:
                dt = datetime.fromtimestamp(ts)
                prices.append({
                    'date': dt.strftime("%Y-%m-%d"),
                    'close': close,
                    'high': high or close,
                    'low': low or close,
                })
        _price_cache[code] = prices
        return prices
    except Exception:
        _price_cache[code] = []
        return []


def get_position_at_date(code, target_date):
    """取得某日期時的52週位置"""
    prices = _price_cache.get(code, [])
    if not prices:
        return None

    # 找到 target_date 之前的價格
    past = [p for p in prices if p['date'] <= target_date]
    if len(past) < 60:
        return None

    current = past[-1]['close']
    # 近 240 天（約52週）的高低點
    lookback = past[-240:] if len(past) >= 240 else past
    high_52w = max(p['high'] for p in lookback)
    low_52w = min(p['low'] for p in lookback)

    price_range = high_52w - low_52w
    if price_range <= 0:
        return None

    position_pct = (current - low_52w) / price_range * 100

    if position_pct >= 90:
        return {'position_pct': position_pct, 'label': '極高', 'adj': -5}
    elif position_pct >= 75:
        return {'position_pct': position_pct, 'label': '偏高', 'adj': -3}
    elif position_pct >= 40:
        return {'position_pct': position_pct, 'label': '中間', 'adj': 0}
    elif position_pct >= 20:
        return {'position_pct': position_pct, 'label': '偏低', 'adj': 3}
    else:
        return {'position_pct': position_pct, 'label': '極低', 'adj': 5}


def main():
    print("=" * 70)
    print("  價格位置規則回測")
    print("=" * 70)
    print()

    # 載入所有已結算推薦
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
            all_recs.append({
                'date': date_str,
                'code': rec.get('stock_code') or rec.get('symbol', ''),
                'name': rec.get('stock_name') or rec.get('name', ''),
                'score': rec.get('score', 0),
                'result': result,
            })

    print(f"已結算推薦: {len(all_recs)} 筆")
    success = sum(1 for r in all_recs if r['result'] == 'success')
    print(f"原始準確率: {success}/{len(all_recs)} = {success/len(all_recs)*100:.1f}%")
    print()

    # 抓股價
    codes = list(set(r['code'] for r in all_recs))
    print(f"取得 {len(codes)} 檔股價...")
    for i, code in enumerate(codes):
        fetch_stock_data(code)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(codes)}", flush=True)
            time.sleep(0.5)
    print()

    # 對每筆推薦計算位置
    position_groups = defaultdict(list)
    adj_recs = []

    for rec in all_recs:
        pos = get_position_at_date(rec['code'], rec['date'])
        if not pos:
            continue

        rec['position'] = pos['label']
        rec['position_pct'] = pos['position_pct']
        rec['adj'] = pos['adj']
        rec['adj_score'] = rec['score'] + pos['adj']
        adj_recs.append(rec)
        position_groups[pos['label']].append(rec)

    print(f"有位置資料: {len(adj_recs)} 筆")
    print()

    # 各位置準確率
    print("=" * 60)
    print("  各價格位置的準確率")
    print("=" * 60)
    print()

    print(f"{'位置':<8} {'準確率':>8} {'成功':>6} {'失敗':>6} {'樣本':>6}")
    print("-" * 40)

    for label in ['極低', '偏低', '中間', '偏高', '極高']:
        recs = position_groups.get(label, [])
        if not recs:
            continue
        s = sum(1 for r in recs if r['result'] == 'success')
        f = len(recs) - s
        acc = s / len(recs) * 100
        print(f"{label:<8} {acc:>6.1f}% {s:>6} {f:>6} {len(recs):>6}")

    print()

    # 調整後影響
    print("=" * 60)
    print("  調整後影響")
    print("=" * 60)
    print()

    # 被排除的（原>=65，調整後<65）
    excluded = [r for r in adj_recs if r['score'] >= 65 and r['adj_score'] < 65]
    excluded_s = sum(1 for r in excluded if r['result'] == 'success')
    excluded_f = len(excluded) - excluded_s
    print(f"會被排除: {len(excluded)} 檔 (success={excluded_s}, fail={excluded_f})")
    for r in excluded:
        print(f"  {r['date']} {r['code']} {r['name']} {r['score']}→{r['adj_score']} {r['position']} {r['result']}")
    print()

    # 加分 vs 扣分 vs 不變
    up = [r for r in adj_recs if r['adj'] > 0]
    down = [r for r in adj_recs if r['adj'] < 0]
    neutral = [r for r in adj_recs if r['adj'] == 0]

    for label, group in [('加分', up), ('扣分', down), ('不變', neutral)]:
        if group:
            s = sum(1 for r in group if r['result'] == 'success')
            acc = s / len(group) * 100
            print(f"{label}: {acc:.1f}% ({s}/{len(group)})")

    print()

    # 整體影響
    remaining = [r for r in adj_recs if r['adj_score'] >= 65]
    remaining_s = sum(1 for r in remaining if r['result'] == 'success')
    orig_total = len(adj_recs)
    orig_s = sum(1 for r in adj_recs if r['result'] == 'success')
    orig_acc = orig_s / orig_total * 100
    new_acc = remaining_s / len(remaining) * 100 if remaining else 0

    print("=" * 60)
    print(f"  原始: {orig_s}/{orig_total} = {orig_acc:.1f}%")
    print(f"  新規則: {remaining_s}/{len(remaining)} = {new_acc:.1f}%")
    print(f"  變化: {new_acc - orig_acc:+.1f}% (排除 {orig_total - len(remaining)} 檔)")
    print("=" * 60)


if __name__ == "__main__":
    main()
