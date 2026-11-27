"""軌道B 候選初篩（唯讀）：11-26 TOP50 買超 ×（>5K 張 或 avg_rank<=30）× 今日漲幅<3% × 非軌道A"""
import sys, json, time, datetime as dt, urllib.request

D = 'data/2026-11-27'
t = json.load(open('data/2026-11-26/institutional_top50.json', encoding='utf-8'))
TRACK_A = {'2880', '2603', '2610', '2412', '2379', '2615'}


def meta(code):
    for suf in ('.TW', '.TWO'):
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}?range=10d&interval=1d'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                j = json.load(r)['chart']['result'][0]
            if j['meta'].get('regularMarketPrice') is not None:
                return j
        except Exception:
            pass
    return None


rows = []
for s in t['stocks']:
    if s['total'] <= 0:
        continue
    c = s['code']
    lots = s['total'] / 1000
    if not (lots > 5000 or s['avg_rank'] <= 30):
        continue
    j = meta(c)
    if not j:
        rows.append(dict(code=c, name=s['name'], error='no quote'))
        continue
    m = j['meta']
    q = j['indicators']['quote'][0]
    bars = []
    for ts, cl, op, vol in zip(j['timestamp'], q['close'], q['open'], q['volume']):
        d = dt.datetime.fromtimestamp(ts, dt.timezone(dt.timedelta(hours=8))).strftime('%Y-%m-%d')
        bars.append((d, cl, op, vol))
    prev = [b for b in bars if b[0] < '2026-11-27' and b[1] is not None]
    pc = prev[-1][1]
    price = m['regularMarketPrice']
    chg = (price / pc - 1) * 100
    rows.append(dict(code=c, name=s['name'], lots=round(lots), rank=s['avg_rank'], price=price,
                     prev=round(pc, 2), prev_date=prev[-1][0], chg=round(chg, 2),
                     d5=s['5day_change'], track_a=c in TRACK_A))
    time.sleep(0.2)

json.dump(rows, open(D + '/_intraday/pool.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in rows:
    if 'error' in r:
        print(r['code'], r['name'], r['error'])
        continue
    ok = r['chg'] < 3 and not r['track_a']
    print(('✔' if ok else ' '), r['code'], r['name'], f"{r['lots']:+}張 rk{r['rank']} 現{r['price']} 前{r['prev']}({r['prev_date'][5:]}) {r['chg']:+}% 5日{r['d5']:+}", 'A' if r['track_a'] else '')
print('候選', ' '.join(r['code'] for r in rows if 'error' not in r and r['chg'] < 3 and not r['track_a']))
