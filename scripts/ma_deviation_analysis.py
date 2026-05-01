#!/usr/bin/env python3
"""
MA Deviation Analysis: Which moving average deviation best predicts success/failure?

Reads predictions.json, fetches historical prices from Yahoo Finance,
calculates deviation from MA5/MA10/MA20/MA60 at entry time,
and analyzes which MA best separates winners from losers.
"""

import json
import time
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from yahoo_finance_api import get_history

PREDICTIONS_PATH = str(Path(__file__).parent.parent / "data" / "predictions" / "predictions.json")

def load_settled_recommendations():
    """Load all settled (success/fail) recommendations with recommend_price."""
    with open(PREDICTIONS_PATH) as f:
        data = json.load(f)

    settled = []
    for date_key, day_data in data.items():
        if not isinstance(day_data, dict):
            continue
        preds = day_data.get('predictions', [])
        for p in preds:
            result = p.get('result', '')
            rp = p.get('recommend_price')
            if result in ('success', 'fail') and rp:
                settled.append({
                    'date': date_key,
                    'symbol': p.get('symbol'),
                    'name': p.get('name', ''),
                    'recommend_price': float(rp),
                    'result': result,
                })
    return settled


def fetch_historical_prices(symbol, retries=2):
    """Fetch ~300 days of historical prices from Yahoo Finance."""
    for attempt in range(retries + 1):
        try:
            history = get_history(symbol, period='300d', interval='1d')
            if not history or 'timestamps' not in history:
                raise ValueError("No data returned")

            timestamps = history['timestamps']
            closes = history['closes']

            # Convert timestamps to dates
            prices = []
            for ts, close in zip(timestamps, closes):
                if close is not None:
                    dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    prices.append((dt, float(close)))
            return prices
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            else:
                print(f"  ERROR fetching {symbol}: {e}")
                return None


def calculate_mas(closes, idx, periods=[5, 10, 20, 60]):
    """Calculate moving averages at a given index."""
    mas = {}
    for p in periods:
        if idx >= p - 1:
            ma_val = sum(closes[idx - p + 1:idx + 1]) / p
            mas[f'ma{p}'] = ma_val
        else:
            mas[f'ma{p}'] = None
    return mas


def find_entry_index(prices, recommend_date, recommend_price):
    """
    Find the index in the price series closest to the recommendation date.
    Strategy: Look for the date match first, then closest price match nearby.
    """
    dates = [p[0] for p in prices]
    closes = [p[1] for p in prices]

    # Try exact date match
    if recommend_date in dates:
        idx = dates.index(recommend_date)
        return idx

    # Try day before (recommendation might be based on prev day close)
    rec_dt = datetime.strptime(recommend_date, '%Y-%m-%d')
    for delta in range(0, 5):
        check_date = (rec_dt - timedelta(days=delta)).strftime('%Y-%m-%d')
        if check_date in dates:
            return dates.index(check_date)

    # Try day after
    for delta in range(1, 5):
        check_date = (rec_dt + timedelta(days=delta)).strftime('%Y-%m-%d')
        if check_date in dates:
            return dates.index(check_date)

    # Last resort: find closest price match in the last 30 entries
    best_idx = None
    best_diff = float('inf')
    search_start = max(0, len(closes) - 60)
    for i in range(search_start, len(closes)):
        diff = abs(closes[i] - recommend_price)
        if diff < best_diff:
            best_diff = diff
            best_idx = i

    return best_idx


