import json
P='data/tracking/tracking_2026-10-02.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-10-02/_intraday_prices.json',encoding='utf-8'))
pb=json.load(open('data/2026-10-02/_intraday_prices_top50.json',encoding='utf-8'))
pb.update(pr)
TS='2026-10-02 12:10'
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        if c=='2867':
            r['intraday_time']='序列停滯凍結（Yahoo 報價 9.7 為 08-19 舊值）'; continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        r['intraday_day_change_pct']=p['chg']
        r['intraday_two_day_pct']=p['drop2d']
        r['intraday_dist_to_stop_pct']=round((p['price']/r['stop_loss']-1)*100,2)
        r['intraday_high']=p['high']; r['intraday_low']=p['low']
ratio={'2395':'L0（10-01 T86 +490 張，翻買）','1303':'14.8%（L4）','1301':'21.2%（L4）','1326':'47.6%（L4）','6505':'25.5%（L4）'}
for r in t['opening_exits_today']:
    c=r['stock_code']; p=pr[c]
    r['intraday_price']=p['price']; r['intraday_time']=TS
    r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
    r['intraday_day_change_pct']=p['chg']
    r['sell_ratio_intraday']=ratio[c]
    r['execution_status']='已決事項（10-01 盤後定案，v8.3.7 不重評）；入帳價依 v8.3.2 盤後填 10-02 收盤價'
