#!/usr/bin/env python3
"""
LINE 摘要產生器
從分析結果中提取重點，產生簡潔的 LINE 推送內容

用法：
    python scripts/generate_line_summary.py before_market 2026-02-14
    python scripts/generate_line_summary.py intraday 2026-02-14
    python scripts/generate_line_summary.py after_market 2026-02-14
    python scripts/generate_line_summary.py holiday 2026-02-14
"""

import sys
import io
import json
from pathlib import Path

# Windows 環境強制 UTF-8 輸出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"


def _get(rec, *keys, default="?"):
    """從推薦中讀取欄位，依序嘗試多個欄位名"""
    for k in keys:
        v = rec.get(k)
        if v is not None and v != "":
            return v
    return default


def load_json(filepath):
    """讀取 JSON 檔案"""
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def before_market_summary(date):
    """盤前摘要：推薦股票清單"""
    tracking = load_json(DATA_DIR / "tracking" / f"tracking_{date}.json")
    if not tracking:
        return f"[{date}] 盤前分析完成，但無法讀取推薦資料"

    recs = tracking.get("recommendations", [])
    if not recs:
        return f"[{date}] 盤前分析完成，無推薦股票"

    lines = [f"[{date}] 盤前分析完成", f"推薦 {len(recs)} 檔：", ""]

    for r in recs:
        code = _get(r, "stock_code", "symbol")
        name = _get(r, "stock_name", "name")
        score = _get(r, "score")
        entry = _get(r, "recommend_price", "entry_price")
        target = _get(r, "target_price", "target")
        stop = _get(r, "stop_loss")
        position = _get(r, "position")
        industry = _get(r, "industry", default="")
        rating = _get(r, "rating", default="")
        reason = _get(r, "reason", default="")
        risk = _get(r, "risk_note", "risk", "warning", default="")

        # 計算目標/停損漲跌%
        target_pct = ""
        stop_pct = ""
        if isinstance(entry, (int, float)) and isinstance(target, (int, float)) and entry > 0:
            target_pct = f"(+{(target - entry) / entry * 100:.1f}%)"
        if isinstance(entry, (int, float)) and isinstance(stop, (int, float)) and entry > 0:
            stop_pct = f"({(stop - entry) / entry * 100:.1f}%)"

        lines.append(f"{rating} {name}({code}) {score}分")
        lines.append(f"產業：{industry}｜倉位：{position}")
        lines.append(f"進場：{entry} → 目標：{target}{target_pct}｜停損：{stop}{stop_pct}")
        if reason:
            lines.append(f"理由：{reason}")
        if risk:
            lines.append(f"⚠️ {risk}")
        lines.append("")

    # 今日注意事項
    ctx = tracking.get("market_context", {})
    if ctx:
        catalysts = ctx.get("key_catalysts", [])
        negatives = ctx.get("negative_catalysts", [])
        if catalysts or negatives:
            lines.append("---")
            lines.append("今日注意：")
            for c in catalysts:
                lines.append(f"  📈 {c}")
            for n in negatives:
                lines.append(f"  📉 {n}")

    return "\n".join(lines)


