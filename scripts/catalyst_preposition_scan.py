#!/usr/bin/env python3
"""
催化劑預埋掃描工具 v1.0 — 提前發現法人佈局機會

核心邏輯：
    法人開始買（多日累積）+ 股價還沒動（5日漲幅低）+ 催化劑正在升溫
    = 提前 1-2 天進場的機會

三層分級：
    L3（佈局完成）：連3+天TOP50 + 動能<-30% + 漲幅<5%  → 正常倉位 15-20%
    L2（早期佈局）：連2+天TOP50 + 動能<+50%  + 漲幅<5%  → 小倉位 5-10%
    L1（態度轉變）：首次進TOP50 + 前期不在    + 漲幅<3%  → 僅觀察

使用方式：
    python3 scripts/catalyst_preposition_scan.py                    # 今天，回看7天
    python3 scripts/catalyst_preposition_scan.py --date 2026-03-20  # 指定日期
    python3 scripts/catalyst_preposition_scan.py --lookback 10      # 回看10天
    python3 scripts/catalyst_preposition_scan.py --threshold 3      # 漲幅門檻3%

輸出：
    data/YYYY-MM-DD/catalyst_preposition_scan.json
    Console 報告（含 L3/L2/L1 分級）
"""

import sys
import io
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import warnings
warnings.filterwarnings('ignore')

# Windows 環境 stdout/stderr 編碼修正
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 路徑設定
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'

# 不直接 import chip_analysis（會觸發 stdout 雙重包裝問題），改用 subprocess

# 股票產業對照（從 industry_chains.json 動態載入）
def load_industry_map():
    """從 industry_chains.json 建立 股票代號→產業 對照表"""
    chain_file = DATA_DIR / 'industry_chains.json'
    mapping = {}
    if chain_file.exists():
        with open(chain_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for industry_key, industry_data in data.get('industries', {}).items():
            industry_name = industry_data.get('name', industry_key)
            for tier_key, tier_data in industry_data.get('tiers', {}).items():
                for stock in tier_data.get('stocks', []):
                    code = stock.get('code', '')
                    if code:
                        mapping[code] = {
                            'industry': industry_name,
                            'tier': tier_key,
                            'category': stock.get('category', ''),
                            'catalysts': industry_data.get('catalysts', [])
                        }
    return mapping


def get_trading_dates(target_date, lookback=7):
    """取得 target_date 往前 lookback 個交易日（有 institutional_top50.json 的日期）"""
    dates = []
    current = target_date
    max_attempts = lookback * 3  # 預留週末/假日空間

    for _ in range(max_attempts):
        if len(dates) >= lookback:
            break
        date_str = current.strftime('%Y-%m-%d')
        json_path = DATA_DIR / date_str / 'institutional_top50.json'
        if json_path.exists():
            dates.append(date_str)
        current -= timedelta(days=1)

    return dates


def load_institutional_data(date_str):
    """載入單日的 institutional_top50.json"""
    json_path = DATA_DIR / date_str / 'institutional_top50.json'
    if not json_path.exists():
        return None
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_chip_analysis(stock_codes, days=10):
    """呼叫 chip_analysis.py 取得動能數據"""
    if not stock_codes:
        return {}

    chip_script = SCRIPT_DIR / 'chip_analysis.py'
    cmd = [sys.executable, str(chip_script)] + list(stock_codes) + ['--days', str(days)]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace',
            cwd=str(PROJECT_DIR)
        )
        return parse_chip_output(result.stdout)
    except Exception as e:
        print(f"  ⚠️ chip_analysis 執行失敗: {e}", file=sys.stderr)
        return {}


def parse_number(text):
    """解析數字字串，處理 K/M 後綴和逗號"""
    text = text.strip().replace(',', '').replace('+', '').replace('張', '').replace('/日', '').strip()
    multiplier = 1
    if text.endswith('K'):
        text = text[:-1]
        multiplier = 1000
    elif text.endswith('M'):
        text = text[:-1]
        multiplier = 1000000
    try:
        return int(float(text) * multiplier)
    except (ValueError, TypeError):
        return 0


