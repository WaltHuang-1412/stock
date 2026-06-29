#!/usr/bin/env python3
"""
法人持股水位分析工具
功能：
1. 查詢外資/投信持股比例
2. 計算賣超佔持股比例
3. 評估出場壓力
4. 追蹤持股比例變化

用法：
  python3 scripts/holdings_analysis.py 2409           # 單檔查詢
  python3 scripts/holdings_analysis.py 2409 3481 2330 # 多檔查詢
  python3 scripts/holdings_analysis.py 2409 --days 15 # 指定天數
"""

import sys
import io

# Windows 環境 stdout/stderr 編碼修正（避免中文/emoji 輸出時 cp950 報錯）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import json
from datetime import datetime, timedelta
import time

# 忽略 SSL 警告
import warnings
warnings.filterwarnings('ignore')


def get_foreign_holdings():
    """查詢外資持股比例（全市場）"""
    url = 'https://www.twse.com.tw/rwd/zh/fund/MI_QFIIS?date=&selectType=ALLBUT0999&response=json'

    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        data = r.json()

        if 'data' not in data:
            return {}

        holdings = {}
        for row in data['data']:
            stock_code = row[0]
            stock_name = row[1]
            try:
                issued_shares = int(row[3].replace(',', ''))  # 發行股數
                foreign_available = int(row[4].replace(',', ''))  # 外資尚可投資
                foreign_held = int(row[5].replace(',', ''))  # 外資持股
                local_pct = float(row[6])  # 本國人持股比例
                foreign_pct = float(row[7])  # 外資持股比例

                holdings[stock_code] = {
                    'name': stock_name,
                    'issued_shares': issued_shares,
                    'foreign_held': foreign_held,
                    'foreign_pct': foreign_pct,
                    'local_pct': local_pct,
                    'foreign_held_lots': foreign_held // 1000  # 轉換為張數
                }
            except (ValueError, IndexError):
                continue

        return holdings
    except Exception as e:
        print(f"❌ 查詢外資持股失敗: {e}")
        return {}


def get_trust_holdings(stock_code):
    """查詢投信持股（需從其他來源）"""
    # 投信持股需要從基金持股明細查詢，這裡先返回 None
    # 未來可以擴展
    return None


def get_recent_institutional_flow(stock_code, days=10):
    """查詢近N日法人買賣超（單位：張）"""
    total_flow = 0
    foreign_flow = 0
    trust_flow = 0
    daily_data = []

    date = datetime.now()
    count = 0
    attempts = 0
    max_attempts = days + 15  # 考慮假日

    while count < days and attempts < max_attempts:
        date_str = date.strftime('%Y%m%d')

        url = f'https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALLBUT0999&response=json'

        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            data = r.json()

            if 'data' in data and len(data['data']) > 0:
                for row in data['data']:
                    if row[0].strip() == stock_code:
                        try:
                            # API 返回的是「股」，需要除以1000轉換為「張」
                            foreign = int(row[4].replace(',', '')) // 1000
                            trust = int(row[10].replace(',', '')) // 1000
                            dealer = int(row[11].replace(',', '')) // 1000
                            total = foreign + trust + dealer  # 外資+投信+自營

                            daily_data.append({
                                'date': date_str,
                                'total': total,
                                'foreign': foreign,
                                'trust': trust
                            })

                            total_flow += total
                            foreign_flow += foreign
                            trust_flow += trust
                            count += 1
                        except (ValueError, IndexError):
                            pass
                        break

            time.sleep(0.3)
        except Exception:
            pass

        date -= timedelta(days=1)
        attempts += 1

    return {
        'days': count,
        'total_flow': total_flow,  # 單位：張
        'foreign_flow': foreign_flow,  # 單位：張
        'trust_flow': trust_flow,  # 單位：張
        'daily_data': daily_data
    }


def calculate_exit_pressure(holdings_info, flow_info):
    """計算出場壓力指標"""
    if not holdings_info or not flow_info:
        return None

    foreign_held_lots = holdings_info['foreign_held_lots']
    foreign_flow = flow_info['foreign_flow']  # 已經是張數

    if foreign_held_lots == 0:
        return None

    # 計算賣超佔持股比例
    flow_pct = (foreign_flow / foreign_held_lots) * 100

    # 評估壓力等級
    if flow_pct < -20:
        pressure = '🔴 高壓（大量出貨中）'
        suggestion = '建議減碼或觀望'
    elif flow_pct < -10:
        pressure = '🟠 中高壓（持續出貨）'
        suggestion = '密切關注，設好停損'
    elif flow_pct < -5:
        pressure = '🟡 中壓（小幅調節）'
        suggestion = '觀察是否持續'
    elif flow_pct < 5:
        pressure = '⚪ 低壓（持平）'
        suggestion = '法人態度中性'
    elif flow_pct < 10:
        pressure = '🟢 吸籌（小幅加碼）'
        suggestion = '正向訊號'
    else:
        pressure = '🔥 強力吸籌（大幅加碼）'
        suggestion = '法人積極佈局'

    return {
        'foreign_held_lots': foreign_held_lots,
        'foreign_flow_lots': foreign_flow,
        'flow_pct': flow_pct,
        'pressure': pressure,
        'suggestion': suggestion
    }


