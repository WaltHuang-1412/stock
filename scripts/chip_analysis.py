#!/usr/bin/env python3
"""
籌碼分析工具 - N天法人歷史查詢
Chip Analysis Tool

功能：
- 查詢指定股票近N天的法人買賣超歷史
- 計算累計淨買超、連買天數
- 判斷是否「真連續」（中間有沒有賣）

使用方式：
    python3 scripts/chip_analysis.py 2883              # 單檔，預設10天
    python3 scripts/chip_analysis.py 2883 2887 2303   # 多檔
    python3 scripts/chip_analysis.py 2883 --days 20   # 指定天數

最後更新：2026-01-22（跨平台修復）
"""

import requests
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# 添加 scripts 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

# 導入跨平台工具（P0 修復）
try:
    from utils import get_tw_now
    USE_CROSS_PLATFORM = True
except ImportError:
    USE_CROSS_PLATFORM = False

def get_trading_days(n_days=10):
    """
    取得最近N個交易日的日期列表

    P0修復：使用跨平台時區
    """
    dates = []
    # P0-2: 使用跨平台時區
    if USE_CROSS_PLATFORM:
        current = get_tw_now()
    else:
        current = datetime.now()

    while len(dates) < n_days:
        # 跳過週末
        if current.weekday() < 5:  # 0-4 是週一到週五
            dates.append(current.strftime('%Y%m%d'))
        current -= timedelta(days=1)

    return dates


def fetch_institutional_data(stock_code, date):
    """查詢單日法人數據"""
    url = f'https://www.twse.com.tw/rwd/en/fund/T86?date={date}&selectType=ALL&response=json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        data = response.json()

        if 'data' not in data or not data['data']:
            return None

        for row in data['data']:
            if row[0].strip() == stock_code:
                # 單位：股，需轉換為張
                foreign = int(row[3].replace(',', '')) // 1000
                trust = int(row[9].replace(',', '')) // 1000
                dealer = int(row[10].replace(',', '')) // 1000
                total = int(row[17].replace(',', '')) // 1000
                name = row[1].strip() if len(row) > 1 else stock_code

                return {
                    'date': date,
                    'name': name,
                    'foreign': foreign,
                    'trust': trust,
                    'dealer': dealer,
                    'total': total
                }

        return None

    except Exception as e:
        return None


def analyze_chip_history(stock_code, n_days=10):
    """分析股票籌碼歷史"""

    print(f"\n🔍 查詢 {stock_code} 近 {n_days} 天法人數據...")

    dates = get_trading_days(n_days + 5)  # 多取幾天避免假日
    history = []
    stock_name = stock_code

    for date in dates:
        if len(history) >= n_days:
            break

        data = fetch_institutional_data(stock_code, date)

        if data:
            history.append(data)
            stock_name = data['name']
            # 避免請求太快被擋
            time.sleep(0.3)

    if not history:
        print(f"❌ 查無 {stock_code} 的法人數據")
        return None

    # 數據完整性檢查
    if len(history) < n_days:
        print(f"⚠️ 警告：要求{n_days}天，只取得{len(history)}天數據")

    # 計算統計（全期間）
    total_net = sum(d['total'] for d in history)
    foreign_net = sum(d['foreign'] for d in history)
    trust_net = sum(d['trust'] for d in history)

    buy_days = sum(1 for d in history if d['total'] > 0)
    sell_days = sum(1 for d in history if d['total'] < 0)

    # 🆕 計算近5天趨勢（重要！用於偵測反轉）
    recent_5d = history[:5] if len(history) >= 5 else history
    recent_5d_total = sum(d['total'] for d in recent_5d)
    recent_5d_foreign = sum(d['foreign'] for d in recent_5d)
    recent_5d_trust = sum(d['trust'] for d in recent_5d)
    recent_5d_buy_days = sum(1 for d in recent_5d if d['total'] > 0)
    recent_5d_sell_days = sum(1 for d in recent_5d if d['total'] < 0)

    # 計算「真連續」買超天數（從最近一天往回算，遇到賣超就停）
    consecutive_buy = 0
    for d in history:
        if d['total'] > 0:
            consecutive_buy += 1
        else:
            break

    # 找最大單日買/賣
    max_buy = max(history, key=lambda x: x['total'])
    min_buy = min(history, key=lambda x: x['total'])

    return {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'days': len(history),
        'requested_days': n_days,  # 🆕 記錄要求天數，用於完整性檢查
        'history': history,
        'summary': {
            'total_net': total_net,
            'foreign_net': foreign_net,
            'trust_net': trust_net,
            'buy_days': buy_days,
            'sell_days': sell_days,
            'consecutive_buy': consecutive_buy,
            'max_buy': max_buy,
            'max_sell': min_buy if min_buy['total'] < 0 else None,
            # 🆕 近5天趨勢（用於偵測反轉）
            'recent_5d': {
                'total': recent_5d_total,
                'foreign': recent_5d_foreign,
                'trust': recent_5d_trust,
                'buy_days': recent_5d_buy_days,
                'sell_days': recent_5d_sell_days
            }
        }
    }


