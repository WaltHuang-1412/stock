#!/usr/bin/env python3
"""
盤中雙軌分析工具
Intraday Dual-Track Analysis System

Track A: 追蹤盤前推薦股（防事後諸葛）
Track B: 全市場即時掃描（發現新機會）

執行時機：12:30-13:00
輸出：雙軌分析結果 + 可執行建議（非判斷對錯）

作者：Claude Code
最後更新：2026-01-22（跨平台修復）
"""

import sys
import io

# Windows 環境 stdout/stderr 編碼修正（避免中文/emoji 輸出時 cp950 報錯）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# yfinance 可選依賴（P0 修復：解決 Python 3.15 相容性問題）
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("⚠️ 警告: yfinance 未安裝，將使用 Yahoo Finance API 直接查詢")

# 添加 scripts 目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

# 導入跨平台工具（P0 修復）
try:
    from utils import (
        get_tracking_file,
        get_tw_now,
        get_tw_today,
        get_analysis_dir,
        ensure_dir,
        read_json,
        write_json
    )
    USE_CROSS_PLATFORM = True
except ImportError:
    import os
    USE_CROSS_PLATFORM = False

# 全市場掃描清單（200檔活躍股票）
MARKET_UNIVERSE = [
    # 權值股
    '2330', '2317', '2454', '2308', '2412', '2382', '1303', '1301',
    '2881', '2882', '2891', '2886', '1326', '2892', '3711', '2002',

    # 金融股（完整）
    '2880', '2883', '2884', '2885', '2887', '2888', '2889', '2890',
    '5880', '2801', '2809', '2812', '2834', '2845', '2849',

    # 半導體
    '2303', '3008', '2379', '2408', '3034', '6770', '2337', '2344',
    '3189', '3037', '2449', '3443', '6415', '8016', '3661',

    # 電子零組件
    '2327', '2409', '3481', '2377', '3231', '2356', '2357', '2395',
    '2301', '2324', '2353', '2354', '2385', '3017', '3023',

    # 傳產塑化
    '1402', '1605', '2207', '6505', '2610', '2609', '2615', '2603',
    '2912', '9910', '1101', '1102', '2201', '2227', '2231',

    # 生技醫療
    '4743', '1707', '4142', '6547', '6446', '1760', '4174', '4123',

    # 其他重要個股
    '3045', '2105', '2707', '9904', '2633', '3529', '4904', '4938',
    '1504', '1507', '1513', '1515', '1590', '2206', '2458', '2498'
]

def read_tracking_file(date_str):
    """
    讀取盤前推薦追蹤記錄

    P0修復：使用跨平台路徑和檔案讀取
    """
    # P0-1: 使用跨平台路徑
    if USE_CROSS_PLATFORM:
        tracking_file = get_tracking_file(date_str)
        tracking = read_json(tracking_file)
        if tracking is None:
            print("⚠️ 找不到tracking檔案，將只執行Track B全市場掃描")
        return tracking
    else:
        tracking_file = f'data/tracking/tracking_{date_str}.json'

        if not os.path.exists(tracking_file):
            print("⚠️ 找不到tracking檔案，將只執行Track B全市場掃描")
            return None

        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                tracking = json.load(f)
            return tracking
        except Exception as e:
            print(f"讀取tracking檔案失敗: {e}")
            return None