def intraday_summary(date):
    """盤中摘要：推薦股表現 + 操作建議"""
    tracking = load_json(DATA_DIR / "tracking" / f"tracking_{date}.json")
    if not tracking:
        return f"[{date}] 盤中分析完成，但無法讀取追蹤資料"

    recs = tracking.get("recommendations", [])
    if not recs:
        return f"[{date}] 盤中分析完成，無追蹤股票"

    lines = [f"[{date}] 盤中分析完成", ""]

    for r in recs:
        code = _get(r, "stock_code", "symbol")
        name = _get(r, "stock_name", "name")
        entry = _get(r, "recommend_price", "entry_price")

        # 支援巢狀結構 intraday{} 和平層 intraday_price
        intra = r.get("intraday", {})
        if isinstance(intra, dict) and intra:
            intraday = intra.get("price", "?")
            change = intra.get("vs_recommend_pct", "?")
            strategy = intra.get("intraday_strategy", "")
        else:
            intraday = r.get("intraday_price", "?")
            change = r.get("intraday_vs_recommend_pct", r.get("intraday_change", "?"))
            strategy = r.get("intraday_strategy", "")

        if isinstance(change, (int, float)):
            sign = "+" if change >= 0 else ""
            change_str = f"{sign}{change:.1f}%"
        else:
            change_str = str(change)

        # 狀態圖示
        if isinstance(change, (int, float)):
            if change >= 3:
                icon = "🟢"
            elif change >= 0:
                icon = "🔵"
            elif change >= -3:
                icon = "🟡"
            else:
                icon = "🔴"
        else:
            icon = "⚪"

        lines.append(f"{icon} {name}({code}) {change_str}")
        lines.append(f"  推薦:{entry} → 盤中:{intraday}")
        if strategy:
            # 只取策略的前 30 字
            short = strategy[:30] + ("..." if len(strategy) > 30 else "")
            lines.append(f"  策略:{short}")
        lines.append("")

    # === Track B：盤中發現 + 佈局機會 ===
    intraday_data = tracking.get("intraday_analysis", {})
    discoveries = intraday_data.get("track_b_discoveries", [])
    if discoveries:
        lines.append("---")
        lines.append("🔍 盤中發現（佈局機會）")
        lines.append("")
        for d in discoveries:
            name = d.get("stock_name", d.get("name", "?"))
            code = d.get("stock_code", d.get("symbol", "?"))
            chg = d.get("intraday_change", "?")
            price = d.get("price", "")
            vol = d.get("volume_ratio", "")
            chip = d.get("chip_data", "")
            action = d.get("action", "")
            vol_str = f" 量比{vol}x" if vol else ""
            price_str = f" 現價:{price}" if price else ""
            lines.append(f"📌 {name}({code}) {chg}{price_str}{vol_str}")
            if chip:
                lines.append(f"  {chip}")
            if action:
                lines.append(f"  → {action}")
            lines.append("")

    # === Track A 警告摘要 ===
    track_a = intraday_data.get("track_a_summary", {})
    warnings = track_a.get("warnings", [])
    forced_stops = track_a.get("forced_stops", 0)
    if forced_stops > 0 or warnings:
        lines.append("---")
        if forced_stops > 0:
            lines.append(f"🛑 強制停損：{forced_stops} 檔")
        for w in warnings:
            lines.append(f"⚠️ {w}")

    return "\n".join(lines)


def _short_reason(reason, max_len=50):
    """截取推薦原因的重點"""
    if not reason:
        return ""
    # 取第一句或前 max_len 字
    for sep in ["。", "；", "\n"]:
        if sep in reason:
            reason = reason.split(sep)[0]
            break
    if len(reason) > max_len:
        reason = reason[:max_len] + "..."
    return reason


