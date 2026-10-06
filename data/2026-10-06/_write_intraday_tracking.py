import json
P='data/tracking/tracking_2026-10-06.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-10-06/_intraday_prices.json',encoding='utf-8'))
TS='2026-10-06 12:10'
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        if c=='2867':
            r['intraday_time']='序列停滯凍結（Yahoo 報價 9.7 為 08-19 舊值）'; continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_day_change_pct']=p['chg']
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        r['intraday_dist_to_stop_pct']=round((p['price']/r['stop_loss']-1)*100,2)
        r['intraday_two_day_pct']=p['drop2d']
        r['intraday_high']=p['high']; r['intraday_low']=p['low']
        r['result']='holding'
# 待複核 12:30 複核①
ratio={'8150':5.5,'1326':6.5}
for r in t['pending_review_v833']:
    c=r['stock_code']
    r['review_1_result']=f"12:30 reversal_alert（10-05 T86，10-06 T86 未公布）賣超佔比 {ratio[c]}% ≥5% → 複核①成立"
    r['review_1_price']=pr[c]['price']
    if c=='8150':
        r['note_intraday']='12:10 報價 128.5 已越目標 124.5（高 130.0）；若收盤 ≥124.5 依結算規則 success 結案（D1，非 D0），結算優先於待複核'
# 開盤出場清單盤中狀態
exits=[('2609','陽明','追蹤 10-01',59.4),('2327','國巨*','追蹤 10-02',602.0),('6257','矽格','追蹤 10-01',254.0),('6770','力積電','持倉 yaml 2 張',81.4),('4938','和碩','持倉 yaml 1 張',85.0)]
ratio_x={'2609':'17.9%','2327':'15.8%','6257':'7.7%','6770':'14.5%','4938':'9.3%'}
t['opening_exits_intraday_status']=[{'stock_code':c,'stock_name':n,'source':s,'base_price':b,'intraday_price':pr[c]['price'],'intraday_time':TS,'intraday_day_change_pct':pr[c]['chg'],'intraday_return_pct':round((pr[c]['price']/b-1)*100,2),'sell_ratio_intraday':ratio_x[c]+'（L4，10-05 T86）','execution_status':'已決事項（10-05 盤後定案，v8.3.7 不重評）；入帳價依 v8.3.2 盤後填 10-06 收盤價'} for c,n,s,b in exits]
t['stop_loss_check_intraday_v8310']={'time':TS,'results':[
 {'stock_code':'2330','stock_name':'台積電','price':2580.0,'stop_loss':None,'hit':'不適用（yaml 無 stop_loss 欄位）'},
 {'stock_code':'6770','stock_name':'力積電','price':74.6,'low':74.2,'stop_loss':73.26,'hit':'✅ 未觸發（+1.83%；惟 L4 已決出場）'},
 {'stock_code':'2337','stock_name':'旺宏','price':120.0,'stop_loss':147.6,'hit':'🛑 觸及停損（-18.70%，重複輸出）'},
 {'stock_code':'2313','stock_name':'華通','price':252.5,'stop_loss':235.98,'hit':'✅ 未觸發（+7.00%）'},
 {'stock_code':'3090','stock_name':'日電貿','price':173.5,'stop_loss':256.5,'hit':'🛑 觸及停損（-32.36%，重複輸出）'},
 {'stock_code':'1301','stock_name':'台塑','price':68.8,'stop_loss':54.08,'hit':'✅ 未觸發（+27.22%）'},
 {'stock_code':'4938','stock_name':'和碩','price':89.9,'stop_loss':76.5,'hit':'✅ 未觸發（+17.52%；惟 L4 已決出場）'}],
 'new_triggers':0}