def get_realtime_data_api(stock_code):
    """使用 Yahoo Finance API 直接查詢（無需 yfinance 套件）"""
    import requests
    import warnings

    # 抑制所有警告和錯誤輸出
    warnings.filterwarnings('ignore')

    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}.TW?interval=1d&range=5d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()
        result = data.get('chart', {}).get('result', [])

        if not result:
            return None

        quote = result[0]
        meta = quote.get('meta', {})
        indicators = quote.get('indicators', {}).get('quote', [{}])[0]

        closes = indicators.get('close', [])
        volumes = indicators.get('volume', [])

        # 過濾掉 None 值
        valid_closes = [c for c in closes if c is not None]
        valid_volumes = [v for v in volumes if v is not None]

        if len(valid_closes) < 2:
            return None

        current_price = valid_closes[-1]
        prev_close = valid_closes[-2] if len(valid_closes) >= 2 else current_price
        current_volume = valid_volumes[-1] if valid_volumes else 0

        # 計算指標
        change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0

        # 計算 5 日平均量
        recent_volumes = [v for v in valid_volumes[:-1] if v is not None]
        avg_volume_5d = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
        volume_ratio = current_volume / avg_volume_5d if avg_volume_5d > 0 else 0

        # 獲取股票名稱
        stock_name = meta.get('longName', '') or meta.get('shortName', '') or stock_code

        return {
            'code': stock_code,
            'name': stock_name,
            'current_price': round(current_price, 2),
            'prev_close': round(prev_close, 2),
            'change_pct': round(change_pct, 2),
            'volume': current_volume,
            'volume_ratio': round(volume_ratio, 2)
        }
    except Exception:
        return None


def get_realtime_data(stock_code):
    """獲取即時股價數據（P0修復：支援無 yfinance 環境）"""
    import warnings
    import os

    # 抑制所有警告
    warnings.filterwarnings('ignore')

    # 抑制 yfinance 的錯誤輸出（重定向 stderr）
    original_stderr = sys.stderr
    sys.stderr = open(os.devnull, 'w')

    # 優先使用 yfinance（如果可用）
    if HAS_YFINANCE:
        try:
            ticker = yf.Ticker(f"{stock_code}.TW")
            hist = ticker.history(period='5d')

            if hist.empty or len(hist) < 2:
                return get_realtime_data_api(stock_code)  # 降級到 API

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            current_volume = hist['Volume'].iloc[-1]

            # 計算指標
            change_pct = ((current_price - prev_close) / prev_close) * 100
            avg_volume_5d = hist['Volume'].iloc[:-1].mean()
            volume_ratio = current_volume / avg_volume_5d if avg_volume_5d > 0 else 0

            # 獲取股票名稱
            info = ticker.info
            stock_name = info.get('longName', stock_code)
            if not stock_name or stock_name == stock_code:
                stock_name = info.get('shortName', stock_code)

            result = {
                'code': stock_code,
                'name': stock_name,
                'current_price': round(current_price, 2),
                'prev_close': round(prev_close, 2),
                'change_pct': round(change_pct, 2),
                'volume': current_volume,
                'volume_ratio': round(volume_ratio, 2)
            }
            # 恢復 stderr
            sys.stderr.close()
            sys.stderr = original_stderr
            return result
        except Exception:
            # 恢復 stderr
            sys.stderr.close()
            sys.stderr = original_stderr
            return get_realtime_data_api(stock_code)  # 降級到 API
    else:
        # 恢復 stderr
        sys.stderr.close()
        sys.stderr = original_stderr
        # 無 yfinance，直接使用 API
        return get_realtime_data_api(stock_code)

def parse_recommend_price(price_str):
    """解析推薦價格，支援範圍格式如 '18.0-18.3' 或單一數值"""
    if price_str is None:
        return None

    # 如果已經是數字，直接返回
    if isinstance(price_str, (int, float)):
        return float(price_str)

    price_str = str(price_str).strip()

    # 處理「觀察開盤」等非數值情況
    if not any(c.isdigit() for c in price_str):
        return None

    # 處理範圍格式 "18.0-18.3"
    if '-' in price_str:
        parts = price_str.split('-')
        try:
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            return (low + high) / 2  # 返回中間價
        except (ValueError, IndexError):
            pass

    # 嘗試直接轉換
    try:
        return float(price_str)
    except ValueError:
        return None

