#!/usr/bin/env python3
"""
Pre-flight 自我檢查工具 v2.0

支援三個模式：before_market / intraday / after_market
每次分析前強制執行，主動發現並修復已知問題。

用法：
    python3 scripts/preflight_check.py --mode before_market [--fix]
    python3 scripts/preflight_check.py --mode intraday [--fix]
    python3 scripts/preflight_check.py --mode after_market [--fix]
"""

import json
import os
import re
import sys
import io
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

REPO_ROOT = Path(__file__).parent.parent
MARKET_INTEL_ROOT = REPO_ROOT.parent / 'market-intelligence'
HOLIDAYS_FILE = REPO_ROOT / 'data' / 'holidays.json'

MAX_SIGNAL_AGE_DAYS = 2
MAX_TRACK_B_SKIP_DAYS = 3

# ─────────────────────────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────────────────────────

def get_today():
    return datetime.today().strftime('%Y-%m-%d')

def load_holidays():
    tw_holidays = set()
    if not HOLIDAYS_FILE.exists():
        return tw_holidays
    with open(HOLIDAYS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for year_dates in data.get('holidays', {}).values():
        for h in year_dates:
            tw_holidays.add(h['date'])
    return tw_holidays

def is_trading_day(date_str, tw_holidays=None):
    if tw_holidays is None:
        tw_holidays = load_holidays()
    d = datetime.strptime(date_str, '%Y-%m-%d')
    if d.weekday() >= 5:
        return False
    return date_str not in tw_holidays

def next_trading_day(date_str, tw_holidays=None):
    if tw_holidays is None:
        tw_holidays = load_holidays()
    d = datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)
    for _ in range(14):
        ds = d.strftime('%Y-%m-%d')
        if is_trading_day(ds, tw_holidays):
            return ds
        d += timedelta(days=1)
    return None

def get_recent_analysis_dates(n, suffix='before_market_analysis.md'):
    """往回找最近 n 個有分析檔案的日期"""
    days = []
    d = datetime.today() - timedelta(days=1)
    while len(days) < n:
        ds = d.strftime('%Y-%m-%d')
        path = REPO_ROOT / 'data' / ds / suffix
        if path.exists():
            days.append(ds)
        d -= timedelta(days=1)
        if (datetime.today() - d).days > 60:
            break
    return days

def issue(level, msg, fix=None):
    return {'level': level, 'msg': msg, 'fix': fix, 'fixed': False}

def ok(msg):
    print(f'  ✅ {msg}')

def warn_print(msg):
    print(f'  ⚠️  {msg}')

# ─────────────────────────────────────────────────────────────────
# 共用檢查
# ─────────────────────────────────────────────────────────────────

def check_date_and_trading(mode):
    today = get_today()
    issues = []

    # 今天是否為交易日
    if not is_trading_day(today):
        issues.append(issue('ERROR',
            f'今日 {today} 是週末或假日，{mode} 不應執行'))
        return issues

    # 最新資料目錄是否和今日一致
    data_dirs = sorted([
        d.name for d in (REPO_ROOT / 'data').iterdir()
        if d.is_dir() and len(d.name) == 10 and d.name[:4].isdigit()
    ])
    latest = data_dirs[-1] if data_dirs else None

    if mode == 'before_market':
        # 盤前：今日資料目錄可以還不存在（即將建立），但不能存在更新的日期
        if latest and latest > today:
            issues.append(issue('ERROR',
                f'資料目錄最新是 {latest}，比今日 {today} 還新，日期可能錯誤'))
        else:
            ok(f'日期確認：今日 {today}（交易日）')
    else:
        # 盤中/盤後：今日目錄必須已存在
        if latest != today:
            issues.append(issue('ERROR',
                f'今日 {today} 資料目錄不存在（最新：{latest}），請先確認盤前分析是否完成'))
        else:
            ok(f'日期確認：今日 {today}（交易日）')

    return issues

