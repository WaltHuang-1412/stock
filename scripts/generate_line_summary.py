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
        code = r.get("stock_code", "?")
        name = r.get("stock_name", "?")
        score = r.get("score", "?")
        entry = r.get("recommend_price", "?")
        target = r.get("target_price", "?")
        stop = r.get("stop_loss", "?")
        position = r.get("position", "?")
        industry = r.get("industry", "")
        rating = r.get("rating", "")

        lines.append(f"{rating} {name}({code}) {score}分")
        lines.append(f"  進場:{entry} 目標:{target} 停損:{stop}")
        lines.append(f"  倉位:{position} 產業:{industry}")
        lines.append("")

    # 市場概況（簡要）
    ctx = tracking.get("market_context", {})
    if ctx:
        lines.append("---")
        lines.append("市場概況：")
        for key, val in ctx.items():
            if isinstance(val, dict):
                change = val.get("change_pct", val.get("change", ""))
                if change:
                    lines.append(f"  {key}: {change}")
            elif isinstance(val, (int, float, str)):
                lines.append(f"  {key}: {val}")

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
        code = r.get("stock_code", "?")
        name = r.get("stock_name", "?")
        entry = r.get("recommend_price", "?")
        intraday = r.get("intraday_price", "?")
        change = r.get("intraday_vs_recommend_pct", "?")
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

        code = r.get("stock_code", "?")
        name = r.get("stock_name", "?")
        score = r.get("score", "?")
        entry = r.get("recommend_price", "?")
        close = r.get("closing_price", "?")
        change = r.get("vs_recommend_pct", "?")
        reason = r.get("reason", "")
        catalyst = r.get("catalyst", "")

        if isinstance(change, (int, float)):
            sign = "+" if change >= 0 else ""
            change_str = f"{sign}{change:.1f}%"
        else:
            change_str = str(change)

        icon = "✅" if result == "success" else "❌" if result == "fail" else "⚪"
        short = _short_reason(reason) or _short_reason(catalyst)

        entry_info = {
            "line": f"{icon} {name}({code}) {change_str} ({entry}→{close}) {score}分",
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
