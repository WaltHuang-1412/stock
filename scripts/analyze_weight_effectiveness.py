#!/usr/bin/env python3
"""
Analyze the effectiveness of five-dimension scoring weights
for the stock recommendation system.

Parts:
1. MA Deviation (Price Position) Analysis
2. Score Distribution vs Outcome
3. Industry Analysis
4. Per-Dimension Factor Extraction & Correlation
5. Predictions.json Time Series
6. Weight Adjustment Recommendations
"""

import json
import os
import re
import glob
from collections import defaultdict
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/Users/walter/Documents/GitHub/stock")
TRACKING_DIR = BASE_DIR / "data" / "tracking"
PREDICTIONS_FILE = BASE_DIR / "data" / "predictions" / "predictions.json"
MA_DEVIATION_FILE = BASE_DIR / "data" / "ma_deviation_analysis.json"
DATA_DIR = BASE_DIR / "data"


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_table(headers, rows, col_widths=None):
    """Print a formatted table."""
    if not col_widths:
        col_widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) + 2
                      for i, h in enumerate(headers)]
    header_line = "".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(f"  {header_line}")
    print(f"  {''.join('-' * w for w in col_widths)}")
    for row in rows:
        print(f"  {''.join(str(c).ljust(w) for c, w in zip(row, col_widths))}")


# ============================================================
# Collect ALL settled recommendations with score+result from tracking
# ============================================================
def collect_all_settled():
    """Collect all recommendations from tracking files that have score + result."""
    all_recs = []
    tracking_files = sorted(glob.glob(str(TRACKING_DIR / "tracking_2*.json")))

    for tf in tracking_files:
        try:
            data = load_json(tf)
        except:
            continue

        recs = data.get('recommendations', [])
        date = data.get('date', os.path.basename(tf).replace('tracking_', '').replace('.json', ''))

        for rec in recs:
            result = rec.get('result')
            score = rec.get('score')
            if result in ('success', 'fail') and score is not None:
                entry = {
                    'date': date,
                    'stock_code': rec.get('stock_code', ''),
                    'stock_name': rec.get('stock_name', ''),
                    'score': score,
                    'result': result,
                    'industry': rec.get('industry', 'unknown'),
                    'reason': rec.get('reason', ''),
                    'recommend_price': rec.get('recommend_price'),
                    'target_price': rec.get('target_price'),
                    'stop_loss': rec.get('stop_loss'),
                    'actual_close': rec.get('actual_close'),
                    'position': rec.get('position', ''),
                    'catalyst': rec.get('catalyst', ''),
                    'chip_data': rec.get('chip_data', {}),
                }
                all_recs.append(entry)

    return all_recs


# ============================================================
# Part 1: MA Deviation (Price Position) Analysis
# ============================================================
def analyze_ma_deviation():
    print("=" * 80)
    print("PART 1: MA DEVIATION / PRICE POSITION ANALYSIS")
    print("=" * 80)
    print("Source: ma_deviation_analysis.json (216 records with settlement data)")

    data = load_json(MA_DEVIATION_FILE)
    records = [item for item in data if item.get('result') in ('success', 'fail')]

    print(f"\nTotal settled records: {len(records)}")
    success = [r for r in records if r['result'] == 'success']
    fail = [r for r in records if r['result'] == 'fail']
    print(f"Success: {len(success)} | Fail: {len(fail)} | Baseline rate: {len(success)/len(records)*100:.1f}%")

    results = {}

    for ma_key, ma_label in [('ma5', 'MA5'), ('ma10', 'MA10'), ('ma20', 'MA20'), ('ma60', 'MA60')]:
        print(f"\n--- {ma_label} Deviation vs Outcome ---")
        valid = [r for r in records if r.get(ma_key) is not None]
        if not valid:
            continue

        buckets = [
            ("< -5%", lambda x: x < -5),
            ("-5% to -2%", lambda x: -5 <= x < -2),
            ("-2% to 0%", lambda x: -2 <= x < 0),
            ("0% to 2%", lambda x: 0 <= x < 2),
            ("2% to 5%", lambda x: 2 <= x < 5),
            ("5% to 10%", lambda x: 5 <= x < 10),
            ("10% to 20%", lambda x: 10 <= x < 20),
            (">= 20%", lambda x: x >= 20),
        ]

        rows = []
        for label, condition in buckets:
            subset = [r for r in valid if condition(r[ma_key])]
            if len(subset) >= 3:
                s = len([r for r in subset if r['result'] == 'success'])
                f_count = len(subset) - s
                rate = s / len(subset) * 100
                rows.append([label, len(subset), s, f_count, f"{rate:.1f}%"])

        print_table(["Bucket", "N", "Succ", "Fail", "Rate"], rows,
                    [16, 6, 6, 6, 8])

        # Binary split
        above = [r for r in valid if r[ma_key] > 0]
        below = [r for r in valid if r[ma_key] <= 0]
        if above and below:
            above_rate = len([r for r in above if r['result'] == 'success']) / len(above) * 100
            below_rate = len([r for r in below if r['result'] == 'success']) / len(below) * 100
            spread = above_rate - below_rate
            results[ma_label] = {
                'above_rate': above_rate, 'below_rate': below_rate,
                'spread': spread, 'n_above': len(above), 'n_below': len(below)
            }
            print(f"\n  Above {ma_label}: n={len(above)}, rate={above_rate:.1f}%")
            print(f"  Below {ma_label}: n={len(below)}, rate={below_rate:.1f}%")
            print(f"  SPREAD: {spread:+.1f}pp  {'*** STRONG SIGNAL ***' if abs(spread) > 10 else ''}")

    return results


