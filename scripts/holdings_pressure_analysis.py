#!/usr/bin/env python3
"""
持股壓力分析工具（簡化版，無外部依賴）
使用方式：python scripts/holdings_pressure_analysis.py
"""

import urllib.request
import json
import ssl
from datetime import datetime

def get_current_holdings():
    """讀取持股清單（手動解析YAML）"""
    holdings = []

    with open('portfolio/my_holdings.yaml', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_holding = {}
    for line in lines:
        line = line.strip()

        if line.startswith('- symbol:'):
            if current_holding and current_holding.get('quantity', 0) > 0:
                holdings.append(current_holding)
            current_holding = {}
            current_holding['symbol'] = line.split('"')[1]

        elif 'name:' in line and current_holding:
            current_holding['name'] = line.split('"')[1]

        elif 'buy_price:' in line and current_holding:
            try:
                current_holding['cost'] = float(line.split(':')[1].strip().split('#')[0].strip())
            except:
                pass

        elif 'quantity:' in line and current_holding:
            try:
                qty_str = line.split(':')[1].strip().split('#')[0].strip()
                current_holding['quantity'] = int(qty_str) if qty_str else 0
            except:
                current_holding['quantity'] = 0

    # 最後一筆
    if current_holding and current_holding.get('quantity', 0) > 0:
        holdings.append(current_holding)

    return holdings

def get_stock_price(stock_code):
    """查詢即時股價"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW?interval=1d&range=2d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read())

        result = data['chart']['result'][0]
        meta = result['meta']

        current = meta.get('regularMarketPrice', meta.get('chartPreviousClose'))
        prev = meta.get('previousClose', meta.get('chartPreviousClose'))

        return current, prev
    except:
        return None, None

def get_institutional_data_from_analysis():
    """從今日盤前分析讀取法人數據"""
    try:
        with open('data/2026-01-20/before_market_analysis.md', 'r', encoding='utf-8') as f:
            content = f.read()

        # 簡單解析持股警示表格
        institutional_map = {}

        if '| 緯創(3231)' in content and '-62K' in content:
            institutional_map['3231'] = -62
        if '| 群創(3481)' in content and '-33K' in content:
            institutional_map['3481'] = -33
        if '| 南亞(1303)' in content and '-18K' in content:
            institutional_map['1303'] = -18
        if '| 台積電(2330)' in content and '-11K' in content:
            institutional_map['2330'] = -11
        if '| 兆豐金(2886)' in content and '-2.5K' in content:
            institutional_map['2886'] = -2.5
        if '| 台塑(1301)' in content and '+10K' in content:
            institutional_map['1301'] = 10

        return institutional_map
    except:
        return {}

def analyze_pressure(cost, current_price, institutional_flow, profit_pct):
    """分析出場壓力"""
    pressure_level = 0
    reasons = []

    # 虧損判斷
    if profit_pct < -10:
        pressure_level += 3
        reasons.append(f"虧損{profit_pct:.1f}%")
    elif profit_pct < -5:
        pressure_level += 2
        reasons.append(f"虧損{profit_pct:.1f}%")

    # 法人賣超判斷
    if institutional_flow < -50:
        pressure_level += 3
        reasons.append(f"法人狂賣{institutional_flow:.0f}K")
    elif institutional_flow < -20:
        pressure_level += 2
        reasons.append(f"法人大賣{institutional_flow:.0f}K")
    elif institutional_flow < 0:
        pressure_level += 1
        reasons.append(f"法人賣超{institutional_flow:.0f}K")

    # 暴利判斷
    if profit_pct > 50:
        pressure_level += 2
        reasons.append(f"暴利{profit_pct:.1f}%")
    elif profit_pct > 20:
        pressure_level += 1
        reasons.append(f"高報酬{profit_pct:.1f}%")

    # 壓力等級
    if pressure_level >= 5:
        level = "🔴🔴🔴 極高"
        action = "🚨 立即出場"
    elif pressure_level >= 3:
        level = "🔴🔴 高"
        action = "🔥 盡快減碼"
    elif pressure_level >= 2:
        level = "🟡 中"
        action = "⚠️ 觀察減碼"
    else:
        level = "🟢 低"
        action = "✅ 續抱"

    return level, action, reasons

def main():
    print("=" * 60)
    print("📊 持股壓力分析報告")
    print(f"⏰ 分析時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()

    # 讀取持股
    holdings = get_current_holdings()
    print(f"✅ 讀取到 {len(holdings)} 檔持股\n")

    # 讀取法人數據
    institutional_map = get_institutional_data_from_analysis()

    # 分析結果
    results = []

    print("📈 查詢即時股價與法人數據...\n")

    for holding in holdings:
        code = holding['symbol']
        name = holding['name']
        cost = holding['cost']
        qty = holding['quantity']

        # 查詢股價
        current, prev = get_stock_price(code)

        if current is None:
            print(f"❌ {name}({code}): 無法獲取股價")
            continue

        # 計算報酬率
        profit_pct = ((current - cost) / cost * 100)

        # 法人數據
        institutional_flow = institutional_map.get(code, 0)

        # 壓力分析
        level, action, reasons = analyze_pressure(cost, current, institutional_flow, profit_pct)

        results.append({
            'code': code,
            'name': name,
            'cost': cost,
            'current': current,
            'profit_pct': profit_pct,
            'institutional': institutional_flow,
            'level': level,
            'action': action,
            'reasons': reasons
        })

        print(f"✅ {name}({code}): {current:.2f}元 ({profit_pct:+.2f}%) 法人{institutional_flow:+.1f}K")

    print("\n" + "=" * 60)
    print("📋 壓力分析總覽")
    print("=" * 60)
    print()
    print(f"{'代號':<8} {'名稱':<10} {'成本':>8} {'現價':>8} {'報酬%':>8} {'法人':>8} {'壓力等級':<12} {'建議'}")
    print("-" * 90)

    # 按壓力等級排序
    results.sort(key=lambda x: x['level'], reverse=True)

    for r in results:
        print(f"{r['code']:<8} {r['name']:<10} {r['cost']:>8.2f} {r['current']:>8.2f} {r['profit_pct']:>7.2f}% "
              f"{r['institutional']:>7.1f}K {r['level']:<12} {r['action']}")

    print("\n" + "=" * 60)
    print("⚠️ 立即處理建議")
    print("=" * 60)
    print()

    urgent = [r for r in results if '極高' in r['level'] or '高' in r['level']]

    if urgent:
        for i, r in enumerate(urgent, 1):
            print(f"{i}. {r['name']}({r['code']}): {r['action']}")
            print(f"   原因: {', '.join(r['reasons'])}")
            print()
    else:
        print("✅ 無需立即處理的持股")

    print("分析完成！")

if __name__ == '__main__':
    main()
