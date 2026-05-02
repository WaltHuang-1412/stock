#!/usr/bin/env python3
"""
催化主題預警工具 v1.0 — 搶在法人前面進場

核心邏輯：
    美股龍頭連續上漲 → 對應台股產業還沒動 → 法人還沒進場 → 預先佈局

    與 Module A（catalyst_preposition_scan.py）的差異：
    - Module A：法人已經在買，股價還沒動 → 跟在法人後面
    - Module B：催化劑正在升溫，法人還沒買 → 搶在法人前面

三層訊號：
    🔥 強訊號：美股龍頭累計>+10% or 連3天上漲 → 台股還沒動 → 進場 5-10%
    🟢 中訊號：美股龍頭累計>+5%  or 連2天上漲 → 台股還沒動 → 觀察/小倉 5%
    🟡 弱訊號：美股龍頭單日>+3%               → 台股還沒動 → 僅觀察

使用方式：
    python3 scripts/catalyst_theme_detector.py                    # 今天
    python3 scripts/catalyst_theme_detector.py --date 2026-03-20  # 指定日期
    python3 scripts/catalyst_theme_detector.py --lookback 10      # 回看10天

輸出：
    data/YYYY-MM-DD/catalyst_theme_signals.json
    Console 報告（含預先佈局候選股）
"""

import sys
import io
import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import warnings
warnings.filterwarnings('ignore')

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'

# 直接 import chip_analysis / reversal_alert（避免 subprocess 開銷 + 共享快取）
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from chip_analysis import analyze_chip_history as _analyze_chip_history
    HAS_CHIP_ANALYSIS = True
except ImportError:
    HAS_CHIP_ANALYSIS = False

try:
    from reversal_alert import detect_reversal as _detect_reversal
    HAS_REVERSAL_ALERT = True
except ImportError:
    HAS_REVERSAL_ALERT = False

# 超大型股排除（市值太大，不在TOP50不代表沒人買，意義不同）
MEGA_CAP_EXCLUDE = {
    '2330',  # 台積電
    '2317',  # 鴻海
    '2454',  # 聯發科
    '2308',  # 台達電
    '2412',  # 中華電
}

# ============================================================
# 美股龍頭 → 台股產業對照（從 us_leader_alert.py 同步）
# ============================================================

def _load_leader_mapping():
    """從 data/us_leader_mapping.json 讀取龍頭對應表"""
    mapping_file = Path(__file__).parent.parent / 'data' / 'us_leader_mapping.json'
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        result = {}
        for name, info in data.get('leaders', {}).items():
            result[name] = {
                'tw_industry': info.get('tw_industry', ''),
                'tw_stocks': info.get('tw_stocks', {}),
                'industry_chain_key': info.get('industry_chain_key', ''),
            }
        groups = data.get('industry_groups', {})
        return result, groups
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[WARN] 無法讀取 {mapping_file}: {e}", file=sys.stderr)
        return {}, {}

US_LEADER_TO_TW, INDUSTRY_GROUPS = _load_leader_mapping()


def get_available_dates(target_date, lookback=7):
    """取得有 us_asia_markets.json 的交易日列表"""
    dates = []
    current = target_date
    for _ in range(lookback * 3):
        if len(dates) >= lookback:
            break
        date_str = current.strftime('%Y-%m-%d')
        json_path = DATA_DIR / date_str / 'us_asia_markets.json'
        if json_path.exists():
            dates.append(date_str)
        current -= timedelta(days=1)
    return dates


