import json,re
T='2026-10-02'
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
top=json.load(open('data/2026-10-01/institutional_top50.json',encoding='utf-8'))
buy={s['code']:s for s in top['stocks'] if s['total']>0}
A=json.load(open(f'data/{T}/catalyst_preposition_scan.json',encoding='utf-8'))
L2={x['code'] for x in A['l2_stocks']}
L3A={x['code'] for x in A['l3_stocks']}
names=json.load(open('data/cache/stock_names.json',encoding='utf-8'))
NM={'6488':'環球晶','3131':'弘塑','3680':'家登','3324':'雙鴻','3374':'精材','5347':'世界先進'}
# code:(時事,產業,催化對齊,🔴覆寫可用,註)
M={
'2327':(19,18,1,0,'🟡被動元件缺貨漲價 點名↑ 18＋方向↑加速 +1；被動元件 tier_0 MLCC龍頭'),
'2492':(19,17,1,0,'🟡被動元件 點名↑+1；tier_0 晶片電阻（🟡非🔴 → 覆寫不適用）'),
'2481':(16,14,1,0,'🟡被動元件族群（未點名）；tier_from_tracker'),
'3042':(19,14,1,0,'🟡被動元件 點名↑+1；tier_from_tracker'),
'3026':(19,14,1,0,'🟡被動元件 點名↑+1；tier_from_tracker'),
'6168':(19,14,1,0,'🟡被動元件 點名↑；tier_from_tracker'),
'3090':(16,13,0,0,'🟡被動元件通路 tier_2（未點名）'),
'8046':(19,18,1,0,'🟡ABF載板 點名↑+1；tier_0 AI晶片載板'),
'3189':(19,18,1,0,'🟡ABF載板 點名↑+1；tier_0 FC-BGA 載板'),
'3037':(19,18,1,0,'🟡ABF載板/PCB 點名↑ 18＋方向↑加速 +1；tier_0 AI晶片ABF載板'),
'6213':(19,13,1,0,'🟡ABF/CCL 點名↑+1；tier_3 CCL'),
'6672':(16,14,1,0,'🟡ABF/PCB tier_from_tracker（未點名）'),
'2383':(19,14,1,0,'🟡CCL 點名↑'),
'2368':(19,14,1,0,'🟡ABF/PCB 點名↑；tier_2'),
'2367':(16,14,0,0,'PCB tier_2、未點名'),
'2313':(16,13,0,0,'🟡ABF/PCB（未點名）tier_2'),
'3231':(22,17,1,1,'🔴AI伺服器 點名↑ 21＋方向↑加速 +1；AI tier_1'),
'2317':(22,17,1,1,'🔴AI 點名↑（甲骨文-騰訊算力租賃）+1；AI tier_1'),
'3706':(22,14,1,1,'🔴AI 點名↑+1；tier_from_tracker'),
'2382':(22,18,1,1,'🔴AI 點名↑+1；AI tier_1 龍頭'),
'6669':(22,17,1,1,'🔴AI 點名↑+1'),
'4938':(22,14,1,1,'🔴AI 點名↑（美系 AI 伺服器新單出貨）+1；AI tier_from_tracker'),
'3013':(22,14,1,1,'🔴AI 點名↑（VR200 機櫃）+1；tier_from_tracker'),
'2308':(22,14,1,1,'🔴AI 點名↑+1；AI tier_3'),
'2404':(22,17,1,1,'🔴AI 點名↑+1；廠務工程 tier_0'),
'6196':(22,14,1,1,'🔴AI 點名↑+1；tier_from_tracker'),
'2330':(22,20,1,1,'🔴AI 點名↑ 21＋方向↑加速 +1；半導體 tier_0 龍頭'),
'2303':(21,18,1,1,'🔴AI（今日未點名，下緣 20）+1；🟡台股市場動態點名↑；半導體 tier_0'),
'3711':(22,18,1,1,'🔴AI 點名↑+1；AI tier_0 CoWoS'),
'6257':(21,14,1,1,'🔴AI（封測，未點名，下緣 20）+1；tier_from_tracker'),
'6239':(21,15,1,1,'🔴AI/記憶體封測（未點名）+1；半導體 tier_1'),
'8150':(21,15,1,1,'🔴AI/記憶體封測（未點名）+1；半導體 tier_1'),
'2449':(21,18,1,1,'🔴AI 測試（⚪點名↑）；tier_0'),
'2356':(20,15,1,0,'🔴AI（未點名）；AI tier_1'),
'2376':(20,14,1,1,'🔴AI tier_from_tracker（未點名）'),
'3702':(20,14,1,0,'🔴AI tier_from_tracker（未點名）'),
'2347':(20,14,1,0,'🔴AI tier_from_tracker（未點名）；非影響鏈點名 → 覆寫不採'),
'2379':(20,15,1,0,'🔴AI tier_from_tracker／網通 tier_1 乙太網路晶片（未點名，下緣 20）'),
'2353':(10,13,0,0,'⚪記憶體缺貨衝擊終端（PC 毛利承壓，方向→偏空）'),
'2377':(12,13,0,0,'AI PC tier_from_tracker、未點名'),
'2301':(16,14,0,0,'AI tier_3 電源、今日僅⚪太空點名'),
'3583':(20,14,1,0,'🔴AI 設備（⚪點名）'),
'6770':(23,14,1,1,'🔴DRAM／光通訊雙點名↑ 21＋MU +3.03% +1＋多重🔴共振 +1；tier_from_tracker'),
'2344':(22,17,1,1,'🔴DRAM 點名↑ 21＋MU +3.03% +1；記憶體 tier_0'),
'2408':(22,18,1,1,'🔴DRAM 點名↑ 21＋MU +3.03% +1；記憶體 tier_0'),
'2337':(22,17,1,1,'🔴DRAM 點名↑ 21＋MU +3.03% +1；記憶體 tier_0'),
'2609':(21,14,1,1,'🔴中東（含航運）點名↑；tier_from_tracker'),
'2603':(21,14,1,1,'🔴中東點名↑；tier_from_tracker'),
'2615':(21,14,1,1,'🔴中東點名↑；tier_from_tracker'),
'6505':(22,14,1,1,'🔴中東點名↑＋方向↑ +1；塑化 tier_from_tracker'),
'1303':(22,17,1,1,'🔴中東點名↑+1；塑化 tier_0'),
'1326':(22,17,1,1,'🔴中東點名↑+1；塑化 tier_0'),
'1301':(20,18,1,1,'🔴中東鏈（未直接點名）；塑化 tier_0 龍頭'),
'1314':(14,13,0,0,'中東 tier_from_tracker 登錄、未點名；營收連衰'),
'1312':(14,13,0,0,'中東 tier_from_tracker 登錄、未點名'),
'1718':(12,13,0,0,'塑化 tier_2 化纖、未點名'),
'1727':(11,13,0,0,'⚪塑化股逆勢走強點名↑（觀察中）'),
'2618':(10,17,0,0,'🔴中東鏈標「↓ 燃油成本壓力」＝利空'),
'2610':(10,17,0,0,'🔴中東鏈標「↓ 燃油成本壓力」＝利空'),
'2345':(21,17,1,1,'🔴光通訊點名↑；網通 tier_0'),
'4977':(21,17,1,1,'🔴光通訊點名↑'),
'3234':(20,17,1,0,'🔴光通訊（未點名）'),
'4956':(14,13,0,0,'光通訊 tier_from_tracker、未點名'),
'2392':(12,13,0,0,'連接器 tier_2、未點名'),
'3017':(11,14,0,0,'⚪散熱'),'3324':(11,14,0,0,'⚪散熱'),'6230':(10,14,0,0,'散熱 tier_2、未點名'),
'3443':(18,18,1,0,'🟡ASIC 點名↑'),'3661':(18,17,1,0,'🟡ASIC 點名↑'),
'3035':(17,15,1,0,'🟡ASIC 客製化需求鏈（未點名，中段 17）；ASIC tier_1'),
'2891':(20,17,1,0,'🔴聯準會點名↑'),'2882':(18,17,0,0,'🔴聯準會點名→；🟡美債↓'),'2890':(18,13,0,0,'🔴聯準會點名→ 現增稀釋'),'2883':(18,13,0,0,'🔴聯準會點名→ 現增稀釋'),
'2886':(18,17,0,0,'🔴聯準會鏈未點名；金融 tier_0'),'2884':(16,13,0,0,'金融未點名'),'2892':(16,13,0,0,'金融未點名'),'2801':(16,15,0,0,'金融 tier_1 銀行、未點名'),
'5876':(10,13,0,0,'金融 tier_from_tracker'),'2867':(10,13,0,0,'凍結'),
'2412':(12,17,0,0,'電信 tier_0；⚪太空點名→'),'3045':(10,17,0,0,'電信 tier_0；⚪公開收購精誠'),
'2395':(15,14,1,0,'🟢邊緣AI／工業電腦'),
'2634':(11,13,0,0,'⚪軍工與無人機點名↑（觀察中）'),
'1102':(10,15,0,0,'水泥 tier_1、無🔴🟡對應'),
'6533':(10,13,0,0,'AI資安 tier_from_tracker、無🔴🟡對應'),
'3167':(10,13,0,0,'被動元件舊主題 tier_from_tracker、未點名'),
'3036':(10,13,0,0,'通路、無🔴🟡對應'),
}
LEADER_L1={'2345','2412','3042','2449'}
DISP={'2030':'🔴🔴 TWSE 處置股（10/02~10/08）','3016':'🔴🔴 TWSE 處置股（10/01~10/12）','6168':'🔴🔴 TWSE 處置股（09/24~10/02）','3443':'🔴🔴 TWSE 處置股（09/29~10/05）'}
MU=set()
COLD={'2337':-5,'1102':-5,'1718':-3}
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
    if total<70: excl.append('總分<70')
    out.append(dict(code=c,name=nm,level=lvl,avg_rank=ar,total_k=round(tot),buy_ratio=(b or {}).get('buy_ratio'),d5=d5,cum=ch.get('cum'),bs=f"{ch.get('buyd')}/{ch.get('selld')}",consec=consec,f5=ch.get('f5'),mom=ch.get('mom'),vs_ma20=vm,
        news=news,inst=inst,ind=ind,tech=tech,price=price,sub=sub,mods=mods,total=total,excl=excl,note=note,close=p.get('current'),
        rev_yoy=rv.get(c,{}).get('yoy'),pull=rv.get(c,{}).get('pullback_5d'),eps_q=e.get('latest_quarter'),fr_chg=fr.get(c,{}).get('ratio_change'),alert=r.get('alert_reason')))
json.dump(out,open(f'data/{T}/pool_table.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for o in sorted(out,key=lambda o:-o['total']):
    ms=' '.join(f'{k}{v:+d}' for k,v in o['mods'])
    print(f"{o['code']} {o['name']}|{o['news']}/{o['inst']}/{o['ind']}/{o['tech']}/{o['price']}={o['sub']}|{ms}|{o['total']}|{'PASS' if not o['excl'] else '❌'+'；'.join(o['excl'])}")