def format_number(n):
    """格式化數字顯示"""
    if abs(n) >= 10000:
        return f"{n//1000:+,}K"
    else:
        return f"{n:+,}"


def print_chip_report(result):
    """輸出籌碼分析報告"""

    if not result:
        return

    stock_code = result['stock_code']
    stock_name = result['stock_name']
    history = result['history']
    summary = result['summary']

    print()
    print("=" * 60)
    print(f"📊 {stock_name}({stock_code}) 籌碼分析")
    print("=" * 60)

    # 每日明細
    print()
    print(f"【近 {result['days']} 日法人買賣超】")
    print("-" * 60)
    print(f"{'日期':<12} {'三大法人':>10} {'外資':>10} {'投信':>10} {'狀態':<6}")
    print("-" * 60)

    for d in history:
        date_str = f"{d['date'][:4]}/{d['date'][4:6]}/{d['date'][6:]}"
        status = "🟢 買" if d['total'] > 0 else "🔴 賣" if d['total'] < 0 else "➖ 平"

        print(f"{date_str:<12} {format_number(d['total']):>10} {format_number(d['foreign']):>10} {format_number(d['trust']):>10} {status}")

    print("-" * 60)

    # 統計摘要
    # 🆕 數據完整性警告
    if result.get('requested_days') and result['days'] < result['requested_days']:
        print()
        print(f"⚠️ 數據不完整：要求 {result['requested_days']} 天，只取得 {result['days']} 天")
        print("-" * 60)

    print()
    print(f"【統計摘要】（{result['days']}天）")
    print("-" * 60)
    print(f"  累計淨買超（三大法人）: {format_number(summary['total_net'])} 張")
    print(f"  累計淨買超（外資）    : {format_number(summary['foreign_net'])} 張")
    print(f"  累計淨買超（投信）    : {format_number(summary['trust_net'])} 張")
    print()
    print(f"  買超天數: {summary['buy_days']} 天")
    print(f"  賣超天數: {summary['sell_days']} 天")
    print(f"  真連續買超: {summary['consecutive_buy']} 天（從最近一天往回算）")

    # 🆕 近5天趨勢（重要！用於偵測反轉）
    if 'recent_5d' in summary:
        r5 = summary['recent_5d']
        print()
        print("【近5天趨勢】⚠️ 重要")
        print("-" * 60)
        print(f"  近5天淨買超（三大法人）: {format_number(r5['total'])} 張")
        print(f"  近5天淨買超（外資）    : {format_number(r5['foreign'])} 張")
        print(f"  近5天淨買超（投信）    : {format_number(r5['trust'])} 張")
        print(f"  近5天買/賣：{r5['buy_days']}買 / {r5['sell_days']}賣")
    print()

    if summary['max_buy']:
        max_buy = summary['max_buy']
        print(f"  最大單日買超: {format_number(max_buy['total'])} 張 ({max_buy['date'][:4]}/{max_buy['date'][4:6]}/{max_buy['date'][6:]})")

    if summary['max_sell']:
        max_sell = summary['max_sell']
        print(f"  最大單日賣超: {format_number(max_sell['total'])} 張 ({max_sell['date'][:4]}/{max_sell['date'][4:6]}/{max_sell['date'][6:]})")

    print()

    # 籌碼判斷
    print("【籌碼判斷】")
    print("-" * 60)

    # 🆕 取得近5天趨勢數據
    r5 = summary.get('recent_5d', {})
    r5_total = r5.get('total', 0)
    r5_foreign = r5.get('foreign', 0)
    r5_trust = r5.get('trust', 0)

    # 判斷邏輯（加入反轉偵測）
    if summary['consecutive_buy'] >= 5 and summary['total_net'] > 0:
        print("  ✅ 法人持續佈局中（連續買超≥5天）")
        verdict = "佈局"
    elif summary['consecutive_buy'] >= 3 and summary['total_net'] > 0:
        print("  ✅ 法人短線買進中（連續買超3-4天）")
        verdict = "買進"
    elif summary['buy_days'] > summary['sell_days'] and summary['total_net'] > 0:
        print("  🟡 法人偏多但不連續（買多於賣）")
        verdict = "偏多"
    elif summary['total_net'] < 0 and summary['consecutive_buy'] == 0:
        print("  🔴 法人出貨中（累計賣超且最近在賣）")
        verdict = "出貨"
    elif summary['total_net'] > 0 and summary['consecutive_buy'] == 0:
        print("  ⚠️ 法人態度轉變（累計買超但最近開始賣）")
        verdict = "反轉"
    else:
        print("  ➖ 法人態度不明確")
        verdict = "觀望"

    # 🆕 反轉警告（累計正但近5天負）
    if summary['total_net'] > 0 and r5_total < 0:
        print(f"  🚨 反轉警告：累計+{format_number(summary['total_net'])}，但近5天{format_number(r5_total)}")
        verdict = "反轉警告"

    # 外資 vs 投信（累計判斷）
    print()
    print("  【累計判斷】")
    if summary['foreign_net'] > 0 and summary['trust_net'] > 0:
        print("  🔥 外資+投信同步買超（最佳）")
    elif summary['foreign_net'] > 0 and summary['trust_net'] < 0:
        print("  ⚠️ 外資買、投信賣（法人對決）")
    elif summary['foreign_net'] < 0 and summary['trust_net'] > 0:
        print("  ⚠️ 投信買、外資賣（法人對決）")
    elif summary['foreign_net'] < 0 and summary['trust_net'] < 0:
        print("  🔴 外資+投信同步賣超（避開）")

    # 🆕 近5天外資 vs 投信（更準確的近期態度）
    if r5:
        print()
        print("  【近5天判斷】⚠️ 更重要")
        if r5_foreign > 0 and r5_trust > 0:
            print("  🔥 近5天外資+投信同步買超")
        elif r5_foreign > 0 and r5_trust < 0:
            print("  ⚠️ 近5天外資買、投信賣（對決中）")
        elif r5_foreign < 0 and r5_trust > 0:
            print("  ⚠️ 近5天投信買、外資賣（對決中）")
        elif r5_foreign < 0 and r5_trust < 0:
            print("  🔴 近5天外資+投信同步賣超")

    print()
    print("=" * 60)

    return verdict


if __name__ == '__main__':
    # 解析參數
    args = sys.argv[1:]

    if not args:
        print("使用方式:")
        print("  python3 scripts/chip_analysis.py 2883              # 單檔，預設10天")
        print("  python3 scripts/chip_analysis.py 2883 2887 2303   # 多檔")
        print("  python3 scripts/chip_analysis.py 2883 --days 20   # 指定天數")
        sys.exit(1)

    # 解析天數參數
    n_days = 10
    stock_codes = []

    i = 0
    while i < len(args):
        if args[i] == '--days' and i + 1 < len(args):
            n_days = int(args[i + 1])
            i += 2
        else:
            stock_codes.append(args[i])
            i += 1

    if not stock_codes:
        print("❌ 請輸入股票代號")
        sys.exit(1)

    print("=" * 60)
    print("📊 籌碼分析工具")
    print(f"   查詢範圍：近 {n_days} 個交易日")
    print(f"   股票數量：{len(stock_codes)} 檔")
    print("=" * 60)

    # 分析每檔股票
    for code in stock_codes:
        result = analyze_chip_history(code, n_days)
        if result:
            print_chip_report(result)
