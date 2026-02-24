#!/usr/bin/env python3
"""
市場狀態判斷器

根據台股/美股休市日行事曆，判斷今天應該執行什麼動作。

輸出（stdout）：
  full     — 台股開市，執行完整盤前分析
  snapshot — 台股休市，但上次台股交易日後美股有新交易日，執行假日快照
  skip     — 台股休市且美股也沒有新交易日，跳過

用法：
  python scripts/check_market_status.py              # 用今天日期
  python scripts/check_market_status.py --date 2026-02-16
  python scripts/check_market_status.py --mode intraday   # 盤中/盤後只需判斷台股開市
"""

import sys
import io
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
HOLIDAYS_FILE = PROJECT_DIR / "data" / "holidays.json"


def load_holidays():
    """讀取台股+美股休市日"""
    tw_holidays = set()
    us_holidays = set()

    if not HOLIDAYS_FILE.exists():
        print(f"[WARN] {HOLIDAYS_FILE} 不存在，僅用週末判斷", file=sys.stderr)
        return tw_holidays, us_holidays

    with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 台股假日
    for year_dates in data.get("holidays", {}).values():
        for h in year_dates:
            tw_holidays.add(h["date"])

    # 美股假日
    for year_dates in data.get("us_holidays", {}).values():
        for h in year_dates:
            us_holidays.add(h["date"])

    return tw_holidays, us_holidays


def is_trading_day(date_str, holidays):
    """判斷某日是否為交易日（非週末 且 不在假日清單中）"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if dt.weekday() >= 5:  # 週六=5, 週日=6
        return False
    return date_str not in holidays


def find_previous_tw_trading_day(date_str, tw_holidays):
    """往前找上一個台股交易日"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    for i in range(1, 30):
        prev = dt - timedelta(days=i)
        prev_str = prev.strftime("%Y-%m-%d")
        if is_trading_day(prev_str, tw_holidays):
            return prev_str
    return None


def has_us_trading_days_since(last_tw_day, target_date, us_holidays):
    """
    檢查 last_tw_day (含) 到 target_date (不含) 之間，
    美股是否有至少一個交易日。

    含 last_tw_day 的原因：
    台股盤前 08:30 只捕捉前一天的美股收盤。
    所以 last_tw_day 當天的美股收盤（05:00 隔日台灣時間）
    不會被 last_tw_day 的盤前分析捕捉，需要快照。
    """
    start = datetime.strptime(last_tw_day, "%Y-%m-%d")
    end = datetime.strptime(target_date, "%Y-%m-%d")

    dt = start
    while dt < end:
        date_str = dt.strftime("%Y-%m-%d")
        if is_trading_day(date_str, us_holidays):
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
    tw_holidays, us_holidays = load_holidays()

    tw_open = is_trading_day(date_str, tw_holidays)

    if tw_open:
        return "full"

    # 台股休市
    if mode in ("intraday", "after_market"):
        return "skip"

    # 盤前模式：檢查美股是否有新交易日
    last_tw_day = find_previous_tw_trading_day(date_str, tw_holidays)
    if not last_tw_day:
        return "skip"

    if has_us_trading_days_since(last_tw_day, date_str, us_holidays):
        return "snapshot"

    return "skip"


def main():
    parser = argparse.ArgumentParser(description="市場狀態判斷器")
    parser.add_argument("--date", default=None, help="目標日期 (YYYY-MM-DD)，預設今天")
    parser.add_argument("--mode", default="before_market",
                        choices=["before_market", "intraday", "after_market"],
                        help="分析模式（預設 before_market）")
    parser.add_argument("--verbose", action="store_true", help="輸出詳細資訊到 stderr")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    tw_holidays, us_holidays = load_holidays()
    tw_open = is_trading_day(date_str, tw_holidays)

    result = check_market_status(date_str, args.mode)

    if args.verbose:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        print(f"日期: {date_str} ({weekday_names[dt.weekday()]})", file=sys.stderr)
        print(f"模式: {args.mode}", file=sys.stderr)
        print(f"台股: {'開市' if tw_open else '休市'}", file=sys.stderr)

        if not tw_open and args.mode == "before_market":
            last_tw = find_previous_tw_trading_day(date_str, tw_holidays)
            has_us = has_us_trading_days_since(last_tw, date_str, us_holidays) if last_tw else False
            print(f"上一台股交易日: {last_tw}", file=sys.stderr)
            print(f"期間美股有交易: {'是' if has_us else '否'}", file=sys.stderr)

        print(f"結果: {result}", file=sys.stderr)

    # stdout 只輸出結果，供 PS1 讀取
    print(result)


if __name__ == "__main__":
    main()