def analyze_tracking_stocks(tracking):
    """Track A: 分析盤前推薦股表現"""
    results = []
    recommendations = tracking.get('recommendations', [])

    print(f"追蹤 {len(recommendations)} 檔推薦股...")

    for rec in recommendations:
        stock_code = rec['stock_code']
        stock_name = rec['stock_name']
        recommend_price_raw = rec.get('recommend_price')
        recommend_price = parse_recommend_price(recommend_price_raw)

        data = get_realtime_data(stock_code)
        if not data:
            continue

        # 計算相對推薦價的表現（若無有效推薦價則跳過比較）
        if recommend_price and recommend_price > 0:
            price_vs_recommend = ((data['current_price'] - recommend_price) / recommend_price) * 100
        else:
            price_vs_recommend = 0
            recommend_price = data['prev_close']  # 用昨收作為參考

        # 給出操作建議而非判斷
        if data['change_pct'] < -5:
            action = "⚠️ 大跌，檢查停損位"
            priority = 1
        elif data['change_pct'] < -2:
            action = "✅ 回檔，可考慮加碼"
            priority = 2
        elif data['change_pct'] < 0:
            action = "📍 小跌，正常波動"
            priority = 3
        elif data['change_pct'] < 3:
            action = "✅ 上漲，續抱觀察"
            priority = 4
        else:
            action = "📈 大漲，可部分獲利"
            priority = 5

        results.append({
            'code': stock_code,
            'name': stock_name,
            'recommend_price': recommend_price,
            'current_price': data['current_price'],
            'change_pct': data['change_pct'],
            'price_vs_recommend': round(price_vs_recommend, 2),
            'volume_ratio': data['volume_ratio'],
            'action': action,
            'priority': priority
        })

    return sorted(results, key=lambda x: x['priority'])

def scan_market_opportunities():
    """Track B: 全市場掃描"""
    print(f"掃描 {len(MARKET_UNIVERSE)} 檔股票...")

    results = {
        'gainers': [],      # 漲幅榜
        'losers': [],       # 跌幅榜
        'volume_burst': [], # 爆量股
        'suspicious': []    # 疑似佈局
    }

    # 使用多線程加速
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_realtime_data, code): code
                  for code in MARKET_UNIVERSE}

        for future in as_completed(futures):
            data = future.result()
            if not data:
                continue

            # 分類
            if data['change_pct'] > 2:
                results['gainers'].append(data)
            elif data['change_pct'] < -2:
                results['losers'].append(data)

            if data['volume_ratio'] > 2:
                results['volume_burst'].append(data)

            # 疑似佈局：小漲(0-2%) + 放量(>1.5x)
            if 0 < data['change_pct'] < 2 and data['volume_ratio'] > 1.5:
                results['suspicious'].append(data)

    # 排序
    results['gainers'] = sorted(results['gainers'],
                                key=lambda x: x['change_pct'], reverse=True)[:10]
    results['losers'] = sorted(results['losers'],
                               key=lambda x: x['change_pct'])[:10]
    results['volume_burst'] = sorted(results['volume_burst'],
                                     key=lambda x: x['volume_ratio'], reverse=True)[:10]
    results['suspicious'] = sorted(results['suspicious'],
                                   key=lambda x: x['volume_ratio'], reverse=True)[:10]

    return results

def check_if_recommended(stock_code, tracking):
    """檢查是否為盤前推薦股"""
    if not tracking:
        return False

    recommendations = tracking.get('recommendations', [])
    recommended_codes = [r['stock_code'] for r in recommendations]
    return stock_code in recommended_codes

