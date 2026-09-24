import sys,json
sys.path.insert(0,'scripts')
from datetime import datetime,timezone,timedelta
from yahoo_finance_api import get_history
TPE=timezone(timedelta(hours=8))
codes=sys.argv[1].split(',')
out={}
for c in codes:
    h=get_history(c,period="1mo",interval="1d")
    rows=[]
    for ts,cl,v in zip(h['timestamps'],h['closes'],h.get('volumes') or []):
        dt=datetime.fromtimestamp(ts,tz=TPE)
        rows.append((dt.strftime('%Y-%m-%d %H:%M:%S'),cl,v))
    last=rows[-4:]
    real=[r for r in rows if r[0].endswith('09:00:00') and r[1] is not None and r[2]]
    out[c]=[(r[0][:10],round(r[1],2)) for r in real[-4:]]
    print(c,'LAST RAW:',[(r[0],round(r[1],2) if r[1] else None,r[2]) for r in last[-2:]])
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
