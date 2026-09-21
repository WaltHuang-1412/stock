#!/usr/bin/env python3
"""
量測 TWSE T86（三大法人買賣超）當日實際公布時點

動機：2026-09-21 把盤後排程由 14:30 改為 16:00，理由是「14:30 時 T86 尚未公布」。
      但 14:30 查無、隔日 08:0x 查得到 —— 公布時點只知道落在這 18 小時之間，
      16:00 是依慣例推測而非量測。本腳本把它量出來，避免用猜的訂排程。

作法：從指定時間起每 5 分鐘打一次 T86，記錄第一次拿到資料的時刻，寫入
      data/cache/t86_publish_probe.jsonl（每日一行，可累積多日驗證）。

用法：
    python scripts/probe_t86_publish_time.py                    # 今日，14:00 起探測至 18:00
    python scripts/probe_t86_publish_time.py --start 14:00 --until 18:00 --interval 5
"""

import sys
import os
import io
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests

os.environ['PYTHONUTF8'] = '1'

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT = PROJECT_DIR / "data" / "cache" / "t86_publish_probe.jsonl"
TPE = timezone(timedelta(hours=8))


def t86_available(date_yyyymmdd):
    """回傳 (是否有資料, 筆數或錯誤訊息)"""
    url = (
        "https://www.twse.com.tw/rwd/zh/fund/T86"
        f"?date={date_yyyymmdd}&selectType=ALL&response=json"
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        data = r.json()
        rows = data.get("data") or []
        return (len(rows) > 0), len(rows)
    except Exception as exc:
        return False, f"error: {exc}"


def parse_hhmm(s):
    h, m = s.split(":")
    return int(h), int(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYYMMDD，預設今日")
    ap.add_argument("--start", default="14:00")
    ap.add_argument("--until", default="18:00")
    ap.add_argument("--interval", type=int, default=5, help="分鐘")
    args = ap.parse_args()

    import urllib3
    urllib3.disable_warnings()

    now = datetime.now(TPE)
    date_str = args.date or now.strftime("%Y%m%d")

    sh, sm = parse_hhmm(args.start)
    uh, um = parse_hhmm(args.until)
    start_at = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
    until_at = now.replace(hour=uh, minute=um, second=0, microsecond=0)

    if now < start_at:
        wait = (start_at - now).total_seconds()
        print(f"[等待] 現在 {now:%H:%M}，{args.start} 開始探測 T86 {date_str}（等 {wait/60:.0f} 分鐘）", flush=True)
        time.sleep(wait)

    attempts = []
    found_at = None
    row_count = None

    while True:
        t = datetime.now(TPE)
        if t > until_at:
            print(f"[結束] 已過 {args.until} 仍未取得 T86 {date_str}", flush=True)
            break

        ok, info = t86_available(date_str)
        stamp = t.strftime("%H:%M:%S")
        attempts.append({"at": stamp, "ok": ok, "info": info})
        print(f"  {stamp}  {'✅ 有資料 %s 筆' % info if ok else '❌ 查無 (%s)' % info}", flush=True)

        if ok:
            found_at = stamp
            row_count = info
            break

        time.sleep(args.interval * 60)

    record = {
        "date": date_str,
        "probed_on": now.strftime("%Y-%m-%d"),
        "start": args.start,
        "until": args.until,
        "interval_min": args.interval,
        "first_available_at": found_at,
        "row_count": row_count if found_at else None,
        "attempts": attempts,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print()
    if found_at:
        print(f"[結果] T86 {date_str} 首次可取得時間 = {found_at}（{row_count} 筆）")
        hh, mm, _ = found_at.split(":")
        mins = int(hh) * 60 + int(mm)
        if mins > 16 * 60:
            print("[警告] 晚於 16:00 —— 盤後排程 16:00 仍會撲空，須再往後調")
        else:
            print("[OK] 早於 16:00 —— 盤後排程設 16:00 可取得當日法人資料")
    else:
        print(f"[結果] 探測區間內未取得，盤後排程 16:00 的假設無法成立，須延後或改用其他資料源")
    print(f"[存檔] {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
