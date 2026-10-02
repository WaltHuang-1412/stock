import sys, json, yaml, urllib.request, time
sys.path.insert(0, 'scripts')
import settlement_checker as sc
A = 'data/2026-10-02/_after/'
TODAY = '2026-10-02'
# code: (name, 推薦日, 推薦價, 目標, 停損)
H = {}
import glob, re
for line in open(A + '_settlement.txt', encoding='utf-8'):
    m = re.search(r'(\d{4}) (\S+) \[A\] 推薦日 (\d{4}-\d\d-\d\d)', line)
    if m: H[m.group(1)] = dict(name=m.group(2), date=m.group(3))
for c, v in H.items():
    t = json.load(open(f"data/tracking/tracking_{v['date']}.json", encoding='utf-8'))
    for r in t['recommendations'] + t.get('track_b_recommendations', []):
        if r['stock_code'] == c and r.get('recommend_date', v['date']) == v['date']:
            v.update(p=r['recommend_price'], tp=r['target_price'], sl=round(r['recommend_price'] * (1 + r.get('stop_loss_pct', -10) / 100), 2), sl_file=r.get('stop_loss'))
y = yaml.safe_load(open('portfolio/my_holdings.yaml', encoding='utf-8'))
Y = {h['symbol']: h for h in y['holdings'] if h.get('quantity')}
codes = sorted(set(H) | set(Y))
# TWSE MIS 收盤
mis = {}
for ex in ('tse', 'otc'):
    for i in range(0, len(codes), 5):
        q = '|'.join(f'{ex}_{c}.tw' for c in codes[i:i + 5])
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(f'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={q}&json=1&delay=0', headers={'User-Agent': 'Mozilla/5.0'}), timeout=15))
            for a in d.get('msgArray', []):
                mis[a['c']] = dict(z=a.get('z'), y=a.get('y'), t=a.get('t'), d=a.get('d'), l=a.get('l'), h=a.get('h'), n=a.get('n'))
        except Exception as e: print('MIS err', q, e)
        time.sleep(1.5)
json.dump(mis, open(A + 'mis_close.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
rows = {}
for c in codes:
    s = sc.get_close_series(c)
    tail = s[-4:] if s else None
    m = mis.get(c, {})
    v = dict(H.get(c, {}))
    v['tail'] = tail; v['mis'] = m
    if c in Y: v['yaml'] = dict(name=Y[c]['name'], qty=Y[c]['quantity'], stop=Y[c].get('stop_loss'), buy=Y[c].get('buy_price'))
    rows[c] = v
    nm = v.get('name') or Y[c]['name']
    print(c, nm, '|series', [(d[5:], x) for d, x in tail] if tail else None, '|MIS z', m.get('z'), 'y', m.get('y'), 'l', m.get('l'), m.get('d'), m.get('t'),
          '|rec', v.get('date'), v.get('p'), 'tp', v.get('tp'), 'sl', v.get('sl'), v.get('sl_file'), '|yaml', v.get('yaml'))
json.dump(rows, open(A + 'rows_raw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
