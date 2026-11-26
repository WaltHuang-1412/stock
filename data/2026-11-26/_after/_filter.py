import json, sys
sys.path.insert(0,'scripts')
import settlement_checker as sc
D='data/2026-11-26/_after'
chip=json.load(open(D+'/chip_pool.json',encoding='utf-8'))
rv={r['stock_code']:r for r in json.load(open(D+'/pool/reversal_alerts.json',encoding='utf-8'))}
top=json.load(open('data/2026-11-26/institutional_top50.json',encoding='utf-8'))['stocks'][:50]
k=next(iter(chip.values()))
print('chip keys', list(k.keys()))
for s in top:
    c=s['code']; r=chip.get(c)
    if not r: print(c,'no chip'); continue
    d=r.get('daily_data') or r.get('history') or r.get('data')
    rows=sorted(d,key=lambda x:x['date'],reverse=True)
    f5=sum(x['foreign'] for x in rows[:5]); t10=sum(x['total'] for x in rows)
    cons=0
    for x in rows:
        if x['total']>0: cons+=1
        else: break
    sd=sum(1 for x in rows if x['total']<0)
    a=sum(x['total'] for x in rows[:5])/5; b=sum(x['total'] for x in rows[5:10])/5
    mom=(a-b)/abs(b)*100 if b else float('nan')
    ser=sc.get_close_series(c)
    d5=(ser[-1][1]/ser[-6][1]-1)*100 if ser and len(ser)>6 else None
    d2=(ser[-1][1]/ser[-3][1]-1)*100 if ser else None
    lv=rv.get(c,{}).get('level')
    print(f"{c} {s['name']} L={lv} f5={f5} t10={t10} cons={cons} sd={sd} mom={mom:.0f} d5={d5:.1f} today={s['total']} avg={s['avg_rank']} br={s['buy_ratio']:.0f}")
    s.update(lv=lv,f5=f5,t10=t10,cons=cons,sd=sd,mom=mom,d5=d5,last=ser[-1])
json.dump(top,open(D+'/pool_summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
