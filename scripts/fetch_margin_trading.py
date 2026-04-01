#!/usr/bin/env python3
"""
融資融券數據抓取 + 快取

來源：TWSE 官方 API (MI_MARGN)
快取：data/cache/twse_margin_YYYYMMDD.json

欄位說明（Table 1 的 fields）：
  [0] 代號  [1] 名稱
  融資：[2] 買進  [3] 賣出  [4] 現金償還  [5] 前日餘額  [6] 今日餘額  [7] 限額
  融券：[8] 買進  [9] 賣出  [10] 現券償還  [11] 前日餘額  [12] 今日餘額  [13] 限額
  [14] 資券互抵  [15] 註記
"""

import sys
import io
import json
import time
import requests
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"

_memory_cache = {}


def _cache_path(date_str):
    return CACHE_DIR / f"twse_margin_{date_str}.json"


def _parse_int(s):
    """解析逗號分隔的數字字串"""
    try:
        return int(s.replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0


def fetch_margin_data(date_str):
    """
    取得某一天全市場融資融券數據（含快取）

    Args:
        date_str: YYYYMMDD 格式日期

    Returns:
        dict: {stock_code: {margin_buy, margin_sell, margin_balance, margin_prev,
                            short_buy, short_sell, short_balance, short_prev,
                            offset}}
        空 dict 表示該日無資料
    """
    if date_str in _memory_cache:
        return _memory_cache[date_str]

    cache_file = _cache_path(date_str)
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _memory_cache[date_str] = data
            return data
        except (json.JSONDecodeError, IOError):
            pass

    url = f'https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date={date_str}&selectType=ALL&response=json'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        raw = resp.json()
    except Exception:
        return {}

    if raw.get('stat') != 'OK' or 'tables' not in raw:
        return {}

    # Table 1 = 個股融資融券明細
    tables = raw['tables']
    if len(tables) < 2:
        return {}

    table = tables[1]
    rows = table.get('data', [])

    result = {}
    for row in rows:
        if len(row) < 15:
            continue
        code = row[0].strip()
        if not code or code.startswith('00') or not code[0].isdigit():
            continue
        if len(code) != 4:
            continue

        try:
            result[code] = {
                'name': row[1].strip(),
                'margin_buy': _parse_int(row[2]),
                'margin_sell': _parse_int(row[3]),
                'margin_cash_repay': _parse_int(row[4]),
                'margin_prev': _parse_int(row[5]),
                'margin_balance': _parse_int(row[6]),
                'short_buy': _parse_int(row[8]),
                'short_sell': _parse_int(row[9]),
                'short_cash_repay': _parse_int(row[10]),
                'short_prev': _parse_int(row[11]),
                'short_balance': _parse_int(row[12]),
                'offset': _parse_int(row[14]),
            }
        except (ValueError, IndexError):
            continue

    if len(result) >= 500:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        except IOError:
            pass
        _memory_cache[date_str] = result

    return result


def fetch_margin_range(start_date, end_date):
    """批次抓取日期範圍內的融資融券（自動跳過假日）"""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    results = {}
    current = start
    while current <= end:
        if current.weekday() < 5:  # 跳過週末
            date_str = current.strftime("%Y%m%d")
            cache_file = _cache_path(date_str)

            if cache_file.exists():
                data = fetch_margin_data(date_str)
            else:
                print(f"  抓取 {date_str}...", end=" ", flush=True)
                data = fetch_margin_data(date_str)
                if data:
                    print(f"OK ({len(data)} 檔)")
                else:
                    print("無資料（假日）")
                time.sleep(0.5)

            if data:
                results[date_str] = data

        current += timedelta(days=1)

    return results


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        date = sys.argv[1]
        data = fetch_margin_data(date)
        print(f"日期: {date}, 股票數: {len(data)}")
        if data:
            sample = list(data.items())[:3]
            for code, info in sample:
                print(f"  {code} {info['name']}: 融資餘額={info['margin_balance']}, 融券餘額={info['short_balance']}")
    else:
        print("用法: python fetch_margin_trading.py YYYYMMDD")
        print("範例: python fetch_margin_trading.py 20260331")