def analyze_stock(stock_code, holdings_data, days=10):
    """分析單檔股票"""
    print(f"\n{'='*60}")
    print(f"📊 {stock_code} 法人持股水位分析")
    print('='*60)

    # 取得持股資料
    if stock_code not in holdings_data:
        print(f"❌ 找不到 {stock_code} 的外資持股資料")
        return None

    holdings = holdings_data[stock_code]

    print(f"\n【外資持股概況】")
    print(f"  股票名稱：{holdings['name']}")
    print(f"  發行股數：{holdings['issued_shares']:,} 股")
    print(f"  外資持股：{holdings['foreign_held']:,} 股 ({holdings['foreign_held_lots']:,} 張)")
    print(f"  外資持股比例：{holdings['foreign_pct']:.2f}%")
    print(f"  本國人持股比例：{holdings['local_pct']:.2f}%")

    # 查詢近期法人買賣超
    print(f"\n⏳ 正在查詢近 {days} 日法人買賣超...")
    flow_info = get_recent_institutional_flow(stock_code, days)

    if flow_info['days'] > 0:
        print(f"\n【近 {flow_info['days']} 日法人動向】")
        print(f"  三大法人累計：{flow_info['total_flow']:+,} 張")
        print(f"  外資累計：{flow_info['foreign_flow']:+,} 張")
        print(f"  投信累計：{flow_info['trust_flow']:+,} 張")

        # 計算出場壓力
        pressure = calculate_exit_pressure(holdings, flow_info)

        if pressure:
            print(f"\n【出場壓力分析】")
            print(f"  外資持股：{pressure['foreign_held_lots']:,} 張")
            print(f"  近期外資買賣超：{pressure['foreign_flow_lots']:+,} 張")
            print(f"  買賣超佔持股比例：{pressure['flow_pct']:+.2f}%")
            print(f"  壓力評估：{pressure['pressure']}")
            print(f"  操作建議：{pressure['suggestion']}")

            # 預估未來壓力
            print(f"\n【出貨空間預估】")
            current_pct = holdings['foreign_pct']

            # 假設外資持股可能降到的水位
            target_levels = [
                (current_pct - 5, "輕度減碼"),
                (current_pct - 10, "中度減碼"),
                (current_pct - 15, "重度減碼"),
            ]

            print(f"  目前外資持股：{current_pct:.2f}%")
            for target_pct, desc in target_levels:
                if target_pct > 0:
                    shares_to_sell = holdings['foreign_held'] * (1 - target_pct/current_pct)
                    lots_to_sell = shares_to_sell // 1000
                    print(f"  若降至 {target_pct:.1f}%（{desc}）：還需賣出約 {lots_to_sell:,.0f} 張")

        return {
            'stock_code': stock_code,
            'stock_name': holdings['name'],
            'holdings': holdings,
            'flow': flow_info,
            'pressure': pressure
        }
    else:
        print("❌ 無法取得法人買賣超資料")
        return None


def print_summary(results):
    """列印摘要表格"""
    if not results:
        return

    print(f"\n{'='*80}")
    print("📋 持股水位分析摘要")
    print('='*80)

    print(f"\n| 股票 | 外資持股% | 近期外資 | 佔持股% | 壓力評估 |")
    print(f"|------|----------|---------|--------|---------|")

    for r in results:
        if r and r.get('pressure'):
            p = r['pressure']
            h = r['holdings']
            print(f"| {r['stock_code']} {r['stock_name'][:4]} | {h['foreign_pct']:.1f}% | {p['foreign_flow_lots']:+,}張 | {p['flow_pct']:+.1f}% | {p['pressure'][:10]} |")


def main():
    if len(sys.argv) < 2:
        print("用法：python3 holdings_analysis.py <股票代號> [股票代號2] ... [--days N]")
        print("範例：python3 holdings_analysis.py 2409 3481 2330")
        print("      python3 holdings_analysis.py 2409 --days 15")
        sys.exit(1)

    # 解析參數
    stocks = []
    days = 10

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--days' and i + 1 < len(sys.argv):
            days = int(sys.argv[i + 1])
            i += 2
        else:
            stocks.append(sys.argv[i])
            i += 1

    print("="*60)
    print("📊 法人持股水位分析工具")
    print(f"   查詢股票：{', '.join(stocks)}")
    print(f"   分析天數：{days} 天")
    print("="*60)

    # 取得全市場外資持股資料
    print("\n⏳ 正在載入外資持股資料...")
    holdings_data = get_foreign_holdings()

    if not holdings_data:
        print("❌ 無法取得外資持股資料")
        sys.exit(1)

    print(f"✅ 已載入 {len(holdings_data)} 檔股票的外資持股資料")

    # 分析每檔股票
    results = []
    for stock in stocks:
        result = analyze_stock(stock, holdings_data, days)
        results.append(result)

    # 列印摘要
    print_summary(results)

    print(f"\n{'='*60}")
    print("✅ 分析完成")
    print("="*60)


if __name__ == '__main__':
    main()