def main():
    print("=" * 90)
    print("MA DEVIATION ANALYSIS - Which MA best predicts success/failure?")
    print("=" * 90)
    print()

    # Step 1: Load settled recommendations
    settled = load_settled_recommendations()
    print(f"Loaded {len(settled)} settled recommendations ({sum(1 for s in settled if s['result']=='success')} success, {sum(1 for s in settled if s['result']=='fail')} fail)")
    print()

    # Deduplicate: same symbol+date+recommend_price, keep first
    seen = set()
    unique_settled = []
    for s in settled:
        key = (s['symbol'], s['date'], s['recommend_price'])
        if key not in seen:
            seen.add(key)
            unique_settled.append(s)
    settled = unique_settled
    print(f"After dedup: {len(settled)} unique recommendations")
    print()

    # Step 2: Fetch prices and calculate deviations
    # Cache prices by symbol to avoid redundant API calls
    price_cache = {}
    results = []
    errors = []

    unique_symbols = sorted(set(s['symbol'] for s in settled))
    print(f"Fetching prices for {len(unique_symbols)} unique symbols...")
    print()

    for i, symbol in enumerate(unique_symbols):
        print(f"  [{i+1}/{len(unique_symbols)}] Fetching {symbol}...", end=" ", flush=True)
        prices = fetch_historical_prices(symbol)
        if prices:
            price_cache[symbol] = prices
            print(f"OK ({len(prices)} days)")
        else:
            print("FAILED")
        time.sleep(0.5)

    print()
    print(f"Successfully fetched: {len(price_cache)}/{len(unique_symbols)} symbols")
    print()

    # Step 3: Calculate deviations for each recommendation
    print("-" * 90)
    print(f"{'Date':<12} {'Sym':<6} {'Name':<8} {'RecPrice':>9} {'Result':<8} {'vs_MA5':>8} {'vs_MA10':>8} {'vs_MA20':>8} {'vs_MA60':>8}")
    print("-" * 90)

    for s in settled:
        symbol = s['symbol']
        if symbol not in price_cache:
            errors.append(f"{symbol} ({s['date']}): no price data")
            continue

        prices = price_cache[symbol]
        closes = [p[1] for p in prices]

        idx = find_entry_index(prices, s['date'], s['recommend_price'])
        if idx is None or idx < 60:
            # Need at least 60 days for MA60
            if idx is not None and idx >= 20:
                # Can still do MA5/10/20
                pass
            elif idx is not None and idx >= 5:
                pass
            else:
                errors.append(f"{symbol} ({s['date']}): insufficient history (idx={idx})")
                continue

        mas = calculate_mas(closes, idx)

        rec_price = s['recommend_price']
        deviations = {}
        for ma_name, ma_val in mas.items():
            if ma_val and ma_val > 0:
                dev = (rec_price - ma_val) / ma_val * 100
                deviations[ma_name] = round(dev, 2)
            else:
                deviations[ma_name] = None

        entry = {
            'date': s['date'],
            'symbol': symbol,
            'name': s.get('name', ''),
            'recommend_price': rec_price,
            'result': s['result'],
            'entry_close': closes[idx],
            'entry_date_actual': prices[idx][0],
            **deviations,
        }
        results.append(entry)

        # Print raw data
        vs5 = f"{deviations.get('ma5', 'N/A'):>7.2f}%" if deviations.get('ma5') is not None else "    N/A"
        vs10 = f"{deviations.get('ma10', 'N/A'):>7.2f}%" if deviations.get('ma10') is not None else "    N/A"
        vs20 = f"{deviations.get('ma20', 'N/A'):>7.2f}%" if deviations.get('ma20') is not None else "    N/A"
        vs60 = f"{deviations.get('ma60', 'N/A'):>7.2f}%" if deviations.get('ma60') is not None else "    N/A"

        name = (s.get('name') or '')[:6]
        print(f"{s['date']:<12} {symbol:<6} {name:<8} {rec_price:>9.1f} {s['result']:<8} {vs5:>8} {vs10:>8} {vs20:>8} {vs60:>8}")

    print("-" * 90)
    print(f"Total data points: {len(results)}")
    print()

    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print()

    # Step 4: Analysis
    print("=" * 90)
    print("ANALYSIS: Success Rate by MA Deviation Buckets")
    print("=" * 90)
    print()

    ma_names = ['ma5', 'ma10', 'ma20', 'ma60']
    buckets = [
        ('<-10%', -999, -10),
        ('-10~-5%', -10, -5),
        ('-5~0%', -5, 0),
        ('0~3%', 0, 3),
        ('3~5%', 3, 5),
        ('5~10%', 5, 10),
        ('10~15%', 10, 15),
        ('15~20%', 15, 20),
        ('>20%', 20, 999),
    ]

    for ma_name in ma_names:
        print(f"\n{'='*60}")
        print(f"  {ma_name.upper()} Deviation Analysis")
        print(f"{'='*60}")
        print(f"{'Bucket':<12} {'Total':>6} {'Success':>8} {'Fail':>6} {'WinRate':>9} {'AvgDev':>8}")
        print(f"{'-'*12} {'-'*6} {'-'*8} {'-'*6} {'-'*9} {'-'*8}")

        total_with_data = 0
        bucket_data = []

        for label, lo, hi in buckets:
            in_bucket = [r for r in results if r.get(ma_name) is not None and lo <= r[ma_name] < hi]
            success = sum(1 for r in in_bucket if r['result'] == 'success')
            fail = sum(1 for r in in_bucket if r['result'] == 'fail')
            total = success + fail
            total_with_data += total

            if total > 0:
                win_rate = success / total * 100
                avg_dev = sum(r[ma_name] for r in in_bucket) / total
                significance = "***" if total >= 20 else "**" if total >= 10 else "*" if total >= 5 else ""
                print(f"{label:<12} {total:>6} {success:>8} {fail:>6} {win_rate:>8.1f}% {avg_dev:>7.1f}% {significance}")
                bucket_data.append((label, total, success, fail, win_rate, avg_dev))
            else:
                print(f"{label:<12} {total:>6} {'':>8} {'':>6} {'':>9} {'':>8}")

        print(f"\n  Total with {ma_name} data: {total_with_data}")

        # Find best threshold
        if bucket_data:
            # Try each possible threshold point
            valid_data = [(r[ma_name], r['result']) for r in results if r.get(ma_name) is not None]
            if valid_data:
                thresholds = [-10, -5, -3, 0, 3, 5, 7, 10, 15, 20]
                print(f"\n  Threshold Analysis (below vs above):")
                print(f"  {'Threshold':>10} | {'Below':>6}  {'WR_below':>9} | {'Above':>6}  {'WR_above':>9} | {'Diff':>7}")
                print(f"  {'-'*10}-+-{'-'*6}--{'-'*9}-+-{'-'*6}--{'-'*9}-+-{'-'*7}")

                best_diff = 0
                best_threshold = None

                for t in thresholds:
                    below = [(d, r) for d, r in valid_data if d < t]
                    above = [(d, r) for d, r in valid_data if d >= t]

                    if len(below) >= 5 and len(above) >= 5:
                        wr_below = sum(1 for _, r in below if r == 'success') / len(below) * 100
                        wr_above = sum(1 for _, r in above if r == 'success') / len(above) * 100
                        diff = wr_below - wr_above

                        marker = ""
                        if abs(diff) > abs(best_diff):
                            best_diff = diff
                            best_threshold = t

                        print(f"  {t:>9}% | {len(below):>6}  {wr_below:>8.1f}% | {len(above):>6}  {wr_above:>8.1f}% | {diff:>+6.1f}%")

                if best_threshold is not None:
                    print(f"\n  ** Best threshold for {ma_name}: {best_threshold}% (win rate diff: {best_diff:+.1f}%)")

    # Step 5: Cross-MA comparison
    print("\n" + "=" * 90)
    print("CROSS-MA COMPARISON: Which MA is most predictive?")
    print("=" * 90)
    print()

    # For each MA, calculate correlation with outcome
    print(f"{'MA':<8} {'N':>5} {'Avg_Win':>9} {'Avg_Lose':>10} {'Diff':>8} {'Best_Thr':>10} {'WR<Thr':>8} {'WR>=Thr':>9} {'Spread':>8}")
    print("-" * 85)

    ma_summary = []
    for ma_name in ma_names:
        valid = [(r[ma_name], r['result']) for r in results if r.get(ma_name) is not None]
        if not valid:
            continue

        wins = [d for d, r in valid if r == 'success']
        losses = [d for d, r in valid if r == 'fail']

        avg_win = sum(wins) / len(wins) if wins else 0
        avg_lose = sum(losses) / len(losses) if losses else 0

        # Find best split threshold
        best_spread = 0
        best_t = 0
        best_wr_below = 0
        best_wr_above = 0

        for t in range(-15, 25):
            below = [(d, r) for d, r in valid if d < t]
            above = [(d, r) for d, r in valid if d >= t]
            if len(below) >= 10 and len(above) >= 10:
                wr_b = sum(1 for _, r in below if r == 'success') / len(below) * 100
                wr_a = sum(1 for _, r in above if r == 'success') / len(above) * 100
                spread = abs(wr_b - wr_a)
                if spread > best_spread:
                    best_spread = spread
                    best_t = t
                    best_wr_below = wr_b
                    best_wr_above = wr_a

        print(f"{ma_name:<8} {len(valid):>5} {avg_win:>8.2f}% {avg_lose:>9.2f}% {avg_win-avg_lose:>7.2f}% {best_t:>9}% {best_wr_below:>7.1f}% {best_wr_above:>8.1f}% {best_spread:>7.1f}%")
        ma_summary.append((ma_name, len(valid), avg_win, avg_lose, best_t, best_wr_below, best_wr_above, best_spread))

    # Step 6: Detailed breakdown for the most predictive MA
    print()
    if ma_summary:
        best_ma = max(ma_summary, key=lambda x: x[7])
        print(f"WINNER: {best_ma[0].upper()} with {best_ma[7]:.1f}% win rate spread at threshold {best_ma[4]}%")
        print(f"  Below {best_ma[4]}%: {best_ma[5]:.1f}% win rate")
        print(f"  Above {best_ma[4]}%: {best_ma[6]:.1f}% win rate")

    # Step 7: Combined signal analysis
    print("\n" + "=" * 90)
    print("COMBINED SIGNAL: MA20 + MA60 interaction")
    print("=" * 90)
    print()

    # 2D analysis: MA20 deviation vs MA60 deviation
    both_valid = [r for r in results if r.get('ma20') is not None and r.get('ma60') is not None]
    if both_valid:
        print(f"Data points with both MA20 and MA60: {len(both_valid)}")
        print()

        # Categorize
        categories = {
            'Below MA20 & Below MA60': lambda r: r['ma20'] < 0 and r['ma60'] < 0,
            'Below MA20 & Above MA60': lambda r: r['ma20'] < 0 and r['ma60'] >= 0,
            'Above MA20 & Below MA60': lambda r: r['ma20'] >= 0 and r['ma60'] < 0,
            'Above MA20 & Above MA60': lambda r: r['ma20'] >= 0 and r['ma60'] >= 0,
        }

        print(f"{'Category':<30} {'Total':>6} {'Success':>8} {'Fail':>6} {'WinRate':>9}")
        print("-" * 65)
        for cat_name, cat_fn in categories.items():
            in_cat = [r for r in both_valid if cat_fn(r)]
            success = sum(1 for r in in_cat if r['result'] == 'success')
            fail = len(in_cat) - success
            wr = success / len(in_cat) * 100 if in_cat else 0
            sig = "***" if len(in_cat) >= 20 else "**" if len(in_cat) >= 10 else "*" if len(in_cat) >= 5 else ""
            print(f"{cat_name:<30} {len(in_cat):>6} {success:>8} {fail:>6} {wr:>8.1f}% {sig}")

    # Step 8: Overextended analysis (practical thresholds)
    print("\n" + "=" * 90)
    print("PRACTICAL RECOMMENDATIONS")
    print("=" * 90)
    print()

    for ma_name in ma_names:
        valid = [r for r in results if r.get(ma_name) is not None]
        if not valid:
            continue

        # Test specific penalty thresholds
        for thresh in [3, 5, 7, 10]:
            overext = [r for r in valid if r[ma_name] >= thresh]
            not_overext = [r for r in valid if r[ma_name] < thresh]

            if len(overext) >= 5 and len(not_overext) >= 5:
                wr_over = sum(1 for r in overext if r['result'] == 'success') / len(overext) * 100
                wr_not = sum(1 for r in not_overext if r['result'] == 'success') / len(not_overext) * 100

                if wr_not - wr_over >= 5:
                    print(f"  {ma_name.upper()}: Penalty at >={thresh}% deviation -> WR drops from {wr_not:.1f}% to {wr_over:.1f}% (delta={wr_not-wr_over:.1f}%, n_over={len(overext)}, n_under={len(not_overext)})")

    # Step 9: Below MA analysis (potential buy signal)
    print()
    print("Below-MA (potential contrarian buy signal):")
    for ma_name in ma_names:
        valid = [r for r in results if r.get(ma_name) is not None]
        if not valid:
            continue

        for thresh in [-10, -5, -3, 0]:
            below = [r for r in valid if r[ma_name] < thresh]
            if len(below) >= 5:
                wr = sum(1 for r in below if r['result'] == 'success') / len(below) * 100
                print(f"  {ma_name.upper()} < {thresh}%: WR={wr:.1f}% (n={len(below)})")

    # Final summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print()
    print("Note: *** = n>=20, ** = n>=10, * = n>=5 (statistical significance indicator)")
    print(f"Total analyzed: {len(results)} recommendations out of {len(settled)} settled")
    print(f"Overall win rate: {sum(1 for r in results if r['result']=='success')/len(results)*100:.1f}%")
    print()

    # Save raw data for further analysis
    output_path = str(Path(__file__).parent.parent / "data" / "ma_deviation_analysis.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Raw data saved to: {output_path}")


if __name__ == '__main__':
    main()
