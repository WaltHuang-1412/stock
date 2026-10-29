import re,json
t=open('data/2026-10-29/_pool/chip.txt',encoding='utf-8').read()
blocks=re.split(r'\n={60}\n📊 (.+?)\((\d+)\) 籌碼分析\n={60}\n',t)
rows={}
for i in range(1,len(blocks),3):
    name,code,b=blocks[i],blocks[i+1],blocks[i+2]
    g=lambda p:(re.search(p,b) or [None,None])[1]
    rows[code]=dict(name=name,cum=g(r'累計淨買超（三大法人）: (\S+)'),cumF=g(r'累計淨買超（外資）\s*: (\S+)'),cumT=g(r'累計淨買超（投信）\s*: (\S+)'),
      buy=g(r'買超天數: (\d+)'),sell=g(r'賣超天數: (\d+)'),cons=g(r'真連續買超: (\d+)'),c5=g(r'近5天淨買超（三大法人）: (\S+)'),f5=g(r'近5天淨買超（外資）: (\S+)'),mom=g(r'動能變化: (\S+)'),
      today=g(r'\n2026/10/28\s+(\S+)'))
rv=json.load(open('data/2026-10-29/reversal_alerts.json',encoding='utf-8'))
pp=json.load(open('data/2026-10-29/price_position_check.json',encoding='utf-8'))
fr=json.load(open('data/2026-10-29/foreign_ratio_check.json',encoding='utf-8'))
def look(o,c):
    if isinstance(o,dict):
        if c in o: return o[c]
        for k in ('results','stocks','data'):
            if k in o: return look(o[k],c)
    if isinstance(o,list):
        for x in o:
            if isinstance(x,dict) and str(x.get('stock_code') or x.get('symbol') or x.get('code'))==c: return x
    return None
print(type(rv),str(rv)[:300]);print(str(pp)[:300]);print(str(fr)[:300])
for c,r in rows.items():
    print(c,r['name'],'|10d',r['cum'],'F',r['cumF'],'T',r['cumT'],'|買/賣',r['buy'],r['sell'],'|連',r['cons'],'|5d',r['c5'],'F5',r['f5'],'|動能',r['mom'],'|今',r['today'])
print('=========== merged')
rvm={r['stock_code']:r for r in rv}
ppm={r['code']:r for r in pp}
frm={r['code']:r for r in fr}
for c,r in rows.items():
    b=re.search(r'📊 .+?\('+c+r'\) 籌碼分析.*?(?=\n📊 |\Z)',t,re.S).group(0)
    f5=re.search(r'近5天淨買超（外資）\s*: (\S+)',b); r['f5']=f5.group(1) if f5 else None
    v=rvm.get(c,{}); p=ppm.get(c,{}); f=frm.get(c,{})
    print(c,r['name'],'| L',v.get('level'),'|F5',r['f5'],'|連',r['cons'],'|動能',r['mom'],'|MA20',p.get('vs_ma20'),'adj',p.get('adj'),'|外資比',f.get('ratio_change'),f.get('suggestion'),'|',(v.get('alert_reason') or '')[:60])
