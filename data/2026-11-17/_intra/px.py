import sys,json,time,requests
sys.path.insert(0,'scripts')
import settlement_checker as sc
def rt(code):
    for suf in ('.TW','.TWO'):
        try:
            r=requests.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{code}{suf}?interval=1d&range=5d',headers={'User-Agent':'Mozilla/5.0'},timeout=10).json()
            m=r['chart']['result'][0]['meta']
            if m.get('regularMarketPrice'): return m['regularMarketPrice'],m.get('regularMarketTime'),m.get('regularMarketVolume'),m.get('regularMarketDayLow'),m.get('regularMarketDayHigh')
        except Exception as e: pass
    return None,None,None,None,None
out={}
for c in sys.argv[1:]:
    p,t,v,lo,hi=rt(c)
    s=sc.get_close_series(c) or []
    s=[x for x in s if str(x[0])<'2026-11-17']
    prev=s[-1] if s else (None,None)
    prev2=s[-2] if len(s)>1 else (None,None)
    chg=(p/prev[1]-1)*100 if p and prev[1] else None
    two=(p/prev2[1]-1)*100 if p and prev2[1] else None
    out[c]=dict(price=p,time=time.strftime('%m-%d %H:%M',time.localtime(t)) if t else None,vol=v,low=lo,high=hi,prev_day=str(prev[0]),prev=prev[1],chg=chg,prev2_day=str(prev2[0]),prev2=prev2[1],two_day=two)
    print(c,json.dumps(out[c],ensure_ascii=False))
json.dump(out,open('data/2026-11-17/_intra/px_'+sys.argv[1]+'.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
