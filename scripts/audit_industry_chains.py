#!/usr/bin/env python3
"""
產業鏈週審核腳本

每週一盤前執行，自動檢查 industry_chains.json 的健康狀態：
  1. 下市/停牌檢查 — 查 TWSE 確認股票是否還在交易
  2. tier_from_tracker 清理 — 統計待審股票，提示人工歸位
  3. 冷門產業檢查 — 找出長期沒出現在分析中的產業
  4. 重複股票檢查 — 同一股票出現在多個產業

用法：
  python scripts/audit_industry_chains.py                    # 完整審核
  python scripts/audit_industry_chains.py --check delisted   # 只查下市
  python scripts/audit_industry_chains.py --fix              # 自動修復（移除下市股）
  python scripts/audit_industry_chains.py --json             # JSON 輸出
"""

import sys
import io
import json
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
CHAINS_FILE = PROJECT_DIR / "data" / "industry_chains.json"
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"

sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from yahoo_finance_api import get_current_price


def load_chains():
    with open(CHAINS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chains(data):
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    with open(CHAINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_stocks(chains_data):
    """取得所有股票及其所屬產業/tier"""
    stocks = []
    for ind_key, ind in chains_data.get("industries", {}).items():
        for tier_name, tier in ind.get("tiers", {}).items():
            for s in tier.get("stocks", []):
                stocks.append({
                    "code": s["code"],
                    "name": s.get("name", ""),
                    "category": s.get("category", ""),
                    "industry": ind_key,
                    "industry_name": ind.get("name", ind_key),
                    "tier": tier_name,
                })
    return stocks


# ── 檢查 1: 下市/停牌 ──────────────────────────────────────────────

def check_delisted(stocks, batch_size=10):
    """查詢 Yahoo Finance 確認股票是否還有報價"""
    delisted = []
    active = []
    errors = []

    total = len(stocks)
    unique_codes = list({s["code"] for s in stocks})
    print(f"  查詢 {len(unique_codes)} 檔股票...", file=sys.stderr)

    for i, code in enumerate(unique_codes):
        if i > 0 and i % batch_size == 0:
            print(f"  進度 {i}/{len(unique_codes)}...", file=sys.stderr)
            time.sleep(1)  # 避免 rate limit

        price = get_current_price(code)
        if price is None:
            delisted.append(code)
        else:
            active.append(code)

    # 回填到 stocks
    delisted_set = set(delisted)
    results = []
    for s in stocks:
        if s["code"] in delisted_set:
            results.append({**s, "status": "delisted"})

    return results


# ── 檢查 2: tier_from_tracker 待審 ──────────────────────────────────

def check_tracker_tier(chains_data):
    """統計 tier_from_tracker 中的待審股票"""
    pending = []
    for ind_key, ind in chains_data.get("industries", {}).items():
        tier = ind.get("tiers", {}).get("tier_from_tracker")
        if tier and tier.get("stocks"):
            for s in tier["stocks"]:
                pending.append({
                    "code": s["code"],
                    "name": s.get("name", ""),
                    "category": s.get("category", ""),
                    "industry": ind_key,
                    "industry_name": ind.get("name", ind_key),
                })
    return pending


# ── 檢查 3: 冷門產業 ──────────────────────────────────────────────

def check_cold_industries(chains_data, days=30):
    """找出近 N 天沒出現在 tracking 推薦中的產業"""
    # 收集近期推薦過的產業
    recent_industries = set()
    today = datetime.now()

    for i in range(days):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        tracking_file = TRACKING_DIR / f"tracking_{d_str}.json"
        if not tracking_file.exists():
            continue
        try:
            with open(tracking_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for rec in data.get("recommendations", []):
                ind = rec.get("industry", "")
                if ind:
                    recent_industries.add(ind)
        except (json.JSONDecodeError, KeyError):
            pass

    # 比對 industry_chains
    all_industries = set(chains_data.get("industries", {}).keys())
    cold = []
    for ind_key in sorted(all_industries):
        ind = chains_data["industries"][ind_key]
        ind_name = ind.get("name", ind_key)
        # 檢查產業名稱或 key 是否有出現在推薦的 industry 欄位中
        matched = any(
            ind_key in ri or ind_name in ri or ri in ind_name
            for ri in recent_industries
        )
        if not matched:
            stock_count = sum(
                len(t.get("stocks", []))
                for t in ind.get("tiers", {}).values()
            )
            cold.append({
                "industry": ind_key,
                "industry_name": ind_name,
                "stock_count": stock_count,
            })

    return cold


# ── 檢查 4: 重複股票 ──────────────────────────────────────────────

def check_duplicates(stocks):
    """找出同一股票出現在多個產業的情況"""
    code_map = defaultdict(list)
    for s in stocks:
        code_map[s["code"]].append(s)

    duplicates = []
    for code, entries in code_map.items():
        industries = list({e["industry"] for e in entries})
        if len(industries) > 1:
            duplicates.append({
                "code": code,
                "name": entries[0]["name"],
                "industries": industries,
                "count": len(industries),
            })

    return sorted(duplicates, key=lambda x: -x["count"])


# ── 自動修復 ──────────────────────────────────────────────────────

def fix_delisted(chains_data, delisted_codes):
    """從 industry_chains.json 移除下市股"""
    removed = []
    delisted_set = set(delisted_codes)

    for ind_key, ind in chains_data.get("industries", {}).items():
        for tier_name, tier in ind.get("tiers", {}).items():
            original = tier.get("stocks", [])
            filtered = [s for s in original if s["code"] not in delisted_set]
            if len(filtered) < len(original):
                for s in original:
                    if s["code"] in delisted_set:
                        removed.append({
                            "code": s["code"],
                            "name": s.get("name", ""),
                            "industry": ind_key,
                            "tier": tier_name,
                        })
                tier["stocks"] = filtered

    return removed


# ── 主流程 ──────────────────────────────────────────────────────

def run_audit(checks=None, fix=False, output_json=False):
    """執行審核"""
    chains_data = load_chains()
    all_stocks = get_all_stocks(chains_data)
    run_all = checks is None

    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_industries": len(chains_data.get("industries", {})),
        "total_stocks": len(all_stocks),
        "checks": {},
    }

    # 1. 下市檢查
    if run_all or "delisted" in checks:
        print("\n🔍 檢查 1: 下市/停牌股票", file=sys.stderr)
        delisted = check_delisted(all_stocks)
        report["checks"]["delisted"] = {
            "count": len(delisted),
            "stocks": delisted,
        }

        if fix and delisted:
            codes = [d["code"] for d in delisted]
            removed = fix_delisted(chains_data, codes)
            save_chains(chains_data)
            report["checks"]["delisted"]["fixed"] = len(removed)
            print(f"  ✅ 已移除 {len(removed)} 檔下市股", file=sys.stderr)

    # 2. tier_from_tracker 待審
    if run_all or "tracker" in checks:
        print("\n🔍 檢查 2: tier_from_tracker 待審股票", file=sys.stderr)
        pending = check_tracker_tier(chains_data)
        report["checks"]["tracker_pending"] = {
            "count": len(pending),
            "stocks": pending,
        }

    # 3. 冷門產業
    if run_all or "cold" in checks:
        print("\n🔍 檢查 3: 冷門產業（近30天未推薦）", file=sys.stderr)
        cold = check_cold_industries(chains_data)
        report["checks"]["cold_industries"] = {
            "count": len(cold),
            "industries": cold,
        }

    # 4. 重複股票
    if run_all or "duplicates" in checks:
        print("\n🔍 檢查 4: 跨產業重複股票", file=sys.stderr)
        duplicates = check_duplicates(all_stocks)
        report["checks"]["duplicates"] = {
            "count": len(duplicates),
            "stocks": duplicates,
        }

    return report


def print_report(report):
    """人類可讀格式輸出"""
    print(f"\n{'='*60}")
    print(f"📋 產業鏈週審核報告 — {report['date']}")
    print(f"   {report['total_industries']} 產業 / {report['total_stocks']} 檔股票")
    print(f"{'='*60}")

    checks = report.get("checks", {})

    # 下市
    delisted = checks.get("delisted", {})
    if "count" in delisted:
        count = delisted["count"]
        if count > 0:
            print(f"\n🔴 下市/停牌：{count} 檔")
            for s in delisted["stocks"]:
                print(f"   {s['code']} {s['name']} ← [{s['industry']}] {s['tier']}")
            if delisted.get("fixed"):
                print(f"   ✅ 已自動移除 {delisted['fixed']} 檔")
        else:
            print(f"\n✅ 下市/停牌：無")

    # 待審
    pending = checks.get("tracker_pending", {})
    if "count" in pending:
        count = pending["count"]
        if count > 0:
            print(f"\n🟡 tier_from_tracker 待審：{count} 檔")
            by_industry = defaultdict(list)
            for s in pending["stocks"]:
                by_industry[s["industry"]].append(s)
            for ind, stocks in by_industry.items():
                names = ", ".join(f"{s['name']}({s['code']})" for s in stocks)
                print(f"   [{ind}] {names}")
        else:
            print(f"\n✅ tier_from_tracker：無待審")

    # 冷門
    cold = checks.get("cold_industries", {})
    if "count" in cold:
        count = cold["count"]
        if count > 0:
            print(f"\n🟡 冷門產業（近30天未推薦）：{count} 個")
            for c in cold["industries"]:
                print(f"   [{c['industry']}] {c['industry_name']}（{c['stock_count']} 檔）")
        else:
            print(f"\n✅ 冷門產業：無")

    # 重複
    dups = checks.get("duplicates", {})
    if "count" in dups:
        count = dups["count"]
        if count > 0:
            print(f"\n🟡 跨產業重複：{count} 檔")
            for d in dups["stocks"]:
                inds = ", ".join(d["industries"])
                print(f"   {d['code']} {d['name']} → {inds}")
        else:
            print(f"\n✅ 跨產業重複：無")

    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="產業鏈週審核")
    parser.add_argument("--check", nargs="+",
                        choices=["delisted", "tracker", "cold", "duplicates"],
                        help="只執行指定檢查項目")
    parser.add_argument("--fix", action="store_true",
                        help="自動修復（移除下市股）")
    parser.add_argument("--json", action="store_true",
                        help="JSON 格式輸出")
    args = parser.parse_args()

    report = run_audit(checks=args.check, fix=args.fix, output_json=args.json)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
