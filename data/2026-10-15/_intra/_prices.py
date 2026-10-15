import sys,json,requests
sys.path.insert(0,'scripts')
import settlement_checker as sc
codes=sys.argv[1:]
out={}
for c in codes:
    px=None
    for suf in ('.TW','.TWO'):
        try:
            r=requests.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{c}{suf}?interval=1d&range=5d',headers={'User-Agent':'Mozilla/5.0'},timeout=15).json()
            m=r['chart']['result'][0]['meta']
            px=m['regularMarketPrice'];t=m['regularMarketTime'];vol=m.get('regularMarketVolume');break
        except Exception as e: pass
    try:
        s=sc.get_close_series(c); prev=s[-1] if s else None
    except Exception as e: prev=None
    out[c]=(px,prev)
    pc=None
    if px and prev: pc=round((px/prev[1]-1)*100,2)
    print(c,px,prev,pc,flush=True)
json.dump(out,open('data/2026-10-15/_intra/prices.json','w'))
