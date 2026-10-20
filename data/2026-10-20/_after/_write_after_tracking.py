import json
D='2026-10-20'; f=f'data/tracking/tracking_{D}.json'
t=json.load(open(f,encoding='utf-8'))
t['phase']='after_market'
closes={'2887':41.0,'2002':19.6,'2886':53.2,'2892':40.75,'2882':110.0,'1326':73.8,'1802':67.4,'1605':37.0,'2867':None}
t86={'2887':-19629,'2002':24566,'2886':1273,'2892':1642,'2882':-7508}
lv={'2887':'L4 37.6%','2002':'L0','2886':'L0','2892':'L0','2882':'L4 33.7%'}
hs={'2002':'續抱；10-20 T86 +24,566 張、真連買 8 天',
    '2886':'續抱；+1,273 張、真連買 10 天，距目標 1.5%',
    '2892':'續抱；+1,642 張、真連買 8 天',
    '2882':'待複核② 33.7% ≥5%（10-20 T86 -7,508 張）→ 兩次皆 ≥5% 成立 → 10-21 開盤出場（已決事項）'}
for r in t['recommendations']:
    c=r['stock_code']; cl=closes[c]
    r['actual_close']=cl; r['close_price']=cl; r['return_pct']=round((cl-r['recommend_price'])/r['recommend_price']*100,2)
    r['result']='holding'; r['t86_today']=t86[c]; r['reversal_after']=lv[c]
    r['holding_status']='D0 不判定；10-20 T86 賣超 -19,629 張佔 5 日均量 37.6% ≥8%（外資 -22,524）→ 鐵律③ L4，不受 v8.3.3 保護 → 10-21 開盤出場（已決事項）'
for r in t['carry_over_recommendations']:
    c=r['stock_code']; cl=closes.get(c)
    if cl is None:
        r['holding_status']='⚠️ 序列停滯（末日 2026-08-19），凍結'; continue
    r['actual_close']=cl; r['return_pct']=round((cl-r['recommend_price'])/r['recommend_price']*100,2)
    if c in ('1326','1802','1605'):
        r['result']='success' if cl>r['recommend_price'] else 'fail'; r['settled_date']=D; r['settled_price']=cl
        r['holding_status']='已於 10-20 收盤價入帳結算（見 removed_stocks）'
    else:
        r['t86_today']=t86[c]; r['reversal_after']=lv[c]; r['holding_status']=hs[c]
t['pending_review_status']=[{'stock_code':'2882','stock_name':'國泰金',
  'review_1_1230':'6.4% ≥5%（來源 10-19 T86，與盤前同源）',
  'review_2_after':'33.7% ≥5%（來源 10-20 T86，賣超 -7,508 張，外資 -7,372；16:17 公布後重跑 reversal_alert）',
  'verdict':'兩次皆 ≥5% → 10-21 開盤出場（已決事項，不重評）'}]
sl=[('2887',41.0,38.12),('2002',19.6,17.28),('2886',53.2,45.0),('2892',40.75,35.73),('2882',110.0,102.15),('1326',73.8,70.83),('1802',67.4,60.21),('1605',37.0,34.65),('6770',64.1,73.26),('2337',100.0,147.6),('3090',157.0,256.5),('2313',243.5,235.98),('1301',74.9,54.08),('4938',105.0,76.5)]
t['after_close_stop_loss_check']=[{'stock_code':c,'close':cl,'stop_loss':s,'hit':cl<s} for c,cl,s in sl]
t['after_close_two_day_drawdown']={'2887':-3.42,'2002':0.26,'2886':-0.93,'2892':-1.81,'2882':-5.17,'1326':-6.23,'1802':0.75,'1605':-3.9,'6770':-4.75,'2337':-6.54,'3090':-7.92,'1301':-8.77,'2313':-1.81,'4938':2.94,'2330':-0.62}
t['after_reversal_holdings']={'2887':'L4 37.6%','2882':'L4 33.7%','6770':'L4 12.1%','3090':'L4 20.9%','1301':'L4 10.5%','2330':'L4 25.6%','2337':'L3 近2日 -13,475','2002':'健康 +24,566','4938':'健康 +7,651','2886':'L0 +1,273','2892':'L0 +1,642','2313':'L0 +2,092'}
t['tomorrow_opening_exits']=[
 {'stock_code':'2887','stock_name':'台新新光金','category':'追蹤新增L4','recommend_date':D,'reason':'10-20 T86 賣超 -19,629 張佔 5 日均量 37.6% ≥8%（外資 -22,524），不受 v8.3.3 保護 → 10-21 開盤出場，收盤價入帳'},
 {'stock_code':'2882','stock_name':'國泰金','category':'待複核定案','recommend_date':'2026-10-16','reason':'v8.3.3 複核① 6.4%／複核② 33.7%（10-20 T86 -7,508 張）皆 ≥5% → 10-21 開盤出場，收盤價入帳'},
 {'stock_code':'6770','stock_name':'力積電','category':'持倉已決','reason':'收盤 64.1<停損 73.26；10-20 T86 L4 12.1%'},
 {'stock_code':'2337','stock_name':'旺宏','category':'持倉已決','reason':'收盤 100.0<停損 147.6；L3'},
 {'stock_code':'3090','stock_name':'日電貿','category':'持倉已決','reason':'收盤 157.0<停損 256.5；L4 20.9%'},
 {'stock_code':'1301','stock_name':'台塑','category':'持倉已決','reason':'L4 10.5%（-13,255 張）；損益 +24.7% 仍 > yaml 停利 20%'},
 {'stock_code':'2313','stock_name':'華通','category':'持倉已決','reason':'已決事項不重評（今日 L0 +2,092）'},
 {'stock_code':'4938','stock_name':'和碩','category':'持倉已決','reason':'已決事項不重評（今日買超 +7,651）'},
 {'stock_code':'2330','stock_name':'台積電零股','category':'持倉已決','reason':'L4 25.6%（-8,356 張）'}]
