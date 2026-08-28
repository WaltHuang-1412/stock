#!/usr/bin/env python3
"""
結算判斷器

掃描「所有」tracking 檔中 result='holding' 的推薦，用歷史日收盤從推薦日逐日重演，
機械式判斷結算結果。

結算規則（逐交易日走訪，取最先觸發者）：
  1. 收盤價 ≥ 目標價 → success
  2. 收盤價 ≤ 停損價 → fail（停損價由 stop_loss_pct 重算）
  3. 持有交易日數 ≥ settlement_days → 收盤>推薦價=success，≤推薦價=fail
  4. 以上皆無 → holding

v2 修正（2026-07-13，殭屍 holding 清理後）：
  - 掃描全部 tracking_*.json，不再只掃近 15 天（舊版漏掃 → 殭屍單成因）
  - 同一股票不同日期的推薦各自獨立結算，以 (recommend_date, code, track) 去重，
    不再被較新推薦遮蔽（修正「重複建檔遮蔽 D10」）
  - 交易日數改用個股價格序列（成交量>0 的日 K）計算，颱風/臨時休市日不誤計
    （Yahoo 會在休市日塞量=0 的假 K 棒，一律過濾）
  - 目標/停損改用歷史收盤逐日判斷，補結算時能還原「當時就該結」的日期與價格

用法：
  python scripts/settlement_checker.py                    # 掃描所有 holding
  python scripts/settlement_checker.py --date 2026-05-02  # 指定結算日
  python scripts/settlement_checker.py --json              # JSON 輸出
"""

import sys
import io
import json
import argparse
import glob
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = PROJECT_DIR / "data" / "tracking"
TPE = timezone(timedelta(hours=8))

sys.path.insert(0, str(PROJECT_DIR / "scripts"))
from yahoo_finance_api import get_history

_history_cache = {}


def get_close_series(code):
    """個股日收盤序列 [(date_str, close), ...] 遞增排序。

    過濾成交量=0 的假 K 棒（颱風/休市日 Yahoo 沿用前收塞入），失敗返回 None。
    """
    if code in _history_cache:
        return _history_cache[code]

    h = get_history(code, period="1y", interval="1d")
    series = None
    if h and h.get("timestamps") and h.get("closes"):
        vols = h.get("volumes") or [None] * len(h["timestamps"])
        dedup = {}
        for ts, c, v in zip(h["timestamps"], h["closes"], vols):
            if c is None or not v:
                continue
            d = datetime.fromtimestamp(ts, tz=TPE).strftime("%Y-%m-%d")
            dedup[d] = round(float(c), 2)
        series = sorted(dedup.items()) or None

    _history_cache[code] = series
    return series


def _entry_from_rec(rec, file_date, track):
    """從 tracking 記錄建立待結算項目，recommend_price 相容舊格式 intraday_price"""
    price = rec.get("recommend_price") or rec.get("intraday_price")
    default_pct = -5 if track == "B" else -10
    return {
        "stock_code": rec.get("stock_code"),
        "stock_name": rec.get("stock_name", ""),
        "industry": rec.get("industry", ""),
        "track": track,
        "recommend_date": rec.get("recommend_date") or file_date,
        "recommend_price": price,
        "target_price": rec.get("target_price"),
        "stop_loss": rec.get("stop_loss"),
        "stop_loss_pct": rec.get("stop_loss_pct", default_pct),
        "settlement_days": rec.get("settlement_days", 10),
        "score": rec.get("score"),
        "position": rec.get("position", ""),
        "source_file": f"tracking_{file_date}.json",
    }


def find_all_holdings():
    """掃描全部 tracking 檔，找出所有 result='holding' 的推薦。

    以 (recommend_date, stock_code, track) 為身分去重 —— 同一筆推薦被後續檔案
    carry over 時只取最早（原始）檔的版本；同一股票不同日期的推薦各自保留。
    """
    holdings = {}  # key=(recommend_date, code, track)

    for path in sorted(glob.glob(str(TRACKING_DIR / "tracking_*.json"))):
        file_date = Path(path).stem.replace("tracking_", "")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            print(f"⚠️ 無法讀取 {path}，跳過", file=sys.stderr)
            continue

        for list_key, track in (("recommendations", "A"), ("track_b_recommendations", "B")):
            for rec in data.get(list_key) or []:
                if not isinstance(rec, dict):
                    continue
                if rec.get("result", "holding") != "holding":
                    continue
                entry = _entry_from_rec(rec, file_date, track)
                key = (entry["recommend_date"], entry["stock_code"], track)
                if key not in holdings:  # 檔案按日期排序，先見者即原始檔
                    holdings[key] = entry

        # holdings 陣列（盤後 tracking 會把前幾天的放這裡）：無 track 資訊，
        # 只在同 (recommend_date, code) 尚無任何軌的記錄時補入
        for rec in data.get("holdings") or []:
            if not isinstance(rec, dict):
                continue
            if rec.get("result", "holding") != "holding":
                continue
            entry = _entry_from_rec(rec, file_date, "A")
            rd, code = entry["recommend_date"], entry["stock_code"]
            if any(k[0] == rd and k[1] == code for k in holdings):
                continue
            holdings[(rd, code, "A")] = entry

    return list(holdings.values())


