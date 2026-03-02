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
            # 兼容兩種格式：top50_buy（舊）或 stocks（新）
            stock_list = data.get('top50_buy', data.get('stocks', []))
            for idx, stock in enumerate(stock_list, 1):
                stocks.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'rank': idx,  # 使用順序作為排名
                    'institutional_total': stock.get('total', stock.get('institutional_total', 0)),
                    'source': 'institutional_top50'
                })
            return stocks
    except FileNotFoundError:
        print(f"警告：找不到 {top50_file}，返回空數據", file=sys.stderr)
        return []


def load_leader_alerts(date_str):
    """
    載入美股龍頭預警（us_leader_alerts.json）

    回傳：
      excluded_codes: set  — Level 3 直接排除的股票代號
      downgraded_codes: dict — Level 2 降級評分 {code: {reason, adjustment}}
      warning_codes: dict  — Level 1 提示注意 {code: {reason, adjustment}}
    """
    alerts_file = project_root / "data" / date_str / "us_leader_alerts.json"
    try:
        with open(alerts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        summary = data.get('summary', {})
        excluded  = set(summary.get('excluded_stocks', []))
        downgraded = summary.get('downgraded_stocks', {})
        warning    = summary.get('warning_stocks', {})
        return excluded, downgraded, warning
    except FileNotFoundError:
        print(f"警告：找不到 {alerts_file}，跳過龍頭預警過濾", file=sys.stderr)
        return set(), {}, {}
    except Exception as e:
        print(f"警告：讀取 us_leader_alerts.json 失敗: {e}", file=sys.stderr)
        return set(), {}, {}


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


def apply_leader_alerts(merged, excluded_codes, downgraded_codes, warning_codes):
    """
    對已合併的候選股套用龍頭預警：
    - Level 3（excluded）：直接移除
    - Level 2（downgraded）：標記 alert_level=2 + score_adjustment
    - Level 1（warning）：標記 alert_level=1 + score_adjustment
    """
    result = []
    removed = []

    for stock in merged:
        code = stock['code']

        if code in excluded_codes:
            removed.append(stock)
            continue  # Level 3：直接排除

        if code in downgraded_codes:
            stock['alert_level'] = 2
            stock['alert_info'] = downgraded_codes[code]
        elif code in warning_codes:
            stock['alert_level'] = 1
            stock['alert_info'] = warning_codes[code]
        else:
            stock['alert_level'] = 0

        result.append(stock)

    return result, removed


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

    # 載入龍頭預警
    print("\n🚨 載入美股龍頭預警...")
    excluded_codes, downgraded_codes, warning_codes = load_leader_alerts(date_str)
    print(f"  Level 3 排除：{len(excluded_codes)} 檔")
    print(f"  Level 2 降級：{len(downgraded_codes)} 檔")
    print(f"  Level 1 提示：{len(warning_codes)} 檔")

    # 合併
    print("\n🔄 合併候選股...")
    merged_raw = merge_candidates(group_a, group_b)

    # 套用龍頭預警（排除 Level 3）
    merged, removed = apply_leader_alerts(merged_raw, excluded_codes, downgraded_codes, warning_codes)

    if removed:
        print(f"\n🚫 Level 3 龍頭預警排除 {len(removed)} 檔：")
        for s in removed:
            print(f"  ✗ {s['name']}({s['code']})")

    # 統計
    dual_confirmed = [s for s in merged if s.get('dual_confirmed')]
    only_institutional = [s for s in merged if s['sources'] == ['institutional_top50']]
    only_catalyst = [s for s in merged if s['sources'] == ['industry_catalyst']]
    alert_l2 = [s for s in merged if s.get('alert_level') == 2]
    alert_l1 = [s for s in merged if s.get('alert_level') == 1]

    print(f"\n  合併前總數：{len(group_a) + len(group_b)} 檔")
    print(f"  去重後總數：{len(merged_raw)} 檔")
    print(f"  排除後總數：{len(merged)} 檔")
    print()
    print(f"  🔥 雙重確認（法人+時事）：{len(dual_confirmed)} 檔")
    print(f"  📊 僅法人 TOP50：{len(only_institutional)} 檔")
    print(f"  🎯 僅時事驅動：{len(only_catalyst)} 檔")
    if alert_l2:
        print(f"  ⚠️  Level 2 降級（-15分）：{len(alert_l2)} 檔")
    if alert_l1:
        print(f"  ℹ️  Level 1 提示（-5分）：{len(alert_l1)} 檔")

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
            "only_catalyst": len(only_catalyst),
            "excluded_by_leader_alert": len(removed),
            "alert_level_2": len(alert_l2),
            "alert_level_1": len(alert_l1)
        },
        "excluded_stocks": [s['code'] for s in removed],
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