t['tomorrow_pending_review']=[]
t['tomorrow_recommendations']=[{
 'stock_code':'3706','stock_name':'神達','industry':'AI伺服器（tier_from_tracker 待審區；另登錄 電動車 tier_1 充電樁、綠能 tier_1 儲能）',
 'recommend_date':'2026-10-21','recommend_price':80.7,'target_price':87.16,'stop_loss_pct':-10,'stop_loss':72.63,'settlement_days':10,'position':'10%','score':88,
 'score_breakdown':{'時事':20,'法人':18,'產業':14,'技術':11,'價格':10,'動能-51.6%':10,'營收+88.6%回檔-2.8%':5,'EPS+20.3%':3,'外資持股比週減-0.18%':-3},
 'reason':'🛤️軌道A 法人TOP50 #16（avg_rank 17，10-20 買超 +2,734 張、外資 +2,587）；10 日累計 +19,218 張、近 5 天外資 +7,134；動能 -51.6% 佈局完成 +10；反轉 L0（10-19 曾 L4 -1,416 張，今日翻買）；9 月營收 YoY +88.6% 且 5 日回檔 -2.8%（+5）；EPS YoY +20.3%（+3）；外資持股比週減 -0.18%（-3）；月線 0.0%、季線 -1.3%；時事：AI伺服器與半導體🔴超強＋AI算力大單擴散，topic_tracker 標 神達↑；10-19 經濟部核准子公司神雲科技 126 億楊梅建廠＋企業級 AI 算力中心。⚠️風險：10 日中 3 天賣超、昨日才被法人賣；外資持股比週減；神達現增（台廠籌資擴產潮）稀釋；AI 泡沫階段「惡化」；本週 4 檔新推薦（1326/1802/1605/2887）全部 D0–D1 轉 L4，進場後若 T86 翻賣即出場；10/21 台指期結算日',
 'checks':{'法人現身門檻':'在 TOP50 買超 → 通過','準確率①催化對齊':'AI伺服器🔴 ✓','準確率②外資近5天':'+7,134 ✓','準確率③反轉':'L0 ✓','龍頭預警':'10-20 盤前 0 檔（美股 10-20 尚未收盤）','處置/注意':'不在官方清單','dossier':'stock_dossier_after.json：事件 0，mentions 18','pattern_today':'檔案 2026-10-05 已逾 3 天，跳過'}}]
t['tomorrow_observations']=[
 {'stock_code':'3026','stock_name':'禾伸堂','score_est':80,'note':'被動元件🟡；TOP50 #8 +3,104 張、外資持股比 +0.65%（+5）、EPS +178%（+5）；但官方注意股（近10日1次／30日2次）、6 日累積週轉率 43.8% 接近 50% 門檻、最快 3 個營業日處置，且今日 +8.0% 單日急漲 → 持有期內高機率進入處置（禁止進場），不推薦'},
 {'stock_code':'3231','stock_name':'緯創','note':'TOP1 +42,702 張（單日 ≥30K、真連買 1 天 → 過量買超 -5）；近 5 天外資 -5,467 → 準確率②不過；10-15 曾 -40,663'},
 {'stock_code':'6456','stock_name':'GIS-KY','score_est':72,'note':'動能 -43%、營收 +5、持股比 +5，但 EPS 連 4 季負成長 -5、無催化對齊 → 準確率①不過'},
 {'stock_code':'9904','stock_name':'寶成','score_est':67,'note':'真連買 10 天、累計 +77,627，但無催化對齊、產業邊緣，<70'},
 {'stock_code':'2542','stock_name':'興富發','score_est':57,'note':'真連買 10 天，但房市信貸緊縮🟢負向、月季雙線下'},
 {'stock_code':'2412 中華電／1216 統一／2801 彰銀／2105 正新／3045 台灣大／2324 仁寶／2353 宏碁／2356 英業達／2377 微星／2317 鴻海／2382 廣達','note':'動能 +67%～500%，一票否決或 -10 後 <70；不啟用覆寫'},
 {'stock_code':'1714 和桐／2484 希華／8112 至上／6285 啟碁','note':'近 5 天或 10 日累計為負'}]
t['after_market_notes']=['10-20 T86 於 16:17 公布（n=9），本盤後等到公布後才判定；institutional_top50.json 已改存 10-20 資料（盤前原為 10-19 複本，git 可回溯）','chip_analysis 以執行期包裝含今日（_after/_chip_incl_today.py）','revenue/foreign/price_position/eps 候選池結果存 _after/*_after.json，盤前四份 JSON 已還原']
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok', len(t['tomorrow_recommendations']), len(t['tomorrow_opening_exits']))

p=json.load(open('data/company_profiles.json',encoding='utf-8'))
p['3706']={'name':'神達','business':'神達控股；伺服器／儲存設備與工業電腦由子公司神雲科技主導（營收約八成，北美雲端客戶為主），另有神達數位車用電子','source':'nstock.tw／鉅亨網／Yahoo 奇摩股市 報導（2025–2026），營收占比為 2025 年初數字（WebSearch 2026-10-20）','updated':'2026-10-20'}
json.dump(p,open('data/company_profiles.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('profile ok')
