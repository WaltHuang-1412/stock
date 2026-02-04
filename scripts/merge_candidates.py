#!/usr/bin/env python3
"""
候選股合併器 - 雙軌並行系統
合併法人 TOP50（A組）和時事驅動產業展開（B組）的候選股
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 添加項目根目錄到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_institutional_top50(date_str):
    """載入法人 TOP50 數據"""
    top50_file = project_root / "data" / date_str / "institutional_top50.json"
    try:
        with open(top50_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            stocks = []
            for stock in data.get('top50_buy', []):
                stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'rank': stock.get('rank', 999),
                    'institutional_total': stock.get('institutional_total', 0),
                    'source': 'institutional_top50'
                })
            return stocks
    except FileNotFoundError:
        print(f"警告：找不到 {top50_file}，返回空數據", file=sys.stderr)
        return []


def load_industry_expanded_stocks(date_str):
    """載入時事驅動產業展開的股票"""
    stocks_file = project_root / "data" / date_str / "industry_expanded_stocks.json"
    try:
        with open(stocks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('stocks', [])
    except FileNotFoundError:
        print(f"警告：找不到 {stocks_file}，返回空數據", file=sys.stderr)
        return []


def merge_candidates(group_a, group_b):
    """
    合併兩組候選股

    Args:
        group_a: 法人 TOP50 候選股列表
        group_b: 時事驅動產業展開候選股列表

    Returns:
        合併後的候選股列表，包含來源標記
    """
    merged = {}

    # 處理 A 組（法人 TOP50）
    for stock in group_a:
        code = stock['code']
        merged[code] = {
            **stock,
            'sources': ['institutional_top50'],
            'priority': 'high' if stock.get('rank', 100) <= 20 else 'medium'
        }

    # 處理 B 組（時事驅動）
    for stock in group_b:
        code = stock['code']
        if code in merged:
            # 已存在：標記為雙重確認
            merged[code]['sources'].append('industry_catalyst')
            merged[code]['dual_confirmed'] = True
            merged[code]['priority'] = 'very_high'  # 雙重確認提升優先級

            # 記錄產業催化資訊
            merged[code]['catalyst_industries'] = stock.get('industries', [])
        else:
            # 新股票
            merged[code] = {
                **stock,
                'sources': ['industry_catalyst'],
                'dual_confirmed': False,
                'priority': 'medium'
            }

    # 轉回列表並排序（雙重確認優先）
    result = sorted(
        merged.values(),
        key=lambda x: (
            0 if x.get('dual_confirmed') else 1,  # 雙重確認排最前
            {'very_high': 0, 'high': 1, 'medium': 2, 'low': 3}[x.get('priority', 'medium')]
        )
    )

    return result


def main():
    """主函數"""
    # 獲取日期參數
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"🔄 候選股合併器 v3.1 - {date_str}")
    print("=" * 60)

    # 載入數據
    print("\n📥 載入數據...")

    # A 組：法人 TOP50
    group_a = load_institutional_top50(date_str)
    print(f"  ✓ A組（法人 TOP50）：{len(group_a)} 檔")

    # B 組：時事驅動產業展開
    group_b = load_industry_expanded_stocks(date_str)
    print(f"  ✓ B組（時事驅動）：{len(group_b)} 檔")

    # 合併
    print("\n🔄 合併候選股...")
    merged = merge_candidates(group_a, group_b)

    # 統計
    dual_confirmed = [s for s in merged if s.get('dual_confirmed')]
    only_institutional = [s for s in merged if s['sources'] == ['institutional_top50']]
    only_catalyst = [s for s in merged if s['sources'] == ['industry_catalyst']]

    print(f"  合併前總數：{len(group_a) + len(group_b)} 檔")
    print(f"  去重後總數：{len(merged)} 檔")
    print()
    print(f"  🔥 雙重確認（法人+時事）：{len(dual_confirmed)} 檔")
    print(f"  📊 僅法人 TOP50：{len(only_institutional)} 檔")
    print(f"  🎯 僅時事驅動：{len(only_catalyst)} 檔")

    # 輸出雙重確認股票
    if dual_confirmed:
        print("\n🔥 雙重確認股票（優先推薦）：")
        for stock in dual_confirmed[:10]:  # 只顯示前10檔
            industries_str = ""
            if 'catalyst_industries' in stock:
                industries_str = f" - 產業催化：{', '.join(stock['catalyst_industries'])}"
            print(f"  ⭐ {stock['name']}({stock['code']}){industries_str}")

    # 保存結果
    output = {
        "date": date_str,
        "summary": {
            "total": len(merged),
            "dual_confirmed": len(dual_confirmed),
            "only_institutional": len(only_institutional),
            "only_catalyst": len(only_catalyst)
        },
        "dual_confirmed_stocks": [s['code'] for s in dual_confirmed],
        "all_candidates": merged
    }

    output_file = project_root / "data" / date_str / "merged_candidates.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 結果已保存：{output_file}")

    # 輸出股票代號清單（供 Step 7 評分使用）
    codes_file = project_root / "data" / date_str / "merged_stock_codes.txt"
    with open(codes_file, 'w', encoding='utf-8') as f:
        for stock in merged:
            f.write(f"{stock['code']}\n")

    print(f"💾 股票代號清單：{codes_file}")

    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("\n📋 接下來進入 Step 7：五維度評分")
    print(f"   - 優先評分：{len(dual_confirmed)} 檔雙重確認股票")
    print(f"   - 全部候選：{len(merged)} 檔")


if __name__ == "__main__":
    main()
