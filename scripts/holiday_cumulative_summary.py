#!/usr/bin/env python3
"""
假期/週末累積摘要產生器

當盤前偵測到距上一交易日 >1 天時自動執行。
掃描間隔天數內所有 us_leader_alerts.json，計算龍頭股連漲/連跌天數與持續性等級。

用法：
    python scripts/holiday_cumulative_summary.py --date 2026-02-23
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
DATA_DIR = PROJECT_DIR / "data"
HOLIDAYS_FILE = PROJECT_DIR / "data" / "holidays.json"

# 龍頭股→台股產業對應（與 us_leader_alert.py 一致）
LEADER_TW_INDUSTRIES = {
    "Micron": ["記憶體"],
    "NVIDIA": ["AI", "半導體"],
    "Apple": ["蘋果供應鏈"],
    "AMD": ["半導體"],
    "Tesla": ["電動車"],
    "Super Micro": ["AI"],
    "Broadcom": ["網通設備"],
    "AMAT": ["半導體"],
}

# 要追蹤的龍頭股名稱（在 us_asia_markets.json markdown 中的可能寫法）
LEADER_ALIASES = {
    "Micron": ["Micron", "MU"],
    "NVIDIA": ["NVIDIA", "輝達"],
    "Apple": ["Apple", "AAPL"],
    "AMD": ["AMD"],
    "Tesla": ["Tesla", "TSLA"],
    "Super Micro": ["Super Micro", "SMCI"],
    "Broadcom": ["Broadcom", "AVGO"],
    "AMAT": ["AMAT", "Applied Materials"],
    "Dell": ["Dell"],
    "ASML": ["ASML"],
    "Lam Research": ["Lam Research", "Lam"],
}


def load_holidays():
    """讀取台股假日清單"""
    if not HOLIDAYS_FILE.exists():
        return set()
    with open(HOLIDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    holidays = set()
    for year_dates in data.get("holidays", {}).values():
        for h in year_dates:
            holidays.add(h["date"])
    return holidays


def is_tw_trading_day(date_str, holidays):
    """判斷某日是否為台股交易日"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if dt.weekday() >= 5:  # 週六日
        return False
    if date_str in holidays:
        return False
    return True


