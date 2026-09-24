import json,re,sys
sys.path.insert(0,'scripts')
import settlement_checker as sc
txt=open('data/2026-09-24/_chip_pool.txt',encoding='utf-8').read()
blocks=re.split(r'🔍 查詢 (\d{4,6}) 近',txt)
chip={}
for i in range(1,len(blocks),2):
    c=blocks[i];b=blocks[i+1]
    g=lambda p:(re.search(p,b).group(1) if re.search(p,b) else None)
    chip[c]=dict(cons=g(r'真連續買超: (\d+)'),n5=g(r'近5天淨買超（三大法人）: ([+\-0-9.,K]+)'),f5=g(r'近5天淨買超（外資）\s*: ([+\-0-9.,K]+)'),mom=g(r'動能變化: ([+\-0-9.%]+)'),cum=g(r'累計淨買超[^:：]*[:：]\s*([+\-0-9.,K]+)'))
rev={x['code']:x for x in json.load(open('data/2026-09-24/_after/revenue_check_after.json',encoding='utf-8'))}
fr={x['code']:x for x in json.load(open('data/2026-09-24/_after/foreign_ratio_check_after.json',encoding='utf-8'))}
pp={x['code']:x for x in json.load(open('data/2026-09-24/_after/price_position_check_after.json',encoding='utf-8'))}
top={s['code']:s for s in json.load(open('data/2026-09-23/institutional_top50.json',encoding='utf-8'))['stocks']}
codes=open('data/2026-09-24/_after/_poolcodes.txt').read().split()
out={}
for c in codes:
    s=sc.get_close_series(c) or []
    d5=round((s[-1][1]/s[-6][1]-1)*100,2) if len(s)>6 else None
    ch=chip.get(c,{})
    r=rev.get(c,{});f=fr.get(c,{});p=pp.get(c,{})
    nm=top.get(c,{}).get('name','')
    out[c]=dict(name=nm,last=s[-1] if s else None,d5=d5,**ch,rev_adj=r.get('adj'),rev_m=r.get('month'),yoy=r.get('yoy'),fr=f.get('suggestion'),fr_asof=f.get('as_of'),vs20=p.get('vs_ma20'),pp=p.get('adj'),avg_rank=top.get(c,{}).get('avg_rank'))
    print(c,nm,out[c]['last'],'5d',d5,'mom',ch.get('mom'),'f5',ch.get('f5'),'cons',ch.get('cons'),'rev',r.get('adj'),r.get('month'),'fr',f.get('suggestion'),'vs20',p.get('vs_ma20'),'pp',p.get('adj'))
json.dump(out,open('data/2026-09-24/_after/pool_table.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
