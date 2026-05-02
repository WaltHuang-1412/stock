#!/usr/bin/env python3
"""
產業分散檢查器

驗證推薦清單是否符合產業分散規則：
  1. 單一產業 ≤ 50%
  2. 至少 3 個不同產業
  3. 推薦 6-8 檔

用法：
  python scripts/check_industry_diversification.py --date 2026-05-02
  python scripts/check_industry_diversification.py --stocks '2303:半導體,2317:AI伺服器,2301:光通訊,3661:IC設計,2327:被動元件,2356:AI伺服器'
"""

import sys
import io
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import Counter

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"


def load_recommendations(date_str):
    """從 tracking.json 讀取推薦清單"""
    tracking_file = TRACKING_DIR / f"tracking_{date_str}.json"
    if not tracking_file.exists():
        print(f"❌ tracking_{date_str}.json 不存在", file=sys.stderr)
        return []

    with open(tracking_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    stocks = []
    for rec in data.get("recommendations", []):
        stocks.append({
            "stock_code": rec.get("stock_code"),
            "stock_name": rec.get("stock_name"),
            "industry": rec.get("industry", "未分類"),
            "score": rec.get("score"),
        })
    return stocks


def parse_stocks_arg(stocks_str):
    """解析 --stocks 參數（格式：code:industry,code:industry）"""
    stocks = []
    for item in stocks_str.split(","):
        parts = item.strip().split(":")
        if len(parts) >= 2:
            stocks.append({
                "stock_code": parts[0],
                "stock_name": "",
                "industry": parts[1],
            })
    return stocks


def check_diversification(stocks):
    """檢查產業分散度"""
    total = len(stocks)
    issues = []
    passed = True

    # 規則 1：推薦檔數 6-8
    if total < 6:
        issues.append(f"⚠️ 推薦 {total} 檔，少於 6 檔下限")
    elif total > 8:
        issues.append(f"⚠️ 推薦 {total} 檔，超過 8 檔上限")

    # 統計產業分佈
    industries = Counter(s["industry"] for s in stocks)
    unique_count = len(industries)

    # 規則 2：至少 3 個產業
    if unique_count < 3:
        issues.append(f"🔴 只有 {unique_count} 個產業，需至少 3 個")
        passed = False

    # 規則 3：單一產業 ≤ 50%
    for industry, count in industries.most_common():
        pct = count / total * 100 if total > 0 else 0
        if pct > 50:
            issues.append(f"🔴 {industry} 佔 {count}/{total} ({pct:.0f}%)，超過 50% 上限")
            passed = False

    return {
        "total": total,
        "unique_industries": unique_count,
        "distribution": dict(industries.most_common()),
        "passed": passed and len([i for i in issues if i.startswith("🔴")]) == 0,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser(description="產業分散檢查器")
    parser.add_argument("--date", default=None, help="從 tracking.json 讀取 (YYYY-MM-DD)")
    parser.add_argument("--stocks", default=None, help="直接指定 (code:industry,...)")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    args = parser.parse_args()

    if args.stocks:
        stocks = parse_stocks_arg(args.stocks)
    elif args.date:
        stocks = load_recommendations(args.date)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        stocks = load_recommendations(date_str)

    if not stocks:
        print("❌ 沒有推薦股票可檢查", file=sys.stderr)
        sys.exit(1)

    result = check_diversification(stocks)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        icon = "✅" if result["passed"] else "❌"
        print(f"{icon} 產業分散檢查 — {result['total']} 檔 / {result['unique_industries']} 產業")
        print()

        # 分佈表
        print("產業分佈:")
        total = result["total"]
        for industry, count in result["distribution"].items():
            pct = count / total * 100
            bar = "█" * int(pct / 5)
            print(f"  {industry:12s} {count} 檔 ({pct:4.0f}%) {bar}")

        # 問題
        if result["issues"]:
            print()
            for issue in result["issues"]:
                print(f"  {issue}")

        if result["passed"]:
            print("\n✅ 通過所有規則")
        else:
            print("\n❌ 未通過，請調整推薦組合")


if __name__ == "__main__":
    main()