def parse_chip_output(output):
    """
    解析 chip_analysis.py 的文字輸出，提取關鍵數據

    實際輸出格式範例：
        📊 13,622,601(2603) 籌碼分析
        累計淨買超（三大法人）: +41K 張
        買超天數: 6 天
        真連續買超: 3 天
        動能變化: +500.0%
        動能等級: 🔴 動能爆發（追高風險）
    """
    results = {}
    current_stock = None
    current_data = {}
    import re

    for line in output.split('\n'):
        line_stripped = line.strip()

        # 偵測股票標題行：「📊 13,622,601(2603) 籌碼分析」
        match = re.search(r'[\d,]+\((\d{4})\)\s*籌碼分析', line_stripped)
        if match:
            if current_stock and current_data:
                results[current_stock] = current_data
            current_stock = match.group(1)
            current_data = {
                'momentum_pct': None,
                'momentum_level': None,
                'consecutive_buy': 0,
                'cumulative_total': 0,
                'cumulative_foreign': 0,
                'buy_days': 0,
                'sell_days': 0,
                'recent_5d_avg': 0,
                'prior_5d_avg': 0,
            }
            continue

        if not current_stock:
            continue

        # 累計淨買超（三大法人）: +41K 張
        if '累計淨買超' in line_stripped and '三大法人' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            current_data['cumulative_total'] = parse_number(val)

        # 累計淨買超（外資）: +37K 張
        elif '累計淨買超' in line_stripped and '外資' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            current_data['cumulative_foreign'] = parse_number(val)

        # 買超天數: 6 天
        elif '買超天數' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            val = val.replace('天', '').strip()
            try:
                current_data['buy_days'] = int(val)
            except ValueError:
                pass

        # 賣超天數: 4 天
        elif '賣超天數' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            val = val.replace('天', '').strip()
            try:
                current_data['sell_days'] = int(val)
            except ValueError:
                pass

        # 真連續買超: 3 天
        elif '真連續買超' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            val = val.replace('天', '').strip()
            # 可能是 "3 天（從最近一天往回算）"
            val = val.split('（')[0].strip() if '（' in val else val
            try:
                current_data['consecutive_buy'] = int(val)
            except ValueError:
                pass

        # 動能變化: +500.0%
        elif '動能變化' in line_stripped:
            match_pct = re.search(r'([+-]?\d+\.?\d*)%', line_stripped)
            if match_pct:
                try:
                    current_data['momentum_pct'] = float(match_pct.group(1))
                except ValueError:
                    pass

        # 動能等級: 🔴 動能爆發（追高風險）
        elif '動能等級' in line_stripped:
            if '佈局完成' in line_stripped or '大幅減弱' in line_stripped:
                current_data['momentum_level'] = 5
            elif '減弱' in line_stripped:
                current_data['momentum_level'] = 4
            elif '持續' in line_stripped:
                current_data['momentum_level'] = 3
            elif '增強' in line_stripped:
                current_data['momentum_level'] = 2
            elif '加速' in line_stripped or '爆發' in line_stripped:
                current_data['momentum_level'] = 1

        # 近5日平均: +7,196 張/日
        elif '近5日平均' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            current_data['recent_5d_avg'] = parse_number(val)

        # 前5日平均: +1,032 張/日
        elif '前5日平均' in line_stripped:
            val = line_stripped.split(':')[-1] if ':' in line_stripped else ''
            current_data['prior_5d_avg'] = parse_number(val)

    # 儲存最後一檔
    if current_stock and current_data:
        results[current_stock] = current_data

    return results