t['track_b_recommendations']=[]
obs=[
 ('2404','漢唐','🔎 首要觀察｜盤前 75 分（🔴AI 建廠點名↑、🔥超強催化覆寫〔動能 +109.2%〕）；今日 -2.68%；L0（10-01 T86 +441 張）、10 日累計 +3,404、真連買 2 天、近 5 天外資 +419；營收 2026-08 YoY +59.1% 不加分／持股比 09-30 -0.03% 不調整／EPS Q2 +5；準確率三項與 ≥75 分皆過，惟 Step 3 法人篩選未過（10-01 買超僅 441 張 <5K、不在 TOP50，無 avg_rank）→ 不列盤中新推薦'),
 ('3702','大聯大','盤前 73 分 <75；今日 +0.84%；avg_rank 14.0、10-01 T86 +5,768 張（買超中）、真連買 1 天、近 5 天外資 +8,165；營收 +80.5% 不加分／持股比 +0.29% 不調整／EPS +5；門檻全過但分數未達盤中 75 分'),
 ('6196','帆宣','盤前 70 分 <75；今日 +1.16%；🔥覆寫（動能 +500%）；不在 TOP50'),
 ('3094','聯傑','偵測器強訊號 75（量比 2.89x）；今日 +6.20% ≥3% 已反映；反轉狀態不明、近 5 天外資 -1,947 → ②③未過；5 日 +32.0% 已大漲不評分；知識庫未分類、提及 0 → ①未過；持股比週減 -1.25%（-3）；處置預警：6 日 +36.5%／30 日 +98.1%／週轉 35.5%｜接近注意門檻'),
 ('6438','迅得','偵測器強訊號 60（量比 2.79x）；今日 +2.43%；L0（10-01 T86 +144 張）、10 日累計 +1,573、真連買 4 天（偵測器稱 9 天）、近 5 天外資 +1,215；動能 +261.3% >100% 且對應催化為🟡（企業財報／ABF-PCB tier_from_tracker）非🔴 → 無覆寫，一票否決；5 日 +10.1% >10% 已大漲不評分；不在 TOP50；營收 +15.5% 不加分／持股比 +0.11% 不調整／EPS +17.4% 不調整；⚠️ 擬發 5 億可轉債'),
 ('6934','心誠鎂','偵測器中訊號 55；今日 -1.46%；觀察，未評分'),
 ('2363','矽統','偵測器中訊號 50；今日 +3.30% 已反映；盤前 68 分、①②未過'),
 ('2034','允強','偵測器中訊號 40；今日 +2.54%；觀察，未評分'),
 ('2303','聯電','盤前 118 分（全池最高）；今日 0.00%；②外資近 5 天 -34K 為負 → 未過'),
 ('2317','鴻海','盤前 113 分；今日 -1.18%；③反轉狀態不明＋②外資近 5 天 -5,198 → 未過'),
 ('2408','南亞科','盤前 89 分；今日 +1.54%；③反轉狀態不明 → 未過'),
 ('3045','台灣大','盤前 94 分；今日 0.00%；①催化對齊未過'),
 ('2884','玉山金','盤前 92 分；今日 -0.55%；①②未過'),
 ('2353','宏碁','盤前 90 分；今日 -1.26%；①③未過'),
 ('2892','第一金','盤前 89 分；今日 -0.52%；①②未過'),
 ('2886','兆豐金','盤前 83 分；今日 -0.61%；①未過'),
 ('2481','強茂','盤前 87 分；今日 -1.97%；②③未過'),
 ('3706','神達','盤前 79 分；今日 -0.85%；③反轉狀態不明'),
 ('2377','微星','盤前 75 分；今日 +0.66%；①未過'),
 ('2634','漢翔','盤前 76 分；今日 +2.02%；①③未過'),
 ('3042','晶技','盤前 95 分；今日 +3.89% 已反映；5 日已大漲、②未過'),
 ('8046','南電','盤前 88 分；今日 +3.17% 已反映；動能 +456% 否決、5 日已大漲'),
 ('3189','景碩','盤前 78 分；今日 +3.47% 已反映；5 日已大漲'),
 ('2492','華新科','盤前 69 分；今日 +9.88% 已反映；動能 +490% 否決'),
 ('2340','台亞','今日 +3.99% 已反映；動能否決、5 日已大漲'),
 ('1709','和益','今日 +9.96% 已反映；③不明、5 日已大漲'),
 ('1727','中華化','今日 +9.82% 已反映；①②③未過'),
 ('6213','聯茂','今日 +7.17% 已反映；動能否決、5 日已大漲'),
 ('6672','騰輝電子-KY','今日 +5.18% 已反映；動能否決、5 日已大漲'),
 ('3311','閎暉','今日 +9.97% 已反映；動能否決、5 日已大漲'),
 ('2484','希華','今日 +2.36%；動能 +380% 否決、5 日已大漲、①未過'),
 ('2347','聯強','盤前 70 分；今日 +1.57%；動能 +500% 無覆寫'),
 ('3026','禾伸堂','盤前 70 分；今日 +0.70%；③不明、動能否決'),
 ('3167','大量','盤前 71 分；今日 +0.51%；動能否決、5 日已大漲、①未過'),
 ('2030','彰源','🔴🔴 TWSE 處置股（10/02~10/08）排除；今日 +1.73%'),
 ('6168','宏齊','🔴🔴 TWSE 處置股（09/24~10/02）排除；今日 -1.28%'),
 ('3016','嘉晶','🔴🔴 TWSE 處置股（10/01~10/12）排除；今日 +6.25%'),
]
t['track_b_observations']=[]
for a,b,n in obs:
    v=pb.get(a) or {}
    t['track_b_observations'].append({'stock_code':a,'stock_name':b,'intraday_price':v.get('price'),'intraday_change_pct':v.get('chg'),'note':n})