def output_dual_track_analysis(tracking_results, market_scan, tracking):
    """整合輸出雙軌分析結果"""

    print("\n" + "=" * 80)
    print("📊 盤中雙軌分析結果")
    print("=" * 80)

    # Track A: 推薦股追蹤
    print("\n📍 Track A: 盤前推薦股追蹤")
    print("-" * 40)

    if tracking_results:
        for stock in tracking_results:
            print(f"{stock['name']}({stock['code']}): ")
            print(f"  推薦價: {stock['recommend_price']}元 → 現價: {stock['current_price']}元")
            print(f"  今日漲跌: {stock['change_pct']:+.2f}% | 量比: {stock['volume_ratio']}x")
            print(f"  操作建議: {stock['action']}")
            print()
    else:
        print("無推薦股追蹤資料\n")

    # Track B: 全市場掃描
    print("\n🌐 Track B: 全市場即時掃描")
    print("-" * 40)

    # 漲幅榜
    print("\n📈 漲幅TOP5")
    for i, stock in enumerate(market_scan['gainers'][:5], 1):
        is_rec = check_if_recommended(stock['code'], tracking)
        mark = " [盤前推薦]" if is_rec else " [盤中發現]"
        print(f"{i}. {stock['name']}({stock['code']}): "
              f"{stock['change_pct']:+.2f}% "
              f"量比{stock['volume_ratio']}x{mark}")

    # 跌幅榜
    print("\n📉 跌幅TOP5（可能是機會）")
    for i, stock in enumerate(market_scan['losers'][:5], 1):
        is_rec = check_if_recommended(stock['code'], tracking)
        mark = " [盤前推薦]" if is_rec else " [盤中發現]"
        action = "⚠️ 推薦股大跌" if is_rec else "🔍 研究超跌"
        print(f"{i}. {stock['name']}({stock['code']}): "
              f"{stock['change_pct']:.2f}% {action}{mark}")

    # 爆量股
    print("\n💥 爆量股TOP5")
    for i, stock in enumerate(market_scan['volume_burst'][:5], 1):
        is_rec = check_if_recommended(stock['code'], tracking)
        mark = " [盤前推薦]" if is_rec else " [盤中發現]"
        print(f"{i}. {stock['name']}({stock['code']}): "
              f"{stock['change_pct']:+.2f}% "
              f"量比{stock['volume_ratio']}x{mark}")

    # 疑似佈局
    print("\n🎯 疑似法人佈局（小漲+放量）")
    for i, stock in enumerate(market_scan['suspicious'][:5], 1):
        is_rec = check_if_recommended(stock['code'], tracking)
        if not is_rec:  # 只顯示非推薦股，避免重複
            print(f"{i}. {stock['name']}({stock['code']}): "
                  f"+{stock['change_pct']:.2f}% "
                  f"量比{stock['volume_ratio']}x [新發現]")

def generate_trading_suggestions(tracking_results, market_scan, tracking):
    """生成尾盤操作建議"""

    print("\n" + "=" * 80)
    print("🎯 尾盤操作建議（13:00-13:30）")
    print("=" * 80)

    suggestions = {
        'add': [],      # 可加碼
        'hold': [],     # 續抱
        'profit': [],   # 獲利了結
        'stop': [],     # 停損
        'new': []       # 新機會
    }

    # 分析推薦股
    if tracking_results:
        for stock in tracking_results:
            if stock['change_pct'] < -5:
                suggestions['stop'].append(
                    f"{stock['name']}({stock['code']}) 跌{abs(stock['change_pct']):.1f}% → 執行停損"
                )
            elif stock['change_pct'] < -2:
                suggestions['add'].append(
                    f"{stock['name']}({stock['code']}) 回檔{abs(stock['change_pct']):.1f}% → 可加碼"
                )
            elif stock['change_pct'] > 5:
                suggestions['profit'].append(
                    f"{stock['name']}({stock['code']}) 漲{stock['change_pct']:.1f}% → 部分獲利"
                )
            else:
                suggestions['hold'].append(
                    f"{stock['name']}({stock['code']}) → 續抱觀察"
                )

    # 分析新機會（從爆量股和疑似佈局中選）
    for stock in market_scan['suspicious'][:3]:
        if not check_if_recommended(stock['code'], tracking):
            suggestions['new'].append(
                f"{stock['name']}({stock['code']}) 量比{stock['volume_ratio']}x → 疑似佈局"
            )

    # 輸出建議
    if suggestions['stop']:
        print("\n🛑 停損執行：")
        for s in suggestions['stop']:
            print(f"  • {s}")

    if suggestions['add']:
        print("\n➕ 可加碼：")
        for s in suggestions['add']:
            print(f"  • {s}")

    if suggestions['profit']:
        print("\n💰 部分獲利：")
        for s in suggestions['profit']:
            print(f"  • {s}")

    if suggestions['hold']:
        print("\n📌 續抱觀察：")
        for s in suggestions['hold'][:3]:  # 只顯示前3個
            print(f"  • {s}")
        if len(suggestions['hold']) > 3:
            print(f"  • ...還有{len(suggestions['hold'])-3}檔續抱")

    if suggestions['new']:
        print("\n🔍 盤中新發現（觀察，非推薦）：")
        for s in suggestions['new']:
            print(f"  • {s}")