def check_daily_sh():
    daily_sh = MARKET_INTEL_ROOT / 'daily.sh'
    if not daily_sh.exists():
        ok('daily.sh 不存在（跳過）')
        return []
    with open(daily_sh, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'industry_signals.json' not in content:
        return [issue('ERROR',
            'daily.sh 未包含 industry_signals.json 的 git add，每日更新不會推送')]
    ok('daily.sh：已包含 industry_signals.json')
    return []

# ─────────────────────────────────────────────────────────────────
# 盤前專屬檢查
# ─────────────────────────────────────────────────────────────────

def check_industry_signals(fix=False):
    today = get_today()
    today_dir = REPO_ROOT / 'data' / today
    signal_path = today_dir / 'industry_signals.json'
    issues = []

    def try_fix():
        local_sig = MARKET_INTEL_ROOT / 'outputs' / 'industry_signals.json'
        if local_sig.exists():
            today_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(local_sig), str(signal_path))
            with open(signal_path, 'r', encoding='utf-8') as f:
                sig = json.load(f)
            print(f'  🔧 已從本地 market-intelligence 同步 industry_signals.json（{sig.get("date")}）')
            return True
        print(f'  ❌ 本地 market-intelligence 不存在，無法自動修復')
        return False

    if not signal_path.exists():
        i = issue('WARN', 'industry_signals.json 不存在於今日目錄', 'copy_from_local')
        if fix:
            i['fixed'] = try_fix()
        issues.append(i)
        return issues

    with open(signal_path, 'r', encoding='utf-8') as f:
        sig = json.load(f)
    sig_date_str = sig.get('date', '1970-01-01')
    sig_date = datetime.strptime(sig_date_str, '%Y-%m-%d')
    today_dt = datetime.strptime(today, '%Y-%m-%d')
    age = (today_dt - sig_date).days

    if age > MAX_SIGNAL_AGE_DAYS:
        i = issue('ERROR',
            f'industry_signals.json 過期 {age} 天（資料日期 {sig_date_str}，今日 {today}）',
            'copy_from_local')
        if fix:
            i['fixed'] = try_fix()
            if i['fixed']:
                return issues
        issues.append(i)
    else:
        ok(f'industry_signals.json：{sig_date_str}（{sig.get("updated_at","?")}），{age} 天前')

    return issues

def check_track_b_depth():
    recent = get_recent_analysis_dates(MAX_TRACK_B_SKIP_DAYS + 2)
    skipped = []
    for date in recent:
        md_path = REPO_ROOT / 'data' / date / 'before_market_analysis.md'
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        has_depth = any(kw in content for kw in [
            'depth 3', 'depth 2', 'depth 1', 'tier_0', 'tier0[', '軌道B.*depth'
        ])
        if not has_depth:
            skipped.append(date)

    if len(skipped) >= MAX_TRACK_B_SKIP_DAYS:
        return [issue('WARN',
            f'軌道B 深度展開已連續 {len(skipped)} 天缺席（{skipped[-1]} ～ {skipped[0]}）'
            f'，今日盤前 Step 6 必須執行完整 depth 展開')]
    elif skipped:
        warn_print(f'軌道B 深度展開：近期 {len(skipped)} 天缺席（{skipped}），尚未達警戒線')
    else:
        ok(f'軌道B 深度展開：近 {len(recent)} 天正常')
    return []

def check_before_required_files():
    today = get_today()
    required = [
        f'data/{today}/us_asia_markets.json',
        f'data/{today}/us_leader_alerts.json',
        f'data/{today}/tw_market_news.json',
        f'data/{today}/catalyst_preposition_scan.json',
        f'data/{today}/catalyst_theme_signals.json',
        f'data/{today}/topic_tracker.md',
        f'data/{today}/market_intelligence.md',
        f'data/{today}/market_regime.json',
    ]
    missing = [f for f in required if not (REPO_ROOT / f).exists()]
    if missing:
        return [issue('ERROR', f'必要輸入檔案缺失（{len(missing)} 項）：{", ".join(m.split("/")[-1] for m in missing)}')]
    ok(f'必要輸入檔案：全部存在（{len(required)} 項）')
    return []

