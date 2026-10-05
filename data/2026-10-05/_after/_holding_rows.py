import json
A='data/2026-10-05/_after/'
raw=json.load(open(A+'rows_raw.json',encoding='utf-8'))
S=json.load(open(A+'settlements.json',encoding='utf-8'))
D={'2609':2,'6257':2,'3711':2,'3035':1,'2327':1,'8150':1,'1326':0,'2330':1,'2379':1,'3037':1,'3231':1,'2344':1}
rows={}
for c,v in raw.items():
    if c=='2867' or not v.get('tail'): continue
    t=v['tail']; assert t[-1][0]=='2026-10-05',c
    cl=t[-1][1]; pc=t[-2][1]; p2=t[-3][1]
    assert abs(float(v['mis']['z'])-cl)<1e-6,(c,cl,v['mis'])
    r=dict(name=v.get('name') or v['yaml']['name'],cl=cl,chg=round((cl/pc-1)*100,2),two=round((cl/p2-1)*100,2),low=float(v['mis']['l']),high=float(v['mis']['h']))
    if v.get('p'):
        r.update(date=v['date'],p=v['p'],tp=v['tp'],sl=v['sl'],ret=round((cl/v['p']-1)*100,2),dist_stop=round((cl/v['sl']-1)*100,2),dist_target=round((v['tp']/cl-1)*100,2),D=D[c],settled=c in S)
    if v.get('yaml'): r['yaml']=v['yaml']
    rows[c]=r
    print(c,r['name'],r.get('date'),'D',r.get('D'),'p',r.get('p'),'cl',cl,f"{r['chg']:+.2f}%",'2d',r['two'],'ret',r.get('ret'),'stop',r.get('sl'),r.get('dist_stop'),'tp',r.get('tp'),r.get('dist_target'),'low',r['low'],'hi',r['high'],'settled' if r.get('settled') else '',r.get('yaml',''))
json.dump(rows,open(A+'holding_rows.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