def load_us_market_data(date_str):
    """載入 us_asia_markets.json，提取 JSON 部分"""
    path = DATA_DIR / date_str / 'us_asia_markets.json'
    if not path.exists():
        return None

    content = path.read_text(encoding='utf-8')

    # 檔案可能包含 console 輸出 + JSON，需提取 JSON 部分
    json_match = re.search(r'\{[^{}]*"NASDAQ"[^{}]*\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # 嘗試整個檔案作為 JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def load_institutional_top50(date_str):
    """載入法人 TOP50，回傳買超 set + 各股5日漲幅 dict"""
    path = DATA_DIR / date_str / 'institutional_top50.json'
    if not path.exists():
        return set(), {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        buy_codes = set()
        price_changes = {}  # code → 5day_change
        for s in data.get('stocks', []):
            code = s.get('code', '')
            if s.get('total', 0) > 0:
                buy_codes.add(code)
            change = s.get('5day_change')
            if change is not None and code:
                price_changes[code] = change
        return buy_codes, price_changes
    except (json.JSONDecodeError, KeyError):
        return set(), {}


def load_industry_chains():
    """從 industry_chains.json 補充更多對應股票"""
    path = DATA_DIR / 'industry_chains.json'
    if not path.exists():
        return {}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 建立 industry_key → [stock_codes] 對照
    result = {}
    for key, industry in data.get('industries', {}).items():
        stocks = []
        for tier_key, tier in industry.get('tiers', {}).items():
            for stock in tier.get('stocks', []):
                stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'tier': tier_key,
                    'category': stock.get('category', ''),
                })
        result[key] = stocks
    return result


def analyze_leader_trends(dates, us_data_by_date):
    """
    分析每個美股龍頭在回看期間的趨勢

    Returns: { leader_name: { cumulative, consecutive_up, daily_changes, signal_level } }
    """
    leaders = list(US_LEADER_TO_TW.keys())
    trends = {}

    for leader in leaders:
        daily_changes = []
        for date_str in dates:
            data = us_data_by_date.get(date_str, {})
            change = data.get(leader)
            if change is not None:
                daily_changes.append({'date': date_str, 'change': change})

        if not daily_changes:
            continue

        # 累計漲幅
        cumulative = sum(d['change'] for d in daily_changes)

        # 從最近一天往回算連續上漲天數
        consecutive_up = 0
        for d in daily_changes:
            if d['change'] > 0:
                consecutive_up += 1
            else:
                break

        # 最近一天漲幅
        latest_change = daily_changes[0]['change'] if daily_changes else 0

        # 訊號強度判斷
        signal_level = 'none'
        if cumulative > 10 or consecutive_up >= 3:
            signal_level = 'strong'
        elif cumulative > 5 or consecutive_up >= 2:
            signal_level = 'moderate'
        elif latest_change > 3:
            signal_level = 'weak'
        elif cumulative > 0 and consecutive_up >= 1:
            signal_level = 'nascent'  # 剛開始，太早

        trends[leader] = {
            'cumulative': round(cumulative, 2),
            'consecutive_up': consecutive_up,
            'latest_change': round(latest_change, 2),
            'daily_changes': daily_changes,
            'signal_level': signal_level,
            'days_tracked': len(daily_changes),
        }

    return trends


