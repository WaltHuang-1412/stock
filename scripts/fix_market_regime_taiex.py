#!/usr/bin/env python3
"""
校正 market_regime.json 的 taiex 區塊（v8.3.11）

問題：market_regime.json 由外部 market-intelligence repo 產出，其 taiex.current
      恆為「前兩個交易日」收盤（n=5 一致）。2026-09-18 實測 current=45848.90，
      但當日收盤為 47180.75，差 1332 點，導致 vs_ma20 由 +2.4% 誤報為 -0.53%
      （多空判讀直接相反）。

作法：直接向 Yahoo 取 ^TWII 日線，重算 current / ma20 / ma60 / ma240 / 52週高低
      與各項乖離，覆寫 taiex 區塊，並保留原值於 taiex_original 供回溯。

⚠️ 幻影K過濾：Yahoo 會在真實日K之後附加一列「盤中報價」（非交易日日期、
   時間戳不是 09:00:00、量＝當下報價量）。2026-09-21 實測此列同時污染了
   settlement_checker、Step 4-1 停損比對與 check_price_position。
   本腳本只採用台北時間 09:00:00 的列。

用法：
    python scripts/fix_market_regime_taiex.py --date 2026-09-21
    python scripts/fix_market_regime_taiex.py            # 預設今日
"""

import sys
import os
import io
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
TPE = timezone(timedelta(hours=8))
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETWII"


def fetch_taiex_daily(rng="2y"):
    """取 ^TWII 日線，回傳 [(YYYY-MM-DD, close), ...]，已濾除盤中幻影列"""
    params = {"range": rng, "interval": "1d"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    r = requests.get(CHART_URL, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    payload = r.json()

    result = payload["chart"]["result"][0]
    stamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]

    series = []
    dropped = []
    for ts, close in zip(stamps, closes):
        if close is None:
            continue
        dt = datetime.fromtimestamp(ts, TPE)
        # 真實日K的時間戳一律為台北時間 09:00:00；其餘為盤中報價幻影列
        if (dt.hour, dt.minute, dt.second) != (9, 0, 0):
            dropped.append((dt.strftime("%Y-%m-%d %H:%M:%S"), round(close, 2)))
            continue
        series.append((dt.strftime("%Y-%m-%d"), float(close)))

    series.sort(key=lambda x: x[0])
    return series, dropped


def ma(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def pct(a, b):
    if a is None or b in (None, 0):
        return None
    return round((a - b) / b * 100, 2)


def build_taiex(series):
    closes = [c for _, c in series]
    current = closes[-1]
    as_of = series[-1][0]

    ma20 = ma(closes, 20)
    ma60 = ma(closes, 60)
    ma240 = ma(closes, 240)
    window52 = closes[-240:] if len(closes) >= 240 else closes

    return {
        "current": round(current, 2),
        "as_of": as_of,
        "ma20": round(ma20, 2) if ma20 else None,
        "ma60": round(ma60, 2) if ma60 else None,
        "ma240": round(ma240, 2) if ma240 else None,
        "high_52w": round(max(window52), 2),
        "low_52w": round(min(window52), 2),
        "vs_ma20": pct(current, ma20),
        "vs_ma60": pct(current, ma60),
        "vs_ma240": pct(current, ma240),
        "source": "Yahoo ^TWII (fix_market_regime_taiex.py)",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(TPE).strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    path = PROJECT_DIR / "data" / args.date / "market_regime.json"
    if not path.exists():
        print(f"[略過] 找不到 {path}（market-intelligence 今日未產出）")
        return 0

    series, dropped = fetch_taiex_daily()

    # 只採用 <= 目標日期的日K（對歷史檔校正時不得用到未來資料）
    series = [(d, c) for d, c in series if d <= args.date]

    # 當日盤未收（台北 13:35 前）→ 當日日K未完成，改用前一交易日收盤
    now = datetime.now(TPE)
    if series and series[-1][0] == now.strftime("%Y-%m-%d") and now.hour * 60 + now.minute < 13 * 60 + 35:
        print(f"[未收盤] {series[-1][0]} 日K尚未完成（現在 {now.strftime('%H:%M')}），"
              f"改用前一交易日 {series[-2][0] if len(series) > 1 else 'N/A'} 收盤")
        series = series[:-1]

    if len(series) < 20:
        print(f"[錯誤] ^TWII 日線筆數不足（{len(series)}），不覆寫")
        return 1

    if dropped:
        print(f"[幻影K] 已濾除 {len(dropped)} 列非 09:00:00 的盤中報價：{dropped}")

    fixed = build_taiex(series)

    with open(path, encoding="utf-8") as f:
        regime = json.load(f)

    before = regime.get("taiex", {})
    old_current = before.get("current")
    old_vs20 = before.get("vs_ma20")

    diff = None
    if isinstance(old_current, (int, float)):
        diff = round(fixed["current"] - old_current, 2)

    print(f"檔案         : {path}")
    print(f"原 current   : {old_current}  (vs_ma20 {old_vs20})")
    print(f"實際 current : {fixed['current']}  (vs_ma20 {fixed['vs_ma20']})  資料日 {fixed['as_of']}")
    if diff is not None:
        print(f"差額         : {diff:+} 點")
    if old_vs20 is not None and fixed["vs_ma20"] is not None:
        if (old_vs20 < 0) != (fixed["vs_ma20"] < 0):
            print("[警告] 月線乖離正負號原本是反的 —— 多空判讀受影響，報告須改寫")

    if args.dry_run:
        print("[dry-run] 未寫入")
        return 0

    if "taiex_original" not in regime:
        regime["taiex_original"] = before
    regime["taiex"] = fixed
    regime["taiex_fixed_at"] = datetime.now(TPE).strftime("%Y-%m-%d %H:%M:%S")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(regime, f, ensure_ascii=False, indent=2)

    print("[OK] taiex 區塊已校正（原值保留於 taiex_original）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
