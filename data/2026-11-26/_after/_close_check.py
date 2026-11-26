import sys, json, requests, urllib3
urllib3.disable_warnings()
sys.path.insert(0,'scripts')
import settlement_checker as sc
codes = ['2610','2412','2886','2379','2615','6770','2337','2313','3090','1301','4938','2330','2867']
off = {}
try:
    j = requests.get('https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20261126&type=ALLBUT0999&response=json', timeout=30, verify=False, headers={'User-Agent':'Mozilla/5.0'}).json()
    print('official date', j.get('date'))
    for t in j.get('tables', []):
        f = t.get('fields') or []
        if '證券代號' in f and '收盤價' in f:
            for row in t['data']:
                if row[0] in codes:
                    off[row[0]] = {k: row[f.index(k)] for k in ['開盤價','最高價','最低價','收盤價','成交股數']}
except Exception as e:
    print('official fail', e)
res = {}
for c in codes:
    s = sc.get_close_series(c)
    tail = s[-4:] if s else None
    res[c] = {'series': tail, 'official': off.get(c)}
    print(c, tail, '| TWSE', off.get(c))
json.dump(res, open('data/2026-11-26/_after/closes.json','w',encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
