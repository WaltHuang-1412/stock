#!/usr/bin/env python3
"""
法人賺錢模式追蹤器 — 每天盤後自動更新

功能：
1. 掃描近 N 個交易日的法人交易週期
2. 把每個週期標記 success/fail（買完後 10 日是否正報酬）
3. 統計每個維度的近期勝率（滾動窗口）
4. 找出「當前有效模式」= 近期勝率最高的特徵組合
5. 輸出 data/strategy/pattern_today.json 給盤前讀取

盤前 Step 7 讀取方式：
- hot_patterns: 最近準的模式 → 符合的候選股加分
- cold_patterns: 最近不準的模式 → 符合的候選股降權
- best_combo: 最強組合特徵 → 優先找這種股票
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
STRATEGY_DIR = PROJECT_DIR / "data" / "strategy"


# ===== 數據載入 =====

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
                'dealer': info.get('dealer', 0),
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


# ===== 產業對照 =====

def load_industry_map():
    """從 tracking 檔案建立股票→產業對照"""
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


# ===== 週期偵測 =====

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

            # 10日後報酬
            end_idx = min(buy_end + 10, len(daily) - 1)
            end_price = daily[end_idx]['price']
            if not end_price:
                continue
            ret_10d = (end_price - avg_buy) / avg_buy * 100
            success = ret_10d > 0

            # 5日後報酬
            mid_idx = min(buy_end + 5, len(daily) - 1)
            mid_price = daily[mid_idx]['price']
            ret_5d = (mid_price - avg_buy) / avg_buy * 100 if mid_price else None

            # 外資/投信佔比
            foreign_buy = sum(daily[j]['foreign'] for j in range(buy_start, buy_end + 1))
            trust_buy = sum(daily[j]['trust'] for j in range(buy_start, buy_end + 1))
            foreign_pct = foreign_buy / cum_buy * 100 if cum_buy > 0 else 0
            trust_pct = trust_buy / cum_buy * 100 if cum_buy > 0 else 0

            # 出貨比
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
                'ret_5d': ret_5d,
                'ret_10d': ret_10d,
                'success': success,
                'foreign_pct': foreign_pct,
                'trust_pct': trust_pct,
                'sell_ratio': sell_ratio,
            })
        else:
            i += 1

    return cycles


# ===== 特徵標記 =====

def label_features(cycle, industry_map):
    """為每個週期標記所有特徵"""
    features = {}

    # 連買天數
    d = cycle['buy_days']
    if d <= 2:
        features['buy_days'] = '2天'
    elif d <= 3:
        features['buy_days'] = '3天'
    elif d <= 4:
        features['buy_days'] = '4天'
    elif d <= 5:
        features['buy_days'] = '5天'
    else:
        features['buy_days'] = '6天+'

    # 買超量
    v = cycle['cum_buy']
    if v >= 30000:
        features['volume'] = '30K+'
    elif v >= 10000:
        features['volume'] = '10K-30K'
    elif v >= 5000:
        features['volume'] = '5K-10K'
    else:
        features['volume'] = '<5K'

    # 累積期股價
    p = cycle['price_during']
    if p <= -2:
        features['stealth'] = '越買越跌'
    elif p <= 1:
        features['stealth'] = '偷偷買'
    elif p <= 5:
        features['stealth'] = '邊買邊漲'
    else:
        features['stealth'] = '追漲'

    # 主導者
    if cycle['trust_pct'] > 60:
        features['leader'] = '投信主導'
    elif cycle['foreign_pct'] > 60:
        features['leader'] = '外資主導'
    else:
        features['leader'] = '混合'

    # 出貨速度
    sr = cycle['sell_ratio']
    if sr >= 60:
        features['sell_speed'] = '快速出貨'
    elif sr > 0:
        features['sell_speed'] = '緩慢出貨'
    else:
        features['sell_speed'] = '沒出貨'

    # 產業
    features['industry'] = industry_map.get(cycle['stock'], '未知')

    return features


# ===== 主程式 =====

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"法人模式追蹤器 — {today}")
    print()

    all_data = load_all_t86()
    trading_dates = sorted(all_data.keys())
    print(f"交易日: {len(trading_dates)} 天")

    # 找活躍股
    stock_activity = defaultdict(int)
    for date in trading_dates:
        for code, info in all_data[date].items():
            if abs(info['total']) > 2000:
                stock_activity[code] += 1

    active_stocks = [c for c, _ in sorted(stock_activity.items(), key=lambda x: -x[1])[:100]]
    print(f"活躍股: {len(active_stocks)} 檔")

    # 抓股價
    print("取得股價...", flush=True)
    for i, code in enumerate(active_stocks):
        fetch_prices(code)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(active_stocks)}", flush=True)
            time.sleep(0.5)

    # 產業對照
    industry_map = load_industry_map()

    # 偵測所有週期
    print("偵測交易週期...", flush=True)
    all_cycles = []
    for code in active_stocks:
        cycles = detect_cycles(code, all_data, trading_dates)
        for c in cycles:
            c['features'] = label_features(c, industry_map)
        all_cycles.extend(cycles)

    print(f"共 {len(all_cycles)} 個週期")
    print()

    # ===== 統計每個特徵維度的勝率 =====

    feature_dims = ['buy_days', 'volume', 'stealth', 'leader', 'sell_speed', 'industry']
    dim_stats = {}

    for dim in feature_dims:
        groups = defaultdict(lambda: {'success': 0, 'fail': 0, 'total_ret': 0, 'cycles': []})
        for c in all_cycles:
            val = c['features'].get(dim, '未知')
            if c['success']:
                groups[val]['success'] += 1
            else:
                groups[val]['fail'] += 1
            groups[val]['total_ret'] += c['ret_10d']
            groups[val]['cycles'].append(c)

        dim_result = {}
        for val, stat in groups.items():
            total = stat['success'] + stat['fail']
            if total < 3:  # 至少3筆才有意義
                continue
            dim_result[val] = {
                'accuracy': round(stat['success'] / total * 100, 1),
                'avg_return': round(stat['total_ret'] / total, 2),
                'sample': total,
            }
        dim_stats[dim] = dim_result

    # ===== 找 hot / cold patterns =====

    hot_patterns = []
    cold_patterns = []

    for dim, results in dim_stats.items():
        for val, stat in results.items():
            if stat['sample'] < 3:
                continue
            entry = {
                'dimension': dim,
                'value': val,
                'accuracy': stat['accuracy'],
                'avg_return': stat['avg_return'],
                'sample': stat['sample'],
            }
            if stat['accuracy'] >= 55 and stat['avg_return'] > 0:
                hot_patterns.append(entry)
            elif stat['accuracy'] <= 35 or stat['avg_return'] < -3:
                cold_patterns.append(entry)

    hot_patterns.sort(key=lambda x: x['accuracy'], reverse=True)
    cold_patterns.sort(key=lambda x: x['accuracy'])

    # ===== 找最佳組合（兩兩特徵交叉）=====

    combos = []
    for c in all_cycles:
        f = c['features']
        # 產生所有兩兩組合 key
        keys = list(f.items())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                combo_key = f"{keys[i][0]}={keys[i][1]} + {keys[j][0]}={keys[j][1]}"
                combos.append((combo_key, c['success'], c['ret_10d']))

    combo_stats = defaultdict(lambda: {'success': 0, 'fail': 0, 'total_ret': 0})
    for key, success, ret in combos:
        if success:
            combo_stats[key]['success'] += 1
        else:
            combo_stats[key]['fail'] += 1
        combo_stats[key]['total_ret'] += ret

    best_combos = []
    for key, stat in combo_stats.items():
        total = stat['success'] + stat['fail']
        if total < 5:
            continue
        acc = stat['success'] / total * 100
        avg_ret = stat['total_ret'] / total
        if acc >= 55:
            best_combos.append({
                'combo': key,
                'accuracy': round(acc, 1),
                'avg_return': round(avg_ret, 2),
                'sample': total,
            })

    best_combos.sort(key=lambda x: x['accuracy'], reverse=True)

    # ===== 輸出 JSON =====

    output = {
        'date': today,
        'data_range': f"{trading_dates[0]}~{trading_dates[-1]}",
        'total_cycles': len(all_cycles),
        'overall_success_rate': round(sum(1 for c in all_cycles if c['success']) / len(all_cycles) * 100, 1),
        'dimension_stats': dim_stats,
        'hot_patterns': hot_patterns[:10],
        'cold_patterns': cold_patterns[:10],
        'best_combos': best_combos[:10],
        'worst_combos': sorted(
            [{'combo': k, 'accuracy': round(v['success']/(v['success']+v['fail'])*100,1),
              'avg_return': round(v['total_ret']/(v['success']+v['fail']),2),
              'sample': v['success']+v['fail']}
             for k, v in combo_stats.items()
             if v['success']+v['fail'] >= 5 and v['success']/(v['success']+v['fail']) < 0.35],
            key=lambda x: x['accuracy']
        )[:10],
    }

    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = STRATEGY_DIR / "pattern_today.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # ===== 人看的摘要 =====

    print("=" * 60)
    print(f"  法人當前賺錢模式 ({today})")
    print(f"  數據: {trading_dates[0]}~{trading_dates[-1]}, {len(all_cycles)} 個週期")
    print("=" * 60)
    print()

    print("HOT (最近在賺的模式):")
    for p in hot_patterns[:8]:
        print(f"  {p['dimension']}={p['value']}: {p['accuracy']}% ({p['avg_return']:+.2f}%, {p['sample']}筆)")
    print()

    print("COLD (最近在虧的模式):")
    for p in cold_patterns[:8]:
        print(f"  {p['dimension']}={p['value']}: {p['accuracy']}% ({p['avg_return']:+.2f}%, {p['sample']}筆)")
    print()

    print("BEST COMBO (最強組合):")
    for c in best_combos[:5]:
        print(f"  {c['combo']}: {c['accuracy']}% ({c['avg_return']:+.2f}%, {c['sample']}筆)")
    print()

    worst = output['worst_combos']
    if worst:
        print("WORST COMBO (最差組合):")
        for c in worst[:5]:
            print(f"  {c['combo']}: {c['accuracy']}% ({c['avg_return']:+.2f}%, {c['sample']}筆)")
        print()

    print(f"已存: {out_path}")


if __name__ == "__main__":
    main()
