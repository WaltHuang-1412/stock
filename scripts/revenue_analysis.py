#!/usr/bin/env python3
"""
月營收 × 股價 交叉分析

驗證假說：
1. 營收年增率高 + 股價下跌 = 買入機會？
2. 營收成長股 vs 衰退股 → 後續報酬差多少？
3. 法人買超 + 營收成長 → 是否更準？
4. 營收連續成長幾個月最有效？

數據來源：FinMind API（台灣財經開放數據）+ Yahoo Finance + T86 法人
"""

import sys
import io
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import requests

os.environ['PYTHONUTF8'] = '1'

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"
REPORTS_DIR = PROJECT_DIR / "data" / "reports"


# ===== FinMind 月營收 =====

def fetch_revenue(stock_id, start_date='2025-01-01', end_date='2026-04-01'):
    """從 FinMind 取得月營收"""
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanStockMonthRevenue',
        'data_id': stock_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('status') == 200 and data.get('data'):
            return data['data']
    except Exception:
        pass
    return []


def calc_revenue_yoy(revenues):
    """計算每月營收年增率 (YoY%)

    Returns: {(year, month): yoy_pct, ...}
    """
    monthly = {}
    for r in revenues:
        key = (r['revenue_year'], r['revenue_month'])
        monthly[key] = r['revenue']

    yoy = {}
    for (year, month), rev in monthly.items():
        prev_key = (year - 1, month)
        if prev_key in monthly and monthly[prev_key] > 0:
            yoy[(year, month)] = (rev - monthly[prev_key]) / monthly[prev_key] * 100
    return yoy


def calc_revenue_streak(yoy_data, year, month):
    """計算到 (year, month) 為止的連續營收成長月數"""
    streak = 0
    y, m = year, month
    while True:
        if (y, m) in yoy_data and yoy_data[(y, m)] > 0:
            streak += 1
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        else:
            break
    return streak


# ===== 股價 =====

_price_cache = {}

def fetch_prices(stock_code, days=250):
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


# ===== T86 法人 =====

def load_t86(date_str):
    fp = CACHE_DIR / f"twse_t86_{date_str}.json"
    if not fp.exists():
        return {}
    with open(fp, 'r', encoding='utf-8') as f:
        return json.load(f)


# ===== 報酬計算 =====

def monthly_return(stock_code, year, month, hold_days=20):
    """營收公布後持有 N 個交易日的報酬

    營收在每月 10 號前公布，用每月 11 日為基準買入
    """
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return None

    sorted_dates = sorted(prices.keys())

    # 找到該月 10 號之後的第一個交易日（營收公布後）
    target = f"{year}{month:02d}11"
    buy_date = None
    for d in sorted_dates:
        if d >= target:
            buy_date = d
            break

    if not buy_date:
        return None

    buy_price = prices.get(buy_date)
    if not buy_price:
        return None

    # 往後 hold_days 個交易日
    try:
        idx = sorted_dates.index(buy_date)
    except ValueError:
        return None

    sell_idx = idx + hold_days
    if sell_idx >= len(sorted_dates):
        return None

    sell_price = prices.get(sorted_dates[sell_idx])
    if not sell_price:
        return None

    return (sell_price - buy_price) / buy_price * 100


# ===== 主分析 =====