def classify_positioning(stock_info, chip_data):
    """
    分級佈局階段

    stock_info: 多日彙總數據（days_in_top50, total_buying, latest_5day_change 等）
    chip_data: chip_analysis 動能數據
    """
    days_in_top50 = stock_info.get('days_in_top50', 0)
    latest_change = stock_info.get('latest_5day_change', 999)
    avg_rank_best = stock_info.get('avg_rank_best', 50)
    consecutive_buy = chip_data.get('consecutive_buy', 0) if chip_data else 0
    momentum_pct = chip_data.get('momentum_pct', 0) if chip_data else 0
    buy_days = chip_data.get('buy_days', 0) if chip_data else 0
    sell_days = chip_data.get('sell_days', 0) if chip_data else 0
    cumulative = chip_data.get('cumulative_total', 0) if chip_data else 0

    # 基本排除條件
    if latest_change > 10:
        return None  # 已大漲，不是預埋機會
    if cumulative < 0:
        return None  # 累計賣超，不考慮
    if sell_days >= 7:
        return None  # 多數時間在賣（v7.9.1 規則）

    # L3: 佈局完成
    if (days_in_top50 >= 3 and
        consecutive_buy >= 3 and
        momentum_pct is not None and momentum_pct < -30 and
        latest_change < 5):
        return {
            'level': 'L3',
            'label': '佈局完成',
            'emoji': '🔥',
            'position': '15-20%',
            'confidence': '高',
            'reason': f'連{consecutive_buy}天買超+動能{momentum_pct:+.1f}%佈局完成+漲幅僅{latest_change:+.1f}%'
        }

    # L2: 早期佈局
    if (days_in_top50 >= 2 and
        (consecutive_buy >= 2 or buy_days >= 6) and
        momentum_pct is not None and momentum_pct < 50 and
        latest_change < 5):
        return {
            'level': 'L2',
            'label': '早期佈局',
            'emoji': '🟢',
            'position': '5-10%',
            'confidence': '中',
            'reason': f'{days_in_top50}天在TOP50+動能{momentum_pct:+.1f}%+漲幅僅{latest_change:+.1f}%'
        }

    # L1: 態度轉變（動能 > 100% 排除，那是追高不是預埋）
    if (days_in_top50 >= 1 and
        latest_change < 3 and
        cumulative > 0 and
        (momentum_pct is None or momentum_pct < 100)):
        return {
            'level': 'L1',
            'label': '態度轉變',
            'emoji': '🟡',
            'position': '觀察',
            'confidence': '低',
            'reason': f'{days_in_top50}天在TOP50+漲幅{latest_change:+.1f}%尚未反映'
        }

    # 動能 > 100% 但多日出現 → 標記為「已追高」（不推薦）
    if momentum_pct is not None and momentum_pct > 100:
        return {
            'level': 'SKIP',
            'label': '追高風險',
            'emoji': '⚠️',
            'position': '不推薦',
            'confidence': '-',
            'reason': f'動能{momentum_pct:+.1f}%已追高，法人可能正在出貨'
        }

    return None


