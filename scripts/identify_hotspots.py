#!/usr/bin/env python3
"""
時事識別引擎 - 自動識別今日熱點產業
輸入：美股數據 + 台股新聞
輸出：熱點產業清單 + 催化強度
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_industry_chains():
    """載入產業鏈知識庫"""
    chains_file = project_root / "data" / "industry_chains.json"
    with open(chains_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_us_asia_markets(date_str):
    """載入美股/亞股數據"""
    market_file = project_root / "data" / date_str / "us_asia_markets.json"
    try:
        with open(market_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"警告：找不到 {market_file}，返回空數據", file=sys.stderr)
        return {}


def load_tw_news(date_str):
    """載入台股新聞"""
    news_file = project_root / "data" / date_str / "tw_market_news.json"
    try:
        # 嘗試多種編碼
        for encoding in ['utf-8', 'utf-8-sig', 'cp950', 'gbk']:
            try:
                with open(news_file, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    return data
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

        # 如果所有編碼都失敗，返回空數據
        print(f"警告：無法解析 {news_file}，返回空數據", file=sys.stderr)
        return []
    except FileNotFoundError:
        print(f"警告：找不到 {news_file}，返回空數據", file=sys.stderr)
        return []


def identify_from_us_markets(markets_data, industry_chains):
    """從美股數據識別熱點（動態讀取 industry_chains.json 的 us_market_signals）"""
    hotspots = {}  # industry_key -> best triggered signal

    for industry_key, industry_info in industry_chains["industries"].items():
        signals = industry_info.get("us_market_signals", [])
        if not signals:
            continue

        best_change = 0
        best_catalyst = ""

        for sig in signals:
            indicator = sig["indicator"]
            threshold = sig["threshold"]
            direction = sig["direction"]
            strength_high = sig.get("strength_high", threshold * 2)

            raw = markets_data.get(indicator, 0)
            if raw is None:
                continue

            # 方向判斷：positive = 漲觸發，negative = 跌觸發
            if direction == "positive":
                triggered = raw >= threshold
                effective = raw
                label = f"{indicator}{raw:+.2f}%"
            else:
                triggered = raw <= -threshold
                effective = abs(raw)
                label = f"{indicator}{raw:+.2f}%（利多{industry_info['name']}）"

            if not triggered:
                continue

            if effective > best_change:
                best_change = effective
                best_catalyst = label
                best_strength_high = strength_high

        if best_catalyst:
            strength = "strong" if best_change >= best_strength_high else "medium"
            hotspots[industry_key] = {
                "industry": industry_key,
                "catalyst": best_catalyst,
                "strength": strength,
                "change": best_change,
            }

    return list(hotspots.values())


def identify_from_tw_news(news_data, industry_chains):
    """從台股新聞識別熱點"""
    hotspots = []

    if not news_data:
        return hotspots

    # 遍歷所有產業，檢查新聞關鍵字
    for industry_key, industry_info in industry_chains["industries"].items():
        catalysts = industry_info.get("catalysts", [])

        # 檢查新聞中是否包含產業關鍵字
        matched_news = []
        for news_item in news_data:
            if isinstance(news_item, dict):
                title = news_item.get("title", "")
                content = news_item.get("content", "")
            else:
                title = str(news_item)
                content = ""

            # 檢查是否匹配任何催化劑關鍵字
            for catalyst in catalysts:
                if catalyst in title or catalyst in content:
                    matched_news.append(title)
                    break

        # 如果有匹配的新聞，加入熱點
        if matched_news:
            # 根據新聞數量判斷強度
            if len(matched_news) >= 3:
                strength = "strong"
            elif len(matched_news) >= 2:
                strength = "medium"
            else:
                strength = "weak"

            hotspots.append({
                "industry": industry_key,
                "catalyst": f"{industry_info['name']}相關新聞 × {len(matched_news)}",
                "strength": strength,
                "news": matched_news[:2]  # 只保留前2條新聞
            })

    return hotspots


def merge_and_deduplicate(us_hotspots, tw_hotspots):
    """合併並去重熱點"""
    merged = {}

    # 先加入美股熱點（優先）
    for hotspot in us_hotspots:
        industry = hotspot["industry"]
        merged[industry] = hotspot

    # 加入台股新聞熱點
    for hotspot in tw_hotspots:
        industry = hotspot["industry"]
        if industry in merged:
            # 已存在：提升強度
            if hotspot["strength"] == "strong":
                merged[industry]["strength"] = "strong"
            merged[industry]["catalyst"] += f" + {hotspot['catalyst']}"
        else:
            # 新產業
            merged[industry] = hotspot

    # 轉回列表並排序（strong > medium > weak）
    strength_order = {"strong": 3, "medium": 2, "weak": 1}
    result = sorted(
        merged.values(),
        key=lambda x: strength_order[x["strength"]],
        reverse=True
    )

    return result


def main():
    """主函數"""
    # 獲取日期參數
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"🔍 時事識別引擎 - {date_str}")
    print("=" * 60)

    # 載入數據
    print("\n📥 載入數據...")
    industry_chains = load_industry_chains()
    us_markets = load_us_asia_markets(date_str)
    tw_news = load_tw_news(date_str)

    print(f"  ✓ 產業鏈知識庫：{len(industry_chains['industries'])} 個產業")
    print(f"  ✓ 美股數據：{len(us_markets)} 個指標")
    print(f"  ✓ 台股新聞：{len(tw_news) if tw_news else 0} 則")

    # 識別熱點
    print("\n🎯 識別熱點產業...")
    us_hotspots = identify_from_us_markets(us_markets, industry_chains)
    tw_hotspots = identify_from_tw_news(tw_news, industry_chains)

    print(f"  ✓ 美股觸發：{len(us_hotspots)} 個產業")
    print(f"  ✓ 新聞觸發：{len(tw_hotspots)} 個產業")

    # 合併去重
    final_hotspots = merge_and_deduplicate(us_hotspots, tw_hotspots)

    print(f"\n🔥 最終熱點：{len(final_hotspots)} 個產業")
    print("=" * 60)

    # 輸出結果
    if not final_hotspots:
        print("\n⚠️  今日無明確熱點，建議依法人 TOP50 為主")
        return

    for i, hotspot in enumerate(final_hotspots, 1):
        industry_info = industry_chains["industries"][hotspot["industry"]]

        # 強度圖示
        if hotspot["strength"] == "strong":
            strength_icon = "🔴"
            depth = 3
        elif hotspot["strength"] == "medium":
            strength_icon = "🟡"
            depth = 2
        else:
            strength_icon = "⚪"
            depth = 1

        print(f"\n{i}. {strength_icon} {industry_info['name']} ({hotspot['industry']})")
        print(f"   催化劑：{hotspot['catalyst']}")
        print(f"   強度：{hotspot['strength']} → 建議展開深度 Tier 0-{depth}")

        # 顯示新聞（如果有）
        if "news" in hotspot:
            print(f"   相關新聞：")
            for news in hotspot["news"]:
                print(f"     - {news}")

    # 輸出 JSON 格式（供下一步使用）
    output = {
        "date": date_str,
        "hotspots": final_hotspots,
        "summary": {
            "total": len(final_hotspots),
            "strong": sum(1 for h in final_hotspots if h["strength"] == "strong"),
            "medium": sum(1 for h in final_hotspots if h["strength"] == "medium"),
            "weak": sum(1 for h in final_hotspots if h["strength"] == "weak")
        }
    }

    # 保存結果
    output_file = project_root / "data" / date_str / "hotspots.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 結果已保存：{output_file}")
    print("\n" + "=" * 60)
    print("✅ 完成！接下來執行 dynamic_industry_expander.py 展開產業鏈")


if __name__ == "__main__":
    main()