def _num(v):
    """轉數字；區間字串（'27.0-27.5'）或文字（'開盤價附近'）返回 None"""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def check_settlement(entries, date_str):
    """逐筆用歷史收盤從推薦日重演結算"""
    results = []

    # 先抓齊全部序列，求「市場最新交易日」＝所有序列末日的最大值。
    # 個股序列末日落後市場最新日 ＝ 序列停滯（停牌/斷更），凍結判定（v8.3.8）。
    all_series = {}
    for info in entries:
        code = info["stock_code"]
        if code and code not in all_series:
            all_series[code] = get_close_series(code)
    market_last = max((s[-1][0] for s in all_series.values() if s), default=None)

    for info in entries:
        code = info["stock_code"]
        recommend_price = _num(info["recommend_price"])
        target_price = _num(info["target_price"])  # 非數字目標 → 只用停損/D10 規則

        if not code or not recommend_price:
            results.append({**info, "close": None, "result": "error",
                            "reason": f"recommend_price 缺漏或非數字（{info['recommend_price']!r}），無法結算"})
            continue

        series = all_series.get(code)
        if not series:
            results.append({**info, "close": None, "result": "error",
                            "reason": "無法取得收盤價序列"})
            continue

        if market_last and series[-1][0] < market_last:
            results.append({**info, "close": series[-1][1], "result": "holding",
                            "stale_series": True, "change_pct": round(
                                (series[-1][1] - recommend_price) / recommend_price * 100, 2),
                            "reason": (f"⚠️ 序列停滯（末日 {series[-1][0]}，市場最新 {market_last}）"
                                       f"｜凍結判定：不結算、不出場、D 不推進（v8.3.8）")})
            continue

        # 用 stop_loss_pct 重算 stop_loss（非數字時依軌道預設）
        stop_loss_pct = _num(info.get("stop_loss_pct")) or (-5 if info.get("track") == "B" else -10)
        stop_loss = round(recommend_price * (1 + stop_loss_pct / 100), 2)
        settlement_days = int(_num(info.get("settlement_days")) or 10)

        # 推薦日之後、結算日（含）之前的交易日
        days = [(d, c) for d, c in series if info["recommend_date"] < d <= date_str]

        entry = {**info, "stop_loss": stop_loss}
        settled = False
        for i, (d, close) in enumerate(days, 1):
            if target_price and close >= target_price:
                entry.update(result="success", settled_date=d, close=close, holding_days=i,
                             reason=f"D{i} 收盤 {close} ≥ 目標 {target_price}")
                settled = True
                break
            if close <= stop_loss:
                entry.update(result="fail", settled_date=d, close=close, holding_days=i,
                             reason=f"D{i} 收盤 {close} ≤ 停損 {stop_loss}")
                settled = True
                break
            if i >= settlement_days:
                if close > recommend_price:
                    entry.update(result="success",
                                 reason=f"D{i} 到期，收盤 {close} > 推薦 {recommend_price}")
                else:
                    entry.update(result="fail",
                                 reason=f"D{i} 到期，收盤 {close} ≤ 推薦 {recommend_price}")
                entry.update(settled_date=d, close=close, holding_days=i)
                settled = True
                break

        if not settled:
            close = days[-1][1] if days else series[-1][1]
            holding_days = len(days)
            dist_target = round((target_price - close) / close * 100, 1) if target_price else None
            dist_stop = round((close - stop_loss) / close * 100, 1)
            entry.update(result="holding", close=close, holding_days=holding_days,
                         reason=f"D{holding_days}/{settlement_days} | 距目標 {dist_target}% | 距停損 {dist_stop}%")

        entry["change_pct"] = round((entry["close"] - recommend_price) / recommend_price * 100, 2)
        results.append(entry)

    return results


def main():
    parser = argparse.ArgumentParser(description="結算判斷器")
    parser.add_argument("--date", default=None, help="結算日期 (YYYY-MM-DD)，預設今天")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    args = parser.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    print(f"📊 結算判斷 — {date_str}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    holdings = find_all_holdings()
    if not holdings:
        print("沒有找到任何 holding 中的股票", file=sys.stderr)
        if args.json:
            print(json.dumps({"date": date_str, "results": []}, ensure_ascii=False, indent=2))
        return

    print(f"找到 {len(holdings)} 筆 holding 中（含同股票不同日期推薦）", file=sys.stderr)

    results = check_settlement(holdings, date_str)

    if args.json:
        output = {
            "date": date_str,
            "results": results,
            "summary": {
                "success": sum(1 for r in results if r["result"] == "success"),
                "fail": sum(1 for r in results if r["result"] == "fail"),
                "holding": sum(1 for r in results if r["result"] == "holding"),
                "error": sum(1 for r in results if r["result"] == "error"),
            }
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        settled = [r for r in results if r["result"] in ("success", "fail")]
        holding = [r for r in results if r["result"] == "holding"]
        errors = [r for r in results if r["result"] == "error"]

        if settled:
            print(f"\n🔔 應結算 ({len(settled)} 筆):")
            for r in settled:
                icon = "✅" if r["result"] == "success" else "❌"
                print(f"  {icon} {r['stock_code']} {r['stock_name']} [{r['track']}] "
                      f"推薦日 {r['recommend_date']} | {r['change_pct']:+.1f}% | {r['reason']} "
                      f"@{r['settled_date']} | 來源 {r['source_file']}")

        if holding:
            print(f"\n📍 持有中 ({len(holding)} 筆):")
            for r in holding:
                print(f"  {r['stock_code']} {r['stock_name']} [{r['track']}] "
                      f"推薦日 {r['recommend_date']} | 現價 {r['close']} ({r['change_pct']:+.1f}%) | {r['reason']}")

        if errors:
            print(f"\n⚠️ 查詢失敗 ({len(errors)} 筆):")
            for r in errors:
                print(f"  {r['stock_code']} {r['stock_name']} 推薦日 {r['recommend_date']} | {r['reason']}")


if __name__ == "__main__":
    main()
