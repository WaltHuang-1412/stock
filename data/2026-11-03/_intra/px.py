import json,sys,urllib.request
def q(code):
    for suf in ('.TW','.TWO'):
        try:
            r=urllib.request.Request(f'https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}?range=10d&interval=1d',headers={'User-Agent':'Mozilla/5.0'})
            d=json.load(urllib.request.urlopen(r,timeout=15))['chart']['result'][0]
            m=d['meta'];ts=d['timestamp'];c=d['indicators']['quote'][0]['close']
            import datetime
            rows=[(datetime.datetime.fromtimestamp(t).strftime('%m-%d'),x) for t,x in zip(ts,c) if x]
            prev=[x for dd,x in rows if dd!='11-03']
            return m['regularMarketPrice'],prev[-1],m.get('regularMarketTime'),prev[-2] if len(prev)>1 else None
        except Exception as e: err=e
    return None
for c in sys.argv[1:]:
    r=q(c)
    if r: print(c,r[0],'prev',round(r[1],2),'chg%',round((r[0]/r[1]-1)*100,2),'prev2',r[3])
    else: print(c,'FAIL')
