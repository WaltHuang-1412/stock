#!/usr/bin/env python3
"""
tracking.json 欄位正規化工具
在 LINE 推送前執行，自動將各種欄位別名統一為標準名稱。
確保 generate_line_summary.py 能正確讀取。

使用方式：
    python scripts/normalize_tracking_fields.py 2026-02-24
    python scripts/normalize_tracking_fields.py          # 自動用今天日期
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"

# === 標準欄位名稱 + 別名對照表 ===

# recommendations[] 內的欄位
REC_FIELD_MAP = {
    # 標準名: [別名列表]
    "stock_code": ["symbol", "code"],
    "stock_name": ["name"],
    "recommend_price": ["entry_price", "entry_price_original"],
    "actual_close": ["closing_price", "close_price", "closing"],
    "vs_recommend_pct": ["change_pct", "close_change_pct", "actual_change_pct", "daily_change_pct"],
    "result": ["final_result"],
    "fail_reason": ["result_reason", "result_note"],
    "target_price": ["target", "target_original"],
    "stop_loss": ["stop_loss_original"],
    "intraday_price": ["intraday_close", "current_price"],
    "intraday_change": ["intraday_change_pct", "daily_change", "day_change_pct"],
    "intraday_strategy": ["intraday_action", "intraday_status"],
}

# intraday_analysis.track_a[] 內的欄位
TRACK_A_FIELD_MAP = {
    "stock_code": ["symbol", "code"],
    "stock_name": ["name"],
    "intraday_price": ["price", "current_price", "intraday_close"],
    "intraday_change": ["change", "change_pct", "daily_change"],
    "vs_recommend": ["vs_recommend_pct", "profit_pct", "vs_entry"],
    "strategy": ["intraday_strategy", "action", "intraday_action"],
    "volume_ratio": ["vol_ratio", "intraday_vol_ratio", "intraday_volume_ratio"],
    "exit_signal": ["signal", "exit_status"],
}

# intraday_analysis.track_b_discoveries[] 內的欄位
TRACK_B_FIELD_MAP = {
    "stock_code": ["symbol", "code"],
    "stock_name": ["name"],
    "price": ["current_price", "intraday_price"],
    "intraday_change": ["change", "change_pct"],
    "volume_ratio": ["vol_ratio"],
    "action": ["strategy", "suggestion"],
}


def normalize_fields(obj, field_map):
    """將物件中的別名欄位改為標準名稱"""
    if not isinstance(obj, dict):
        return obj, 0

    changes = 0
    for standard_name, aliases in field_map.items():
        if standard_name in obj:
            continue  # 已有標準名，跳過
        for alias in aliases:
            if alias in obj:
                obj[standard_name] = obj.pop(alias)
                changes += 1
                break
    return obj, changes


def ensure_string_to_number(obj, field_name):
    """將字串百分比轉為數字（如 "+7.65%" → 7.65）"""
    val = obj.get(field_name)
    if isinstance(val, str) and val not in ("?", "", "N/A"):
        try:
            obj[field_name] = float(val.replace("%", "").replace("+", "").replace(",", ""))
            return 1
        except ValueError:
            pass
    return 0


def normalize_tracking(date):
    """正規化指定日期的 tracking.json"""
    tracking_file = DATA_DIR / "tracking" / f"tracking_{date}.json"

    if not tracking_file.exists():
        print(f"[SKIP] tracking_{date}.json 不存在", file=sys.stderr)
        return False

    with open(tracking_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_changes = 0

    # 1. 正規化 recommendations[]
    for rec in data.get("recommendations", []):
        _, changes = normalize_fields(rec, REC_FIELD_MAP)
        total_changes += changes
        # vs_recommend_pct 轉數字
        total_changes += ensure_string_to_number(rec, "vs_recommend_pct")

    # 2. 正規化 intraday_analysis
    intraday = data.get("intraday_analysis", {})

    # track_a
    for ta in intraday.get("track_a", []):
        _, changes = normalize_fields(ta, TRACK_A_FIELD_MAP)
        total_changes += changes
        total_changes += ensure_string_to_number(ta, "vs_recommend")

    # track_b_discoveries
    for tb in intraday.get("track_b_discoveries", []):
        _, changes = normalize_fields(tb, TRACK_B_FIELD_MAP)
        total_changes += changes

    # missed_opportunities: 確保是字串陣列
    missed = intraday.get("missed_opportunities", [])
    if missed and isinstance(missed[0], dict):
        normalized = []
        for m in missed:
            stock = m.get("stock_name", m.get("name", "?"))
            code = m.get("stock_code", m.get("symbol", "?"))
            chg = m.get("change", m.get("intraday_change", "?"))
            normalized.append(f"{stock}({code}){chg}")
        intraday["missed_opportunities"] = normalized
        total_changes += len(missed)

    # 3. 正規化 after_market_analysis / after_market_summary
    after_key = None
    for key in ("after_market_analysis", "after_market_summary"):
        if key in data:
            after_key = key
            break

    if after_key and after_key != "after_market_analysis":
        data["after_market_analysis"] = data.pop(after_key)
        total_changes += 1

    # 4. 寫回
    if total_changes > 0:
        with open(tracking_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] tracking_{date}.json 正規化完成：修正 {total_changes} 個欄位")
    else:
        print(f"[OK] tracking_{date}.json 欄位已正確，無需修正")

    return True


def main():
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    normalize_tracking(date)


if __name__ == "__main__":
    main()
