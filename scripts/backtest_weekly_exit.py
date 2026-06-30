"""
回測：比較三種出場策略
  A - 現行系統：固定目標價 / -10% 停損 / 10 交易日到期
  B - 週線 20MA：跌破週線 20MA 才出
  C - 前週低點：跌破前一根週K棒低點才出

進場資料來自 data/predictions/predictions.json
"""

import json
import sys
from pathlib import Path

import yfinance as yf
import pandas as pd
import numpy as np

PREDICTIONS_PATH = Path("data/predictions/predictions.json")
CACHE_DIR = Path("data/backtest_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_valid_recommendations():
    with open(PREDICTIONS_PATH, "r") as f:
        d = json.load(f)
    recs = []
    for date, entry in d.items():
        if not isinstance(entry, dict) or "predictions" not in entry:
            continue
        for p in entry["predictions"]:
            rp = p.get("recommend_price")
            sl = p.get("stop_loss")
            tp = p.get("target_price")
            result = p.get("result")
            symbol = p.get("symbol") or p.get("stock_code")
            if (
                isinstance(rp, (int, float))
                and isinstance(sl, (int, float))
                and isinstance(tp, (int, float))
                and result in ["success", "fail", "holding"]
                and symbol
            ):
                recs.append({
                    "date": date,
                    "symbol": str(symbol),
                    "recommend_price": float(rp),
                    "target_price": float(tp),
                    "stop_loss": float(sl),
                    "original_result": result,
                })
    return recs


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


def fetch_price_data(symbol: str):
    cache_d = CACHE_DIR / f"{symbol}_daily.parquet"
    cache_w = CACHE_DIR / f"{symbol}_weekly.parquet"
    ticker = f"{symbol}.TW"
    try:
        if cache_d.exists():
            daily = pd.read_parquet(cache_d)
        else:
            daily = yf.download(ticker, start="2025-01-01", end="2026-12-31",
                                interval="1d", auto_adjust=True, progress=False)
            daily = flatten_columns(daily)
            if daily.empty:
                return None, None
            daily.to_parquet(cache_d)

        if cache_w.exists():
            weekly = pd.read_parquet(cache_w)
        else:
            weekly = yf.download(ticker, start="2024-01-01", end="2026-12-31",
                                 interval="1wk", auto_adjust=True, progress=False)
            weekly = flatten_columns(weekly)
            if weekly.empty:
                return daily, None
            weekly.to_parquet(cache_w)

        return daily, weekly
    except Exception as e:
        print(f"  fetch error {symbol}: {e}", file=sys.stderr)
        return None, None


def get_scalar(val):
    if isinstance(val, pd.Series):
        return float(val.iloc[0])
    return float(val)


def simulate_method_a(daily, entry_date, recommend_price, target_price, stop_loss):
    entry_dt = pd.Timestamp(entry_date)
    future = daily.index[daily.index > entry_dt][:10]
    if len(future) == 0:
        return None
    for dt in future:
        row = daily.loc[dt]
        low = get_scalar(row["Low"])
        high = get_scalar(row["High"])
        close = get_scalar(row["Close"])
        if low <= stop_loss:
            exit_price, exit_date, result = stop_loss, dt, "fail"
            break
        if high >= target_price:
            exit_price, exit_date, result = target_price, dt, "success"
            break
    else:
        exit_date = future[-1]
        exit_price = get_scalar(daily.loc[exit_date, "Close"])
        result = "success" if exit_price > recommend_price else "fail"
    holding = len(future[:list(future).index(exit_date) + 1])
    ret = (exit_price - recommend_price) / recommend_price * 100
    return {"result": result, "ret": ret, "holding_days": holding,
            "exit_price": exit_price, "exit_date": str(exit_date.date())}


MIN_WEEKS = 4  # 至少持有 4 週，才讓 MA20 / 前週低點 觸發出場


def simulate_method_b(daily, weekly, entry_date, recommend_price, stop_loss):
    if weekly is None or len(weekly) < 21:
        return None
    w = weekly.copy()
    w["MA20"] = w["Close"].rolling(20).mean()
    entry_dt = pd.Timestamp(entry_date)
    future_w = w[w.index > entry_dt]
    # 過濾掉 Close 為 NaN 的未來週（資料尚未收盤）
    future_w = future_w[future_w["Close"].notna()]
    # 樣本需至少 MIN_WEEKS 根週K，否則視為「資料不足」跳過
    if len(future_w) < MIN_WEEKS:
        return None
    exit_date = exit_price = result = None
    for i, (dt, row) in enumerate(future_w.iterrows()):
        close = get_scalar(row["Close"])
        ma20 = get_scalar(row["MA20"])
        # 停損不受最少持有週數限制
        if close <= stop_loss:
            exit_price, exit_date, result = stop_loss, dt, "fail"
            break
        if pd.isna(ma20):
            continue
        # 最少持有 MIN_WEEKS 週後才允許 MA20 觸發
        if i >= MIN_WEEKS and close < ma20:
            exit_price, exit_date = close, dt
            result = "success" if close > recommend_price else "fail"
            break
    if exit_date is None:
        # 尚未觸發訊號，用最新收盤價強制結算（mark_to_market）
        exit_date = future_w.index[-1]
        exit_price = get_scalar(future_w.iloc[-1]["Close"])
        result = "success" if exit_price > recommend_price else "fail"
    holding = len(daily.index[(daily.index > entry_dt) & (daily.index <= exit_date)])
    ret = (exit_price - recommend_price) / recommend_price * 100
    return {"result": result, "ret": ret, "holding_days": holding,
            "exit_price": exit_price, "exit_date": str(exit_date.date())}


def simulate_method_c(daily, weekly, entry_date, recommend_price, stop_loss):
    if weekly is None or len(weekly) < 2:
        return None
    entry_dt = pd.Timestamp(entry_date)
    future_w = weekly[weekly.index > entry_dt]
    future_w = future_w[future_w["Close"].notna()]
    if len(future_w) < MIN_WEEKS:
        return None

    past_w = weekly[weekly.index <= entry_dt]
    prev_low = get_scalar(past_w.iloc[-1]["Low"]) if len(past_w) > 0 else None

    exit_date = exit_price = result = None
    for i, (dt, row) in enumerate(future_w.iterrows()):
        close = get_scalar(row["Close"])
        w_low = get_scalar(row["Low"])
        if close <= stop_loss:
            exit_price, exit_date, result = stop_loss, dt, "fail"
            break
        # 最少持有 MIN_WEEKS 週後才允許前週低點觸發
        if i >= MIN_WEEKS and prev_low is not None and close < prev_low:
            exit_price, exit_date = close, dt
            result = "success" if close > recommend_price else "fail"
            break
        prev_low = w_low
    if exit_date is None:
        exit_date = future_w.index[-1]
        exit_price = get_scalar(future_w.iloc[-1]["Close"])
        result = "success" if exit_price > recommend_price else "fail"
    holding = len(daily.index[(daily.index > entry_dt) & (daily.index <= exit_date)])
    ret = (exit_price - recommend_price) / recommend_price * 100
    return {"result": result, "ret": ret, "holding_days": holding,
            "exit_price": exit_price, "exit_date": str(exit_date.date())}


def calc_stats(results, label):
    all_valid = [r for r in results if r is not None]
    valid = [r for r in all_valid if r["result"] in ("success", "fail")]
    if not valid:
        print(f"\n{label}: 無有效資料")
        return
    holding_count = 0
    rets = [r["ret"] for r in valid if not np.isnan(r["ret"])]
    wins = [r for r in valid if r["result"] == "success"]
    losses = [r for r in valid if r["result"] == "fail"]
    h_days = [r["holding_days"] for r in valid]
    win_rate = len(wins) / len(valid) * 100
    avg_ret = np.nanmean(rets)
    avg_win = np.nanmean([r["ret"] for r in wins]) if wins else 0
    avg_loss = np.nanmean([r["ret"] for r in losses]) if losses else 0
    avg_hold = np.mean(h_days)
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

    print(f"\n{'='*52}")
    print(f"  {label}")
    print(f"{'='*52}")
    skipped = len([r for r in results if r is None])
    print(f"  樣本數       : {len(valid)}（跳過 {skipped} 筆資料不足）")
    print(f"  勝率         : {win_rate:.1f}%  ({len(wins)}勝 / {len(losses)}敗)")
    print(f"  平均報酬     : {avg_ret:+.2f}%")
    print(f"  平均獲利     : {avg_win:+.2f}%")
    print(f"  平均虧損     : {avg_loss:+.2f}%")
    print(f"  期望值       : {expectancy:+.2f}%")
    print(f"  平均持有天數 : {avg_hold:.1f} 日")

    bins = [-999, -10, -5, 0, 5, 10, 20, 999]
    labels_b = ["<-10%", "-10~-5%", "-5~0%", "0~5%", "5~10%", "10~20%", ">20%"]
    counts = pd.cut(rets, bins=bins, labels=labels_b).value_counts().sort_index()
    print("  報酬分佈:")
    total = sum(counts)
    for lb, cnt in counts.items():
        bar = "█" * int(cnt / max(counts) * 18) if max(counts) > 0 else ""
        pct = cnt / total * 100 if total > 0 else 0
        print(f"    {lb:>10s}: {cnt:3d} ({pct:4.1f}%)  {bar}")


def main():
    print("載入推薦資料...")
    recs = load_valid_recommendations()
    print(f"有效樣本: {len(recs)} 筆（{recs[0]['date']} ~ {recs[-1]['date']}）")

    symbols = list(set(r["symbol"] for r in recs))
    print(f"涉及股票: {len(symbols)} 檔，開始下載價格資料...")

    price_cache = {}
    failed = []
    for i, sym in enumerate(symbols):
        sys.stdout.write(f"\r  [{i+1}/{len(symbols)}] {sym}   ")
        sys.stdout.flush()
        daily, weekly = fetch_price_data(sym)
        if daily is None or len(daily) == 0:
            failed.append(sym)
        else:
            price_cache[sym] = (daily, weekly)
    print(f"\n完成，{len(failed)} 檔失敗: {failed[:10]}")

    results_a, results_b, results_c = [], [], []
    skipped = 0
    for rec in recs:
        sym = rec["symbol"]
        if sym not in price_cache:
            skipped += 1
            results_a.append(None); results_b.append(None); results_c.append(None)
            continue
        daily, weekly = price_cache[sym]
        results_a.append(simulate_method_a(daily, rec["date"], rec["recommend_price"],
                                           rec["target_price"], rec["stop_loss"]))
        results_b.append(simulate_method_b(daily, weekly, rec["date"], rec["recommend_price"],
                                           rec["stop_loss"]))
        results_c.append(simulate_method_c(daily, weekly, rec["date"], rec["recommend_price"],
                                           rec["stop_loss"]))

    print(f"\n回測完成（跳過 {skipped} 筆無資料）")
    calc_stats(results_a, "方法 A：現行系統（固定目標/停損/10日）")
    calc_stats(results_b, "方法 B：週線 20MA 跌破才出")
    calc_stats(results_c, "方法 C：前週K棒低點跌破才出")

    output = []
    for i, rec in enumerate(recs):
        output.append({
            "date": rec["date"],
            "symbol": rec["symbol"],
            "recommend_price": rec["recommend_price"],
            "original_result": rec["original_result"],
            "method_a": results_a[i],
            "method_b": results_b[i],
            "method_c": results_c[i],
        })
    out_path = Path("data/backtest_weekly_exit.json")
    with open(out_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n詳細結果已存至 {out_path}")


if __name__ == "__main__":
    main()
