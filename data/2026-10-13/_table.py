import json,re,sys
T='2026-10-13'
def num(s):
    s=s.replace(',','').replace('張','').strip()
    m=1000 if s.endswith('K') else 1
    s=s.rstrip('K')
    return float(s)*m
txt=open(f'data/{T}/chip_pool_stdout.txt',encoding='utf-8').read()
chip={}
for blk in re.split(r'🔍 查詢 ',txt)[1:]:
    code=blk.split()[0]
    g=lambda p:(re.search(p,blk) or [None,None])[1]
    chip[code]=dict(cum=num(g(r'累計淨買超（三大法人）:\s*(\S+)')) if g(r'累計淨買超（三大法人）:\s*(\S+)') else None,
      sell=g(r'賣超天數:\s*(\d+)'),streak=g(r'真連續買超:\s*(\d+)'),
      f5=num(g(r'近5天淨買超（外資）\s*:\s*(\S+)')) if g(r'近5天淨買超（外資）\s*:\s*(\S+)') else None,
      t5=num(g(r'近5天淨買超（三大法人）\s*:\s*(\S+)')) if g(r'近5天淨買超（三大法人）\s*:\s*(\S+)') else None)
top=json.load(open(f'data/{T}/institutional_top50.json',encoding='utf-8'))['stocks']
buys=[x for x in top if x['total']>0]
rank={x['code']:(i+1,x) for i,x in enumerate(buys)}
pp={x['code']:x for x in json.load(open(f'data/{T}/price_position_check.json',encoding='utf-8'))}
rv={x['code']:x for x in json.load(open(f'data/{T}/revenue_check.json',encoding='utf-8'))}
ep={x['code']:x for x in json.load(open(f'data/{T}/eps_check.json',encoding='utf-8'))}
fr={x['code']:x for x in json.load(open(f'data/{T}/foreign_ratio_check.json',encoding='utf-8'))}
ra={x['stock_code']:x for x in json.load(open(f'data/{T}/reversal_alerts_pool.json',encoding='utf-8'))}
names={x['code']:x['name'] for x in top}
for c in open(f'data/{T}/_score_pool.txt').read().split():
    r=rank.get(c); ch=chip.get(c,{})
    print(c,names.get(c,''),'| rk',r[0] if r else '-', 'avg',r[1].get('avg_rank') if r else '-','tot',int(r[1]['total']/1000) if r else '-','| streak',ch.get('streak'),'sell',ch.get('sell'),'cum10',ch.get('cum'),'f5',ch.get('f5'),
      '| L',ra.get(c,{}).get('level','0'),
      '| vsMA20',pp.get(c,{}).get('vs_ma20'),'pos',pp.get(c,{}).get('adj'),
      '| rev',rv.get(c,{}).get('yoy'),rv.get(c,{}).get('adj'),'stale' if rv.get(c,{}).get('stale') else '',
      '| eps',ep.get(c,{}).get('latest_quarter'),ep.get(c,{}).get('adj'),
      '| fr',fr.get(c,{}).get('ratio_change'),fr.get(c,{}).get('suggestion'),'stale' if fr.get(c,{}).get('stale') else '')