def find_preposition_candidates(leader_trends, top50_codes, industry_chains, price_changes):
    """
    找出「催化劑升溫但法人還沒買」的台股

    邏輯：
    1. 美股龍頭有 moderate/strong 訊號
    2. 對應的台股不在法人 TOP50（法人還沒進場）
    3. 台股 5 日漲幅 < 10%（還沒大漲）
    4. 排除超大型股（台積電、鴻海等）
    5. = 預先佈局候選
    """
    candidates = []

    for leader, trend in leader_trends.items():
        if trend['signal_level'] in ('none', 'nascent'):
            continue

        mapping = US_LEADER_TO_TW.get(leader, {})
        tw_stocks = mapping.get('tw_stocks', {})
        industry = mapping.get('tw_industry', '')
        chain_key = mapping.get('industry_chain_key', '')

        # 合併 industry_chains.json 的股票
        all_stocks = dict(tw_stocks)
        if chain_key and chain_key in industry_chains:
            for stock in industry_chains[chain_key]:
                if stock['code'] not in all_stocks:
                    all_stocks[stock['code']] = stock['name']

        # 催化劑成熟度（綜合連漲天數 + 累計漲幅）
        # 修正：僅看 consecutive_up 會誤判。如 Micron 累計+45%但最後一天-0.76%
        #        → consecutive_up=0 → 被標「早期」，實際應為「成熟」
        maturity = 'early'  # 預設：早期
        cumulative_abs = abs(trend['cumulative'])
        if trend['consecutive_up'] >= 5 or cumulative_abs >= 30:
            maturity = 'mature'  # 成熟：連漲5天+ 或 累計>30%
        elif trend['consecutive_up'] >= 3 or cumulative_abs >= 15:
            maturity = 'mid'  # 中期：連漲3-4天 或 累計>15%

        for code, name in all_stocks.items():
            # 排除超大型股
            if code in MEGA_CAP_EXCLUDE:
                continue

            in_top50 = code in top50_codes

            # 取得台股5日漲幅
            tw_5d_change = price_changes.get(code)

            # 如果已經大漲 >10%，不算預先佈局機會
            already_moved = False
            if tw_5d_change is not None and tw_5d_change > 10:
                already_moved = True

            candidates.append({
                'code': code,
                'name': name,
                'us_leader': leader,
                'tw_industry': industry,
                'signal_level': trend['signal_level'],
                'leader_cumulative': trend['cumulative'],
                'leader_consecutive_up': trend['consecutive_up'],
                'leader_latest': trend['latest_change'],
                'in_top50': in_top50,
                'tw_5d_change': tw_5d_change,
                'already_moved': already_moved,
                'maturity': maturity,
                'status': '⚠️ 法人已進場' if in_top50 else ('📈 已大漲' if already_moved else '✅ 法人尚未進場'),
            })

    return candidates


def score_candidate(c):
    """
    計算預先佈局分數（0-100）

    高分 = 催化劑強 + 法人還沒買 + 台股還沒漲 + 催化劑還在早期
    低分 = 法人已買 or 台股已漲 or 催化劑已成熟（追高風險）
    """
    score = 0

    # 催化強度（30%）
    if c['signal_level'] == 'strong':
        score += 30
    elif c['signal_level'] == 'moderate':
        score += 20
    elif c['signal_level'] == 'weak':
        score += 10

    # 法人未進場（30%）— 核心
    if not c['in_top50']:
        score += 30
    else:
        score += 5

    # 台股未反映（20%）— 新增
    tw_change = c.get('tw_5d_change')
    if c.get('already_moved'):
        score -= 15  # 已大漲，扣分
    elif tw_change is not None:
        if tw_change < 2:
            score += 20  # 完全沒動，最佳
        elif tw_change < 5:
            score += 12  # 小漲，還可以
        elif tw_change < 10:
            score += 5   # 漲了一些，空間有限
    else:
        score += 10  # 沒有數據，中性

    # 催化劑成熟度（20%）— 新增：早期 > 中期 > 成熟
    maturity = c.get('maturity', 'early')
    if maturity == 'early':
        score += 20  # 催化剛開始，最佳進場時機
    elif maturity == 'mid':
        score += 12  # 催化確認中，還可以
    elif maturity == 'mature':
        score += 3   # 催化已成熟，追高風險，幾乎不加分

    return max(0, score)  # 不低於 0


