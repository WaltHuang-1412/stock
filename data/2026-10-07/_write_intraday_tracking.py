import json
P='data/tracking/tracking_2026-10-07.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-10-07/_intraday_prices.json',encoding='utf-8'))
TS='2026-10-07 12:11'
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        if c=='2867':
            r['intraday_time']='序列停滯凍結（Yahoo 報價 9.7 為 08-19 舊值，不採用）'; continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_day_change_pct']=p['chg']
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        r['intraday_dist_to_stop_pct']=round((p['price']/r['stop_loss']-1)*100,2)
        r['intraday_two_day_pct']=p['drop2d']
        r['intraday_high']=p['high']; r['intraday_low']=p['low']
        r['result']='holding'
ratio={'2330':6.1,'2344':5.2}
for r in t['pending_review_v833']:
    c=r['stock_code']
    r['review_1_result']=f"12:30 reversal_alert（仍為 10-06 T86，10-07 T86 未公布）賣超佔比 {ratio[c]}% ≥5% → 複核①成立（盤前 {r['sell_ratio_pct']}%，分母 avg_5day_volume 滾動所致，賣超張數未變）"
    r['review_1_price']=pr[c]['price']
    r['review_1_time']=TS
t['opening_exits_intraday_status']=[
 {'stock_code':'3231','stock_name':'緯創','source':'追蹤 10-05（已決事項，10-06 盤後定案）','base_price':189.5,'intraday_price':186.0,'intraday_time':TS,'intraday_day_change_pct':-1.85,'intraday_return_pct':round((186.0/189.5-1)*100,2),'sell_ratio_intraday':'13.1%（L4，10-06 T86 -4,981）','execution_status':'已決事項開盤出場（v8.3.7 不重評）；入帳價依 v8.3.2 盤後填 10-07 收盤價'},
 {'stock_code':'2337','stock_name':'旺宏','source':'持倉 yaml 1 張','base_price':164.0,'intraday_price':119.5,'intraday_time':TS,'intraday_day_change_pct':0.0,'intraday_return_pct':-27.13,'execution_status':'鐵律① 119.5<147.6 觸及停損（重複輸出：流程紀錄已出場、yaml 未更新）'},
 {'stock_code':'3090','stock_name':'日電貿','source':'持倉 yaml 1 張','base_price':285.0,'intraday_price':175.5,'intraday_time':TS,'intraday_day_change_pct':1.45,'intraday_return_pct':-38.42,'execution_status':'鐵律① 175.5<256.5 觸及停損（重複輸出：yaml 未更新）'},
 {'stock_code':'6770','stock_name':'力積電','source':'持倉 yaml 2 張','base_price':81.4,'intraday_price':73.9,'intraday_time':TS,'intraday_day_change_pct':-0.54,'intraday_return_pct':-9.21,'sell_ratio_intraday':'13.9%（L4，10-06 T86 -16,606）','execution_status':'10-06 已決 L4 出場（yaml 未更新）；今日仍 L4；盤中低 73.1 已跌破停損 73.26（報價 73.9 未破）'},
 {'stock_code':'4938','stock_name':'和碩','source':'持倉 yaml 1 張','base_price':85.0,'intraday_price':89.8,'intraday_time':TS,'intraday_day_change_pct':-0.22,'intraday_return_pct':5.65,'execution_status':'10-06 已決 L4 出場（yaml 未更新）；10-06 T86 +958 狀態不明、累計 -5,786'}]
t['stop_loss_check_intraday_v8310']={'time':TS,'results':[
 {'stock_code':'2330','stock_name':'台積電','price':2580.0,'stop_loss':None,'hit':'不適用（yaml 無 stop_loss 欄位）'},
 {'stock_code':'6770','stock_name':'力積電','price':73.9,'low':73.1,'stop_loss':73.26,'hit':'✅ 報價未觸發（+0.87%）；盤中低點 73.1 曾跌破；L4 已決出場'},
 {'stock_code':'2337','stock_name':'旺宏','price':119.5,'stop_loss':147.6,'hit':'🛑 觸及停損（-19.04%，重複輸出）'},
 {'stock_code':'2313','stock_name':'華通','price':247.5,'stop_loss':235.98,'hit':'✅ 未觸發（+4.88%）'},
 {'stock_code':'3090','stock_name':'日電貿','price':175.5,'stop_loss':256.5,'hit':'🛑 觸及停損（-31.58%，重複輸出）'},
 {'stock_code':'1301','stock_name':'台塑','price':75.4,'stop_loss':54.08,'hit':'✅ 未觸發（+39.42%）；持倉損益 +25.5% 已超過 yaml strategy take_profit_percent 20%'},
 {'stock_code':'4938','stock_name':'和碩','price':89.8,'stop_loss':76.5,'hit':'✅ 未觸發（+17.39%；L4 已決出場）'}],
 'new_triggers':0}