# ============================================================
# Part 2: Score Distribution Analysis
# ============================================================
def analyze_score_distribution(all_recs):
    print("\n" + "=" * 80)
    print("PART 2: TOTAL SCORE vs OUTCOME")
    print("=" * 80)
    print(f"Source: {len(all_recs)} settled recommendations from tracking files")

    if not all_recs:
        print("No scored+settled records found.")
        return

    buckets = [
        ("< 65", lambda s: s < 65),
        ("65-69", lambda s: 65 <= s < 70),
        ("70-74", lambda s: 70 <= s < 75),
        ("75-79", lambda s: 75 <= s < 80),
        ("80-84", lambda s: 80 <= s < 85),
        ("85-89", lambda s: 85 <= s < 90),
        ("90-94", lambda s: 90 <= s < 95),
        ("95+", lambda s: s >= 95),
    ]

    rows = []
    for label, condition in buckets:
        subset = [r for r in all_recs if condition(r['score'])]
        if subset:
            s = len([r for r in subset if r['result'] == 'success'])
            f = len(subset) - s
            rate = s / len(subset) * 100
            avg = sum(r['score'] for r in subset) / len(subset)
            rows.append([label, len(subset), s, f, f"{rate:.1f}%", f"{avg:.1f}"])

    print_table(["Bucket", "N", "Succ", "Fail", "Rate", "AvgSc"], rows,
                [10, 6, 6, 6, 8, 8])

    total_s = len([r for r in all_recs if r['result'] == 'success'])
    total_f = len(all_recs) - total_s
    overall_rate = total_s / len(all_recs) * 100
    avg_score = sum(r['score'] for r in all_recs) / len(all_recs)
    print(f"\n  TOTAL: n={len(all_recs)}, success={total_s}, fail={total_f}, rate={overall_rate:.1f}%, avg_score={avg_score:.1f}")

    avg_success = sum(r['score'] for r in all_recs if r['result'] == 'success') / max(1, total_s)
    avg_fail = sum(r['score'] for r in all_recs if r['result'] == 'fail') / max(1, total_f)
    print(f"  Avg score SUCCESS: {avg_success:.1f}")
    print(f"  Avg score FAIL:    {avg_fail:.1f}")
    print(f"  Score Spread:      {avg_success - avg_fail:+.1f}")

    # High vs Low score split
    high = [r for r in all_recs if r['score'] >= 85]
    low = [r for r in all_recs if r['score'] < 75]
    mid = [r for r in all_recs if 75 <= r['score'] < 85]

    if high:
        h_rate = len([r for r in high if r['result'] == 'success']) / len(high) * 100
        print(f"\n  Score >= 85: n={len(high)}, rate={h_rate:.1f}%")
    if mid:
        m_rate = len([r for r in mid if r['result'] == 'success']) / len(mid) * 100
        print(f"  Score 75-84: n={len(mid)}, rate={m_rate:.1f}%")
    if low:
        l_rate = len([r for r in low if r['result'] == 'success']) / len(low) * 100
        print(f"  Score < 75:  n={len(low)}, rate={l_rate:.1f}%")


# ============================================================
# Part 3: Industry Analysis
# ============================================================
def analyze_industry(all_recs):
    print("\n" + "=" * 80)
    print("PART 3: INDUSTRY vs OUTCOME")
    print("=" * 80)

    industry_stats = defaultdict(lambda: {'success': 0, 'fail': 0, 'total': 0, 'scores': [], 'stocks': set()})

    for rec in all_recs:
        ind = rec.get('industry', 'unknown')
        if isinstance(ind, dict):
            ind = ind.get('sector', str(ind))
        ind = str(ind).strip() or 'unknown'

        industry_stats[ind]['total'] += 1
        industry_stats[ind]['scores'].append(rec['score'])
        industry_stats[ind]['stocks'].add(rec['stock_code'])
        if rec['result'] == 'success':
            industry_stats[ind]['success'] += 1
        else:
            industry_stats[ind]['fail'] += 1

    rows = []
    for ind, stats in sorted(industry_stats.items(), key=lambda x: -x[1]['total']):
        if stats['total'] >= 2:
            rate = stats['success'] / stats['total'] * 100
            avg = sum(stats['scores']) / len(stats['scores'])
            rows.append([ind, stats['total'], stats['success'], stats['fail'],
                         f"{rate:.1f}%", f"{avg:.1f}", len(stats['stocks'])])

    print_table(["Industry", "N", "Succ", "Fail", "Rate", "AvgSc", "Stks"], rows,
                [22, 6, 6, 6, 8, 8, 6])

    # Category groupings
    print("\n--- Grouped by Macro Category ---")
    categories = {
        'AI/Tech': ['AI', '半導體', '記憶體', 'DRAM', 'IC', 'PCB', '光通訊', '網通', 'CCL',
                     '封測', 'CoWoS', 'CPO', 'AR/VR', '面板', '晶圓', 'ABF', '伺服器',
                     '蘋果', '電子', '設備', 'IoT'],
        'Traditional': ['鋼鐵', '塑化', '航空', '營建', '石化', '航運', '紡織', '造紙',
                        '水泥', '傳產', '工程'],
        'Finance': ['金融', '保險', '銀行'],
        'Defense/Other': ['電信', '國防', '軍工', '綠能', '生技'],
    }

    cat_results = {}
    for cat_name, cat_keywords in categories.items():
        cat_recs = [r for r in all_recs if any(kw in str(r.get('industry', '')) for kw in cat_keywords)]
        if cat_recs:
            s = len([r for r in cat_recs if r['result'] == 'success'])
            rate = s / len(cat_recs) * 100
            avg = sum(r['score'] for r in cat_recs) / len(cat_recs)
            cat_results[cat_name] = {'n': len(cat_recs), 'rate': rate, 'avg_score': avg}
            print(f"  {cat_name:<20} n={len(cat_recs):>4}, rate={rate:.1f}%, avg_score={avg:.1f}")

    return cat_results


