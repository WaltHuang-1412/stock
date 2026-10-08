import json
P='data/tracking/tracking_2026-10-08.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-10-08/_intraday_prices.json',encoding='utf-8'))
TS='2026-10-08 12:30'
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        if c=='2867':
            r['intraday_time']='序列停滯凍結（Yahoo 9.7 為 08-19 舊值，不採用）'; continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_day_change_pct']=p['chg']
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        r['intraday_dist_to_stop_pct']=round((p['price']/r['stop_loss']-1)*100,2)
        r['intraday_two_day_pct']=p['drop2d']
        r['intraday_high']=p['high']; r['intraday_low']=p['low']
        r['result']='holding'
hold=[('2330','台積電',None),('6770','力積電',73.26),('2337','旺宏',147.6),('2313','華通',235.98),('3090','日電貿',256.5),('1301','台塑',54.08),('4938','和碩',76.5)]
res=[]
for c,n,sl in hold:
    p=pr[c]['price']
    if sl is None: h='不適用（yaml 無 stop_loss 欄位）'
    elif p<sl: h='🛑 觸及停損（%s%%）'%round((p/sl-1)*100,2)
    else: h='✅ 未觸發（距停損 +%s%%）'%round((p/sl-1)*100,2)
    res.append({'stock_code':c,'stock_name':n,'price':p,'stop_loss':sl,'hit':h})
t['stop_loss_check_intraday_v8310']={'time':TS,'results':res,'new_triggers':0,'note':'6770/2337/3090 為重複輸出（流程已判出場、yaml 未更新）'}
t['two_day_drawdown_check_intraday']={'time':TS,'rule':'2 日累計跌幅 >-10%（10-06 收盤 → 12:30 報價）','triggers':0,'worst':{'2308':-3.66,'3035':-3.56,'2404':-2.62,'6770':-2.29}}
t['intraday_market']={'taiex':49410.76,'taiex_prev_close':49806.37,'taiex_change_pct':-0.79,'time':'~12:30','source':'Yahoo ^TWII curl'}
t['opening_exits_intraday_status']=[
 {'stock_code':'2330','stock_name':'台積電','source':'已決事項','base_price':2575.0,'intraday_price':2555.0,'intraday_return_pct':-0.78,'sell_ratio_intraday':'L2 3.6%（10-07 T86 -650）','execution_status':'已決事項開盤出場（v8.3.7 不重評）；入帳價依 v8.3.2 盤後填 10-08 收盤'},
 {'stock_code':'2344','stock_name':'華邦電','source':'已決事項','base_price':181.0,'intraday_price':177.0,'intraday_return_pct':-2.21,'sell_ratio_intraday':'10-07 T86 +12,918 翻買（揭露）','execution_status':'已決事項開盤出場（不重評）'},
 {'stock_code':'3711','stock_name':'日月光投控','source':'盤前新 L4','base_price':703.0,'intraday_price':731.0,'intraday_return_pct':3.98,'sell_ratio_intraday':'12.7% L4（-1,352）≥8%','execution_status':'開盤出場清單；盤中仍 L4 ≥8%，維持'},
 {'stock_code':'2308','stock_name':'台達電','source':'盤前新 L4','base_price':2005.0,'intraday_price':1975.0,'intraday_return_pct':-1.5,'sell_ratio_intraday':'20.2% L4（-1,981）≥8%','execution_status':'開盤出場清單；盤中仍 L4，維持'},
 {'stock_code':'6770','stock_name':'力積電','source':'持倉 yaml 2 張','intraday_price':72.6,'sell_ratio_intraday':'35.9% L4（-39,660）','execution_status':'鐵律① 72.6<73.26＋L4，維持開盤出場（yaml 未更新）'},
 {'stock_code':'2313','stock_name':'華通','source':'持倉 yaml 2 張','intraday_price':249.0,'sell_ratio_intraday':'16.9% L4（-7,433）≥8%','execution_status':'新 L4 開盤出場清單；價在停損上方'},
 {'stock_code':'4938','stock_name':'和碩','source':'持倉 yaml 1 張','intraday_price':89.6,'sell_ratio_intraday':'15.2% L4（-753）','execution_status':'10-05 已決 L4，yaml 未更新'},
 {'stock_code':'2337','stock_name':'旺宏','source':'持倉 yaml 1 張','intraday_price':117.0,'sell_ratio_intraday':'21.7% L4','execution_status':'鐵律① 117<147.6，重複輸出（yaml 未更新）'},
 {'stock_code':'3090','stock_name':'日電貿','source':'持倉 yaml 1 張','intraday_price':174.5,'sell_ratio_intraday':'22.3% L4','execution_status':'鐵律① 174.5<256.5，重複輸出（yaml 未更新）'}]
