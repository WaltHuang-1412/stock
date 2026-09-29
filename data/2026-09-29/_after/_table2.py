import json,sys
sys.path.insert(0,'scripts')
import settlement_checker as sc
A='data/2026-09-29/_after/'
chip=json.load(open(A+'chip_pool_0929.json',encoding='utf-8'))
L=lambda f:{x['code']:x for x in json.load(open(A+f,encoding='utf-8'))}
rev=L('revenue_check_after2.json');fr=L('foreign_ratio_check_after2.json');pp=L('price_position_check_after2.json')
try: eps=L('eps_check_after2.json')
except Exception as e: eps={}; print('eps load',e)
top={s['code']:s for s in json.load(open('data/2026-09-29/institutional_top50.json',encoding='utf-8'))['stocks'] if s['total']>0}
t86=json.load(open('data/cache/twse_t86_20260929.json',encoding='utf-8'))
out={}
for c in open(A+'_poolcodes2.txt').read().split():
    s=sc.get_close_series(c) or []
    d5=round((s[-1][1]/s[-6][1]-1)*100,2) if len(s)>6 else None
    ch=chip.get(c,{}); sm=ch.get('summary',{}); r5=sm.get('recent_5d',{}); mo=ch.get('momentum') or {}
    r=rev.get(c,{});f=fr.get(c,{});p=pp.get(c,{});e=eps.get(c,{})
    o=dict(name=t86.get(c,{}).get('name'),last=s[-1] if s else None,d5=d5,cum=sm.get('total_net') or sm.get('cumulative') ,cons=sm.get('consecutive_buy'),
           f5=r5.get('foreign'),n5=r5.get('total'),mom=mo.get('change_pct') if isinstance(mo,dict) else mo,
           rev=r.get('adj'),rev_m=r.get('month'),yoy=r.get('yoy'),fr=(f.get('suggestion') or '')[:3],fr_asof=f.get('as_of'),vs20=p.get('vs_ma20'),pp=p.get('adj'),
           eps=e.get('adj'),eps_q=e.get('quarter') or e.get('latest_quarter'),avg_rank=top.get(c,{}).get('avg_rank'),ratio=round(top.get(c,{}).get('buy_ratio',0),1),tot=t86.get(c,{}).get('total'),fo=t86.get(c,{}).get('foreign'),tr=t86.get(c,{}).get('trust'))
    out[c]=o
    print(c,o['name'],'|cl',o['last'][1] if o['last'] else None,'5d',d5,'|T86',o['tot'],'外',o['fo'],'投',o['tr'],'rank',o['avg_rank'],'|cum',o['cum'],'cons',o['cons'],'f5',o['f5'],'mom',o['mom'],'|rev',o['rev'],o['rev_m'],'fr',o['fr'],o['fr_asof'],'eps',o['eps'],o['eps_q'],'|vs20',o['vs20'],'pp',o['pp'])
json.dump(out,open(A+'pool_table2.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