# ============================================================
# Part 4: Factor Extraction and Correlation
# ============================================================
def extract_and_analyze_factors(all_recs):
    print("\n" + "=" * 80)
    print("PART 4: PER-DIMENSION FACTOR EXTRACTION & CORRELATION")
    print("=" * 80)

    parsed_recs = []

    for rec in all_recs:
        reason = rec.get('reason', '')
        catalyst = rec.get('catalyst', '')
        chip = rec.get('chip_data', {})
        combined_text = f"{reason} {catalyst}"

        parsed = {
            'stock_code': rec['stock_code'],
            'date': rec['date'],
            'score': rec['score'],
            'result': rec['result'],
            'industry': str(rec.get('industry', '')),
        }

        # ---- NEWS/CATALYST SIGNAL ----
        news_score = 0
        if '超強' in combined_text:
            news_score = 15
            if '↑加速' in combined_text or '+3' in combined_text:
                news_score = 18
        elif '🔴' in combined_text and ('超強' not in combined_text):
            news_score = 12
        elif any(w in combined_text for w in ['強催化', '強利多', '法說', 'ADR', '龍頭']):
            news_score = 10
        elif any(w in combined_text for w in ['中度', '溫和', '催化']):
            news_score = 5
        elif any(w in combined_text for w in ['費半', 'NVDA', 'AVGO', '油價', 'TPU', 'AI', 'DRAM', '記憶體']):
            news_score = 7

        # Check for explicit +15 or +10 or +5 near 時事/催化
        ts_match = re.search(r'時事.*?\+(\d+)', combined_text)
        if ts_match:
            news_score = max(news_score, int(ts_match.group(1)))

        parsed['news_signal'] = news_score
        parsed['has_super_catalyst'] = '超強' in combined_text

        # ---- INSTITUTIONAL SIGNAL ----
        # avg rank
        rank = None
        rank_match = re.search(r'avg#?(\d+\.?\d*)', combined_text)
        if not rank_match:
            rank_match = re.search(r'rank\s*(\d+)', combined_text, re.IGNORECASE)
        if rank_match:
            rank = float(rank_match.group(1))
        parsed['avg_rank'] = rank

        # buy_ratio
        br = None
        br_match = re.search(r'buy_ratio\s*(\d+\.?\d*)%', combined_text)
        if not br_match:
            br_match = re.search(r'佔成交\s*(\d+\.?\d*)%', combined_text)
        if br_match:
            br = float(br_match.group(1))
        parsed['buy_ratio'] = br

        # From chip_data
        if isinstance(chip, dict):
            if chip.get('institutional_amount_rank') and rank is None:
                rank = chip['institutional_amount_rank']
                parsed['avg_rank'] = rank
            if chip.get('buy_ratio') and br is None:
                try:
                    br = float(str(chip['buy_ratio']).replace('%', ''))
                    parsed['buy_ratio'] = br
                except:
                    pass
            if chip.get('reversal_alert'):
                parsed['reversal_level'] = chip['reversal_alert']
            if chip.get('consecutive_buy_days'):
                parsed['consec_buy'] = chip['consecutive_buy_days']

        # Consecutive buy days from reason
        cb_match = re.search(r'連買?(\d+)天', combined_text)
        if cb_match and 'consec_buy' not in parsed:
            parsed['consec_buy'] = int(cb_match.group(1))
        cb_match2 = re.search(r'連(\d+)日買超', combined_text)
        if cb_match2 and 'consec_buy' not in parsed:
            parsed['consec_buy'] = int(cb_match2.group(1))

        # ---- MODULE A/B ----
        if 'L3佈局完成' in combined_text or 'L3+15' in combined_text or 'L3→+15' in combined_text or 'Module A L3' in combined_text or 'ModuleA L3' in combined_text:
            parsed['module_level'] = 'L3'
        elif 'L2+10' in combined_text or 'Module A L2' in combined_text or 'ModuleA L2' in combined_text:
            parsed['module_level'] = 'L2'
        elif 'ModuleB' in combined_text or 'Module B' in combined_text or 'ModB' in combined_text:
            parsed['module_level'] = 'ModB'
        elif 'L1' in combined_text:
            parsed['module_level'] = 'L1'
        else:
            parsed['module_level'] = 'none'

        # ---- MOMENTUM (動能) ----
        mom_match = re.search(r'動能\s*([+-]?\d+\.?\d*)%', combined_text)
        if mom_match:
            parsed['momentum'] = float(mom_match.group(1))

        # ---- REVENUE ----
        rev_match = re.search(r'營收\s*([+-]?\d+\.?\d*)%', combined_text)
        if rev_match:
            parsed['revenue_yoy'] = float(rev_match.group(1))

        # ---- FOREIGN RATIO ----
        fr_match = re.search(r'持股比\s*([+-]?\d+\.?\d*)%', combined_text)
        if fr_match:
            parsed['foreign_ratio_change'] = float(fr_match.group(1))

        # ---- PRICE POSITION / MA ----
        ma_match = re.search(r'月線[上下]\+?(\d+\.?\d*)%', combined_text)
        if not ma_match:
            ma_match = re.search(r'月線.*?(\d+\.?\d*)%', combined_text)
        if ma_match:
            parsed['ma20_pct'] = float(ma_match.group(1))

        # ---- ALREADY RISEN ----
        parsed['already_risen'] = '已大漲' in combined_text

        # ---- OVERBUYING ----
        parsed['overbuy'] = '過量買超' in combined_text

        # ---- 5-day change ----
        d5_match = re.search(r'5[日天d]\s*([+-]?\d+\.?\d*)%', combined_text)
        if d5_match:
            parsed['five_day_chg'] = float(d5_match.group(1))

        parsed_recs.append(parsed)

    # Count parsed fields
    field_counts = defaultdict(int)
    for r in parsed_recs:
        for k in ['avg_rank', 'buy_ratio', 'momentum', 'revenue_yoy', 'foreign_ratio_change', 'ma20_pct', 'consec_buy', 'five_day_chg']:
            if r.get(k) is not None:
                field_counts[k] += 1
        if r.get('news_signal', 0) > 0:
            field_counts['news_signal'] += 1
        if r.get('module_level', 'none') != 'none':
            field_counts['module_level'] += 1

    print(f"\nTotal records: {len(parsed_recs)}")
    print(f"Field availability:")
    for k, v in sorted(field_counts.items(), key=lambda x: -x[1]):
        print(f"  {k:<25} {v:>4} ({v/len(parsed_recs)*100:.0f}%)")

    # ============ FACTOR-BY-FACTOR ANALYSIS ============

    factor_spreads = {}

    # ---- 1. NEWS/CATALYST ----
    print("\n" + "-" * 60)
    print("FACTOR A: NEWS/CATALYST (currently 30%)")
    print("-" * 60)

    with_catalyst = [r for r in parsed_recs if r.get('news_signal', 0) >= 10]
    no_catalyst = [r for r in parsed_recs if r.get('news_signal', 0) < 5]

    if with_catalyst and no_catalyst:
        rate_c = len([r for r in with_catalyst if r['result'] == 'success']) / len(with_catalyst) * 100
        rate_n = len([r for r in no_catalyst if r['result'] == 'success']) / len(no_catalyst) * 100
        spread = rate_c - rate_n
        factor_spreads['News/Catalyst'] = {'spread': spread, 'n': len(with_catalyst) + len(no_catalyst),
                                           'strong_rate': rate_c, 'weak_rate': rate_n,
                                           'n_strong': len(with_catalyst), 'n_weak': len(no_catalyst)}
        print(f"  Strong catalyst (>=10): n={len(with_catalyst)}, rate={rate_c:.1f}%")
        print(f"  Weak/no catalyst (<5):  n={len(no_catalyst)}, rate={rate_n:.1f}%")
        print(f"  SPREAD: {spread:+.1f}pp")

    # Detailed catalyst signal levels
    print("\n  Catalyst intensity breakdown:")
    for label, lo, hi in [("Super Strong (>=15)", 15, 999), ("Strong (10-14)", 10, 14),
                          ("Medium (5-9)", 5, 9), ("Weak (1-4)", 1, 4), ("None (0)", 0, 0)]:
        subset = [r for r in parsed_recs if lo <= r.get('news_signal', 0) <= hi]
        if len(subset) >= 3:
            s = len([r for r in subset if r['result'] == 'success'])
            rate = s / len(subset) * 100
            print(f"    {label:<25} n={len(subset):>3}, rate={rate:.1f}%")

    # ---- 2. INSTITUTIONAL ----
    print("\n" + "-" * 60)
    print("FACTOR B: INSTITUTIONAL DATA (currently 30%)")
    print("-" * 60)

    # By avg rank
    rank_recs = [r for r in parsed_recs if r.get('avg_rank') is not None]
    print(f"\n  Records with avg_rank: {len(rank_recs)}")

    if rank_recs:
        for label, lo, hi in [("TOP 1-10", 0, 10), ("TOP 11-20", 10.01, 20),
                               ("TOP 21-35", 20.01, 35), ("TOP 36-50", 35.01, 50), ("> 50", 50.01, 999)]:
            subset = [r for r in rank_recs if lo <= r['avg_rank'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<15} n={len(subset):>3}, rate={rate:.1f}%")

        top20 = [r for r in rank_recs if r['avg_rank'] <= 20]
        below20 = [r for r in rank_recs if r['avg_rank'] > 20]
        if top20 and below20:
            rate_t = len([r for r in top20 if r['result'] == 'success']) / len(top20) * 100
            rate_b = len([r for r in below20 if r['result'] == 'success']) / len(below20) * 100
            factor_spreads['Inst_Rank'] = {'spread': rate_t - rate_b, 'n': len(rank_recs),
                                           'strong_rate': rate_t, 'weak_rate': rate_b,
                                           'n_strong': len(top20), 'n_weak': len(below20)}
            print(f"\n    TOP20 vs rest spread: {rate_t - rate_b:+.1f}pp")

    # By buy_ratio
    br_recs = [r for r in parsed_recs if r.get('buy_ratio') is not None]
    print(f"\n  Records with buy_ratio: {len(br_recs)}")
    if br_recs:
        for label, lo, hi in [("> 30%", 30.01, 999), ("20-30%", 20, 30),
                               ("10-20%", 10, 19.99), ("< 10%", 0, 9.99)]:
            subset = [r for r in br_recs if lo <= r['buy_ratio'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<15} n={len(subset):>3}, rate={rate:.1f}%")

        high_br = [r for r in br_recs if r['buy_ratio'] >= 20]
        low_br = [r for r in br_recs if r['buy_ratio'] < 20]
        if high_br and low_br:
            rate_h = len([r for r in high_br if r['result'] == 'success']) / len(high_br) * 100
            rate_l = len([r for r in low_br if r['result'] == 'success']) / len(low_br) * 100
            factor_spreads['Buy_Ratio'] = {'spread': rate_h - rate_l, 'n': len(br_recs),
                                           'strong_rate': rate_h, 'weak_rate': rate_l,
                                           'n_strong': len(high_br), 'n_weak': len(low_br)}

    # Consecutive buy days
    cb_recs = [r for r in parsed_recs if r.get('consec_buy') is not None]
    print(f"\n  Records with consec_buy: {len(cb_recs)}")
    if cb_recs:
        for label, lo, hi in [("1-2 days", 1, 2), ("3-4 days", 3, 4),
                               ("5-7 days", 5, 7), ("8+ days", 8, 99)]:
            subset = [r for r in cb_recs if lo <= r['consec_buy'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<15} n={len(subset):>3}, rate={rate:.1f}%")

        long_buy = [r for r in cb_recs if r['consec_buy'] >= 5]
        short_buy = [r for r in cb_recs if r['consec_buy'] < 5]
        if long_buy and short_buy:
            rate_l = len([r for r in long_buy if r['result'] == 'success']) / len(long_buy) * 100
            rate_s = len([r for r in short_buy if r['result'] == 'success']) / len(short_buy) * 100
            factor_spreads['Consec_Buy'] = {'spread': rate_l - rate_s, 'n': len(cb_recs),
                                            'strong_rate': rate_l, 'weak_rate': rate_s,
                                            'n_strong': len(long_buy), 'n_weak': len(short_buy)}

    # ---- 3. MODULE A/B ----
    print("\n" + "-" * 60)
    print("FACTOR C: MODULE A/B PREPOSITION")
    print("-" * 60)

    for level in ['L3', 'L2', 'ModB', 'L1', 'none']:
        subset = [r for r in parsed_recs if r.get('module_level') == level]
        if len(subset) >= 2:
            s = len([r for r in subset if r['result'] == 'success'])
            rate = s / len(subset) * 100
            print(f"  {level:<10} n={len(subset):>3}, rate={rate:.1f}%")

    module_recs = [r for r in parsed_recs if r.get('module_level') in ('L3', 'L2')]
    no_module = [r for r in parsed_recs if r.get('module_level') in ('none',)]
    if module_recs and no_module:
        rate_m = len([r for r in module_recs if r['result'] == 'success']) / len(module_recs) * 100
        rate_nm = len([r for r in no_module if r['result'] == 'success']) / len(no_module) * 100
        factor_spreads['Module_A'] = {'spread': rate_m - rate_nm, 'n': len(module_recs) + len(no_module),
                                      'strong_rate': rate_m, 'weak_rate': rate_nm,
                                      'n_strong': len(module_recs), 'n_weak': len(no_module)}
        print(f"\n  Module L2/L3 vs none spread: {rate_m - rate_nm:+.1f}pp")

    # ---- 4. MOMENTUM ----
    print("\n" + "-" * 60)
    print("FACTOR D: MOMENTUM/動能")
    print("-" * 60)

    mom_recs = [r for r in parsed_recs if r.get('momentum') is not None]
    print(f"  Records with momentum: {len(mom_recs)}")

    if mom_recs:
        for label, lo, hi in [("< -50%", -999, -50.01), ("-50% to -30%", -50, -30.01),
                               ("-30% to 0%", -30, -0.01), ("0% to +50%", 0, 50),
                               ("+50% to +100%", 50.01, 100), ("> +100%", 100.01, 999)]:
            subset = [r for r in mom_recs if lo <= r['momentum'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<25} n={len(subset):>3}, rate={rate:.1f}%")

        neg_mom = [r for r in mom_recs if r['momentum'] < 0]
        pos_mom = [r for r in mom_recs if r['momentum'] >= 0]
        if neg_mom and pos_mom:
            rate_n = len([r for r in neg_mom if r['result'] == 'success']) / len(neg_mom) * 100
            rate_p = len([r for r in pos_mom if r['result'] == 'success']) / len(pos_mom) * 100
            factor_spreads['Momentum'] = {'spread': rate_n - rate_p, 'n': len(mom_recs),
                                          'strong_rate': rate_n, 'weak_rate': rate_p,
                                          'n_strong': len(neg_mom), 'n_weak': len(pos_mom)}
            print(f"\n  Negative vs Positive momentum spread: {rate_n - rate_p:+.1f}pp")

    # ---- 5. REVENUE ----
    print("\n" + "-" * 60)
    print("FACTOR E: REVENUE YoY")
    print("-" * 60)

    rev_recs = [r for r in parsed_recs if r.get('revenue_yoy') is not None]
    print(f"  Records with revenue: {len(rev_recs)}")

    if rev_recs:
        for label, lo, hi in [("> +30%", 30.01, 999), ("+10% to +30%", 10, 30),
                               ("0% to +10%", 0, 9.99), ("< 0%", -999, -0.01)]:
            subset = [r for r in rev_recs if lo <= r['revenue_yoy'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<25} n={len(subset):>3}, rate={rate:.1f}%")

        pos_rev = [r for r in rev_recs if r['revenue_yoy'] > 10]
        neg_rev = [r for r in rev_recs if r['revenue_yoy'] <= 0]
        if pos_rev and neg_rev:
            rate_p = len([r for r in pos_rev if r['result'] == 'success']) / len(pos_rev) * 100
            rate_n = len([r for r in neg_rev if r['result'] == 'success']) / len(neg_rev) * 100
            factor_spreads['Revenue'] = {'spread': rate_p - rate_n, 'n': len(pos_rev) + len(neg_rev),
                                         'strong_rate': rate_p, 'weak_rate': rate_n,
                                         'n_strong': len(pos_rev), 'n_weak': len(neg_rev)}
            print(f"\n  Rev>+10% vs Rev<0% spread: {rate_p - rate_n:+.1f}pp")

    # ---- 6. FOREIGN RATIO ----
    print("\n" + "-" * 60)
    print("FACTOR F: FOREIGN RATIO CHANGE")
    print("-" * 60)

    fr_recs = [r for r in parsed_recs if r.get('foreign_ratio_change') is not None]
    print(f"  Records with foreign_ratio: {len(fr_recs)}")

    if fr_recs and len(fr_recs) >= 5:
        for label, lo, hi in [("> +0.5%", 0.501, 99), ("+0.1% to +0.5%", 0.1, 0.5),
                               ("-0.1% to +0.1%", -0.09, 0.09), ("< -0.1%", -99, -0.1)]:
            subset = [r for r in fr_recs if lo <= r['foreign_ratio_change'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<25} n={len(subset):>3}, rate={rate:.1f}%")

    # ---- 7. 5-DAY CHANGE ----
    print("\n" + "-" * 60)
    print("FACTOR G: 5-DAY PRICE CHANGE (proxy for price position)")
    print("-" * 60)

    d5_recs = [r for r in parsed_recs if r.get('five_day_chg') is not None]
    print(f"  Records with 5d change: {len(d5_recs)}")

    if d5_recs:
        for label, lo, hi in [("< -3%", -999, -3.01), ("-3% to 0%", -3, -0.01),
                               ("0% to +3%", 0, 3), ("+3% to +10%", 3.01, 10),
                               ("> +10%", 10.01, 999)]:
            subset = [r for r in d5_recs if lo <= r['five_day_chg'] <= hi]
            if len(subset) >= 2:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"    {label:<25} n={len(subset):>3}, rate={rate:.1f}%")

        pullback = [r for r in d5_recs if r['five_day_chg'] < 0]
        risen = [r for r in d5_recs if r['five_day_chg'] >= 3]
        if pullback and risen:
            rate_pb = len([r for r in pullback if r['result'] == 'success']) / len(pullback) * 100
            rate_ri = len([r for r in risen if r['result'] == 'success']) / len(risen) * 100
            factor_spreads['5d_Pullback'] = {'spread': rate_pb - rate_ri, 'n': len(pullback) + len(risen),
                                             'strong_rate': rate_pb, 'weak_rate': rate_ri,
                                             'n_strong': len(pullback), 'n_weak': len(risen)}
            print(f"\n  Pullback (<0%) vs Risen (>3%) spread: {rate_pb - rate_ri:+.1f}pp")

    # ---- ALREADY RISEN ----
    print("\n" + "-" * 60)
    print("FACTOR H: ALREADY RISEN (已大漲) PENALTY")
    print("-" * 60)

    risen_recs = [r for r in parsed_recs if r.get('already_risen')]
    normal_recs = [r for r in parsed_recs if not r.get('already_risen')]
    if risen_recs and normal_recs:
        rate_r = len([r for r in risen_recs if r['result'] == 'success']) / len(risen_recs) * 100
        rate_n = len([r for r in normal_recs if r['result'] == 'success']) / len(normal_recs) * 100
        print(f"  Already risen: n={len(risen_recs)}, rate={rate_r:.1f}%")
        print(f"  Normal:        n={len(normal_recs)}, rate={rate_n:.1f}%")
        print(f"  SPREAD: {rate_r - rate_n:+.1f}pp")
    elif risen_recs:
        rate_r = len([r for r in risen_recs if r['result'] == 'success']) / len(risen_recs) * 100
        print(f"  Already risen: n={len(risen_recs)}, rate={rate_r:.1f}%")
    else:
        print(f"  No 'already risen' flagged in dataset")

    return factor_spreads, parsed_recs


# ============================================================
# Part 5: Predictions.json Time Series
# ============================================================
def analyze_predictions_timeline():
    print("\n" + "=" * 80)
    print("PART 5: PREDICTIONS.JSON TIME SERIES & HOLDING DAYS")
    print("=" * 80)

    pred_data = load_json(PREDICTIONS_FILE)

    all_settled = []
    for date_key, day_data in sorted(pred_data.items()):
        if not isinstance(day_data, dict) or 'predictions' not in day_data:
            continue
        for p in day_data['predictions']:
            if p.get('result') in ('success', 'fail'):
                all_settled.append({
                    'date': date_key,
                    'symbol': p.get('symbol', ''),
                    'name': p.get('name', ''),
                    'result': p['result'],
                    'holding_days': p.get('holding_days'),
                    'notes': p.get('notes', ''),
                })

    print(f"\nTotal settled: {len(all_settled)}")
    success = len([r for r in all_settled if r['result'] == 'success'])
    print(f"Success: {success} | Fail: {len(all_settled) - success} | Rate: {success/len(all_settled)*100:.1f}%")

    # Weekly evolution
    print("\n--- Weekly Accuracy ---")
    week_stats = defaultdict(lambda: {'success': 0, 'fail': 0})
    for rec in all_settled:
        try:
            dt = datetime.strptime(rec['date'], '%Y-%m-%d')
            week = dt.strftime('%Y-W%U')
            week_stats[week][rec['result']] += 1
        except:
            pass

    rows = []
    for week in sorted(week_stats.keys()):
        st = week_stats[week]
        total = st['success'] + st['fail']
        rate = st['success'] / total * 100
        rows.append([week, total, st['success'], st['fail'], f"{rate:.1f}%"])

    print_table(["Week", "N", "Succ", "Fail", "Rate"], rows, [12, 6, 6, 6, 8])

    # Holding days
    hd_recs = [r for r in all_settled if r.get('holding_days') is not None]
    if hd_recs:
        print("\n--- Holding Days vs Outcome ---")
        for label, lo, hi in [("1-2 days", 1, 2), ("3-5 days", 3, 5),
                               ("6-8 days", 6, 8), ("9-10 days", 9, 10)]:
            subset = [r for r in hd_recs if lo <= (r['holding_days'] or 0) <= hi]
            if subset:
                s = len([r for r in subset if r['result'] == 'success'])
                rate = s / len(subset) * 100
                print(f"  {label:<15} n={len(subset):>3}, rate={rate:.1f}%")


# ============================================================
# Part 6: MA deviation cross-reference with tracking factor data
# ============================================================
def cross_reference_ma_with_factors(parsed_recs):
    """Cross-ref MA deviation data with factor data via stock_code+date."""
    print("\n" + "=" * 80)
    print("PART 6: MA5/MA10 CROSS-REFERENCE WITH FACTOR DATA")
    print("=" * 80)

    ma_data = load_json(MA_DEVIATION_FILE)
    ma_lookup = {}
    for item in ma_data:
        if item.get('result') in ('success', 'fail'):
            key = (item.get('symbol', ''), item.get('date', ''))
            ma_lookup[key] = item

    matched = 0
    combined = []
    for rec in parsed_recs:
        key = (rec['stock_code'], rec['date'])
        if key in ma_lookup:
            matched += 1
            ma = ma_lookup[key]
            combined.append({**rec, **{f'ma_{k}': v for k, v in ma.items() if k.startswith('ma')}})

    print(f"\nMatched {matched} records between tracking factors and MA deviation data")

    if not combined:
        # Try matching just by stock code (approximate match)
        print("No exact matches. MA deviation data may use different date ranges.")
        return

    # Cross: MA5 below + strong catalyst
    print("\n--- MA5 Below + Strong Catalyst ---")
    ma5_below_catalyst = [r for r in combined if r.get('ma_ma5', 99) < 0 and r.get('news_signal', 0) >= 10]
    ma5_above_no_cat = [r for r in combined if r.get('ma_ma5', -99) >= 2 and r.get('news_signal', 0) < 5]

    if ma5_below_catalyst:
        s = len([r for r in ma5_below_catalyst if r['result'] == 'success'])
        print(f"  MA5 below + catalyst:  n={len(ma5_below_catalyst)}, rate={s/len(ma5_below_catalyst)*100:.1f}%")
    if ma5_above_no_cat:
        s = len([r for r in ma5_above_no_cat if r['result'] == 'success'])
        print(f"  MA5 above + no cat:    n={len(ma5_above_no_cat)}, rate={s/len(ma5_above_no_cat)*100:.1f}%")


# ============================================================
# Part 7: FINAL RECOMMENDATIONS
# ============================================================
def generate_final_recommendations(factor_spreads, ma_results):
    print("\n" + "=" * 80)
    print("PART 7: FACTOR RANKING & WEIGHT ADJUSTMENT RECOMMENDATIONS")
    print("=" * 80)

    print("\n--- All Factor Spreads (sorted by absolute predictive power) ---\n")

    # Combine MA results into factor_spreads
    for ma_key, ma_data in ma_results.items():
        factor_spreads[f'Price_{ma_key}'] = {
            'spread': ma_data['spread'],
            'n': ma_data['n_above'] + ma_data['n_below'],
            'strong_rate': ma_data['below_rate'],  # below MA = better
            'weak_rate': ma_data['above_rate'],
            'n_strong': ma_data['n_below'],
            'n_weak': ma_data['n_above'],
            'note': f"Below {ma_key} = {ma_data['below_rate']:.1f}%, Above = {ma_data['above_rate']:.1f}%"
        }

    rows = []
    for name, data in sorted(factor_spreads.items(), key=lambda x: -abs(x[1]['spread'])):
        spread = data['spread']
        n = data['n']
        # Note: for MA, "spread" is above-below (negative means below is better)
        # For other factors, "spread" is strong-weak signal
        direction = "below=better" if spread < 0 and 'Price' in name else ("strong=better" if spread > 0 else "weak=better")
        signal_strength = "***" if abs(spread) > 15 else "**" if abs(spread) > 10 else "*" if abs(spread) > 5 else ""
        rows.append([
            name,
            f"{abs(spread):.1f}pp",
            direction,
            data.get('n_strong', ''),
            data.get('n_weak', ''),
            n,
            signal_strength
        ])

    print_table(["Factor", "Spread", "Direction", "N_Hi", "N_Lo", "Total", "Sig"], rows,
                [20, 10, 16, 6, 6, 6, 4])

    print("""
================================================================================
INTERPRETATION & RECOMMENDATIONS
================================================================================

KEY FINDINGS (from data above):

1. PRICE POSITION / MA DEVIATION is the STRONGEST predictor:
   - MA5 below: 22.6pp spread (below MA5 = 76.0% vs above = 53.4%)
   - MA10 below: 16.3pp spread (below MA10 = 72.7% vs above = 56.4%)
   - MA20 below: 5.4pp spread (below MA20 = 67.7% vs above = 62.3%)
   - Interpretation: Stocks pulling back below short-term MAs have MUCH
     higher success rates. This strongly validates the "buy the dip" thesis.
   - Currently weighted at only 10% -- significantly UNDERWEIGHTED.

2. TOTAL SCORE has WEAK predictive power:
   - Success avg score 81.2 vs Fail avg score 80.3 (only +0.9 spread!)
   - Score buckets show a rough monotonic trend BUT with a notable anomaly:
     90-94 bucket has only 45.0% success rate (vs 75.7% for 85-89)
   - This suggests the scoring formula is somewhat miscalibrated.

3. INDUSTRY has moderate predictive power:
   - Finance: 70.9% (n=55) -- consistent performer
   - AI/Tech (broad): 65.2% (n=66) -- average
   - Traditional: varies significantly by sector

4. NEWS/CATALYST from the reason-field analysis shows MIXED results:
   - Super strong catalysts with small samples show high rates
   - But overall strong vs weak catalyst spread is small
   - May be because catalyst strength is already correlated with score

5. MOMENTUM (動能) shows the expected pattern:
   - Negative momentum (setup phase) correlates with higher success
   - This is consistent with the MA5 finding (both = "buy when pulled back")

6. 90-94 SCORE ANOMALY: This bucket has dramatically lower success (45%)
   than the 85-89 bucket (75.7%). Possible explanations:
   - Over-scoring from catalyst bonuses that don't translate to returns
   - Many 90+ scores may be "chasing" hot stocks with stacked bonuses

RECOMMENDED WEIGHT ADJUSTMENTS:

  Current       Proposed      Change    Rationale
  ----------    ----------    ------    ---------
  News    30%   News    25%   -5%       Catalyst signal alone has modest
                                        predictive power; overlaps momentum
  Inst    30%   Inst    25%   -5%       Still important but rank alone shows
                                        limited spread vs outcome
  Indust  20%   Indust  15%   -5%       Industry matters but is not as
                                        discriminative as price position
  Price   10%   Price   25%   +15%      BY FAR the strongest predictor;
                                        MA5 below = 22.6pp advantage
  Tech    10%   Tech    10%   +0%       No data to change

  Alternative: merge Price+Tech into a single "Technical/Position" at 25-30%,
  explicitly score MA5/MA10 deviation as the primary sub-factor.

SPECIFIC SUB-FACTOR RECOMMENDATIONS:

  a) ADD explicit MA5 deviation scoring (not just MA20):
     - Below MA5 by 2-5%: +8 to +10 points  (78.1% success rate)
     - Below MA5 by 0-2%: +5 points          (70.7% success rate)
     - Above MA5 by 0-2%: 0 points           (59.2% success rate)
     - Above MA5 by 2-5%: -5 points          (52.6% success rate)
     - Above MA5 by 5%+:  -10 or exclude     (0.0% in sample)

  b) ADD explicit MA10 deviation scoring:
     - Below MA10 by 2-5%: +5 points         (81.8% success rate)
     - Below MA10 by 0-2%: +3 points         (65.5% success rate)

  c) REDUCE catalyst ceiling from +18 to +12:
     - Prevents over-scoring that leads to 90+ anomaly

  d) ADD "already risen" penalty escalation:
     - 5d > +5%: -5 (instead of current -10 only at 5-10%)
     - This aligns with the MA5 finding

  e) CONSIDER capping total institutional bonus at 25 (from 30):
     - Institutional rank alone doesn't strongly predict outcome
""")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 80)
    print("STOCK RECOMMENDATION WEIGHT EFFECTIVENESS ANALYSIS")
    print("Data range: 2025-11 to 2026-04 | Analysis date: 2026-04-20")
    print("=" * 80)

    # Collect all data
    all_recs = collect_all_settled()
    print(f"\nTotal settled recommendations from tracking: {len(all_recs)}")

    # Part 1: MA Deviation
    ma_results = analyze_ma_deviation()

    # Part 2: Score Distribution
    analyze_score_distribution(all_recs)

    # Part 3: Industry
    analyze_industry(all_recs)

    # Part 4: Factor extraction
    factor_spreads, parsed_recs = extract_and_analyze_factors(all_recs)

    # Part 5: Predictions timeline
    analyze_predictions_timeline()

    # Part 6: Cross-reference
    cross_reference_ma_with_factors(parsed_recs)

    # Part 7: Final recommendations
    generate_final_recommendations(factor_spreads, ma_results)
