#!/usr/bin/env python3
"""
融資融券 × 法人買賣超 交叉分析

驗證假說：
1. 法人買 + 融資減 → 主力吃貨散戶割肉 → 勝率高？
2. 法人買 + 融資增 → 散戶追高 → 勝率低？
3. 券資比高 → 軋空行情？
4. 融資暴增 → 反指標？
"""

import sys
import io
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import requests

import os
os.environ['PYTHONUTF8'] = '1'

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"

sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from fetch_margin_trading import fetch_margin_data


def load_t86(date_str):
    """載入 T86 法人資料"""
    fp = CACHE_DIR / f"twse_t86_{date_str}.json"
    if not fp.exists():
        return {}
    with open(fp, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_available_dates():
    """找出同時有 T86 和融資融券的交易日"""
    t86_dates = set()
    for fp in CACHE_DIR.glob("twse_t86_*.json"):
        d = fp.stem.replace("twse_t86_", "")
        t86_dates.add(d)
    return sorted(t86_dates)


_price_cache = {}

def fetch_prices(stock_code, days=90):
    if stock_code in _price_cache:
        return _price_cache[stock_code]
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW"
    params = {"interval": "1d", "range": f"{days}d"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
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


def forward_return(stock_code, buy_date, trading_dates, horizon):
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return None
    buy_price = prices.get(buy_date)
    if not buy_price:
        return None
    try:
        idx = trading_dates.index(buy_date)
    except ValueError:
        return None
    target_idx = idx + horizon
    if target_idx >= len(trading_dates):
        return None
    sell_price = prices.get(trading_dates[target_idx])
    if not sell_price:
        return None
    return (sell_price - buy_price) / buy_price * 100


def print_stats(label, returns):
    if not returns:
        print(f"  {label}: 無數據")
        return
    avg = sum(returns) / len(returns)
    wr = sum(1 for r in returns if r > 0) / len(returns) * 100
    median = sorted(returns)[len(returns) // 2]
    print(f"  {label}: 平均 {avg:+.2f}%, 中位數 {median:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(returns)}")


def main():
    print("=" * 70)
    print("  融資融券 × 法人買賣超 交叉分析")
    print("=" * 70)
    print()

    # Step 1: 取得可用交易日
    t86_dates = get_available_dates()
    print(f"[1/5] T86 可用交易日: {len(t86_dates)} 天 ({t86_dates[0]}~{t86_dates[-1]})")

    # Step 2: 批次抓融資融券（有快取的不重抓）
    print(f"[2/5] 抓取融資融券數據...")
    margin_dates = []
    for date in t86_dates:
        data = fetch_margin_data(date)
        if data:
            margin_dates.append(date)
        else:
            print(f"  {date}: 抓取中...", end=" ", flush=True)
            time.sleep(0.5)
            data = fetch_margin_data(date)
            if data:
                margin_dates.append(date)
                print(f"OK")
            else:
                print(f"無資料")

    print(f"  融資融券可用: {len(margin_dates)} 天")
    trading_dates = sorted(set(t86_dates) & set(margin_dates))
    print(f"  交叉可用: {len(trading_dates)} 天")
    print()

    # Step 3: 收集法人 TOP30 + 融資變化
    print(f"[3/5] 建立法人×融資交叉表...")

    records = []
    all_codes = set()

    for date in trading_dates:
        t86 = load_t86(date)
        margin = fetch_margin_data(date)

        # 法人 TOP30 買超
        items = [(code, info['total']) for code, info in t86.items()
                 if code.isdigit() and len(code) == 4 and not code.startswith('00')]
        items.sort(key=lambda x: x[1], reverse=True)
        top30 = items[:30]

        for code, inst_total in top30:
            if inst_total <= 0:
                continue
            if code not in margin:
                continue

            m = margin[code]
            margin_change = m['margin_balance'] - m['margin_prev']
            margin_balance = m['margin_balance']
            short_balance = m['short_balance']
            short_ratio = short_balance / margin_balance * 100 if margin_balance > 0 else 0

            records.append({
                'date': date,
                'code': code,
                'inst_total': inst_total,
                'margin_change': margin_change,
                'margin_balance': margin_balance,
                'short_balance': short_balance,
                'short_ratio': short_ratio,
            })
            all_codes.add(code)

    print(f"  記錄數: {len(records)}, 不重複股票: {len(all_codes)}")
    print()

    # Step 4: 取得股價
    print(f"[4/5] 取得股價... ({len(all_codes)} 檔)")
    code_list = list(all_codes)
    for i, code in enumerate(code_list):
        if code not in _price_cache:
            fetch_prices(code)
            if (i + 1) % 5 == 0:
                print(f"  {i+1}/{len(code_list)}", flush=True)
                time.sleep(0.5)
    print(f"  完成")
    print()

    # Step 5: 分析
    print(f"[5/5] 交叉分析結果")
    print()

    # ============================
    # 分析 1: 四象限（法人買×融資增減）
    # ============================
    print("=" * 60)
    print("  分析 1: 法人買超 × 融資增減 → 後續 5 日報酬")
    print("=" * 60)
    print()

    quadrants = {
        'inst_buy_margin_down': [],   # 法人買 + 融資減
        'inst_buy_margin_up': [],     # 法人買 + 融資增
    }

    for rec in records:
        ret = forward_return(rec['code'], rec['date'], trading_dates, 5)
        if ret is None:
            continue
        if rec['margin_change'] < 0:
            quadrants['inst_buy_margin_down'].append(ret)
        elif rec['margin_change'] > 0:
            quadrants['inst_buy_margin_up'].append(ret)

    print_stats("法人買 + 融資減（主力吃貨）", quadrants['inst_buy_margin_down'])
    print_stats("法人買 + 融資增（散戶追高）", quadrants['inst_buy_margin_up'])
    print()

    # 再細分融資變化幅度
    print("  --- 融資變化幅度細分 ---")
    margin_buckets = defaultdict(list)
    for rec in records:
        ret = forward_return(rec['code'], rec['date'], trading_dates, 5)
        if ret is None:
            continue
        mc = rec['margin_change']
        mb = rec['margin_balance']
        if mb == 0:
            continue
        pct = mc / mb * 100  # 融資增減比例

        if pct <= -5:
            margin_buckets['融資大減(>-5%)'].append(ret)
        elif pct <= -1:
            margin_buckets['融資小減(-1~-5%)'].append(ret)
        elif pct < 1:
            margin_buckets['融資持平(-1~+1%)'].append(ret)
        elif pct < 5:
            margin_buckets['融資小增(+1~+5%)'].append(ret)
        else:
            margin_buckets['融資大增(>+5%)'].append(ret)

    for label in ['融資大減(>-5%)', '融資小減(-1~-5%)', '融資持平(-1~+1%)', '融資小增(+1~+5%)', '融資大增(>+5%)']:
        print_stats(label, margin_buckets.get(label, []))
    print()

    # ============================
    # 分析 2: 券資比 vs 報酬
    # ============================
    print("=" * 60)
    print("  分析 2: 券資比 vs 後續 5 日報酬（法人 TOP30 買超股）")
    print("=" * 60)
    print()

    short_buckets = defaultdict(list)
    for rec in records:
        ret = forward_return(rec['code'], rec['date'], trading_dates, 5)
        if ret is None:
            continue
        sr = rec['short_ratio']
        if sr >= 30:
            short_buckets['券資比>=30%'].append(ret)
        elif sr >= 20:
            short_buckets['券資比20-30%'].append(ret)
        elif sr >= 10:
            short_buckets['券資比10-20%'].append(ret)
        else:
            short_buckets['券資比<10%'].append(ret)

    for label in ['券資比>=30%', '券資比20-30%', '券資比10-20%', '券資比<10%']:
        print_stats(label, short_buckets.get(label, []))
    print()

    # ============================
    # 分析 3: 不同持有天數
    # ============================
    print("=" * 60)
    print("  分析 3: 法人買+融資減 vs 法人買+融資增 — 不同天期")
    print("=" * 60)
    print()

    for horizon in [1, 3, 5, 7, 10]:
        down_rets = []
        up_rets = []
        for rec in records:
            ret = forward_return(rec['code'], rec['date'], trading_dates, horizon)
            if ret is None:
                continue
            if rec['margin_change'] < 0:
                down_rets.append(ret)
            elif rec['margin_change'] > 0:
                up_rets.append(ret)

        down_avg = sum(down_rets) / len(down_rets) if down_rets else 0
        down_wr = sum(1 for r in down_rets if r > 0) / len(down_rets) * 100 if down_rets else 0
        up_avg = sum(up_rets) / len(up_rets) if up_rets else 0
        up_wr = sum(1 for r in up_rets if r > 0) / len(up_rets) * 100 if up_rets else 0
        diff = down_avg - up_avg

        print(f"  {horizon:>2}日: 融資減 {down_avg:+.2f}%({down_wr:.0f}%) vs 融資增 {up_avg:+.2f}%({up_wr:.0f}%)  差距 {diff:+.2f}%")
    print()

    # ============================
    # 分析 4: 法人大買 + 融資（拆解 30K+ 陷阱）
    # ============================
    print("=" * 60)
    print("  分析 4: 法人大買(>=30K) 拆解 — 融資是否追進？")
    print("=" * 60)
    print()

    big_buy_down = []
    big_buy_up = []

    for rec in records:
        if rec['inst_total'] < 30000:
            continue
        ret = forward_return(rec['code'], rec['date'], trading_dates, 5)
        if ret is None:
            continue
        if rec['margin_change'] < 0:
            big_buy_down.append(ret)
        elif rec['margin_change'] > 0:
            big_buy_up.append(ret)

    print_stats("法人>=30K + 融資減", big_buy_down)
    print_stats("法人>=30K + 融資增", big_buy_up)
    print()

    # ============================
    # 分析 5: 最佳/最差組合排行
    # ============================
    print("=" * 60)
    print("  分析 5: 最佳組合（法人買+融資減+券資比高）")
    print("=" * 60)
    print()

    golden = []  # 法人買 + 融資減 + 券資比 >= 10%
    for rec in records:
        if rec['margin_change'] >= 0:
            continue
        if rec['short_ratio'] < 10:
            continue
        ret = forward_return(rec['code'], rec['date'], trading_dates, 5)
        if ret is None:
            continue
        golden.append({**rec, 'return_5d': ret})

    print_stats("黃金組合（法人買+融資減+券資比>=10%）", [g['return_5d'] for g in golden])
    print()

    if golden:
        golden.sort(key=lambda x: x['return_5d'], reverse=True)
        print(f"  {'日期':<12} {'股票':>6} {'法人買超':>8} {'融資變化':>8} {'券資比':>8} {'5日報酬':>8}")
        print(f"  {'-'*58}")
        for g in golden[:10]:
            print(f"  {g['date']:<12} {g['code']:>6} {g['inst_total']:>+8,} {g['margin_change']:>+8,} {g['short_ratio']:>7.1f}% {g['return_5d']:>+7.2f}%")
        print()

    # ============================
    # 總結
    # ============================
    print("=" * 60)
    print("  結論")
    print("=" * 60)
    print()

    q_down = quadrants['inst_buy_margin_down']
    q_up = quadrants['inst_buy_margin_up']
    if q_down and q_up:
        avg_down = sum(q_down) / len(q_down)
        avg_up = sum(q_up) / len(q_up)
        wr_down = sum(1 for r in q_down if r > 0) / len(q_down) * 100
        wr_up = sum(1 for r in q_up if r > 0) / len(q_up) * 100
        diff = avg_down - avg_up
        wr_diff = wr_down - wr_up

        print(f"  法人買+融資減 vs 法人買+融資增:")
        print(f"    報酬差距: {diff:+.2f}%  勝率差距: {wr_diff:+.1f}%")
        print()
        if diff > 0.5 and wr_diff > 3:
            print(f"  --> 假說成立：融資減少時跟法人買，報酬顯著較高")
            print(f"  --> 建議加入 Step 7 評分")
        elif diff > 0:
            print(f"  --> 方向正確但差距不大，可考慮作為參考指標")
        else:
            print(f"  --> 假說不成立：融資增減對報酬沒有顯著影響")


if __name__ == "__main__":
    main()
