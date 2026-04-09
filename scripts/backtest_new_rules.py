#!/usr/bin/env python3
"""
回測新規則：如果歷史推薦套用營收+外資持股比規則，準確率會變多少？

邏輯：
1. 讀取所有 tracking 的已結算推薦（success/fail）
2. 對每檔查營收 YoY 和外資持股比週變化
3. 計算調整後分數
4. 模擬：分數被扣到 <65 的 fail → 會被排除（避免虧損）
5. 模擬：分數被加到更高的 success → 確認不會誤殺好股
6. 比較原始 vs 調整後準確率
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
CACHE_DIR = PROJECT_DIR / "data" / "cache"

sys.path.insert(0, str(PROJECT_DIR / "scripts"))


# ===== 數據載入 =====

def load_all_settled():
    """讀取所有已結算的推薦"""
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
            code = rec.get('stock_code') or rec.get('symbol', '')
            score = rec.get('score', 0)
            name = rec.get('stock_name') or rec.get('name', '')

            all_recs.append({
                'date': date_str,
                'code': code,
                'name': name,
                'score': score,
                'result': result,
            })
    return all_recs


def load_revenue_cache():
    fp = CACHE_DIR / "revenue_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_foreign_ratio_cache():
    fp = CACHE_DIR / "foreign_ratio_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# ===== 營收查詢 =====

def fetch_revenue_if_missing(code, cache):
    if code in cache:
        return
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanStockMonthRevenue',
        'data_id': code,
        'start_date': '2024-06-01',
        'end_date': '2026-04-01',
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('status') == 200 and data.get('data'):
            cache[code] = data['data']
    except Exception:
        pass


def get_revenue_yoy(code, rec_date, cache):
    """取得推薦日期時的最新營收 YoY"""
    if code not in cache:
        return None, 0

    revenues = cache[code]
    monthly = {}
    for r in revenues:
        key = (r['revenue_year'], r['revenue_month'])
        monthly[key] = r['revenue']

    # 推薦日期的年月（用上個月營收，因為本月還沒公布）
    try:
        dt = datetime.strptime(rec_date, "%Y-%m-%d")
    except ValueError:
        return None, 0

    # 最新可用的營收月份（推薦日之前的）
    check_month = dt.month - 1
    check_year = dt.year
    if check_month == 0:
        check_month = 12
        check_year -= 1

    # 計算 YoY
    current = monthly.get((check_year, check_month))
    prev = monthly.get((check_year - 1, check_month))

    if current and prev and prev > 0:
        yoy = (current - prev) / prev * 100
    else:
        # 再往前一個月
        check_month -= 1
        if check_month == 0:
            check_month = 12
            check_year -= 1
        current = monthly.get((check_year, check_month))
        prev = monthly.get((check_year - 1, check_month))
        if current and prev and prev > 0:
            yoy = (current - prev) / prev * 100
        else:
            return None, 0

    # 計算連續衰退月數
    decline_streak = 0
    y, m = check_year, check_month
    while True:
        cur = monthly.get((y, m))
        pre = monthly.get((y - 1, m))
        if cur and pre and pre > 0 and (cur - pre) / pre * 100 < 0:
            decline_streak += 1
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        else:
            break

    return yoy, decline_streak


# ===== 外資持股比查詢 =====

def fetch_ratio_if_missing(code, cache):
    if code in cache:
        return
    url = 'https://api.finmindtrade.com/api/v4/data'
    params = {
        'dataset': 'TaiwanStockShareholding',
        'data_id': code,
        'start_date': '2025-10-01',
        'end_date': '2026-04-01',
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get('status') == 200 and data.get('data'):
            cache[code] = data['data']
    except Exception:
        pass


def get_ratio_change(code, rec_date, cache):
    """取得推薦日期時的外資持股比變化"""
    if code not in cache:
        return None

    rows = cache[code]
    if len(rows) < 2:
        return None

    # 找推薦日期之前最近的兩期
    current = None
    prev = None
    for row in rows:
        row_date = row['date'].replace('-', '')
        rec_date_clean = rec_date.replace('-', '')
        if row_date <= rec_date_clean:
            prev = current
            current = row

    if current is None or prev is None:
        return None

    cur_ratio = current.get('ForeignInvestmentSharesRatio', 0)
    prev_ratio = prev.get('ForeignInvestmentSharesRatio', 0)
    return cur_ratio - prev_ratio


# ===== 股價回檔查詢（簡化：用 Yahoo Finance）=====

_price_cache = {}

def get_5d_change(code, rec_date):
    """取得近 5 日漲跌幅"""
    if code not in _price_cache:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
            params = {"interval": "1d", "range": "30d"}
            r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            data = r.json()
            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            closes = result['indicators']['quote'][0]['close']
            prices = {}
            for ts, close in zip(timestamps, closes):
                if close is not None:
                    dt = datetime.fromtimestamp(ts)
                    prices[dt.strftime("%Y-%m-%d")] = close
            _price_cache[code] = prices
        except Exception:
            _price_cache[code] = {}

    prices = _price_cache[code]
    sorted_dates = sorted(prices.keys())
    if rec_date not in prices:
        return None

    try:
        idx = sorted_dates.index(rec_date)
    except ValueError:
        return None

    if idx < 5:
        return None

    current = prices[rec_date]
    past = prices[sorted_dates[idx - 5]]
    if not current or not past:
        return None

    return (current - past) / past * 100


# ===== 主分析 =====

def main():
    print("=" * 70)
    print("  新規則歷史回測驗證")
    print("=" * 70)
    print()

    # 1. 載入已結算推薦
    recs = load_all_settled()
    print(f"已結算推薦: {len(recs)} 筆")
    success = sum(1 for r in recs if r['result'] == 'success')
    fail = len(recs) - success
    orig_accuracy = success / len(recs) * 100
    print(f"原始準確率: {success}/{len(recs)} = {orig_accuracy:.1f}%")
    print()

    # 2. 補抓營收和持股數據
    rev_cache = load_revenue_cache()
    ratio_cache = load_foreign_ratio_cache()

    all_codes = list(set(r['code'] for r in recs))
    print(f"補抓缺少的數據... ({len(all_codes)} 檔)")

    missing_rev = [c for c in all_codes if c not in rev_cache]
    missing_ratio = [c for c in all_codes if c not in ratio_cache]

    for i, code in enumerate(missing_rev):
        fetch_revenue_if_missing(code, rev_cache)
        if (i + 1) % 5 == 0:
            print(f"  營收: {i+1}/{len(missing_rev)}", flush=True)
            time.sleep(1)
        else:
            time.sleep(0.3)

    for i, code in enumerate(missing_ratio):
        fetch_ratio_if_missing(code, ratio_cache)
        if (i + 1) % 5 == 0:
            print(f"  持股: {i+1}/{len(missing_ratio)}", flush=True)
            time.sleep(1)
        else:
            time.sleep(0.3)

    # 儲存更新的快取
    with open(CACHE_DIR / "revenue_cache.json", 'w', encoding='utf-8') as f:
        json.dump(rev_cache, f, ensure_ascii=False)
    with open(CACHE_DIR / "foreign_ratio_cache.json", 'w', encoding='utf-8') as f:
        json.dump(ratio_cache, f, ensure_ascii=False)

    print(f"  營收快取: {len(rev_cache)} 檔, 持股快取: {len(ratio_cache)} 檔")
    print()

    # 3. 對每筆推薦計算調整分數
    print("計算調整分數...")
    print()

    adjusted_recs = []
    adjustments_applied = {'revenue_plus': 0, 'revenue_minus': 0, 'ratio_plus': 0, 'ratio_minus': 0}

    for rec in recs:
        code = rec['code']
        date = rec['date']
        score = rec['score']
        adj_score = score
        adj_reasons = []

        # 營收檢查
        yoy, decline_streak = get_revenue_yoy(code, date, rev_cache)

        # 近5日回檔幅度
        pullback = get_5d_change(code, date)

        if yoy is not None and yoy >= 30 and pullback is not None and pullback <= -2:
            adj_score += 5
            adj_reasons.append(f"營收+{yoy:.0f}%+回檔{pullback:.1f}%→+5")
            adjustments_applied['revenue_plus'] += 1
        elif yoy is not None and yoy >= 10 and pullback is not None and pullback <= -5:
            adj_score += 5
            adj_reasons.append(f"營收+{yoy:.0f}%+回檔{pullback:.1f}%→+5")
            adjustments_applied['revenue_plus'] += 1
        elif decline_streak >= 3:
            adj_score -= 5
            adj_reasons.append(f"連續衰退{decline_streak}月→-5")
            adjustments_applied['revenue_minus'] += 1

        # 外資持股比檢查
        ratio_change = get_ratio_change(code, date, ratio_cache)

        if ratio_change is not None:
            if ratio_change > 0.5:
                adj_score += 5
                adj_reasons.append(f"持股比+{ratio_change:.2f}%→+5")
                adjustments_applied['ratio_plus'] += 1
            elif ratio_change <= -0.1:
                adj_score -= 3
                adj_reasons.append(f"持股比{ratio_change:.2f}%→-3")
                adjustments_applied['ratio_minus'] += 1

        adjusted_recs.append({
            **rec,
            'adj_score': adj_score,
            'adj_reasons': adj_reasons,
            'score_diff': adj_score - score,
        })

    print(f"調整統計:")
    print(f"  營收加分: {adjustments_applied['revenue_plus']} 次")
    print(f"  營收扣分: {adjustments_applied['revenue_minus']} 次")
    print(f"  持股比加分: {adjustments_applied['ratio_plus']} 次")
    print(f"  持股比扣分: {adjustments_applied['ratio_minus']} 次")
    print()

    # 4. 分析影響
    print("=" * 60)
    print("  模擬結果")
    print("=" * 60)
    print()

    # 4a: 分數被扣到 <65 的（原本會被推薦，新規則會排除）
    would_exclude = [r for r in adjusted_recs if r['score'] >= 65 and r['adj_score'] < 65]
    print(f"新規則會排除的推薦（原 ≥65 → 調整後 <65）: {len(would_exclude)} 檔")
    if would_exclude:
        excluded_success = sum(1 for r in would_exclude if r['result'] == 'success')
        excluded_fail = sum(1 for r in would_exclude if r['result'] == 'fail')
        print(f"  其中 success={excluded_success}, fail={excluded_fail}")
        for r in would_exclude:
            print(f"  {r['date']} {r['code']} {r['name']} {r['score']}→{r['adj_score']} {r['result']} {r['adj_reasons']}")
    print()

    # 4b: 分數有調整的成功率比較
    adjusted_up = [r for r in adjusted_recs if r['score_diff'] > 0]
    adjusted_down = [r for r in adjusted_recs if r['score_diff'] < 0]
    no_change = [r for r in adjusted_recs if r['score_diff'] == 0]

    print(f"分數上調: {len(adjusted_up)} 檔")
    if adjusted_up:
        s = sum(1 for r in adjusted_up if r['result'] == 'success')
        print(f"  準確率: {s}/{len(adjusted_up)} = {s/len(adjusted_up)*100:.1f}%")

    print(f"分數下調: {len(adjusted_down)} 檔")
    if adjusted_down:
        s = sum(1 for r in adjusted_down if r['result'] == 'success')
        print(f"  準確率: {s}/{len(adjusted_down)} = {s/len(adjusted_down)*100:.1f}%")

    print(f"無變化: {len(no_change)} 檔")
    if no_change:
        s = sum(1 for r in no_change if r['result'] == 'success')
        print(f"  準確率: {s}/{len(no_change)} = {s/len(no_change)*100:.1f}%")
    print()

    # 4c: 整體影響（假設排除 adj_score < 65 的）
    remaining = [r for r in adjusted_recs if r['adj_score'] >= 65]
    remaining_success = sum(1 for r in remaining if r['result'] == 'success')
    remaining_total = len(remaining)
    new_accuracy = remaining_success / remaining_total * 100 if remaining_total > 0 else 0

    print("=" * 60)
    print(f"  原始: {success}/{len(recs)} = {orig_accuracy:.1f}%")
    print(f"  新規則: {remaining_success}/{remaining_total} = {new_accuracy:.1f}%")
    print(f"  變化: {new_accuracy - orig_accuracy:+.1f}%  (排除了 {len(recs) - remaining_total} 檔)")
    print("=" * 60)
    print()

    # 5. 逐檔細節（有調整的）
    changed = [r for r in adjusted_recs if r['score_diff'] != 0]
    if changed:
        print(f"有調整的推薦明細 ({len(changed)} 檔):")
        print(f"{'日期':<12} {'股票':>6} {'原分':>4} {'新分':>4} {'差':>4} {'結果':>8} {'原因'}")
        print("-" * 75)
        for r in sorted(changed, key=lambda x: x['score_diff']):
            reasons = ', '.join(r['adj_reasons'])
            print(f"{r['date']:<12} {r['code']:>6} {r['score']:>4} {r['adj_score']:>4} {r['score_diff']:>+4} {r['result']:>8} {reasons}")


if __name__ == "__main__":
    main()
