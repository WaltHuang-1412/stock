#!/usr/bin/env python3
"""
TWSE 法人買賣超快取模組

TWSE T86 API 每次回傳全市場 ~900 檔的法人數據，
但 chip_analysis.py 和 reversal_alert.py 各自查同一個 API，
導致同一天的資料被重複下載。

本模組：
1. 查一次 → 快取整天全市場資料到 data/cache/twse_t86_YYYYMMDD.json
2. 後續查詢同一天 → 直接讀快取（0 次 API）
3. 不同股票同一天 → 同一份快取（不需額外呼叫）

效果：30 檔 × 10 天從 600 次 API → 10 次 API（60 倍加速）
"""

import json
import time
import requests
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

CACHE_DIR = Path(__file__).parent.parent / 'data' / 'cache'

# 快取檔案內儲存實際 API 回傳日期的 key（用於讀取時驗證）
METADATA_KEY = '__cache_date__'

# 同一個 process 內的記憶體快取（避免同一天讀檔多次）
_memory_cache = {}


def _cache_path(date_str):
    """快取檔案路徑"""
    return CACHE_DIR / f'twse_t86_{date_str}.json'


def fetch_all_institutional(date_str):
    """
    取得某一天全市場法人買賣超數據（含快取）

    Args:
        date_str: YYYYMMDD 格式日期

    Returns:
        dict: {stock_code: {date, name, foreign, trust, dealer, total}}
        空 dict 表示該日無資料（假日或尚未公布）
    """
    # 1. 記憶體快取
    if date_str in _memory_cache:
        return _memory_cache[date_str]

    # 2. 磁碟快取（含日期驗證）
    cache_file = _cache_path(date_str)
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 驗證快取日期（新格式快取才有此欄位）
            # 若日期不符代表此快取被 TWSE silent fallback 污染，刪除重抓
            cached_date = data.get(METADATA_KEY)
            if cached_date is not None and cached_date != date_str:
                try:
                    cache_file.unlink()
                except OSError:
                    pass
                # 繼續走 API 流程
            else:
                _memory_cache[date_str] = data
                return data
        except (json.JSONDecodeError, IOError):
            pass  # 快取損壞，重新下載

    # 3. 從 TWSE API 下載（中文版，含公司名稱）
    url = f'https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        raw = resp.json()
    except Exception:
        return {}

    if 'data' not in raw or not raw['data']:
        return {}  # 假日或尚未公布，不快取（下次會重試）

    # 驗證 API 回傳日期與請求日期一致（強制）
    # TWSE 在資料未公布時會靜默回傳前一交易日的舊資料，不報錯
    # 若無 date 欄位或日期不符，均視為不可信資料，丟棄不快取
    # 注意：API 回傳格式為 "YYYY/MM/DD"，date_str 格式為 "YYYYMMDD"，需統一後比較
    response_date = raw.get('date', '')
    if not response_date:
        return {}  # TWSE 未回傳日期欄位，無法驗證，拒絕
    response_date_compact = response_date.replace('/', '')
    if response_date_compact != date_str:
        return {}

    # 動態欄位對應（不硬寫索引，用 fields 名稱查找）
    fields = raw.get('fields', [])
    field_map = {}
    for i, f in enumerate(fields):
        if '證券代號' in f:
            field_map['code'] = i
        elif '證券名稱' in f:
            field_map['name'] = i
        elif '外陸資買賣超股數(不含外資自營商)' in f:
            field_map['foreign'] = i
        elif '投信買賣超股數' in f:
            field_map['trust'] = i
        elif f == '自營商買賣超股數':
            field_map['dealer'] = i
        elif '三大法人買賣超股數' in f:
            field_map['total'] = i

    idx_code = field_map.get('code', 0)
    idx_name = field_map.get('name', 1)
    idx_foreign = field_map.get('foreign', 4)
    idx_trust = field_map.get('trust', 10)
    idx_dealer = field_map.get('dealer', 11)
    idx_total = field_map.get('total', 18)

    # 解析全市場資料
    result = {}
    for row in raw['data']:
        code = row[idx_code].strip()
        try:
            def to_int(v):
                if isinstance(v, int):
                    return v
                return int(str(v).replace(',', ''))

            result[code] = {
                'date': date_str,
                'name': row[idx_name].strip() if len(row) > idx_name else code,
                'foreign': to_int(row[idx_foreign]) // 1000,
                'trust': to_int(row[idx_trust]) // 1000,
                'dealer': to_int(row[idx_dealer]) // 1000,
                'total': to_int(row[idx_total]) // 1000,
            }
        except (ValueError, IndexError):
            continue

    # 寫入磁碟快取（資料筆數足夠才存，避免不完整資料污染快取）
    # 正常交易日約 13,000-17,000 檔，低於 10,000 視為不完整
    if len(result) >= 10000:
        # 記錄 API 實際回傳日期，供下次讀取時驗證
        result[METADATA_KEY] = response_date_compact
        # 資料完整，存磁碟快取 + 記憶體快取
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        except IOError:
            pass
        _memory_cache[date_str] = result
    # 不完整的資料不存任何快取，下次查詢會重新打 API

    return result


def get_institutional_data(stock_code, date_str):
    """
    取得單一股票某日法人買賣超（相容舊介面）

    回傳格式與 chip_analysis.py / reversal_alert.py 原本的一致：
    {date, name, foreign, trust, dealer, total}
    或 None（查無資料）
    """
    all_data = fetch_all_institutional(date_str)
    return all_data.get(stock_code)


def clear_memory_cache():
    """清除記憶體快取（測試用）"""
    _memory_cache.clear()
