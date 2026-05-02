#!/usr/bin/env python3
"""
出場訊號檢查工具 - Exit Signal Checker

功能：
- 檢查股票是否觸發出場訊號
- 綜合法人數據 + 技術面 + 價格規則

使用方式：
    python3 scripts/exit_signal_checker.py 2356              # 單檔
    python3 scripts/exit_signal_checker.py 2356 2382 3711   # 多檔
    python3 scripts/exit_signal_checker.py 2356 --cost 50   # 指定成本價

最後更新：2026-01-22
"""

import requests
import sys
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 添加 scripts 目錄到路徑
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils import get_tw_now
    USE_CROSS_PLATFORM = True
except ImportError:
    USE_CROSS_PLATFORM = False

try:
    from twse_institutional_cache import get_institutional_data as cached_get_institutional
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False

from yahoo_finance_api import get_history


def get_stock_data(stock_code, days=20):
    """從 Yahoo Finance 獲取股價數據（自動支援上市/上櫃）"""
    hist = get_history(stock_code, period=f'{days}d', interval='1d')
    if not hist or not hist.get('timestamps'):
        return None

    prices = []
    timestamps = hist['timestamps']
    closes = hist.get('closes', [])
    opens = hist.get('opens', [])
    highs = hist.get('highs', [])
    lows = hist.get('lows', [])
    volumes = hist.get('volumes', [])

    for i, ts in enumerate(timestamps):
        if i < len(closes) and closes[i] is not None:
            prices.append({
                'date': datetime.fromtimestamp(ts).strftime('%Y-%m-%d'),
                'open': opens[i] if i < len(opens) else None,
                'high': highs[i] if i < len(highs) else None,
                'low': lows[i] if i < len(lows) else None,
                'close': closes[i],
                'volume': volumes[i] if i < len(volumes) else None,
            })

    return prices if prices else None


def get_institutional_data(stock_code, days=5):
    """獲取近N天法人數據（優先使用 twse_institutional_cache）"""
    if USE_CROSS_PLATFORM:
        current = get_tw_now()
    else:
        current = datetime.now()

    history = []
    attempts = 0
    max_attempts = days + 10  # 多嘗試幾天避免假日

    while len(history) < days and attempts < max_attempts:
        if current.weekday() < 5:  # 週一到週五
            date_str = current.strftime('%Y%m%d')

            if HAS_CACHE:
                data = cached_get_institutional(stock_code, date_str)
            else:
                data = _fetch_t86_fallback(stock_code, date_str)

            if data:
                history.append({
                    'date': date_str,
                    'total': data['total'],
                    'foreign': data['foreign'],
                    'trust': data['trust'],
                })

        current -= timedelta(days=1)
        attempts += 1

    return history


def _fetch_t86_fallback(stock_code, date_str):
    """T86 直接查詢（cache 不可用時的 fallback，使用中文版 + 動態欄位對應）"""
    import requests as _req
    import warnings as _w
    _w.filterwarnings('ignore')

    url = f'https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', 'Accept': 'application/json'}
    try:
        raw = _req.get(url, headers=headers, timeout=15, verify=False).json()
        if 'data' not in raw or not raw['data']:
            return None

        fields = raw.get('fields', [])
        field_map = {}
        for i, f in enumerate(fields):
            if '證券代號' in f:
                field_map['code'] = i
            elif '外陸資買賣超股數(不含外資自營商)' in f:
                field_map['foreign'] = i
            elif '投信買賣超股數' in f:
                field_map['trust'] = i
            elif '三大法人買賣超股數' in f:
                field_map['total'] = i

        idx_code = field_map.get('code', 0)
        idx_foreign = field_map.get('foreign', 4)
        idx_trust = field_map.get('trust', 10)
        idx_total = field_map.get('total', 18)

        for row in raw['data']:
            if row[idx_code].strip() == stock_code:
                return {
                    'foreign': int(row[idx_foreign].replace(',', '')) // 1000,
                    'trust': int(row[idx_trust].replace(',', '')) // 1000,
                    'total': int(row[idx_total].replace(',', '')) // 1000,
                }
    except Exception as e:
        print(f"[exit_signal_checker] T86 fallback failed for {stock_code} {date_str}: {e}", file=sys.stderr)
    return None


def calculate_ma(prices, period):
    """計算移動平均線"""
    if len(prices) < period:
        return None
    closes = [p['close'] for p in prices[-period:]]
    return sum(closes) / period