t['two_day_drawdown_check_intraday']={'time':TS,'rule':'2 日累計跌幅 >-10%（10-05 收盤 → 12:11 報價）','triggers':0,'worst':{'3035':-2.78,'6770':-2.51,'3231':-1.85,'2337':-1.65,'3711':-1.48}}
t['intraday_market']={'taiex':49857.39,'taiex_prev_close':49822.55,'taiex_change_pct':0.07,'time':'12:16','source':'Yahoo ^TWII curl（chartPreviousClose 48,353.5 為舊值不採用；前收取 10-06 日K 49,822.55）'}
t['intraday_detector']={'t86_date':'20261006','candidates':532,'realtime_fetched':57,'note':'TWSE MIS 限流，532 檔僅取得 57 檔即時資料','strong':[
 {'stock_code':'2313','stock_name':'華通','score':80,'price':247.5,'chg':-1.8,'vol_ratio':1.64,'note':'持倉（yaml 2 張），非軌道B新候選'},
 {'stock_code':'4927','stock_name':'泰鼎-KY','score':75,'price':54.7,'chg':4.6,'vol_ratio':4.26},
 {'stock_code':'1605','stock_name':'華新','score':75,'price':40.1,'chg':3.5,'vol_ratio':2.01},
 {'stock_code':'1709','stock_name':'和益','score':65,'price':60.7,'chg':-4.1,'vol_ratio':1.32},
 {'stock_code':'1449','stock_name':'佳和','score':60,'price':13.1,'chg':4.8,'vol_ratio':3.84},
 {'stock_code':'9919','stock_name':'康那香','score':60,'price':14.6,'chg':3.6,'vol_ratio':7.2},
 {'stock_code':'2402','stock_name':'毅嘉','score':60,'price':61.5,'chg':3.9,'vol_ratio':2.94}],
 'medium':['2467 志聖 55','1304 台聚 50','6504 南六 50','6936 永鴻生技 40','2369 菱生 40','8926 台汽電 40']}
