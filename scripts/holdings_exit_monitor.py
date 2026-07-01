#!/usr/bin/env python3
"""
持倉出場監控 — 盤中持續監控實際持股的出場訊號 + 推薦股回檔買入提醒

監控對象：portfolio/my_holdings.yaml 中 quantity > 0 的股票
出場訊號：
  🔴 停損預警  ：現價距停損 ≤3%（接近觸發）
  🔴 停損觸發  ：現價 ≤ 停損價
  ⚠️  前週低點  ：現價跌破前週K棒低點（盤中預警）
  📅 週五確認  ：週K收盤 < 前週低點 → Method C 出場
  📅 週五確認  ：週K收盤 < 週線20MA → Method B 出場

買入提醒：
  📉 回到推薦價：今日推薦股現價 ≤ tracking.json 的 recommend_price → 可考慮進場

用法：
    python scripts/holdings_exit_monitor.py           # 執行一次
    python scripts/holdings_exit_monitor.py --loop    # 持續監控到收盤
    python scripts/holdings_exit_monitor.py --dry-run # 測試（不推 LINE）
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Windows cp950 不支援 emoji，強制 utf-8 輸出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml
import yfinance as yf
import pandas as pd
import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
HOLDINGS_FILE = PROJECT_DIR / "portfolio" / "my_holdings.yaml"
ALERT_LOG_FILE = PROJECT_DIR / "data" / "holdings_monitor_alert_log.json"
LOCK_FILE = PROJECT_DIR / "data" / "holdings_monitor.lock"


def acquire_lock():
    """確保只有一個 instance 在執行，已有程序跑時直接退出。"""
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            import psutil
            if psutil.pid_exists(pid):
                print(f"[lock] 已有程序在執行（PID {pid}），退出")
                sys.exit(0)
        except Exception:
            pass
    LOCK_FILE.write_text(str(os.getpid()))


def release_lock():
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass

MARKET_OPEN  = "09:00"
MARKET_CLOSE = "13:30"
CHECK_INTERVAL = 300  # 5 分鐘

DRY_RUN = "--dry-run" in sys.argv

# === .env 載入 ===
env_file = PROJECT_DIR / ".env"
if env_file.exists():
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


# ── 持倉載入 ─────────────────────────────────────────────

def load_holdings():
    with open(HOLDINGS_FILE, encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return [h for h in d.get("holdings", []) if float(h.get("quantity", 0)) > 0]


# ── 市場偵測（上市 .TW / 上櫃 .TWO）────────────────────
# 執行期間快取，避免同一股票重複偵測

_market_cache = {}  # code -> "TW" or "TWO"

def detect_market(code):
    """回傳 'TW'（上市）或 'TWO'（上櫃），結果快取整個執行期。"""
    if code in _market_cache:
        return _market_cache[code]
    url = (f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
           f"?ex_ch=tse_{code}.tw&json=1")
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0",
                                       "Referer": "https://mis.twse.com.tw/"},
                         timeout=6)
        items = r.json().get("msgArray", [])
        if items and items[0].get("c") == code:
            _market_cache[code] = "TW"
            return "TW"
    except Exception:
        pass
    _market_cache[code] = "TWO"
    return "TWO"


# ── 即時價格（上市 / 上櫃 自動判斷）─────────────────────

def fetch_realtime(code):
    market = detect_market(code)
    exchange = "tse" if market == "TW" else "otc"
    url = (f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
           f"?ex_ch={exchange}_{code}.tw&json=1")
    try:
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://mis.twse.com.tw/",
        }, timeout=10)
        items = r.json().get("msgArray", [])
        if items:
            item = items[0]
            price_str = item.get("z", "")
            if price_str and price_str != "-":
                return float(price_str)
            y = item.get("y", "")
            if y:
                return float(y)
    except Exception:
        pass
    return None


# ── 週線資料（yfinance，當日快取）────────────────────────

_weekly_cache = {}
_weekly_cache_date = None

def get_weekly_data(code):
    global _weekly_cache_date
    today = datetime.now().strftime("%Y-%m-%d")
    if _weekly_cache_date != today:
        _weekly_cache.clear()
        _weekly_cache_date = today

    if code in _weekly_cache:
        return _weekly_cache[code]

    start = (datetime.now() - timedelta(weeks=104)).strftime("%Y-%m-%d")
    market = detect_market(code)
    suffix = ".TW" if market == "TW" else ".TWO"
    try:
        df = yf.download(f"{code}{suffix}", start=start,
                         interval="1wk", auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df[df["Close"].notna()]
        _weekly_cache[code] = df
        return df
    except Exception:
        return None


def get_prev_week_low(weekly):
    """前一根完整週K的低點"""
    if weekly is None or len(weekly) < 2:
        return None
    return float(weekly.iloc[-2]["Low"])




def get_weekly_ma20(weekly):
    """最新一根完整週K的 20MA 值"""
    if weekly is None or len(weekly) < 21:
        return None
    closes = weekly["Close"].values
    if len(closes) < 20:
        return None
    return float(closes[-20:].mean())


def get_latest_weekly_close(weekly):
    if weekly is None or len(weekly) == 0:
        return None
    return float(weekly.iloc[-1]["Close"])


# ── 訊號檢查 ──────────────────────────────────────────────

def check_holding(h, is_friday):
    code = h["symbol"]
    name = h["name"]
    buy_price = float(h["buy_price"])
    stop_loss = h.get("stop_loss")
    if stop_loss is not None:
        stop_loss = float(stop_loss)
    else:
        stop_loss = buy_price * 0.90  # 無設定預設 -10%

    price = fetch_realtime(code)
    if price is None:
        return None

    weekly = get_weekly_data(code)
    prev_low = get_prev_week_low(weekly)
    ma20 = get_weekly_ma20(weekly)
    ret = (price - buy_price) / buy_price * 100

    alerts = []

    # 停損觸發
    if price <= stop_loss:
        alerts.append({
            "level": "STOP",
            "msg": f"🔴 停損觸發：現價 {price} ≤ 停損 {stop_loss:.2f}（{ret:+.1f}%）→ 立即出場"
        })
    # 停損預警（距停損 3% 內）
    elif stop_loss and price <= stop_loss * 1.03:
        dist = (price - stop_loss) / stop_loss * 100
        alerts.append({
            "level": "WARN",
            "msg": f"⚠️ 接近停損：現價 {price}，距停損 {stop_loss:.2f} 僅 {dist:.1f}%（{ret:+.1f}%）"
        })

    # Method C 盤中預警：跌破前週低點
    if prev_low and price < prev_low:
        alerts.append({
            "level": "WARN",
            "msg": f"⚠️ 跌破前週低點 {prev_low:.2f}（現價 {price}，{ret:+.1f}%）"
        })

    # 週五收盤確認（只在收盤後才判斷，避免盤中未完成的週K誤觸）
    if is_friday and datetime.now().strftime("%H:%M") >= MARKET_CLOSE:
        weekly_close = get_latest_weekly_close(weekly)
        if weekly_close:
            # Method C：週收盤 < 前週低點
            if prev_low and weekly_close < prev_low:
                alerts.append({
                    "level": "EXIT",
                    "msg": f"📅 [Method C] 週收盤 {weekly_close} < 前週低點 {prev_low:.2f} → 下週一出場"
                })
            # Method B：週收盤 < 週線 20MA
            if ma20 and weekly_close < ma20:
                alerts.append({
                    "level": "EXIT",
                    "msg": f"📅 [Method B] 週收盤 {weekly_close} < 週線20MA {ma20:.2f} → 下週一出場"
                })

    if alerts:
        return {"code": code, "name": name, "price": price, "ret": ret, "alerts": alerts}
    return None


# ── 告警去重 ──────────────────────────────────────────────

def load_alert_log():
    if not ALERT_LOG_FILE.exists():
        return {}
    with open(ALERT_LOG_FILE, encoding="utf-8") as f:
        log = json.load(f)
    # 清除 7 天前的舊紀錄（key 格式為 {code}_{YYYY-MM-DD}_{level}）
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    return {k: v for k, v in log.items()
            if len(k.split("_")) >= 3 and k.split("_")[1] >= cutoff}


def save_alert_log(log):
    ALERT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def should_alert(log, code, level, today):
    # 同一檔股票同一種訊號，一天只推一次
    key = f"{code}_{today}_{level}"
    return key not in log


def mark_alerted(log, code, level, today):
    key = f"{code}_{today}_{level}"
    log[key] = datetime.now().strftime("%H:%M")


# ── LINE 推送 ─────────────────────────────────────────────

def send_line(text):
    # 出場警告用獨立的 alert token（新 bot），不與分析群組共用
    token   = os.environ.get("LINE_ALERT_CHANNEL_TOKEN", "") or os.environ.get("LINE_CHANNEL_TOKEN", "")
    user_id = os.environ.get("LINE_USER_ID", "")
    send_to = user_id
    if not token or not send_to:
        print("  LINE 未設定，跳過推送")
        return
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"to": send_to, "messages": [{"type": "text", "text": text}]},
        timeout=10,
    )
    if resp.status_code == 200:
        print("  LINE 推送成功")
    else:
        print(f"  LINE 推送失敗: {resp.status_code}")


# ── 買入訊號：推薦股監控 ──────────────────────────────────

def load_recommendations():
    """讀取今日 tracking.json 的 holding 推薦股"""
    today = datetime.now().strftime("%Y-%m-%d")
    f = PROJECT_DIR / "data" / "tracking" / f"tracking_{today}.json"
    if not f.exists():
        return []
    try:
        d = json.load(open(f, encoding="utf-8"))
        recs = [r for r in d.get("recommendations", [])
                if r.get("result", "holding") == "holding"]
        recs += [r for r in d.get("track_b_recommendations", [])
                 if r.get("result", "holding") == "holding"]
        return recs
    except Exception:
        return []


def check_buy_signal(rec):
    """回到推薦價提醒：現價 ≤ 推薦價 → 可考慮進場"""
    code = str(rec.get("stock_code") or rec.get("symbol", ""))
    name = rec.get("stock_name") or rec.get("name", code)
    recommend_price = rec.get("recommend_price")
    if not recommend_price:
        return None
    recommend_price = float(recommend_price)

    price = fetch_realtime(code)
    if not price:
        return None

    if price <= recommend_price:
        diff_pct = (price - recommend_price) / recommend_price * 100
        return {
            "code": code, "name": name, "price": price,
            "recommend_price": recommend_price,
            "msg": f"📉 回到推薦價：現價 {price} ≤ 推薦 {recommend_price}（{diff_pct:+.1f}%）→ 可考慮進場"
        }
    return None


# ── 主要邏輯 ──────────────────────────────────────────────

def is_market_hours():
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    t = now.strftime("%H:%M")
    return MARKET_OPEN <= t <= MARKET_CLOSE


def run_once():
    now = datetime.now()

    if not DRY_RUN and not is_market_hours():
        print(f"[{now.strftime('%H:%M:%S')}] 非盤中時段，跳過")
        return

    is_friday = (now.weekday() == 4)
    today = now.strftime("%Y-%m-%d")
    print(f"[{now.strftime('%H:%M:%S')}] 持倉檢查中...{'（週五確認）' if is_friday else ''}{'（dry-run）' if DRY_RUN else ''}")

    holdings = load_holdings()
    if not holdings:
        print("  無持倉")
        return

    alert_log = load_alert_log()
    triggered = []

    for h in holdings:
        result = check_holding(h, is_friday)
        if not result:
            continue
        code, name, price, ret = result["code"], result["name"], result["price"], result["ret"]
        print(f"  {code} {name}：現價 {price}（{ret:+.1f}%）")
        for a in result["alerts"]:
            level = a["level"]
            if should_alert(alert_log, code, level, today):
                print(f"    → {a['msg']}")
                triggered.append(f"{name}（{code}）\n{a['msg']}")
                if not DRY_RUN:
                    mark_alerted(alert_log, code, level, today)
            else:
                print(f"    （已通知過）{a['msg'][:40]}...")

        time.sleep(0.3)

    if triggered:
        msg = f"📊 持倉出場訊號 {now.strftime('%m/%d %H:%M')}\n\n" + "\n\n".join(triggered)
        print(f"\n{msg}")
        if not DRY_RUN:
            send_line(msg)
            save_alert_log(alert_log)
    else:
        codes = [h["symbol"] for h in holdings]
        print(f"  {' '.join(codes)} — 無出場訊號")

    # ── 買入訊號：推薦股回到推薦價 ─────────────────────
    recs = load_recommendations()
    if recs:
        print(f"\n[買入掃描] {len(recs)} 檔推薦股...")
        buy_triggered = []
        for rec in recs:
            code = str(rec.get("stock_code") or rec.get("symbol", ""))
            name = rec.get("stock_name") or rec.get("name", code)
            recommend_price = rec.get("recommend_price")
            price = fetch_realtime(code)
            if price is None or not recommend_price:
                print(f"  {code} {name}：無法取得價格")
                continue
            recommend_price = float(recommend_price)
            diff_pct = (price - recommend_price) / recommend_price * 100
            if price <= recommend_price:
                alert_key = f"BUY_{code}_{today}_PRICE"
                print(f"  {code} {name}：現價 {price}，推薦 {recommend_price}（{diff_pct:+.1f}%）→ 📉 可進場")
                if alert_key not in alert_log:
                    buy_triggered.append(f"{name}（{code}）\n📉 回到推薦價：現價 {price} ≤ 推薦 {recommend_price}（{diff_pct:+.1f}%）→ 可考慮進場")
                    if not DRY_RUN:
                        alert_log[alert_key] = now.strftime("%H:%M")
                else:
                    print(f"    （今日已通知過）")
            else:
                print(f"  {code} {name}：現價 {price}，推薦 {recommend_price}（{diff_pct:+.1f}%）— 未回檔")
            time.sleep(0.3)

        if buy_triggered:
            msg = f"📉 回到推薦價 {now.strftime('%m/%d %H:%M')}\n\n" + "\n\n".join(buy_triggered)
            print(f"\n{msg}")
            if not DRY_RUN:
                send_line(msg)
                save_alert_log(alert_log)
        else:
            print("  — 無回檔訊號")


def run_loop():
    print(f"持倉監控啟動 — 每 {CHECK_INTERVAL // 60} 分鐘一次（{MARKET_OPEN}~{MARKET_CLOSE}）")
    holdings = load_holdings()
    print(f"監控 {len(holdings)} 檔：{' '.join(h['symbol'] for h in holdings)}")
    print()

    while True:
        if is_market_hours():
            run_once()
            next_t = (datetime.now() + timedelta(seconds=CHECK_INTERVAL)).strftime("%H:%M:%S")
            print(f"  下次：{next_t}\n")
            time.sleep(CHECK_INTERVAL)
        else:
            now = datetime.now()
            t = now.strftime("%H:%M")
            if t > MARKET_CLOSE:
                print(f"[{t}] 已收盤，監控結束")
                break
            elif t < MARKET_OPEN:
                wait = max(0, (datetime.strptime(MARKET_OPEN, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day) - now).seconds)
                print(f"[{t}] 尚未開盤，等待 {wait // 60} 分鐘...")
                time.sleep(min(wait, 60))
            else:
                time.sleep(30)


if __name__ == "__main__":
    if "--dry-run" not in sys.argv:
        acquire_lock()
    try:
        if "--loop" in sys.argv:
            run_loop()
        else:
            run_once()
    finally:
        if "--dry-run" not in sys.argv:
            release_lock()