def check_exit_signals(stock_code, cost_price=None):
    """檢查出場訊號"""

    print(f"\n🔍 檢查 {stock_code} 出場訊號...")

    # 獲取數據
    prices = get_stock_data(stock_code, 30)
    if not prices or len(prices) < 5:
        print(f"❌ 無法獲取 {stock_code} 股價數據")
        return None

    institutional = get_institutional_data(stock_code, 5)

    # 當前價格資訊
    current = prices[-1]
    current_price = current['close']
    current_volume = current['volume']
    prev = prices[-2] if len(prices) > 1 else current
    prev_price = prev['close']
    prev_volume = prev['volume']

    # 計算指標
    ma5 = calculate_ma(prices, 5)
    ma10 = calculate_ma(prices, 10)
    ma20 = calculate_ma(prices, 20)

    # 近5日最高價
    recent_high = max(p['high'] for p in prices[-5:])
    # 近10日最高價
    high_10d = max(p['high'] for p in prices[-10:]) if len(prices) >= 10 else recent_high

    # 計算漲跌
    daily_change = (current_price - prev_price) / prev_price * 100
    from_high_5d = (current_price - recent_high) / recent_high * 100
    from_high_10d = (current_price - high_10d) / high_10d * 100

    # 量比
    avg_volume_5d = sum(p['volume'] for p in prices[-6:-1]) / 5 if len(prices) > 5 else prev_volume
    volume_ratio = current_volume / avg_volume_5d if avg_volume_5d > 0 else 1

    # 獲利計算
    profit_pct = None
    if cost_price:
        profit_pct = (current_price - cost_price) / cost_price * 100

    # 法人數據分析
    inst_today = institutional[0] if institutional else None
    inst_yesterday = institutional[1] if len(institutional) > 1 else None

    # 連續買超天數
    consecutive_buy = 0
    for inst in institutional:
        if inst['total'] > 0:
            consecutive_buy += 1
        else:
            break

    # ==================== 出場訊號檢查 ====================

    signals = {
        'triggered': [],
        'warning': [],
        'safe': []
    }

    # 1. 法人反轉（最重要）
    if inst_today and inst_yesterday:
        if inst_yesterday['total'] > 0 and inst_today['total'] < -3000:
            signals['triggered'].append(f"🚨 法人反轉：昨日買{inst_yesterday['total']:+,}→今日賣{inst_today['total']:+,}")
        elif inst_today['total'] < -5000:
            signals['triggered'].append(f"🚨 法人大賣：今日賣超 {inst_today['total']:+,} 張")
        elif inst_today['total'] < 0:
            signals['warning'].append(f"⚠️ 法人賣超：{inst_today['total']:+,} 張（觀察）")
        else:
            signals['safe'].append(f"✅ 法人買超：{inst_today['total']:+,} 張")

    # 2. 投信反轉
    if inst_today and inst_yesterday:
        if inst_yesterday['trust'] > 0 and inst_today['trust'] < -1000:
            signals['warning'].append(f"⚠️ 投信反轉：昨日買{inst_yesterday['trust']:+,}→今日賣{inst_today['trust']:+,}")

    # 3. 跌破 MA5
    if ma5:
        if current_price < ma5:
            signals['triggered'].append(f"🚨 跌破MA5：現價{current_price:.2f} < MA5 {ma5:.2f}")
        else:
            signals['safe'].append(f"✅ 站穩MA5：現價{current_price:.2f} > MA5 {ma5:.2f}")

    # 4. 跌破 MA10
    if ma10:
        if current_price < ma10:
            signals['warning'].append(f"⚠️ 跌破MA10：現價{current_price:.2f} < MA10 {ma10:.2f}")

    # 5. 從高點回落 > 5%
    if from_high_5d < -5:
        signals['triggered'].append(f"🚨 高點回落：從5日高點 {recent_high:.2f} 回落 {from_high_5d:.1f}%")
    elif from_high_5d < -3:
        signals['warning'].append(f"⚠️ 小幅回落：從5日高點回落 {from_high_5d:.1f}%")

    # 6. 爆量長黑K
    is_black_candle = daily_change < -2
    is_high_volume = volume_ratio > 2
    if is_black_candle and is_high_volume:
        signals['triggered'].append(f"🚨 爆量長黑：跌{daily_change:.1f}%，量比{volume_ratio:.1f}x")
    elif is_black_candle:
        signals['warning'].append(f"⚠️ 收黑K：跌{daily_change:.1f}%")

    # 7. 連漲後警戒
    consecutive_green = 0
    for p in reversed(prices[:-1]):
        if prices[prices.index(p)+1]['close'] > p['close']:
            consecutive_green += 1
        else:
            break
    if consecutive_green >= 5:
        signals['warning'].append(f"⚠️ 連漲{consecutive_green}天，注意回調風險")

    # 8. 獲利目標
    if profit_pct is not None:
        if profit_pct >= 20:
            signals['triggered'].append(f"🎯 獲利達標：+{profit_pct:.1f}%（建議分批獲利了結）")
        elif profit_pct >= 15:
            signals['warning'].append(f"💰 獲利{profit_pct:.1f}%（可考慮減碼1/3）")
        elif profit_pct >= 10:
            signals['safe'].append(f"💰 獲利{profit_pct:.1f}%（持續觀察）")
        elif profit_pct > 0:
            signals['safe'].append(f"💰 獲利{profit_pct:.1f}%")
        else:
            signals['warning'].append(f"📉 虧損{profit_pct:.1f}%")

    # 9. 開高走低（漲停隔日風險）
    if current['open'] > prev['close'] * 1.03 and daily_change < 0:
        signals['warning'].append(f"⚠️ 開高走低：開盤漲但收跌{daily_change:.1f}%")

    return {
        'stock_code': stock_code,
        'current_price': current_price,
        'daily_change': daily_change,
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'from_high_5d': from_high_5d,
        'from_high_10d': from_high_10d,
        'volume_ratio': volume_ratio,
        'institutional': inst_today,
        'consecutive_buy': consecutive_buy,
        'profit_pct': profit_pct,
        'signals': signals
    }


