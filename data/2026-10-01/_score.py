import json,re
T='2026-10-01'
def L(f): return json.load(open(f'data/{T}/{f}',encoding='utf-8'))
chip={}
txt=open(f'data/{T}/_chip_pool.txt',encoding='utf-8').read()
def num(s):
    if s is None: return None
    s=s.replace(',','').replace('+','')
    m=re.match(r'(-?[\d.]+)(K?)',s)
    return float(m.group(1))*(1000 if m.group(2) else 1) if m else None
def g(p,blk):
    m=re.search(p,blk)
    return m.group(1) if m else None
for blk in re.split(r'\n📊 ',txt)[1:]:
    m=re.match(r'(.+?)\((\d+)\) 籌碼分析',blk)
    if not m: continue
    name,code=m.groups()
    chip[code]=dict(name=name,cum=g(r'累計淨買超（三大法人）: (\S+)',blk),buyd=g(r'買超天數: (\d+)',blk),selld=g(r'賣超天數: (\d+)',blk),
        consec=g(r'真連續買超: (\d+)',blk),f5=g(r'近5天淨買超（外資）\s*: (\S+)',blk),mom=g(r'動能變化: (\S+)',blk))
rev={r['stock_code']:r for r in L('reversal_alerts.json')}
pp={r['code']:r for r in L('price_position_check.json')}
rv={r['code']:r for r in L('revenue_check.json')}
ep={r['code']:r for r in L('eps_check.json')}
fr={r['code']:r for r in L('foreign_ratio_check.json')}
top=json.load(open('data/2026-09-30/institutional_top50.json',encoding='utf-8'))
buy={s['code']:s for s in top['stocks'] if s['total']>0}
A=json.load(open(f'data/{T}/catalyst_preposition_scan.json',encoding='utf-8'))
L2={x['code'] for x in A['l2_stocks']}
names=json.load(open('data/cache/stock_names.json',encoding='utf-8'))
NM={'6488':'環球晶','3131':'弘塑','3680':'家登','3324':'雙鴻','3374':'精材','5347':'世界先進'}
# code:(時事,產業,催化對齊,🔴覆寫可用,註)
M={
'2609':(21,14,1,1,'🔴中東影響鏈點名↑（北美線高檔）；tier_from_tracker'),
'2603':(21,14,1,1,'🔴中東點名↑；tier_from_tracker'),
'2615':(21,14,1,1,'🔴中東點名↑；tier_from_tracker'),
'6505':(21,14,1,1,'🔴中東點名↑；塑化 tier_from_tracker'),
'1303':(21,17,1,1,'🔴中東點名↑；塑化 tier_0'),
'1326':(21,17,1,1,'🔴中東點名↑；塑化 tier_0'),
'1301':(20,18,1,1,'🔴中東鏈（未直接點名）＋⚪塑化股逆勢走強點名↑；塑化 tier_0 龍頭'),
'1314':(14,13,0,0,'中東 tier_from_tracker 登錄但未點名；當日新聞「核心產品 CPL 逆風」＋營收連衰'),
'1312':(14,13,0,0,'中東 tier_from_tracker 登錄、未點名'),
'1718':(12,13,0,0,'塑化 tier_2 化纖、未點名、提及 0'),
'1310':(10,8,0,0,'知識庫未分類'),
'2618':(12,17,0,0,'🔴中東鏈標「→ 燃油成本壓力回升」＝利空方向，覆寫不成立'),
'2610':(12,17,0,0,'🔴中東鏈標「→ 燃油成本壓力回升」＝利空方向，覆寫不成立'),
'3711':(22,18,1,1,'🔴AI 點名↑ 21＋方向↑加速 +1；AI tier_0'),
'6257':(21,14,1,1,'🔴AI（未點名，下緣 20）＋方向↑加速 +1；tier_from_tracker'),
'6239':(21,15,1,1,'🔴AI/記憶體封測（未點名）+1；半導體 tier_1'),
'2303':(22,18,1,1,'🔴AI 點名↑+1；半導體 tier_0'),
'2330':(22,20,1,1,'🔴AI 點名↑+1；半導體 tier_0 龍頭'),
'2308':(20,14,1,1,'🔴AI 鏈標「→」；AI tier_3'),
'2404':(22,17,1,1,'🔴AI 點名↑+1；廠務工程 tier_0'),
'6196':(22,14,1,1,'🔴AI 點名↑+1；tier_from_tracker'),
'3231':(22,17,1,1,'🔴AI 點名↑+1'),'2382':(22,18,1,1,'🔴AI 點名↑+1'),'6669':(22,17,1,1,'🔴AI 點名↑+1'),'3706':(22,14,1,1,'🔴AI 點名↑+1'),
'2317':(20,17,1,1,'🔴AI（未點名）；AI tier_1'),'2354':(16,13,0,0,'AI tier_3 機殼、未點名'),'2324':(14,13,0,0,'⚪AI Factory 點名（觀察中）'),
'6770':(22,14,1,1,'🔴DRAM／光通訊點名↑；tier_from_tracker'),
'2344':(21,17,1,1,'🔴DRAM 點名↑；記憶體 tier_0'),
'2408':(21,18,1,1,'🔴DRAM 點名↑；記憶體 tier_0'),
'2337':(21,17,1,1,'🔴DRAM 點名↑；記憶體 tier_0'),
'8150':(20,15,1,1,'🔴AI/記憶體封測'),
'3481':(14,17,0,0,'🟢面板雙虎（中度）；面板 tier_0'),'2409':(14,17,0,0,'🟢友達先進封裝（中度）'),'6116':(13,13,0,0,'🟢面板'),
'1101':(10,13,0,0,'⚪台泥歐洲併購'),'2002':(10,17,0,0,'⚪鋼鐵觸底'),'1605':(10,13,0,0,'⚪銅供給'),'3576':(10,13,0,0,'⚪太空AI'),
'2371':(11,13,0,0,'⚪AI Factory 電力架構點名↑（觀察中，非🔴/🟡）'),
'2892':(16,13,0,0,'🔴聯準會鏈未點名（金融）'),'2887':(16,17,0,0,'金融 tier_0、未點名'),
'2891':(20,17,1,0,'🔴聯準會點名↑'),'2886':(18,17,0,0,'🔴聯準會未點名'),'2884':(16,13,0,0,'金融未點名'),'2882':(20,17,1,0,'🔴聯準會點名→'),'2890':(18,13,0,0,'🔴聯準會點名→ 現增稀釋'),'2883':(18,13,0,0,'🔴聯準會點名→ 現增稀釋'),
'2412':(12,17,0,0,'電信 tier_0；⚪太空點名→'),'3045':(10,17,0,0,'電信 tier_0；⚪公開收購精誠'),'5876':(10,13,0,0,'金融 tier_from_tracker'),
'2395':(15,14,1,0,'🟢邊緣AI／工業電腦'),'3702':(20,14,1,0,'🔴AI tier_from_tracker'),'2376':(20,14,1,1,'🔴AI tier_from_tracker'),
'2454':(14,17,0,0,'⚪高通/聯發科'),'2345':(21,17,1,1,'🔴光通訊點名↑'),'3717':(21,14,1,1,'🔴光通訊點名↑'),
'4763':(10,8,0,0,'⚪材料-KY 併購'),'2313':(16,13,0,0,'🟡ABF/PCB（未點名）'),'3090':(16,13,0,0,'🟡被動元件通路'),'4938':(14,13,0,0,'無🔴🟡對應'),
'3661':(18,14,1,0,'🟡ASIC'),'2383':(18,14,1,0,'🟡CCL'),'3583':(20,14,1,0,'🔴AI 設備'),'2356':(20,15,1,0,'🔴AI'),'3017':(18,14,0,0,'⚪散熱'),
}
MU={'6770','2344','2408','2337'}
COLD={'1101':-5,'2337':-5}
out=[]
pool=open(f'data/{T}/_pool.txt').read().split()
for c in pool:
    ch=chip.get(c,{}); r=rev.get(c,{}); p=pp.get(c,{}); b=buy.get(c)
    nm=ch.get('name') or (b or {}).get('name') or names.get(c) or NM.get(c,'?')
    if isinstance(nm,dict): nm=nm.get('name','?')
    news,ind,align,ovr,note=M.get(c,(10,8,0,0,'知識庫未分類／無🔴🟡對應'))
    lvl=r.get('level',-1)
    mom=num(ch['mom'].replace('%','')) if ch.get('mom') else None
    consec=int(ch['consec']) if ch.get('consec') else 0; selld=int(ch['selld']) if ch.get('selld') else 0
    f5=num(ch.get('f5'))
    if b:
        ar=b['avg_rank']; inst=21 if ar<=10 else 18 if ar<=20 else 14 if ar<=35 else 10
        br=b['buy_ratio']; inst+= 2 if br>20 else 1 if br>=10 else 0
        if b['foreign']>0 and b['trust']>=100000: inst+=1
        tot=b['total']/1000
    else: inst=6; tot=0; ar=None
    if consec>=5: inst+=1
    inst=min(inst,25)
    if selld>=7: inst=min(inst,15)
    mods=[]
    if selld==6: mods.append(('賣超6天',-5))
    if tot>=30000 and consec<7: mods.append(('過量買超',-5))
    if lvl==0 and mom is not None and mom<-30 and consec>=3: tech=14
    elif lvl==0 and mom is not None and mom<0: tech=12
    elif lvl==0 and 3<=consec<=4: tech=11
    elif lvl==0: tech=10
    elif lvl==1: tech=8
    elif lvl==-1: tech=9
    else: tech=4
    price=p.get('adj',0) or 0
    sub=news+inst+ind+tech+price
    excl=[]
    d5=(b or {}).get('5day_change')
    if lvl in (3,4): excl.append(f'反轉 L{lvl}')
    if lvl==2: mods.append(('反轉L2',-15))
    if lvl==1: mods.append(('反轉L1',-5))
    if lvl==-1: excl.append('③反轉狀態不明/數據不足（非 L0）')
    if mom is not None:
        if mom<-30: mods.append(('動能<-30%',15))
        elif mom<0: mods.append(('動能<0',10))
        elif mom>100:
            if ovr and not (d5 and d5>20): mods.append(('🔥超強催化覆寫',0))
            else: excl.append(f'動能 {mom:+.0f}% >100% 無覆寫')
        elif mom>50: mods.append(('動能50-100%',-10))
    if d5 is not None:
        if d5>10: excl.append(f'5日 {d5:+.1f}% >10% 已大漲')
        elif d5>=5: mods.append(('5日5-10%',-10))
    if c in L2: mods.append(('📶訊號A L2',10))
    ra=rv.get(c,{}).get('adj') or 0
    if ra: mods.append(('營收',ra))
    e=ep.get(c,{}); ea=e.get('adj') or 0
    if e.get('latest_quarter')=='2025-12-31':
        ea=0; note+='｜⚠️EPS 快取停於 2025Q4（金融業），本因子未採計'
    if ea: mods.append(('EPS',ea))
    fs=fr.get(c,{}).get('suggestion','') or ''
    fa=5 if fs.startswith('+5') else (-3 if fs.startswith('-3') else 0)
    if fa: mods.append(('持股比',fa))
    if c in COLD: mods.append(('cold',COLD[c]))
    neg=max(sum(v for k,v in mods if v<0),-20); pos=sum(v for k,v in mods if v>0)
    total=sub+pos+neg
    if not align: excl.append('①催化對齊未過')
    if f5 is not None and f5<0: excl.append(f'②外資近5天 {f5:+,.0f} 為負')
    vm=p.get('vs_ma20')
    if not b and vm is not None and 0<=vm<=5: excl.append(f'法人現身門檻未過（不在TOP50買超×乖離{vm:+.2f}%）')
    if c in MU: excl.append('🔔美光今日財報→當日不開新倉')
    if total<70: excl.append('總分<70')
    out.append(dict(code=c,name=nm,level=lvl,avg_rank=ar,total_k=round(tot),buy_ratio=(b or {}).get('buy_ratio'),d5=d5,cum=ch.get('cum'),bs=f"{ch.get('buyd')}/{ch.get('selld')}",consec=consec,f5=ch.get('f5'),mom=ch.get('mom'),vs_ma20=vm,
        news=news,inst=inst,ind=ind,tech=tech,price=price,sub=sub,mods=mods,total=total,excl=excl,note=note,close=p.get('current'),
        rev_yoy=rv.get(c,{}).get('yoy'),pull=rv.get(c,{}).get('pullback_5d'),eps_q=e.get('latest_quarter'),fr_chg=fr.get(c,{}).get('ratio_change'),alert=r.get('alert_reason')))
json.dump(out,open(f'data/{T}/pool_table.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for o in sorted(out,key=lambda o:-o['total']):
    ms=' '.join(f'{k}{v:+d}' for k,v in o['mods'])
    print(f"{o['code']} {o['name']}|{o['news']}/{o['inst']}/{o['ind']}/{o['tech']}/{o['price']}={o['sub']}|{ms}|{o['total']}|{'PASS' if not o['excl'] else '❌'+'；'.join(o['excl'])}")
