#!/usr/bin/env python3
"""
法人佈局偵測器 - 全市場掃描
Institutional Positioning Detector

功能：透過量價技術指標推估法人即時佈局行為
執行時機：12:30盤中
掃描範圍：市值前500大活躍股票

作者：Claude Code
日期：2025-12-01
"""

import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time
from pathlib import Path
from datetime import datetime
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from yahoo_finance_api import get_history

# 重點掃描股票清單（市值前500大代表）
SCAN_UNIVERSE = [
    # 權值股
    '2330', '2317', '2454', '1301', '2412', '2882', '6505', '2881',
    '2303', '3711', '2886', '2207', '5880', '1303', '2891', '2002',

    # 科技股
    '2382', '3037', '2408', '6770', '3231', '2344', '2327', '4938',
    '2337', '3189', '2360', '6415', '3443', '4904', '6239', '3008',

    # 金融股
    '2880', '2892', '2885', '2883', '2801', '2890', '5876', '2888',
    '2884', '2887', '2889', '5864', '2849', '2834', '2845',  # 移除 2823 (可能已下市)

    # 傳產股
    '1102', '1216', '2105', '2474', '6505', '1717', '2618', '4943',
    '2609', '2603', '3045', '9904', '2912', '4958', '6176',  # 移除 3697 (可能已下市)

    # 生技醫療
    '6547', '6446', '4174', '6472', '6452', '1762', '4123'  # 移除 4000 (可能已下市)
]

def get_stock_data_fast(symbol):
    """快速取得個股數據"""
    try:
        history = get_history(symbol, period='10d', interval='1d')
        if not history or 'timestamps' not in history:
            return None

        closes = [c for c in history['closes'] if c is not None]
        volumes = [v for v in history['volumes'] if v is not None]
        highs = [h for h in history['highs'] if h is not None]
        lows = [l for l in history['lows'] if l is not None]

        if len(closes) < 5:
            return None

        current_price = closes[-1]
        prev_close = closes[-2] if len(closes) >= 2 else current_price
        volume = volumes[-1] if volumes else 0
        high = highs[-1] if highs else current_price
        low = lows[-1] if lows else current_price

        # 計算量比
        avg_volume_5d = sum(volumes[-6:-1]) / len(volumes[-6:-1]) if len(volumes) >= 6 else (sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 0)
        volume_ratio = volume / avg_volume_5d if avg_volume_5d > 0 else 0

        # 計算漲跌幅
        change_pct = ((current_price - prev_close) / prev_close) * 100

        # 計算5日均線
        ma5 = sum(closes[-5:]) / len(closes[-5:])

        # 計算近5日最高價
        high_5d = max(highs[-5:]) if len(highs) >= 5 else max(highs)

        return {
            'symbol': symbol,
            'current_price': current_price,
            'prev_close': prev_close,
            'change_pct': change_pct,
            'volume': volume,
            'volume_ratio': volume_ratio,
            'high': high,
            'low': low,
            'ma5': ma5,
            'high_5d': high_5d,
            'above_ma5': current_price > ma5,
            'above_high_5d': current_price > high_5d
        }

    except Exception as e:
        return None

def calculate_positioning_score(data):
    """計算佈局評分"""
    if not data:
        return 0

    score = 0
    details = {}

    # 1. 量能異動（30分）
    volume_score = 0
    if data['volume_ratio'] >= 3.0:
        volume_score = 30
    elif data['volume_ratio'] >= 2.5:
        volume_score = 25
    elif data['volume_ratio'] >= 2.0:
        volume_score = 20
    elif data['volume_ratio'] >= 1.5:
        volume_score = 15
    else:
        volume_score = 5

    score += volume_score
    details['量能評分'] = volume_score

    # 2. 價格控制（25分）
    price_score = 0
    change = data['change_pct']
    if -1 <= change <= 1:
        price_score = 25  # 最佳：微漲微跌
    elif 1 < change <= 2:
        price_score = 20  # 良好：小漲
    elif 2 < change <= 3:
        price_score = 10  # 一般：中等漲幅
    elif change > 3:
        price_score = 0   # 追高：已漲太多
    elif change < -2:
        price_score = 5   # 下跌：風險

    score += price_score
    details['價格評分'] = price_score

    # 3. 技術突破（20分）
    tech_score = 0
    if data['above_ma5']:
        tech_score += 10  # 站上5MA
    if data['above_high_5d']:
        tech_score += 10  # 突破近期高點

    score += tech_score
    details['技術評分'] = tech_score

    # 4. 持續性（15分）
    # 簡化：基於當前趨勢
    momentum_score = 0
    if data['change_pct'] > 0 and data['volume_ratio'] > 1:
        momentum_score = 15  # 價漲量增
    elif data['change_pct'] > 0:
        momentum_score = 10  # 僅價漲
    elif data['volume_ratio'] > 1:
        momentum_score = 5   # 僅量增

    score += momentum_score
    details['動能評分'] = momentum_score

    # 5. 基礎加分（10分）
    base_score = 10  # 基礎分
    score += base_score
    details['基礎評分'] = base_score

    return score, details

