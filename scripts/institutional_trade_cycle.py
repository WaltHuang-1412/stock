#!/usr/bin/env python3
"""
法人交易週期分析 — 找出法人的完整買賣模式

不是看「跟法人買會不會賺」，而是看「法人自己是怎麼操作的」：
1. 累積期：連續買了幾天？買了多少？股價有沒有動？
2. 拉抬期：什麼時候股價開始漲？漲多少？
3. 出貨期：什麼時候開始賣？賣多久？
4. 獲利：整個週期法人賺了多少？

目標：找出可以提前偵測的 pattern
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


# ===== 交易週期偵測 =====

def detect_trade_cycles(stock_code, all_data, trading_dates):
    """偵測法人的完整買→賣週期"""
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return []

    # 建立每日法人淨買超序列
    daily = []
    for date in trading_dates:
        day_data = all_data.get(date, {})
        stock_info = day_data.get(stock_code, {})
        total = stock_info.get('total', 0)
        foreign = stock_info.get('foreign', 0)
        trust = stock_info.get('trust', 0)
        price = prices.get(date)
        daily.append({
            'date': date,
            'total': total,
            'foreign': foreign,
            'trust': trust,
            'price': price,
        })

    # 偵測週期：連續買超 → 轉為賣超
    cycles = []
    i = 0
    while i < len(daily):
        # 找買超起點
        if daily[i]['total'] > 0:
            buy_start = i

            # Phase 1: 累積期（連續買超）
            cum_buy = 0
            while i < len(daily) and daily[i]['total'] > 0:
                cum_buy += daily[i]['total']
                i += 1
            buy_end = i - 1
            buy_days = buy_end - buy_start + 1

            if buy_days < 2:  # 至少連買 2 天才算
                continue

            # 買入均價估算（用累積期間的平均收盤價）
            buy_prices = [daily[j]['price'] for j in range(buy_start, buy_end + 1) if daily[j]['price']]
            if not buy_prices:
                continue
            avg_buy_price = sum(buy_prices) / len(buy_prices)

            # Phase 2: 持有/拉抬期（不管買賣，看股價表現）
            peak_price = avg_buy_price
            peak_date_idx = buy_end
            for j in range(buy_end + 1, min(buy_end + 21, len(daily))):  # 最多看 20 天
                if daily[j]['price'] and daily[j]['price'] > peak_price:
                    peak_price = daily[j]['price']
                    peak_date_idx = j

            # Phase 3: 出貨期（買完之後的賣超）
            sell_start = buy_end + 1
            cum_sell = 0
            sell_days = 0
            j = sell_start
            while j < min(sell_start + 15, len(daily)):
                if daily[j]['total'] < 0:
                    cum_sell += abs(daily[j]['total'])
                    sell_days += 1
                j += 1

            # 計算報酬
            end_idx = min(buy_end + 10, len(daily) - 1)
            end_price = daily[end_idx]['price'] if daily[end_idx]['price'] else avg_buy_price
            holding_return = (peak_price - avg_buy_price) / avg_buy_price * 100
            actual_return = (end_price - avg_buy_price) / avg_buy_price * 100

            # 外資 vs 投信拆解
            foreign_buy = sum(daily[j]['foreign'] for j in range(buy_start, buy_end + 1))
            trust_buy = sum(daily[j]['trust'] for j in range(buy_start, buy_end + 1))

            cycles.append({
                'stock': stock_code,
                'buy_start': daily[buy_start]['date'],
                'buy_end': daily[buy_end]['date'],
                'buy_days': buy_days,
                'cum_buy': cum_buy,
                'avg_buy_price': avg_buy_price,
                'peak_price': peak_price,
                'peak_date': daily[peak_date_idx]['date'],
                'holding_return': holding_return,
                'actual_10d_return': actual_return,
                'sell_days': sell_days,
                'cum_sell': cum_sell,
                'sell_ratio': cum_sell / cum_buy * 100 if cum_buy > 0 else 0,
                'foreign_pct': foreign_buy / cum_buy * 100 if cum_buy > 0 else 0,
                'trust_pct': trust_buy / cum_buy * 100 if cum_buy > 0 else 0,
                'price_during_buy': (buy_prices[-1] - buy_prices[0]) / buy_prices[0] * 100 if len(buy_prices) > 1 else 0,
            })
        else:
            i += 1

    return cycles


# ===== 主分析 =====

def main():
    print("=" * 70)
    print("  法人交易週期分析 — 找出法人的賺錢模式")
    print("=" * 70)
    print()

    all_data = load_all_t86()
    trading_dates = sorted(all_data.keys())
    print(f"交易日: {len(trading_dates)} 天 ({trading_dates[0]}~{trading_dates[-1]})")

    # 找最常被法人操作的股票
    stock_activity = defaultdict(int)
    for date in trading_dates:
        for code, info in all_data[date].items():
            if abs(info['total']) > 3000:
                stock_activity[code] += 1

    active_stocks = sorted(stock_activity.items(), key=lambda x: -x[1])[:80]
    codes = [c for c, _ in active_stocks]
    print(f"活躍股: {len(codes)} 檔")
    print()

    # 抓股價
    print("取得股價...")
    for i, code in enumerate(codes):
        fetch_prices(code)
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(codes)}", flush=True)
            time.sleep(0.5)
    print()

    # 偵測所有週期
    print("偵測交易週期...")
    all_cycles = []
    for code in codes:
        cycles = detect_trade_cycles(code, all_data, trading_dates)
        all_cycles.extend(cycles)
    print(f"找到 {len(all_cycles)} 個交易週期")
    print()

    # ===== 分析 1: 累積天數 vs 報酬 =====
    print("=" * 60)
    print("  分析 1: 法人累積幾天最賺？")
    print("=" * 60)
    print()

    by_days = defaultdict(list)
    for c in all_cycles:
        d = min(c['buy_days'], 10)
        by_days[d].append(c)

    print(f"{'累積天數':<8} {'平均報酬':>10} {'最高報酬':>10} {'勝率':>8} {'累積期漲幅':>12} {'樣本':>6}")
    print("-" * 60)
    for d in sorted(by_days.keys()):
        cycles = by_days[d]
        rets = [c['actual_10d_return'] for c in cycles]
        peaks = [c['holding_return'] for c in cycles]
        during = [c['price_during_buy'] for c in cycles]
        avg = sum(rets) / len(rets)
        avg_peak = sum(peaks) / len(peaks)
        avg_during = sum(during) / len(during)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        label = f"{d}天" if d < 10 else "10+天"
        print(f"{label:<8} {avg:>+9.2f}% {avg_peak:>+9.2f}% {wr:>6.1f}% {avg_during:>+10.2f}% {len(rets):>6}")
    print()

    # ===== 分析 2: 累積量 vs 報酬 =====
    print("=" * 60)
    print("  分析 2: 法人買多少最賺？")
    print("=" * 60)
    print()

    by_volume = defaultdict(list)
    for c in all_cycles:
        v = c['cum_buy']
        if v >= 50000:
            by_volume['50K+'].append(c)
        elif v >= 20000:
            by_volume['20K-50K'].append(c)
        elif v >= 10000:
            by_volume['10K-20K'].append(c)
        elif v >= 5000:
            by_volume['5K-10K'].append(c)
        else:
            by_volume['<5K'].append(c)

    print(f"{'累積量':<12} {'10日報酬':>10} {'最高報酬':>10} {'勝率':>8} {'樣本':>6}")
    print("-" * 50)
    for label in ['50K+', '20K-50K', '10K-20K', '5K-10K', '<5K']:
        cycles = by_volume.get(label, [])
        if not cycles:
            continue
        rets = [c['actual_10d_return'] for c in cycles]
        peaks = [c['holding_return'] for c in cycles]
        avg = sum(rets) / len(rets)
        avg_peak = sum(peaks) / len(peaks)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        print(f"{label:<12} {avg:>+9.2f}% {avg_peak:>+9.2f}% {wr:>6.1f}% {len(rets):>6}")
    print()

    # ===== 分析 3: 累積期股價漲跌 vs 後續報酬 =====
    print("=" * 60)
    print("  分析 3: 法人偷偷買（股價沒動）vs 邊買邊漲")
    print("=" * 60)
    print()

    by_stealth = defaultdict(list)
    for c in all_cycles:
        p = c['price_during_buy']
        if p <= -2:
            by_stealth['越買越跌(<-2%)'].append(c)
        elif p <= 1:
            by_stealth['偷偷買(-2~+1%)'].append(c)
        elif p <= 5:
            by_stealth['邊買邊漲(+1~+5%)'].append(c)
        else:
            by_stealth['追漲(>+5%)'].append(c)

    print(f"{'模式':<22} {'10日報酬':>10} {'勝率':>8} {'樣本':>6}")
    print("-" * 50)
    for label in ['越買越跌(<-2%)', '偷偷買(-2~+1%)', '邊買邊漲(+1~+5%)', '追漲(>+5%)']:
        cycles = by_stealth.get(label, [])
        if not cycles:
            continue
        rets = [c['actual_10d_return'] for c in cycles]
        avg = sum(rets) / len(rets)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        print(f"{label:<22} {avg:>+9.2f}% {wr:>6.1f}% {len(rets):>6}")
    print()

    # ===== 分析 4: 外資主導 vs 投信主導 =====
    print("=" * 60)
    print("  分析 4: 外資主導 vs 投信主導的週期")
    print("=" * 60)
    print()

    by_leader = defaultdict(list)
    for c in all_cycles:
        if c['foreign_pct'] > 60:
            by_leader['外資主導(>60%)'].append(c)
        elif c['trust_pct'] > 60:
            by_leader['投信主導(>60%)'].append(c)
        else:
            by_leader['混合買超'].append(c)

    print(f"{'主導者':<18} {'10日報酬':>10} {'最高報酬':>10} {'勝率':>8} {'樣本':>6}")
    print("-" * 55)
    for label in ['外資主導(>60%)', '投信主導(>60%)', '混合買超']:
        cycles = by_leader.get(label, [])
        if not cycles:
            continue
        rets = [c['actual_10d_return'] for c in cycles]
        peaks = [c['holding_return'] for c in cycles]
        avg = sum(rets) / len(rets)
        avg_peak = sum(peaks) / len(peaks)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        print(f"{label:<18} {avg:>+9.2f}% {avg_peak:>+9.2f}% {wr:>6.1f}% {len(rets):>6}")
    print()

    # ===== 分析 5: 出貨速度 =====
    print("=" * 60)
    print("  分析 5: 買完之後出貨速度")
    print("=" * 60)
    print()

    by_sell = defaultdict(list)
    for c in all_cycles:
        sr = c['sell_ratio']
        if sr >= 80:
            by_sell['快速出貨(≥80%)'].append(c)
        elif sr >= 40:
            by_sell['部分出貨(40-80%)'].append(c)
        elif sr > 0:
            by_sell['微量出貨(<40%)'].append(c)
        else:
            by_sell['沒有出貨(0%)'].append(c)

    print(f"{'出貨比例':<20} {'累積期漲幅':>12} {'10日報酬':>10} {'樣本':>6}")
    print("-" * 50)
    for label in ['快速出貨(≥80%)', '部分出貨(40-80%)', '微量出貨(<40%)', '沒有出貨(0%)']:
        cycles = by_sell.get(label, [])
        if not cycles:
            continue
        rets = [c['actual_10d_return'] for c in cycles]
        during = [c['price_during_buy'] for c in cycles]
        avg = sum(rets) / len(rets)
        avg_during = sum(during) / len(during)
        print(f"{label:<20} {avg_during:>+10.2f}% {avg:>+9.2f}% {len(rets):>6}")
    print()

    # ===== 分析 6: 最佳組合 =====
    print("=" * 60)
    print("  分析 6: 最賺錢的法人模式組合")
    print("=" * 60)
    print()

    # 偷偷買 + 連買3天以上 + 外資主導
    golden = [c for c in all_cycles
              if c['price_during_buy'] <= 1  # 股價沒動
              and c['buy_days'] >= 3          # 至少3天
              and c['foreign_pct'] > 50]      # 外資為主

    trapped = [c for c in all_cycles
               if c['price_during_buy'] > 5    # 邊買邊漲
               and c['sell_ratio'] > 50]        # 買完就賣

    print(f"黃金模式（偷偷買+3天+外資）: ", end="")
    if golden:
        rets = [c['actual_10d_return'] for c in golden]
        avg = sum(rets) / len(rets)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        print(f"平均 {avg:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(golden)}")
    else:
        print("無樣本")

    print(f"陷阱模式（追漲+快出貨）: ", end="")
    if trapped:
        rets = [c['actual_10d_return'] for c in trapped]
        avg = sum(rets) / len(rets)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        print(f"平均 {avg:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(trapped)}")
    else:
        print("無樣本")

    print()

    # ===== 分析 7: 具體案例 =====
    print("=" * 60)
    print("  最成功的 10 個交易週期")
    print("=" * 60)
    print()

    top_cycles = sorted(all_cycles, key=lambda c: c['holding_return'], reverse=True)[:10]
    print(f"{'股票':>6} {'買入期間':<22} {'天數':>4} {'累計買':>8} {'累積漲幅':>10} {'最高報酬':>10} {'外資%':>6}")
    print("-" * 75)
    for c in top_cycles:
        print(f"{c['stock']:>6} {c['buy_start']}~{c['buy_end']} {c['buy_days']:>4} {c['cum_buy']:>+8,} {c['price_during_buy']:>+9.1f}% {c['holding_return']:>+9.1f}% {c['foreign_pct']:>5.0f}%")
    print()

    print("=" * 60)
    print("  最失敗的 10 個交易週期")
    print("=" * 60)
    print()

    worst_cycles = sorted(all_cycles, key=lambda c: c['holding_return'])[:10]
    print(f"{'股票':>6} {'買入期間':<22} {'天數':>4} {'累計買':>8} {'累積漲幅':>10} {'最高報酬':>10} {'外資%':>6}")
    print("-" * 75)
    for c in worst_cycles:
        print(f"{c['stock']:>6} {c['buy_start']}~{c['buy_end']} {c['buy_days']:>4} {c['cum_buy']:>+8,} {c['price_during_buy']:>+9.1f}% {c['holding_return']:>+9.1f}% {c['foreign_pct']:>5.0f}%")
    print()

    # ===== 總結 =====
    print("=" * 60)
    print("  法人賺錢模式總結")
    print("=" * 60)
    print()

    stealth = by_stealth.get('偷偷買(-2~+1%)', [])
    chase = by_stealth.get('追漲(>+5%)', [])
    if stealth and chase:
        s_avg = sum(c['actual_10d_return'] for c in stealth) / len(stealth)
        c_avg = sum(c['actual_10d_return'] for c in chase) / len(chase)
        print(f"  1. 偷偷買 {s_avg:+.2f}% vs 追漲 {c_avg:+.2f}% → {'偷偷買贏' if s_avg > c_avg else '追漲贏'}")

    foreign_led = by_leader.get('外資主導(>60%)', [])
    trust_led = by_leader.get('投信主導(>60%)', [])
    if foreign_led and trust_led:
        f_avg = sum(c['actual_10d_return'] for c in foreign_led) / len(foreign_led)
        t_avg = sum(c['actual_10d_return'] for c in trust_led) / len(trust_led)
        print(f"  2. 外資主導 {f_avg:+.2f}% vs 投信主導 {t_avg:+.2f}% → {'外資贏' if f_avg > t_avg else '投信贏'}")

    no_sell = by_sell.get('沒有出貨(0%)', [])
    fast_sell = by_sell.get('快速出貨(≥80%)', [])
    if no_sell and fast_sell:
        n_avg = sum(c['actual_10d_return'] for c in no_sell) / len(no_sell)
        f_avg = sum(c['actual_10d_return'] for c in fast_sell) / len(fast_sell)
        print(f"  3. 沒出貨 {n_avg:+.2f}% vs 快速出貨 {f_avg:+.2f}% → {'沒出貨贏' if n_avg > f_avg else '出貨贏'}")


if __name__ == "__main__":
    main()