def after_market_summary(date):
    """盤後摘要：準確率 + 評分原因 + 失敗分析 + 明日重點"""
    tracking = load_json(DATA_DIR / "tracking" / f"tracking_{date}.json")
    if not tracking:
        return f"[{date}] 盤後分析完成，但無法讀取追蹤資料"

    recs = tracking.get("recommendations", [])
    if not recs:
        return f"[{date}] 盤後分析完成，無追蹤股票"

    # 計算準確率
    total = 0
    success = 0
    success_list = []
    fail_list = []
    for r in recs:
        result = r.get("result", "")
        if result:
            total += 1
            if result == "success":
                success += 1

        code = _get(r, "stock_code", "symbol")
        name = _get(r, "stock_name", "name")
        score = _get(r, "score")
        entry = _get(r, "recommend_price", "entry_price")
        close = _get(r, "closing_price", "close_price")
        change = _get(r, "vs_recommend_pct")
        reason = _get(r, "reason", default="")
        catalyst = _get(r, "catalyst", default="")

        if isinstance(change, (int, float)):
            sign = "+" if change >= 0 else ""
            change_str = f"{sign}{change:.1f}%"
        else:
            change_str = str(change)

        icon = "✅" if result == "success" else "❌" if result == "fail" else "⚪"
        short = _short_reason(reason) or _short_reason(catalyst)

        # 格式化價格（避免浮點數過長）
        entry_fmt = f"{entry:.1f}" if isinstance(entry, float) else str(entry)
        close_fmt = f"{close:.1f}" if isinstance(close, float) else str(close)

        entry_info = {
            "line": f"{icon} {name}({code}) {change_str} ({entry_fmt}→{close_fmt}) {score}分",
            "reason": short,
            "name": name,
            "code": code,
            "change_str": change_str,
            "result": result,
        }

        if result == "fail":
            fail_list.append(entry_info)
        else:
            success_list.append(entry_info)

    # === 標題 + 準確率 ===
    if total > 0:
        acc = success / total * 100
        lines = [f"[{date}] 盤後驗證", f"準確率：{success}/{total} = {acc:.0f}%", ""]
    else:
        lines = [f"[{date}] 盤後分析完成", ""]

    # === 個股結果（含評分與原因）===
    for item in success_list + fail_list:
        lines.append(item["line"])
        if item["reason"]:
            lines.append(f"  原因:{item['reason']}")
        lines.append("")

    # === 失敗原因深度分析 ===
    if fail_list:
        lines.append("---")
        lines.append("失敗分析：")
        for item in fail_list:
            name = item["name"]
            code = item["code"]
            change = item["change_str"]
            # 從 tracking 找更多失敗資訊
            rec = next((r for r in recs if r.get("stock_code") == code), {})
            fail_reason = rec.get("fail_reason", "")
            if fail_reason:
                lines.append(f"  {name}({code}) {change}")
                short_fail = _short_reason(fail_reason, 80)
                lines.append(f"  → {short_fail}")
            else:
                lines.append(f"  {name}({code}) {change}（原因待分析）")
            lines.append("")

    # === 明日重點 ===
    after_summary = tracking.get("after_market_summary", {})
    tomorrow = ""
    if isinstance(after_summary, dict):
        tomorrow = after_summary.get("tomorrow_focus", "")
        if not tomorrow:
            tomorrow = after_summary.get("next_day_prediction", "")
        if not tomorrow:
            tomorrow = after_summary.get("notes", after_summary.get("summary", ""))

    if tomorrow:
        lines.append("---")
        lines.append("明日重點：")
        short = str(tomorrow)[:200] + ("..." if len(str(tomorrow)) > 200 else "")
        lines.append(short)

    return "\n".join(lines)


def holiday_summary(date):
    """假日摘要：美股快照重點"""
    # 嘗試讀取 holiday_snapshot.md
    snapshot = DATA_DIR / date / "holiday_snapshot.md"
    if snapshot.exists():
        with open(snapshot, "r", encoding="utf-8") as f:
            content = f.read()
        # 截取前 2000 字（留餘量給 LINE 5000 上限）
        if len(content) > 2000:
            content = content[:2000] + "\n\n...（詳見 GitHub）"
        return content

    # fallback: 讀取 us_leader_alerts.json
    alerts = load_json(DATA_DIR / date / "us_leader_alerts.json")
    if alerts:
        return f"[{date}] 假日美股快照完成\n\n{json.dumps(alerts, ensure_ascii=False, indent=2)[:2000]}"

    return f"[{date}] 假日美股快照完成"


def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/generate_line_summary.py <mode> <date>")
        print("mode: before_market | intraday | after_market | holiday")
        sys.exit(1)

    mode = sys.argv[1]
    date = sys.argv[2]

    handlers = {
        "before_market": before_market_summary,
        "intraday": intraday_summary,
        "after_market": after_market_summary,
        "holiday": holiday_summary,
    }

    if mode not in handlers:
        print(f"未知模式: {mode}")
        sys.exit(1)

    summary = handlers[mode](date)
    print(summary)


if __name__ == "__main__":
    main()
