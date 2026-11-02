import sys,json,requests
sys.path.insert(0,'scripts')
import settlement_checker as sc
codes=sys.argv[1:]
H={'User-Agent':'Mozilla/5.0'}
for c in codes:
    px=None;pc=None;src=''
    for suf in ('.TW','.TWO'):
        try:
            r=requests.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{c}{suf}?interval=1d&range=5d',headers=H,timeout=15).json()
            m=r['chart']['result'][0]['meta']
            px=m.get('regularMarketPrice'); t=m.get('regularMarketTime'); src=suf; break
        except Exception as e: continue
    try:
        s=sc.get_close_series(c); pc=s[-1] if s else None
    except Exception as e: pc=str(e)
    print(c,px,t if px else '',pc)
