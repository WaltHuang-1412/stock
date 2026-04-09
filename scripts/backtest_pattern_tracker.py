#!/usr/bin/env python3
"""
驗證模式追蹤器：用前半段數據的 pattern 選後半段的股票，看準不準

方法：
1. 把 32 個交易日切成兩半：前 16 天（訓練）、後 16 天（測試）
2. 用前 16 天跑模式追蹤器，找出 hot/cold patterns
3. 看後 16 天的法人交易週期，符合 hot 的勝率 vs 符合 cold 的勝率
4. 跟「不用追蹤器」的基準線比較
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

def fetch_prices(stock_code, days=120):
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
        prices = {}
        for ts, close in zip(timestamps, closes):
            if close is not None:
                dt = datetime.fromtimestamp(ts)
                prices[dt.strftime("%Y%m%d")] = close
        _price_cache[stock_code] = prices
        return prices
    except Exception:
        _price_cache[stock_code] = {}
        return {}


def load_industry_map():
    tracking_dir = PROJECT_DIR / "data" / "tracking"
    mapping = {}
    for fp in sorted(tracking_dir.glob("tracking_202*.json")):
        if 'example' in fp.name:
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for rec in data.get('recommendations', []) + data.get('holding_tracking', []):
            code = rec.get('stock_code', '')
            industry = rec.get('industry', '')
            if isinstance(industry, dict):
                industry = industry.get('sector', '')
            if code and industry:
                mapping[code] = industry
    return mapping


def detect_cycles(stock_code, all_data, trading_dates):
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return []

    daily = []
    for date in trading_dates:
        day_data = all_data.get(date, {})
        stock_info = day_data.get(stock_code, {})
        daily.append({
            'date': date,
            'total': stock_info.get('total', 0),
            'foreign': stock_info.get('foreign', 0),
            'trust': stock_info.get('trust', 0),
            'price': prices.get(date),
        })

    cycles = []
    i = 0
    while i < len(daily):
        if daily[i]['total'] > 0:
            buy_start = i
            cum_buy = 0
            while i < len(daily) and daily[i]['total'] > 0:
                cum_buy += daily[i]['total']
                i += 1
            buy_end = i - 1
            buy_days = buy_end - buy_start + 1

            if buy_days < 2:
                continue

            buy_prices = [daily[j]['price'] for j in range(buy_start, buy_end + 1) if daily[j]['price']]
            if not buy_prices:
                continue
            avg_buy = sum(buy_prices) / len(buy_prices)
            price_during = (buy_prices[-1] - buy_prices[0]) / buy_prices[0] * 100 if len(buy_prices) > 1 and buy_prices[0] else 0

            end_idx = min(buy_end + 10, len(daily) - 1)
            end_price = daily[end_idx]['price']
            if not end_price:
                continue
            ret_10d = (end_price - avg_buy) / avg_buy * 100
            success = ret_10d > 0

            foreign_buy = sum(daily[j]['foreign'] for j in range(buy_start, buy_end + 1))
            trust_buy = sum(daily[j]['trust'] for j in range(buy_start, buy_end + 1))
            foreign_pct = foreign_buy / cum_buy * 100 if cum_buy > 0 else 0
            trust_pct = trust_buy / cum_buy * 100 if cum_buy > 0 else 0

            sell_start = buy_end + 1
            cum_sell = 0
            for j in range(sell_start, min(sell_start + 10, len(daily))):
                if daily[j]['total'] < 0:
                    cum_sell += abs(daily[j]['total'])
            sell_ratio = cum_sell / cum_buy * 100 if cum_buy > 0 else 0

            cycles.append({
                'stock': stock_code,
                'buy_start': daily[buy_start]['date'],
                'buy_end': daily[buy_end]['date'],
                'buy_days': buy_days,
                'cum_buy': cum_buy,
                'price_during': price_during,
                'ret_10d': ret_10d,
                'success': success,
                'foreign_pct': foreign_pct,
                'trust_pct': trust_pct,
                'sell_ratio': sell_ratio,
            })
        else:
            i += 1

    return cycles


def label_features(cycle, industry_map):
    features = {}
    d = cycle['buy_days']
    features['buy_days'] = '2天' if d <= 2 else '3天' if d <= 3 else '4天' if d <= 4 else '5天' if d <= 5 else '6天+'

    v = cycle['cum_buy']
    features['volume'] = '30K+' if v >= 30000 else '10K-30K' if v >= 10000 else '5K-10K' if v >= 5000 else '<5K'

    p = cycle['price_during']
    features['stealth'] = '越買越跌' if p <= -2 else '偷偷買' if p <= 1 else '邊買邊漲' if p <= 5 else '追漲'

    features['leader'] = '投信主導' if cycle['trust_pct'] > 60 else '外資主導' if cycle['foreign_pct'] > 60 else '混合'

    sr = cycle['sell_ratio']
    features['sell_speed'] = '快速出貨' if sr >= 60 else '緩慢出貨' if sr > 0 else '沒出貨'

    features['industry'] = industry_map.get(cycle['stock'], '未知')
    return features


def find_hot_cold(cycles, min_sample=3):
    """從一批週期中找出 hot/cold patterns"""
    feature_dims = ['buy_days', 'volume', 'stealth', 'leader', 'sell_speed', 'industry']
    hot = {}
    cold = {}

    for dim in feature_dims:
        groups = defaultdict(lambda: {'s': 0, 'f': 0})
        for c in cycles:
            val = c['features'].get(dim, '未知')
            if c['success']:
                groups[val]['s'] += 1
            else:
                groups[val]['f'] += 1

        for val, stat in groups.items():
            total = stat['s'] + stat['f']
            if total < min_sample:
                continue
            acc = stat['s'] / total * 100

            key = f"{dim}={val}"
            if acc >= 60:
                hot[key] = acc
            elif acc <= 35:
                cold[key] = acc

    return hot, cold


def main():
    print("=" * 70)
    print("  模式追蹤器驗證：前半段訓練 → 後半段測試")
    print("=" * 70)
    print()

    all_data = load_all_t86()
    all_dates = sorted(all_data.keys())
    print(f"交易日: {len(all_dates)} 天 ({all_dates[0]}~{all_dates[-1]})")

    # 切半
    mid = len(all_dates) // 2
    train_dates = all_dates[:mid]
    test_dates = all_dates[mid:]
    print(f"訓練期: {train_dates[0]}~{train_dates[-1]} ({len(train_dates)}天)")
    print(f"測試期: {test_dates[0]}~{test_dates[-1]} ({len(test_dates)}天)")
    print()

    # 收集活躍股
    stock_activity = defaultdict(int)
    for date in all_dates:
        for code, info in all_data[date].items():
            if abs(info['total']) > 2000:
                stock_activity[code] += 1

    active_stocks = [c for c, _ in sorted(stock_activity.items(), key=lambda x: -x[1])[:100]]
    print(f"活躍股: {len(active_stocks)} 檔")

    # 抓股價
    print("取得股價...")
    for i, code in enumerate(active_stocks):
        fetch_prices(code)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(active_stocks)}", flush=True)
            time.sleep(0.5)

    industry_map = load_industry_map()

    # ===== 訓練期：偵測週期 + 找 hot/cold =====
    print()
    print("訓練期分析...")
    train_cycles = []
    for code in active_stocks:
        cycles = detect_cycles(code, all_data, train_dates)
        for c in cycles:
            c['features'] = label_features(c, industry_map)
        train_cycles.extend(cycles)

    print(f"  訓練期週期: {len(train_cycles)}")
    train_success = sum(1 for c in train_cycles if c['success'])
    print(f"  訓練期成功率: {train_success}/{len(train_cycles)} = {train_success/len(train_cycles)*100:.1f}%")

    hot, cold = find_hot_cold(train_cycles)
    print(f"  HOT patterns: {len(hot)}")
    for k, v in sorted(hot.items(), key=lambda x: -x[1])[:8]:
        print(f"    {k}: {v:.0f}%")
    print(f"  COLD patterns: {len(cold)}")
    for k, v in sorted(cold.items(), key=lambda x: x[1])[:8]:
        print(f"    {k}: {v:.0f}%")
    print()

    # ===== 測試期：用訓練期的 hot/cold 評估 =====
    print("測試期驗證...")
    test_cycles = []
    for code in active_stocks:
        cycles = detect_cycles(code, all_data, test_dates)
        for c in cycles:
            c['features'] = label_features(c, industry_map)
        test_cycles.extend(cycles)

    print(f"  測試期週期: {len(test_cycles)}")
    test_success = sum(1 for c in test_cycles if c['success'])
    test_baseline = test_success / len(test_cycles) * 100 if test_cycles else 0
    print(f"  測試期基準成功率: {test_success}/{len(test_cycles)} = {test_baseline:.1f}%")
    print()

    # 分類：符合 hot / 符合 cold / 都不符合
    hot_match = []
    cold_match = []
    neutral = []

    for c in test_cycles:
        is_hot = False
        is_cold = False

        for dim in ['buy_days', 'volume', 'stealth', 'leader', 'sell_speed', 'industry']:
            key = f"{dim}={c['features'].get(dim, '')}"
            if key in hot:
                is_hot = True
            if key in cold:
                is_cold = True

        if is_hot and not is_cold:
            hot_match.append(c)
        elif is_cold and not is_hot:
            cold_match.append(c)
        elif is_hot and is_cold:
            neutral.append(c)  # 同時符合 hot 和 cold，不好判斷
        else:
            neutral.append(c)

    def acc(lst):
        if not lst:
            return 0, 0
        s = sum(1 for c in lst if c['success'])
        return s / len(lst) * 100, len(lst)

    hot_acc, hot_n = acc(hot_match)
    cold_acc, cold_n = acc(cold_match)
    neutral_acc, neutral_n = acc(neutral)

    print("=" * 60)
    print("  測試期結果（用訓練期的 hot/cold 分類）")
    print("=" * 60)
    print()
    print(f"  基準線（全部）: {test_baseline:.1f}% ({len(test_cycles)})")
    print(f"  符合 HOT:      {hot_acc:.1f}% ({hot_n})")
    print(f"  符合 COLD:     {cold_acc:.1f}% ({cold_n})")
    print(f"  都不符合:      {neutral_acc:.1f}% ({neutral_n})")
    print()

    # 判斷有效性
    print("=" * 60)
    print("  結論")
    print("=" * 60)
    print()

    hot_lift = hot_acc - test_baseline
    cold_lift = test_baseline - cold_acc

    print(f"  HOT 提升: {hot_lift:+.1f}% （{hot_acc:.1f}% vs 基準{test_baseline:.1f}%）")
    print(f"  COLD 壓低: {cold_lift:+.1f}% （基準{test_baseline:.1f}% vs {cold_acc:.1f}%）")
    print()

    if hot_lift > 3 and cold_lift > 3:
        print("  --> 模式追蹤器有效：HOT 能選出更好的，COLD 能避開更差的")
    elif hot_lift > 3:
        print("  --> HOT 有效但 COLD 區分力不足，建議只用加分不用扣分")
    elif cold_lift > 3:
        print("  --> COLD 有效但 HOT 區分力不足，建議只用扣分不用加分")
    else:
        print("  --> 模式追蹤器無效：無法有效區分好壞，建議移除加減分")

    # 滾動驗證（多切幾次看穩不穩定）
    print()
    print("=" * 60)
    print("  穩定性檢查（滾動切分）")
    print("=" * 60)
    print()

    window = 10  # 訓練窗口
    for start in range(0, len(all_dates) - window - 5, 5):
        t_dates = all_dates[start:start + window]
        v_dates = all_dates[start + window:start + window + 8]

        if len(v_dates) < 5:
            continue

        t_cycles = []
        for code in active_stocks:
            for c in detect_cycles(code, all_data, t_dates):
                c['features'] = label_features(c, industry_map)
                t_cycles.append(c)

        if len(t_cycles) < 20:
            continue

        h, c_patterns = find_hot_cold(t_cycles, min_sample=3)

        v_cycles = []
        for code in active_stocks:
            for vc in detect_cycles(code, all_data, v_dates):
                vc['features'] = label_features(vc, industry_map)
                v_cycles.append(vc)

        if len(v_cycles) < 10:
            continue

        h_match = [vc for vc in v_cycles if any(f"{d}={vc['features'].get(d,'')}" in h for d in ['buy_days','volume','stealth','leader','sell_speed','industry']) and not any(f"{d}={vc['features'].get(d,'')}" in c_patterns for d in ['buy_days','volume','stealth','leader','sell_speed','industry'])]
        c_match = [vc for vc in v_cycles if any(f"{d}={vc['features'].get(d,'')}" in c_patterns for d in ['buy_days','volume','stealth','leader','sell_speed','industry']) and not any(f"{d}={vc['features'].get(d,'')}" in h for d in ['buy_days','volume','stealth','leader','sell_speed','industry'])]

        base = sum(1 for vc in v_cycles if vc['success']) / len(v_cycles) * 100
        h_acc = sum(1 for vc in h_match if vc['success']) / len(h_match) * 100 if h_match else 0
        c_acc = sum(1 for vc in c_match if vc['success']) / len(c_match) * 100 if c_match else 0

        print(f"  {t_dates[0]}~{t_dates[-1]} → {v_dates[0]}~{v_dates[-1]}: 基準{base:.0f}% HOT{h_acc:.0f}%({len(h_match)}) COLD{c_acc:.0f}%({len(c_match)})")


if __name__ == "__main__":
    main()
