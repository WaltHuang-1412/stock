#!/usr/bin/env python3
"""
結算判斷器

掃描近期 tracking 中所有 holding 的股票，查詢收盤價，機械式判斷結算結果。

結算規則：
  1. 收盤價 ≥ 目標價 → success
  2. 收盤價 ≤ 停損價 → fail
  3. 持有天數 ≥ settlement_days → 收盤>推薦價=success，≤推薦價=fail
  4. 以上皆無 → holding

用法：
  python scripts/settlement_checker.py                    # 掃描所有 holding
  python scripts/settlement_checker.py --date 2026-05-02  # 指定日期
  python scripts/settlement_checker.py --json              # JSON 輸出
"""

import sys
import io
import json
import argparse
import glob
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"

sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from yahoo_finance_api import get_current_price


def find_all_holdings(date_str):
    """掃描近 15 天的 tracking，找出所有 result='holding' 的股票"""
    holdings = {}  # key=stock_code, value=最早的推薦資訊
    dt = datetime.strptime(date_str, "%Y-%m-%d")

    for i in range(15):
        d = dt - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        tracking_file = TRACKING_DIR / f"tracking_{d_str}.json"

        if not tracking_file.exists():
            continue

        with open(tracking_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 掃描 recommendations
        for rec in data.get("recommendations", []):
            code = rec.get("stock_code")
            result = rec.get("result", "holding")

            if result != "holding" or code in holdings:
                continue

            # 找推薦日期：如果有 recommend_date 就用，否則用 tracking 的 date
            recommend_date = rec.get("recommend_date", d_str)

            holdings[code] = {
                "stock_code": code,
                "stock_name": rec.get("stock_name", ""),
                "industry": rec.get("industry", ""),
                "recommend_date": recommend_date,
                "recommend_price": rec.get("recommend_price"),
                "target_price": rec.get("target_price"),
                "stop_loss": rec.get("stop_loss"),
                "stop_loss_pct": rec.get("stop_loss_pct", -10),
                "settlement_days": rec.get("settlement_days", 10),
                "score": rec.get("score"),
                "position": rec.get("position", ""),
            }

        # 掃描 holdings（盤後 tracking 會把前幾天的放這裡）
        for h in data.get("holdings", []):
            code = h.get("stock_code")
            result = h.get("result", "holding")

            if result != "holding" or code in holdings:
                continue

            recommend_date = h.get("recommend_date", d_str)
            holdings[code] = {
                "stock_code": code,
                "stock_name": h.get("stock_name", ""),
                "industry": h.get("industry", ""),
                "recommend_date": recommend_date,
                "recommend_price": h.get("recommend_price"),
                "target_price": h.get("target_price"),
                "stop_loss": h.get("stop_loss"),
                "stop_loss_pct": h.get("stop_loss_pct", -10),
                "settlement_days": h.get("settlement_days", 10),
                "score": h.get("score"),
                "position": h.get("position", ""),
            }

    return holdings


def count_trading_days(start_date, end_date):
    """計算兩個日期之間的交易日數（簡易版：排除週末）"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    count = 0
    dt = start + timedelta(days=1)
    while dt <= end:
        if dt.weekday() < 5:  # 排除週末
            count += 1
        dt += timedelta(days=1)
    return count


def check_settlement(holdings, date_str):
    """對所有 holding 股票查詢收盤價並判斷結算"""
    results = []

    for code, info in holdings.items():
        close = get_current_price(code)
        if close is None:
            results.append({
                **info,
                "close": None,
                "result": "error",
                "reason": "無法取得收盤價",
            })
            continue

        recommend_price = info["recommend_price"]
        target_price = info["target_price"]

        # 用 stop_loss_pct 重算 stop_loss
        stop_loss_pct = info.get("stop_loss_pct", -10)
        stop_loss = round(recommend_price * (1 + stop_loss_pct / 100), 2)

        settlement_days = info.get("settlement_days", 10)
        holding_days = count_trading_days(info["recommend_date"], date_str)

        change_pct = round((close - recommend_price) / recommend_price * 100, 2)

        entry = {
            **info,
            "stop_loss": stop_loss,
            "close": close,
            "change_pct": change_pct,
            "holding_days": holding_days,
        }

        # 結算判斷
        if close >= target_price:
            entry["result"] = "success"
            entry["reason"] = f"收盤 {close} ≥ 目標 {target_price}"
        elif close <= stop_loss:
            entry["result"] = "fail"
            entry["reason"] = f"收盤 {close} ≤ 停損 {stop_loss}"
        elif holding_days >= settlement_days:
            if close > recommend_price:
                entry["result"] = "success"
                entry["reason"] = f"D{holding_days} 到期，收盤 {close} > 推薦 {recommend_price}"
            else:
                entry["result"] = "fail"
                entry["reason"] = f"D{holding_days} 到期，收盤 {close} ≤ 推薦 {recommend_price}"
        else:
            entry["result"] = "holding"
            dist_target = round((target_price - close) / close * 100, 1)
            dist_stop = round((close - stop_loss) / close * 100, 1)
            entry["reason"] = f"D{holding_days}/{settlement_days} | 距目標 {dist_target}% | 距停損 {dist_stop}%"

        results.append(entry)

    return results


def main():
    parser = argparse.ArgumentParser(description="結算判斷器")
    parser.add_argument("--date", default=None, help="結算日期 (YYYY-MM-DD)，預設今天")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    print(f"📊 結算判斷 — {date_str}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # 找出所有 holding
    holdings = find_all_holdings(date_str)
    if not holdings:
        print("沒有找到任何 holding 中的股票", file=sys.stderr)
        if args.json:
            print(json.dumps({"date": date_str, "results": []}, ensure_ascii=False, indent=2))
        return

    print(f"找到 {len(holdings)} 檔 holding 中", file=sys.stderr)

    # 查詢收盤價 + 判斷結算
    results = check_settlement(holdings, date_str)

    if args.json:
        output = {
            "date": date_str,
            "results": results,
            "summary": {
                "success": sum(1 for r in results if r["result"] == "success"),
                "fail": sum(1 for r in results if r["result"] == "fail"),
                "holding": sum(1 for r in results if r["result"] == "holding"),
                "error": sum(1 for r in results if r["result"] == "error"),
            }
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 表格輸出
        settled = [r for r in results if r["result"] in ("success", "fail")]
        holding = [r for r in results if r["result"] == "holding"]
        errors = [r for r in results if r["result"] == "error"]

        if settled:
            print(f"\n🔔 今日結算 ({len(settled)} 檔):")
            for r in settled:
                icon = "✅" if r["result"] == "success" else "❌"
                print(f"  {icon} {r['stock_code']} {r['stock_name']} | {r['change_pct']:+.1f}% | {r['reason']}")

        if holding:
            print(f"\n📍 持有中 ({len(holding)} 檔):")
            for r in holding:
                print(f"  {r['stock_code']} {r['stock_name']} | 現價 {r['close']} ({r['change_pct']:+.1f}%) | {r['reason']}")

        if errors:
            print(f"\n⚠️ 查詢失敗 ({len(errors)} 檔):")
            for r in errors:
                print(f"  {r['stock_code']} {r['stock_name']} | {r['reason']}")


if __name__ == "__main__":
    main()
