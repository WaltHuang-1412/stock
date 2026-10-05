import json,sys,re
sys.path.insert(0,'scripts')
import settlement_checker as sc
A='data/2026-10-05/_after/'
chip=json.load(open(A+'chip_pool_1005.json',encoding='utf-8'))
L=lambda f:{x['code']:x for x in json.load(open(A+f,encoding='utf-8'))}
rev=L('revenue_check_after.json');fr=L('foreign_ratio_check_after.json');pp=L('price_position_check_after.json');eps=L('eps_check_after.json')
top={s['code']:s for s in json.load(open('data/2026-10-05/institutional_top50.json',encoding='utf-8'))['stocks'] if s['total']>0}
t86=json.load(open('data/cache/twse_t86_20261005.json',encoding='utf-8'))
ic=json.load(open('data/industry_chains.json',encoding='utf-8'))
def find(o,code,path,res):
    if isinstance(o,dict):
        if str(o.get('code') or o.get('symbol') or o.get('stock_code'))==code: res.append('/'.join(path)+'|'+str(o.get('category','')))
        for k,v in o.items(): find(v,code,path+[k] if not k.isdigit() else path,res)
    elif isinstance(o,list):
        for v in o: find(v,code,path,res)
tt=open('data/2026-10-05/topic_tracker.md',encoding='utf-8').read()
out={}
for c in open(A+'_poolcodes.txt').read().split():
    s=sc.get_close_series(c) or []
    d5=round((s[-1][1]/s[-6][1]-1)*100,2) if len(s)>6 else None
    ch=chip.get(c,{}); sm=ch.get('summary',{}); r5=sm.get('recent_5d',{}); mo=ch.get('momentum') or {}
    r=rev.get(c,{});f=fr.get(c,{});p=pp.get(c,{});e=eps.get(c,{})
    res=[];find(ic,c,[],res)
    name=t86.get(c,{}).get('name')
    o=dict(name=name,last=s[-1] if s else None,d5=d5,cum=sm.get('total_net'),cons=sm.get('consecutive_buy'),bd=sm.get('buy_days'),sd=sm.get('sell_days'),
           f5=r5.get('foreign'),n5=r5.get('total'),mom=round(mo.get('change_pct'),1) if mo.get('change_pct') is not None else None,
           rev=r.get('adj'),rev_m=r.get('month'),yoy=r.get('yoy'),pb=r.get('pullback_5d'),fr=f.get('suggestion'),fr_asof=f.get('as_of'),vs20=p.get('vs_ma20'),pp=p.get('adj'),
           eps=e.get('adj'),eps_q=e.get('latest_quarter'),avg_rank=top.get(c,{}).get('avg_rank'),ratio=round(top.get(c,{}).get('buy_ratio',0) or 0,1),tot=t86.get(c,{}).get('total'),fo=t86.get(c,{}).get('foreign'),tr=t86.get(c,{}).get('trust'),
           ind=res[:4],tt=len(re.findall(re.escape(c),tt)))
    out[c]=o
    print(c,name,'|cl',o['last'][1] if o['last'] else None,o['last'][0][5:] if o['last'] else '','5d',d5,'|T86',o['tot'],'外',o['fo'],'投',o['tr'],'rk',o['avg_rank'],o['ratio'],'|cum',o['cum'],'連',o['cons'],f"買{o['bd']}賣{o['sd']}",'f5',o['f5'],'mom',o['mom'],'|rev',o['rev'],o['yoy'],'fr',(o['fr'] or '')[:8],'eps',o['eps'],(o['eps_q'] or '')[:7],'|vs20',o['vs20'],'pp',o['pp'],'|tt',o['tt'],'|',';'.join(o['ind'])[:110])
json.dump(out,open(A+'pool_table.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