def scan(target_date_str, lookback=7, price_threshold=5.0):
    """
    主掃描邏輯

    1. 讀取多日法人 TOP50
    2. 彙總每檔股票的多日累積數據
    3. 篩選：多日買超 + 股價未漲
    4. chip_analysis 取動能
    5. 分級輸出
    """
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    trading_dates = get_trading_dates(target_date, lookback)

    if not trading_dates:
        print("❌ 找不到任何 institutional_top50.json 資料")
        return []

    print(f"📊 催化劑預埋掃描")
    print(f"   目標日期：{target_date_str}")
    print(f"   回看天數：{len(trading_dates)} 個交易日")
    print(f"   資料期間：{trading_dates[-1]} ~ {trading_dates[0]}")
    print(f"   漲幅門檻：<{price_threshold}%")
    print()

    # ─── Step 1: 彙總多日法人數據 ───

    stock_aggregate = {}  # code → 彙總數據

    for i, date_str in enumerate(trading_dates):
        data = load_institutional_data(date_str)
        if not data or 'stocks' not in data:
            continue

        is_latest = (i == 0)  # 最新一天

        for stock in data['stocks']:
            code = stock.get('code', '')
            if not code:
                continue

            total = stock.get('total', 0)
            if total <= 0:
                continue  # 只看買超的

            if code not in stock_aggregate:
                stock_aggregate[code] = {
                    'code': code,
                    'name': stock.get('name', code),
                    'days_in_top50': 0,
                    'appearances': [],  # 每天的數據
                    'total_buying': 0,
                    'avg_rank_best': 50,
                    'avg_rank_latest': 50,
                    'latest_5day_change': 0,
                    'latest_close': 0,
                    'latest_buy_ratio': 0,
                    'latest_foreign': 0,
                    'latest_trust': 0,
                }

            agg = stock_aggregate[code]
            agg['days_in_top50'] += 1
            agg['total_buying'] += total
            agg['appearances'].append({
                'date': date_str,
                'total': total,
                'avg_rank': stock.get('avg_rank', 50),
                'foreign': stock.get('foreign', 0),
                'trust': stock.get('trust', 0),
                '5day_change': stock.get('5day_change', 0),
                'buy_ratio': stock.get('buy_ratio', 0),
            })

            rank = stock.get('avg_rank', 50)
            if rank < agg['avg_rank_best']:
                agg['avg_rank_best'] = rank

            # 用最近出現日的數據（不一定是 day 0）
            if agg['latest_close'] == 0 or is_latest:
                close = stock.get('close_price') or 0
                change = stock.get('5day_change') or 0
                if close and close > 0:
                    agg['latest_close'] = close
                if change != 0 or agg['latest_5day_change'] == 0:
                    agg['latest_5day_change'] = change
                agg['avg_rank_latest'] = rank
                agg['latest_buy_ratio'] = stock.get('buy_ratio', 0)
                agg['latest_foreign'] = stock.get('foreign', 0)
                agg['latest_trust'] = stock.get('trust', 0)

    # ─── Step 2: 篩選候選（多日出現 + 股價未漲） ───

    candidates = []
    for code, agg in stock_aggregate.items():
        # 至少出現 1 天
        if agg['days_in_top50'] < 1:
            continue
        # 股價漲幅門檻
        if agg['latest_5day_change'] > price_threshold:
            continue
        candidates.append(agg)

    # 按 days_in_top50 + total_buying 排序
    candidates.sort(key=lambda x: (-x['days_in_top50'], -x['total_buying']))

    print(f"   篩選結果：{len(stock_aggregate)} 檔出現在買超TOP50，{len(candidates)} 檔通過漲幅門檻")
    print()

    if not candidates:
        print("❌ 沒有符合條件的候選股")
        return []

    # ─── Step 3: chip_analysis 取動能（取前 30 檔） ───

    top_codes = [c['code'] for c in candidates[:30]]
    print(f"⏳ 正在對 {len(top_codes)} 檔候選股執行籌碼分析...")
    chip_results = run_chip_analysis(top_codes, days=10)
    print(f"   取得 {len(chip_results)} 檔籌碼數據")
    print()

    # ─── Step 4: 載入產業對照 ───

    industry_map = load_industry_map()

    # ─── Step 5: 分級 ───

    l3_stocks = []
    l2_stocks = []
    l1_stocks = []

    for candidate in candidates[:30]:
        code = candidate['code']
        chip = chip_results.get(code)

        classification = classify_positioning(candidate, chip)
        if not classification:
            continue

        # 補充產業資訊
        ind_info = industry_map.get(code, {})
        entry = {
            **candidate,
            'classification': classification,
            'industry': ind_info.get('industry', '其他'),
            'category': ind_info.get('category', ''),
            'chip_data': chip or {},
        }

        if classification['level'] == 'L3':
            l3_stocks.append(entry)
        elif classification['level'] == 'L2':
            l2_stocks.append(entry)
        elif classification['level'] == 'L1':
            l1_stocks.append(entry)
        # SKIP = 追高風險，不列入任何推薦

    # ─── Step 6: 輸出報告 ───

    print("=" * 70)
    print(f"🔍 催化劑預埋掃描報告 — {target_date_str}")
    print("=" * 70)

    total_found = len(l3_stocks) + len(l2_stocks) + len(l1_stocks)

    if l3_stocks:
        print()
        print(f"🔥 Level 3：佈局完成（{len(l3_stocks)} 檔）→ 正常倉位 15-20%")
        print("-" * 60)
        for s in l3_stocks:
            chip = s.get('chip_data', {})
            print(f"  {s['name']}({s['code']}) | {s['industry']}")
            print(f"    avg_rank 最佳 {s['avg_rank_best']:.1f} | {s['days_in_top50']}天在TOP50 | 累計買超 {s['total_buying']:+,}")
            print(f"    5日漲幅 {s['latest_5day_change']:+.1f}% | 收盤 {s['latest_close']}")
            print(f"    動能 {chip.get('momentum_pct', 'N/A')}% | 連買 {chip.get('consecutive_buy', 'N/A')}天 | {chip.get('buy_days', '?')}買{chip.get('sell_days', '?')}賣")
            print(f"    → {s['classification']['reason']}")
            print()

    if l2_stocks:
        print()
        print(f"🟢 Level 2：早期佈局（{len(l2_stocks)} 檔）→ 小倉位 5-10%")
        print("-" * 60)
        for s in l2_stocks:
            chip = s.get('chip_data', {})
            print(f"  {s['name']}({s['code']}) | {s['industry']}")
            print(f"    avg_rank 最佳 {s['avg_rank_best']:.1f} | {s['days_in_top50']}天在TOP50 | 累計買超 {s['total_buying']:+,}")
            print(f"    5日漲幅 {s['latest_5day_change']:+.1f}% | 收盤 {s['latest_close']}")
            print(f"    動能 {chip.get('momentum_pct', 'N/A')}% | 連買 {chip.get('consecutive_buy', 'N/A')}天 | {chip.get('buy_days', '?')}買{chip.get('sell_days', '?')}賣")
            print(f"    → {s['classification']['reason']}")
            print()

    if l1_stocks:
        print()
        print(f"🟡 Level 1：態度轉變（{len(l1_stocks)} 檔）→ 僅觀察")
        print("-" * 60)
        for s in l1_stocks:
            chip = s.get('chip_data', {})
            print(f"  {s['name']}({s['code']}) | {s['industry']}")
            print(f"    avg_rank 最佳 {s['avg_rank_best']:.1f} | {s['days_in_top50']}天在TOP50 | 累計買超 {s['total_buying']:+,}")
            print(f"    5日漲幅 {s['latest_5day_change']:+.1f}% | 收盤 {s['latest_close']}")
            if chip:
                print(f"    動能 {chip.get('momentum_pct', 'N/A')}% | {chip.get('buy_days', '?')}買{chip.get('sell_days', '?')}賣")
            print(f"    → {s['classification']['reason']}")
            print()

    if not total_found:
        print()
        print("  （無符合條件的預埋機會）")

    # 統計摘要
    print("=" * 70)
    print(f"📋 統計：L3={len(l3_stocks)} / L2={len(l2_stocks)} / L1={len(l1_stocks)} / 總計={total_found}")
    print(f"   回看期間 TOP50 出現過 {len(stock_aggregate)} 檔，通過漲幅門檻 {len(candidates)} 檔")
    print("=" * 70)

    # ─── Step 7: 儲存 JSON ───

    output_dir = DATA_DIR / target_date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'catalyst_preposition_scan.json'

    scan_result = {
        'date': target_date_str,
        'lookback_dates': trading_dates,
        'price_threshold': price_threshold,
        'total_scanned': len(stock_aggregate),
        'total_filtered': len(candidates),
        'l3_stocks': [format_output(s) for s in l3_stocks],
        'l2_stocks': [format_output(s) for s in l2_stocks],
        'l1_stocks': [format_output(s) for s in l1_stocks],
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(scan_result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 已儲存: {output_path}")

    return l3_stocks + l2_stocks + l1_stocks


def format_output(stock_entry):
    """格式化輸出 JSON"""
    chip = stock_entry.get('chip_data', {})
    return {
        'code': stock_entry['code'],
        'name': stock_entry['name'],
        'industry': stock_entry.get('industry', ''),
        'category': stock_entry.get('category', ''),
        'level': stock_entry['classification']['level'],
        'label': stock_entry['classification']['label'],
        'position': stock_entry['classification']['position'],
        'confidence': stock_entry['classification']['confidence'],
        'reason': stock_entry['classification']['reason'],
        'days_in_top50': stock_entry['days_in_top50'],
        'total_buying': stock_entry['total_buying'],
        'avg_rank_best': stock_entry['avg_rank_best'],
        'latest_5day_change': stock_entry['latest_5day_change'],
        'latest_close': stock_entry['latest_close'],
        'latest_buy_ratio': stock_entry['latest_buy_ratio'],
        'momentum_pct': chip.get('momentum_pct'),
        'consecutive_buy': chip.get('consecutive_buy', 0),
        'buy_days': chip.get('buy_days', 0),
        'sell_days': chip.get('sell_days', 0),
        'cumulative_total': chip.get('cumulative_total', 0),
        'appearances': stock_entry.get('appearances', []),
    }


def main():
    parser = argparse.ArgumentParser(description='催化劑預埋掃描工具')
    parser.add_argument('--date', type=str, default=None,
                        help='目標日期 (YYYY-MM-DD)，預設今天')
    parser.add_argument('--lookback', type=int, default=7,
                        help='回看交易日數 (預設 7)')
    parser.add_argument('--threshold', type=float, default=5.0,
                        help='5日漲幅門檻%% (預設 5.0)')
    args = parser.parse_args()

    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now().strftime('%Y-%m-%d')

    scan(target_date, lookback=args.lookback, price_threshold=args.threshold)


if __name__ == '__main__':
    main()
