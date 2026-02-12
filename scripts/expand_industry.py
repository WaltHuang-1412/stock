#!/usr/bin/env python3
"""
產業展開工具 - 靈活展開指定產業的所有股票
用法1：python3 expand_industry.py 塑化 --depth 2
用法2：python3 expand_industry.py --stock 1303
用法3：python3 expand_industry.py 塑化 --auto（自動判斷深度）🆕 v2.0
"""

import json
import sys
import io
import argparse
from pathlib import Path
from datetime import datetime
import os

# Windows 環境 stdout 編碼修正（避免 emoji 輸出時 cp950 報錯）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加項目根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_industry_chains():
    """載入產業鏈知識庫"""
    chains_file = project_root / "data" / "industry_chains.json"
    with open(chains_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_us_market_data(date_str):
    """
    讀取美股市場數據

    Args:
        date_str: 日期（YYYY-MM-DD）

    Returns:
        美股數據字典（key=指標名稱, value=漲跌幅）
    """
    data_dir = project_root / "data" / date_str
    json_file = data_dir / "us_asia_markets.json"

    if not json_file.exists():
        print(f"⚠️  找不到美股數據：{json_file}", file=sys.stderr)
        print(f"   請先執行：python scripts/fetch_us_asia_markets.py --output-dir data/{date_str}", file=sys.stderr)
        return {}

    # 讀取檔案內容（可能包含混合格式：終端輸出 + JSON）
    with open(json_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 嘗試直接解析 JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # 如果失敗，嘗試提取 JSON 部分（從第一個 { 到最後一個 }）
        json_start = content.find('{')
        json_end = content.rfind('}')
        if json_start != -1 and json_end != -1:
            json_content = content[json_start:json_end + 1]
            data = json.loads(json_content)
        else:
            print(f"❌ 無法從檔案中提取 JSON：{json_file}", file=sys.stderr)
            return {}

    return data


def determine_depth_auto(industry_key, us_market_data, industry_chains):
    """
    根據催化劑強度自動判斷深度

    Args:
        industry_key: 產業代號（如 "塑化"、"AI"）
        us_market_data: 美股數據字典
        industry_chains: 產業鏈知識庫

    Returns:
        depth (0-3) 和 catalyst_info（催化資訊）
    """
    if industry_key not in industry_chains["industries"]:
        return 2, None  # 找不到產業，預設 depth 2

    industry_info = industry_chains["industries"][industry_key]
    catalysts = industry_info.get("catalysts", [])

    if not catalysts or not us_market_data:
        return 2, None  # 沒有催化劑資訊或美股數據，預設 depth 2

    # 找出最大變化幅度的催化劑
    max_change = 0
    max_catalyst = None
    max_value = 0

    for catalyst in catalysts:
        if catalyst in us_market_data:
            change = abs(us_market_data[catalyst])
            if change > max_change:
                max_change = change
                max_catalyst = catalyst
                max_value = us_market_data[catalyst]

    # 根據變化幅度判斷深度
    if max_change >= 5:
        depth = 3  # 強烈催化（> ±5%）
        strength = "強烈"
    elif max_change >= 2:
        depth = 2  # 中等催化（±2% ~ ±5%）
        strength = "中等"
    elif max_change >= 0.5:
        depth = 1  # 微弱催化（±0.5% ~ ±2%）
        strength = "微弱"
    else:
        depth = 0  # 幾乎無催化（< ±0.5%）
        strength = "幾乎無"

    catalyst_info = {
        "catalyst": max_catalyst,
        "value": max_value,
        "abs_change": max_change,
        "strength": strength,
        "depth": depth
    }

    return depth, catalyst_info


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
    parser = argparse.ArgumentParser(description='產業展開工具 v2.0（支援自動判斷深度）')
    parser.add_argument('industry', nargs='?', help='產業名稱（如：塑化、AI、半導體）')
    parser.add_argument('--stock', help='股票代號（自動識別產業）')
    parser.add_argument('--depth', type=int, default=None, help='展開深度（0-3），如不指定則預設2，如使用 --auto 則自動判斷')
    parser.add_argument('--auto', action='store_true', help='自動判斷深度（根據美股數據）🆕')
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

    # 決定深度（手動 or 自動）
    catalyst_info = None
    if args.auto:
        # 自動判斷深度
        print(f"🤖 自動判斷深度模式（根據美股數據）")
        print("=" * 60)

        # 載入美股數據
        us_market_data = load_us_market_data(date_str)

        if not us_market_data:
            print(f"⚠️  無法載入美股數據，使用預設深度 2", file=sys.stderr)
            depth = 2
        else:
            # 自動判斷深度
            depth, catalyst_info = determine_depth_auto(industry_key, us_market_data, industry_chains)

            if catalyst_info:
                print(f"✅ 催化劑：{catalyst_info['catalyst']} ({catalyst_info['value']:+.2f}%)")
                print(f"✅ 催化強度：{catalyst_info['strength']}（絕對值 {catalyst_info['abs_change']:.2f}%）")
                print(f"✅ 自動深度：{depth}")
            else:
                print(f"⚠️  找不到催化劑資訊，使用預設深度 2")
                depth = 2

        print("=" * 60)
        print()
    else:
        # 手動指定深度
        depth = args.depth if args.depth is not None else 2

    # 展開產業
    print(f"📊 展開產業：{industry_name}（Tier 0-{depth}）")
    print("=" * 60)

    stocks = expand_industry(industry_key, depth, industry_chains)

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
        "depth": depth,
        "auto_mode": args.auto,
        "date": date_str,
        "total_stocks": len(stocks),
        "stocks": stocks
    }

    # 如果有催化劑資訊，加入 JSON
    if catalyst_info:
        industry_data["catalyst_info"] = catalyst_info

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
        industry_entry = {
            "industry_key": industry_key,
            "industry_name": industry_name,
            "depth": depth,
            "auto_mode": args.auto,
            "stock_count": len(stocks)
        }
        # 如果有催化劑資訊，加入
        if catalyst_info:
            industry_entry["catalyst"] = catalyst_info["catalyst"]
            industry_entry["catalyst_change"] = catalyst_info["value"]
            industry_entry["catalyst_strength"] = catalyst_info["strength"]

        all_expanded["industries"].append(industry_entry)

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