t['intraday_detector']={'t86_date':'20261007','candidates':626,'realtime_fetched':54,'strong':[
 {'stock_code':'6505','stock_name':'台塑化','score':65,'price':111.0,'chg':3.7,'vol_ratio':1.32},
 {'stock_code':'1735','stock_name':'日勝化','score':60,'price':23.3,'chg':0.7,'vol_ratio':2.21},
 {'stock_code':'8213','stock_name':'志超','score':60,'price':38.3,'chg':1.6,'vol_ratio':9.7},
 {'stock_code':'6136','stock_name':'富爾特','score':60,'price':26.4,'chg':4.4,'vol_ratio':3.07}],
 'medium':['1315 達新 50','7780 大研生醫 50','1524 耿鼎 50','6671 三能-KY 45']}
t['track_b_recommendations']=[]
t['track_b_observations']=[
 {'stock_code':'6505','stock_name':'台塑化','reason':'偵測器強訊號 65；12:14 111.0（+3.74% ≥3% 已反映）；盤前已因②外資近 5 天 -9.1K＋5 日 +10% 排除；2 日 +9.4%'},
 {'stock_code':'8213','stock_name':'志超','reason':'偵測器強訊號 60（量比 9.7x）；38.35（+1.72%）；5 日 +12.8% >10% 已大漲、2 日 +11.8%、近 6 日週轉接近注意門檻；營收 +35% 但回檔不足不加分；EPS +5% 不調整'},
 {'stock_code':'1735','stock_name':'日勝化','reason':'偵測器強訊號 60；23.3（+0.65%）；5 日 +15.6% 已大漲；真連買僅 1 天、10 日累計僅 +85 張'},
 {'stock_code':'6136','stock_name':'富爾特','reason':'偵測器強訊號 60；26.05（+3.17% ≥3% 已反映）；10 日累計 -66 張（負）、狀態不明'},
 {'stock_code':'1102','stock_name':'亞泥','reason':'盤前 80 分觀察：①催化對齊未過（無對應催化、營收連衰）；36.3（+1.11%）；仍維持觀察'},
 {'stock_code':'3042','stock_name':'晶技','reason':'盤前 66 分 <75（不在 TOP50、外資 10 日負）；213.0（+1.19%）；5 日 -2.3%、營收 +23.5% 不加分、EPS +52% +5、持股比 +0.22% 不調整、價位 13；近 6 日週轉 46.4% 接近 50% 注意門檻；仍 <75'}]
t['track_b_expansion_note']='盤中軌道B池＝偵測器強訊號 4 檔＋盤前觀察名單 2 檔（亞泥／晶技）；盤前 49 檔候選已全部評分且僅國喬過門檻。偵測器強訊號 4 檔皆被硬性排除（已反映／5 日>10%／累計負），觀察名單 2 檔 <75 或①未過。結論：今日無盤中新推薦（0 檔）。連假前最後交易日，不為湊數放寬。'
t['intraday_data_quality']={'t86':'10-07 T86 已可用（與盤前同一份）；10-08 T86 盤中不可得','price_source':'Yahoo chart regularMarketPrice（12:07~12:14）＋ get_close_series 10-07 收盤為前收','taiex':'Yahoo ^TWII curl','detector':'626 候選僅取得 54 檔即時資料（MIS 限流）','check_scripts':'revenue/foreign/eps/price_position 對 3 檔跑完，盤前四份 JSON 已自 _intra/bak 還原','2867':'序列停滯（末日 08-19），凍結判定','preflight':'L4 未出場 ERROR 為已知誤報（7 檔皆已在開盤出場清單）'}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('written')
