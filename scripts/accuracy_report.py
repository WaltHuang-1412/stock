#!/usr/bin/env python3
"""
準確率分類統計報表

功能：
讀取所有 tracking 檔案，按多維度統計準確率：
1. 按產業
2. 按評分區間
3. 按法人連買天數
4. 按動能區間
5. 按金額排名（如有資料）

用法：
    python scripts/accuracy_report.py              # 產生報表
    python scripts/accuracy_report.py --line        # 同時產生 LINE 摘要
"""

import sys
import io
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Windows 環境強制 UTF-8 輸出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"
REPORTS_DIR = PROJECT_DIR / "data" / "reports"


def load_all_recommendations():
    """讀取所有 tracking 檔案的推薦"""
    all_recs = []

    for filepath in sorted(TRACKING_DIR.glob("tracking_202*.json")):
        if 'example' in filepath.name:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        date_str = data.get('date', filepath.stem.replace('tracking_', ''))
        recs = data.get('recommendations', [])

        for rec in recs:
            # 統一欄位
            code = rec.get('stock_code') or rec.get('symbol', '?')
            name = rec.get('stock_name') or rec.get('name', '?')
            result = rec.get('result', '')

            # 只統計有結果的
            if result not in ('success', 'fail'):
                continue

            # 產業
            industry = rec.get('industry', '')
            if isinstance(industry, dict):
                industry = industry.get('sector', '')
            if not industry:
                industry = '未分類'

            # 評分
            score = rec.get('score', 0)

            # 法人連買天數
            chip = rec.get('chip_analysis', rec.get('chip_data', {}))
            consecutive_days = 0
            if isinstance(chip, dict):
                consecutive_days = chip.get('consecutive_buying_days',
                                   chip.get('continuous_buying_days',
                                   chip.get('consecutive_buy_days', 0)))

            # 動能
            momentum = rec.get('chip_momentum', None)
            if momentum is None and isinstance(chip, dict):
                mom_str = chip.get('momentum_change', '')
                if isinstance(mom_str, str):
                    try:
                        momentum = float(mom_str.replace('%', ''))
                    except ValueError:
                        momentum = None
                elif isinstance(mom_str, (int, float)):
                    momentum = mom_str

            # 金額排名（新欄位，可能不存在）
            amount_rank = rec.get('amount_rank', None)

            all_recs.append({
                'date': date_str,
                'code': code,
                'name': name,
                'result': result,
                'industry': industry,
                'score': score,
                'consecutive_days': consecutive_days,
                'momentum': momentum,
                'amount_rank': amount_rank,
            })

    return all_recs


def calc_accuracy(recs):
    """計算準確率"""
    total = len(recs)
    if total == 0:
        return 0, 0, 0, 0.0
    success = sum(1 for r in recs if r['result'] == 'success')
    fail = total - success
    accuracy = success / total * 100
    return total, success, fail, accuracy


def group_by(recs, key_fn):
    """按指定函數分組"""
    groups = defaultdict(list)
    for r in recs:
        key = key_fn(r)
        if key is not None:
            groups[key].append(r)
    return groups


