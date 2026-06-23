#!/usr/bin/env python3
"""
賣出策略回測：Level 3/4 訊號「賣 vs 撐」比較
使用 T86 快取重建歷史反轉訊號，對照持倉後續漲跌
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# ── 讀取 T86 快取 ──────────────────────────────────────────
def load_t86(date_str):
    """從快取讀取單日所有股票的法人資料，回傳 {code: {foreign, trust, dealer, total}}
    快取格式：{stock_code: {date, name, foreign, trust, dealer, total}}，單位：張
    """
    path = ROOT / "data" / "cache" / f"twse_t86_{date_str}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    result = {}
    for code, row in raw.items():
        if not isinstance(row, dict):
            continue
        result[code] = {
            "foreign": row.get("foreign", 0),
            "trust":   row.get("trust", 0),
            "dealer":  row.get("dealer", 0),
            "total":   row.get("total", 0),
        }
    return result

# ── 交易日清單 ──────────────────────────────────────────────
def get_trading_dates_in_cache():
    cache_dir = ROOT / "data" / "cache"
    dates = []
    for f in sorted(cache_dir.glob("twse_t86_*.json")):
        d = f.stem.replace("twse_t86_", "")
        dates.append(d)
    return sorted(dates)

def date_range_from_cache(start: str, end: str, all_dates: list):
    return [d for d in all_dates if start <= d <= end]

# ── 重建 reversal level ─────────────────────────────────────
def compute_reversal_level(stock_code: str, as_of_date: str, all_dates: list) -> dict:
    """
    使用 T86 快取重算 reversal level（簡化版，僅判斷 Level 0-4）
    需要 as_of_date 當日及前 9 個交易日共 10 天資料
    """
    idx = all_dates.index(as_of_date) if as_of_date in all_dates else -1
    if idx < 0:
        return {"level": -1, "reason": "no data"}

    window = all_dates[max(0, idx - 9): idx + 1]
    daily = []
    for d in window:
        t86 = load_t86(d)
        if stock_code in t86:
            daily.append({"date": d, **t86[stock_code]})

    if len(daily) < 3:
        return {"level": -1, "reason": "insufficient data"}

    today_data = daily[-1]
    today_total = today_data["total"]

    # Level 4：今日爆量賣超（單日 total < -20,000 張）
    if today_total < -20000:
        return {"level": 4, "reason": f"爆量賣超 {today_total:+,}張"}

    # Level 3：連續 2 天賣超且累計轉負
    if len(daily) >= 2:
        last2 = [d["total"] for d in daily[-2:]]
        if all(v < 0 for v in last2):
            cumulative = sum(d["total"] for d in daily)
            if cumulative < 0:
                return {"level": 3, "reason": f"連續賣超2天，累計{cumulative:+,}張"}

    # Level 2：連買後突然賣（今日賣，前一日買，累計仍正）
    if len(daily) >= 2 and today_total < 0 and daily[-2]["total"] > 0:
        cumulative = sum(d["total"] for d in daily)
        if cumulative > 0:
            return {"level": 2, "reason": f"單日反轉，今日{today_total:+,}張"}

    # Level 1：動能減弱（近5日均 vs 前5日均，降幅>30%）
    if len(daily) >= 10:
        recent = [d["total"] for d in daily[-5:]]
        prev   = [d["total"] for d in daily[-10:-5]]
        r_avg = sum(recent) / 5
        p_avg = sum(prev) / 5
        if p_avg > 0 and r_avg < p_avg * 0.7:
            return {"level": 1, "reason": "動能減弱>30%"}

    return {"level": 0, "reason": "safe"}

# ── 讀取 predictions.json，取出有效持倉紀錄 ──────────────────
def load_active_predictions():
    path = ROOT / "data" / "predictions" / "predictions.json"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    recs = []
    for date_key, val in raw.items():
        if not (isinstance(date_key, str) and len(date_key) == 10 and date_key[4] == "-"):
            continue
        preds = val.get("predictions", [])
        if not preds:
            continue
        for p in preds:
            symbol = p.get("symbol", "")
            rec_price = p.get("recommend_price")
            stop_loss = p.get("stop_loss")
            target    = p.get("target_price")
            result    = p.get("result", "holding")
            settled   = p.get("settled_date", "") or ""
            stop_pct  = p.get("stop_loss_pct", -10)

            # 只處理有有效推薦價和停損的紀錄
            try:
                rec_price = float(rec_price)
                stop_loss = float(stop_loss) if stop_loss else rec_price * (1 + stop_pct / 100)
            except (TypeError, ValueError):
                continue

            if rec_price <= 0:
                continue

            recs.append({
                "symbol":       symbol,
                "rec_date":     date_key,
                "rec_price":    rec_price,
                "stop_loss":    stop_loss,
                "target":       float(target) if target else None,
                "result":       result,
                "settled_date": settled,
            })
    return recs

# ── 取得股票歷史收盤價 ─────────────────────────────────────
_price_cache = {}

def get_prices_after(symbol: str, from_date: str, days: int = 15) -> dict:
    """回傳 {date_str: close_price}，from_date 之後 days 個交易日"""
    global _price_cache
    key = symbol
    if key not in _price_cache:
        try:
            import yfinance as yf
            ticker = f"{symbol}.TW"
            df = yf.download(ticker, start="2026-05-01", progress=False)[["Close"]]
            df.index = df.index.strftime("%Y%m%d")
            _price_cache[key] = {d: float(row["Close"].iloc[0]) for d, row in df.iterrows()}
        except Exception:
            _price_cache[key] = {}

    prices = _price_cache[key]
    result = {}
    count = 0
    for d in sorted(prices):
        if d > from_date and count < days:
            result[d] = prices[d]
            count += 1
    return result

# ── 主流程 ─────────────────────────────────────────────────
def main():
    all_dates = get_trading_dates_in_cache()
    print(f"T86 快取：{all_dates[0]} ~ {all_dates[-1]}（{len(all_dates)} 天）\n")

    recs = load_active_predictions()
    print(f"有效持倉紀錄：{len(recs)} 筆\n")

    # 針對每個 T86 日期，找出當天在 holding 的股票
    events = []  # Level 3+ 事件
    checked = set()

    for date in all_dates:
        t86_day = load_t86(date)
        if not t86_day:
            continue

        for rec in recs:
            sym = rec["symbol"]
            if sym not in t86_day:
                continue

            rec_date    = rec["rec_date"].replace("-", "")
            settled_raw = rec["settled_date"].replace("-", "") if rec["settled_date"] else "99999999"

            # 只算「推薦日 <= 當日 < 結算日」的持倉期間
            if not (rec_date <= date < settled_raw):
                continue

            # 避免同一股票同一天重複計算（同股票可能有多筆推薦）
            # 取最近的那筆
            dedup_key = (sym, date)
            if dedup_key in checked:
                continue
            checked.add(dedup_key)

            rev = compute_reversal_level(sym, date, all_dates)
            if rev["level"] >= 3:
                events.append({
                    "signal_date": date,
                    "symbol":      sym,
                    "level":       rev["level"],
                    "reason":      rev["reason"],
                    "rec_date":    rec["rec_date"],
                    "rec_price":   rec["rec_price"],
                    "stop_loss":   rec["stop_loss"],
                    "target":      rec["target"],
                    "result":      rec["result"],
                    "settled_date":rec["settled_date"],
                })

    print(f"Level 3+ 持倉中訊號：{len(events)} 筆\n")
    print("=" * 80)

    summary = {"sell_wins": 0, "hold_wins": 0, "draw": 0, "no_data": 0}
    rows = []

    for ev in events:
        sym        = ev["symbol"]
        sig_date   = ev["signal_date"]
        rec_price  = ev["rec_price"]
        stop_loss  = ev["stop_loss"]
        target     = ev["target"]

        # 取訊號當日收盤（賣出價）
        prices = get_prices_after(sym, sig_date, days=15)
        if not prices:
            summary["no_data"] += 1
            continue

        price_dates = sorted(prices)
        sell_price  = prices[price_dates[0]]  # 隔日賣出（訊號隔天開盤估算收盤）

        # 取最終結算價（結算日收盤 or 10日後 or 目前最新）
        final_price = prices[price_dates[-1]]  # 最晚可知的價格

        sell_return  = (sell_price - rec_price) / rec_price * 100
        hold_return  = (final_price - rec_price) / rec_price * 100
        diff         = hold_return - sell_return

        verdict = "draw"
        if diff > 3:
            verdict = "hold_wins"
        elif diff < -3:
            verdict = "sell_wins"
        summary[verdict] += 1

        rows.append({
            "訊號日":   f"{sig_date[:4]}-{sig_date[4:6]}-{sig_date[6:]}",
            "股票":     sym,
            "Lv":       ev["level"],
            "推薦價":   f"{rec_price:.1f}",
            "訊號日收": f"{sell_price:.1f}",
            "賣出%":    f"{sell_return:+.1f}%",
            "最終收":   f"{final_price:.1f}",
            "撐到底%":  f"{hold_return:+.1f}%",
            "結論":     "撐贏" if verdict == "hold_wins" else ("賣贏" if verdict == "sell_wins" else "平手"),
            "原因":     ev["reason"][:30],
        })

    # 輸出表格
    headers = ["訊號日", "股票", "Lv", "推薦價", "訊號日收", "賣出%", "最終收", "撐到底%", "結論"]
    widths  = [12, 6, 4, 8, 9, 8, 8, 9, 6]
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))

    for r in sorted(rows, key=lambda x: x["訊號日"]):
        line = "  ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths))
        print(line)
        print(f"    └ {r['原因']}")

    print()
    print("=" * 80)
    print(f"統計（差距 >3% 才算輸贏）：")
    total = len(rows)
    if total == 0:
        print("  無有效案例")
        return
    print(f"  撐到底勝：{summary['hold_wins']} ({summary['hold_wins']/total*100:.0f}%)")
    print(f"  賣出勝：  {summary['sell_wins']} ({summary['sell_wins']/total*100:.0f}%)")
    print(f"  平手：    {summary['draw']} ({summary['draw']/total*100:.0f}%)")
    print(f"  無價格：  {summary['no_data']}")
    print(f"  總計：    {total} 筆")

    if total > 0:
        avg_sell = sum(float(r["賣出%"].rstrip("%")) for r in rows) / total
        avg_hold = sum(float(r["撐到底%"].rstrip("%")) for r in rows) / total
        print(f"\n  平均賣出報酬：{avg_sell:+.1f}%")
        print(f"  平均撐到底報酬：{avg_hold:+.1f}%")

    # 按論點類型分析（簡易分類：從 reason 欄位推測）
    print()
    lv4 = [r for r in rows if r["Lv"] == 4]
    lv3 = [r for r in rows if r["Lv"] == 3]
    for label, grp in [("Level 4", lv4), ("Level 3", lv3)]:
        if grp:
            h_wins = sum(1 for r in grp if r["結論"] == "撐贏")
            s_wins = sum(1 for r in grp if r["結論"] == "賣贏")
            print(f"  {label}（{len(grp)}筆）：撐贏{h_wins} / 賣贏{s_wins} / 平手{len(grp)-h_wins-s_wins}")

if __name__ == "__main__":
    main()