def main():
    print("=" * 70)
    print("  月營收 × 股價 交叉分析")
    print("=" * 70)
    print()

    # Step 1: 決定分析對象 — 從 T86 找出最常出現的股票
    print("[1/5] 找出分析對象（T86 常見股）...")

    stock_freq = defaultdict(int)
    t86_files = sorted(CACHE_DIR.glob("twse_t86_*.json"))

    for fp in t86_files:
        with open(fp, 'r', encoding='utf-8') as f:
            day_data = json.load(f)
        for code in day_data:
            if code.isdigit() and len(code) == 4 and not code.startswith('00'):
                total = day_data[code].get('total', 0)
                if abs(total) > 1000:  # 法人有在操作的
                    stock_freq[code] += 1

    # 取出現 >= 10 天的股票（法人常關注的）
    target_stocks = [code for code, freq in stock_freq.items() if freq >= 10]
    target_stocks.sort()
    print(f"  法人常操作股票: {len(target_stocks)} 檔")
    print()

    # Step 2: 抓月營收（FinMind 有速率限制，分批）
    print("[2/5] 抓取月營收（FinMind API）...")

    revenue_cache_path = CACHE_DIR / "revenue_cache.json"
    revenue_data = {}

    # 讀取快取
    if revenue_cache_path.exists():
        with open(revenue_cache_path, 'r', encoding='utf-8') as f:
            revenue_data = json.load(f)
        print(f"  快取已有: {len(revenue_data)} 檔")

    # 抓缺少的
    missing = [c for c in target_stocks if c not in revenue_data]
    print(f"  需要抓取: {len(missing)} 檔")

    for i, code in enumerate(missing):
        revs = fetch_revenue(code, '2024-06-01', '2026-04-01')
        if revs:
            revenue_data[code] = revs
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(missing)}", flush=True)
            time.sleep(1)  # FinMind 速率限制
        else:
            time.sleep(0.3)

    # 存快取
    if missing:
        with open(revenue_cache_path, 'w', encoding='utf-8') as f:
            json.dump(revenue_data, f, ensure_ascii=False)

    print(f"  營收數據: {len(revenue_data)} 檔")
    print()

    # Step 3: 計算每檔的營收年增率
    print("[3/5] 計算營收年增率...")

    stock_yoy = {}
    for code, revs in revenue_data.items():
        yoy = calc_revenue_yoy(revs)
        if yoy:
            stock_yoy[code] = yoy

    print(f"  有 YoY 數據: {len(stock_yoy)} 檔")
    print()

    # Step 4: 抓股價
    print("[4/5] 取得股價...")
    codes_with_rev = list(stock_yoy.keys())
    for i, code in enumerate(codes_with_rev):
        if code not in _price_cache:
            fetch_prices(code, 300)
            if (i + 1) % 5 == 0:
                print(f"  {i+1}/{len(codes_with_rev)}", flush=True)
                time.sleep(0.5)
    print(f"  完成")
    print()

    # Step 5: 交叉分析
    print("[5/5] 交叉分析")
    print()

    # ============================
    # 分析 1: 營收 YoY 分組 → 後續報酬
    # ============================
    print("=" * 60)
    print("  分析 1: 營收年增率 vs 營收公布後 20 日報酬")
    print("=" * 60)
    print()

    yoy_buckets = defaultdict(list)

    # 分析 2025/7 ~ 2026/2 的營收（需要前一年同期對比）
    for code, yoy in stock_yoy.items():
        for (year, month), yoy_pct in yoy.items():
            ret = monthly_return(code, year, month, hold_days=20)
            if ret is None:
                continue

            if yoy_pct >= 30:
                yoy_buckets['營收年增>=30%'].append(ret)
            elif yoy_pct >= 10:
                yoy_buckets['營收年增10-30%'].append(ret)
            elif yoy_pct >= 0:
                yoy_buckets['營收年增0-10%'].append(ret)
            elif yoy_pct >= -10:
                yoy_buckets['營收衰退0~-10%'].append(ret)
            else:
                yoy_buckets['營收衰退>-10%'].append(ret)

    header = f"{'營收狀況':<20} | {'平均報酬':>10} | {'中位數':>10} | {'勝率':>8} | {'樣本':>6}"
    print(header)
    print("-" * len(header))

    for label in ['營收年增>=30%', '營收年增10-30%', '營收年增0-10%', '營收衰退0~-10%', '營收衰退>-10%']:
        rets = yoy_buckets.get(label, [])
        if rets:
            avg = sum(rets) / len(rets)
            median = sorted(rets)[len(rets) // 2]
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            print(f"{label:<20} | {avg:>+9.2f}% | {median:>+9.2f}% | {wr:>6.1f}% | {len(rets):>6}")
    print()

    # ============================
    # 分析 2: 營收連續成長月數 vs 報酬
    # ============================
    print("=" * 60)
    print("  分析 2: 營收連續成長月數 vs 後續 20 日報酬")
    print("=" * 60)
    print()

    streak_buckets = defaultdict(list)

    for code, yoy in stock_yoy.items():
        for (year, month), yoy_pct in yoy.items():
            if yoy_pct <= 0:
                continue
            ret = monthly_return(code, year, month, hold_days=20)
            if ret is None:
                continue
            streak = calc_revenue_streak(yoy, year, month)

            if streak >= 6:
                streak_buckets['連續成長>=6個月'].append(ret)
            elif streak >= 3:
                streak_buckets['連續成長3-5個月'].append(ret)
            else:
                streak_buckets['成長1-2個月'].append(ret)

    for label in ['連續成長>=6個月', '連續成長3-5個月', '成長1-2個月']:
        rets = streak_buckets.get(label, [])
        if rets:
            avg = sum(rets) / len(rets)
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            print(f"  {label}: 平均 {avg:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(rets)}")
    print()

    # ============================
    # 分析 3: 法人買超 × 營收成長 交叉
    # ============================
    print("=" * 60)
    print("  分析 3: 法人買超 × 營收成長 交叉分析")
    print("=" * 60)
    print()
    print("  （法人 TOP30 買超股，區分營收成長 vs 衰退）")
    print()

    # 用最近一期營收 YoY 分類
    cross_results = {
        'inst_buy_rev_up': [],      # 法人買 + 營收成長
        'inst_buy_rev_down': [],    # 法人買 + 營收衰退
        'inst_buy_rev_strong': [],  # 法人買 + 營收年增>=20%
    }

    t86_dates = sorted([fp.stem.replace("twse_t86_", "") for fp in t86_files])

    for date_str in t86_dates:
        t86 = load_t86(date_str)
        if not t86:
            continue

        # 找 TOP30 買超
        items = [(code, info['total']) for code, info in t86.items()
                 if code.isdigit() and len(code) == 4 and not code.startswith('00')]
        items.sort(key=lambda x: x[1], reverse=True)

        dt = datetime.strptime(date_str, "%Y%m%d")
        # 用上個月的營收（本月營收要到 10 號才公布）
        rev_month = dt.month - 1
        rev_year = dt.year
        if rev_month == 0:
            rev_month = 12
            rev_year -= 1

        for code, inst_total in items[:30]:
            if inst_total <= 0:
                continue
            if code not in stock_yoy:
                continue

            yoy = stock_yoy[code]
            latest_yoy = yoy.get((rev_year, rev_month))
            if latest_yoy is None:
                # 再往前一個月
                prev_m = rev_month - 1
                prev_y = rev_year
                if prev_m == 0:
                    prev_m = 12
                    prev_y -= 1
                latest_yoy = yoy.get((prev_y, prev_m))

            if latest_yoy is None:
                continue

            # 計算 5 日報酬
            prices = _price_cache.get(code, {})
            sorted_dates = sorted(prices.keys())
            if date_str not in prices:
                continue

            try:
                idx = sorted_dates.index(date_str)
            except ValueError:
                continue

            if idx + 5 >= len(sorted_dates):
                continue

            buy_p = prices[date_str]
            sell_p = prices[sorted_dates[idx + 5]]
            if not buy_p or not sell_p:
                continue

            ret = (sell_p - buy_p) / buy_p * 100

            if latest_yoy > 0:
                cross_results['inst_buy_rev_up'].append(ret)
            else:
                cross_results['inst_buy_rev_down'].append(ret)

            if latest_yoy >= 20:
                cross_results['inst_buy_rev_strong'].append(ret)

    for label, display in [
        ('inst_buy_rev_up', '法人買 + 營收成長'),
        ('inst_buy_rev_down', '法人買 + 營收衰退'),
        ('inst_buy_rev_strong', '法人買 + 營收年增>=20%'),
    ]:
        rets = cross_results[label]
        if rets:
            avg = sum(rets) / len(rets)
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            median = sorted(rets)[len(rets) // 2]
            print(f"  {display}: 平均 {avg:+.2f}%, 中位數 {median:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(rets)}")
    print()

    # ============================
    # 分析 4: 營收成長 + 股價回檔 = 黃金買點？
    # ============================
    print("=" * 60)
    print("  分析 4: 營收成長 + 股價回檔 = 黃金買點？")
    print("=" * 60)
    print()

    dip_buy_results = defaultdict(list)

    for date_str in t86_dates:
        dt = datetime.strptime(date_str, "%Y%m%d")
        rev_month = dt.month - 1
        rev_year = dt.year
        if rev_month == 0:
            rev_month = 12
            rev_year -= 1

        t86 = load_t86(date_str)
        if not t86:
            continue

        for code in stock_yoy:
            if code not in t86:
                continue

            inst_total = t86[code].get('total', 0)
            if inst_total <= 0:
                continue

            yoy = stock_yoy[code]
            latest_yoy = yoy.get((rev_year, rev_month))
            if latest_yoy is None or latest_yoy <= 0:
                continue

            # 計算近 5 日跌幅
            prices = _price_cache.get(code, {})
            sorted_dates = sorted(prices.keys())
            if date_str not in prices:
                continue

            try:
                idx = sorted_dates.index(date_str)
            except ValueError:
                continue

            if idx < 5 or idx + 5 >= len(sorted_dates):
                continue

            current_price = prices[date_str]
            price_5d_ago = prices.get(sorted_dates[idx - 5])
            if not price_5d_ago or not current_price:
                continue

            recent_change = (current_price - price_5d_ago) / price_5d_ago * 100

            # 5 日後報酬
            sell_price = prices.get(sorted_dates[idx + 5])
            if not sell_price:
                continue

            ret = (sell_price - current_price) / current_price * 100

            if recent_change <= -5:
                dip_buy_results['營收成長+近5日跌>=5%'].append(ret)
            elif recent_change <= -2:
                dip_buy_results['營收成長+近5日跌2-5%'].append(ret)
            elif recent_change <= 0:
                dip_buy_results['營收成長+近5日持平'].append(ret)
            else:
                dip_buy_results['營收成長+近5日漲'].append(ret)

    print("  （法人買超 + 營收成長 + 近5日股價表現分組）")
    print()
    for label in ['營收成長+近5日跌>=5%', '營收成長+近5日跌2-5%', '營收成長+近5日持平', '營收成長+近5日漲']:
        rets = dip_buy_results.get(label, [])
        if rets:
            avg = sum(rets) / len(rets)
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            print(f"  {label}: 平均 {avg:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(rets)}")
    print()

    # ============================
    # 總結
    # ============================
    print("=" * 60)
    print("  總結")
    print("=" * 60)
    print()

    # 比較法人買+營收成長 vs 法人買+營收衰退
    up = cross_results['inst_buy_rev_up']
    down = cross_results['inst_buy_rev_down']
    if up and down:
        avg_up = sum(up) / len(up)
        avg_down = sum(down) / len(down)
        wr_up = sum(1 for r in up if r > 0) / len(up) * 100
        wr_down = sum(1 for r in down if r > 0) / len(down) * 100
        print(f"  法人買+營收成長: 平均 {avg_up:+.2f}%, 勝率 {wr_up:.1f}%")
        print(f"  法人買+營收衰退: 平均 {avg_down:+.2f}%, 勝率 {wr_down:.1f}%")
        print(f"  差距: 報酬 {avg_up - avg_down:+.2f}%, 勝率 {wr_up - wr_down:+.1f}%")
        print()

        if avg_up - avg_down > 0.5 and wr_up - wr_down > 3:
            print("  --> 營收成長有效：法人買+營收好 > 法人買+營收差")
            print("  --> 建議加入評分系統")
        elif avg_up > avg_down:
            print("  --> 方向正確但差距不大，可作為參考")
        else:
            print("  --> 營收對短期報酬影響不明顯")


if __name__ == "__main__":
    main()
