# -*- coding: utf-8 -*-
"""補值:vs_ma20 從 Yahoo 歷史價計算、TAIEX 序列(交易日曆)"""
import json, os, time, datetime
import requests

SP = os.path.dirname(os.path.abspath(__file__))
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

with open(os.path.join(SP, 'backtest_dataset.json'), encoding='utf-8') as f:
    rows = json.load(f)

# ---------- 1. vs_ma20 補算(Yahoo 歷史價) ----------
HIST_CACHE_FILE = os.path.join(SP, 'hist_cache.json')
hist_cache = {}
if os.path.exists(HIST_CACHE_FILE):
    with open(HIST_CACHE_FILE, encoding='utf-8') as f:
        hist_cache = json.load(f)

def fetch_daily(symbol, suffixes=('.TW', '.TWO')):
    """回傳 {date_str: close}"""
    for suf in suffixes:
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}{suf}?interval=1d&range=1y'
            resp = requests.get(url, headers=HEADERS, timeout=10)
            data = resp.json()
            res = data.get('chart', {}).get('result')
            if not res:
                continue
            res = res[0]
            ts = res.get('timestamp', [])
            closes = res['indicators']['quote'][0].get('close', [])
            out = {}
            for t, c in zip(ts, closes):
                if c is not None:
                    ds = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d')
                    out[ds] = c
            if out:
                return out
        except Exception:
            continue
    return None

need_codes = sorted({r['code'] for r in rows if r['vs_ma20'] is None})
todo = [c for c in need_codes if c not in hist_cache]
print(f'需要抓歷史價的股票數: {len(need_codes)}(cache 已有 {len(need_codes) - len(todo)})')
for i, code in enumerate(todo):
    hist_cache[code] = fetch_daily(code)
    time.sleep(0.25)
    if (i + 1) % 25 == 0:
        print(f'  {i+1}/{len(todo)}')
        with open(HIST_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(hist_cache, f)
with open(HIST_CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(hist_cache, f)

def vs_ma20_at(code, date):
    h = hist_cache.get(code)
    if not h:
        return None
    upto = sorted(d for d in h if d <= date)
    if len(upto) < 20:
        return None
    ma20 = sum(h[d] for d in upto[-20:]) / 20
    cur = h[upto[-1]]
    return (cur - ma20) / ma20 * 100

filled = 0
for r in rows:
    if r['vs_ma20'] is None:
        v = vs_ma20_at(r['code'], r['date'])
        if v is not None:
            r['vs_ma20'] = round(v, 2)
            r['vs_ma20_src'] = 'yahoo'
            filled += 1
print(f'vs_ma20 補了 {filled} 筆')

# ---------- 2. TAIEX 序列(交易日曆用) ----------
def fetch_index():
    try:
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5ETWII?interval=1d&range=1y'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        res = data['chart']['result'][0]
        ts = res['timestamp']
        closes = res['indicators']['quote'][0]['close']
        out = {}
        for t, c in zip(ts, closes):
            if c is not None:
                out[datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d')] = c
        return out
    except Exception as e:
        print('TAIEX fetch fail:', e)
        return {}

taiex = fetch_index()
print(f'TAIEX 序列天數: {len(taiex)}({min(taiex)} ~ {max(taiex)})' if taiex else 'TAIEX 抓取失敗')
with open(os.path.join(SP, 'taiex_series.json'), 'w', encoding='utf-8') as f:
    json.dump(taiex, f)

with open(os.path.join(SP, 'backtest_dataset.json'), 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print('--- 補值後覆蓋率 ---')
print(f'vs_ma20: {sum(1 for r in rows if r["vs_ma20"] is not None)}/{len(rows)}')
print(f'ret: {sum(1 for r in rows if r["ret"] is not None)}/{len(rows)}')
