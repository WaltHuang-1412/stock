#!/usr/bin/env python3
"""
Tracking檔案格式統一工具
用途：將舊版tracking檔案格式統一為新版格式
執行方式：python3 scripts/normalize_tracking_format.py [--preview]
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

def normalize_recommendation(rec):
    """標準化單個推薦記錄"""
    normalized = rec.copy()

    # 統一股票代碼欄位 (symbol -> stock_code)
    if 'symbol' in rec and 'stock_code' not in rec:
        normalized['stock_code'] = rec['symbol']
        # 保留原欄位供相容
        normalized['symbol'] = rec['symbol']

    # 統一股票名稱欄位 (name -> stock_name)
    if 'name' in rec and 'stock_name' not in rec:
        normalized['stock_name'] = rec['name']
        # 保留原欄位供相容
        normalized['name'] = rec['name']

    # 統一推薦日期欄位 (date -> recommend_date)
    if 'date' in rec and 'recommend_date' not in rec:
        # 從父層 date 或檔案名稱推斷
        normalized['recommend_date'] = rec['date']

    # 確保必要欄位存在
    required_fields = {
        'status': 'pending',
        'tracking_days': 7,
        'daily_updates': []
    }

    for field, default_value in required_fields.items():
        if field not in normalized:
            normalized[field] = default_value

    # 標準化價格格式（如果是字串範圍，取第一個值）
    if 'recommend_price' in rec:
        price = rec['recommend_price']
        if isinstance(price, str) and '-' in price:
            try:
                # "26.8-27.2" -> 26.8
                normalized['recommend_price'] = float(price.split('-')[0])
            except ValueError:
                pass  # 保持原值

    return normalized

def normalize_tracking_file(file_path, preview=False):
    """標準化單個tracking檔案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        original_data = json.dumps(data, ensure_ascii=False, indent=2)
        changes_made = []

        # 確保基本結構
        if 'recommendations' not in data:
            data['recommendations'] = []
            changes_made.append("+ 新增 recommendations 陣列")

        if 'metadata' not in data:
            data['metadata'] = {}
            changes_made.append("+ 新增 metadata 物件")

        # 從檔案名稱提取日期
        file_date = None
        filename = os.path.basename(file_path)
        if 'tracking_' in filename:
            try:
                date_str = filename.replace('tracking_', '').replace('.json', '')
                file_date = date_str  # YYYY-MM-DD 格式
            except:
                pass

        # 標準化所有推薦記錄
        recommendations = data.get('recommendations', [])
        normalized_recommendations = []

        for i, rec in enumerate(recommendations):
            original_rec = rec.copy()
            normalized_rec = normalize_recommendation(rec)

            # 如果缺少推薦日期，嘗試從檔案推斷
            if 'recommend_date' not in normalized_rec and file_date:
                normalized_rec['recommend_date'] = file_date
                changes_made.append(f"+ 推薦 {i+1}: 新增 recommend_date = {file_date}")

            # 檢查變更
            if normalized_rec != original_rec:
                stock_name = normalized_rec.get('stock_name') or normalized_rec.get('name', f'股票{i+1}')
                for key in normalized_rec:
                    if key not in original_rec:
                        changes_made.append(f"+ {stock_name}: 新增 {key}")
                    elif normalized_rec[key] != original_rec[key]:
                        changes_made.append(f"* {stock_name}: 更新 {key}")

            normalized_recommendations.append(normalized_rec)

        data['recommendations'] = normalized_recommendations

        # 更新metadata
        data['metadata'].update({
            'normalized_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'format_version': '2.0'
        })

        # 檢查是否有變更
        new_data = json.dumps(data, ensure_ascii=False, indent=2)
        has_changes = original_data != new_data

        if preview:
            return has_changes, changes_made, None
        elif has_changes:
            # 備份原檔案
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(json.loads(original_data), f, ensure_ascii=False, indent=2)

            # 寫入標準化後的檔案
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return has_changes, changes_made, backup_path
        else:
            return False, [], None

    except Exception as e:
        return False, [f"❌ 錯誤: {str(e)}"], None

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='Tracking檔案格式統一工具')
    parser.add_argument('--preview', action='store_true', help='預覽模式，不實際修改檔案')
    parser.add_argument('--file', type=str, help='指定單一檔案處理')

    args = parser.parse_args()

    print("🔧 Tracking檔案格式統一工具")
    print("=" * 60)

    if args.preview:
        print("📋 預覽模式：僅顯示將要進行的變更\n")

    # 找到所有tracking檔案
    tracking_dir = Path('data/tracking')
    if args.file:
        tracking_files = [Path(args.file)]
    else:
        tracking_files = list(tracking_dir.glob('tracking_*.json'))

    if not tracking_files:
        print("❌ 找不到tracking檔案")
        return

    print(f"📂 找到 {len(tracking_files)} 個tracking檔案\n")

    total_processed = 0
    total_changed = 0
    total_errors = 0

    # 處理每個檔案
    for file_path in tracking_files:
        print(f"📄 處理 {file_path.name}...")

        has_changes, changes, backup_path = normalize_tracking_file(file_path, args.preview)

        total_processed += 1

        if changes and changes[0].startswith('❌'):
            total_errors += 1
            print(f"   ❌ 處理失敗: {changes[0]}")
        elif has_changes:
            total_changed += 1
            print(f"   ✅ {'將要變更' if args.preview else '已標準化'}")
            for change in changes[:5]:  # 最多顯示5個變更
                print(f"      {change}")
            if len(changes) > 5:
                print(f"      ... 還有 {len(changes) - 5} 個變更")
            if backup_path:
                print(f"   💾 備份至: {backup_path}")
        else:
            print(f"   ✅ 格式已是最新，無需變更")

        print()

    # 統計結果
    print("=" * 60)
    print("📊 處理結果統計")
    print(f"📂 處理檔案: {total_processed}")
    print(f"✅ 需要變更: {total_changed}")
    print(f"❌ 處理失敗: {total_errors}")
    print(f"🎯 成功率: {(total_processed - total_errors) / total_processed * 100:.1f}%")

    if args.preview and total_changed > 0:
        print(f"\n💡 執行 'python3 {sys.argv[0]}' 開始實際標準化")

if __name__ == '__main__':
    main()