t['intraday']={
 'time':'2026-10-02 12:30','taiex':48434.56,'taiex_change_pct':round((48434.56/48353.49-1)*100,2),'taiex_base':'10-01 收盤 48,353.49（Yahoo ^TWII curl，12:11 報價；chartPreviousClose 48,024.6 為 09-24 舊值，不採用）',
 'preflight':{'warnings':1,'errors':1,'l4_error_verdict':'28 檔逐檔對照：1303 南亞／1301 台塑／1326 台化／6505 台塑化 為已決事項今日開盤出場；6770 力積電／2337 旺宏／2313 華通 為 my_holdings.yaml 仍列但流程紀錄已出場（yaml 未更新，若實際仍持有鐵律適用）；其餘 21 檔（1718/1314/1312/2618/2610/2449/2356/2368/2367/2382/6669/2308/3583/2383/2603/2891/2882/2890/2883/3443/3661）為盤前候選池排除股，非 holding → 追蹤部位無漏出場'},
 'exit_rules':{'stop_loss_hits':0,'two_day_drawdown_hits':0,'reversal_l3_l4_new':0,'pending_review':0,
   'closest_to_stop':'5876 上海商銀 48.7，距停損 44.82 還有 +8.66%（今日到期）；3231 緯創 186.5，距停損 171.45 還有 +8.78%','worst_two_day':'2395 研華 -1.24%（09-30 收 726.0 → 717.0）'},
 'opening_exits_recheck':'2395 研華 L0（10-01 T86 +490 張）／1303 南亞 14.8%／1301 台塑 21.2%／1326 台化 47.6%／6505 台塑化 25.5%（10-01 T86、avg_5day_volume 分母、12:3x 取樣）；已決事項不重評',
 'reversal_scan':'24 檔（軌道A 19＋yaml 持倉 5）：L4 7 檔全為盤前已列者（塑化四檔已決出場；6770 14.2%／2337 6.0%／2313 12.0% 為 yaml 已出場部位）；L2 1 檔 6257 矽格（-293 張＝2.3%，同盤前）；買超中 5、L0 9、狀態不明 2（2867 凍結、4938 和碩）',
 'd10_today':'5876 上海商銀 48.7（收盤 >49.8 才 success）／2412 中華電 145.5（>143.5）／2395 研華 717.0（已決出場）→ 盤後以收盤價結算',
 'target_touched_d0':'8150 南茂 127.0（漲停，≥目標 124.5）；D0 不結算，D1 起由 settlement_checker 判定',
 'frozen':['2867 三商壽（序列停滯，末日 2026-08-19）'],
 'holdings_stop_loss_recheck':'0 筆新觸發；6770 力積電 77.0 > 73.26（惟 L4 14.2%）；2337 旺宏 122.0<147.6、2313 華通 227.0<235.98、3090 日電貿 173.5<256.5 皆為流程紀錄已出場部位（yaml 未更新）重複輸出；1301 台塑 68.6>54.08（已決事項出場）、4938 和碩 89.5>76.5 未觸發；2330 無停損欄',
 'prior_decisions_status':'已決事項 5 筆（2395/1303/1301/1326/6505）今日開盤出場，原樣執行不重評',
 'detector':{'scanned':469,'realtime_fetched':58,'coverage_pct':12.4,'strong':['3094 聯傑 75','6438 迅得 60'],'moderate':['6934 心誠鎂 55','2363 矽統 50','2034 允強 40']},
 'track_b_result':'今日無盤中新推薦（0 檔）；偵測器強訊號 3094 聯傑（今日 +6.2% 已反映、5 日已大漲、②③未過）、6438 迅得（動能 +261% 否決、5 日 +10.1% 已大漲）皆未過；2404 漢唐 75 分門檻全過但 Step 3 法人篩選未過（列首要觀察）；3702 大聯大 73 分 <75',
 'dossier_intraday':'無盤中新推薦 → 依 Step 3.5 免跑',
 'tier_from_tracker_added':0,
 'data_source_notes':['現價取 Yahoo chart meta.regularMarketPrice（12:10~12:17，約延遲 20 分鐘）','前收取 get_close_series 10-01 收盤','intraday_institutional_detector 469 檔僅取得 58 檔即時行情（TWSE MIS 限流），覆蓋率 12.4%','盤中 check_* 腳本 JSON 另存 _intraB/*_intraday.json，盤前版本已還原','法人數據為 10-01 T86（與盤前同一份），10-02 T86 盤後才公布','exit_signal_checker 逐檔帶各自推薦價執行']
}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in t['opening_exits_today']: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['intraday_price'],r['intraday_return_pct'],r['intraday_day_change_pct'])
for r in t['recommendations']+t['carry_over_recommendations']: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['target_price'],r['stop_loss'],r.get('intraday_price'),r.get('intraday_day_change_pct'),r.get('intraday_return_pct'),r.get('intraday_dist_to_stop_pct'),r.get('intraday_two_day_pct'),r.get('holding_days'),r.get('intraday_high'))
