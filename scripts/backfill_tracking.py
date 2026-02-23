#!/usr/bin/env python3
"""
歷史 Tracking 資料補齊工具

功能：
1. 掃描所有 tracking_*.json，找出缺少 closing_price 和 result 的推薦
2. 用 Yahoo Finance API 取得歷史收盤價
3. 自動判斷 success/fail（收盤價 >= 推薦價 = success）
4. 統一欄位名稱（symbol→stock_code, close_price→closing_price 等）
5. 寫回 tracking 檔案

用法：
    python scripts/backfill_tracking.py --dry-run    # 預覽不寫入
    python scripts/backfill_tracking.py              # 執行補齊
"""

import sys
import io
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Windows 環境強制 UTF-8 輸出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))
from yahoo_finance_api import get_history

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"


def normalize_recommendation(rec, parent_date):
    """統一推薦欄位名稱"""
    # stock_code
    if 'stock_code' not in rec and 'symbol' in rec:
        rec['stock_code'] = rec.pop('symbol')

    # stock_name
    if 'stock_name' not in rec and 'name' in rec:
        rec['stock_name'] = rec.pop('name')

    # recommend_price
    if 'recommend_price' not in rec and 'entry_price' in rec:
        entry = rec.pop('entry_price')
        if isinstance(entry, str) and '-' in entry:
            # "27.0-27.5" → 取中間值
            parts = entry.split('-')
            try:
                rec['recommend_price'] = (float(parts[0]) + float(parts[1])) / 2
            except ValueError:
                rec['recommend_price'] = None
        else:
            try:
                rec['recommend_price'] = float(entry)
            except (ValueError, TypeError):
                rec['recommend_price'] = None

    # target_price
    if 'target_price' not in rec and 'target' in rec:
        try:
            rec['target_price'] = float(rec.pop('target'))
        except (ValueError, TypeError):
            pass

    # closing_price（統一用 closing_price）
    if 'closing_price' not in rec:
        if 'close_price' in rec and rec['close_price']:
            rec['closing_price'] = rec['close_price']

    # recommend_date
    if 'recommend_date' not in rec:
        rec['recommend_date'] = parent_date

    return rec


def get_closing_price_for_date(stock_code, target_date_str):
    """
    取得指定日期的收盤價

    Args:
        stock_code: 股票代號（如 '2330'）
        target_date_str: 目標日期 'YYYY-MM-DD'

    Returns:
        float or None
    """
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d")
        days_ago = (datetime.now() - target).days

        # Yahoo Finance 免費版限制：約 2 個月
        if days_ago > 90:
            return None

        # 取足夠長的歷史
        period = f"{min(days_ago + 10, 90)}d"
        hist = get_history(stock_code, period=period, interval='1d')
        if not hist or not hist.get('timestamps') or not hist.get('closes'):
            return None

        # 找到目標日期的收盤價
        for ts, close in zip(hist['timestamps'], hist['closes']):
            if close is None:
                continue
            dt = datetime.fromtimestamp(ts)
            if dt.strftime("%Y-%m-%d") == target_date_str:
                return close

        # 找不到精確日期，取最接近的
        target_ts = target.timestamp()
        best_close = None
        best_diff = float('inf')
        for ts, close in zip(hist['timestamps'], hist['closes']):
            if close is None:
                continue
            diff = abs(ts - target_ts)
            if diff < best_diff and diff < 86400 * 3:  # 3天內
                best_diff = diff
                best_close = close

        return best_close

    except Exception as e:
        print(f"  ❌ 查詢 {stock_code} {target_date_str} 失敗: {e}")
        return None


def backfill_tracking_file(filepath, dry_run=False):
    """補齊單一 tracking 檔案"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    parent_date = data.get('date', filepath.stem.replace('tracking_', ''))
    recs = data.get('recommendations', [])
    if not recs:
        return 0, 0

    modified = 0
    skipped = 0

    for rec in recs:
        # 統一欄位
        normalize_recommendation(rec, parent_date)

        stock_code = rec.get('stock_code', '?')
        stock_name = rec.get('stock_name', '?')
        recommend_price = rec.get('recommend_price')

        # 檢查是否需要補齊
        has_closing = rec.get('closing_price') is not None
        has_result = rec.get('result') and rec['result'] in ('success', 'fail')

        if has_closing and has_result:
            continue  # 已完整

        # 確保 recommend_price 是數字
        if recommend_price:
            try:
                recommend_price = float(recommend_price)
                rec['recommend_price'] = recommend_price
            except (ValueError, TypeError):
                recommend_price = None

        if not recommend_price:
            print(f"  ⚠️ {stock_name}({stock_code}) 無推薦價，跳過")
            skipped += 1
            continue

        # 取得收盤價
        if not has_closing:
            if dry_run:
                print(f"  [DRY] {stock_name}({stock_code}) 需補收盤價 (日期: {parent_date})")
                modified += 1
                continue

            closing = get_closing_price_for_date(stock_code, parent_date)
            if closing is not None:
                rec['closing_price'] = closing
                rec['vs_recommend_pct'] = round((closing - recommend_price) / recommend_price * 100, 2)
                print(f"  ✅ {stock_name}({stock_code}) 收盤價={closing} (推薦價={recommend_price})")
            else:
                print(f"  ❌ {stock_name}({stock_code}) 無法取得收盤價")
                skipped += 1
                continue

            # API rate limit
            time.sleep(0.5)

        # 判斷 result
        closing_price = rec.get('closing_price')
        if closing_price and recommend_price and not has_result:
            if closing_price >= recommend_price:
                rec['result'] = 'success'
            else:
                rec['result'] = 'fail'
            print(f"       → result={rec['result']} ({closing_price} vs {recommend_price})")

        modified += 1

    # 寫回
    if modified > 0 and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return modified, skipped


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=" * 50)
        print("DRY RUN 模式（預覽，不寫入）")
        print("=" * 50)
    else:
        print("=" * 50)
        print("歷史 Tracking 資料補齊工具")
        print("=" * 50)

    tracking_files = sorted(TRACKING_DIR.glob("tracking_202*.json"))
    # 排除 example
    tracking_files = [f for f in tracking_files if 'example' not in f.name]

    total_modified = 0
    total_skipped = 0
    files_updated = 0

    for filepath in tracking_files:
        date_str = filepath.stem.replace('tracking_', '')
        print(f"\n📁 {filepath.name} ({date_str})")

        modified, skipped = backfill_tracking_file(filepath, dry_run)
        total_modified += modified
        total_skipped += skipped
        if modified > 0:
            files_updated += 1

    print(f"\n{'=' * 50}")
    print(f"完成！")
    print(f"檔案數：{len(tracking_files)}")
    print(f"更新檔案：{files_updated}")
    print(f"補齊推薦：{total_modified}")
    print(f"跳過推薦：{total_skipped}")
    if dry_run:
        print(f"\n（DRY RUN 模式，未實際寫入）")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