def find_previous_trading_day(date_str, holidays):
    """往前找上一個台股交易日"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    for i in range(1, 30):
        prev = dt - timedelta(days=i)
        prev_str = prev.strftime("%Y-%m-%d")
        if is_tw_trading_day(prev_str, holidays):
            return prev_str
    return None


def parse_change_from_markdown(content, stock_aliases):
    """從 us_asia_markets.json (markdown格式) 解析龍頭股漲跌幅"""
    import re
    for alias in stock_aliases:
        # 匹配 "Micron(MU): $428.17 (+3.43%)" 或 "⭐ Micron(MU): $428.17 (+3.43%)"
        pattern = rf"{re.escape(alias)}.*?\(([+-]?\d+\.?\d*)%\)"
        match = re.search(pattern, content)
        if match:
            return float(match.group(1))
    return None


def parse_change_from_alerts(alerts_data, stock_name):
    """從 us_leader_alerts.json 解析龍頭股漲跌幅"""
    for alert in alerts_data.get("alerts", []):
        if alert.get("us_stock") == stock_name:
            return alert.get("change_pct")
    return None


def collect_daily_data(date_str):
    """收集某一天的龍頭股漲跌數據"""
    day_dir = DATA_DIR / date_str
    results = {}

    # 讀取 us_asia_markets.json (markdown)
    markets_file = day_dir / "us_asia_markets.json"
    md_content = ""
    if markets_file.exists():
        with open(markets_file, "r", encoding="utf-8") as f:
            md_content = f.read()

    # 讀取 us_leader_alerts.json
    alerts_file = day_dir / "us_leader_alerts.json"
    alerts_data = {}
    if alerts_file.exists():
        try:
            with open(alerts_file, "r", encoding="utf-8") as f:
                alerts_data = json.load(f)
        except json.JSONDecodeError:
            pass

    for leader, aliases in LEADER_ALIASES.items():
        # 優先從 markdown 解析
        change = parse_change_from_markdown(md_content, aliases)
        # fallback: 從 alerts 解析（只有跌的會出現）
        if change is None:
            change = parse_change_from_alerts(alerts_data, leader)
        if change is not None:
            results[leader] = change

    return results


def calculate_sustained_level(daily_changes):
    """計算持續性等級"""
    if not daily_changes:
        return "無數據"

    # 計算連漲/連跌天數（從最後一天往前數）
    consecutive_up = 0
    consecutive_down = 0
    for change in reversed(daily_changes):
        if change > 0:
            consecutive_up += 1
        else:
            break
    for change in reversed(daily_changes):
        if change < 0:
            consecutive_down += 1
        else:
            break

    cumulative = sum(daily_changes)
    avg_abs = sum(abs(c) for c in daily_changes) / len(daily_changes)

    # 超強：連漲≥3天 且 每天平均>5%
    if consecutive_up >= 3 and all(c > 5 for c in daily_changes[-consecutive_up:]):
        return "超強"
    # 超強（跌）：連跌≥3天 且 每天平均<-5%
    if consecutive_down >= 3 and all(c < -5 for c in daily_changes[-consecutive_down:]):
        return "超強利空"
    # 強：連漲≥3天 或 累計>15%
    if consecutive_up >= 3 or cumulative > 15:
        return "強"
    # 強利空：連跌≥3天 或 累計<-15%
    if consecutive_down >= 3 or cumulative < -15:
        return "強利空"
    # 一般
    return "一般"


def generate_cumulative_summary(target_date):
    """產生累積摘要"""
    holidays = load_holidays()

    # 找上一個交易日
    prev_trading_day = find_previous_trading_day(target_date, holidays)
    if not prev_trading_day:
        print("找不到上一個交易日", file=sys.stderr)
        return None

    # 計算間隔天數
    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    prev_dt = datetime.strptime(prev_trading_day, "%Y-%m-%d")
    gap_days = (target_dt - prev_dt).days

    if gap_days <= 1:
        print(f"間隔僅 {gap_days} 天，不需要累積摘要")
        return None

    # 掃描間隔天數內所有快照
    raw_daily_data = {}  # {date: {leader: change}}
    scan_dt = prev_dt + timedelta(days=1)
    while scan_dt <= target_dt:
        scan_date = scan_dt.strftime("%Y-%m-%d")
        day_data = collect_daily_data(scan_date)
        if day_data:
            raw_daily_data[scan_date] = day_data
        scan_dt += timedelta(days=1)

    if not raw_daily_data:
        print("間隔期間無美股數據", file=sys.stderr)
        return None

    # 去重：週末/假日快照會複製前一交易日數據
    # 如果某天所有龍頭股的漲跌幅與前一天完全相同，視為重複快照跳過
    all_daily_data = {}
    prev_data = None
    for d in sorted(raw_daily_data.keys()):
        cur_data = raw_daily_data[d]
        if prev_data is not None and cur_data == prev_data:
            print(f"  跳過重複快照：{d}", file=sys.stderr)
            continue
        all_daily_data[d] = cur_data
        prev_data = cur_data

    if not all_daily_data:
        print("去重後無有效美股數據", file=sys.stderr)
        return None

    sorted_dates = sorted(all_daily_data.keys())
    print(f"  快照去重：{len(raw_daily_data)} → {len(all_daily_data)} 個唯一交易日", file=sys.stderr)

    # 彙整每個龍頭股的逐日變化
    leaders_summary = {}
    all_leaders = set()
    for day_data in all_daily_data.values():
        all_leaders.update(day_data.keys())

    for leader in sorted(all_leaders):
        daily_changes = []
        for d in sorted_dates:
            change = all_daily_data[d].get(leader)
            if change is not None:
                daily_changes.append(change)

        if not daily_changes:
            continue

        cumulative = sum(daily_changes)

        # 連漲/連跌天數
        consecutive_up = 0
        for c in reversed(daily_changes):
            if c > 0:
                consecutive_up += 1
            else:
                break
        consecutive_down = 0
        for c in reversed(daily_changes):
            if c < 0:
                consecutive_down += 1
            else:
                break

        sustained_level = calculate_sustained_level(daily_changes)

        leaders_summary[leader] = {
            "daily_changes": daily_changes,
            "dates": [d for d in sorted_dates if leader in all_daily_data.get(d, {})],
            "cumulative": round(cumulative, 2),
            "trading_days": len(daily_changes),
            "consecutive_up": consecutive_up,
            "consecutive_down": consecutive_down,
            "sustained_level": sustained_level,
        }

    # 篩選持續性催化（超強/強/強利空/超強利空）
    sustained_catalysts = []
    for leader, info in leaders_summary.items():
        if info["sustained_level"] in ("超強", "強"):
            tw_industries = LEADER_TW_INDUSTRIES.get(leader, [])
            note_parts = []
            if info["consecutive_up"] >= 3:
                note_parts.append(f"連漲{info['consecutive_up']}天")
            if info["cumulative"] > 15:
                note_parts.append(f"累計+{info['cumulative']}%")
            sustained_catalysts.append({
                "leader": leader,
                "level": info["sustained_level"],
                "tw_industries": tw_industries,
                "cumulative": info["cumulative"],
                "consecutive_up": info["consecutive_up"],
                "note": "、".join(note_parts) if note_parts else f"累計{info['cumulative']:+.1f}%",
            })
        elif info["sustained_level"] in ("超強利空", "強利空"):
            tw_industries = LEADER_TW_INDUSTRIES.get(leader, [])
            note_parts = []
            if info["consecutive_down"] >= 3:
                note_parts.append(f"連跌{info['consecutive_down']}天")
            if info["cumulative"] < -15:
                note_parts.append(f"累計{info['cumulative']}%")
            sustained_catalysts.append({
                "leader": leader,
                "level": info["sustained_level"],
                "tw_industries": tw_industries,
                "cumulative": info["cumulative"],
                "consecutive_down": info["consecutive_down"],
                "note": "、".join(note_parts) if note_parts else f"累計{info['cumulative']:+.1f}%",
            })

    # 排序：超強在前
    level_order = {"超強": 0, "超強利空": 1, "強": 2, "強利空": 3}
    sustained_catalysts.sort(key=lambda x: level_order.get(x["level"], 9))

    result = {
        "target_date": target_date,
        "previous_trading_day": prev_trading_day,
        "gap_days": gap_days,
        "us_trading_days": len(sorted_dates),
        "snapshot_dates": sorted_dates,
        "leaders": leaders_summary,
        "sustained_catalysts": sustained_catalysts,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="假期/週末累積摘要")
    parser.add_argument("--date", required=True, help="目標日期 (YYYY-MM-DD)")
    args = parser.parse_args()

    result = generate_cumulative_summary(args.date)
    if result is None:
        sys.exit(0)

    # 輸出到 data/YYYY-MM-DD/cumulative_summary.json
    output_dir = DATA_DIR / args.date
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "cumulative_summary.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 累積摘要已產生：{output_file}", file=sys.stderr)

    # 也輸出到 stdout 供人閱讀
    cats = result.get("sustained_catalysts", [])
    print(f"\n{'='*50}")
    print(f"假期累積摘要（{result['previous_trading_day']} → {result['target_date']}）")
    print(f"間隔 {result['gap_days']} 天，美股交易 {result['us_trading_days']} 天")
    print(f"{'='*50}")

    if cats:
        print(f"\n🔥 持續性催化（{len(cats)} 個）：")
        for c in cats:
            industries = "、".join(c["tw_industries"]) if c["tw_industries"] else "—"
            print(f"  [{c['level']}] {c['leader']}：{c['note']}（影響：{industries}）")
    else:
        print("\n✅ 無持續性催化訊號")

    # 列出所有龍頭股摘要
    print(f"\n📊 龍頭股逐日變化：")
    for leader, info in sorted(result["leaders"].items(), key=lambda x: -abs(x[1]["cumulative"])):
        changes_str = " → ".join(f"{c:+.1f}%" for c in info["daily_changes"])
        print(f"  {leader}: {changes_str}（累計{info['cumulative']:+.1f}%，{info['sustained_level']}）")


if __name__ == "__main__":
    main()