def print_report(result):
    """輸出檢查報告"""

    if not result:
        return

    stock_code = result['stock_code']
    signals = result['signals']

    print()
    print("=" * 60)
    print(f"📊 {stock_code} 出場訊號檢查報告")
    print("=" * 60)

    # 基本資訊
    print()
    print("【基本資訊】")
    print("-" * 60)
    print(f"  現價：{result['current_price']:.2f} 元（{result['daily_change']:+.2f}%）")
    if result['ma5']:
        print(f"  MA5：{result['ma5']:.2f}（{'站上' if result['current_price'] > result['ma5'] else '跌破'}）")
    if result['ma10']:
        print(f"  MA10：{result['ma10']:.2f}（{'站上' if result['current_price'] > result['ma10'] else '跌破'}）")
    print(f"  5日高點回落：{result['from_high_5d']:.1f}%")
    print(f"  量比：{result['volume_ratio']:.1f}x")

    if result['institutional']:
        inst = result['institutional']
        print(f"  今日法人：{inst['total']:+,}（外資{inst['foreign']:+,}、投信{inst['trust']:+,}）")
        print(f"  連續買超：{result['consecutive_buy']} 天")

    if result['profit_pct'] is not None:
        print(f"  持股獲利：{result['profit_pct']:+.1f}%")

    # 出場訊號
    print()
    print("【出場訊號檢查】")
    print("-" * 60)

    triggered_count = len(signals['triggered'])
    warning_count = len(signals['warning'])

    if signals['triggered']:
        for s in signals['triggered']:
            print(f"  {s}")

    if signals['warning']:
        for s in signals['warning']:
            print(f"  {s}")

    if signals['safe']:
        for s in signals['safe']:
            print(f"  {s}")

    # 綜合建議
    print()
    print("【綜合建議】")
    print("-" * 60)

    if triggered_count >= 2:
        print("  🔴 強烈建議出場：多個出場訊號觸發")
        print("     → 建議：立即減碼 50-100%")
    elif triggered_count == 1:
        print("  🟠 建議減碼：有出場訊號觸發")
        print("     → 建議：減碼 30-50%，設停損")
    elif warning_count >= 2:
        print("  🟡 提高警覺：多個警告訊號")
        print("     → 建議：密切觀察，準備減碼")
    elif warning_count == 1:
        print("  🟡 留意風險：有警告訊號")
        print("     → 建議：持續觀察，設好停損")
    else:
        print("  🟢 目前安全：無出場訊號")
        print("     → 建議：續抱，持續追蹤法人動向")

    print()
    print("=" * 60)


def main():
    args = sys.argv[1:]

    if not args:
        print("使用方式:")
        print("  python3 scripts/exit_signal_checker.py 2356              # 單檔")
        print("  python3 scripts/exit_signal_checker.py 2356 2382 3711   # 多檔")
        print("  python3 scripts/exit_signal_checker.py 2356 --cost 50   # 指定成本價")
        sys.exit(1)

    # 解析參數
    stock_codes = []
    cost_price = None

    i = 0
    while i < len(args):
        if args[i] == '--cost' and i + 1 < len(args):
            cost_price = float(args[i + 1])
            i += 2
        else:
            stock_codes.append(args[i])
            i += 1

    if not stock_codes:
        print("❌ 請輸入股票代號")
        sys.exit(1)

    print("=" * 60)
    print("📊 出場訊號檢查工具")
    print(f"   檢查股票：{', '.join(stock_codes)}")
    if cost_price:
        print(f"   成本價：{cost_price} 元")
    print("=" * 60)

    for code in stock_codes:
        result = check_exit_signals(code, cost_price)
        if result:
            print_report(result)


if __name__ == '__main__':
    main()
