#!/usr/bin/env python3
"""
盤中即時量能分析工具
目的：客觀找出「法人正在佈局、但還沒大漲」的機會股

使用方式：
python3 intraday_scanner.py

執行時機：
- 建議在 12:00-12:30 執行（盤中）
- 可在 13:00 前決定尾盤策略
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import requests
import time
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent))
from yahoo_finance_api import get_history

def get_institutional_data(date_str):
    """獲取指定日期的法人數據"""
    url = f'https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json'
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                institutional_data = {}
                for row in data['data']:
                    code = row[0].strip()
                    name = row[1].strip()
                    try:
                        inst_net = float(row[4].replace(',', ''))
                        trust_net = float(row[10].replace(',', ''))
                        dealer_net = float(row[7].replace(',', ''))
                        foreign_net = inst_net - trust_net - dealer_net

                        institutional_data[code] = {
                            'name': name,
                            'inst_net': inst_net,
                            'trust_net': trust_net,
                            'dealer_net': dealer_net,
                            'foreign_net': foreign_net
                        }
                    except:
                        pass
                return institutional_data
    except Exception as e:
        print(f"法人數據查詢失敗: {e}")

    return {}

def get_stock_list():
    """獲取台股主要股票列表（上市公司）"""
    # 這裡列出台股主要標的（可擴充）
    # 格式: 股票代號
    stocks = []

    # 權值股 + 熱門股
    major_stocks = [
        '2330', '2317', '2454', '2881', '2882', '2883', '2884', '2885', '2886', '2887', '2888', '2890', '2891', '2892',
        '2303', '2308', '2382', '2412', '2408', '3008', '3711', '6505', '1301', '1303', '1326',
        '2337', '2344', '2377', '2395', '2609', '2610', '2618', '2633', '3037', '3045', '6415',
        '6770', '6239', '3715', '8112', '3013', '2408', '2409', '5347', '6531', '3034'
    ]

    return major_stocks

def analyze_intraday_volume():
    """盤中量能分析主程式"""

    print("=" * 80)
    print("盤中即時量能分析工具")
    print("=" * 80)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 獲取昨日法人數據
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    print(f"正在載入 {yesterday} 法人數據...")
    institutional_data = get_institutional_data(yesterday)
    print(f"已載入 {len(institutional_data)} 檔股票法人數據")
    print()

    # 2. 掃描股票
    print("正在掃描股票即時量能...")
    stock_list = get_stock_list()

    results = []

    for i, code in enumerate(stock_list):
        try:
            history = get_history(code, period='10d', interval='1d')

            if not history or 'timestamps' not in history:
                continue

            closes = [c for c in history['closes'] if c is not None]
            volumes = [v for v in history['volumes'] if v is not None]

            if len(closes) < 6 or len(volumes) < 6:
                continue

            # 當日數據
            current_price = closes[-1]
            prev_close = closes[-2]
            current_volume = volumes[-1]

            # 計算指標
            change_pct = ((current_price - prev_close) / prev_close) * 100
            avg_volume_5d = sum(volumes[-6:-1]) / len(volumes[-6:-1])
            volume_ratio = current_volume / avg_volume_5d if avg_volume_5d > 0 else 0

            # 獲取法人數據
            inst_info = institutional_data.get(code, {})
            trust_net = inst_info.get('trust_net', 0)
            foreign_net = inst_info.get('foreign_net', 0)
            inst_net = inst_info.get('inst_net', 0)

            # 儲存結果
            results.append({
                'code': code,
                'name': inst_info.get('name', ''),
                'price': current_price,
                'change_pct': change_pct,
                'volume': current_volume,
                'volume_ratio': volume_ratio,
                'trust_net': trust_net,
                'foreign_net': foreign_net,
                'inst_net': inst_net
            })

            # 進度顯示
            if (i + 1) % 10 == 0:
                print(f"已掃描 {i+1}/{len(stock_list)} 檔...")

            time.sleep(0.1)  # 避免請求過快

        except Exception as e:
            continue

    print(f"掃描完成！共 {len(results)} 檔有效數據")
    print()

    # 3. 篩選機會股
    df = pd.DataFrame(results)

    # 篩選條件
    print("=" * 80)
    print("🔥 機會股篩選（法人佈局中、但還沒大漲）")
    print("=" * 80)
    print()

    # 條件1: 爆量但小漲（量比>3倍、漲幅<3%）+ 昨日法人買超
    opportunity_stocks = df[
        (df['volume_ratio'] > 3.0) &  # 爆量
        (df['change_pct'] > -1) &      # 不是下跌
        (df['change_pct'] < 3) &       # 還沒大漲
        (df['inst_net'] > 1000)        # 昨日法人買超
    ].sort_values('volume_ratio', ascending=False)

    if len(opportunity_stocks) > 0:
        print("✅ 發現機會股（爆量+小漲+法人買）：")
        print()
        print(f"{'代號':<6} {'名稱':<10} {'漲跌%':>7} {'量比':>6} {'昨日投信':>10} {'昨日外資':>10}")
        print("-" * 70)
        for _, row in opportunity_stocks.head(15).iterrows():
            print(f"{row['code']:<6} {row['name']:<10} {row['change_pct']:>6.2f}% {row['volume_ratio']:>5.1f}x "
                  f"{row['trust_net']:>10,.0f} {row['foreign_net']:>10,.0f}")
        print()
    else:
        print("❌ 目前無符合條件的機會股")
        print()

    # 條件2: 投信大買（昨日投信買超>1000K）+ 今日爆量
    trust_focus = df[
        (df['trust_net'] > 1000) &     # 投信大買
        (df['volume_ratio'] > 2.0)     # 爆量
    ].sort_values('trust_net', ascending=False)

    if len(trust_focus) > 0:
        print("=" * 80)
        print("📊 投信聚焦股（昨日投信大買+今日爆量）：")
        print("=" * 80)
        print()
        print(f"{'代號':<6} {'名稱':<10} {'漲跌%':>7} {'量比':>6} {'昨日投信':>10} {'判斷':<20}")
        print("-" * 70)
        for _, row in trust_focus.head(15).iterrows():
            judgment = ""
            if row['change_pct'] > 5:
                judgment = "❌ 已大漲（太晚）"
            elif row['change_pct'] > 3:
                judgment = "⚠️ 偏強（觀望）"
            elif row['change_pct'] > 0:
                judgment = "✅ 吸貨中（機會）"
            else:
                judgment = "⚠️ 接刀中（風險）"

            print(f"{row['code']:<6} {row['name']:<10} {row['change_pct']:>6.2f}% {row['volume_ratio']:>5.1f}x "
                  f"{row['trust_net']:>10,.0f} {judgment:<20}")
        print()

    # 條件3: 外資大買（昨日外資買超>5000K）+ 今日爆量
    foreign_focus = df[
        (df['foreign_net'] > 5000) &   # 外資大買
        (df['volume_ratio'] > 2.0)     # 爆量
    ].sort_values('foreign_net', ascending=False)

    if len(foreign_focus) > 0:
        print("=" * 80)
        print("🌍 外資聚焦股（昨日外資大買+今日爆量）：")
        print("=" * 80)
        print()
        print(f"{'代號':<6} {'名稱':<10} {'漲跌%':>7} {'量比':>6} {'昨日外資':>10} {'判斷':<20}")
        print("-" * 70)
        for _, row in foreign_focus.head(15).iterrows():
            judgment = ""
            if row['change_pct'] > 5:
                judgment = "❌ 已大漲（太晚）"
            elif row['change_pct'] > 3:
                judgment = "⚠️ 偏強（觀望）"
            elif row['change_pct'] > 0:
                judgment = "✅ 吸貨中（機會）"
            else:
                judgment = "⚠️ 接刀中（風險）"

            print(f"{row['code']:<6} {row['name']:<10} {row['change_pct']:>6.2f}% {row['volume_ratio']:>5.1f}x "
                  f"{row['foreign_net']:>10,.0f} {judgment:<20}")
        print()

    # 條件4: 法人對決（投信買+外資賣 或 投信賣+外資買）
    institutional_conflict = df[
        (
            ((df['trust_net'] > 1000) & (df['foreign_net'] < -5000)) |  # 投信買+外資賣
            ((df['trust_net'] < -1000) & (df['foreign_net'] > 5000))    # 投信賣+外資買
        )
    ].sort_values('volume_ratio', ascending=False)

    if len(institutional_conflict) > 0:
        print("=" * 80)
        print("⚠️ 法人對決股（投信vs外資意見分歧）：")
        print("=" * 80)
        print()
        print(f"{'代號':<6} {'名稱':<10} {'漲跌%':>7} {'量比':>6} {'投信':>10} {'外資':>10} {'判斷':<15}")
        print("-" * 80)
        for _, row in institutional_conflict.head(10).iterrows():
            if row['trust_net'] > 0:
                judgment = "投信買vs外資賣"
            else:
                judgment = "投信賣vs外資買"

            print(f"{row['code']:<6} {row['name']:<10} {row['change_pct']:>6.2f}% {row['volume_ratio']:>5.1f}x "
                  f"{row['trust_net']:>10,.0f} {row['foreign_net']:>10,.0f} {judgment:<15}")
        print()

    # 條件5: 爆量下跌（可能是停損或出貨）
    volume_dump = df[
        (df['volume_ratio'] > 3.0) &   # 爆量
        (df['change_pct'] < -2)        # 下跌
    ].sort_values('volume_ratio', ascending=False)

    if len(volume_dump) > 0:
        print("=" * 80)
        print("❌ 爆量下跌股（法人出貨或停損）：")
        print("=" * 80)
        print()
        print(f"{'代號':<6} {'名稱':<10} {'跌幅%':>7} {'量比':>6} {'昨日法人':>10} {'判斷':<20}")
        print("-" * 70)
        for _, row in volume_dump.head(10).iterrows():
            judgment = ""
            if row['inst_net'] < -1000:
                judgment = "❌ 法人出貨（避開）"
            elif row['inst_net'] > 1000:
                judgment = "⚠️ 法人接刀（風險）"
            else:
                judgment = "⚠️ 散戶恐慌"

            print(f"{row['code']:<6} {row['name']:<10} {row['change_pct']:>6.2f}% {row['volume_ratio']:>5.1f}x "
                  f"{row['inst_net']:>10,.0f} {judgment:<20}")
        print()

    print("=" * 80)
    print("分析完成")
    print("=" * 80)
    print()
    print("📌 使用建議：")
    print("1. 優先關注「機會股」：爆量+小漲+法人買 → 可能是法人吸貨中")
    print("2. 「投信聚焦股」若為✅吸貨中 → 可考慮尾盤進場")
    print("3. 「法人對決股」需觀望 → 等盤後法人數據確認誰對誰錯")
    print("4. 「爆量下跌股」避開 → 尤其是法人出貨的標的")
    print()

if __name__ == '__main__':
    try:
        analyze_intraday_volume()
    except KeyboardInterrupt:
        print("\n程式中斷")
    except Exception as e:
        print(f"\n執行錯誤: {e}")
        import traceback
        traceback.print_exc()
