import sys,json; sys.path.insert(0,'scripts')
import check_price_position as cp
out=open('data/2026-10-06/_trackB/extra_checks.txt','w',encoding='utf-8')
res={}
for c in ['3017','3443']:
    r=cp.analyze_position(c); out.write(f'pricepos {c} {r}\n'); res[c]=r
pp=json.load(open('data/2026-10-06/price_position_check.json',encoding='utf-8'))
out.write(f'{type(pp)} {(list(pp.keys())[:3] if isinstance(pp,dict) else pp[0])}\n')
if isinstance(pp,dict):
    for c,r in res.items(): pp[c]=r
else:
    for c,r in res.items(): pp.append(r if isinstance(r,dict) else {'code':c,'result':r})
json.dump(pp,open('data/2026-10-06/price_position_check.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
out.close()
