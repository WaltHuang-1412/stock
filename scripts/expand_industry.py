#!/usr/bin/env python3
"""
產業展開工具 - 靈活展開指定產業的所有股票
用法1：python3 expand_industry.py 塑化 --depth 2
用法2：python3 expand_industry.py --stock 1303
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加項目根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_industry_chains():
    """載入產業鏈知識庫"""
    chains_file = project_root / "data" / "industry_chains.json"
    with open(chains_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_stock_industry(stock_code, industry_chains):
    """根據股票代號查詢所屬產業"""
    for industry_key, industry_data in industry_chains["industries"].items():
        tiers = industry_data.get("tiers", {})
        for tier_key, tier_data in tiers.items():
            stocks = tier_data.get("stocks", [])
            for stock in stocks:
                if stock["code"] == stock_code:
                    return industry_key, industry_data["name"], stock["name"]
    return None, None, None


def expand_industry(industry_key, depth, industry_chains):
    """
    展開單一產業

    Args:
        industry_key: 產業代號（如 "塑化"、"AI"）
        depth: 展開深度（0-3）
        industry_chains: 產業鏈知識庫

    Returns:
        股票清單
    """
    if industry_key not in industry_chains["industries"]:
        print(f"❌ 錯誤：產業「{industry_key}」不在知識庫中", file=sys.stderr)
        print(f"\n可用產業清單：", file=sys.stderr)
        for key in industry_chains["industries"].keys():
            name = industry_chains["industries"][key]["name"]
            print(f"  - {key}（{name}）", file=sys.stderr)
        return []

    industry_info = industry_chains["industries"][industry_key]
    tiers = industry_info.get("tiers", {})

    stocks = []
    tier_names = ["tier_0", "tier_1", "tier_2", "tier_3"]

    # 根據深度展開對應的 tier
    for i in range(min(depth + 1, 4)):  # depth=2 展開 tier_0~2
        tier_key = tier_names[i]
        if tier_key in tiers:
            tier_stocks = tiers[tier_key].get("stocks", [])
            for stock in tier_stocks:
                stocks.append({
                    "code": stock["code"],
                    "name": stock["name"],
                    "category": stock.get("category", ""),
                    "tier": tier_key,
                    "tier_name": tiers[tier_key]["name"]
                })

    return stocks


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='產業展開工具')
    parser.add_argument('industry', nargs='?', help='產業名稱（如：塑化、AI、半導體）')
    parser.add_argument('--stock', help='股票代號（自動識別產業）')
    parser.add_argument('--depth', type=int, default=2, help='展開深度（0-3，預設2）')
    parser.add_argument('--date', help='日期（YYYY-MM-DD，預設今日）')

    args = parser.parse_args()

    # 獲取日期
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 載入產業鏈知識庫
    industry_chains = load_industry_chains()

    # 判斷使用方式
    if args.stock:
        # 用法2：基於股票代號
        print(f"🔍 查詢股票產業...")
        industry_key, industry_name, stock_name = find_stock_industry(args.stock, industry_chains)

        if not industry_key:
            print(f"❌ 錯誤：找不到股票 {args.stock}", file=sys.stderr)
            sys.exit(1)

        print(f"  {stock_name}({args.stock}) → {industry_name}")
        print()

    elif args.industry:
        # 用法1：直接指定產業
        industry_key = args.industry
        if industry_key in industry_chains["industries"]:
            industry_name = industry_chains["industries"][industry_key]["name"]
        else:
            print(f"❌ 錯誤：產業「{industry_key}」不在知識庫中", file=sys.stderr)
            print(f"\n可用產業清單：", file=sys.stderr)
            for key in industry_chains["industries"].keys():
                name = industry_chains["industries"][key]["name"]
                print(f"  - {key}（{name}）", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)

    # 展開產業
    print(f"📊 展開產業：{industry_name}（Tier 0-{args.depth}）")
    print("=" * 60)

    stocks = expand_industry(industry_key, args.depth, industry_chains)

    if not stocks:
        print(f"⚠️  產業「{industry_key}」無股票資料")
        sys.exit(0)

    # 按 tier 分組顯示
    tier_groups = {}
    for stock in stocks:
        tier = stock["tier"]
        if tier not in tier_groups:
            tier_groups[tier] = []
        tier_groups[tier].append(stock)

    all_codes = []
    for tier in ["tier_0", "tier_1", "tier_2", "tier_3"]:
        if tier in tier_groups:
            tier_stocks = tier_groups[tier]
            tier_name = tier_stocks[0]["tier_name"]
            print(f"\n{tier.upper()}（{tier_name}）：")
            for stock in tier_stocks:
                print(f"  {stock['code']} {stock['name']}（{stock['category']}）")
                all_codes.append(stock['code'])

    print()
    print(f"總計：{len(stocks)} 檔")
    print()

    # 保存股票代號清單
    output_dir = project_root / "data" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    codes_file = output_dir / "industry_stock_codes.txt"
    with open(codes_file, 'w', encoding='utf-8') as f:
        for code in all_codes:
            f.write(f"{code}\n")

    # 保存完整的 JSON（供 merge_candidates.py 使用）
    industry_json_file = output_dir / f"industry_{industry_key}.json"
    industry_data = {
        "industry_key": industry_key,
        "industry_name": industry_name,
        "depth": args.depth,
        "date": date_str,
        "total_stocks": len(stocks),
        "stocks": stocks
    }
    with open(industry_json_file, 'w', encoding='utf-8') as f:
        json.dump(industry_data, f, ensure_ascii=False, indent=2)

    # 累加到總 JSON（多次執行會累積）
    expanded_stocks_file = output_dir / "industry_expanded_stocks.json"
    if expanded_stocks_file.exists():
        with open(expanded_stocks_file, 'r', encoding='utf-8') as f:
            all_expanded = json.load(f)
    else:
        all_expanded = {
            "date": date_str,
            "industries": [],
            "total_stocks": 0,
            "stocks": []
        }

    # 更新產業清單（避免重複）
    existing_industries = [ind["industry_key"] for ind in all_expanded["industries"]]
    if industry_key not in existing_industries:
        all_expanded["industries"].append({
            "industry_key": industry_key,
            "industry_name": industry_name,
            "depth": args.depth,
            "stock_count": len(stocks)
        })

    # 更新股票清單（去重）
    existing_codes = [s["code"] for s in all_expanded["stocks"]]
    for stock in stocks:
        if stock["code"] not in existing_codes:
            all_expanded["stocks"].append(stock)
            existing_codes.append(stock["code"])

    all_expanded["total_stocks"] = len(all_expanded["stocks"])

    with open(expanded_stocks_file, 'w', encoding='utf-8') as f:
        json.dump(all_expanded, f, ensure_ascii=False, indent=2)

    print(f"💾 已保存：{codes_file}")
    print(f"💾 已保存：{industry_json_file}")
    print(f"💾 已更新：{expanded_stocks_file}（總計 {all_expanded['total_stocks']} 檔）")
    print()
    print("=" * 60)
    print("📋 接下來可執行：")
    print(f"   python3 scripts/chip_analysis.py {' '.join(all_codes)} --days 10")
    print()


if __name__ == "__main__":
    main()
