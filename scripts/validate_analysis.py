#!/usr/bin/env python3
"""
分析完整性驗證工具

功能：
- 驗證盤前/盤中/盤後分析是否符合v5.7規範
- 檢查推薦數量、產業分散、檔案完整性
- 不符合規範 → 禁止commit

使用方式：
    python3 scripts/validate_analysis.py before_market 2026-01-21
    python3 scripts/validate_analysis.py intraday 2026-01-21
    python3 scripts/validate_analysis.py after_market 2026-01-21

返回值：
    0 = 驗證通過
    1 = 驗證失敗
"""

import sys
import json
import os
from datetime import datetime

def validate_before_market(date_str):
    """驗證盤前分析完整性（v5.7規範）"""
    errors = []
    warnings = []

    # 1. 檢查檔案存在
    md_file = f"data/{date_str}/before_market_analysis.md"
    json_file = f"data/tracking/tracking_{date_str}.json"

    if not os.path.exists(md_file):
        errors.append(f"❌ 盤前分析檔案不存在: {md_file}")
    if not os.path.exists(json_file):
        errors.append(f"❌ tracking檔案不存在: {json_file}")
        return errors, warnings  # 無法繼續驗證

    # 2. 檢查 tracking.json 內容
    with open(json_file, 'r', encoding='utf-8') as f:
        tracking = json.load(f)

    # 2.1 檢查推薦數量
    recs = tracking.get('recommendations', [])
    if len(recs) < 6:
        errors.append(f"❌ 推薦數量不足: {len(recs)}檔（應為 6-8檔）")
    elif len(recs) > 8:
        warnings.append(f"⚠️  推薦數量過多: {len(recs)}檔（建議 6-8檔）")

    # 2.2 檢查產業分散（動態：直接讀取 industry 欄位，不硬編碼產業清單）
    industries = {}
    missing_industry = 0
    for rec in recs:
        industry = rec.get('industry', '')
        if industry:
            industries[industry] = industries.get(industry, 0) + 1
        else:
            missing_industry += 1
            industries['未分類'] = industries.get('未分類', 0) + 1

    if missing_industry > 0:
        warnings.append(f"⚠️  {missing_industry} 檔推薦缺少 industry 欄位（tracking.json 每檔應包含 industry）")

    if len(industries) < 4:
        errors.append(f"❌ 產業數量不足: {len(industries)}個（應至少4個）")
        errors.append(f"   目前產業: {', '.join(industries.keys())}")

    for ind, count in industries.items():
        ratio = count / len(recs)
        if ratio > 0.5:
            errors.append(f"❌ 產業過度集中: {ind} 佔比{ratio*100:.0f}%（應≤50%）")

    # 2.3 檢查每檔推薦股是否有必要欄位
    for rec in recs:
        stock_name = rec.get('stock_name', '未知')
        if 'score' not in rec:
            errors.append(f"❌ {stock_name} 缺少評分")
        if 'reason' not in rec:
            errors.append(f"❌ {stock_name} 缺少推薦理由")
        if 'recommend_price' not in rec:
            warnings.append(f"⚠️  {stock_name} 缺少推薦價格")

    # 2.4 檢查強制步驟（讀取 MD 檔案內容檢查）
    if os.path.exists(md_file):
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Step 1: 歷史驗證（強制）
        has_verification = ('昨日推薦驗證' in md_content or
                           '準確率' in md_content or
                           '推薦績效' in md_content or
                           '歷史驗證' in md_content)
        if not has_verification:
            errors.append(f"❌ 缺少歷史驗證（強制）")

        # Module A: 催化預埋掃描（強制）
        has_module_a = ('催化預埋掃描' in md_content or
                       'Module A' in md_content or
                       'L3 佈局完成' in md_content)
        if not has_module_a:
            errors.append(f"❌ 缺少 Module A 催化預埋掃描段落（強制）")
            errors.append(f"   報告必須包含獨立的 Module A 段落，列出 L3/L2/L1/追高排除結果")

        # Module B: 催化主題預警（強制）
        has_module_b = ('催化主題預警' in md_content or
                       'Module B' in md_content)
        if not has_module_b:
            errors.append(f"❌ 缺少 Module B 催化主題預警段落（強制）")
            errors.append(f"   報告必須包含獨立的 Module B 段落，逐檔列出篩選結果")

        # 籌碼深度分析（強制）
        has_chip_analysis = ('籌碼深度分析' in md_content or
                            '反轉預警' in md_content or
                            '近10日法人' in md_content)
        if not has_chip_analysis:
            errors.append(f"❌ 缺少籌碼深度分析（強制）")

    return errors, warnings

