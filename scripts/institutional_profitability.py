#!/usr/bin/env python3
"""
法人收益分析 — 研究「跟著法人買能賺多少」

分析維度：
1. 法人 TOP N 買超股 → 後續 1/3/5/10 日報酬
2. 外資 vs 投信 vs 合計 → 誰更準？
3. 連買天數 vs 報酬 → 連買幾天最甜？
4. 買超金額 vs 報酬 → 買越多越準？
5. 法人買賣行為模式 → 累積→拉抬→出貨 pattern
6. 與我們系統推薦的對比

數據來源：data/cache/twse_t86_*.json + Yahoo Finance
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

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"
REPORTS_DIR = PROJECT_DIR / "data" / "reports"

# ===== 1. 載入所有 T86 資料 =====

def load_all_t86():
    """載入所有 T86 快取 → {date_str: {stock_code: {foreign, trust, dealer, total}}}"""
    all_data = {}
    for fp in sorted(CACHE_DIR.glob("twse_t86_*.json")):
        date_str = fp.stem.replace("twse_t86_", "")  # "20260331"
        with open(fp, 'r', encoding='utf-8') as f:
            day_data = json.load(f)
        # 過濾 ETF (00 開頭) 和無效資料
        filtered = {}
        for code, info in day_data.items():
            if code.startswith("00") or not code.isdigit():
                continue
            if len(code) != 4:
                continue
            filtered[code] = {
                'foreign': info.get('foreign', 0),
                'trust': info.get('trust', 0),
                'dealer': info.get('dealer', 0),
                'total': info.get('total', 0),
            }
        all_data[date_str] = filtered
    return all_data


def get_trading_dates(all_data):
    """取得排序後的交易日列表"""
    return sorted(all_data.keys())


# ===== 2. 股價資料 =====

_price_cache = {}

def fetch_prices(stock_code, days=60):
    """從 Yahoo Finance 取得股價"""
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
                date_str = dt.strftime("%Y%m%d")
                prices[date_str] = close

        _price_cache[stock_code] = prices
        return prices
    except Exception as e:
        _price_cache[stock_code] = {}
        return {}


def batch_fetch_prices(stock_codes, days=60):
    """批次取得股價（帶速率限制）"""
    total = len(stock_codes)
    for i, code in enumerate(stock_codes):
        if code not in _price_cache:
            fetch_prices(code, days)
            if (i + 1) % 5 == 0:
                print(f"  取得股價中... {i+1}/{total}", flush=True)
                time.sleep(0.5)  # 避免被 ban
    print(f"  股價取得完成: {total} 檔", flush=True)


# ===== 3. 核心分析函數 =====

def rank_stocks_by_buying(day_data, by='total', top_n=50):
    """依買超排名"""
    items = [(code, info[by]) for code, info in day_data.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:top_n]


def calculate_forward_return(stock_code, buy_date, trading_dates, horizon_days):
    """計算前瞻報酬率"""
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return None

    buy_price = prices.get(buy_date)
    if buy_price is None:
        return None

    # 找到 buy_date 在 trading_dates 中的位置
    try:
        idx = trading_dates.index(buy_date)
    except ValueError:
        return None

    # 往後找 horizon_days 個交易日
    target_idx = idx + horizon_days
    if target_idx >= len(trading_dates):
        return None

    target_date = trading_dates[target_idx]
    sell_price = prices.get(target_date)
    if sell_price is None:
        return None

    return (sell_price - buy_price) / buy_price * 100


def find_consecutive_buying(stock_code, end_date, all_data, trading_dates, by='total'):
    """計算到 end_date 為止的連買天數"""
    try:
        idx = trading_dates.index(end_date)
    except ValueError:
        return 0

    consecutive = 0
    for i in range(idx, -1, -1):
        date = trading_dates[i]
        day_data = all_data.get(date, {})
        stock_info = day_data.get(stock_code, {})
        if stock_info.get(by, 0) > 0:
            consecutive += 1
        else:
            break
    return consecutive


def analyze_accumulation_pattern(stock_code, all_data, trading_dates):
    """分析法人累積→拉抬→出貨模式"""
    prices = _price_cache.get(stock_code, {})
    if not prices:
        return None

    daily_flow = []
    for date in trading_dates:
        day_data = all_data.get(date, {})
        stock_info = day_data.get(stock_code, {})
        total = stock_info.get('total', 0)
        price = prices.get(date)
        daily_flow.append({
            'date': date,
            'total': total,
            'price': price,
        })

    # 尋找「連續買超→股價上漲→開始賣超」的 pattern
    patterns = []
    i = 0
    while i < len(daily_flow):
        # Phase 1: 累積（連續買超）
        if daily_flow[i]['total'] > 0:
            acc_start = i
            while i < len(daily_flow) and daily_flow[i]['total'] > 0:
                i += 1
            acc_end = i - 1
            acc_days = acc_end - acc_start + 1

            if acc_days >= 3:  # 至少連買3天才算累積
                start_price = daily_flow[acc_start]['price']
                end_price = daily_flow[acc_end]['price']
                total_bought = sum(daily_flow[j]['total'] for j in range(acc_start, acc_end + 1))

                # Phase 2: 看後續表現
                post_return = None
                if end_price and i + 5 <= len(daily_flow):
                    future_price = daily_flow[min(i + 4, len(daily_flow) - 1)]['price']
                    if future_price and end_price:
                        post_return = (future_price - end_price) / end_price * 100

                if start_price and end_price:
                    patterns.append({
                        'stock': stock_code,
                        'start_date': daily_flow[acc_start]['date'],
                        'end_date': daily_flow[acc_end]['date'],
                        'acc_days': acc_days,
                        'total_bought': total_bought,
                        'price_during': (end_price - start_price) / start_price * 100 if start_price else None,
                        'post_5d_return': post_return,
                    })
        else:
            i += 1

    return patterns


# ===== 4. 主分析 =====

def main():
    print("=" * 70)
    print("  法人收益分析 — 研究「跟著法人買能賺多少」")
    print("=" * 70)
    print()

    # 載入 T86 資料
    print("[1/6] 載入 T86 快取資料...")
    all_data = load_all_t86()
    trading_dates = get_trading_dates(all_data)
    print(f"  交易日數: {len(trading_dates)} 天 ({trading_dates[0]} ~ {trading_dates[-1]})")
    print(f"  每日平均股票數: {sum(len(d) for d in all_data.values()) // len(all_data)}")
    print()

    # 找出每天的 TOP 買超股
    print("[2/6] 分析每日 TOP 買超股...")
    daily_tops = {}
    all_top_codes = set()

    for date in trading_dates:
        top_total = rank_stocks_by_buying(all_data[date], 'total', 30)
        top_foreign = rank_stocks_by_buying(all_data[date], 'foreign', 30)
        top_trust = rank_stocks_by_buying(all_data[date], 'trust', 30)

        daily_tops[date] = {
            'total': top_total,
            'foreign': top_foreign,
            'trust': top_trust,
        }

        for code, _ in top_total + top_foreign + top_trust:
            all_top_codes.add(code)

    print(f"  需要取得股價的股票: {len(all_top_codes)} 檔")
    print()

    # 取得股價
    print("[3/6] 批次取得股價資料...")
    batch_fetch_prices(list(all_top_codes), days=90)
    print()

    # ===== 分析 1: TOP N 買超 → 後續報酬 =====
    print("[4/6] 分析法人 TOP N 買超後續報酬...")
    print()

    horizons = [1, 3, 5, 10]
    categories = ['total', 'foreign', 'trust']
    cat_names = {'total': '三大法人合計', 'foreign': '外資', 'trust': '投信'}

    for top_n in [10, 20, 30]:
        print(f"{'='*60}")
        print(f"  TOP {top_n} 買超 → 後續報酬率")
        print(f"{'='*60}")
        print()

        header = f"{'類別':<12} | {'1日':>8} | {'3日':>8} | {'5日':>8} | {'10日':>8} | {'勝率(5日)':>10} | {'樣本':>6}"
        print(header)
        print("-" * len(header))

        for cat in categories:
            returns_by_horizon = {h: [] for h in horizons}

            for date in trading_dates:
                top_stocks = rank_stocks_by_buying(all_data[date], cat, top_n)

                for code, amount in top_stocks:
                    if amount <= 0:
                        continue
                    for h in horizons:
                        ret = calculate_forward_return(code, date, trading_dates, h)
                        if ret is not None:
                            returns_by_horizon[h].append(ret)

            avg_returns = {}
            win_rate_5d = 0
            sample = 0
            for h in horizons:
                if returns_by_horizon[h]:
                    avg_returns[h] = sum(returns_by_horizon[h]) / len(returns_by_horizon[h])
                else:
                    avg_returns[h] = 0

            if returns_by_horizon[5]:
                win_rate_5d = sum(1 for r in returns_by_horizon[5] if r > 0) / len(returns_by_horizon[5]) * 100
                sample = len(returns_by_horizon[5])

            row = f"{cat_names[cat]:<10} | {avg_returns.get(1,0):>+7.2f}% | {avg_returns.get(3,0):>+7.2f}% | {avg_returns.get(5,0):>+7.2f}% | {avg_returns.get(10,0):>+7.2f}% | {win_rate_5d:>8.1f}% | {sample:>6}"
            print(row)

        print()

    # ===== 分析 2: 連買天數 vs 報酬 =====
    print(f"{'='*60}")
    print(f"  連買天數 vs 後續 5 日報酬")
    print(f"{'='*60}")
    print()

    consec_returns = defaultdict(list)

    for date in trading_dates:
        top_stocks = rank_stocks_by_buying(all_data[date], 'total', 30)

        for code, amount in top_stocks:
            if amount <= 0:
                continue
            consec = find_consecutive_buying(code, date, all_data, trading_dates, 'total')
            ret = calculate_forward_return(code, date, trading_dates, 5)
            if ret is not None:
                bucket = min(consec, 10)  # 10+ 歸為一組
                consec_returns[bucket].append(ret)

    header = f"{'連買天數':<10} | {'平均報酬':>10} | {'勝率':>8} | {'最大獲利':>10} | {'最大虧損':>10} | {'樣本':>6}"
    print(header)
    print("-" * len(header))

    for days in sorted(consec_returns.keys()):
        rets = consec_returns[days]
        avg = sum(rets) / len(rets)
        wr = sum(1 for r in rets if r > 0) / len(rets) * 100
        mx = max(rets)
        mn = min(rets)
        label = f"{days}天" if days < 10 else "10+天"
        print(f"{label:<10} | {avg:>+9.2f}% | {wr:>6.1f}% | {mx:>+9.2f}% | {mn:>+9.2f}% | {len(rets):>6}")

    print()

    # ===== 分析 3: 買超金額分級 vs 報酬 =====
    print(f"{'='*60}")
    print(f"  買超金額分級 vs 後續 5 日報酬（三大法人合計，單位:千張）")
    print(f"{'='*60}")
    print()

    amount_returns = defaultdict(list)

    for date in trading_dates:
        day_data = all_data[date]
        for code, info in day_data.items():
            total = info['total']
            if total <= 0:
                continue

            ret = calculate_forward_return(code, date, trading_dates, 5)
            if ret is not None:
                if total >= 30000:
                    bucket = "30K+ (超大量)"
                elif total >= 10000:
                    bucket = "10K-30K (大量)"
                elif total >= 5000:
                    bucket = "5K-10K (中量)"
                elif total >= 1000:
                    bucket = "1K-5K (小量)"
                else:
                    bucket = "<1K (微量)"
                amount_returns[bucket].append(ret)

    header = f"{'買超量級':<18} | {'平均報酬':>10} | {'勝率':>8} | {'樣本':>8}"
    print(header)
    print("-" * len(header))

    for bucket in ["30K+ (超大量)", "10K-30K (大量)", "5K-10K (中量)", "1K-5K (小量)", "<1K (微量)"]:
        if bucket in amount_returns:
            rets = amount_returns[bucket]
            avg = sum(rets) / len(rets)
            wr = sum(1 for r in rets if r > 0) / len(rets) * 100
            print(f"{bucket:<18} | {avg:>+9.2f}% | {wr:>6.1f}% | {len(rets):>8}")

    print()

    # ===== 分析 4: 外資 vs 投信 比較 =====
    print(f"{'='*60}")
    print(f"  外資 vs 投信：誰買的比較準？（TOP20，後續5日）")
    print(f"{'='*60}")
    print()

    for cat, cat_name in [('foreign', '外資'), ('trust', '投信')]:
        only_this = []  # 只有這個法人買，其他沒買
        both_buy = []   # 兩個法人都買

        for date in trading_dates:
            top_this = dict(rank_stocks_by_buying(all_data[date], cat, 20))
            other_cat = 'trust' if cat == 'foreign' else 'foreign'
            top_other = dict(rank_stocks_by_buying(all_data[date], other_cat, 20))

            for code, amount in top_this.items():
                if amount <= 0:
                    continue
                ret = calculate_forward_return(code, date, trading_dates, 5)
                if ret is not None:
                    if code in top_other and top_other[code] > 0:
                        both_buy.append(ret)
                    else:
                        only_this.append(ret)

        print(f"  {cat_name} TOP20:")
        if only_this:
            avg = sum(only_this) / len(only_this)
            wr = sum(1 for r in only_this if r > 0) / len(only_this) * 100
            print(f"    只有{cat_name}買: 平均 {avg:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(only_this)}")
        if both_buy:
            avg = sum(both_buy) / len(both_buy)
            wr = sum(1 for r in both_buy if r > 0) / len(both_buy) * 100
            print(f"    {cat_name}+另一方都買: 平均 {avg:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(both_buy)}")
        print()

    # ===== 分析 5: 累積→拉抬模式 =====
    print(f"{'='*60}")
    print(f"  法人累積→拉抬模式分析（連買>=3天的 pattern）")
    print(f"{'='*60}")
    print()

    # 找出出現在 TOP10 最多次的股票
    stock_freq = defaultdict(int)
    for date in trading_dates:
        top10 = rank_stocks_by_buying(all_data[date], 'total', 10)
        for code, amount in top10:
            if amount > 0:
                stock_freq[code] += 1

    frequent_stocks = sorted(stock_freq.items(), key=lambda x: x[1], reverse=True)[:30]

    all_patterns = []
    for code, freq in frequent_stocks:
        patterns = analyze_accumulation_pattern(code, all_data, trading_dates)
        if patterns:
            for p in patterns:
                p['freq_in_top10'] = freq
            all_patterns.extend(patterns)

    # 按累積天數分組
    pattern_by_days = defaultdict(list)
    for p in all_patterns:
        d = min(p['acc_days'], 10)
        pattern_by_days[d].append(p)

    header = f"{'累積天數':<10} | {'累積期漲幅':>12} | {'後5日報酬':>12} | {'成功率':>8} | {'樣本':>6}"
    print(header)
    print("-" * len(header))

    for days in sorted(pattern_by_days.keys()):
        pats = pattern_by_days[days]
        during = [p['price_during'] for p in pats if p['price_during'] is not None]
        post = [p['post_5d_return'] for p in pats if p['post_5d_return'] is not None]

        avg_during = sum(during) / len(during) if during else 0
        avg_post = sum(post) / len(post) if post else 0
        wr = sum(1 for r in post if r > 0) / len(post) * 100 if post else 0
        label = f"{days}天" if days < 10 else "10+天"
        print(f"{label:<10} | {avg_during:>+10.2f}% | {avg_post:>+10.2f}% | {wr:>6.1f}% | {len(post):>6}")

    print()

    # ===== 分析 6: 法人「反指標」— 大買後暴跌 =====
    print(f"{'='*60}")
    print(f"  法人「反指標」案例 — TOP10 大買後 5 日虧損最多")
    print(f"{'='*60}")
    print()

    worst_cases = []
    for date in trading_dates:
        top10 = rank_stocks_by_buying(all_data[date], 'total', 10)
        for code, amount in top10:
            if amount <= 0:
                continue
            ret = calculate_forward_return(code, date, trading_dates, 5)
            if ret is not None:
                worst_cases.append({
                    'date': date,
                    'code': code,
                    'amount': amount,
                    'return_5d': ret,
                })

    worst_cases.sort(key=lambda x: x['return_5d'])

    print(f"{'日期':<12} | {'股票':>6} | {'買超(張)':>10} | {'5日報酬':>10}")
    print("-" * 50)
    for case in worst_cases[:15]:
        print(f"{case['date']:<12} | {case['code']:>6} | {case['amount']:>10,} | {case['return_5d']:>+9.2f}%")

    print()
    print(f"  --- TOP10 大買後 5 日獲利最多 ---")
    print()

    best_cases = sorted(worst_cases, key=lambda x: x['return_5d'], reverse=True)
    print(f"{'日期':<12} | {'股票':>6} | {'買超(張)':>10} | {'5日報酬':>10}")
    print("-" * 50)
    for case in best_cases[:15]:
        print(f"{case['date']:<12} | {case['code']:>6} | {case['amount']:>10,} | {case['return_5d']:>+9.2f}%")

    print()

    # ===== 分析 7: 與我們推薦的對比 =====
    print(f"{'='*60}")
    print(f"  我們系統推薦 vs 單純跟法人 TOP10")
    print(f"{'='*60}")
    print()

    # 載入 tracking 資料
    tracking_dir = PROJECT_DIR / "data" / "tracking"
    our_results = {'success': 0, 'fail': 0}

    for fp in sorted(tracking_dir.glob("tracking_202*.json")):
        if 'example' in fp.name:
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for rec in data.get('recommendations', []):
            result = rec.get('result', '')
            if result in ('success', 'fail'):
                our_results[result] += 1

    our_total = our_results['success'] + our_results['fail']
    our_accuracy = our_results['success'] / our_total * 100 if our_total > 0 else 0

    # 法人 TOP10 的5日勝率
    inst_5d_returns = []
    for date in trading_dates:
        top10 = rank_stocks_by_buying(all_data[date], 'total', 10)
        for code, amount in top10:
            if amount <= 0:
                continue
            ret = calculate_forward_return(code, date, trading_dates, 5)
            if ret is not None:
                inst_5d_returns.append(ret)

    inst_wr = sum(1 for r in inst_5d_returns if r > 0) / len(inst_5d_returns) * 100 if inst_5d_returns else 0
    inst_avg = sum(inst_5d_returns) / len(inst_5d_returns) if inst_5d_returns else 0

    print(f"  我們系統準確率: {our_accuracy:.1f}% ({our_results['success']}/{our_total})")
    print(f"  法人TOP10 5日勝率: {inst_wr:.1f}% (平均報酬: {inst_avg:+.2f}%)")
    print(f"  法人TOP10 5日樣本: {len(inst_5d_returns)}")
    print()

    # ===== 總結 =====
    print(f"{'='*60}")
    print(f"  關鍵發現摘要")
    print(f"{'='*60}")
    print()

    # 計算每個維度的最佳策略
    best_consec = max(consec_returns.items(),
                      key=lambda x: sum(x[1])/len(x[1]) if x[1] else -999)
    best_consec_avg = sum(best_consec[1]) / len(best_consec[1]) if best_consec[1] else 0

    print(f"  1. 最佳連買天數: {best_consec[0]}天 (平均報酬 {best_consec_avg:+.2f}%)")

    # 外資 vs 投信整體
    for cat, cat_name in [('foreign', '外資'), ('trust', '投信')]:
        all_rets = []
        for date in trading_dates:
            top20 = rank_stocks_by_buying(all_data[date], cat, 20)
            for code, amount in top20:
                if amount <= 0:
                    continue
                ret = calculate_forward_return(code, date, trading_dates, 5)
                if ret is not None:
                    all_rets.append(ret)
        if all_rets:
            avg = sum(all_rets) / len(all_rets)
            wr = sum(1 for r in all_rets if r > 0) / len(all_rets) * 100
            print(f"  2. {cat_name} TOP20 5日: 平均 {avg:+.2f}%, 勝率 {wr:.1f}%")

    # 最佳買超量級
    best_amount = max(amount_returns.items(),
                      key=lambda x: sum(x[1])/len(x[1]) if x[1] else -999)
    best_amount_avg = sum(best_amount[1]) / len(best_amount[1]) if best_amount[1] else 0
    print(f"  3. 最佳買超量級: {best_amount[0]} (平均 {best_amount_avg:+.2f}%)")
    print()

    # 儲存報表
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"institutional_profitability_{datetime.now().strftime('%Y-%m-%d')}.txt"

    # 重新導向輸出到檔案（簡化版）
    print(f"報表已輸出至螢幕。如需儲存，請重新導向: python scripts/institutional_profitability.py > report.txt")


if __name__ == "__main__":
    main()
