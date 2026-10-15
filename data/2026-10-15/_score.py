import json,re,sys
T='2026-10-15'
def num(s):
    s=s.replace(',','').replace('張','').strip(); m=1000 if s.endswith('K') else 1
    return float(s.rstrip('K'))*m
txt=open(f'data/{T}/chip_pool_stdout.txt',encoding='utf-8').read()
chip={}
for blk in re.split(r'🔍 查詢 ',txt)[1:]:
    code=blk.split()[0]
    g=lambda p:(re.search(p,blk) or [None,None])[1]
    mo=g(r'動能變化:\s*([+-]?[\d.]+)%')
    chip[code]=dict(cum=num(g(r'累計淨買超（三大法人）:\s*(\S+)')),sell=int(g(r'賣超天數:\s*(\d+)')),streak=int(g(r'真連續買超:\s*(\d+)')),
      f5=num(g(r'近5天淨買超（外資）\s*:\s*(\S+)')),mom=float(mo) if mo else 0)
top=json.load(open(f'data/{T}/institutional_top50.json',encoding='utf-8'))['stocks']
buys=[x for x in top if x['total']>0]
rank={x['code']:x for x in buys}
L=lambda f:{x['code']:x for x in json.load(open(f'data/{T}/{f}',encoding='utf-8'))}
pp,rv,ep,fr=L('price_position_check.json'),L('revenue_check.json'),L('eps_check.json'),L('foreign_ratio_check.json')
ra={x['stock_code']:x for x in json.load(open(f'data/{T}/reversal_alerts_pool.json',encoding='utf-8'))}
NAME={x['code']:x['name'] for x in top}
NAME.update({'3231':'緯創','3711':'日月光投控','8046':'南電','3189':'景碩','3037':'欣興','3443':'創意','2408':'南亞科','2344':'華邦電','3035':'智原','3023':'信邦','3481':'群創','2317':'鴻海','2382':'廣達','2886':'兆豐金','2892':'第一金','2891':'中信金','2887':'台新新光金','2880':'華南金','2881':'富邦金','2882':'國泰金','2449':'京元電','2412':'中華電','2377':'微星','2392':'正崴','2409':'友達','2603':'長榮','1605':'華新','6116':'彩晶','2801':'彰銀','2610':'華航'})
# 時事 base, 產業 base（人工判斷，依 topic_tracker / industry_chains tier）
SHI={'2891':20,'2885':16,'2887':20,'2618':8,'2002':16,'2886':15,'2892':20,'2610':8,'1216':10,'2884':14,'9904':9,'2882':12,'1314':15,'2449':20,'2801':14,'2881':20,'3706':18,'2412':12,'3702':12,'2353':10,'1102':10,'2382':20,'2377':16,'3231':20,'3035':16,'3023':14,'3481':16,'3711':20,'8046':18,'3189':18,'3037':18,'3443':20,'2603':22,'2609':22,'2880':20,'2408':20,'2344':20,'2027':14,'2324':16,'2317':16,'2327':16,'2323':14,'2409':16,'6116':12,'2105':8,'2855':12,'6005':12,'3576':12,'1711':8,'2371':8,'2392':12,'1605':14}
IND={'2881':17,'2882':17,'2886':17,'2887':17,'2880':17,'2891':17,'2885':17,'2884':17,'2801':15,'2002':17,'2412':17,'2610':17,'2618':17,'3711':18,'2449':18,'3037':18,'3189':18,'8046':18,'2382':16,'2317':16,'3231':16,'3706':15,'3023':13,'3035':15,'3443':18,'3481':17,'2408':17,'2344':17,'1102':15,'2603':17,'2609':17,'2327':15,'2323':13,'2409':15,'2324':15}
LEAD={'3443':-15,'2382':-15,'3231':-15,'2324':-5,'2408':-5,'2344':-5,'2317':-5,'2449':-5,'3711':-5,'2412':-5}
out=[]
for c in open(f'data/{T}/_score_pool.txt').read().split():
    if c not in SHI: continue
    ch=chip[c]; r=rank.get(c); lvl=ra[c]['level']; p=pp[c]['adj']
    d5=r['5day_change'] if r else None
    # 法人
    if r:
        ar=r['avg_rank']; base=21.5 if ar<=10 else 18 if ar<=20 else 14 if ar<=35 else 10
        br=r['buy_ratio']; base+=2 if br>20 else 1 if br>=10 else 0
        if r['foreign']>0 and r['trust']>0: base+=1
    else: base=6
    if ch['streak']>=5: base+=1
    base=min(base,30)
    if ch['sell']>=7: base=min(base,15)
    mods=[]
    if ch['sell']==6: mods.append(('賣超6天',-5))
    if r and r['total']>=30000000 and ch['streak']<7: mods.append(('過量買超',-5))
    # 技術
    if lvl in (0,-1):
        tech=14 if (ch['mom']<-30 and ch['streak']>=3) else 12 if (ch['mom']<0 or 3<=ch['streak']<=4) else 10
    else: tech=5
    mom=ch['mom']; mm=15 if mom<-30 else 10 if mom<0 else 0 if mom<=50 else -10 if mom<=100 else None
    rva=rv[c]['adj'] if not rv[c].get('stale') else 0
    epa=ep[c]['adj']; fra=fr[c]['suggestion']; fra=5 if '+5' in fra else -3 if '-3' in fra else 0
    rev=-15 if lvl==2 else -5 if lvl==1 else 0
    lead=LEAD.get(c,0)
    tot=SHI.get(c,0)+base+IND.get(c,14)+tech+p
    adj=(rva+max(-5,min(5,epa))+fra+rev+(mm or 0)+lead+sum(v for _,v in mods))
    big=0
    if d5 is not None and d5>10: big=None
    elif d5 is not None and d5>5: big=-10
    # 已大漲 5日5-10% -10
    if big: adj+=big
    out.append(dict(c=c,n=NAME.get(c,''),tot=tot+adj,shi=SHI.get(c),inst=base,ind=IND.get(c,14),tech=tech,pos=p,rev=rva,eps=epa,fr=fra,rv=rev,mom=round(mom,1),mm=mm,lead=lead,mods=mods,big=big,lvl=lvl,streak=ch['streak'],sell=ch['sell'],f5=ch['f5'],cum=ch['cum'],d5=d5,intop=bool(r),vsma=pp[c]['vs_ma20']))
out.sort(key=lambda x:-x['tot'])
for o in out: print(o['c'],o['n'],o['tot'],'| 時',o['shi'],'法',o['inst'],'產',o['ind'],'技',o['tech'],'價',o['pos'],'| 營',o['rev'],'EPS',o['eps'],'持',o['fr'],'反',o['rv'],'動能',o['mom'],o['mm'],'龍',o['lead'],o['mods'],'大漲',o['big'],'| L',o['lvl'],'連買',o['streak'],'賣',o['sell'],'f5',int(o['f5']),'cum',int(o['cum']),'d5',o['d5'] and round(o['d5'],1),'top50' if o['intop'] else '-','ma',o['vsma'])
json.dump(out,open(f'data/{T}/_scores.json','w',encoding='utf-8'),ensure_ascii=False)
