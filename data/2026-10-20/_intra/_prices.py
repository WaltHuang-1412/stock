import sys,json,datetime
sys.path.insert(0,'scripts')
from yahoo_finance_api import get_current_price
import settlement_checker as sc
codes=sys.argv[1:]
out={}
for c in codes:
    px=get_current_price(c)
    s=sc.get_close_series(c) or []
    # filter: keep only real daily bars (prev close = last bar whose date < today)
    prev=[x for x in s if str(x[0])<'2026-10-20']
    pc=prev[-1] if prev else None
    p2=prev[-2] if len(prev)>1 else None
    chg=(px/pc[1]-1)*100 if px and pc else None
    two=(px/p2[1]-1)*100 if px and p2 else None
    out[c]={'price':px,'prev_date':str(pc[0]) if pc else None,'prev_close':pc[1] if pc else None,'chg_pct':round(chg,2) if chg is not None else None,'two_day_pct':round(two,2) if two is not None else None,'series_last':str(s[-1][0]) if s else None}
    print(c,out[c])
json.dump({'time':datetime.datetime.now().isoformat(),'data':out},open('data/2026-10-20/_intra/prices.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