def scan(target_date_str, lookback=7):
    """主掃描邏輯"""
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    dates = get_available_dates(target_date, lookback)

    if not dates:
        print("❌ 找不到任何 us_asia_markets.json 資料")
        return []

    print(f"🔍 催化主題預警掃描（Module B）")
    print(f"   目標日期：{target_date_str}")
    print(f"   回看天數：{len(dates)} 個交易日（{dates[-1]} ~ {dates[0]}）")
    print()

    # ─── Step 1: 載入多日美股數據 ───
    us_data_by_date = {}
    for d in dates:
        data = load_us_market_data(d)
        if data:
            us_data_by_date[d] = data

    print(f"   載入 {len(us_data_by_date)} 天美股數據")

    # ─── Step 2: 分析龍頭趨勢 ───
    leader_trends = analyze_leader_trends(dates, us_data_by_date)

    # ─── Step 3: 載入法人 TOP50（最新日期）+ 股價漲幅 ───
    # 修正：不能直接用 us_asia_markets 的 dates，因為週末快照日沒有 institutional_top50.json
    # 改為獨立掃描有 institutional_top50.json 的日期
    top50_codes = set()
    price_changes = {}  # code → latest 5day_change
    top50_dates_found = 0
    scan_date = target_date
    for _ in range(lookback * 3):  # 往回掃描，找到3天有TOP50的
        if top50_dates_found >= 3:
            break
        d = scan_date.strftime('%Y-%m-%d')
        top50_path = DATA_DIR / d / 'institutional_top50.json'
        if top50_path.exists():
            codes, changes = load_institutional_top50(d)
            top50_codes |= codes
            for code, change in changes.items():
                if code not in price_changes:
                    price_changes[code] = change
            top50_dates_found += 1
        scan_date -= timedelta(days=1)

    print(f"   近{top50_dates_found}天法人TOP50：{len(top50_codes)} 檔股票")

    # ─── Step 4: 載入產業鏈 ───
    industry_chains = load_industry_chains()

    # ─── Step 5: 找候選股 ───
    candidates = find_preposition_candidates(leader_trends, top50_codes, industry_chains, price_changes)

    # ─── Step 6: 評分排名 ───
    for c in candidates:
        c['score'] = score_candidate(c)

    # 分組：預先佈局（法人未進場+未大漲） vs 法人已進場 vs 已大漲
    preposition = [c for c in candidates
                   if not c['in_top50'] and not c.get('already_moved') and c['score'] >= 40]
    in_top50 = [c for c in candidates if c['in_top50'] and c['score'] >= 20]
    already_moved = [c for c in candidates if c.get('already_moved')]

    preposition.sort(key=lambda x: -x['score'])
    in_top50.sort(key=lambda x: -x['score'])

    # 去重（同一檔股票可能被多個龍頭指向，保留分數最高的）
    seen = set()
    deduped_pre = []
    for c in preposition:
        if c['code'] not in seen:
            seen.add(c['code'])
            deduped_pre.append(c)

    seen_in = set()
    deduped_in = []
    for c in in_top50:
        if c['code'] not in seen_in:
            seen_in.add(c['code'])
            deduped_in.append(c)

    # ─── 輸出報告 ───

    print()
    print("=" * 70)
    print(f"📡 催化主題預警報告 — {target_date_str}")
    print("=" * 70)

    # 先輸出龍頭趨勢
    print()
    print("📈 美股龍頭趨勢（回看 {}天）".format(len(dates)))
    print("-" * 60)

    signal_map = {'strong': '🔥 強', 'moderate': '🟢 中', 'weak': '🟡 弱', 'nascent': '⚪ 初', 'none': '─'}
    for leader, trend in sorted(leader_trends.items(), key=lambda x: -x[1]['cumulative']):
        sig = signal_map.get(trend['signal_level'], '─')
        cum = trend['cumulative']
        up = trend['consecutive_up']
        latest = trend['latest_change']
        industry = US_LEADER_TO_TW.get(leader, {}).get('tw_industry', '')
        print(f"  {leader:20s} 累計{cum:+7.1f}% | 連漲{up}天 | 最新{latest:+.1f}% | {sig} | → {industry}")

    maturity_label = {'early': '🟢早期', 'mid': '🟡中期', 'mature': '🔴成熟'}

    # 預先佈局候選（法人未進場 + 未大漲）
    if deduped_pre:
        print()
        print(f"🎯 預先佈局候選（法人尚未進場+台股未大漲，{len(deduped_pre)} 檔）")
        print("-" * 60)
        print("  催化劑正在升溫，但法人還沒開始買 → 進場窗口")
        print()

        for c in deduped_pre[:15]:
            level_emoji = {'strong': '🔥', 'moderate': '🟢', 'weak': '🟡'}.get(c['signal_level'], '')
            mat = maturity_label.get(c.get('maturity', ''), '')
            tw_chg = c.get('tw_5d_change')
            tw_str = f"台股5日{tw_chg:+.1f}%" if tw_chg is not None else "台股漲幅未知"
            print(f"  {level_emoji} {c['name']}({c['code']}) {c['score']}分 | {c['tw_industry']} | {mat}")
            print(f"    催化：{c['us_leader']} 累計{c['leader_cumulative']:+.1f}% 連漲{c['leader_consecutive_up']}天")
            print(f"    法人：✅ 尚未進入TOP50 | {tw_str}")
            if c.get('maturity') == 'mature':
                print(f"    ⚠️ 催化劑已成熟（連漲{c['leader_consecutive_up']}天），追高風險較高")
            print()
    else:
        print()
        print("  （無符合條件的預先佈局候選）")

    # 法人已進場（確認訊號）
    if deduped_in:
        print()
        print(f"📊 法人已進場（{len(deduped_in)} 檔，搭配 Module A 確認）")
        print("-" * 60)
        for c in deduped_in[:10]:
            tw_chg = c.get('tw_5d_change')
            tw_str = f"5日{tw_chg:+.1f}%" if tw_chg is not None else ""
            print(f"  ⚠️ {c['name']}({c['code']}) | {c['tw_industry']} | {c['us_leader']} {c['leader_cumulative']:+.1f}% | {tw_str}")

    # 已大漲排除
    if already_moved:
        moved_names = [f"{c['name']}({c['code']})" for c in already_moved[:5]]
        print(f"\n  📈 已大漲排除：{', '.join(moved_names)}")

    print()
    print("=" * 70)
    print(f"📋 統計：預先佈局 {len(deduped_pre)} 檔 / 法人已進場 {len(deduped_in)} 檔 / 已大漲排除 {len(already_moved)} 檔")
    print("=" * 70)

    # ─── Step 7: 自動對候選跑 chip_analysis + reversal_alert ───
    # 使用直接 import（共享 twse_institutional_cache 記憶體快取，避免重複 API 呼叫）
    chip_results = {}
    top_candidates = deduped_pre[:10]
    if top_candidates:
        codes_to_check = [c['code'] for c in top_candidates]
        print()
        print(f"🔬 自動對 {len(codes_to_check)} 檔候選執行 chip_analysis + reversal_alert")
        print("-" * 60)

        import io
        from contextlib import redirect_stdout, redirect_stderr

        for code in codes_to_check:
            chip_results[code] = {
                'cumulative_total': None, 'buy_days': None, 'sell_days': None,
                'momentum_pct': None, 'consecutive_buy': None,
                'cumulative_foreign': None, 'reversal_level': None,
                'exclusion_reason': None,
            }

        # chip_analysis：直接呼叫，suppress print 輸出
        if HAS_CHIP_ANALYSIS:
            for code in codes_to_check:
                try:
                    buf = io.StringIO()
                    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
                        chip = _analyze_chip_history(code, 10)
                    if chip:
                        summary = chip.get('summary', {})
                        momentum = chip.get('momentum') or {}
                        chip_results[code].update({
                            'cumulative_total': summary.get('total_net'),
                            'cumulative_foreign': summary.get('foreign_net'),
                            'buy_days': summary.get('buy_days'),
                            'sell_days': summary.get('sell_days'),
                            'consecutive_buy': summary.get('consecutive_buy'),
                            'momentum_pct': momentum.get('change_pct'),
                        })
                except Exception as e:
                    print(f"  ⚠️ chip_analysis 失敗 {code}: {e}", file=sys.stderr)
        else:
            print("  ⚠️ chip_analysis 模組不可用", file=sys.stderr)

        # reversal_alert：直接呼叫，suppress print 輸出
        if HAS_REVERSAL_ALERT:
            for code in codes_to_check:
                try:
                    buf = io.StringIO()
                    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
                        rev = _detect_reversal(code, days=10)
                    if rev:
                        wl = rev.get('warning_level', -1)
                        al = rev.get('alert_level', 'unknown')
                        if al == 'unknown' or wl == -1:
                            chip_results[code]['reversal_level'] = 'unknown'
                        elif wl == 0:
                            chip_results[code]['reversal_level'] = 'Level 0'
                        else:
                            chip_results[code]['reversal_level'] = f'Level {wl}'
                except Exception as e:
                    print(f"  ⚠️ reversal_alert 失敗 {code}: {e}", file=sys.stderr)
        else:
            print("  ⚠️ reversal_alert 模組不可用", file=sys.stderr)

        # 判定排除原因
        for code, r in chip_results.items():
            reasons = []
            rev = r.get('reversal_level', 'unknown')
            if rev in ('Level 3', 'Level 4'):
                reasons.append(f"反轉{rev}排除")
            mom = r.get('momentum_pct')
            if mom is not None and abs(mom) > 100 and (r.get('cumulative_total') or 0) >= 0:
                # 動能>100% 但要注意負累計的動能是假的
                reasons.append(f"動能{mom:+.0f}%>100%排除")
            cum = r.get('cumulative_total')
            if cum is not None and cum < 0:
                reasons.append(f"累計{cum:+,}為負")
            if rev == 'unknown':
                reasons.append("數據不足無法評分")
            if not reasons:
                reasons.append("通過基礎篩選")
            r['exclusion_reason'] = '｜'.join(reasons)
            r['passed'] = len(reasons) == 1 and reasons[0] == "通過基礎篩選"

        # 輸出結果
        print()
        print("📋 Module B 候選逐檔篩選結果")
        print("-" * 60)
        for c in top_candidates:
            code = c['code']
            r = chip_results.get(code, {})
            cum = r.get('cumulative_total', '?')
            bd = r.get('buy_days', '?')
            sd = r.get('sell_days', '?')
            rev = r.get('reversal_level', '?')
            mom = r.get('momentum_pct', '?')
            reason = r.get('exclusion_reason', '未執行')
            passed = '✅' if r.get('passed') else '❌'
            mat_label = {'early': '🟢早期', 'mid': '🟡中期', 'mature': '🔴成熟'}.get(c.get('maturity', ''), '')
            print(f"  {passed} {c['name']}({code}) | {mat_label} | 累計={cum} | {bd}買{sd}賣 | {rev} | 動能={mom} | {reason}")

    # ─── 儲存 JSON ───
    output_dir = DATA_DIR / target_date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'catalyst_theme_signals.json'

    output = {
        'date': target_date_str,
        'lookback_dates': dates,
        'leader_trends': {k: {kk: vv for kk, vv in v.items() if kk != 'daily_changes'}
                          for k, v in leader_trends.items()},
        'preposition_candidates': [
            {
                'code': c['code'],
                'name': c['name'],
                'tw_industry': c['tw_industry'],
                'us_leader': c['us_leader'],
                'signal_level': c['signal_level'],
                'leader_cumulative': c['leader_cumulative'],
                'leader_consecutive_up': c['leader_consecutive_up'],
                'maturity': c.get('maturity', ''),
                'tw_5d_change': c.get('tw_5d_change'),
                'in_top50': c['in_top50'],
                'score': c['score'],
                # 自動附加 chip_analysis + reversal_alert 結果
                'chip_data': chip_results.get(c['code'], {}),
            }
            for c in deduped_pre[:15]
        ],
        'already_in_top50': [
            {
                'code': c['code'],
                'name': c['name'],
                'tw_industry': c['tw_industry'],
                'us_leader': c['us_leader'],
                'leader_cumulative': c['leader_cumulative'],
                'tw_5d_change': c.get('tw_5d_change'),
            }
            for c in deduped_in[:10]
        ],
        'already_moved_count': len(already_moved),
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 已儲存: {output_path}")

    return deduped_pre


def main():
    parser = argparse.ArgumentParser(description='催化主題預警工具（Module B）')
    parser.add_argument('--date', type=str, default=None, help='目標日期 (YYYY-MM-DD)')
    parser.add_argument('--lookback', type=int, default=7, help='回看交易日數 (預設 7)')
    args = parser.parse_args()

    target = args.date or datetime.now().strftime('%Y-%m-%d')
    scan(target, lookback=args.lookback)


if __name__ == '__main__':
    main()
