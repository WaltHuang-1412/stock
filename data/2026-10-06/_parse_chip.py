import re,json,sys
txt=open(sys.argv[1],encoding='utf-8').read()
blocks=re.split(r'🔍 查詢 (\d+) 近',txt)[1:]
out={}
def num(s):
    s=s.replace(',','').replace('張','').strip()
    m=re.match(r'([+-]?[\d.]+)(K?)',s)
    if not m: return None
    v=float(m.group(1)); 
    if m.group(2)=='K': v*=1000
    return int(v)
for i in range(0,len(blocks),2):
    code=blocks[i]; b=blocks[i+1]
    def g(pat):
        m=re.search(pat,b); return m.group(1).strip() if m else None
    name=g(r'📊 (.+?)\('+code+r'\)')
    d={'name':name,
       'cum10':num(g(r'累計淨買超（三大法人）: (.+?) 張') or '0'),
       'cum10_f':num(g(r'累計淨買超（外資）\s*: (.+?) 張') or '0'),
       'cum10_t':num(g(r'累計淨買超（投信）\s*: (.+?) 張') or '0'),
       'buy_days':int(g(r'買超天數: (\d+)') or 0),'sell_days':int(g(r'賣超天數: (\d+)') or 0),
       'consec':int(g(r'真連續買超: (\d+)') or 0),
       'n5':num(g(r'近5天淨買超（三大法人）: (.+?) 張') or '0'),
       'n5_f':num(g(r'近5天淨買超（外資）\s*: (.+?) 張') or '0'),
       'n5_t':num(g(r'近5天淨買超（投信）\s*: (.+?) 張') or '0'),
       'mom':g(r'動能變化: (.+?)%'),
       'max_buy':g(r'最大單日買超: (.+?) \('),
       'today':None}
    m=re.search(r'2026/10/05\s+(\S+)\s+(\S+)\s+(\S+)',b)
    if m: d['today']=num(m.group(1)); d['today_f']=num(m.group(2)); d['today_t']=num(m.group(3))
    out[code]=d
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(f"{'code':5} {'name':8} {'today':>8} {'cum10':>8} {'b/s':>4} {'cons':>4} {'n5':>8} {'n5_f':>8} {'mom%':>8}")
for c,d in out.items():
    print(f"{c:5} {str(d['name'])[:6]:8} {str(d['today']):>8} {d['cum10']:>8} {d['buy_days']}/{d['sell_days']:<2} {d['consec']:>4} {d['n5']:>8} {d['n5_f']:>8} {str(d['mom']):>8}")
