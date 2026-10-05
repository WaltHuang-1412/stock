import json,re
T='2026-10-05'
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
top=json.load(open('data/2026-10-02/institutional_top50.json',encoding='utf-8'))
buy={s['code']:s for s in top['stocks'] if s['total']>0}
A=json.load(open(f'data/{T}/catalyst_preposition_scan.json',encoding='utf-8'))
L2={x['code'] for x in A['l2_stocks']}
L3A={x['code'] for x in A['l3_stocks']}
names=json.load(open('data/cache/stock_names.json',encoding='utf-8'))
NM={'6488':'環球晶','3131':'弘塑','3680':'家登','3324':'雙鴻','3374':'精材','5347':'世界先進'}
# code:(時事,產業,催化對齊,🔴覆寫可用,註)
M={
'2330':(22,20,1,1,'🔴AI伺服器與半導體 點名↑ 21＋方向↑加速 +1（費半 +2.40%、ADR +2.96%）；半導體 tier_0 龍頭'),
'2317':(22,17,1,1,'🔴AI 點名↑（GB300 機器人組裝）21＋方向↑加速 +1，惟 tracker 註「外資調節」；AI tier_1'),
'3706':(22,14,1,1,'🔴AI 點名↑+1；tier_from_tracker'),
'2382':(22,18,1,1,'🔴AI 點名↑+1；AI tier_1 龍頭'),
'6669':(22,17,1,1,'🔴AI 點名↑+1'),
'4938':(22,14,1,1,'🔴AI 點名↑+1；AI tier_from_tracker'),
'3231':(21,17,1,1,'🔴AI 點名但方向「→」（外資調節）→ 下緣 20＋方向↑加速 +1；AI tier_1'),
'2301':(22,14,1,1,'🔴AI 點名↑+1；AI tier_3 電源'),
'3013':(22,14,1,1,'🔴AI 點名↑+1；tier_from_tracker'),
'2308':(22,14,1,1,'🔴AI 點名↑+1；AI tier_3'),
'2356':(20,15,1,0,'🔴AI（未點名，下緣 20）；AI tier_1'),
'2404':(22,17,1,1,'🔴AI 點名↑+1；🟡台積電產能鏈點名↑；廠務工程 tier_0'),
'6196':(22,14,1,1,'🔴AI 點名↑+1；tier_from_tracker'),
'2303':(22,18,1,1,'🔴AI 點名↑ 21＋方向↑加速 +1（聯電 ADR +4.20%）；半導體 tier_0'),
'3711':(23,18,1,1,'🔴AI 點名↑ 21＋加分 +2（日月光 ADR +6.08% >+5%、方向↑加速；合計封頂 +2）；AI tier_0 CoWoS'),
'6257':(21,14,1,1,'🔴AI（封測，未直接點名，下緣 20）+1；⚪AI高階測試點名↑；tier_from_tracker'),
'6239':(22,15,1,1,'🔴AI／🔴DRAM 雙點名↑ 21＋方向↑加速 +1；半導體 tier_1 封測'),
'8150':(21,15,1,1,'🔴AI/記憶體封測（未點名，下緣 20）+1；半導體 tier_1'),
'2449':(20,18,1,0,'🔴AI 測試（🟡財報鏈點名→）；tier_0'),
'3583':(20,14,1,0,'🔴AI 設備（⚪散熱設備點名↑）'),
'2454':(20,15,1,0,'🔴AI 點名「→」；🟡ASIC 點名→；IC設計 tier_1'),
'2379':(20,15,1,0,'🔴AI tier_from_tracker／網通 tier_1（未點名，下緣 20）'),
'3702':(20,14,1,0,'🔴AI tier_from_tracker（未點名）'),
'2376':(15,14,1,0,'🟢邊緣AI 點名→；⚪AI Factory 電力點名↑'),
'2357':(15,14,1,0,'🟢邊緣AI／工業電腦 點名↑（10/8 RTX Spark 筆電）14＋方向↑ +1；tier_from_tracker'),
'2377':(15,13,1,0,'🟢邊緣AI 點名↑ 14＋1；AI PC tier_from_tracker'),
'2353':(12,13,0,0,'🟢邊緣AI 點名→；⚪記憶體缺貨衝擊終端（偏空）'),
'6770':(22,14,1,1,'🔴DRAM／光通訊雙點名↑ 21＋多重🔴共振 +1；tier_from_tracker'),
'2344':(21,17,1,1,'🔴DRAM 點名↑ 21；記憶體 tier_0'),
'2408':(21,18,1,1,'🔴DRAM 點名↑ 21（9 月營收）；記憶體 tier_0'),
'2337':(21,17,1,1,'🔴DRAM 點名↑ 21；記憶體 tier_0'),
'3006':(21,14,1,1,'🔴DRAM 點名↑ 21（8 月營收 +605%）；tier_from_tracker'),
'2342':(10,8,0,0,'知識庫未分類（功率半導體；⚪半導體第二波漲價未點名）'),
'2609':(22,14,1,1,'🔴中東（含航運）點名↑ 21＋方向↑ +1；tier_from_tracker'),
'2603':(22,14,1,1,'🔴中東點名↑+1；tier_from_tracker'),
'2615':(22,14,1,1,'🔴中東點名↑+1；tier_from_tracker'),
'6505':(22,14,1,1,'🔴中東點名↑ 21＋方向↑ +1；塑化 tier_from_tracker'),
'1303':(22,17,1,1,'🔴中東點名↑+1；塑化 tier_0'),
'1326':(22,17,1,1,'🔴中東點名↑+1；塑化 tier_0'),
'1301':(20,18,1,0,'🔴中東鏈（未直接點名，下緣 20；⚪塑化股逆勢走強點名↑）；塑化 tier_0 龍頭；非🔴影響鏈點名 → 覆寫不採'),
'1314':(14,13,0,0,'中東 tier_from_tracker 登錄、未點名'),
'1312':(14,13,0,0,'中東 tier_from_tracker 登錄、未點名'),
'1313':(11,13,0,0,'塑化 tier_2 化學材料、未點名'),
'1310':(10,8,0,0,'知識庫未分類（SM 單體）'),
'1714':(10,8,0,0,'知識庫未分類'),
'1718':(12,13,0,0,'塑化 tier_2 化纖、未點名'),
'1409':(10,13,0,0,'tier_from_tracker（舊主題），今日未點名'),
'1402':(10,8,0,0,'知識庫未分類'),
'1727':(12,13,0,0,'⚪塑化股逆勢走強／⚪台積電特化 雙點名↑（觀察中）'),
'2618':(10,17,0,0,'🔴中東鏈標「↓ 燃油成本壓力」＝利空'),
'2610':(10,17,0,0,'🔴中東鏈標「↓ 燃油成本壓力」＝利空'),
'2345':(21,17,1,1,'🔴光通訊點名↑ 21；網通 tier_0'),
'4977':(21,17,1,1,'🔴光通訊點名↑'),
'3008':(18,15,0,0,'🔴光通訊點名「→ 法說觀察」（10/8 法說）；蘋果鏈 tier_1'),
'3714':(14,13,0,0,'光通訊／友達先進封裝 tier_from_tracker（今日未點名）'),
'2327':(19,18,1,0,'🟡被動元件缺貨漲價 點名↑ 18＋方向↑加速 +1；被動元件 tier_0 MLCC龍頭'),
'2492':(19,17,1,0,'🟡被動元件 點名↑+1；tier_0 晶片電阻'),
'3026':(19,14,1,0,'🟡被動元件 點名↑+1；tier_from_tracker'),
'3042':(19,14,1,0,'🟡被動元件 點名↑+1；tier_from_tracker'),
'2481':(14,14,0,0,'⚪半導體第二波漲價（功率半導體）點名↑（觀察中，首見 10/05）；🟡被動元件未點名'),
'3090':(16,13,0,0,'🟡被動元件通路 tier_2（tracker 引日電貿說法、影響鏈未點名）'),
'3037':(19,18,1,0,'🟡ABF載板/PCB 點名↑ 18＋方向↑加速 +1；tier_0 AI晶片ABF載板'),
'3189':(19,18,1,0,'🟡ABF載板 點名↑+1；tier_0 FC-BGA 載板'),
'8046':(19,18,1,0,'🟡ABF載板 點名↑+1（9 月營收 +57.8%）；tier_0'),
'6213':(19,13,1,0,'🟡ABF/CCL 點名↑+1；tier_3 CCL'),
'6672':(19,14,1,0,'🟡ABF/CCL 點名↑+1；tier_from_tracker'),
'2383':(19,14,1,0,'🟡CCL 點名↑+1'),
'2368':(19,14,1,0,'🟡ABF/PCB 點名↑+1；tier_2'),
'4958':(17,14,1,0,'🟡ABF/PCB 點名「→ 10/13 法說」（中段 17）；🔴台股市場動態點名↑（外資投信加碼焦點）；tier_from_tracker'),
'8021':(14,13,0,0,'PCB 鑽針；tier_from_tracker（籌資擴產舊主題），今日未點名'),
'4927':(14,13,0,0,'PCB；tier_from_tracker（財報），今日未點名'),
'2313':(16,13,0,0,'🟡ABF/PCB（未點名）tier_2'),
'2409':(19,17,1,0,'🟡友達先進封裝雙線作戰 點名↑ 18＋方向↑加速 +1（tracker 註「股價漲幅過大」）；面板 tier_0'),
'3481':(19,17,1,0,'🟡友達先進封裝（面板雙虎）點名↑ 18＋1；面板 tier_0'),
'6116':(16,13,0,0,'🟡友達先進封裝鏈點名「→」；tier_from_tracker'),
'3673':(10,8,0,0,'知識庫未分類'),'6120':(10,8,0,0,'知識庫未分類'),'1802':(10,8,0,0,'知識庫未分類'),
'3443':(18,18,1,0,'🟡ASIC 點名↑'),'3661':(18,17,1,0,'🟡ASIC 點名↑'),
'3035':(17,15,1,0,'🟡ASIC 客製化需求鏈（未點名，中段 17）；ASIC tier_1'),
'2891':(21,17,1,0,'🔴聯準會點名↑（AI 融資商機）'),'2882':(16,17,0,0,'🔴聯準會／🟡美債 雙點名↓（債券評價損失）＝利空'),
'2890':(18,13,0,0,'🔴聯準會點名→ 現增稀釋'),'2883':(18,13,0,0,'🔴聯準會點名→ 現增 200-250 億稀釋'),
'2886':(18,17,0,0,'🔴聯準會鏈未點名；金融 tier_0'),'2884':(16,13,0,0,'金融未點名'),'2892':(16,13,0,0,'金融未點名'),
'5880':(16,13,0,0,'金融 tier_from_tracker、未點名'),'2855':(10,13,0,0,'證券 tier_from_tracker（舊主題）、未點名'),
'2867':(10,13,0,0,'凍結'),
'2412':(12,17,0,0,'電信 tier_0；無🔴🟡對應'),'3045':(10,17,0,0,'電信 tier_0；無🔴🟡對應'),
'2002':(15,17,1,0,'🟢鋼鐵需求觸底反轉 點名↑ 14＋方向↑轉強 +1（今日開 11 月盤價）；鋼鐵 tier_0 龍頭'),
'2023':(15,13,1,0,'🟢鋼鐵 點名↑ 14＋1；tier_from_tracker'),
'1605':(15,13,1,0,'🟢鋼鐵 點名↑ 14＋1；tier_from_tracker（線纜／銅）'),
'1102':(10,15,0,0,'水泥 tier_1、無🔴🟡對應'),
'2542':(10,13,0,0,'營建 tier_from_tracker；🟢台灣房市方向↓'),
'9933':(12,13,0,0,'⚪AI建廠潮外溢 點名↑（觀察中）；tier_from_tracker'),
'2371':(12,13,0,0,'⚪AI Factory 電力架構 點名↑（觀察中）；電動車 tier_1'),
'1504':(12,13,0,0,'⚪AI Factory 電力／⚪AI建廠潮 點名↑（觀察中）'),
'1519':(12,13,0,0,'⚪AI建廠潮外溢 點名↑（觀察中）'),
'1513':(11,13,0,0,'重電 tier_from_tracker（AI 電力舊主題）、今日未點名'),
'3576':(11,13,0,0,'tier_from_tracker（太空AI／衛星舊主題）、🔴🟡未點名'),
'2634':(11,13,0,0,'軍工 tier_from_tracker、今日無🔴🟡對應'),
'3023':(16,14,1,0,'🟡企業財報重點 點名↑（中下緣 16）；⚪人形機器人點名↑；AI tier_2 連接器'),
'3017':(12,14,0,0,'⚪AI散熱 點名↑（觀察中）；AI tier_2'),
'2392':(10,13,0,0,'連接器 tier_2、未點名'),
'2474':(10,14,0,0,'蘋果鏈 tier_1 機殼、今日未點名'),
'6415':(10,8,0,0,'知識庫未分類'),
'2340':(10,8,0,0,'知識庫未分類'),'1709':(10,8,0,0,'知識庫未分類'),
}
LEADER_L1={'1303'}
LEADER_L3={'2408','2344','2337','6770'}
DISP={'3443':'🔴🔴 TWSE 處置股（09/29~10/05）'}
MU=set()
COLD={'2337':-5,'2002':-5,'1102':-5,'2317':-3,'1310':-3,'1312':-3}
D5=json.load(open("data/2026-10-05/_d5.json"))
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
    if d5 is None and D5.get(c): d5=D5[c]['d5']
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
    if c in L3A: mods.append(('📶訊號A L3',15))
    ra=rv.get(c,{}).get('adj') or 0
    if rv.get(c,{}).get('month')!='2026-08': ra=0
    if ra: mods.append(('營收',ra))
    e=ep.get(c,{}); ea=e.get('adj') or 0
    if e.get('latest_quarter')=='2025-12-31':
        ea=0; note+='｜⚠️EPS 快取停於 2025Q4（金融業），本因子未採計'
    if ea: mods.append(('EPS',ea))
    fs=fr.get(c,{}).get('suggestion','') or ''
    fa=5 if fs.startswith('+5') else (-3 if fs.startswith('-3') else 0)
    if fr.get(c,{}).get('stale'): fa=0
    if fa: mods.append(('持股比',fa))
    if c in COLD: mods.append(('cold',COLD[c]))
    if c in LEADER_L1: mods.append(('龍頭預警L1',-5))
    neg=max(sum(v for k,v in mods if v<0),-20); pos=sum(v for k,v in mods if v>0)
    total=sub+pos+neg
    if not align: excl.append('①催化對齊未過')
    if f5 is not None and f5<0: excl.append(f'②外資近5天 {f5:+,.0f} 為負')
    vm=p.get('vs_ma20')
    if not b and vm is not None and 0<=vm<=5: excl.append(f'法人現身門檻未過（不在TOP50買超×乖離{vm:+.2f}%）')
    if c in DISP: excl.insert(0,DISP[c])
    if c in LEADER_L3: excl.insert(0,'🚫 龍頭預警 Level 3（Western Digital -10.22%）直接排除')
    if total<70: excl.append('總分<70')
    out.append(dict(code=c,name=nm,level=lvl,avg_rank=ar,total_k=round(tot),buy_ratio=(b or {}).get('buy_ratio'),d5=d5,cum=ch.get('cum'),bs=f"{ch.get('buyd')}/{ch.get('selld')}",consec=consec,f5=ch.get('f5'),mom=ch.get('mom'),vs_ma20=vm,
        news=news,inst=inst,ind=ind,tech=tech,price=price,sub=sub,mods=mods,total=total,excl=excl,note=note,close=p.get('current'),
        rev_yoy=rv.get(c,{}).get('yoy'),pull=rv.get(c,{}).get('pullback_5d'),eps_q=e.get('latest_quarter'),fr_chg=fr.get(c,{}).get('ratio_change'),alert=r.get('alert_reason')))
json.dump(out,open(f'data/{T}/pool_table.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for o in sorted(out,key=lambda o:-o['total']):
    ms=' '.join(f'{k}{v:+d}' for k,v in o['mods'])
    print(f"{o['code']} {o['name']}|{o['news']}/{o['inst']}/{o['ind']}/{o['tech']}/{o['price']}={o['sub']}|{ms}|{o['total']}|{'PASS' if not o['excl'] else '❌'+'；'.join(o['excl'])}")
