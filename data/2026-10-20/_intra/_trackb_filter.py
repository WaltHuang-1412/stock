import sys,json
sys.path.insert(0,'scripts')
from yahoo_finance_api import get_current_price
import settlement_checker as sc
t=json.load(open('data/2026-10-20/institutional_top50.json',encoding='utf-8'))
print('keys',list(t.keys())[:10])
buys=t.get('buy') or t.get('top_buy') or t.get('buy_top50') or []
if not buys:
    for k,v in t.items():
        if isinstance(v,list) and v and isinstance(v[0],dict) and (v[0].get('total',0) or 0)>0: buys=v;break
print('buy count',len(buys), 'sample', buys[0] if buys else None)
trackA={'2887','2002','2886','2892','2882','2867','1326','1802','1605'}
det=json.load(open('data/2026-10-20/intraday_detector.json',encoding='utf-8'))
strong=[s['code'] if 'code' in s else s.get('stock_code') for s in det.get('strong_signals',det.get('strong',[]))]
print('strong',strong)
rows=[]
for b in buys:
    code=str(b.get('code') or b.get('stock_code') or b.get('symbol'))
    if code in trackA: continue
    px=get_current_price(code)
    s=sc.get_close_series(code) or []
    prev=[x for x in s if str(x[0])<'2026-10-20']
    pc=prev[-1][1] if prev else None
    chg=round((px/pc-1)*100,2) if px and pc else None
    rows.append({'code':code,'name':b.get('name'),'avg_rank':b.get('avg_rank'),'total':b.get('total'),'foreign':b.get('foreign'),'trust':b.get('trust'),'buy_ratio':b.get('buy_ratio'),'5day':b.get('5day_change') or b.get('change_5d'),'price':px,'prev_close':pc,'chg':chg,'det':code in strong})
    print(rows[-1])
json.dump(rows,open('data/2026-10-20/_intra/trackb_top50_prices.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('\n=== 候選（漲幅<3% 且 total>5K 或 avg_rank<=30）===')
for r in rows:
    if r['chg'] is not None and r['chg']<3 and ((r['total'] or 0)>5000 or (r['avg_rank'] or 99)<=30):
        print(r['code'],r['name'],'rank',r['avg_rank'],'total',r['total'],'chg',r['chg'],'5d',r['5day'])
