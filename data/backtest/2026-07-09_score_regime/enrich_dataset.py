# -*- coding: utf-8 -*-
"""補值:avg_rank 從原始張數重算、vs_ma20 從 Yahoo 歷史價計算、TAIEX 序列、TWSE 外資買賣金額"""
import json, glob, os, sys, time, datetime
import requests

ROOT = r'C:\Users\walter.huang\Documents\github\stock'
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

with open(os.path.join(SP, 'backtest_dataset.json'), encoding='utf-8') as f:
    rows = json.load(f)

# ---------- 1. avg_rank 補算 ----------
def compute_avg_rank(date):
    path = os.path.join(ROOT, f'data/{date}/institutional_top50.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
    except Exception:
        return {}
    buys = [s for s in d.get('stocks', []) if (s.get('total') or 0) > 0]
    out = {}
    for s in buys:
        if s.get('avg_rank') is not None:
            out[str(s['code'])] = s['avg_rank']
    if out:
        return out
    # fallback: volume_rank + amount_rank 平均
    if buys and buys[0].get('volume_rank') and buys[0].get('amount_rank'):
        for s in buys:
            out[str(s['code'])] = (s['volume_rank'] + s['amount_rank']) / 2
        return out
    # fallback2: 只有原始張數 → 按 total 排名
    buys.sort(key=lambda s: -(s.get('total') or 0))
    for i, s in enumerate(buys, 1):
        out[str(s['code'])] = float(i)
    return out

rank_cache = {}
for r in rows:
    if r['avg_rank'] is None:
        if r['date'] not in rank_cache:
            rank_cache[r['date']] = compute_avg_rank(r['date'])
        r['avg_rank'] = rank_cache[r['date']].get(r['code'])

# ---------- 2. vs_ma20 補算(Yahoo 歷史價) ----------
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
print(f'需要抓歷史價的股票數: {len(need_codes)}')
for i, code in enumerate(need_codes):
    if code in hist_cache:
        continue
    hist_cache[code] = fetch_daily(code)
    time.sleep(0.25)
    if (i + 1) % 25 == 0:
        print(f'  {i+1}/{len(need_codes)}')
        with open(HIST_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(hist_cache, f)
with open(HIST_CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(hist_cache, f)

def vs_ma20_at(code, date):
    h = hist_cache.get(code)
    if not h:
        return None
    dates = sorted(h.keys())
    upto = [d for d in dates if d <= date]
    if len(upto) < 20:
        return None
    last20 = upto[-20:]
    ma20 = sum(h[d] for d in last20) / 20
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

# ---------- 3. TAIEX 序列(^TWII 不加後綴) ----------
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
print(f'TAIEX 序列天數: {len(taiex)}')
with open(os.path.join(SP, 'taiex_series.json'), 'w', encoding='utf-8') as f:
    json.dump(taiex, f)

# ---------- 4. TWSE 外資買賣金額(BFI82U)----------
# 先試一天,確認格式
def fetch_bfi82u(yyyymmdd):
    try:
        url = f'https://www.twse.com.tw/rwd/zh/fund/BFI82U?dayDate={yyyymmdd}&type=day&response=json'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        d = resp.json()
        if d.get('stat') != 'OK':
            return None
        for row_ in d.get('data', []):
            if '外資及陸資' in row_[0] and '自營' not in row_[0]:
                # 買進金額, 賣出金額, 買賣差額
                net = float(row_[3].replace(',', ''))
                return net / 1e8  # 億
    except Exception:
        return None
    return None

test = fetch_bfi82u('20260702')
print('BFI82U 測試 20260702 外資淨買賣(億):', test)

with open(os.path.join(SP, 'backtest_dataset.json'), 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

print('--- 補值後覆蓋率 ---')
print(f'avg_rank: {sum(1 for r in rows if r["avg_rank"] is not None)}/{len(rows)}')
print(f'vs_ma20: {sum(1 for r in rows if r["vs_ma20"] is not None)}/{len(rows)}')
print(f'ret: {sum(1 for r in rows if r["ret"] is not None)}/{len(rows)}')
