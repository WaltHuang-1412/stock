#!/usr/bin/env python3
"""
法人反轉預警工具 v2.0（多層次預警）

功能：
- 四層預警系統：動能減弱 → 單日反轉 → 連續賣超 → 爆量賣超
- 整合籌碼動能分析，提前偵測「買超減速」
- 保護用戶避免買在法人出貨日

使用方式：
    python3 scripts/reversal_alert.py              # 掃描持股
    python3 scripts/reversal_alert.py 2330 2303    # 指定股票
    python3 scripts/reversal_alert.py --watchlist  # 掃描觀察清單

四層預警：
    Level 1: ⚠️ 動能減弱（買超減速>30%，還沒反轉）
    Level 2: ⚠️⚠️ 單日反轉（連買後突然賣，但累計仍正）
    Level 3: 🔴 連續賣超（連續2日賣超，累計轉負）
    Level 4: 🔴🔴 爆量賣超（單日賣超>20K）

教訓來源：
- 12/10：力積電連續狂買+50K → 隔日法人反轉-20K
- 01/21：聯電連續買超 → 今日法人-59K大舉出貨
- 01/22：凱基金 1/19 +35K → 1/21 反轉-2.5K（需要提前預警）

v2.0 更新（2026-01-22）：
- 🆕 整合籌碼動能分析
- 🆕 四層預警系統
- 🆕 提前偵測買超減速
"""

import sys
import io

# Windows 環境 stdout/stderr 編碼修正（避免中文/emoji 輸出時 cp950 報錯）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import sys
import os
from datetime import datetime, timedelta

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

def get_institutional_data(stock_code, date_str):
    """Get institutional trading data for a specific date"""
    import warnings
    warnings.filterwarnings('ignore')

    url = f'https://www.twse.com.tw/rwd/en/fund/T86?date={date_str}&selectType=ALL&response=json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
    }

    try:
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        data = r.json()
        if 'data' not in data or not data['data']:
            return None
        for row in data['data']:
            if row[0].strip() == stock_code:
                # 單位：股，需轉換為張
                foreign = int(row[3].replace(',', '')) // 1000
                trust = int(row[9].replace(',', '')) // 1000
                total = int(row[17].replace(',', '')) // 1000
                return {
                    'date': date_str,
                    'foreign': foreign,
                    'trust': trust,
                    'total': total
                }
    except Exception as e:
        pass
    return None

def get_trading_dates(days=10):
    """Get last N trading days (Mon-Fri)"""
    dates = []
    current = datetime.now()
    while len(dates) < days:
        if current.weekday() < 5:  # Mon-Fri
            dates.append(current.strftime('%Y%m%d'))
        current -= timedelta(days=1)
    return dates

def calculate_momentum(data_list):
    """
    計算籌碼動能（整合自 chip_analysis.py）

    Returns:
        dict: 動能分析結果
    """
    if len(data_list) < 10:
        return None

    # 前5日 vs 近5日平均
    recent_5 = data_list[-5:]  # 最近5天
    previous_5 = data_list[-10:-5]  # 前5天

    recent_avg = sum(d['total'] for d in recent_5) / 5
    previous_avg = sum(d['total'] for d in previous_5) / 5

    # 計算動能變化率
    if previous_avg != 0:
        momentum_change = ((recent_avg - previous_avg) / abs(previous_avg)) * 100
    else:
        momentum_change = 0

    return {
        'recent_avg': recent_avg,
        'previous_avg': previous_avg,
        'change_pct': momentum_change
    }

