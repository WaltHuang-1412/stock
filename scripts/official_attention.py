#!/usr/bin/env python3
"""
官方注意股／處置股資料（TWSE + TPEx）

取代 reversal_alert.check_disposition_risk 的「自算注意股」估計。
自算版只比對漲幅／週轉率，漏掉官方各款的附加條件，實測嚴重高估
（2026-10-12：1303 南亞自算連續達標 15 天，官方近 30 日僅公告 1 次、未處置）。

資料來源（皆為官方、免認證）：
- TWSE 注意交易資訊歷史  www.twse.com.tw/rwd/zh/announcement/notice?startDate&endDate
- TWSE 處置股            openapi.twse.com.tw/v1/announcement/punish
- TWSE 累計次數異常預告  openapi.twse.com.tw/v1/announcement/notetrans
- TWSE 交易日            www.twse.com.tw/rwd/zh/afterTrading/FMTQIK
- TPEx 注意（僅最新一日） www.tpex.org.tw/openapi/v1/tpex_trading_warning_information
- TPEx 處置 / 累計預告    tpex_disposal_information / tpex_trading_warning_note

處置條件（取自 TWSE notetrans 官方說明）：
- 連續 3 個營業日達第四條第一項「第一款」
- 或 連續 5 個營業日／最近 10 日內 6 日／最近 30 日內 12 日，達「第一款至第八款」任一款
- 處置期間內再被公告注意的次數不列入統計（官方揭露表已排除）

TPEx 只提供最新一日，歷史改由本模組每日快照累積（data/cache/tpex_attention_log.json），
累積天數不足時結果會標 coverage_days。

用法：
    python scripts/official_attention.py 1303 2340      # 查個股
    python scripts/official_attention.py --lists        # 印處置/注意清單
"""

import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "official_attention.json"
TPEX_LOG = CACHE_DIR / "tpex_attention_log.json"
CACHE_TTL = 3600  # 秒
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

_CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8,
       "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13}
_CLAUSE_RE = re.compile(r"第([一二三四五六七八九十]+)款")

_MEM = {"data": None, "at": 0.0}


def _roc_date(s):
    """'115.10.08' / '115/10/08' / '1151008' → date"""
    s = str(s).strip()
    m = re.match(r"^(\d{2,3})[./](\d{1,2})[./](\d{1,2})$", s)
    if m:
        y, mo, d = map(int, m.groups())
    elif re.match(r"^\d{7}$", s):
        y, mo, d = int(s[:3]), int(s[3:5]), int(s[5:])
    else:
        return None
    return date(y + 1911, mo, d)


def _get_json(url, timeout=20):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _clauses(text):
    out = set()
    for m in _CLAUSE_RE.finditer(text or ""):
        n = _CN.get(m.group(1))
        if n:
            out.add(n)
    return out


