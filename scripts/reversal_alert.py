#!/usr/bin/env python3
"""
法人反轉預警工具 v1.0

功能：
- 偵測「連續買超後突然賣超」的股票
- 提前預警潛在的法人獲利了結
- 保護用戶避免買在法人出貨日

使用方式：
    python3 scripts/reversal_alert.py              # 掃描持股
    python3 scripts/reversal_alert.py 2330 2303    # 指定股票
    python3 scripts/reversal_alert.py --watchlist  # 掃描觀察清單

教訓來源：
- 12/10：力積電連續狂買+50K → 隔日法人反轉-20K
- 01/21：聯電連續買超 → 今日法人-59K大舉出貨
"""

import requests
import yaml
import sys
import os
from datetime import datetime, timedelta

def get_institutional_data(stock_code, date_str):
    """Get institutional trading data for a specific date"""
    url = f'https://www.twse.com.tw/rwd/en/fund/T86?date={date_str}&selectType=ALL&response=json'
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if 'data' not in data:
            return None
        for row in data['data']:
            if row[0].strip() == stock_code:
                foreign = int(row[4].replace(',', ''))
                trust = int(row[7].replace(',', ''))
                total = foreign + trust
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

def detect_reversal(stock_code, stock_name="", days=7):
    """
    偵測法人反轉訊號

    反轉定義：
    1. 前N-1日連續買超（或多數買超）
    2. 最近1-2日突然轉為賣超

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
        'recommendation': ''
    }

    # 計算前N-2日的買賣狀況
    early_data = data_list[:-2] if len(data_list) > 2 else data_list[:-1]
    recent_data = data_list[-2:]  # 最近2日

    early_buy_days = sum(1 for d in early_data if d['total'] > 0)
    early_total = sum(d['total'] for d in early_data)

    recent_total = sum(d['total'] for d in recent_data)
    latest = data_list[-1]

    # 反轉判斷邏輯

    # 🔴 高危反轉：連續買超後突然大賣
    if early_buy_days >= len(early_data) * 0.7 and early_total > 10000:
        if latest['total'] < -10000:
            result['alert_level'] = 'critical'
            result['alert_reason'] = f"連續買超後突然大賣！前{len(early_data)}日買超{early_total:+,}張，今日賣超{latest['total']:+,}張"
            result['recommendation'] = '🔴 高危！考慮立即減碼或出場'
        elif latest['total'] < -5000:
            result['alert_level'] = 'high'
            result['alert_reason'] = f"連續買超後轉賣！前{len(early_data)}日買超{early_total:+,}張，今日賣超{latest['total']:+,}張"
            result['recommendation'] = '🟠 警戒！觀察明日是否續賣'
        elif latest['total'] < 0:
            result['alert_level'] = 'medium'
            result['alert_reason'] = f"買超趨勢可能反轉。前{len(early_data)}日買超{early_total:+,}張，今日小賣{latest['total']:+,}張"
            result['recommendation'] = '🟡 注意！設好停損觀察'

    # 🟡 中度反轉：買超力道明顯減弱
    elif early_buy_days >= len(early_data) * 0.6 and early_total > 5000:
        if recent_total < early_total * 0.3:
            result['alert_level'] = 'medium'
            result['alert_reason'] = f"買超力道減弱！前期累計{early_total:+,}張，近2日僅{recent_total:+,}張"
            result['recommendation'] = '🟡 買超動能減弱，注意反轉風險'

    # ✅ 持續買超
    elif latest['total'] > 5000 and early_total > 0:
        result['alert_level'] = 'safe'
        result['alert_reason'] = f"法人持續買超中。今日{latest['total']:+,}張"
        result['recommendation'] = '✅ 籌碼健康，可續抱'

    return result

def load_holdings():
    """Load holdings from portfolio file"""
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
    print("🔔 法人反轉預警工具 v1.0")
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

    alerts = {'critical': [], 'high': [], 'medium': [], 'safe': []}

    for stock in stocks:
        symbol = stock['symbol']
        name = stock.get('name', '')

        print(f"\n🔍 分析 {name}({symbol})...")
        result = detect_reversal(symbol, name)

        if result:
            level = result['alert_level']
            if level != 'none':
                alerts[level].append(result)

                # 輸出詳細資訊
                if level == 'critical':
                    print(f"   🔴 {result['alert_reason']}")
                elif level == 'high':
                    print(f"   🟠 {result['alert_reason']}")
                elif level == 'medium':
                    print(f"   🟡 {result['alert_reason']}")
                elif level == 'safe':
                    print(f"   ✅ {result['alert_reason']}")

                print(f"   → {result['recommendation']}")

    # 輸出總結
    print("\n" + "=" * 60)
    print("📊 反轉預警總結")
    print("=" * 60)

    if alerts['critical']:
        print(f"\n🔴 高危反轉（{len(alerts['critical'])}檔）- 考慮立即行動：")
        for a in alerts['critical']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")

    if alerts['high']:
        print(f"\n🟠 警戒反轉（{len(alerts['high'])}檔）- 密切觀察：")
        for a in alerts['high']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")

    if alerts['medium']:
        print(f"\n🟡 注意反轉（{len(alerts['medium'])}檔）- 設好停損：")
        for a in alerts['medium']:
            print(f"   • {a['stock_name']}({a['stock_code']}): {a['alert_reason']}")

    if alerts['safe']:
        print(f"\n✅ 籌碼健康（{len(alerts['safe'])}檔）：")
        for a in alerts['safe']:
            print(f"   • {a['stock_name']}({a['stock_code']})")

    total_alerts = len(alerts['critical']) + len(alerts['high']) + len(alerts['medium'])
    if total_alerts == 0:
        print("\n✅ 無反轉警示，籌碼狀況良好")
    else:
        print(f"\n⚠️ 共 {total_alerts} 檔有反轉風險，請注意！")

if __name__ == '__main__':
    main()
