#!/usr/bin/env python3
"""
動態產業展開器 - 根據熱點產業和催化強度展開產業鏈
輸入：hotspots.json（熱點產業清單）
輸出：候選股票清單
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 添加項目根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_industry_chains():
    """載入產業鏈知識庫"""
    chains_file = project_root / "data" / "industry_chains.json"
    with open(chains_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_hotspots(date_str):
    """載入熱點產業"""
    hotspots_file = project_root / "data" / date_str / "hotspots.json"
    try:
        with open(hotspots_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到 {hotspots_file}", file=sys.stderr)
        print("請先執行：python3 scripts/identify_hotspots.py", file=sys.stderr)
        sys.exit(1)


def expand_industry_chain(industry_key, depth, industry_chains):
    """
    展開單一產業鏈

    Args:
        industry_key: 產業代號（如 "AI"、"衛星通訊"）
        depth: 展開深度（1-3）
        industry_chains: 產業鏈知識庫

    Returns:
        股票清單
    """
    if industry_key not in industry_chains["industries"]:
        print(f"  ⚠️  警告：產業 {industry_key} 不在知識庫中", file=sys.stderr)
        return []

    industry_info = industry_chains["industries"][industry_key]
    tiers = industry_info.get("tiers", {})

    stocks = []
    tier_names = ["tier_0", "tier_1", "tier_2", "tier_3"]

    # 根據深度展開對應的 tier
    for i in range(min(depth + 1, 4)):  # depth=3 展開 tier_0~3
        tier_key = tier_names[i]
        if tier_key in tiers:
            tier_stocks = tiers[tier_key].get("stocks", [])
            for stock in tier_stocks:
                stocks.append({
                    **stock,
                    "industry": industry_key,
                    "industry_name": industry_info["name"],
                    "tier": tier_key,
                    "tier_name": tiers[tier_key]["name"]
                })

    return stocks


def main():
    """主函數"""
    # 獲取日期參數
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"🚀 動態產業展開器 - {date_str}")
    print("=" * 60)

    # 載入數據
    print("\n📥 載入數據...")
    industry_chains = load_industry_chains()
    hotspots_data = load_hotspots(date_str)

    hotspots = hotspots_data.get("hotspots", [])
    print(f"  ✓ 產業鏈知識庫：{len(industry_chains['industries'])} 個產業")
    print(f"  ✓ 今日熱點：{len(hotspots)} 個產業")

    if not hotspots:
        print("\n⚠️  今日無熱點，無需展開產業鏈")
        return

    # 展開產業鏈
    print("\n📊 展開產業鏈...")
    all_stocks = []
    industry_stats = {}

    for i, hotspot in enumerate(hotspots, 1):
        industry_key = hotspot["industry"]
        strength = hotspot["strength"]
        catalyst = hotspot["catalyst"]

        # 根據強度決定深度
        if strength == "strong":
            depth = 3  # Tier 0-3
        elif strength == "medium":
            depth = 2  # Tier 0-2
        else:
            depth = 1  # Tier 0-1

        print(f"\n{i}. {industry_key}（{strength}）")
        print(f"   催化劑：{catalyst}")
        print(f"   展開深度：Tier 0-{depth}")

        # 展開產業鏈
        stocks = expand_industry_chain(industry_key, depth, industry_chains)
        all_stocks.extend(stocks)

        industry_stats[industry_key] = {
            "total": len(stocks),
            "depth": depth,
            "strength": strength,
            "catalyst": catalyst
        }

        print(f"   股票數：{len(stocks)} 檔")

        # 顯示各 Tier 的股票數
        tier_count = defaultdict(int)
        for stock in stocks:
            tier_count[stock["tier"]] += 1

        for tier in sorted(tier_count.keys()):
            print(f"     - {tier}: {tier_count[tier]} 檔")

    # 去重（同一股票可能出現在多個產業）
    print(f"\n🔄 合併去重...")
    print(f"  展開前：{len(all_stocks)} 檔（含重複）")

    # 去重：使用 dict 以 code 為鍵
    unique_stocks = {}
    for stock in all_stocks:
        code = stock["code"]
        if code not in unique_stocks:
            unique_stocks[code] = stock
            unique_stocks[code]["industries"] = [stock["industry"]]
        else:
            # 股票已存在，記錄多產業
            if stock["industry"] not in unique_stocks[code]["industries"]:
                unique_stocks[code]["industries"].append(stock["industry"])

    stocks_list = list(unique_stocks.values())
    print(f"  去重後：{len(stocks_list)} 檔")

    # 按產業分組統計
    print("\n📊 產業分布：")
    industry_stock_count = defaultdict(int)
    for stock in stocks_list:
        for industry in stock["industries"]:
            industry_stock_count[industry] += 1

    for industry_key, count in sorted(industry_stock_count.items(), key=lambda x: x[1], reverse=True):
        industry_name = industry_chains["industries"][industry_key]["name"]
        print(f"  - {industry_name}（{industry_key}）：{count} 檔")

    # 標記多產業股票（交叉受惠）
    multi_industry_stocks = [s for s in stocks_list if len(s["industries"]) > 1]
    if multi_industry_stocks:
        print(f"\n🔗 多產業交叉股票：{len(multi_industry_stocks)} 檔")
        for stock in multi_industry_stocks[:10]:  # 只顯示前10檔
            industries_str = " + ".join([
                industry_chains["industries"][ind]["name"]
                for ind in stock["industries"]
            ])
            print(f"  - {stock['name']}({stock['code']})：{industries_str}")

    # 輸出結果
    output = {
        "date": date_str,
        "hotspots_summary": hotspots_data.get("summary", {}),
        "industry_stats": industry_stats,
        "total_stocks": len(stocks_list),
        "multi_industry_count": len(multi_industry_stocks),
        "stocks": stocks_list
    }

    # 保存結果
    output_file = project_root / "data" / date_str / "industry_expanded_stocks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 結果已保存：{output_file}")

    # 輸出股票代號清單（供 chip_analysis.py 使用）
    codes_file = project_root / "data" / date_str / "industry_stock_codes.txt"
    with open(codes_file, 'w', encoding='utf-8') as f:
        for stock in stocks_list:
            f.write(f"{stock['code']}\n")

    print(f"💾 股票代號清單：{codes_file}")

    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("\n📋 接下來可執行：")
    print(f"   python3 scripts/chip_analysis.py $(cat data/{date_str}/industry_stock_codes.txt | tr '\\n' ' ') --days 10")


if __name__ == "__main__":
    main()
