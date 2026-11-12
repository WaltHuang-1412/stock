import re,json
D='data/2026-11-12/'
def L(p): return json.load(open(D+p,encoding='utf-8',errors='replace'))
t=open(D+'_chip_stdout.txt',encoding='utf-8',errors='replace').read()
blocks=re.split(r'📊 (?=\S+\(\d{4,5}\) 籌碼分析)',t)[1:]
def g(p,b):
    m=re.search(p,b); return m.group(1) if m else '?'
rows={}
for b in blocks:
    n,c=re.match(r'(\S+)\((\d+)\)',b).groups()
    rows[c]=dict(n=n,cum=g(r'累計淨買超（三大法人）\s*:\s*(\S+)',b),bd=g(r'買超天數: (\d+)',b),sd=g(r'賣超天數: (\d+)',b),cons=g(r'真連續買超: (\d+)',b),f5=g(r'近5天淨買超（外資）\s*:\s*(\S+)',b),mom=g(r'動能變化: (\S+)',b))
# reversal
rt=open(D+'_pool_reversal.txt',encoding='utf-8',errors='replace').read()
rev={}
for m in re.finditer(r'🔍 分析 \((\d+)\)\.\.\.\n(.*?)(?=\n🔍 分析|\n=====)',rt,re.S):
    rev[m.group(1)]=m.group(2).strip().split('\n')[0][:70]
top={s['code']:s for s in L('../2026-11-11/institutional_top50.json')['stocks']}
pp={r['code']:r for r in L('price_position_check.json')}
eps={r['code']:r for r in L('eps_check.json')}
fr={r['code']:r for r in L('foreign_ratio_check.json')}
rv={r['code']:r for r in L('revenue_check.json')}
import sys
for c,r in rows.items():
    s=top.get(c)
    lv=rev.get(c,'?')
    lv=re.sub(r'今日','',lv)
    print(c,r['n'],'|rk',s['avg_rank'] if s else '-','5d',round(s['5day_change'],1) if s else '-','br',round(s['buy_ratio']) if s else '-','|cum',r['cum'],'cons',r['cons'],'bd/sd',r['bd'],r['sd'],'f5',r['f5'],'mom',r['mom'],'|',lv,'|ma20',pp[c]['vs_ma20'],'pp',pp[c]['adj'],'|eps',eps[c].get('adj'),eps[c].get('eps_yoy_pct'),eps[c].get('latest_quarter'),'|fr',fr[c].get('ratio_change'),fr[c].get('stale'),'|rev',rv[c].get('month'),rv[c].get('adj'),rv[c].get('yoy'))