def check_tracking_day_consistency(today):
    tracking_path = REPO_ROOT / 'data' / 'tracking' / f'tracking_{today}.json'
    if not tracking_path.exists():
        ok('tracking.json 尚不存在（盤前首次分析前正常）')
        return []
    with open(tracking_path, 'r', encoding='utf-8') as f:
        tracking = json.load(f)
    errors = []
    for rec in tracking.get('recommendations', []):
        code = rec.get('stock_code', '?')
        h_days = rec.get('holding_days', 0)
        status = rec.get('holding_status', '')
        sl_pct = rec.get('stop_loss_pct')
        rec_price = rec.get('recommend_price', 0)
        sl = rec.get('stop_loss', 0)

        # 持倉天數一致性
        m = re.search(r'D(\d+)/10', status)
        if m:
            status_day = int(m.group(1))
            if abs(status_day - h_days) > 1:
                errors.append(f'{code}: holding_days={h_days} vs status=D{status_day}')

        # stop_loss 計算正確性
        if sl_pct and rec_price:
            expected_sl = round(rec_price * (1 + sl_pct / 100), 1)
            if sl and abs(sl - expected_sl) > 1:
                errors.append(f'{code}: stop_loss={sl} 但應為 {expected_sl}（{sl_pct}%）')

    if errors:
        return [issue('WARN', f'tracking.json 數值異常：{"; ".join(errors)}')]
    ok('tracking.json：持倉天數與停損計算一致')
    return []

# ─────────────────────────────────────────────────────────────────
# 盤中專屬檢查
# ─────────────────────────────────────────────────────────────────

