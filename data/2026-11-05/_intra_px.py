import sys,json,urllib.request
sys.path.insert(0,'scripts')
import settlement_checker as sc
codes=sys.argv[1:]
for c in codes:
    px=None
    for suf in ('.TW','.TWO'):
        try:
            r=urllib.request.Request(f'https://query1.finance.yahoo.com/v8/finance/chart/{c}{suf}?interval=1d&range=5d',headers={'User-Agent':'Mozilla/5.0'})
            j=json.load(urllib.request.urlopen(r,timeout=15))
            m=j['chart']['result'][0]['meta']; px=m['regularMarketPrice']; break
        except Exception as e: pass
    s=sc.get_close_series(c)
    prev=s[-1] if s else None
    print(c,px,prev, round((px/prev[1]-1)*100,2) if px and prev else None)
