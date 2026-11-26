import json,re
D='data/2026-11-26'
rv=json.load(open(D+'/_pool_rev/reversal_alerts.json',encoding='utf-8'))
txt=open(D+'/_chip_pool.txt',encoding='utf-8').read()
blocks=re.split(r'📊 (.+?)\((\w+)\) 籌碼分析',txt)
chip={}
for i in range(1,len(blocks),3):
    name,code,b=blocks[i],blocks[i+1],blocks[i+2]
    def g(p):
        m=re.search(p,b); return m.group(1) if m else None
    days=re.findall(r'^(\d{4}/\d\d/\d\d)\s+(\S+)\s+(\S+)\s+(\S+)',b,re.M)
    sec5=b.split('【近5天趨勢】')[-1]
    f5=re.search(r'近5天淨買超（外資）\s*:\s*([+\-\d,K]+)',sec5)
    chip[code]=dict(name=name,cum=g(r'累計淨買超（三大法人）:\s*([+\-\d,K]+)'),cumf=g(r'累計淨買超（外資）\s*:\s*([+\-\d,K]+)'),
      cons=g(r'真連續買超:\s*(\d+)'),bd=g(r'買超天數:\s*(\d+)'),sd=g(r'賣超天數:\s*(\d+)'),f5=f5.group(1) if f5 else None,
      mom=g(r'動能變化:\s*([+\-\d.]+)%'),today=days[0][1:] if days else None)
json.dump(chip,open(D+'/_chip_pool.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
t=json.load(open('data/2026-11-25/institutional_top50.json',encoding='utf-8'))
top={s['code']:s for s in t['stocks']}
pool=open(D+'/_pool.txt').read().split()
print(type(rv), list(rv.keys())[:8] if isinstance(rv,dict) else rv[:2])
if isinstance(rv,dict):
    items=rv.get('alerts') or rv.get('results') or rv.get('stocks') or list(rv.values())
else: items=rv
R={}
def walk(o):
    if isinstance(o,dict):
        c=o.get('stock_code') or o.get('code') or o.get('stock_id')
        if c and ('level' in o or 'warning_level' in o): R[str(c)]=o
        for v in o.values(): walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
walk(rv)
print(len(R), list(R.values())[:1])
for c in pool:
    x=chip.get(c,{}); r=R.get(c,{}); s=top.get(c)
    print(c,x.get('name'),'|lv',r.get('level'),r.get('warning_level'),'|cum',x.get('cum'),'f5',x.get('f5'),'cons',x.get('cons'),'sd',x.get('sd'),'mom',x.get('mom'),'|',('rk%s 5d%+.1f br%.0f'%(s['avg_rank'],s['5day_change'],s['buy_ratio'])) if s else '-', x.get('today'))
