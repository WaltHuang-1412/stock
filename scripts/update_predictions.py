#!/usr/bin/env python3
"""
Predictions 更新器

讀取今日 tracking.json 的結算結果，自動更新 predictions.json。

功能：
  1. 更新各推薦的 result/settled_date/settled_price/holding_days
  2. 重算頂層統計（settled_accuracy/settled_count/total_success/total_fail/holding_count）
  3. 新增今日推薦到 predictions.json（如果有新推薦）

用法：
  python scripts/update_predictions.py                     # 用今天日期
  python scripts/update_predictions.py --date 2026-05-02   # 指定日期
  python scripts/update_predictions.py --dry-run            # 只顯示不寫入
"""

import sys
import io
import json
import argparse
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"
PREDICTIONS_FILE = PROJECT_DIR / "data" / "predictions" / "predictions.json"


def load_predictions():
    with open(PREDICTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_predictions(data):
    with open(PREDICTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_tracking(date_str):
    tracking_file = TRACKING_DIR / f"tracking_{date_str}.json"
    if not tracking_file.exists():
        return None
    with open(tracking_file, "r", encoding="utf-8") as f:
        return json.load(f)


def update_from_tracking(predictions, tracking, date_str):
    """從 tracking 更新 predictions 中的結算結果"""
    changes = []

    # 收集今日所有結算結果（從 recommendations + removed_stocks）
    settled_stocks = {}

    # 先掃 removed_stocks（可能沒有價格）
    for rec in tracking.get("removed_stocks", []):
        code = rec.get("stock_code")
        result = rec.get("result")
        if result in ("success", "fail"):
            close = rec.get("last_close") or rec.get("settled_price") or rec.get("actual_close")
            settled_stocks[code] = {
                "result": result,
                "close": close,
                "return_pct": rec.get("return_pct"),
                "fail_reason": rec.get("removal_reason"),
            }

    # 再掃 recommendations（有更完整的價格資訊，覆蓋 removed_stocks）
    for rec in tracking.get("recommendations", []):
        code = rec.get("stock_code")
        result = rec.get("result")
        if result in ("success", "fail"):
            close = rec.get("actual_close") or rec.get("close_price") or rec.get("settled_price")
            if close is not None or code not in settled_stocks:
                settled_stocks[code] = {
                    "result": result,
                    "close": close,
                    "return_pct": rec.get("return_pct"),
                    "fail_reason": rec.get("fail_reason"),
                }

    if not settled_stocks:
        print("  今日無新結算", file=sys.stderr)
        return changes

    # 在 predictions 中找到對應的 holding 項目並更新
    for date_key, day_data in predictions.items():
        if not isinstance(day_data, dict) or "predictions" not in day_data:
            continue

        for pred in day_data["predictions"]:
            symbol = pred.get("symbol")
            if symbol not in settled_stocks:
                continue
            if pred.get("result") != "holding":
                continue

            settlement = settled_stocks[symbol]
            old_result = pred["result"]
            pred["result"] = settlement["result"]
            pred["settled_date"] = date_str
            pred["settled_price"] = settlement["close"]
            if settlement.get("fail_reason"):
                pred["fail_reason"] = settlement["fail_reason"]

            changes.append({
                "symbol": symbol,
                "name": pred.get("name", ""),
                "from": old_result,
                "to": settlement["result"],
                "date_key": date_key,
                "settled_price": settlement["close"],
            })

            # 移除已處理的
            del settled_stocks[symbol]

    return changes


def add_new_recommendations(predictions, tracking, date_str):
    """將今日新推薦加入 predictions"""
    if date_str in predictions:
        print(f"  predictions 已有 {date_str} key，跳過新增", file=sys.stderr)
        return []

    new_preds = []
    for rec in tracking.get("recommendations", []):
        # 只加 recommend_date 等於今天的（排除前幾天 carry over 的）
        rec_date = rec.get("recommend_date")
        if rec_date and rec_date != date_str:
            continue

        new_preds.append({
            "symbol": rec.get("stock_code"),
            "name": rec.get("stock_name"),
            "recommend_price": rec.get("recommend_price"),
            "target_price": rec.get("target_price"),
            "stop_loss": rec.get("stop_loss"),
            "stop_loss_pct": rec.get("stop_loss_pct"),
            "settlement_days": rec.get("settlement_days"),
            "position": rec.get("position"),
            "score": rec.get("score"),
            "result": "holding",
            "settled_date": None,
            "settled_price": None,
            "holding_days": 1,
        })

    # Track B 新推薦
    for rec in tracking.get("track_b_recommendations", []):
        new_preds.append({
            "symbol": rec.get("stock_code"),
            "name": rec.get("stock_name"),
            "recommend_price": rec.get("recommend_price"),
            "target_price": rec.get("target_price"),
            "stop_loss": rec.get("stop_loss"),
            "stop_loss_pct": rec.get("stop_loss_pct", -5),
            "settlement_days": rec.get("settlement_days", 10),
            "position": rec.get("position"),
            "score": rec.get("score"),
            "result": "holding",
            "settled_date": None,
            "settled_price": None,
            "holding_days": 1,
            "track": "B",
        })

    if new_preds:
        predictions[date_str] = {
            "predictions": new_preds,
            "settled_accuracy": None,
            "settled_count": 0,
        }

    return new_preds


def recalculate_stats(predictions):
    """重算頂層統計"""
    total_success = 0
    total_fail = 0
    total_holding = 0

    for key, value in predictions.items():
        if not isinstance(value, dict) or "predictions" not in value:
            continue

        for pred in value["predictions"]:
            result = pred.get("result")
            if result == "success":
                total_success += 1
            elif result == "fail":
                total_fail += 1
            elif result == "holding":
                total_holding += 1

    settled_count = total_success + total_fail
    accuracy = round(total_success / settled_count * 100, 1) if settled_count > 0 else 0

    predictions["settled_accuracy"] = f"{accuracy}%"
    predictions["settled_count"] = settled_count
    predictions["total_success"] = total_success
    predictions["total_fail"] = total_fail
    predictions["holding_count"] = total_holding

    return {
        "settled_accuracy": f"{accuracy}%",
        "settled_count": settled_count,
        "total_success": total_success,
        "total_fail": total_fail,
        "holding_count": total_holding,
    }


def main():
    parser = argparse.ArgumentParser(description="Predictions 更新器")
    parser.add_argument("--date", default=None, help="日期 (YYYY-MM-DD)，預設今天")
    parser.add_argument("--dry-run", action="store_true", help="只顯示變更不寫入")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    print(f"📊 更新 predictions.json — {date_str}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # 讀取資料
    tracking = load_tracking(date_str)
    if tracking is None:
        print(f"❌ tracking_{date_str}.json 不存在", file=sys.stderr)
        sys.exit(1)

    predictions = load_predictions()

    # 1. 更新結算結果
    print("\n📋 結算更新:", file=sys.stderr)
    changes = update_from_tracking(predictions, tracking, date_str)
    for c in changes:
        icon = "✅" if c["to"] == "success" else "❌"
        print(f"  {icon} {c['symbol']} {c['name']} | {c['from']} → {c['to']} | 結算價 {c['settled_price']}", file=sys.stderr)

    # 2. 新增今日推薦
    print("\n📋 新增推薦:", file=sys.stderr)
    new_preds = add_new_recommendations(predictions, tracking, date_str)
    if new_preds:
        for p in new_preds:
            print(f"  + {p['symbol']} {p['name']} | 推薦價 {p['recommend_price']} | {p['score']}分", file=sys.stderr)
    else:
        print("  無新增", file=sys.stderr)

    # 3. 重算統計
    stats = recalculate_stats(predictions)
    print(f"\n📊 統計:", file=sys.stderr)
    print(f"  準確率: {stats['settled_accuracy']} ({stats['total_success']}s / {stats['total_fail']}f / {stats['settled_count']}t)", file=sys.stderr)
    print(f"  Holding: {stats['holding_count']}", file=sys.stderr)

    # 寫入
    if args.dry_run:
        print("\n⚠️ dry-run 模式，不寫入", file=sys.stderr)
    else:
        save_predictions(predictions)
        print(f"\n✅ 已更新 {PREDICTIONS_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