def generate_report(recs):
    """產生 Markdown 報表"""
    lines = []
    today = datetime.now().strftime("%Y-%m-%d")

    total, success, fail, accuracy = calc_accuracy(recs)

    lines.append(f"# 準確率分類統計報表")
    lines.append(f"")
    lines.append(f"**產生日期**：{today}")
    lines.append(f"**統計期間**：{recs[0]['date']} ~ {recs[-1]['date']}" if recs else "無資料")
    lines.append(f"**總推薦數**：{total}（成功 {success} / 失敗 {fail}）")
    lines.append(f"**整體準確率**：{accuracy:.1f}%")
    lines.append("")

    # === 1. 按產業 ===
    lines.append("---")
    lines.append("## 1. 按產業")
    lines.append("")
    lines.append("| 產業 | 總數 | 成功 | 失敗 | 準確率 |")
    lines.append("|------|------|------|------|--------|")

    groups = group_by(recs, lambda r: r['industry'])
    sorted_groups = sorted(groups.items(), key=lambda x: calc_accuracy(x[1])[3], reverse=True)
    for key, group in sorted_groups:
        t, s, f, a = calc_accuracy(group)
        bar = "█" * int(a / 10) + "░" * (10 - int(a / 10))
        lines.append(f"| {key} | {t} | {s} | {f} | {a:.0f}% {bar} |")

    # === 2. 按評分區間 ===
    lines.append("")
    lines.append("---")
    lines.append("## 2. 按評分區間")
    lines.append("")
    lines.append("| 評分 | 總數 | 成功 | 失敗 | 準確率 |")
    lines.append("|------|------|------|------|--------|")

    def score_bucket(r):
        s = r['score']
        if s >= 85:
            return "≥85（強烈推薦）"
        elif s >= 75:
            return "75-84（推薦）"
        elif s >= 65:
            return "65-74（可考慮）"
        else:
            return "<65（不推薦）"

    groups = group_by(recs, score_bucket)
    for key in ["≥85（強烈推薦）", "75-84（推薦）", "65-74（可考慮）", "<65（不推薦）"]:
        if key in groups:
            t, s, f, a = calc_accuracy(groups[key])
            lines.append(f"| {key} | {t} | {s} | {f} | {a:.0f}% |")

    # === 3. 按法人連買天數 ===
    lines.append("")
    lines.append("---")
    lines.append("## 3. 按法人連買天數")
    lines.append("")
    lines.append("| 連買天數 | 總數 | 成功 | 失敗 | 準確率 |")
    lines.append("|---------|------|------|------|--------|")

    def days_bucket(r):
        d = r['consecutive_days']
        if d >= 5:
            return "≥5天"
        elif d >= 3:
            return "3-4天"
        elif d >= 1:
            return "1-2天"
        else:
            return "0天（無連買）"

    groups = group_by(recs, days_bucket)
    for key in ["≥5天", "3-4天", "1-2天", "0天（無連買）"]:
        if key in groups:
            t, s, f, a = calc_accuracy(groups[key])
            lines.append(f"| {key} | {t} | {s} | {f} | {a:.0f}% |")

    # === 4. 按動能區間 ===
    lines.append("")
    lines.append("---")
    lines.append("## 4. 按動能區間")
    lines.append("")
    lines.append("| 動能 | 總數 | 成功 | 失敗 | 準確率 | 含義 |")
    lines.append("|------|------|------|------|--------|------|")

    def momentum_bucket(r):
        m = r['momentum']
        if m is None:
            return None
        try:
            m = float(m)
        except (ValueError, TypeError):
            return None
        if m < -30:
            return "<-30%（佈局完成）"
        elif m <= 0:
            return "-30%~0%（佈局中）"
        elif m <= 50:
            return "0~+50%（觀察）"
        elif m <= 100:
            return "+50~+100%（謹慎）"
        else:
            return ">+100%（追高風險）"

    groups = group_by(recs, momentum_bucket)
    labels = {
        "<-30%（佈局完成）": "法人佈局完成，準備拉抬",
        "-30%~0%（佈局中）": "法人持續買，力道減弱",
        "0~+50%（觀察）": "法人買超加速中",
        "+50~+100%（謹慎）": "動能過強，追高風險",
        ">+100%（追高風險）": "爆量追高，極高風險",
    }
    for key in labels:
        if key in groups:
            t, s, f, a = calc_accuracy(groups[key])
            lines.append(f"| {key} | {t} | {s} | {f} | {a:.0f}% | {labels[key]} |")

    # === 5. 按金額排名 ===
    recs_with_rank = [r for r in recs if r['amount_rank'] is not None]
    if recs_with_rank:
        lines.append("")
        lines.append("---")
        lines.append("## 5. 按金額排名")
        lines.append("")
        lines.append("| 金額排名 | 總數 | 成功 | 失敗 | 準確率 |")
        lines.append("|---------|------|------|------|--------|")

        def rank_bucket(r):
            rank = r['amount_rank']
            if rank is None:
                return None
            if rank <= 10:
                return "TOP10"
            elif rank <= 20:
                return "TOP11-20"
            elif rank <= 35:
                return "TOP21-35"
            else:
                return "TOP36-50"

        groups = group_by(recs_with_rank, rank_bucket)
        for key in ["TOP10", "TOP11-20", "TOP21-35", "TOP36-50"]:
            if key in groups:
                t, s, f, a = calc_accuracy(groups[key])
                lines.append(f"| {key} | {t} | {s} | {f} | {a:.0f}% |")
    else:
        lines.append("")
        lines.append("---")
        lines.append("## 5. 按金額排名")
        lines.append("")
        lines.append("（尚無金額排名資料，待資料累積後統計）")

    # === 結論 ===
    lines.append("")
    lines.append("---")
    lines.append("## 結論與建議")
    lines.append("")

    # 找最準和最不準的產業
    industry_groups = group_by(recs, lambda r: r['industry'])
    industry_stats = [(k, calc_accuracy(v)) for k, v in industry_groups.items() if len(v) >= 3]
    if industry_stats:
        best = max(industry_stats, key=lambda x: x[1][3])
        worst = min(industry_stats, key=lambda x: x[1][3])
        lines.append(f"- 最準產業：**{best[0]}**（{best[1][3]:.0f}%，{best[1][0]}檔）")
        lines.append(f"- 最差產業：**{worst[0]}**（{worst[1][3]:.0f}%，{worst[1][0]}檔）")

    # 評分區間結論
    score_groups = group_by(recs, score_bucket)
    high_score = score_groups.get("≥85（強烈推薦）", [])
    low_score = score_groups.get("<65（不推薦）", [])
    if high_score:
        _, _, _, a = calc_accuracy(high_score)
        lines.append(f"- ≥85分準確率：{a:.0f}%")
    if low_score:
        _, _, _, a = calc_accuracy(low_score)
        lines.append(f"- <65分準確率：{a:.0f}%")

    return "\n".join(lines)


