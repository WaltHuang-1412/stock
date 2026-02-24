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

    # 2. 正規化 intraday 資料結構
    #    Claude 寫入格式不固定，統一轉換為 intraday_analysis.track_a (list)
    intraday = data.get("intraday_analysis", {})

    # 2a. intraday_update → intraday_analysis（key 名稱不同）
    if not intraday and "intraday_update" in data:
        intraday = data.pop("intraday_update")
        data["intraday_analysis"] = intraday
        total_changes += 1

    # 2b. intraday_prices (dict by code) → track_a (list)
    #     例：{"2886": {"intraday_price": 40.8, "action": "續抱"}, ...}
    if "intraday_prices" in intraday and "track_a" not in intraday:
        prices_dict = intraday.pop("intraday_prices")
        track_a = []
        recs_map = {r.get("stock_code", r.get("symbol", "")): r
                    for r in data.get("recommendations", [])}
        for code, info in prices_dict.items():
            entry = {"stock_code": code}
            entry["stock_name"] = recs_map.get(code, {}).get(
                "stock_name", recs_map.get(code, {}).get("name", ""))
            entry["intraday_price"] = info.get("intraday_price", info.get("price", "?"))
            entry["intraday_change"] = info.get("change_today_pct",
                info.get("change_pct", info.get("intraday_change", "?")))
            # vs_recommend: 盤中價 vs 推薦價
            rec = recs_map.get(code, {})
            rec_price = rec.get("recommend_price", rec.get("entry_price"))
            intra_price = entry["intraday_price"]
            if isinstance(rec_price, (int, float)) and isinstance(intra_price, (int, float)) and rec_price > 0:
                entry["vs_recommend"] = round((intra_price - rec_price) / rec_price * 100, 2)
            entry["strategy"] = info.get("action", info.get("strategy",
                info.get("intraday_strategy", "")))
            entry["volume_ratio"] = info.get("volume_ratio", info.get("vol_ratio", ""))
            track_a.append(entry)
        intraday["track_a"] = track_a
        total_changes += len(track_a)

    # 2c. tracking_results (list) → track_a
    if "tracking_results" in intraday and "track_a" not in intraday:
        intraday["track_a"] = intraday.pop("tracking_results")
        total_changes += 1

    # 2d. 從 recommendations 內嵌 intraday 欄位建立 track_a（fallback）
    if not intraday.get("track_a"):
        recs = data.get("recommendations", [])
        built_track_a = []
        for rec in recs:
            code = rec.get("stock_code", rec.get("symbol", ""))
            name = rec.get("stock_name", rec.get("name", ""))
            # 格式 A：nested intraday object
            intra = rec.get("intraday", {})
            if isinstance(intra, dict) and intra:
                entry = {
                    "stock_code": code,
                    "stock_name": name,
                    "intraday_price": intra.get("price", intra.get("intraday_price", "?")),
                    "vs_recommend": intra.get("vs_recommend_pct", "?"),
                    "strategy": intra.get("intraday_strategy", intra.get("strategy", "")),
                    "volume_ratio": intra.get("volume_ratio", ""),
                }
                built_track_a.append(entry)
            # 格式 B：flat intraday_price 欄位
            elif rec.get("intraday_price") is not None:
                entry = {
                    "stock_code": code,
                    "stock_name": name,
                    "intraday_price": rec.get("intraday_price", "?"),
                    "vs_recommend": rec.get("intraday_vs_recommend_pct",
                        rec.get("vs_recommend_pct", "?")),
                    "strategy": rec.get("intraday_strategy", ""),
                    "volume_ratio": rec.get("intraday_vol_ratio",
                        rec.get("volume_ratio", "")),
                }
                built_track_a.append(entry)
        if built_track_a:
            if "intraday_analysis" not in data:
                data["intraday_analysis"] = {}
                intraday = data["intraday_analysis"]
            intraday["track_a"] = built_track_a
            total_changes += len(built_track_a)

    # track_a 欄位正規化
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