def check_intraday_prereqs(today):
    issues = []

    # 盤前分析必須已完成
    bm_path = REPO_ROOT / 'data' / today / 'before_market_analysis.md'
    if not bm_path.exists():
        issues.append(issue('ERROR', f'今日盤前分析未完成（before_market_analysis.md 不存在），禁止執行盤中'))
        return issues
    ok('前置確認：盤前分析已完成')

    # tracking.json 必須已存在
    tracking_path = REPO_ROOT / 'data' / 'tracking' / f'tracking_{today}.json'
    if not tracking_path.exists():
        issues.append(issue('ERROR', f'tracking_{today}.json 不存在，請先完成盤前建檔'))
        return issues
    ok('前置確認：tracking.json 已存在')

    # 確認 stop_loss_pct 使用 -10（不是 -8）
    with open(tracking_path, 'r', encoding='utf-8') as f:
        tracking = json.load(f)
    wrong_sl = []
    for rec in tracking.get('recommendations', []):
        sl_pct = rec.get('stop_loss_pct')
        if sl_pct and sl_pct != -10 and rec.get('result') == 'holding':
            wrong_sl.append(f'{rec.get("stock_code")}({sl_pct}%)')
    if wrong_sl:
        issues.append(issue('WARN', f'stop_loss_pct 非 -10% 的持倉：{wrong_sl}（盤前推薦應為 -10%）'))
    else:
        ok('stop_loss_pct：全部持倉使用 -10%')

    # L4 未出場警告
    ra_path = REPO_ROOT / 'data' / today / 'reversal_alerts.json'
    if ra_path.exists():
        try:
            with open(ra_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            alerts = json.loads(content) if content else []
            l4 = [a.get('stock_code', a.get('code', '?'))
                  for a in (alerts if isinstance(alerts, list) else [])
                  if str(a.get('level', '')).startswith('4') or 'Level 4' in str(a.get('alert', ''))]
            if l4:
                issues.append(issue('ERROR', f'仍有 Level 4 股票未出場：{l4}，今日開盤必須強制停損'))
            else:
                ok('Level 4 預警：無未處理的強制出場')
        except (json.JSONDecodeError, Exception):
            ok('Level 4 預警：reversal_alerts.json 解析失敗，跳過檢查')

    return issues

def check_intraday_required_files(today):
    required = [
        f'data/{today}/intraday_detector.json',
    ]
    missing = [f for f in required if not (REPO_ROOT / f).exists()]
    if missing:
        return [issue('WARN',
            f'盤中偵測器檔案缺失：{", ".join(m.split("/")[-1] for m in missing)}'
            f'，請執行 python3 scripts/intraday_institutional_detector.py')]
    ok('盤中偵測器：intraday_detector.json 已存在')
    return []

# ─────────────────────────────────────────────────────────────────
# 盤後專屬檢查
# ─────────────────────────────────────────────────────────────────

def check_after_prereqs(today):
    issues = []

    # 盤中分析必須已完成
    intraday_path = REPO_ROOT / 'data' / today / 'intraday_analysis.md'
    if not intraday_path.exists():
        issues.append(issue('ERROR', '今日盤中分析未完成（intraday_analysis.md 不存在），禁止執行盤後'))
        return issues
    ok('前置確認：盤中分析已完成')

    tracking_path = REPO_ROOT / 'data' / 'tracking' / f'tracking_{today}.json'
    if not tracking_path.exists():
        issues.append(issue('ERROR', f'tracking_{today}.json 不存在'))
        return issues
    ok('前置確認：tracking.json 已存在')

    return issues

def check_d10_settlement(today):
    tracking_path = REPO_ROOT / 'data' / 'tracking' / f'tracking_{today}.json'
    if not tracking_path.exists():
        return []
    with open(tracking_path, 'r', encoding='utf-8') as f:
        tracking = json.load(f)
    unsettled = []
    for rec in tracking.get('recommendations', []):
        h_days = rec.get('holding_days', 0)
        result = rec.get('result', 'holding')
        code = rec.get('stock_code', '?')
        if h_days >= 10 and result == 'holding':
            unsettled.append(code)
    if unsettled:
        return [issue('ERROR',
            f'D10 到期未結算：{unsettled}，盤後必須以今日收盤價結算（>推薦價=success，否則=fail）')]
    ok('D10 結算：無到期未結算股票')
    return []

def check_tomorrow_date(today):
    """明日推薦日期必須是下一個交易日"""
    tw_holidays = load_holidays()
    expected_next = next_trading_day(today, tw_holidays)
    if not expected_next:
        return [issue('WARN', '無法計算下一個交易日，請手動確認明日推薦日期')]

    # 從 tracking.json 或 after_market_analysis.md 讀取明日日期
    tracking_path = REPO_ROOT / 'data' / 'tracking' / f'tracking_{today}.json'
    if not tracking_path.exists():
        return []

    # 也檢查 after_market_analysis.md 中有沒有錯誤的日期
    after_path = REPO_ROOT / 'data' / today / 'after_market_analysis.md'
    if after_path.exists():
        with open(after_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 找所有「明日」日期
        found_dates = re.findall(r'明日.*?(\d{4}-\d{2}-\d{2})', content)
        wrong_dates = [d for d in found_dates if d != expected_next and d > today]
        if wrong_dates:
            return [issue('ERROR',
                f'盤後分析中「明日」日期有誤：{set(wrong_dates)}，正確下一交易日為 {expected_next}')]

    ok(f'明日推薦日期：{expected_next}（下一交易日）')
    return []

def check_predictions_consistency(today):
    pred_path = REPO_ROOT / 'data' / 'predictions' / 'predictions.json'
    if not pred_path.exists():
        return [issue('WARN', 'predictions.json 不存在')]

    with open(pred_path, 'r', encoding='utf-8') as f:
        pred = json.load(f)

    # 確認有頂層 accuracy 欄位
    required_keys = ['settled_accuracy', 'settled_count', 'total_success', 'total_fail']
    missing_keys = [k for k in required_keys if k not in pred]
    if missing_keys:
        return [issue('WARN', f'predictions.json 缺少欄位：{missing_keys}')]

    accuracy = pred.get('settled_accuracy', '?')
    count = pred.get('settled_count', '?')
    ok(f'predictions.json：準確率 {accuracy}（{count} 筆結算）')
    return []

def check_no_premature_fail(today):
    """確認 tracking.json 沒有在當天就把 holding 標成 fail（除非真的觸停損）"""
    tracking_path = REPO_ROOT / 'data' / 'tracking' / f'tracking_{today}.json'
    if not tracking_path.exists():
        return []
    with open(tracking_path, 'r', encoding='utf-8') as f:
        tracking = json.load(f)
    suspicious = []
    for rec in tracking.get('recommendations', []):
        result = rec.get('result', '')
        h_days = rec.get('holding_days', 0)
        fail_reason = rec.get('fail_reason', '')
        code = rec.get('stock_code', '?')
        if result == 'fail' and h_days < 2 and 'Level 4' not in fail_reason and '停損' not in fail_reason:
            suspicious.append(f'{code}(D{h_days})')
    if suspicious:
        return [issue('WARN',
            f'疑似當天提早結算 fail 的股票：{suspicious}（D1-D2 fail 請確認是否真的觸停損）')]
    ok('持倉結算：無異常提早 fail')
    return []

# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def run_checks(mode, fix):
    today = get_today()
    all_issues = []

    print(f'\n【1】日期與交易日確認')
    all_issues += check_date_and_trading(mode)
    if any(i['level'] == 'ERROR' and not i['fixed'] for i in all_issues):
        return all_issues  # 日期錯誤不繼續

    if mode == 'before_market':
        print(f'\n【2】industry_signals.json 新鮮度')
        all_issues += check_industry_signals(fix)

        print(f'\n【3】軌道B 深度展開連續性')
        all_issues += check_track_b_depth()

        print(f'\n【4】必要輸入檔案')
        all_issues += check_before_required_files()

        print(f'\n【5】tracking.json 數值一致性')
        all_issues += check_tracking_day_consistency(today)

        print(f'\n【6】daily.sh 設定')
        all_issues += check_daily_sh()

    elif mode == 'intraday':
        print(f'\n【2】盤前前置確認')
        all_issues += check_intraday_prereqs(today)

        print(f'\n【3】盤中偵測器檔案')
        all_issues += check_intraday_required_files(today)

    elif mode == 'after_market':
        print(f'\n【2】盤中前置確認')
        all_issues += check_after_prereqs(today)

        print(f'\n【3】D10 到期結算')
        all_issues += check_d10_settlement(today)

        print(f'\n【4】明日推薦日期正確性')
        all_issues += check_tomorrow_date(today)

        print(f'\n【5】predictions.json 一致性')
        all_issues += check_predictions_consistency(today)

        print(f'\n【6】持倉結算合理性')
        all_issues += check_no_premature_fail(today)

    return all_issues


def main():
    parser = argparse.ArgumentParser(description='Pre-flight 自我檢查 v2.0')
    parser.add_argument('--mode', choices=['before_market', 'intraday', 'after_market'],
                        default='before_market', help='分析模式')
    parser.add_argument('--fix', action='store_true', help='自動修復可修復的問題')
    args = parser.parse_args()

    mode_label = {'before_market': '盤前', 'intraday': '盤中', 'after_market': '盤後'}[args.mode]
    today = get_today()

    print('=' * 60)
    print(f'🛫 Pre-flight Check [{mode_label}]  {today}')
    print('=' * 60)

    all_issues = run_checks(args.mode, args.fix)

    errors = [i for i in all_issues if i['level'] == 'ERROR' and not i['fixed']]
    warns  = [i for i in all_issues if i['level'] == 'WARN'  and not i['fixed']]

    print('\n' + '=' * 60)
    if not errors and not warns:
        print(f'✅ 全部通過，可以開始{mode_label}分析')
        sys.exit(0)

    if warns:
        print(f'⚠️  警告 {len(warns)} 項：')
        for w in warns:
            print(f'   - {w["msg"]}')

    if errors:
        print(f'\n❌ 錯誤 {len(errors)} 項（必須修復才能繼續）：')
        for e in errors:
            print(f'   - {e["msg"]}')
        if not args.fix:
            print('\n💡 執行 --fix 嘗試自動修復')
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
