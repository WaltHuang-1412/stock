import sys,json,re
sys.path.insert(0,'data/2026-11-09')
from _factors import rows,top,pp,eps,fr
def num(s):
    s=s.replace(',','').replace('+','')
    m=1
    if s.endswith('K'): m=1000; s=s[:-1]
    try: return float(s)*m
    except: return 0.0
rev=json.load(open('data/2026-11-09/revenue_check.json',encoding='utf-8',errors='replace'))
revm={ (r.get('code') or r.get('symbol')):r for r in rev} if isinstance(rev,list) else {}
L4=set('2002 2882 2330 2454 3711 2308 2317 3231'.split()); L2={'1102'}
disp={'6213'}
A={'2891':15,'5876':15}
for c in '5880 1216 2892 2412 1101 2887 2801 3045 2880 4904 1709 2609 2002 2882 2382 4938'.split(): A.setdefault(c,10)
catalyst={ # 時事維度 基礎分（取 topic_tracker 對應最強者）
 '2408':20,'2344':20,'2337':20,'6239':20,'2382':20,'2356':20,'2345':20,'6669':20,'3017':20,'2352':20,'2376':20,'3706':14,'1802':10,
 '6770':12,'3481':10,'2409':10,'6116':10,
 '2891':18,'2892':18,'2880':18,'2883':18,'2887':12,'5880':10,'2801':12,'5876':10,
 '2412':14,'1101':14,'2618':20,'2615':20,'2609':20,'1216':10,'9904':10,'4763':10,'2353':10,'2489':10,'3576':10,'6112':10,'1102':10,'4904':14,'1709':10,'2634':12,'4938':10,'1301':12,'6213':12}
ind={'2412':16,'2382':15,'2356':14,'2408':15,'2344':15,'2337':15}
res=[]
for c,r in rows.items():
    s=top.get(c)
    rank=s['avg_rank'] if s else None
    cum=num(r['cum']); fcum=num(r['fcum']); f5=num(r['f5']); cons=int(r['cons']); mom=float(r['mom'].replace('%','').replace('+','')) if r['mom']!='?' else 0
    br=s['buy_ratio'] if s else 0
    base=(21 if rank<=10 else 18 if rank<=20 else 14 if rank<=35 else 10) if rank else 6
    b=base+(2 if br>20 else 1 if br>=10 else 0)+(1 if fcum>0 and cum>0 and r['tcum' if False else 'cum']!='' and False else 0)
    fs=1 if (fcum>0 and cum>fcum*0.0 and True and num(r.get('t5','0'))>0 and f5>0) else 0
    b+=fs+(1 if cons>=5 else 0)
    sd=int(r['sd']); 
    if sd>=7: b=min(b,15)
    elif sd==6: b-=5
    b=min(b,25)
    ev=catalyst.get(c,10); yy=ind.get(c,14)
    lvl='L4' if c in L4 else 'L2' if c in L2 else 'L0'
    tech=(14 if (mom<-30 and cons>=3) else 12 if mom<0 or 3<=cons<=4 else 10) if lvl=='L0' else (4 if lvl=='L2' else 0)
    p=pp[c]['adj']
    e=eps.get(c,{}).get('adj',0); f=fr.get(c,{}).get('suggestion','');fa=5 if '+5' in f else -3 if '-3' in f else 0
    rv=revm.get(c,{})
    rs=rv.get('suggestion') or rv.get('adj') or ''
    ra=5 if '+5分' in str(rs) else -5 if '-5分' in str(rs) else 0
    ma=A.get(c,0)
    mm=15 if mom<-30 else 10 if mom<0 else 0 if mom<=50 else -10 if mom<=100 else None
    gate=[]
    if lvl=='L4': gate.append('反轉L4排除')
    if c in disp: gate.append('處置股排除')
    if mm is None: gate.append('動能>100%追高')
    if f5<0: gate.append('外資近5天<0')
    if (not s) and 0<=pp[c]['vs_ma20']<=5: gate.append('法人現身門檻')
    tot=None if mm is None else ev+b+yy+tech+p+mm+ma+max(-5,min(5,e))+fa+ra
    res.append((c,r['n'],rank,ev,b,yy,tech,p,mm,ma,e,fa,ra,tot,lvl,';'.join(gate)))
res.sort(key=lambda x:(x[13] if x[13] is not None else -999),reverse=True)
print('code name rank 事 法 業 技 價 動能 A e fr rev 總 lvl gate')
for x in res: print(*x)
json.dump([list(x) for x in res],open('data/2026-11-09/_score_table.json','w',encoding='utf-8'),ensure_ascii=False)
