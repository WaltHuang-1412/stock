import re,json,io
D='data/2026-11-09/'
def L(p): return json.load(open(D+p,encoding='utf-8',errors='replace'))
t=open(D+'_chip_stdout.txt',encoding='utf-8',errors='replace').read()
blocks=re.split(r'📊 (?=\S+\(\d{4,5}\) 籌碼分析)',t)[1:]
def g(p,b):
    m=re.search(p,b); return m.group(1) if m else '?'
rows={}
for b in blocks:
    n,c=re.match(r'(\S+)\((\d+)\)',b).groups()
    rows[c]=dict(n=n,cum=g(r'累計淨買超（三大法人）\s*:\s*(\S+)',b),fcum=g(r'累計淨買超（外資）\s*:\s*(\S+)',b),bd=g(r'買超天數: (\d+)',b),sd=g(r'賣超天數: (\d+)',b),cons=g(r'真連續買超: (\d+)',b),f5=g(r'近5天淨買超（外資）\s*:\s*(\S+)',b),t5=g(r'近5天淨買超（三大法人）\s*:\s*(\S+)',b),mom=g(r'動能變化: (\S+)',b))
top={s['code']:s for s in L('institutional_top50.json')['stocks']}
pp={r['code']:r for r in L('price_position_check.json')}
eps={r['code']:r for r in L('eps_check.json')}
fr={r['code']:r for r in L('foreign_ratio_check.json')}
if __name__=='__main__':
    L4=set('2002 2882 2330 2454 3711 2308 2317 3231'.split())
    for c,r in rows.items():
        if c in L4: continue
        s=top.get(c)
        print(c,r['n'],'rank',s['avg_rank'] if s else '-','5d',round(s['5day_change'],1) if s else '-','|f5',r['f5'],'cons',r['cons'],'cum',r['cum'],'mom',r['mom'],'|ma20',pp[c]['vs_ma20'],'pp',pp[c]['adj'],'|eps',eps.get(c,{}).get('adj'),eps.get(c,{}).get('eps_yoy_pct'),eps.get(c,{}).get('latest_quarter'),'fr',fr.get(c,{}).get('suggestion'))