def validate_intraday(date_str):
    """驗證盤中分析完整性"""
    errors = []
    warnings = []

    md_file = f"data/{date_str}/intraday_analysis.md"
    if not os.path.exists(md_file):
        errors.append(f"❌ 盤中分析檔案不存在: {md_file}")
        return errors, warnings

    # 檢查內容包含Track A和Track B
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'Track A' not in content and 'track a' not in content.lower():
        errors.append(f"❌ 缺少 Track A 分析")
    if 'Track B' not in content and 'track b' not in content.lower():
        errors.append(f"❌ 缺少 Track B 分析")
    if '尾盤策略' not in content and '尾盤' not in content:
        warnings.append(f"⚠️  缺少尾盤策略")

    # 檢查tracking.json是否有更新盤中價格
    tracking_file = f"data/tracking/tracking_{date_str}.json"
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r', encoding='utf-8') as f:
            tracking = json.load(f)

        # 這裡可以擴充檢查盤中價格是否更新
        # （目前盤中不一定更新tracking，所以只檢查檔案存在）

    return errors, warnings

def validate_after_market(date_str):
    """驗證盤後分析完整性"""
    errors = []
    warnings = []

    # 檢查檔案
    md_file = f"data/{date_str}/after_market_analysis.md"
    tracking_file = f"data/tracking/tracking_{date_str}.json"
    predictions_file = "data/predictions/predictions.json"

    if not os.path.exists(md_file):
        errors.append(f"❌ 盤後分析檔案不存在: {md_file}")
    if not os.path.exists(tracking_file):
        errors.append(f"❌ tracking檔案不存在: {tracking_file}")
    if not os.path.exists(predictions_file):
        errors.append(f"❌ predictions檔案不存在: {predictions_file}")

    if not os.path.exists(tracking_file):
        return errors, warnings  # 無法繼續驗證

    # 檢查tracking是否更新了收盤價和結果
    with open(tracking_file, 'r', encoding='utf-8') as f:
        tracking = json.load(f)

    recs = tracking.get('recommendations', [])
    for rec in recs:
        stock_name = rec.get('stock_name', '未知')
        if 'close_price' not in rec and 'current_price' not in rec:
            errors.append(f"❌ {stock_name} 缺少收盤價")
        if 'result' not in rec:
            errors.append(f"❌ {stock_name} 缺少驗證結果（success/fail）")
        if 'change_percent' not in rec:
            warnings.append(f"⚠️  {stock_name} 缺少漲跌幅")

    # 檢查是否有準確率計算
    yesterday_verification = tracking.get('yesterday_verification', {})
    if not yesterday_verification:
        errors.append(f"❌ 缺少 yesterday_verification 準確率統計")
    else:
        if 'accuracy' not in yesterday_verification:
            errors.append(f"❌ 缺少準確率計算")
        if 'results' not in yesterday_verification or not yesterday_verification['results']:
            errors.append(f"❌ 缺少推薦股驗證結果明細")

    # 檢查predictions.json是否有今日記錄
    if os.path.exists(predictions_file):
        with open(predictions_file, 'r', encoding='utf-8') as f:
            predictions = json.load(f)

        if date_str not in predictions:
            warnings.append(f"⚠️  predictions.json 缺少 {date_str} 記錄")

    return errors, warnings

def print_validation_result(phase, date_str, errors, warnings):
    """輸出驗證結果"""
    print(f"\n{'='*60}")
    print(f"🔍 驗證 {date_str} {phase} 分析完整性")
    print(f"{'='*60}\n")

    if errors:
        print("❌ 發現錯誤：\n")
        for error in errors:
            print(f"  {error}")

    if warnings:
        print("\n⚠️  警告：\n")
        for warning in warnings:
            print(f"  {warning}")

    if errors:
        print(f"\n{'='*60}")
        print("🚨 分析不完整，請修正後再commit")
        print(f"{'='*60}\n")
        return False
    elif warnings:
        print(f"\n{'='*60}")
        print("⚠️  通過驗證但有警告，建議修正")
        print(f"{'='*60}\n")
        return True
    else:
        print("\n✅ 驗證通過！所有檢查項目符合規範\n")
        print(f"{'='*60}")
        print("✅ 可以 commit")
        print(f"{'='*60}\n")
        return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("使用方式: python3 scripts/validate_analysis.py [phase] [date]")
        print("範例: python3 scripts/validate_analysis.py before_market 2026-01-21")
        print("\nphase 可以是:")
        print("  - before_market  (盤前分析)")
        print("  - intraday       (盤中分析)")
        print("  - after_market   (盤後分析)")
        sys.exit(1)

    phase = sys.argv[1]
    date_str = sys.argv[2]

    if phase == 'before_market':
        errors, warnings = validate_before_market(date_str)
    elif phase == 'intraday':
        errors, warnings = validate_intraday(date_str)
    elif phase == 'after_market':
        errors, warnings = validate_after_market(date_str)
    else:
        print(f"❌ 未知階段: {phase}")
        print("phase 必須是: before_market, intraday, after_market")
        sys.exit(1)

    success = print_validation_result(phase, date_str, errors, warnings)

    # 返回值：有錯誤=1（禁止commit），無錯誤=0（允許commit）
    sys.exit(0 if success else 1)
