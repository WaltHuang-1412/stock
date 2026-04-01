#!/usr/bin/env python3
"""
三因子交叉驗證：期貨未平倉 × 量價結構 × 大戶持股

分析 5: 期貨 — 外資現貨買+期貨多 vs 現貨買+期貨空
分析 6: 量價 — 法人買+量縮 vs 法人買+爆量
分析 4: 大戶 — 外資持股比增加 vs 減少

全部跟法人 TOP30 買超交叉，看後續 5 日報酬
"""

import sys
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


# ===== 共用: T86 + 股價 =====

def load_t86(date_str):
    fp = CACHE_DIR / f"twse_t86_{date_str}.json"
    if not fp.exists():
        return {}
    with open(fp, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_t86_dates():
    return sorted([fp.stem.replace("twse_t86_", "") for fp in CACHE_DIR.glob("twse_t86_*.json")])

_price_cache = {}
_volume_cache = {}

def fetch_price_volume(stock_code, days=90):
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

def print_stats(label, rets):
    if not rets:
        print(f"  {label}: 無數據")
        return
    avg = sum(rets) / len(rets)
    wr = sum(1 for r in rets if r > 0) / len(rets) * 100
    median = sorted(rets)[len(rets) // 2]
    print(f"  {label}: 平均 {avg:+.2f}%, 中位數 {median:+.2f}%, 勝率 {wr:.1f}%, 樣本 {len(rets)}")


# ===== 分析 5: 期貨未平倉 =====

def fetch_futures_data():
    """從 FinMind 取得台指期三大法人未平倉"""
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanFuturesInstitutionalInvestors',
        'data_id': 'TX',
        'start_date': '2026-02-01',
        'end_date': '2026-04-01',
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('status') == 200:
            return data.get('data', [])
    except Exception:
        pass
    return []

def parse_futures_positions(raw_data):
    """解析期貨資料 → {date: {foreign_net_oi, trust_net_oi, dealer_net_oi}}"""
    daily = defaultdict(dict)
    for row in raw_data:
        date = row['date'].replace('-', '')
        investor = row['institutional_investors']
        long_oi = row.get('long_open_interest_balance_volume', 0)
        short_oi = row.get('short_open_interest_balance_volume', 0)
        net_oi = long_oi - short_oi

        if '外資' in investor or 'Foreign' in investor:
            daily[date]['foreign_net_oi'] = net_oi
        elif '投信' in investor or 'Trust' in investor:
            daily[date]['trust_net_oi'] = net_oi
        elif '自營' in investor or 'Dealer' in investor:
            daily[date]['dealer_net_oi'] = net_oi

    return dict(daily)

def analyze_futures(trading_dates):
    print("=" * 60)
    print("  分析 A: 外資期貨多空 × 現貨買超 → 後續 5 日報酬")
    print("=" * 60)
    print()

    raw = fetch_futures_data()
    if not raw:
        print("  無法取得期貨資料")
        return

    futures = parse_futures_positions(raw)
    print(f"  期貨數據: {len(futures)} 天")

    # 外資期貨淨多空變化 + 現貨 TOP30 買超
    results = {
        'spot_buy_futures_long': [],   # 現貨買 + 期貨淨多
        'spot_buy_futures_short': [],  # 現貨買 + 期貨淨空
        'spot_buy_futures_add': [],    # 現貨買 + 期貨多單增加
        'spot_buy_futures_cut': [],    # 現貨買 + 期貨多單減少
    }

    prev_oi = None
    for date in trading_dates:
        if date not in futures:
            continue
        t86 = load_t86(date)
        if not t86:
            continue

        foreign_net_oi = futures[date].get('foreign_net_oi', 0)

        # 外資期貨 OI 變化
        oi_change = None
        if prev_oi is not None:
            oi_change = foreign_net_oi - prev_oi
        prev_oi = foreign_net_oi

        # TOP30 外資買超
        items = [(code, info.get('foreign', 0)) for code, info in t86.items()
                 if code.isdigit() and len(code) == 4 and not code.startswith('00')]
        items.sort(key=lambda x: x[1], reverse=True)

        for code, amount in items[:30]:
            if amount <= 0:
                continue
            ret = forward_return(code, date, trading_dates, 5)
            if ret is None:
                continue

            if foreign_net_oi > 0:
                results['spot_buy_futures_long'].append(ret)
            else:
                results['spot_buy_futures_short'].append(ret)

            if oi_change is not None:
                if oi_change > 0:
                    results['spot_buy_futures_add'].append(ret)
                else:
                    results['spot_buy_futures_cut'].append(ret)

    print_stats("外資現貨買 + 期貨淨多", results['spot_buy_futures_long'])
    print_stats("外資現貨買 + 期貨淨空", results['spot_buy_futures_short'])
    print()
    print_stats("外資現貨買 + 期貨多單增加", results['spot_buy_futures_add'])
    print_stats("外資現貨買 + 期貨多單減少", results['spot_buy_futures_cut'])
    print()

    # 計算差距
    long_r = results['spot_buy_futures_long']
    short_r = results['spot_buy_futures_short']
    if long_r and short_r:
        diff = sum(long_r)/len(long_r) - sum(short_r)/len(short_r)
        wr_diff = (sum(1 for r in long_r if r > 0)/len(long_r) - sum(1 for r in short_r if r > 0)/len(short_r)) * 100
        print(f"  淨多 vs 淨空差距: 報酬 {diff:+.2f}%, 勝率 {wr_diff:+.1f}%")

    add_r = results['spot_buy_futures_add']
    cut_r = results['spot_buy_futures_cut']
    if add_r and cut_r:
        diff = sum(add_r)/len(add_r) - sum(cut_r)/len(cut_r)
        wr_diff = (sum(1 for r in add_r if r > 0)/len(add_r) - sum(1 for r in cut_r if r > 0)/len(cut_r)) * 100
        print(f"  增加 vs 減少差距: 報酬 {diff:+.2f}%, 勝率 {wr_diff:+.1f}%")
    print()


# ===== 分析 6: 量價結構 =====

def analyze_volume_price(trading_dates):
    print("=" * 60)
    print("  分析 B: 量價結構 × 法人買超 → 後續 5 日報酬")
    print("=" * 60)
    print()

    results = {
        'vol_shrink': [],       # 量縮（今日量 < 5日均量 50%）
        'vol_normal': [],       # 正常量
        'vol_surge': [],        # 爆量（今日量 > 5日均量 200%）
        'vol_shrink_dip': [],   # 量縮+下跌（量縮不跌的反面對照）
        'vol_shrink_hold': [],  # 量縮+持平/微漲
    }

    for date in trading_dates:
        t86 = load_t86(date)
        if not t86:
            continue

        items = [(code, info['total']) for code, info in t86.items()
                 if code.isdigit() and len(code) == 4 and not code.startswith('00')]
        items.sort(key=lambda x: x[1], reverse=True)

        for code, inst_total in items[:30]:
            if inst_total <= 0:
                continue

            volumes = _volume_cache.get(code, {})
            prices = _price_cache.get(code, {})
            if not volumes or not prices:
                continue

            sorted_dates = sorted(volumes.keys())
            if date not in volumes:
                continue

            try:
                idx = sorted_dates.index(date)
            except ValueError:
                continue

            if idx < 5:
                continue

            today_vol = volumes[date]
            avg_5d_vol = sum(volumes.get(sorted_dates[idx-i], 0) for i in range(1, 6)) / 5

            if avg_5d_vol == 0:
                continue

            vol_ratio = today_vol / avg_5d_vol

            # 今日漲跌
            today_price = prices.get(date, 0)
            prev_price = prices.get(sorted_dates[idx-1], 0)
            if not today_price or not prev_price:
                continue
            day_change = (today_price - prev_price) / prev_price * 100

            ret = forward_return(code, date, trading_dates, 5)
            if ret is None:
                continue

            if vol_ratio < 0.5:
                results['vol_shrink'].append(ret)
                if day_change < -1:
                    results['vol_shrink_dip'].append(ret)
                else:
                    results['vol_shrink_hold'].append(ret)
            elif vol_ratio > 2.0:
                results['vol_surge'].append(ret)
            else:
                results['vol_normal'].append(ret)

    print("  法人 TOP30 買超 + 成交量分組:")
    print()
    print_stats("量縮（<50%均量）", results['vol_shrink'])
    print_stats("正常量", results['vol_normal'])
    print_stats("爆量（>200%均量）", results['vol_surge'])
    print()
    print("  量縮進一步拆分:")
    print_stats("量縮+下跌", results['vol_shrink_dip'])
    print_stats("量縮+持平/微漲（量縮不跌）", results['vol_shrink_hold'])
    print()

    # 差距
    shrink = results['vol_shrink']
    surge = results['vol_surge']
    if shrink and surge:
        diff = sum(shrink)/len(shrink) - sum(surge)/len(surge)
        wr_diff = (sum(1 for r in shrink if r > 0)/len(shrink) - sum(1 for r in surge if r > 0)/len(surge)) * 100
        print(f"  量縮 vs 爆量差距: 報酬 {diff:+.2f}%, 勝率 {wr_diff:+.1f}%")
    print()


# ===== 分析 4: 大戶持股 =====

def fetch_shareholding_data(stock_codes):
    """從 FinMind 批次取得外資持股比例"""
    all_data = {}
    for i, code in enumerate(stock_codes):
        url = 'https://api.finmindtrade.com/api/v4/data'
        params = {
            'dataset': 'TaiwanStockShareholding',
            'data_id': code,
            'start_date': '2026-02-01',
            'end_date': '2026-04-01',
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()
            if data.get('status') == 200 and data.get('data'):
                all_data[code] = data['data']
        except Exception:
            pass

        if (i + 1) % 5 == 0:
            print(f"  持股數據: {i+1}/{len(stock_codes)}", flush=True)
            time.sleep(1)
        else:
            time.sleep(0.3)

    return all_data

def analyze_shareholding(trading_dates):
    print("=" * 60)
    print("  分析 C: 外資持股比例變化 × 法人買超 → 後續 5 日報酬")
    print("=" * 60)
    print()

    # 找出常見股票
    stock_freq = defaultdict(int)
    for date in trading_dates:
        t86 = load_t86(date)
        for code, info in t86.items():
            if code.isdigit() and len(code) == 4 and not code.startswith('00'):
                if info.get('total', 0) > 1000:
                    stock_freq[code] += 1

    top_stocks = [c for c, f in sorted(stock_freq.items(), key=lambda x: -x[1])[:60]]
    print(f"  抓取 {len(top_stocks)} 檔持股數據...")

    shareholding = fetch_shareholding_data(top_stocks)
    print(f"  取得: {len(shareholding)} 檔")
    print()

    # 建立 {code: {date: foreign_ratio}} 的查找表
    ratio_lookup = {}
    for code, rows in shareholding.items():
        ratio_lookup[code] = {}
        for row in rows:
            d = row['date'].replace('-', '')
            ratio_lookup[code][d] = row.get('ForeignInvestmentSharesRatio', 0)

    results = {
        'ratio_up': [],     # 外資持股比增加
        'ratio_down': [],   # 外資持股比減少
        'ratio_up_big': [], # 大幅增加 (>0.5%)
    }

    for date in trading_dates:
        t86 = load_t86(date)
        if not t86:
            continue

        items = [(code, info['total']) for code, info in t86.items()
                 if code.isdigit() and len(code) == 4 and not code.startswith('00')]
        items.sort(key=lambda x: x[1], reverse=True)

        for code, inst_total in items[:30]:
            if inst_total <= 0 or code not in ratio_lookup:
                continue

            ratios = ratio_lookup[code]
            sorted_ratio_dates = sorted(ratios.keys())

            # 找最近的持股比例和前一期
            current_ratio = None
            prev_ratio = None
            for rd in sorted_ratio_dates:
                if rd <= date:
                    prev_ratio = current_ratio
                    current_ratio = ratios[rd]

            if current_ratio is None or prev_ratio is None:
                continue

            ratio_change = current_ratio - prev_ratio

            ret = forward_return(code, date, trading_dates, 5)
            if ret is None:
                continue

            if ratio_change > 0:
                results['ratio_up'].append(ret)
                if ratio_change > 0.5:
                    results['ratio_up_big'].append(ret)
            else:
                results['ratio_down'].append(ret)

    print_stats("法人買 + 外資持股比增加", results['ratio_up'])
    print_stats("法人買 + 外資持股比減少", results['ratio_down'])
    print_stats("法人買 + 外資持股比大增(>0.5%)", results['ratio_up_big'])
    print()

    up = results['ratio_up']
    down = results['ratio_down']
    if up and down:
        diff = sum(up)/len(up) - sum(down)/len(down)
        wr_diff = (sum(1 for r in up if r > 0)/len(up) - sum(1 for r in down if r > 0)/len(down)) * 100
        print(f"  增加 vs 減少差距: 報酬 {diff:+.2f}%, 勝率 {wr_diff:+.1f}%")
    print()


# ===== 主程式 =====

def main():
    print("=" * 70)
    print("  三因子交叉驗證：期貨 × 量價 × 大戶持股")
    print("=" * 70)
    print()

    trading_dates = get_t86_dates()
    print(f"交易日: {len(trading_dates)} 天 ({trading_dates[0]}~{trading_dates[-1]})")
    print()

    # 收集所有需要股價的股票
    print("準備股價數據...")
    all_codes = set()
    for date in trading_dates:
        t86 = load_t86(date)
        items = sorted(t86.items(), key=lambda x: x[1].get('total', 0), reverse=True)
        for code, info in items[:30]:
            if code.isdigit() and len(code) == 4 and not code.startswith('00'):
                all_codes.add(code)

    print(f"  取得 {len(all_codes)} 檔股價+量...")
    for i, code in enumerate(list(all_codes)):
        fetch_price_volume(code)
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(all_codes)}", flush=True)
            time.sleep(0.5)
    print(f"  完成")
    print()

    # 跑三個分析
    analyze_futures(trading_dates)
    analyze_volume_price(trading_dates)
    analyze_shareholding(trading_dates)

    # 總結
    print("=" * 60)
    print("  總結")
    print("=" * 60)
    print()
    print("  各分析結論請見上方。差距 >0.5% 且勝率差 >3% 視為有效。")


if __name__ == "__main__":
    main()
