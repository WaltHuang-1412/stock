#!/usr/bin/env python3
"""
Track A測試工具 v2.0 - 僅測試用途
⚠️ 注意：這是測試專用工具，僅包含Track A
⚠️ 正式盤中分析請使用：intraday_dual_track.py

功能：僅Track A（追蹤盤前推薦股表現）
適用：開發測試、快速驗證
執行時機：開發測試時
正式分析：請使用 intraday_dual_track.py 完整雙軌系統

作者：Claude Code
最後更新：2026-01-22（跨平台修復）
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import requests
import time
import warnings
warnings.filterwarnings('ignore')

# 添加 scripts 目錄到路徑，以便導入 utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from yahoo_finance_api import get_stock_info, get_history

# 導入跨平台工具（P0 修復）
try:
    from utils import (
        get_tracking_file,
        get_tw_now,
        get_tw_today,
        get_tw_yesterday_compact,
        read_json,
        format_datetime_tw,
    )
    USE_CROSS_PLATFORM = True
except ImportError:
    USE_CROSS_PLATFORM = False
    print("⚠️ 警告: 跨平台工具模組未載入，使用降級方案")

def read_tracking_file(date_str):
    """
    讀取盤前推薦追蹤記錄
    防止事後諸葛：只分析tracking.json中的股票

    P0修復：使用 pathlib 統一路徑處理
    """
    # P0-1: 使用跨平台路徑
    if USE_CROSS_PLATFORM:
        tracking_file = get_tracking_file(date_str)
    else:
        # 降級方案
        tracking_file = Path('data') / 'tracking' / f'tracking_{date_str}.json'

    if not tracking_file.exists():
        print("=" * 80)
        print("⚠️ 警告：今日盤前分析未建立追蹤記錄")
        print("=" * 80)
        print()
        print(f"找不到文件：{tracking_file}")
        print()
        print("無法執行盤中分析（防止事後諸葛）")
        print()
        print("請先執行盤前分析，建立推薦追蹤記錄後再執行盤中分析。")
        print("=" * 80)
        return None

    # P0-3: 使用跨平台讀取（統一 UTF-8）
    if USE_CROSS_PLATFORM:
        return read_json(tracking_file)
    else:
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"讀取追蹤文件失敗: {e}")
            return None

def get_institutional_data(date_str):
    """獲取指定日期的法人數據（前一日）"""
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
                        trust_net = float(row[10].replace(',', ''))  # 投信買賣超
                        dealer_net = float(row[11].replace(',', ''))  # 自營商買賣超
                        foreign_net = float(row[4].replace(',', ''))  # 外資買賣超（不含自營）
                        total_net = float(row[18].replace(',', ''))   # 三大法人買賣超

                        institutional_data[code] = {
                            'name': name,
                            'trust_net': trust_net,
                            'dealer_net': dealer_net,
                            'foreign_net': foreign_net,
                            'total_net': total_net
                        }
                    except:
                        pass
                return institutional_data
    except Exception as e:
        print(f"法人數據查詢失敗: {e}")

    return {}

def get_intraday_data_api(stock_code):
    """使用 yahoo_finance_api 共用模組查詢"""
    try:
        history = get_history(stock_code, period='10d', interval='1d')
        if not history or 'timestamps' not in history:
            return None

        closes = [c for c in history['closes'] if c is not None]
        volumes = [v for v in history['volumes'] if v is not None]
        highs = history['highs']
        lows = history['lows']

        if len(closes) < 2:
            return None

        current_price = closes[-1]
        prev_close = closes[-2]
        current_volume = volumes[-1] if volumes else 0
        today_high = highs[-1] if highs and highs[-1] else current_price
        today_low = lows[-1] if lows and lows[-1] else current_price

        # 計算指標
        change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0

        # 計算 5 日平均量
        recent_volumes = [v for v in volumes[-6:-1] if v is not None]
        avg_volume_5d = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        volume_ratio = current_volume / avg_volume_5d if avg_volume_5d > 0 else 0

        return {
            'current_price': current_price,
            'prev_close': prev_close,
            'change_pct': change_pct,
            'volume': current_volume,
            'volume_ratio': volume_ratio,
            'high': today_high,
            'low': today_low
        }
    except Exception as e:
        print(f"API查詢 {stock_code} 失敗: {e}")
        return None


def get_intraday_data(stock_code):
    """獲取盤中股價量能數據（使用 yahoo_finance_api 共用模組）"""
    return get_intraday_data_api(stock_code)

def calculate_five_dimensions_intraday(stock_data, inst_data, market_context):
    """
    五維度評分（盤中版）

    評分標準：
    1. 法人數據（30%）：昨日法人買賣超
    2. 時事現況（30%）：從market_context取得
    3. 產業邏輯（20%）：從market_context取得
    4. 價格位置（10%）：盤中漲幅（關鍵！）
    5. 技術面（10%）：量比
    """
    scores = {}

    # 1. 法人數據（30%）- 使用昨日數據
    trust_score = 0
    if inst_data['trust_net'] > 10000:
        trust_score = 10
    elif inst_data['trust_net'] > 5000:
        trust_score = 8
    elif inst_data['trust_net'] > 1000:
        trust_score = 6
    elif inst_data['trust_net'] > 0:
        trust_score = 4
    elif inst_data['trust_net'] > -5000:
        trust_score = 3
    else:
        trust_score = 2

    # 法人一致性
    consistency_score = 0
    if inst_data['total_net'] > 10000:
        if inst_data['trust_net'] > 5000 and inst_data['foreign_net'] > 0:
            consistency_score = 10  # 投信+外資一致買超
        elif inst_data['trust_net'] > 5000:
            consistency_score = 7   # 投信主導
        else:
            consistency_score = 5
    elif inst_data['total_net'] > 0:
        consistency_score = 4
    else:
        consistency_score = 2  # 法人對決扣分

    institutional_score = (trust_score + consistency_score) / 2
    scores['法人數據'] = round(institutional_score * 3, 1)  # 30%權重

    # 2. 時事現況（30%）- 簡化評估
    # 這裡需要手動輸入或從market_context取得
    # 暫時使用預設值
    scores['時事現況'] = market_context.get('時事現況評分', 7) * 3  # 30%權重

    # 3. 產業邏輯（20%）- 簡化評估
    scores['產業邏輯'] = market_context.get('產業邏輯評分', 7) * 2  # 20%權重

    # 4. 價格位置（10%）- 盤中漲幅（關鍵！）
    change_pct = stock_data['change_pct']
    price_score = 0
    if change_pct < -2:
        price_score = 9  # 下跌反而是機會
    elif -2 <= change_pct < 0:
        price_score = 10  # 微跌最佳
    elif 0 <= change_pct < 1:
        price_score = 10  # 小漲最佳
    elif 1 <= change_pct < 2:
        price_score = 9   # 微漲可接受
    elif 2 <= change_pct < 3:
        price_score = 6   # 已漲一些
    elif 3 <= change_pct < 5:
        price_score = 3   # 追高風險
    else:
        price_score = 1   # 已大漲，絕對不追

    scores['價格位置'] = round(price_score * 1, 1)  # 10%權重

    # 5. 技術面（10%）- 量比
    volume_ratio = stock_data['volume_ratio']
    volume_score = 0
    if volume_ratio > 3:
        volume_score = 9  # 爆量
    elif volume_ratio > 2:
        volume_score = 8  # 大量
    elif volume_ratio > 1.5:
        volume_score = 7  # 放量
    elif volume_ratio > 1:
        volume_score = 6  # 正常
    else:
        volume_score = 4  # 縮量

    scores['技術面'] = round(volume_score * 1, 1)  # 10%權重

    # 計算總分
    total_score = sum(scores.values())
    scores['總分'] = round(total_score, 1)

    return scores

def get_recommendation_rating(score):
    """根據分數給出推薦等級"""
    if score >= 85:
        return "⭐⭐⭐⭐⭐", "強力推薦", "15-20%"
    elif score >= 75:
        return "⭐⭐⭐⭐", "推薦", "10-15%"
    elif score >= 65:
        return "⭐⭐⭐", "可考慮", "5-10%"
    elif score >= 55:
        return "⭐⭐", "觀望優先", "3-5%"
    else:
        return "❌", "避開", "0%"

def analyze_intraday():
    """主程式：盤中五維度分析"""

    print("=" * 80)
    print("盤中五維度分析工具 v2.1（跨平台修復版）")
    print("=" * 80)

    # P0-2: 使用跨平台時間
    if USE_CROSS_PLATFORM:
        print(f"執行時間: {format_datetime_tw()}")
        today = get_tw_today()
        yesterday = get_tw_yesterday_compact()
    else:
        print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

    print()

    # 1. 讀取盤前追蹤記錄
    print(f"正在讀取盤前推薦記錄：{today}")
    tracking = read_tracking_file(today)

    if tracking is None:
        return

    recommendations = tracking.get('recommendations', [])
    if len(recommendations) == 0:
        print("⚠️ 警告：盤前分析未推薦任何股票")
        print("無法執行盤中分析")
        return

    print(f"✅ 成功讀取 {len(recommendations)} 檔推薦股票")
    print()

    # 2. 獲取昨日法人數據
    print(f"正在載入 {yesterday} 法人數據...")
    institutional_data = get_institutional_data(yesterday)
    print(f"已載入 {len(institutional_data)} 檔股票法人數據")
    print()

    # 3. 市場背景（簡化版，實際應從新聞/美股API獲取）
    market_context = tracking.get('market_context', {})
    print("市場背景：")
    print(f"  美股：{market_context.get('us_market', 'N/A')}")
    print(f"  重大新聞：{', '.join(market_context.get('major_news', ['無']))}")
    print()

    # 為簡化，給予預設評分
    market_context['時事現況評分'] = 7  # 中性
    market_context['產業邏輯評分'] = 7  # 中性

    # 4. 分析盤前推薦股票
    results = []
    print("正在分析盤前推薦股票...")
    print()

    for i, rec in enumerate(recommendations):
        stock_code = rec['stock_code']
        stock_name = rec['stock_name']

        print(f"  分析中...{i+1}/{len(recommendations)} {stock_name}({stock_code})")

        # 獲取盤中數據
        intraday_data = get_intraday_data(stock_code)
        if intraday_data is None:
            continue

        # 獲取法人數據
        inst_data = institutional_data.get(stock_code, {
            'trust_net': 0,
            'foreign_net': 0,
            'dealer_net': 0,
            'total_net': 0
        })

        # 五維度評分
        scores = calculate_five_dimensions_intraday(intraday_data, inst_data, market_context)

        # 整合結果
        results.append({
            'code': stock_code,
            'name': stock_name,
            'recommend_price': rec['recommend_price'],
            'current_price': intraday_data['current_price'],
            'change_pct': intraday_data['change_pct'],
            'volume_ratio': intraday_data['volume_ratio'],
            'scores': scores,
            'inst_data': inst_data
        })

        time.sleep(0.1)

    print()
    print(f"分析完成！共 {len(results)} 檔股票")
    print()

    # 5. 輸出分析結果
    output_analysis_results(results)

def output_analysis_results(results):
    """輸出分析結果"""

    # 依總分排序
    results_sorted = sorted(results, key=lambda x: x['scores']['總分'], reverse=True)

    print("=" * 80)
    print("📊 盤中五維度分析結果")
    print("=" * 80)
    print()

    # 分類輸出
    strong_buy = []
    buy = []
    consider = []
    watch = []
    avoid = []

    for r in results_sorted:
        score = r['scores']['總分']
        rating, level, position = get_recommendation_rating(score)

        r['rating'] = rating
        r['level'] = level
        r['position'] = position

        if score >= 85:
            strong_buy.append(r)
        elif score >= 75:
            buy.append(r)
        elif score >= 65:
            consider.append(r)
        elif score >= 55:
            watch.append(r)
        else:
            avoid.append(r)

    # 輸出各分類
    if len(strong_buy) > 0:
        print("⭐⭐⭐⭐⭐ 強力推薦（85分以上）- 可尾盤進場")
        print("-" * 80)
        for r in strong_buy:
            output_stock_detail(r, "strong_buy")
        print()

    if len(buy) > 0:
        print("⭐⭐⭐⭐ 推薦（75-84分）- 可尾盤進場")
        print("-" * 80)
        for r in buy:
            output_stock_detail(r, "buy")
        print()

    if len(consider) > 0:
        print("⭐⭐⭐ 可考慮（65-74分）- 小倉位試單")
        print("-" * 80)
        for r in consider:
            output_stock_detail(r, "consider")
        print()

    if len(watch) > 0:
        print("⭐⭐ 觀望優先（55-64分）")
        print("-" * 80)
        for r in watch:
            output_stock_detail(r, "watch")
        print()

    if len(avoid) > 0:
        print("❌ 避開（<55分）")
        print("-" * 80)
        for r in avoid:
            output_stock_detail(r, "avoid")
        print()

    # 輸出尾盤策略總結
    print("=" * 80)
    print("🎯 尾盤策略總結（12:30-13:30）")
    print("=" * 80)
    print()

    if len(strong_buy) + len(buy) > 0:
        print("✅ 可進場股票：")
        for r in strong_buy + buy:
            intraday_price = r['current_price']
            position = r['position']
            stop_loss_pct = -2  # 盤中停損-2%
            stop_loss_price = intraday_price * (1 + stop_loss_pct / 100)

            print(f"  • {r['name']}({r['code']}): {intraday_price:.2f}元進場{position}")
            print(f"    停損：{stop_loss_price:.2f}元（-2%）、目標：尾盤+1-2%")
        print()

    if len(consider) > 0:
        print("⚠️ 小倉位試單：")
        for r in consider:
            print(f"  • {r['name']}({r['code']}): {r['current_price']:.2f}元小倉位3-5%")
        print()

    if len(watch) + len(avoid) > 0:
        print("❌ 不建議進場：")
        for r in watch + avoid:
            reason = ""
            if r['change_pct'] > 3:
                reason = "已追高"
            elif r['change_pct'] < -2:
                reason = "下跌風險"
            elif r['scores']['法人數據'] < 15:
                reason = "法人對決"
            else:
                reason = "評分不足"

            print(f"  • {r['name']}({r['code']}): {reason}")
        print()

    print("=" * 80)
    print("⚠️ 重要提醒")
    print("=" * 80)
    print("1. 以上分析僅供盤中參考，基於盤前推薦股票")
    print("2. 盤中進場必須設停損-2%")
    print("3. 尾盤策略目標+1-2%，不追求大漲")
    print("4. 若盤中已漲>3%，不追高進場")
    print("5. 必須對照券商軟體確認價格和量能")
    print("=" * 80)

def output_stock_detail(r, category):
    """輸出個股詳細資訊"""
    # P0修復：處理 recommend_price 可能是字串的情況
    recommend_price = r.get('recommend_price', 'N/A')
    if isinstance(recommend_price, (int, float)):
        recommend_price_str = f"{recommend_price:.2f}元"
    else:
        recommend_price_str = str(recommend_price)

    print(f"{r['rating']} {r['name']}({r['code']}) - 總分：{r['scores']['總分']}分")
    print(f"  盤前推薦價：{recommend_price_str}")
    print(f"  盤中價位：{r['current_price']:.2f}元（{r['change_pct']:+.2f}%）")
    print(f"  量比：{r['volume_ratio']:.1f}x")
    print()
    print(f"  五維度評分：")
    print(f"    📊 法人數據：{r['scores']['法人數據']:.1f}分（昨日投信{r['inst_data']['trust_net']/1000:+.1f}K）")
    print(f"    🌍 時事現況：{r['scores']['時事現況']:.1f}分")
    print(f"    🏭 產業邏輯：{r['scores']['產業邏輯']:.1f}分")
    print(f"    💰 價格位置：{r['scores']['價格位置']:.1f}分（盤中{r['change_pct']:+.2f}%）")
    print(f"    📈 技術面：{r['scores']['技術面']:.1f}分（量比{r['volume_ratio']:.1f}x）")
    print()

    if category in ['strong_buy', 'buy']:
        print(f"  🎯 尾盤策略：")
        print(f"    進場價：{r['current_price']:.2f}元")
        print(f"    倉位：{r['position']}")
        stop_loss = r['current_price'] * 0.98
        target = r['current_price'] * 1.02
        print(f"    停損：{stop_loss:.2f}元（-2%）")
        print(f"    目標：{target:.2f}元（+2%，尾盤）")

    print()

if __name__ == '__main__':
    try:
        analyze_intraday()
    except KeyboardInterrupt:
        print("\n程式中斷")
    except Exception as e:
        print(f"\n執行錯誤: {e}")
        import traceback
        traceback.print_exc()