def save_analysis_report(tracking_results, market_scan, date_str):
    """
    儲存分析報告

    P0修復：使用跨平台路徑和檔案寫入
    """

    # 轉換numpy類型為Python原生類型
    def convert_numpy(obj):
        if hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(item) for item in obj]
        return obj

    # P0-2: 使用跨平台時區
    if USE_CROSS_PLATFORM:
        timestamp = get_tw_now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    report = {
        'timestamp': timestamp,
        'tracking_results': convert_numpy(tracking_results) if tracking_results else [],
        'market_scan': {
            'gainers': convert_numpy(market_scan['gainers'][:10]),
            'losers': convert_numpy(market_scan['losers'][:10]),
            'volume_burst': convert_numpy(market_scan['volume_burst'][:10]),
            'suspicious': convert_numpy(market_scan['suspicious'][:10])
        }
    }

    # P0-1: 使用跨平台路徑
    if USE_CROSS_PLATFORM:
        output_dir = get_analysis_dir(date_str)
        ensure_dir(output_dir)
        output_file = output_dir / 'dual_track_analysis.json'
        success = write_json(output_file, report)
        if not success:
            print("⚠️ 儲存報告失敗")
            print("分析結果已顯示完畢")
    else:
        output_dir = f'data/{date_str}'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = f'{output_dir}/dual_track_analysis.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 儲存報告失敗: {e}")
            print("分析結果已顯示完畢")

    print(f"\n💾 分析報告已儲存至: {output_file}")

def main():
    """主程式"""
    print("=" * 80)
    print("🚀 盤中雙軌分析系統")
    print("=" * 80)

    # P0-2: 使用跨平台時區
    if USE_CROSS_PLATFORM:
        now = get_tw_now()
        date_str = get_tw_today()
    else:
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M:%S')

    print(f"📅 日期: {date_str}")
    print(f"🕐 時間: {current_time}")
    print()

    # Track A: 讀取tracking檔案
    tracking = read_tracking_file(date_str)
    tracking_results = None

    if tracking:
        print("=" * 80)
        print("執行 Track A: 盤前推薦股追蹤...")
        print("=" * 80)
        tracking_results = analyze_tracking_stocks(tracking)
        print(f"✅ Track A 完成，追蹤 {len(tracking_results)} 檔股票")

    # Track B: 全市場掃描
    print("\n" + "=" * 80)
    print("執行 Track B: 全市場掃描...")
    print("=" * 80)
    market_scan = scan_market_opportunities()
    print(f"✅ Track B 完成，掃描 {len(MARKET_UNIVERSE)} 檔股票")

    # 整合輸出
    output_dual_track_analysis(tracking_results, market_scan, tracking)

    # 生成操作建議
    generate_trading_suggestions(tracking_results, market_scan, tracking)

    # 儲存報告
    save_analysis_report(tracking_results, market_scan, date_str)

    print("\n" + "=" * 80)
    print("📊 盤中雙軌分析完成！")
    print("=" * 80)

    # 風險提醒
    print("\n⚠️ 重要提醒：")
    print("1. 數據可能有15-20分鐘延遲")
    print("2. 盤中新發現僅供參考，非投資建議")
    print("3. 請以券商軟體實際價格為準")
    print("4. 投資有風險，決策需謹慎")

if __name__ == '__main__':
    main()