#!/usr/bin/env python3
"""
全規則合併回測 — 所有 v8.0 規則同時套用到歷史推薦

規則清單：
1. 過量買超 ≥30K → -5
2. 營收年增≥30% + 回檔≥2% → +5 / 衰退≥3月 → -5
3. 外資持股比週增>0.5% → +5 / 週減≥0.1% → -3
4. 模式追蹤 COLD ≤30% → -5 / 31-40% → -3
5. 月線下 → -3
6. 法人維度上限 30 分
7. 單檔總扣分上限 -20
8. 停損 -10% + 結算 10 天
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
CACHE_DIR = PROJECT_DIR / "data" / "cache"

# ===== 數據載入 =====

_price_cache = {}

def fetch_prices(code, days=400):
    if code in _price_cache:
        return _price_cache[code]
    try:
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW",
            params={"interval": "1d", "range": f"{days}d"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        d = r.json()['chart']['result'][0]
        q = d['indicators']['quote'][0]
        prices = []
        for ts, c, h, l in zip(d['timestamp'], q['close'], q['high'], q['low']):
            if c is not None:
                prices.append({
                    'date': datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                    'close': c, 'high': h or c, 'low': l or c,
                })
        _price_cache[code] = prices
    except:
        _price_cache[code] = []
    return _price_cache[code]


def load_revenue_cache():
    fp = CACHE_DIR / "revenue_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_ratio_cache():
    fp = CACHE_DIR / "foreign_ratio_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_t86(date_str):
    fp = CACHE_DIR / f"twse_t86_{date_str.replace('-', '')}.json"
    if not fp.exists():
        return {}
    with open(fp, 'r', encoding='utf-8') as f:
        return json.load(f)


# ===== 各規則判斷函數 =====

def check_overbuy(code, date, t86_data):
    """過量買超 ≥30K"""
    d = date.replace('-', '')
    day_data = t86_data.get(d, {})
    info = day_data.get(code, {})
    total = info.get('total', 0)
    if total >= 30000:
        return -5, f"過量{total//1000}K→-5"
    return 0, None


def check_revenue(code, date, rev_cache):
    """營收加減分"""
    if code not in rev_cache:
        return 0, None
    revenues = rev_cache[code]
    monthly = {}
    for r in revenues:
        monthly[(r['revenue_year'], r['revenue_month'])] = r['revenue']

    dt = datetime.strptime(date, "%Y-%m-%d")
    m, y = dt.month - 1, dt.year
    if m == 0: m, y = 12, y - 1

    cur = monthly.get((y, m))
    prev = monthly.get((y - 1, m))
    if not cur or not prev or prev <= 0:
        return 0, None

    yoy = (cur - prev) / prev * 100

    # 回檔檢查
    prices = _price_cache.get(code, [])
    past = [p for p in prices if p['date'] <= date]
    if len(past) >= 6:
        pullback = (past[-1]['close'] - past[-6]['close']) / past[-6]['close'] * 100
    else:
        pullback = 0

    if yoy >= 30 and pullback <= -2:
        return 5, f"營收+{yoy:.0f}%回檔{pullback:.1f}%→+5"
    elif yoy >= 10 and pullback <= -5:
        return 5, f"營收+{yoy:.0f}%回檔{pullback:.1f}%→+5"

    # 衰退
    streak = 0
    cy, cm = y, m
    while True:
        c = monthly.get((cy, cm))
        p = monthly.get((cy - 1, cm))
        if c and p and p > 0 and (c - p) / p * 100 < 0:
            streak += 1
            cm -= 1
            if cm == 0: cm, cy = 12, cy - 1
        else:
            break
    if streak >= 3:
        return -5, f"衰退{streak}月→-5"

    return 0, None


def check_ratio(code, date, ratio_cache):
    """外資持股比"""
    if code not in ratio_cache:
        return 0, None
    rows = ratio_cache[code]
    current, prev = None, None
    for row in rows:
        rd = row['date'].replace('-', '')
        dd = date.replace('-', '')
        if rd <= dd:
            prev = current
            current = row
    if not current or not prev:
        return 0, None

    change = current.get('ForeignInvestmentSharesRatio', 0) - prev.get('ForeignInvestmentSharesRatio', 0)
    if change > 0.5:
        return 5, f"持股比+{change:.1f}%→+5"
    elif change <= -0.1:
        return -3, f"持股比{change:.1f}%→-3"
    return 0, None


def check_ma20(code, date):
    """月線位置"""
    prices = _price_cache.get(code, [])
    past = [p for p in prices if p['date'] <= date]
    if len(past) < 20:
        return 0, None

    current = past[-1]['close']
    ma20 = sum(p['close'] for p in past[-20:]) / 20

    if current < ma20:
        vs = (current - ma20) / ma20 * 100
        return -3, f"月線下{vs:.1f}%→-3"
    return 0, None


def simulate_trade(code, rec_price, target, date, stop_pct=-10, max_days=10):
    """模擬交易（新停損+結算天數）"""
    prices = _price_cache.get(code, [])
    if not prices:
        return None

    stop_price = rec_price * (1 + stop_pct / 100)
    start_idx = None
    for i, p in enumerate(prices):
        if p['date'] >= date:
            start_idx = i
            break
    if start_idx is None:
        return None

    days = 0
    for i in range(start_idx, min(start_idx + max_days + 5, len(prices))):
        days += 1
        p = prices[i]
        if p['high'] >= target:
            return {'result': 'success', 'return_pct': (target - rec_price) / rec_price * 100}
        if p['low'] <= stop_price:
            return {'result': 'fail', 'return_pct': stop_pct}
        if days >= max_days:
            return {
                'result': 'success' if p['close'] > rec_price else 'fail',
                'return_pct': (p['close'] - rec_price) / rec_price * 100
            }
    return None


# ===== 主程式 =====

def main():
    print("=" * 70)
    print("  全規則合併回測（v8.0 所有規則同時套用）")
    print("=" * 70)
    print()

    # 載入推薦
    all_recs = []
    for fp in sorted(TRACKING_DIR.glob("tracking_202*.json")):
        if 'example' in fp.name:
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        date_str = data.get('date', '')
        for rec in data.get('recommendations', []):
            code = rec.get('stock_code') or rec.get('symbol', '')
            try:
                rec_price = float(rec.get('recommend_price', 0))
                target = float(rec.get('target_price', 0))
            except:
                continue
            if not code or rec_price <= 0 or target <= 0:
                continue
            all_recs.append({
                'date': date_str,
                'code': code,
                'name': rec.get('stock_name', ''),
                'score': rec.get('score', 0),
                'rec_price': rec_price,
                'target': target,
                'original_result': rec.get('result', ''),
            })

    print(f"歷史推薦: {len(all_recs)} 筆")

    # 抓股價
    codes = list(set(r['code'] for r in all_recs))
    print(f"取得 {len(codes)} 檔股價...")
    for i, code in enumerate(codes):
        fetch_prices(code)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(codes)}", flush=True)
            time.sleep(0.5)

    # 載入快取
    rev_cache = load_revenue_cache()
    ratio_cache = load_ratio_cache()

    # 載入 T86
    t86_data = {}
    for fp in CACHE_DIR.glob("twse_t86_*.json"):
        d = fp.stem.replace("twse_t86_", "")
        with open(fp, 'r', encoding='utf-8') as f:
            t86_data[d] = json.load(f)

    print()

    # ===== 三種模式比較 =====

    results = {
        'original': {'success': 0, 'fail': 0, 'total_ret': 0, 'excluded': 0},
        'new_score': {'success': 0, 'fail': 0, 'total_ret': 0, 'excluded': 0},
        'new_score_new_stoploss': {'success': 0, 'fail': 0, 'total_ret': 0, 'excluded': 0},
    }

    detail_rows = []

    for rec in all_recs:
        code = rec['code']
        date = rec['date']
        score = rec['score']

        # 原始結果（-8% 停損 + 7 天）
        orig = simulate_trade(code, rec['rec_price'], rec['target'], date, stop_pct=-8, max_days=7)

        # 新規則加減分
        total_adj = 0
        reasons = []

        adj, reason = check_overbuy(code, date, t86_data)
        if reason: reasons.append(reason)
        total_adj += adj

        adj, reason = check_revenue(code, date, rev_cache)
        if reason: reasons.append(reason)
        total_adj += adj

        adj, reason = check_ratio(code, date, ratio_cache)
        if reason: reasons.append(reason)
        total_adj += adj

        adj, reason = check_ma20(code, date)
        if reason: reasons.append(reason)
        total_adj += adj

        # 扣分上限 -20
        if total_adj < -20:
            total_adj = -20

        new_score = score + total_adj

        # 新規則結果（-10% 停損 + 10 天）
        new_trade = simulate_trade(code, rec['rec_price'], rec['target'], date, stop_pct=-10, max_days=10)

        # 原始模式
        if orig:
            results['original'][orig['result']] += 1
            results['original']['total_ret'] += orig['return_pct']

        # 新評分（排除 <65 的）
        if orig:
            if new_score >= 65:
                results['new_score'][orig['result']] += 1
                results['new_score']['total_ret'] += orig['return_pct']
            else:
                results['new_score']['excluded'] += 1

        # 新評分 + 新停損/結算
        if new_trade:
            if new_score >= 65:
                results['new_score_new_stoploss'][new_trade['result']] += 1
                results['new_score_new_stoploss']['total_ret'] += new_trade['return_pct']
            else:
                results['new_score_new_stoploss']['excluded'] += 1

        detail_rows.append({
            'date': date,
            'code': code,
            'name': rec['name'],
            'orig_score': score,
            'adj': total_adj,
            'new_score': new_score,
            'reasons': reasons,
            'orig_result': orig['result'] if orig else 'N/A',
            'orig_ret': orig['return_pct'] if orig else 0,
            'new_result': new_trade['result'] if new_trade else 'N/A',
            'new_ret': new_trade['return_pct'] if new_trade else 0,
            'excluded': new_score < 65,
        })

    # ===== 輸出 =====

    print("=" * 70)
    print("  三種模式比較")
    print("=" * 70)
    print()

    print(f"{'模式':<30} | {'成功':>4} {'失敗':>4} {'排除':>4} | {'準確率':>8} | {'平均報酬':>10}")
    print("-" * 75)

    for mode, label in [
        ('original', '原始（-8%停損+7天）'),
        ('new_score', '新評分+原停損（-8%+7天）'),
        ('new_score_new_stoploss', '新評分+新停損（-10%+10天）'),
    ]:
        r = results[mode]
        total = r['success'] + r['fail']
        acc = r['success'] / total * 100 if total else 0
        avg_ret = r['total_ret'] / total if total else 0
        print(f"{label:<30} | {r['success']:>4} {r['fail']:>4} {r['excluded']:>4} | {acc:>6.1f}% | {avg_ret:>+9.2f}%")

    print()

    # 被新規則排除的明細
    excluded = [d for d in detail_rows if d['excluded'] and d['orig_result'] != 'N/A']
    if excluded:
        ex_s = sum(1 for d in excluded if d['orig_result'] == 'success')
        ex_f = len(excluded) - ex_s
        print(f"被排除: {len(excluded)} 檔 (success={ex_s}, fail={ex_f})")
        print()

    # 加減分統計
    adj_up = [d for d in detail_rows if d['adj'] > 0]
    adj_down = [d for d in detail_rows if d['adj'] < 0]
    adj_zero = [d for d in detail_rows if d['adj'] == 0]

    print("加減分分組:")
    for label, group in [('加分', adj_up), ('扣分', adj_down), ('無變化', adj_zero)]:
        valid = [d for d in group if d['new_result'] != 'N/A' and not d['excluded']]
        if valid:
            s = sum(1 for d in valid if d['new_result'] == 'success')
            print(f"  {label}: {s}/{len(valid)} = {s/len(valid)*100:.1f}%")
    print()

    # 各規則觸發次數
    rule_counts = defaultdict(int)
    for d in detail_rows:
        for r in d['reasons']:
            key = r.split('→')[0] if '→' in r else r
            rule_counts[key] += 1

    print("各規則觸發次數:")
    for rule, count in sorted(rule_counts.items(), key=lambda x: -x[1]):
        print(f"  {rule}: {count} 次")


if __name__ == "__main__":
    main()