t['two_day_drawdown_check_intraday']={'time':TS,'rule':'2 日累計跌幅 >-10%（10-02 收盤 → 12:10 報價）','triggers':0,'worst':{'6770':-2.48,'2337':-1.64,'3035':-1.39,'2344':-0.56,'2609':-0.5,'2327':-0.32}}
t['intraday_market']={'taiex':49741.12,'taiex_prev_close':49712.04,'taiex_change_pct':0.06,'taiex_high':49968.92,'taiex_low':49479.69,'time':'12:19','source':'Yahoo ^TWII curl；chartPreviousClose 48,475.7 為舊值不採用'}
t['intraday_detector']={'t86_date':'20261005','candidates':475,'realtime_fetched':45,'note':'TWSE MIS 限流，475 檔僅取得 45 檔即時資料','strong':[{'stock_code':'4927','stock_name':'泰鼎-KY','score':75,'price':52.4,'chg':-0.9,'vol_ratio':4.9},{'stock_code':'3701','stock_name':'大眾控','score':70,'price':61.3,'chg':0.7,'vol_ratio':10.34},{'stock_code':'5222','stock_name':'全訊','score':65,'price':103.0,'chg':-2.4,'vol_ratio':2.1}],'medium':['6916 華凌 45','1708 東鹼 40','2476 鉅祥 40','5434 崇越 40']}
t['track_b_recommendations']=[]
t['track_b_observations']=[
 {'stock_code':'2412','stock_name':'中華電','reason':'盤前 100 分（📶訊號A L3 +15、動能 -34.5% +15）；12:10 144.0（-1.03%）；L0、10 日累計 +29K、真連買 4 天、近 5 天外資 +15K；營收 +25.6% 不加分／持股比 10-01 +0.04% 不調整／EPS +5.3% 不調整／價位 11；①催化對齊不成立（僅🟢太空AI/低軌衛星且標「→」）→ 觀察（10-05 盤中、10-06 盤前同判）'},
 {'stock_code':'3017','stock_name':'奇鋐','reason':'盤前 78 分；12:10 3,685（+2.79% <3%）；L0、動能 -151.8%（+15）、真連買 1 天、近 5 天三大法人 -199（外資 +7 ≥0 ②通過）；營收 +54.3% 不加分／持股比 09-30 +0.02%／EPS +5／價位 13；①催化僅🟢AI散熱未對齊 → 觀察；2 日 +7.12%'},
 {'stock_code':'4927','stock_name':'泰鼎-KY','reason':'偵測器強訊號 75（量比 4.9x）；12:10 51.6（-2.46%）；10-05 T86 +1,398 張、10 日累計 +5,315、真連買 2 天（偵測器稱 8 天）；動能 +500% >100% 一票否決（🟡ABF/PCB 非🔴，無覆寫）；2 日 +7.17%；營收 +35.5% 不加分／持股比 +0.11% 不調整／EPS 連 3 季負 -3；⚠️ 處置：6 日 +18.1%／30 日 +56.1% 接近注意門檻'},
 {'stock_code':'3701','stock_name':'大眾控','reason':'偵測器強訊號 70（量比 10.34x）；12:10 61.4（+0.82%）；10-05 T86 +526 張、10 日累計 +1,681、真連買 5 天；動能 +500% 否決；不在 TOP50；2 日 +10.83% 已大漲；EPS 連 3 季負 -5；⚠️ 處置風險高：6 日 +48.8%／30 日 +50.7%｜連續達標 3 天｜最快今日處置'},
 {'stock_code':'5222','stock_name':'全訊','reason':'偵測器強訊號 65（量比 2.1x）；12:10 103.0（-2.37%）；上櫃；10-05 +34 張、10 日累計 +347、真連買 4 天、動能 +10.3%（0）；無催化對應、知識庫未分類；營收 2026-09 YoY -69.8%／EPS -2（毛利率 QoQ -7.1pp）／價位 6（雙線下）；五維度 36＋偵測器 5＋EPS -2＝39 <75'},
 {'stock_code':'2301','stock_name':'光寶科','reason':'盤前 79 分（🔥覆寫候選）；12:10 297.0（-0.34%）；10-05 T86 +12,460 張買超中；動能 +210.9% >100% → 盤中篩選條件「動能 ≤100%」不成立（盤中無覆寫例外）；10 日買 4 賣 6；2 日 +5.51%'},
 {'stock_code':'2408','stock_name':'南亞科','reason':'盤前 62 分 <75；12:10 528.0（-0.38%）；動能 +60.4%（-10）、5 日 +5.37%（-10）；營收 +560.9% 不加分／EPS +5／持股比 +0.02%'},
 {'stock_code':'3717','stock_name':'聯嘉投控','reason':'盤前 67 分 <75；12:10 28.9（+4.14% ≥3% 已反映）；持股比 10-02 -0.65% -3；⚠️ 處置：連續達標 1 天、最快剩 2 天'},
 {'stock_code':'2104','stock_name':'國際中橡','reason':'盤前 63 分 <75（📶訊號A L1）；12:10 11.3（+0.44%）；無催化、未分類；EPS 連 2 季負 -3'},
 {'stock_code':'1708','stock_name':'東鹼','reason':'偵測器中訊號 40；盤前 60 分 <75；12:10 57.3（+0.88%）；持股比 10-02 +0.80% +5、EPS +5 已計；無催化、未分類；5 日 +8.6% -10'}]
t['track_b_expansion_note']='盤中 Track B 候選池 10 檔（偵測器強訊號 3＋盤前完整評分 ≥60 未推薦 7）；TOP50 買超其餘 40 檔與盤前同一份 10-05 T86，硬性排除條件（L3/L4／動能 >100%／10 日累計為負／5 日 >10%）盤中不變，逐檔見 intraday_analysis.md 第四節。結論：今日無盤中新推薦（0 檔）。'
t['intraday_data_quality']={'t86':'10-06 T86 12:30 未公布（最新快取 twse_t86_20261005.json，10-05 16:22 落檔）；所有法人數據與盤前同一份','price_source':'Yahoo chart regularMarketPrice（12:09~12:11）＋ get_close_series 10-05 收盤為前收','exit_signal_checker':'首跑 cp950 UnicodeEncodeError 全部失敗 → 以 PYTHONIOENCODING=utf-8 重跑 10 檔逐檔 --cost 成功','check_scripts':'revenue/foreign/eps/price_position 對 10 檔 Track B 池分批跑，輸出另存 _intraB/*_intraday.json，盤前四份 JSON 已自 _intraB/pre 還原','detector':'475 檔候選僅取得 45 檔即時資料（MIS 限流）'}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok',len(t['recommendations']),len(t['track_b_observations']))
