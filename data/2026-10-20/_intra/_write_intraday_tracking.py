import json
p='data/tracking/tracking_2026-10-20.json'
t=json.load(open(p,encoding='utf-8'))
px=json.load(open('data/2026-10-20/_intra/prices.json',encoding='utf-8'))['data']
t['phase']='intraday'
t['intraday_time']='2026-10-20 12:30'
t['intraday_price_source']='Yahoo regularMarketPrice（12:30-12:40）；籌碼為 10/19 T86（今日 T86 尚未公布）'
dmap={'2887':0,'2002':5,'2886':5,'2892':5,'2882':2,'1326':1,'1802':1,'1605':1}
for r in t['recommendations']+t['carry_over_recommendations']:
    c=r['stock_code']
    if c in px and px[c]['price']:
        r['intraday_price']=px[c]['price']
        r['intraday_change_pct']=px[c]['chg_pct']
        r['intraday_return_pct']=round((px[c]['price']/r['recommend_price']-1)*100,2)
        r['two_day_pct']=px[c]['two_day_pct']
    r['result']='holding'
    if c in dmap:
        r['holding_days']=dmap[c]; r['holding_days_label']=f"D{dmap[c]}/10"
t['intraday_reversal']={
 'source':'10-19 T86（同盤前，今日 T86 未公布）',
 'L4':{'2882':'6.4%','1326':'10.1%','1802':'24.3%','1605':'22.8%','6770':'29.1%','2337':'31.1%','3090':'8.6%','1301':'9.5%','2330':'14.1%'},
 'L0':['2887','2002','2886','2892','2313','4938']}
t['pending_review_status']=[{'stock_code':'2882','stock_name':'國泰金','review_1_1230':'6.4% ≥5%（來源 10-19 T86，與盤前同源，無新資訊）','review_2_after':'待盤後以當日 T86 複核','rule':'兩次皆≥5% → 次日開盤出場'}]
sl_map=[('2887',38.12),('2002',17.28),('2886',45.0),('2892',35.73),('2882',102.15),('1326',70.83),('1802',60.21),('1605',34.65),('6770',73.26),('2337',147.6),('3090',256.5),('2313',235.98),('1301',54.08),('4938',76.5)]
t['intraday_stop_loss_check']=[{'stock_code':c,'price':px[c]['price'],'stop_loss':sl,'hit':px[c]['price']<sl} for c,sl in sl_map]
t['two_day_drawdown_check']={c:px[c]['two_day_pct'] for c in px}
t['track_b_recommendations']=[]
t['track_b_observations']=[
 {'stock_code':'6834','stock_name':'天二科技','score_est':84,'reason':'法人#24、動能-83%、營收+132%回檔-16.9%(+5)、EPS+313%(+5)、外資持股比+1.92%(+5)、10日6天賣超(-5)；但 topic_tracker 列「處置股擴大／投機末段訊號」↓、30日+44.8%、週轉8.2% 自算接近注意門檻、無正向催化對齊（準確率篩選①不過）→ 不推薦'},
 {'stock_code':'6141','stock_name':'柏承','reason':'偵測器強訊號60；PCB 強催化、動能-72%、外資持股比+0.77%、EPS+55%；但 12:38 漲幅+3.4%≥3%、5日+6.8%已大漲(-10)、6日+10.6%/週轉8.5% 自算接近注意門檻、法人#44 → 不推薦'},
 {'stock_code':'9105','stock_name':'泰金寶-DR','reason':'法人#22 買超7,160張、動能-75%、股價未反映(-1.2%)；但無產業分類、無催化對齊、真連買1天、EPS無數據 → 約67分 <75'},
 {'stock_code':'3701','stock_name':'大眾控','reason':'偵測器強訊號65；不在TOP50、今日-4.8%量比2.3x屬型態轉弱、EPS連3季負(-5)、topic_tracker 列投機末段↓ → 排除'},
 {'stock_code':'4989','stock_name':'榮科','reason':'偵測器強訊號60；10日累計 -3,804 張（累計為負）→ 排除'},
 {'stock_code':'6722','stock_name':'輝創','reason':'偵測器強訊號65；10日累計僅 +22 張，法人量體過小 → 不評分'},
 {'stock_code':'2504','stock_name':'國產','reason':'營收連8月衰退(-5)、EPS連2季負(-5)、法人#44 → <70'},
 {'stock_code':'2851','stock_name':'中再保','reason':'動能+76%(-10)、5日+6.2%(-10)、營收連4月衰退(-5) → <70'},
 {'stock_code':'1102','stock_name':'亞泥','reason':'真連買9天但動能+63.8%(-10)、法人#46、無催化 → <70'},
 {'stock_code':'4927','stock_name':'泰鼎-KY','reason':'動能+82%(-10)、EPS連3季負(-3)、真連買1天 → <70'},
 {'stock_code':'2880','stock_name':'華南金','reason':'近5天外資 -82 張（準確率篩選②不過）'},
 {'stock_code':'2542','stock_name':'興富發','reason':'盤前61分，盤中+1.0%無新資訊'},
 {'stock_code':'9945','stock_name':'潤泰新','reason':'盤前62分，盤中-0.5%無新資訊'}]
t['intraday_detector_summary']={'strong':['6722','3701','6141','4989'],'medium':['4526'],'adopted':[]}
t['disposition_check_intraday']={'official_disposition_in_pool':[],'official_attention_in_pool':['6278 台表科','6269 台郡（今日+10%）'],'self_calc_near':['6141 柏承','6834 天二科技']}
json.dump(t,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
