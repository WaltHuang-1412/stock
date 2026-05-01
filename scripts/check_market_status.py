#!/usr/bin/env python3
"""
市場狀態判斷器（動態版）

動態查詢 TWSE / Yahoo Finance 判斷台股與美股是否為交易日，
不再依賴靜態 holidays.json。

輸出（stdout）：
  full     — 台股開市，執行完整盤前分析
  snapshot — 台股休市，但上次台股交易日後美股有新交易日，執行假日快照
  skip     — 台股休市且美股也沒有新交易日，跳過

用法：
  python scripts/check_market_status.py              # 用今天日期
  python scripts/check_market_status.py --date 2026-05-01
  python scripts/check_market_status.py --mode intraday
"""

import sys
import io
import json
import argparse
import warnings
import requests
from datetime import datetime, timedelta
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "data" / "cache"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def _is_weekend(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.weekday() >= 5


def is_tw_trading_day(date_str):
    """查詢 TWSE T86 API 判斷台股是否為交易日（有資料=開市）"""
    if _is_weekend(date_str):
        return False

    # 查快取：如果本地已有當天 T86 資料，代表有開市
    date_compact = date_str.replace("-", "")
    cache_file = CACHE_DIR / f"twse_t86_{date_compact}.json"
    if cache_file.exists():
        return True

    # 查 TWSE T86 API
    url = f"https://www.twse.com.tw/rwd/en/fund/T86?date={date_compact}&selectType=ALL&response=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            # 有 data 欄位且非空 = 有交易
            if data.get("data") and len(data["data"]) > 0:
                return True
            # TWSE 回傳但沒資料 = 休市
            return False
    except Exception as e:
        print(f"[WARN] TWSE API 查詢失敗: {e}", file=sys.stderr)

    # API 失敗時：非週末就假設開市（保守策略，避免漏跑）
    print(f"[WARN] 無法確認台股 {date_str} 是否開市，預設為開市", file=sys.stderr)
    return True


def is_us_trading_day(date_str):
    """查詢 Yahoo Finance ^GSPC (S&P 500) 判斷美股是否為交易日"""
    if _is_weekend(date_str):
        return False

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    # Yahoo Finance chart API：查該日前後 3 天範圍，看有沒有該日的 timestamp
    period1 = int((dt - timedelta(days=1)).timestamp())
    period2 = int((dt + timedelta(days=1)).timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
        f"?period1={period1}&period2={period2}&interval=1d"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("chart", {}).get("result")
            if result and result[0].get("timestamp"):
                timestamps = result[0]["timestamp"]
                # 檢查是否有當天的 timestamp
                target_date = dt.date()
                for ts in timestamps:
                    ts_date = datetime.utcfromtimestamp(ts).date()
                    if ts_date == target_date:
                        return True
                return False
    except Exception as e:
        print(f"[WARN] Yahoo Finance API 查詢失敗: {e}", file=sys.stderr)

    # API 失敗時：非週末就假設開市
    print(f"[WARN] 無法確認美股 {date_str} 是否開市，預設為開市", file=sys.stderr)
    return True


def find_previous_tw_trading_day(date_str):
    """往前找上一個台股交易日"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    for i in range(1, 30):
        prev = dt - timedelta(days=i)
        prev_str = prev.strftime("%Y-%m-%d")
        if is_tw_trading_day(prev_str):
            return prev_str
    return None


def has_us_trading_days_since(last_tw_day, target_date):
    """
    檢查 last_tw_day (含) 到 target_date (不含) 之間，
    美股是否有至少一個交易日。
    """
    start = datetime.strptime(last_tw_day, "%Y-%m-%d")
    end = datetime.strptime(target_date, "%Y-%m-%d")

    dt = start
    while dt < end:
        date_str = dt.strftime("%Y-%m-%d")
        if is_us_trading_day(date_str):
            return True
        dt += timedelta(days=1)
    return False


def check_market_status(date_str, mode="before_market"):
    """
    判斷指定日期的市場狀態。

    mode:
      before_market — 盤前：區分 full / snapshot / skip
      intraday      — 盤中：只判斷 full / skip
      after_market   — 盤後：只判斷 full / skip
    """
    tw_open = is_tw_trading_day(date_str)

    if tw_open:
        return "full"

    # 台股休市
    if mode in ("intraday", "after_market"):
        return "skip"

    # 盤前模式：檢查美股是否有新交易日
    last_tw_day = find_previous_tw_trading_day(date_str)
    if not last_tw_day:
        return "skip"

    if has_us_trading_days_since(last_tw_day, date_str):
        return "snapshot"

    return "skip"


def main():
    parser = argparse.ArgumentParser(description="市場狀態判斷器（動態版）")
    parser.add_argument("--date", default=None, help="目標日期 (YYYY-MM-DD)，預設今天")
    parser.add_argument("--mode", default="before_market",
                        choices=["before_market", "intraday", "after_market"],
                        help="分析模式（預設 before_market）")
    parser.add_argument("--verbose", action="store_true", help="輸出詳細資訊到 stderr")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    tw_open = is_tw_trading_day(date_str)
    result = check_market_status(date_str, args.mode)

    if args.verbose:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        print(f"日期: {date_str} ({weekday_names[dt.weekday()]})", file=sys.stderr)
        print(f"模式: {args.mode}", file=sys.stderr)
        print(f"台股: {'開市' if tw_open else '休市'}", file=sys.stderr)

        if not tw_open and args.mode == "before_market":
            last_tw = find_previous_tw_trading_day(date_str)
            has_us = has_us_trading_days_since(last_tw, date_str) if last_tw else False
            print(f"上一台股交易日: {last_tw}", file=sys.stderr)
            print(f"期間美股有交易: {'是' if has_us else '否'}", file=sys.stderr)

        print(f"結果: {result}", file=sys.stderr)

    # stdout 只輸出結果
    print(result)


if __name__ == "__main__":
    main()
