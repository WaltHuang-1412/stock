import sys,json
sys.path.insert(0,'scripts')
from datetime import datetime,timezone,timedelta
from yahoo_finance_api import _fetch_chart
import settlement_checker as sc
TPE=timezone(timedelta(hours=8))
codes=sys.argv[1].split(',')
out={}
for c in codes:
    r=_fetch_chart(c,'1d','1d')
    meta=r.get('meta') if r else None
    p=meta.get('regularMarketPrice') if meta else None
    t=meta.get('regularMarketTime') if meta else None
    s=sc.get_close_series(c) or []
    prior=[x for x in s if x[0]<'2026-09-23']
    pc=prior[-1] if prior else None
    p2=prior[-2] if len(prior)>1 else None
    ts=datetime.fromtimestamp(t,tz=TPE).strftime('%H:%M') if t else None
    chg=round((p/pc[1]-1)*100,2) if p and pc else None
    d2=round((p/p2[1]-1)*100,2) if p and p2 else None
    out[c]={'price':p,'time':ts,'prev':pc,'prev2':p2,'chg':chg,'drop2d':d2,'high':meta.get('regularMarketDayHigh') if meta else None,'low':meta.get('regularMarketDayLow') if meta else None}
    print(c,out[c])
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