def generate_line_summary(recs):
    """產生 LINE 週報摘要"""
    total, success, fail, accuracy = calc_accuracy(recs)

    lines = [
        f"[週報] 準確率統計",
        f"整體：{success}/{total} = {accuracy:.0f}%",
        "",
    ]

    # 產業 TOP3
    industry_groups = group_by(recs, lambda r: r['industry'])
    industry_stats = sorted(
        [(k, calc_accuracy(v)) for k, v in industry_groups.items() if len(v) >= 2],
        key=lambda x: x[1][3], reverse=True
    )

    if industry_stats:
        lines.append("按產業：")
        for name, (t, s, f, a) in industry_stats[:5]:
            lines.append(f"  {name}: {a:.0f}% ({s}/{t})")
        lines.append("")

    # 動能結論
    def momentum_bucket(r):
        m = r['momentum']
        if m is None:
            return None
        try:
            m = float(m)
        except (ValueError, TypeError):
            return None
        if m < -30:
            return "佈局完成(<-30%)"
        elif m > 100:
            return "追高(>+100%)"
        else:
            return None

    mom_groups = group_by(recs, momentum_bucket)
    for key in ["佈局完成(<-30%)", "追高(>+100%)"]:
        if key in mom_groups:
            t, s, f, a = calc_accuracy(mom_groups[key])
            lines.append(f"{key}: {a:.0f}% ({s}/{t})")

    return "\n".join(lines)


def main():
    do_line = '--line' in sys.argv

    print("載入 tracking 資料...")
    recs = load_all_recommendations()
    print(f"找到 {len(recs)} 筆有結果的推薦")

    if not recs:
        print("沒有足夠的資料產生報表")
        print("請先執行 python scripts/backfill_tracking.py 補齊歷史資料")
        sys.exit(1)

    # 產生報表
    report = generate_report(recs)
    print(report)

    # 儲存
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = REPORTS_DIR / f"accuracy_{today}.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 報表已儲存：{report_path}")

    # LINE 摘要
    if do_line:
        summary = generate_line_summary(recs)
        summary_path = REPORTS_DIR / f"accuracy_line_{today}.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"💾 LINE 摘要已儲存：{summary_path}")


if __name__ == "__main__":
    main()
