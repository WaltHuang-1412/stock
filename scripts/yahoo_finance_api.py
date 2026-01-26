#!/usr/bin/env python3
"""
Yahoo Finance API 替代方案（不依賴 yfinance）

功能：
- 獲取即時股價
- 獲取5日漲幅
- 獲取歷史數據
- 適用於 Python 3.15+

使用方式：
    from yahoo_finance_api import get_current_price, get_5day_change, get_history
"""

import requests
import json
from datetime import datetime, timedelta


def get_current_price(code):
    """
    獲取即時股價

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 現價，失敗返回 None
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=1d'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            if 'meta' in result and 'regularMarketPrice' in result['meta']:
                return result['meta']['regularMarketPrice']
    except Exception as e:
        print(f"❌ 查詢 {code} 現價失敗: {e}")

    return None


def get_previous_close(code):
    """
    獲取昨收價

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 昨收價，失敗返回 None
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=2d'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]

            # 方法1: 從meta獲取
            if 'meta' in result and 'previousClose' in result['meta']:
                prev = result['meta']['previousClose']
                if prev is not None:
                    return prev

            # 方法2: 從歷史收盤價獲取
            if 'indicators' in result and 'quote' in result['indicators']:
                quote = result['indicators']['quote'][0]
                if 'close' in quote:
                    closes = [c for c in quote['close'] if c is not None]
                    if len(closes) >= 2:
                        return closes[-2]  # 倒數第二天的收盤價
    except Exception as e:
        print(f"❌ 查詢 {code} 昨收價失敗: {e}")

    return None


def get_5day_change(code):
    """
    取得 5 日漲幅

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 5日漲幅百分比，失敗返回 None
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=5d'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]

            # 獲取收盤價數據
            if 'indicators' in result and 'quote' in result['indicators']:
                quote = result['indicators']['quote'][0]
                if 'close' in quote:
                    closes = [c for c in quote['close'] if c is not None]

                    if len(closes) >= 2:
                        first = closes[0]
                        last = closes[-1]
                        pct = (last - first) / first * 100
                        return pct
    except Exception as e:
        print(f"❌ 查詢 {code} 5日漲幅失敗: {e}")

    return None


def get_history(code, period='5d', interval='1d'):
    """
    獲取歷史數據

    Args:
        code: 股票代號（如 '2330'）
        period: 時間範圍 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        interval: 時間間隔 ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1d', '5d', '1wk', '1mo', '3mo')

    Returns:
        dict: {
            'timestamps': [...],
            'opens': [...],
            'highs': [...],
            'lows': [...],
            'closes': [...],
            'volumes': [...]
        }
        失敗返回 None
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval={interval}&range={period}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]

            history = {}

            # 時間戳
            if 'timestamp' in result:
                history['timestamps'] = result['timestamp']

            # OHLCV數據
            if 'indicators' in result and 'quote' in result['indicators']:
                quote = result['indicators']['quote'][0]
                history['opens'] = quote.get('open', [])
                history['highs'] = quote.get('high', [])
                history['lows'] = quote.get('low', [])
                history['closes'] = quote.get('close', [])
                history['volumes'] = quote.get('volume', [])

            return history
    except Exception as e:
        print(f"❌ 查詢 {code} 歷史數據失敗: {e}")

    return None


def get_volume_ratio(code):
    """
    計算量比（今日量 vs 5日均量）

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 量比，失敗返回 None
    """
    try:
        # 獲取6日數據（今日+過去5日）
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=6d'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]

            if 'indicators' in result and 'quote' in result['indicators']:
                quote = result['indicators']['quote'][0]
                if 'volume' in quote:
                    volumes = [v for v in quote['volume'] if v is not None]

                    if len(volumes) >= 2:
                        today_volume = volumes[-1]
                        avg_5day_volume = sum(volumes[:-1]) / len(volumes[:-1])

                        if avg_5day_volume > 0:
                            ratio = today_volume / avg_5day_volume
                            return ratio
    except Exception as e:
        print(f"❌ 查詢 {code} 量比失敗: {e}")

    return None


def get_stock_info(code):
    """
    獲取完整股票資訊（一次API調用）

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        dict: {
            'current_price': float,
            'prev_close': float,
            'change_pct': float,
            'volume': int,
            'avg_5day_volume': int,
            'volume_ratio': float
        }
        失敗返回 None
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=6d'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]

            info = {}

            # 現價和昨收
            if 'meta' in result:
                info['current_price'] = result['meta'].get('regularMarketPrice')
                info['prev_close'] = result['meta'].get('previousClose')

                if info['current_price'] and info['prev_close']:
                    info['change_pct'] = (info['current_price'] - info['prev_close']) / info['prev_close'] * 100

            # 成交量數據
            if 'indicators' in result and 'quote' in result['indicators']:
                quote = result['indicators']['quote'][0]
                if 'volume' in quote:
                    volumes = [v for v in quote['volume'] if v is not None]

                    if len(volumes) >= 2:
                        info['volume'] = volumes[-1]
                        info['avg_5day_volume'] = int(sum(volumes[:-1]) / len(volumes[:-1]))

                        if info['avg_5day_volume'] > 0:
                            info['volume_ratio'] = volumes[-1] / info['avg_5day_volume']

            return info
    except Exception as e:
        print(f"❌ 查詢 {code} 完整資訊失敗: {e}")

    return None


# 測試函數
if __name__ == '__main__':
    print("=" * 60)
    print("Yahoo Finance API 測試")
    print("=" * 60)

    test_code = '2330'  # 台積電

    print(f"\n測試股票：{test_code}")
    print("-" * 60)

    # 測試現價
    price = get_current_price(test_code)
    print(f"現價：{price}")

    # 測試昨收
    prev = get_previous_close(test_code)
    print(f"昨收：{prev}")

    # 測試5日漲幅
    change = get_5day_change(test_code)
    if change is not None:
        print(f"5日漲幅：{change:+.2f}%")

    # 測試量比
    ratio = get_volume_ratio(test_code)
    if ratio is not None:
        print(f"量比：{ratio:.2f}x")

    # 測試完整資訊
    print("\n完整資訊：")
    info = get_stock_info(test_code)
    if info:
        for key, value in info.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
