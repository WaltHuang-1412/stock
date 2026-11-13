import sys,json,urllib.request
sys.path.insert(0,'scripts')
import settlement_checker as sc
codes=sys.argv[1:]
for c in codes:
    px=None
    for suf in ('.TW','.TWO'):
        try:
            r=urllib.request.Request(f'https://query1.finance.yahoo.com/v8/finance/chart/{c}{suf}?interval=1d&range=5d',headers={'User-Agent':'Mozilla/5.0'})
            j=json.load(urllib.request.urlopen(r,timeout=15))['chart']['result'][0]
            px=j['meta']['regularMarketPrice'];break
        except Exception as e: pass
    try:
        s=sc.get_close_series(c); prev=s[-1] if s else None
    except Exception as e: prev=None
    print(c,'now',px,'lastclose',prev)