def detect_reversal(stock_code, stock_name="", days=10):
    """
    偵測法人反轉訊號（v2.0 多層次預警）

    四層預警系統：
    Level 1: 動能減弱（買超減速>30%）
    Level 2: 單日反轉（連買後突然賣）
    Level 3: 連續賣超（連續2日賣超）
    Level 4: 爆量賣超（單日賣超>20K）

    Returns:
        dict: 反轉分析結果
    """
    dates = get_trading_dates(days)

    # 獲取法人數據
    data_list = []
    for date in dates[::-1]:  # oldest first
        data = get_institutional_data(stock_code, date)
        if data:
            data_list.append(data)

    if len(data_list) < 3:
        return None

    # 分析反轉
    result = {
        'stock_code': stock_code,
        'stock_name': stock_name,
        'data': data_list,
        'alert_level': 'none',
        'alert_reason': '',
        'recommendation': '',
        'warning_level': 0  # 🆕 0=安全, 1-4=四層預警
    }

    # 計算籌碼動能（需要10天數據）
    momentum = None
    if len(data_list) >= 10:
        momentum = calculate_momentum(data_list)
        result['momentum'] = momentum

    # 基本統計
    early_data = data_list[:-2] if len(data_list) > 2 else data_list[:-1]
    recent_2 = data_list[-2:]  # 最近2日
    latest = data_list[-1]

    early_buy_days = sum(1 for d in early_data if d['total'] > 0)
    early_total = sum(d['total'] for d in early_data)
    recent_2_total = sum(d['total'] for d in recent_2)
    cumulative_total = sum(d['total'] for d in data_list)

    # 🆕 四層預警判斷邏輯

    # Level 4: 🔴🔴 爆量賣超（最高危）
    if latest['total'] < -20000:
        result['alert_level'] = 'level4'
        result['warning_level'] = 4
        result['alert_reason'] = f"🔴🔴 Level 4：爆量賣超！今日賣超{latest['total']:+,}張"
        result['recommendation'] = '🔴🔴 極度危險！法人大舉出貨，建議立即出場'
        return result

    # Level 3: 🔴 連續賣超（高危）
    if all(d['total'] < 0 for d in recent_2) and cumulative_total < 0:
        result['alert_level'] = 'level3'
        result['warning_level'] = 3
        result['alert_reason'] = f"🔴 Level 3：連續賣超！近2日累計{recent_2_total:+,}張，累計轉負"
        result['recommendation'] = '🔴 確認反轉！建議減碼或出場'
        return result

    # Level 2: ⚠️⚠️ 單日反轉（警戒）
    if early_buy_days >= len(early_data) * 0.6 and early_total > 5000:
        if latest['total'] < -5000:
            result['alert_level'] = 'level2'
            result['warning_level'] = 2
            result['alert_reason'] = f"⚠️⚠️ Level 2：單日反轉！前期買超{early_total:+,}張，今日賣超{latest['total']:+,}張"
            result['recommendation'] = '⚠️⚠️ 法人翻臉！密切觀察明日，準備停損'
            return result
        elif latest['total'] < 0:
            result['alert_level'] = 'level2_mild'
            result['warning_level'] = 2
            result['alert_reason'] = f"⚠️ Level 2：買轉賣！前期買超{early_total:+,}張，今日小賣{latest['total']:+,}張"
            result['recommendation'] = '⚠️ 注意反轉風險！設好停損'
            return result

    # Level 1: ⚠️ 動能減弱（早期預警）
    if momentum and early_buy_days >= len(early_data) * 0.5:
        if momentum['change_pct'] < -30 and momentum['previous_avg'] > 2000:
            result['alert_level'] = 'level1'
            result['warning_level'] = 1
            result['alert_reason'] = f"⚠️ Level 1：買超減速{momentum['change_pct']:.1f}%！前5日{momentum['previous_avg']:+,.0f}張/日 → 近5日{momentum['recent_avg']:+,.0f}張/日"
            result['recommendation'] = '⚠️ 買超力道減弱！注意可能反轉，建議減碼或鎖利'
            return result

    # ✅ 籌碼健康
    if latest['total'] > 3000 and cumulative_total > 0:
        result['alert_level'] = 'safe'
        result['warning_level'] = 0

        # 加入動能判斷
        if momentum and momentum['change_pct'] > 50:
            result['alert_reason'] = f"✅ 加速買超！今日{latest['total']:+,}張，動能{momentum['change_pct']:+.1f}%"
            result['recommendation'] = '✅ 籌碼超健康！法人加速佈局，可續抱'
        elif momentum and momentum['change_pct'] > 0:
            result['alert_reason'] = f"✅ 持續買超！今日{latest['total']:+,}張，動能{momentum['change_pct']:+.1f}%"
            result['recommendation'] = '✅ 籌碼健康，法人穩定買超，可續抱'
        else:
            result['alert_reason'] = f"✅ 法人買超中。今日{latest['total']:+,}張"
            result['recommendation'] = '✅ 籌碼健康，可續抱'

    return result

