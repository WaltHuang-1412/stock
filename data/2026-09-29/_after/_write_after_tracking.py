import json,sys
T86_TODAY = (len(sys.argv)>1 and sys.argv[1]=='t86')
f='data/tracking/tracking_2026-09-29.json'
t=json.load(open(f,encoding='utf-8'))
mis=json.load(open('data/2026-09-29/_after/mis_close.json',encoding='utf-8'))
c=json.load(open('data/2026-09-29/_after/closes.json'))
D={'4904':'D8/10','5876':'D7/10','2395':'D7/10','2412':'D7/10','2892':'D5/10','2454':'D3/10',
   '2886':'D2/10','2609':'D2/10','3702':'D0/10','6196':'D0/10'}
REV={'4904':'L0 +301','5876':'L0 +130','2395':'L0 +576','2412':'L0 +2,747','2892':'L0 +2,362','2454':'L0 +670',
     '2886':'L0 -20','2609':'L0 +1','3702':'✅健康 +3,451','6196':'L0 +156'}
rows={}
def upd(r):
    k=r['stock_code']
    if k=='2867':
        r['holding_status']='⏸️ 序列停滯凍結（末日 2026-08-19），不結算、不出場、D 不推進（v8.3.8）'; return
    if k not in D: return
    cl=float(mis[k]['z']); pv=float(mis[k]['y']); p=r['recommend_price']
    d=dict(c[k]); assert d['2026-09-24']==pv,(k,d,pv)
    p2=d['2026-09-23']
    r.update({'actual_close':cl,'close_price':cl,'change_percent':round((cl/pv-1)*100,2),'return_pct':round((cl/p-1)*100,2),
              'two_day_pct':round((cl/p2-1)*100,2),'dist_to_stop_pct':round((cl/r['stop_loss']-1)*100,2),
              'holding_days':D[k],'result':'holding',
              'holding_status':f"續抱：反轉 {REV[k]}（09-24 T86；09-29 T86 盤後報告產出時尚未公布）；鐵律①②③ 無觸發；收盤 {cl}（{(cl/p-1)*100:+.2f}%）"})
    rows[k]=dict(name=r['stock_name'],D=D[k],p=p,cl=cl,chg=r['change_percent'],ret=r['return_pct'],two=r['two_day_pct'],
                 tgt=r['target_price'],stop=r['stop_loss'],dist=r['dist_to_stop_pct'],rd=r.get('recommend_date'))
for r in t['recommendations']: upd(r)
for r in t['carry_over_recommendations']: upd(r)
json.dump(rows,open('data/2026-09-29/_after/holding_rows.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for k,v in rows.items(): print(k,v)
vals=[v['chg'] for v in rows.values()]
print('avg chg',round(sum(vals)/len(vals),2),'up',sum(1 for x in vals if x>0),'down',sum(1 for x in vals if x<0),'n',len(vals))
rets=[v['ret'] for v in rows.values()]
print('avg ret',round(sum(rets)/len(rets),2))
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