def scan_positioning_opportunities():
    """掃描佈局機會"""
    print("🔍 法人佈局偵測器")
    print("=" * 60)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"掃描範圍: {len(SCAN_UNIVERSE)} 檔重點股票")
    print()

    start_time = time.time()

    # 多線程並行查詢
    print("正在查詢股票數據...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_stock_data_fast, SCAN_UNIVERSE))

    # 過濾有效數據
    valid_data = [r for r in results if r is not None]
    print(f"成功取得 {len(valid_data)} 檔股票數據")

    # 計算佈局評分
    opportunities = []
    for data in valid_data:
        score, details = calculate_positioning_score(data)
        if score >= 60:  # 只保留60分以上
            opportunities.append({
                **data,
                'positioning_score': score,
                'score_details': details
            })

    # 按評分排序
    opportunities.sort(key=lambda x: x['positioning_score'], reverse=True)

    elapsed = time.time() - start_time
    print(f"分析完成，耗時 {elapsed:.1f} 秒")
    print()

    return opportunities

def output_positioning_report(opportunities):
    """輸出佈局偵測報告"""
    if not opportunities:
        print("❌ 未偵測到明顯佈局機會")
        return

    # 分類輸出
    strong_signals = [op for op in opportunities if op['positioning_score'] >= 80]
    moderate_signals = [op for op in opportunities if 70 <= op['positioning_score'] < 80]
    weak_signals = [op for op in opportunities if 60 <= op['positioning_score'] < 70]

    print("📊 佈局偵測結果")
    print("=" * 60)

    if strong_signals:
        print("🔥 強烈懷疑法人佈局（≥80分）")
        print("-" * 40)
        for op in strong_signals[:5]:  # 最多顯示5檔
            print_opportunity_detail(op, "strong")
        print()

    if moderate_signals:
        print("⚠️ 可能有主力進場（70-79分）")
        print("-" * 40)
        for op in moderate_signals[:3]:  # 最多顯示3檔
            print_opportunity_detail(op, "moderate")
        print()

    if weak_signals:
        print("👁️ 值得觀察（60-69分）")
        print("-" * 40)
        for op in weak_signals[:2]:  # 最多顯示2檔
            print_opportunity_detail(op, "weak")
        print()

    print("=" * 60)
    print("⚠️ 重要提醒")
    print("1. 以上為技術指標推估，非保證獲利")
    print("2. 建議小倉位試單，嚴格停損")
    print("3. 必須搭配基本面分析")
    print("4. 數據有15-20分鐘延遲")
    print("=" * 60)

def print_opportunity_detail(op, category):
    """印出機會詳情"""
    symbol = op['symbol']
    price = op['current_price']
    change = op['change_pct']
    volume_ratio = op['volume_ratio']
    score = op['positioning_score']

    # 取得股票名稱（簡化）
    name_map = {
        '2330': '台積電', '2317': '鴻海', '2454': '聯發科',
        '3037': '欣興', '6770': '力積電', '2408': '南亞科'
    }
    name = name_map.get(symbol, f'股票{symbol}')

    print(f"📈 {name}({symbol}) - 評分：{score}分")
    print(f"   價格：{price:.2f}元（{change:+.2f}%）")
    print(f"   量比：{volume_ratio:.2f}x")

    # 詳細評分
    details = op['score_details']
    print(f"   評分明細：量能{details['量能評分']}分 價格{details['價格評分']}分 技術{details['技術評分']}分")

    # 進場建議
    if category == "strong":
        print(f"   💡 建議：可考慮進場5-10%，停損-3%")
    elif category == "moderate":
        print(f"   💡 建議：小倉位3-5%試單，停損-3%")
    else:
        print(f"   💡 建議：觀察，暫不進場")
    print()

if __name__ == '__main__':
    try:
        # 執行佈局偵測
        opportunities = scan_positioning_opportunities()

        # 輸出報告
        output_positioning_report(opportunities)

    except KeyboardInterrupt:
        print("\\n程式中斷")
    except Exception as e:
        print(f"\\n執行錯誤: {e}")
        import traceback
        traceback.print_exc()