def load_holdings():
    """Load holdings from portfolio file"""
    if not HAS_YAML:
        return []

    holdings_file = 'portfolio/my_holdings.yaml'
    if not os.path.exists(holdings_file):
        return []

    with open(holdings_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    holdings = []
    for h in data.get('holdings', []):
        if h.get('quantity', 0) > 0:  # Only active holdings
            holdings.append({
                'symbol': h['symbol'],
                'name': h['name']
            })
    return holdings

def main():
    print("=" * 60)
    print("🔔 法人反轉預警工具 v2.0（多層次預警）")
    print("=" * 60)

    # 決定掃描標的
    if len(sys.argv) > 1:
        if sys.argv[1] == '--watchlist':
            # TODO: 實作觀察清單
            stocks = []
        else:
            # 指定股票
            stocks = [{'symbol': s, 'name': ''} for s in sys.argv[1:]]
    else:
        # 掃描持股
        stocks = load_holdings()
        if not stocks:
            print("❌ 無持股資料，請指定股票代號")
            print("   用法: python3 scripts/reversal_alert.py 2330 2303")
            return

    print(f"\n掃描標的：{len(stocks)} 檔")
    print("-" * 60)

    # 🆕 v2.0 四層預警分類
    alerts = {
        'level4': [],       # 🔴🔴 爆量賣超
        'level3': [],       # 🔴 連續賣超
        'level2': [],       # ⚠️⚠️ 單日反轉
        'level2_mild': [],  # ⚠️ 買轉賣（較輕微）
        'level1': [],       # ⚠️ 動能減弱
        'safe': []          # ✅ 籌碼健康
    }

    for stock in stocks:
        symbol = stock['symbol']
        name = stock.get('name', '')

        print(f"\n🔍 分析 {name}({symbol})...")
        result = detect_reversal(symbol, name, days=10)  # 使用10天數據

        if result:
            level = result['alert_level']
            if level != 'none':
                alerts[level].append(result)

                # 輸出詳細資訊
                print(f"   {result['alert_reason']}")
                print(f"   → {result['recommendation']}")

    # 輸出總結
    print("\n" + "=" * 60)
    print("📊 法人反轉預警總結（v2.0 四層預警）")
    print("=" * 60)

    if alerts['level4']:
        print(f"\n🔴🔴 Level 4：爆量賣超（{len(alerts['level4'])}檔）- 立即出場：")
        for a in alerts['level4']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")
            print(f"     → {a['recommendation']}")

    if alerts['level3']:
        print(f"\n🔴 Level 3：連續賣超（{len(alerts['level3'])}檔）- 確認反轉：")
        for a in alerts['level3']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")
            print(f"     → {a['recommendation']}")

    level2_total = len(alerts['level2']) + len(alerts['level2_mild'])
    if level2_total > 0:
        print(f"\n⚠️⚠️ Level 2：單日反轉（{level2_total}檔）- 密切觀察：")
        for a in alerts['level2'] + alerts['level2_mild']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")
            print(f"     → {a['recommendation']}")

    if alerts['level1']:
        print(f"\n⚠️ Level 1：動能減弱（{len(alerts['level1'])}檔）- 早期預警：")
        for a in alerts['level1']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")
            print(f"     → {a['recommendation']}")

    if alerts['safe']:
        print(f"\n✅ 籌碼健康（{len(alerts['safe'])}檔）：")
        for a in alerts['safe']:
            reason = a['alert_reason'].replace('✅ ', '')  # 移除emoji避免重複
            print(f"   • {a['stock_name']}({a['stock_code']}): {reason}")

    total_alerts = len(alerts['level4']) + len(alerts['level3']) + len(alerts['level2']) + len(alerts['level2_mild']) + len(alerts['level1'])
    if total_alerts == 0:
        print("\n✅ 無反轉警示，籌碼狀況良好")
    else:
        print(f"\n⚠️ 共 {total_alerts} 檔有反轉風險，請注意！")
        print("\n💡 四層預警說明：")
        print("   Level 1 ⚠️：買超減速>30%（早期預警，考慮減碼）")
        print("   Level 2 ⚠️⚠️：連買後突然賣（密切觀察，準備停損）")
        print("   Level 3 🔴：連續2日賣超（確認反轉，建議出場）")
        print("   Level 4 🔴🔴：爆量賣超>20K（極度危險，立即出場）")

if __name__ == '__main__':
    main()
