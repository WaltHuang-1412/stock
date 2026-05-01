#!/usr/bin/env python3
"""
Yahoo Finance API 替代方案（不依賴 yfinance）

功能：
- 獲取即時股價
- 獲取5日漲幅
- 獲取歷史數據
- 自動支援上市 (.TW) 和上櫃 (.TWO)

使用方式：
    from yahoo_finance_api import get_current_price, get_5day_change, get_history
"""

import requests
import json
from datetime import datetime, timedelta


HEADERS = {'User-Agent': 'Mozilla/5.0'}


def _fetch_chart(code, interval='1d', range_str='1d'):
    """
    底層查詢：自動嘗試 .TW（上市）和 .TWO（上櫃）

    Returns:
        dict: Yahoo Finance chart result，失敗返回 None
    """
    for suffix in ['.TW', '.TWO']:
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}{suffix}?interval={interval}&range={range_str}'
            response = requests.get(url, headers=HEADERS, timeout=10)
            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                # 確認有實際資料（不是空殼）
                if 'meta' in result and result['meta'].get('regularMarketPrice') is not None:
                    return result
        except Exception:
            pass

    return None


def get_current_price(code):
    """
    獲取即時股價

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 現價，失敗返回 None
    """
    result = _fetch_chart(code, range_str='1d')
    if result:
        return result['meta'].get('regularMarketPrice')
    return None


def get_previous_close(code):
    """
    獲取昨收價

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 昨收價，失敗返回 None
    """
    result = _fetch_chart(code, range_str='2d')
    if not result:
        return None

    # 方法1: 從meta獲取
    prev = result.get('meta', {}).get('previousClose')
    if prev is not None:
        return prev

    # 方法2: 從歷史收盤價獲取
    try:
        quote = result['indicators']['quote'][0]
        closes = [c for c in quote['close'] if c is not None]
        if len(closes) >= 2:
            return closes[-2]
    except (KeyError, IndexError):
        pass

    return None


def get_5day_change(code):
    """
    取得 5 日漲幅

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 5日漲幅百分比，失敗返回 None
    """
    result = _fetch_chart(code, range_str='5d')
    if not result:
        return None

    try:
        quote = result['indicators']['quote'][0]
        closes = [c for c in quote['close'] if c is not None]
        if len(closes) >= 2:
            first = closes[0]
            last = closes[-1]
            return (last - first) / first * 100
    except (KeyError, IndexError):
        pass

    return None


def get_history(code, period='5d', interval='1d'):
    """
    獲取歷史數據

    Args:
        code: 股票代號（如 '2330'）
        period: 時間範圍 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        interval: 時間間隔 ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1d', '5d', '1wk', '1mo', '3mo')

    Returns:
        dict: {timestamps, opens, highs, lows, closes, volumes}
        失敗返回 None
    """
    result = _fetch_chart(code, interval=interval, range_str=period)
    if not result:
        return None

    history = {}
    if 'timestamp' in result:
        history['timestamps'] = result['timestamp']

    try:
        quote = result['indicators']['quote'][0]
        history['opens'] = quote.get('open', [])
        history['highs'] = quote.get('high', [])
        history['lows'] = quote.get('low', [])
        history['closes'] = quote.get('close', [])
        history['volumes'] = quote.get('volume', [])
    except (KeyError, IndexError):
        pass

    return history


def get_volume_ratio(code):
    """
    計算量比（今日量 vs 5日均量）

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        float: 量比，失敗返回 None
    """
    result = _fetch_chart(code, range_str='6d')
    if not result:
        return None

    try:
        quote = result['indicators']['quote'][0]
        volumes = [v for v in quote['volume'] if v is not None]
        if len(volumes) >= 2:
            today_volume = volumes[-1]
            avg_5day_volume = sum(volumes[:-1]) / len(volumes[:-1])
            if avg_5day_volume > 0:
                return today_volume / avg_5day_volume
    except (KeyError, IndexError):
        pass

    return None


def get_stock_info(code):
    """
    獲取完整股票資訊（一次API調用）

    Args:
        code: 股票代號（如 '2330'）

    Returns:
        dict: {current_price, prev_close, change_pct, volume, avg_5day_volume, volume_ratio}
        失敗返回 None
    """
    result = _fetch_chart(code, range_str='6d')
    if not result:
        return None

    info = {}

    # 現價和昨收
    meta = result.get('meta', {})
    info['current_price'] = meta.get('regularMarketPrice')
    info['prev_close'] = meta.get('previousClose')

    if info['current_price'] and info['prev_close']:
        info['change_pct'] = (info['current_price'] - info['prev_close']) / info['prev_close'] * 100

    # 成交量數據
    try:
        quote = result['indicators']['quote'][0]
        volumes = [v for v in quote['volume'] if v is not None]
        if len(volumes) >= 2:
            info['volume'] = volumes[-1]
            info['avg_5day_volume'] = int(sum(volumes[:-1]) / len(volumes[:-1]))
            if info['avg_5day_volume'] > 0:
                info['volume_ratio'] = volumes[-1] / info['avg_5day_volume']
    except (KeyError, IndexError):
        pass

    return info


# 測試函數
if __name__ == '__main__':
    print("=" * 60)
    print("Yahoo Finance API 測試")
    print("=" * 60)

    # 測試上市股
    for test_code, label in [('2330', '台積電(上市)'), ('6488', '環球晶(上櫃)')]:
        print(f"\n測試：{test_code} {label}")
        print("-" * 60)

        price = get_current_price(test_code)
        print(f"  現價：{price}")

        prev = get_previous_close(test_code)
        print(f"  昨收：{prev}")

        change = get_5day_change(test_code)
        if change is not None:
            print(f"  5日漲幅：{change:+.2f}%")

        ratio = get_volume_ratio(test_code)
        if ratio is not None:
            print(f"  量比：{ratio:.2f}x")

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
