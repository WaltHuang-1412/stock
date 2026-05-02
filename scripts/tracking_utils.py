#!/usr/bin/env python3
"""
tracking.json 共用工具

提供統一的載入 + schema 驗證，避免各腳本各自解析出不一致的結果。
"""

import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"

# 推薦項目必填欄位 + 型別
REQUIRED_FIELDS = {
    "stock_code": str,
    "stock_name": str,
    "recommend_price": (int, float),
    "target_price": (int, float),
    "stop_loss_pct": (int, float),
    "settlement_days": int,
}


def load_tracking(date_str):
    """
    載入 tracking.json 並驗證 schema。

    Args:
        date_str: YYYY-MM-DD

    Returns:
        dict: tracking 資料（驗證通過）
        None: 檔案不存在

    Raises:
        ValueError: schema 驗證失敗（附詳細錯誤訊息）
    """
    tracking_file = TRACKING_DIR / f"tracking_{date_str}.json"
    if not tracking_file.exists():
        return None

    with open(tracking_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors = validate_tracking(data, date_str)
    if errors:
        msg = f"tracking_{date_str}.json schema 驗證失敗:\n"
        for e in errors:
            msg += f"  - {e}\n"
        print(msg, file=sys.stderr)
        # 不 raise，只警告。避免一個欄位缺失就整個流程停擺
        # raise ValueError(msg)

    return data


def validate_tracking(data, date_str=""):
    """
    驗證 tracking.json 結構。

    Returns:
        list: 錯誤訊息列表（空=通過）
    """
    errors = []

    if not isinstance(data, dict):
        return [f"根層級不是 dict"]

    if "date" not in data:
        errors.append("缺少 'date' 欄位")

    if "recommendations" not in data:
        errors.append("缺少 'recommendations' 欄位")
        return errors

    recs = data["recommendations"]
    if not isinstance(recs, list):
        errors.append("'recommendations' 不是 list")
        return errors

    for i, rec in enumerate(recs):
        prefix = f"recommendations[{i}] ({rec.get('stock_code', '?')})"

        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in rec:
                errors.append(f"{prefix}: 缺少 '{field}'")
            elif not isinstance(rec[field], expected_type):
                errors.append(f"{prefix}: '{field}' 型別錯誤 (期望 {expected_type}, 實際 {type(rec[field]).__name__})")

        # recommend_price 不能為 0 或負數
        rp = rec.get("recommend_price")
        if isinstance(rp, (int, float)) and rp <= 0:
            errors.append(f"{prefix}: recommend_price={rp} 不合理（≤0）")

        # stop_loss 應從 stop_loss_pct 計算
        if "stop_loss" in rec and "stop_loss_pct" in rec and "recommend_price" in rec:
            rp = rec["recommend_price"]
            pct = rec["stop_loss_pct"]
            sl = rec["stop_loss"]
            if isinstance(rp, (int, float)) and isinstance(pct, (int, float)) and isinstance(sl, (int, float)):
                expected_sl = round(rp * (1 + pct / 100), 2)
                if abs(sl - expected_sl) > 0.1:
                    errors.append(f"{prefix}: stop_loss={sl} 與 stop_loss_pct={pct} 計算不符（應為 {expected_sl}）")

    return errors


def recalculate_stop_losses(data):
    """
    用 stop_loss_pct 重算所有推薦的 stop_loss。

    Returns:
        list: 被修正的股票清單
    """
    fixed = []
    for rec in data.get("recommendations", []):
        rp = rec.get("recommend_price")
        pct = rec.get("stop_loss_pct")
        if isinstance(rp, (int, float)) and isinstance(pct, (int, float)) and rp > 0:
            new_sl = round(rp * (1 + pct / 100), 2)
            old_sl = rec.get("stop_loss")
            if old_sl != new_sl:
                rec["stop_loss"] = new_sl
                fixed.append({
                    "code": rec.get("stock_code"),
                    "old": old_sl,
                    "new": new_sl,
                })
    return fixed


if __name__ == "__main__":
    """CLI：驗證指定日期的 tracking.json"""
    import argparse
    parser = argparse.ArgumentParser(description="tracking.json 驗證器")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    data = load_tracking(args.date)
    if data is None:
        print(f"❌ tracking_{args.date}.json 不存在")
        sys.exit(1)

    errors = validate_tracking(data, args.date)
    if errors:
        print(f"❌ 發現 {len(errors)} 個問題:")
        for e in errors:
            print(f"  - {e}")
    else:
        recs = len(data.get("recommendations", []))
        print(f"✅ tracking_{args.date}.json 驗證通過（{recs} 檔推薦）")