def _trading_days(months_back=3):
    """近幾個月的官方交易日（date 升冪）"""
    days = set()
    today = date.today()
    y, m = today.year, today.month
    for _ in range(months_back + 1):
        j = _get_json(f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={y}{m:02d}01&response=json")
        for row in j.get("data", []) or []:
            d = _roc_date(row[0])
            if d:
                days.add(d)
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return sorted(days)


def _fetch_all():
    """抓全部官方資料；任何一項核心資料失敗即丟例外（呼叫端退回 None）"""
    today = date.today()
    start = (today - timedelta(days=75)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    notice = _get_json(
        f"https://www.twse.com.tw/rwd/zh/announcement/notice?response=json&startDate={start}&endDate={end}",
        timeout=40)
    if notice.get("stat") != "OK":
        raise RuntimeError(f"TWSE notice stat={notice.get('stat')}")
    rows = []
    for r in notice.get("data", []) or []:
        d = _roc_date(r[5])
        if d:
            rows.append({"code": str(r[1]).strip(), "name": str(r[2]).strip(),
                         "date": d.isoformat(), "text": r[4]})

    data = {"fetched_at": datetime.now().isoformat(timespec="seconds"),
            "twse_notice": rows,
            "trading_days": [d.isoformat() for d in _trading_days()]}

    # 其餘來源：失敗不致命，缺哪項就留空並記錄
    data["errors"] = {}
    for key, url in (
        ("twse_punish", "https://openapi.twse.com.tw/v1/announcement/punish"),
        ("twse_warn", "https://openapi.twse.com.tw/v1/announcement/notetrans"),
        ("tpex_notice", "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_information"),
        ("tpex_punish", "https://www.tpex.org.tw/openapi/v1/tpex_disposal_information"),
        ("tpex_warn", "https://www.tpex.org.tw/openapi/v1/tpex_trading_warning_note"),
    ):
        try:
            data[key] = _get_json(url)
        except Exception as e:  # noqa: BLE001
            data[key] = []
            data["errors"][key] = str(e)[:120]
    return data


def _update_tpex_log(data):
    """TPEx 只給最新一日 → 每日快照累積成歷史"""
    try:
        log = json.loads(TPEX_LOG.read_text(encoding="utf-8")) if TPEX_LOG.exists() else {}
    except Exception:  # noqa: BLE001
        log = {}
    for r in data.get("tpex_notice", []):
        d = _roc_date(r.get("Date"))
        if not d:
            continue
        day = log.setdefault(d.isoformat(), {})
        day[r.get("SecuritiesCompanyCode", "")] = {
            "name": r.get("CompanyName", ""), "text": r.get("TradingInformation", "")}
    TPEX_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    return log


def load(force=False):
    """回傳官方資料 dict；失敗回 None（呼叫端應退回估計並標註）"""
    now = time.time()
    if not force and _MEM["data"] and now - _MEM["at"] < CACHE_TTL:
        return _MEM["data"]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not force and CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            age = (datetime.now() - datetime.fromisoformat(cached["fetched_at"])).total_seconds()
            if age < CACHE_TTL:
                cached["tpex_log"] = _update_tpex_log(cached)
                _MEM.update(data=cached, at=now)
                return cached
        except Exception:  # noqa: BLE001
            pass
    try:
        data = _fetch_all()
    except Exception as e:  # noqa: BLE001
        print(f"[official_attention] 官方資料抓取失敗：{e}", file=sys.stderr)
        return None
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    data["tpex_log"] = _update_tpex_log(data)
    _MEM.update(data=data, at=now)
    return data


def _period_active(period, today):
    """'115/10/08～115/10/15' 或 '1151008~1151015' 是否涵蓋 today"""
    parts = re.split(r"[～~]", str(period))
    if len(parts) != 2:
        return False
    a, b = _roc_date(parts[0]), _roc_date(parts[1])
    return bool(a and b and a <= today <= b)


def get_lists(data=None):
    """
    回傳 (disposed, attention, warn)：
    - disposed  今日仍在處置期間的代號（TWSE+TPEx）
    - attention 最近一個已公告日被列為注意的代號（TWSE+TPEx）
    - warn      官方「累計次數異常」預告：次一營業日再被公告注意即處置
    """
    data = data or load()
    if not data:
        return None
    today = date.today()
    disposed = {r["Code"] for r in data.get("twse_punish", [])
                if _period_active(r.get("DispositionPeriod", ""), today)}
    disposed |= {r["SecuritiesCompanyCode"] for r in data.get("tpex_punish", [])
                 if _period_active(r.get("DispositionPeriod", ""), today)}
    disposed = {c for c in disposed if re.fullmatch(r"\d{4}", c)}  # 排除權證

    rows = data.get("twse_notice", [])
    last = max((r["date"] for r in rows), default=None)
    attention = {r["code"] for r in rows if r["date"] == last}
    tpex_dates = [_roc_date(r.get("Date")) for r in data.get("tpex_notice", [])]
    tpex_last = max((d for d in tpex_dates if d), default=None)
    attention |= {r["SecuritiesCompanyCode"] for r in data.get("tpex_notice", [])
                  if _roc_date(r.get("Date")) == tpex_last}

    warn = {r["Code"] for r in data.get("twse_warn", [])}
    warn |= {r["SecuritiesCompanyCode"] for r in data.get("tpex_warn", [])}
    attention = {c for c in attention if re.fullmatch(r"\d{4}", c)}
    warn = {c for c in warn if re.fullmatch(r"\d{4}", c)}
    return disposed, attention, warn


def get_status(code, data=None):
    """
    個股官方注意股狀態；查無資料回 None。
    欄位：
      market            'TWSE' | 'TPEX'
      as_of             最近一個已公告的交易日
      dates             近 30 營業日內被公告注意的日期（升冪）
      consecutive_1     連續幾日達第一款（連 3 → 處置）
      consecutive_1_8   連續幾日達第一至八款（連 5 → 處置）
      in10 / in30       近 10 / 30 營業日達第一至八款的日數（6 / 12 → 處置）
      official_warn     官方預告：次日再被公告即處置
      days_to_disposition  若每天都持續被公告，最快還差幾天處置（無注意紀錄則 None）
      coverage_days     可用歷史營業日數（TPEx 初期會 <30）
      latest_text       最近一次公告的注意原因原文
    """
    data = data or load()
    if not data:
        return None
    code = str(code).strip()
    tdays = [date.fromisoformat(d) for d in data.get("trading_days", [])]
    rows = data.get("twse_notice", [])
    max_notice = max((date.fromisoformat(r["date"]) for r in rows), default=None)

    market, mine = "TWSE", []
    for r in rows:
        if r["code"] == code:
            mine.append((date.fromisoformat(r["date"]), _clauses(r["text"]), r["text"]))

    # TPEx：從累積快照取
    log = data.get("tpex_log", {})
    tpex_hit = any(code in v for v in log.values()) or any(
        r.get("SecuritiesCompanyCode") == code for r in data.get("tpex_notice", []))
    tpex_listed = any(r.get("SecuritiesCompanyCode") == code for r in data.get("tpex_punish", [])) \
        or any(r.get("SecuritiesCompanyCode") == code for r in data.get("tpex_warn", []))
    coverage = None
    if tpex_hit or tpex_listed:
        market = "TPEX"
        mine = []
        for d, v in log.items():
            if code in v:
                mine.append((date.fromisoformat(d), _clauses(v[code]["text"]), v[code]["text"]))
        coverage = len(log)
        max_notice = max((date.fromisoformat(d) for d in log), default=None)

    if not max_notice:
        return None
    done = [d for d in tdays if d <= max_notice]
    if not done:
        return None
    window = done[-30:]
    last = window[-1]

    by_day = {}
    for d, cl, txt in mine:
        cur = by_day.setdefault(d, [set(), ""])
        cur[0] |= cl
        cur[1] = txt
    wset = set(window)
    f1 = {d for d, (cl, _) in by_day.items() if d in wset and 1 in cl}
    f18 = {d for d, (cl, _) in by_day.items() if d in wset and any(1 <= c <= 8 for c in cl)}

    def run(flagset):
        n = 0
        for d in reversed(window):
            if d in flagset:
                n += 1
            else:
                break
        return n

    c1, c18 = run(f1), run(f18)
    in10 = sum(1 for d in window[-10:] if d in f18)
    in30 = sum(1 for d in window if d in f18)

    warn = {r["Code"] for r in data.get("twse_warn", [])} | \
           {r["SecuritiesCompanyCode"] for r in data.get("tpex_warn", [])}
    official_warn = code in warn

    # 只有「最近一個公告日仍被列注意」才有倒數意義（早已脫離者不算）
    routes = []
    if last in f18:
        routes = [3 - c1, 5 - c18, 6 - in10, 12 - in30]
    routes = [r for r in routes if r >= 1]
    dtd = min(routes) if routes else None
    if official_warn:
        dtd = 1

    last_txt = ""
    if by_day:
        last_txt = by_day[max(by_day)][1]
    return {
        "market": market,
        "as_of": last.isoformat(),
        "dates": sorted(d.isoformat() for d in by_day if d in window),
        "consecutive_1": c1,
        "consecutive_1_8": c18,
        "in10": in10,
        "in30": in30,
        "official_warn": official_warn,
        "days_to_disposition": dtd,
        "coverage_days": coverage if coverage is not None else len(window),
        "latest_text": last_txt,
    }


def main():
    args = sys.argv[1:]
    data = load(force=True)
    if not data:
        print("官方資料抓取失敗")
        sys.exit(1)
    if data.get("errors"):
        print("部分來源失敗：", data["errors"])
    if "--lists" in args or not args:
        disposed, attention, warn = get_lists(data)
        print(f"處置中 {len(disposed)}：{sorted(disposed)}")
        print(f"最近公告日注意 {len(attention)}：{sorted(attention)}")
        print(f"次日再被公告即處置（官方預告）：{sorted(warn)}")
    for c in [a for a in args if not a.startswith("--")]:
        print(c, json.dumps(get_status(c, data), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
