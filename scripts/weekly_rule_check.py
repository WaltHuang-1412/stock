#!/usr/bin/env python3
"""
每週規則有效性驗證（週五盤後自動執行）

檢查項目：
1. 整體準確率趨勢
2. 新規則（營收/持股比/過量買超）的加分股 vs 扣分股準確率
3. 如果扣分股準確率 ≥ 無變化股 → 規則可能失效，發警告

輸出：data/reports/weekly_rule_check_YYYY-MM-DD.txt（LINE 推送用）
"""

import sys
import os
import io
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"
CACHE_DIR = PROJECT_DIR / "data" / "cache"
REPORTS_DIR = PROJECT_DIR / "data" / "reports"


def load_settled():
    all_recs = []
    for fp in sorted(TRACKING_DIR.glob("tracking_202*.json")):
        if 'example' in fp.name:
            continue
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        date_str = data.get('date', '')
        for rec in data.get('recommendations', []):
            result = rec.get('result', '')
            if result not in ('success', 'fail'):
                continue
            all_recs.append({
                'date': date_str,
                'code': rec.get('stock_code') or rec.get('symbol', ''),
                'name': rec.get('stock_name') or rec.get('name', ''),
                'score': rec.get('score', 0),
                'result': result,
            })
    return all_recs


def load_revenue_cache():
    fp = CACHE_DIR / "revenue_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_ratio_cache():
    fp = CACHE_DIR / "foreign_ratio_cache.json"
    if fp.exists():
        with open(fp, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_revenue_yoy(code, date, cache):
    if code not in cache:
        return None, 0
    revenues = cache[code]
    monthly = {}
    for r in revenues:
        monthly[(r['revenue_year'], r['revenue_month'])] = r['revenue']
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return None, 0
    m, y = dt.month - 1, dt.year
    if m == 0:
        m, y = 12, y - 1
    cur = monthly.get((y, m))
    prev = monthly.get((y - 1, m))
    if cur and prev and prev > 0:
        yoy = (cur - prev) / prev * 100
    else:
        return None, 0
    # decline streak
    streak = 0
    cy, cm = y, m
    while True:
        c = monthly.get((cy, cm))
        p = monthly.get((cy - 1, cm))
        if c and p and p > 0 and (c - p) / p * 100 < 0:
            streak += 1
            cm -= 1
            if cm == 0:
                cm, cy = 12, cy - 1
        else:
            break
    return yoy, streak


def get_ratio_change(code, date, cache):
    if code not in cache:
        return None
    rows = cache[code]
    if len(rows) < 2:
        return None
    current, prev = None, None
    for row in rows:
        rd = row['date'].replace('-', '')
        dd = date.replace('-', '')
        if rd <= dd:
            prev = current
            current = row
    if current is None or prev is None:
        return None
    return current.get('ForeignInvestmentSharesRatio', 0) - prev.get('ForeignInvestmentSharesRatio', 0)


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    recs = load_settled()
    if not recs:
        print("無結算資料")
        return

    rev_cache = load_revenue_cache()
    ratio_cache = load_ratio_cache()

    total = len(recs)
    success = sum(1 for r in recs if r['result'] == 'success')
    overall_acc = success / total * 100

    # 分類
    up, down, neutral = [], [], []

    for rec in recs:
        code, date = rec['code'], rec['date']
        adj = 0

        yoy, decline = get_revenue_yoy(code, date, rev_cache)
        if decline >= 3:
            adj -= 5

        ratio_chg = get_ratio_change(code, date, ratio_cache)
        if ratio_chg is not None:
            if ratio_chg > 0.5:
                adj += 5
            elif ratio_chg <= -0.1:
                adj -= 3

        if adj > 0:
            up.append(rec)
        elif adj < 0:
            down.append(rec)
        else:
            neutral.append(rec)

    def acc(lst):
        if not lst:
            return 0, 0
        s = sum(1 for r in lst if r['result'] == 'success')
        return s / len(lst) * 100, len(lst)

    up_acc, up_n = acc(up)
    down_acc, down_n = acc(down)
    neutral_acc, neutral_n = acc(neutral)

    # 近2週 vs 全期比較
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    recent = [r for r in recs if r['date'] >= two_weeks_ago]
    recent_acc = sum(1 for r in recent if r['result'] == 'success') / len(recent) * 100 if recent else 0

    # 判斷規則是否有效
    rule_ok = down_acc < neutral_acc - 3  # 扣分股準確率比無變化低至少3%才算有效

    # 產出
    lines = []
    lines.append(f"[週報] 規則有效性驗證 {today}")
    lines.append(f"")
    lines.append(f"整體: {success}/{total} = {overall_acc:.1f}%")
    if recent:
        lines.append(f"近2週: {sum(1 for r in recent if r['result']=='success')}/{len(recent)} = {recent_acc:.1f}%")
    lines.append(f"")
    lines.append(f"=== 新規則區分力 ===")
    lines.append(f"加分股: {up_acc:.1f}% ({up_n}檔)")
    lines.append(f"扣分股: {down_acc:.1f}% ({down_n}檔)")
    lines.append(f"無變化: {neutral_acc:.1f}% ({neutral_n}檔)")
    lines.append(f"")

    if rule_ok:
        lines.append(f"結論: 規則有效 (扣分股{down_acc:.0f}% < 無變化{neutral_acc:.0f}%)")
    else:
        lines.append(f"!! 警告: 規則可能失效 !!")
        lines.append(f"扣分股{down_acc:.0f}% vs 無變化{neutral_acc:.0f}%，差距不足")
        lines.append(f"建議檢查是否需要調整或移除規則")

    output = "\n".join(lines)
    print(output)

    # 存檔
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"weekly_rule_check_{today}.txt"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"\n已存: {out_path}")


if __name__ == "__main__":
    main()