t['track_b_recommendations']=[]
t['track_b_observations']=[
 {'stock_code':'2412','stock_name':'中華電','score':78,'reason':'五維度 68（時事 13／法人 21／產業 13／技術 10／價位 11）＋📶訊號A L2 +10；動能 +35% 0、營收 +25.6% 不加分、持股比 10-01 +0.04% 不調整、EPS +5.3% 不調整、5 日 +1.04%；12:11 145.0（-0.34%）；買超中 +3,063、真連買 5、外資近 5 天 +18K；①催化對齊不成立（僅🟢低軌衛星）→ 觀察（10-05 盤中／10-06 盤前／10-07 盤前同判）'},
 {'stock_code':'2892','stock_name':'第一金','score':79,'reason':'五維度 59（時事 10／法人 17／產業 13／技術 11／價位 8）＋📶訊號A L2 +10＋動能 -18.2% +10；營收 +6.3% 不調整、持股比 -0.01% 不調整、⚠️ EPS 停 2025Q4（金控半年報 8/31 已過）視為 0、5 日 -0.13%；12:11 38.85（+0.78%）；買超中 +3,718、真連買 1、外資近 5 天 +984；①催化對齊不成立 → 觀察'},
 {'stock_code':'4906','stock_name':'正文','score':67,'reason':'五維度 60（時事 13／法人 16／產業 7 未分類／技術 11／價位 13）＋動能 -82.7% +15、持股比 10-05 -0.10% -3、EPS +90% +5、5 日 +6.97% -10；12:11 42.15（-1.98%）；買超中 +3,771、真連買 1、外資近 5 天 +333；①催化對齊不成立（🟢衛星）；67 <75'},
 {'stock_code':'2891','stock_name':'中信金','reason':'avg_rank 7、📶訊號A L2、真連買 3；②外資近 5 天 -13K 未過；12:11 68.7（+0.44%）'},
 {'stock_code':'2605','stock_name':'新興','reason':'動能 +202% >100% 否決（無🔴覆寫）、10 日累計 -2,439 狀態不明；持股比 +1.71% +5、EPS +5 不足以翻案；12:11 36.35（-1.62%）'},
 {'stock_code':'6239','stock_name':'力成','reason':'5 日 +10.5% 已大漲、累計 -2,691 狀態不明、②外資近 5 天 -1,698；12:11 305.0（-1.77%）'},
 {'stock_code':'2885','stock_name':'元大金','reason':'累計 -5,763 狀態不明、②外資近 5 天 -11K；12:11 69.8（+0.72%）'},
 {'stock_code':'8150','stock_name':'南茂','reason':'5 日 +22% 已大漲、⚠️ 處置預警 連 5 天最快剩 0 天（近 6 日週轉率 64.3%）；10-06 已以 +10.39% 結算 success；12:11 127.5（0.00%）'},
 {'stock_code':'2886','stock_name':'兆豐金','reason':'動能 +196% >100% 否決（無🔴覆寫）；12:11 49.65（+0.71%）'},
 {'stock_code':'6257','stock_name':'矽格','reason':'5 日 +20.9% 已大漲、⚠️ 接近注意門檻；10-06 已以 +12.60% 結算 success；12:11 277.5（-2.97%）'},
 {'stock_code':'2883','stock_name':'凱基金','reason':'動能 +500%（現增）否決、②外資近 5 天 -7,072、持股比 -0.10% -3；12:11 38.4（+1.99%）'},
 {'stock_code':'2884','stock_name':'玉山金','reason':'②外資近 5 天 -6,695 未過（投信 +16K 撐盤）；12:11 45.75（+0.66%）'},
 {'stock_code':'2890','stock_name':'永豐金','reason':'今日除息、動能 +336% 否決、②外資近 5 天 -11K；12:11 44.85（-0.47%）'},
 {'stock_code':'2887','stock_name':'台新新光金','reason':'累計 -44K、②外資近 5 天 -25K；12:11 42.15（+1.69%）'},
 {'stock_code':'2880','stock_name':'華南金','reason':'動能 +247% 否決、②外資近 5 天 -5,246；12:11 46.75（+2.86%）'},
 {'stock_code':'6213','stock_name':'聯茂','reason':'⚠️ 處置風險高：連續達標 4 天最快明日處置（近 6 日 +29%／90 日 +198%）、5 日 +26.9% 已大漲、持股比 -0.25% -3；12:11 801.0（+1.78%）'},
 {'stock_code':'2382','stock_name':'廣達','reason':'累計 -13K 狀態不明、②外資近 5 天 -12K、持股比 -0.10% -3；12:11 334.5（+0.30%）'},
 {'stock_code':'1504','stock_name':'東元','reason':'動能 +234% >100% 否決（對應主題 AI建廠潮外溢／AI Factory 電力皆為🟢，無🔴覆寫）；L0 累計 +3,960、真連買 5；12:11 72.9（+2.53%）'},
 {'stock_code':'2368','stock_name':'金像電','reason':'5 日 +12.5% 已大漲、累計 -7,080、②外資近 5 天 -5,749；12:11 1,255（-0.40%）'},
 {'stock_code':'1709','stock_name':'和益','reason':'偵測器強訊號 65；不在 10-06 TOP50、10 日累計 -1,035 狀態不明、動能 +206% 否決、⚠️ 接近注意門檻（連 6 天，最快剩 2 天）、持股比 -0.25% -3；12:11 60.5（-4.42%）'},
 {'stock_code':'4927','stock_name':'泰鼎-KY','reason':'偵測器強訊號 75（量比 4.26x）；12:11 54.8（+4.78% ≥3% 已反映）；5 日 +19.5% 已大漲、⚠️ 處置預警 連 1 天'},
 {'stock_code':'1605','stock_name':'華新','reason':'偵測器強訊號 75；12:11 40.1（+3.48% ≥3% 已反映）；盤前列動能 >100% 無覆寫'},
 {'stock_code':'1449','stock_name':'佳和','reason':'偵測器強訊號 60；12:11 13.0（+4.42% ≥3% 已反映）；不在 TOP50'},
 {'stock_code':'9919','stock_name':'康那香','reason':'偵測器強訊號 60；12:11 14.6（+3.91% ≥3% 已反映）；不在 TOP50'},
 {'stock_code':'2402','stock_name':'毅嘉','reason':'偵測器強訊號 60；12:11 61.6（+4.05% ≥3% 已反映）；不在 TOP50'}]
t['track_b_expansion_note']='盤中軌道B候選池 31 檔（10-06 TOP50 買超 total ≥5K 或 avg_rank ≤30 且不在軌道A／持倉 25 檔＋偵測器強訊號 6 檔）；今日漲幅 ≥3% 已反映剔除 11 檔，餘 20 檔跑 chip_analysis／reversal_alert／營收／持股比／價位／EPS。通過硬性排除（L3-L4／動能>100%／累計為負／5 日>10%／處置）且②外資近 5 天 ≥0 者僅 2412 中華電／2892 第一金／4906 正文，三檔皆①催化未對齊（非🔴鏈）。結論：今日無盤中新推薦（0 檔）。'
t['intraday_data_quality']={'t86':'10-07 T86 12:30 未公布（最新快取 twse_t86_20261006.json）；所有法人數據與盤前同一份 10-06 T86','price_source':'Yahoo chart regularMarketPrice（12:07~12:11）＋ get_close_series 10-06 收盤為前收','taiex':'Yahoo ^TWII curl 49,857.39（12:16）；_fetch_chart 對指數回 None','exit_signal_checker':'PYTHONIOENCODING=utf-8 逐檔 --cost 跑 17 檔成功','check_scripts':'revenue/foreign/eps/price_position 對 20 檔軌道B池分批跑，輸出另存 _intraB/*.json，盤前四份 JSON 已自 _intraB/bak 還原','detector':'532 檔候選僅取得 57 檔即時資料（MIS 限流）','disposition':'fetch_twse_lists 首呼叫即回 11 檔處置（與盤前一致），注意股 0；reversal_alert stdout 本次未印處置區塊，改以 fetch_twse_lists 直取'}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok',len(t['recommendations']),len(t['track_b_observations']))
