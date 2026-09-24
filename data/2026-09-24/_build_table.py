import json,re,sys
T='2026-09-24'
def L(f): return json.load(open(f'data/{T}/{f}',encoding='utf-8'))
chip={}
txt=open(f'data/{T}/_chip_pool.txt',encoding='utf-8').read()
for blk in re.split(r'\n📊 ',txt)[1:]:
    m=re.match(r'(.+?)\((\d+)\) 籌碼分析',blk)
    if not m: continue
    name,code=m.groups()
    def g(p):
        mm=re.search(p,blk); return mm.group(1) if mm else None
    chip[code]=dict(name=name,cum=g(r'累計淨買超（三大法人）: (\S+)'),buyd=g(r'買超天數: (\d+)'),selld=g(r'賣超天數: (\d+)'),
        consec=g(r'真連續買超: (\d+)'),f5=g(r'近5天淨買超（外資）\s*: (\S+)'),t5=g(r'近5天淨買超（三大法人）: (\S+)'),mom=g(r'動能變化: (\S+)'))
rev={r['stock_code']:r for r in L('reversal_alerts.json')}
pp={r['code']:r for r in L('price_position_check.json')}
rv={r['code']:r for r in L('revenue_check.json')}
ep={r['code']:r for r in L('eps_check.json')}
fr={r['code']:r for r in L('foreign_ratio_check.json')}
top=json.load(open('data/2026-09-23/institutional_top50.json',encoding='utf-8'))
buy={s['code']:s for s in top['stocks'] if s['total']>0}
sell={s['code']:s for s in top['stocks'] if s['total']<0}
dos=L('stock_dossier_pool.json')['stocks']
pool=open(f'data/{T}/_pool.txt').read().split()
names=json.load(open('data/cache/stock_names.json',encoding='utf-8'))
print('code name|rev|avg_rank tot(張) bratio 5d%|cum10 b/s consec f5 mom|ma20 pp|rvYoY adj|eps adj q|fr adj|events')
for c in pool:
    ch=chip.get(c,{}); r=rev.get(c,{}); p=pp.get(c,{}); b=buy.get(c) or sell.get(c)
    ev=[f"{e['type']}{e['date'][5:]}" for e in dos.get(c,{}).get('events',[])]
    nm=ch.get('name') or (b or {}).get('name') or names.get(c,'?')
    frs=fr.get(c,{}).get('suggestion','')
    fadj=5 if frs.startswith('+5') else (-3 if frs.startswith('-3') else 0)
    print(f"{c} {nm}|L{r.get('level','?')} {(r.get('alert_reason') or '')[:40]}|"
          f"{(b or {}).get('avg_rank','-')} {round((b or {}).get('total',0)/1000)} {round((b or {}).get('buy_ratio',0),1)} {round((b or {}).get('5day_change',0),1) if b else '-'}|"
          f"{ch.get('cum')} {ch.get('buyd')}/{ch.get('selld')} c{ch.get('consec')} f5{ch.get('f5')} m{ch.get('mom')}|"
          f"{p.get('vs_ma20')} {p.get('adj')}|{rv.get(c,{}).get('yoy')} {rv.get(c,{}).get('adj')}|{ep.get(c,{}).get('adj')} {ep.get(c,{}).get('latest_quarter')}|{fr.get(c,{}).get('ratio_change')} {fadj}|{','.join(ev)}")
