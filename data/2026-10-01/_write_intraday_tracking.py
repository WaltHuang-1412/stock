import json
P='data/tracking/tracking_2026-10-01.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-10-01/_intraday_prices.json',encoding='utf-8'))
pb=json.load(open('data/2026-10-01/_intraday_prices_top50.json',encoding='utf-8'))
pb.update(pr)
TS='2026-10-01 12:10'
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
ratio={'2886':'6.1%（L4）','3702':'4.0%（L2）','2376':'12.3%（L4）'}
for r in t['opening_exits_today']:
    c=r['stock_code']; p=pr[c]
    r['intraday_price']=p['price']; r['intraday_time']=TS
    r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
    r['intraday_day_change_pct']=p['chg']
    r['sell_ratio_intraday']=ratio[c]
    r['execution_status']='已決事項（09-30 盤後定案，v8.3.7 不重評）；入帳價依 v8.3.2 盤後填 10-01 收盤價'
for r in t['pending_review_v833']:
    r['review_1_result']='7.5%（reversal_alert 12:3x 取樣，avg_5day_volume 分母；賣超 -178 張未變）≥5% → 第一次複核成立'
    r['review_1_level']='L4'
    r['status_after_review_1']='待盤後第二次複核；兩次皆 ≥5% 才於 10-02 開盤出場'
t['track_b_recommendations']=[]
obs=[
 ('2371','大同','🔎 首要觀察｜偵測器強訊號 95（量比 2.57x、今日 +0.16%）；盤前 85 分＋偵測器 +5＝90；L0（買超中 +7,596）、10 日累計 +19K、真連買 1 天、近 5 天外資 +2,689、動能 -79.6%；營收 2026-08 YoY -11.5% 不調整／持股比 09-29 -0.06% 不調整／EPS Q2 +5；惟對應催化「AI Factory 電力架構」在 topic_tracker 為「觀察中」（非🔴／🟡）→ 準確率①催化對齊未過（同盤前判定），不列盤中新推薦'),
 ('3481','群創','偵測器強訊號 90；今日 -4.57%、量比 1.93x（放量下跌）；動能 +249.5% >100% 無覆寫、①未過、盤前 67 分 → 不推薦'),
 ('3518','柏騰','偵測器強訊號 75；今日 -1.58%；5 日 +25.6% >10% 已大漲不評分；動能 +370.6%；營收連 7 個月衰退 -5、EPS -5、持股比 +5；知識庫未分類、提及 0；處置預警：連續達標 2 天最快明日處置'),
 ('7736','虎山','偵測器強訊號 70；今日 +0.44%；10 日累計僅 +12 張、近 5 天外資 -4 → ②未過；不在 TOP50 × 乖離 -0.3%；營收連 3 個月衰退 -5、EPS +5；未分類、提及 0 → ①未過；五維度 36＋營收 -5＋EPS +5＋偵測器 +5＝41 <75'),
 ('2034','允強','偵測器強訊號 65；今日 -5.04%、量比 2.48x → 型態轉弱（跌幅 ≤-5% 且量比 ≥2x，非「未反映」）；5 日 +7.3%；未分類、提及 0 → ①未過'),
 ('6861','睿生光電','偵測器強訊號 65；今日 -5.90%、量比 2.89x → 型態轉弱；反轉狀態不明（10 日累計 -1,232）、近 5 天外資 -245 → ②③未過；5 日 +11.2% 已大漲；處置預警 🟡 連 7 天、最快剩 4 個交易日'),
 ('2231','為升','偵測器中訊號 55；觀察，未評分'),('6142','友勁','偵測器中訊號 55；觀察，未評分'),
 ('2347','聯強','偵測器中訊號 50；觀察，未評分'),('6944','兆聯實業','偵測器中訊號 40；今日 +3.1% 已反映'),
 ('2408','南亞科','盤前 113 分；今日 0.00%；🔔美光今日財報 → 當日不開新倉，10/02 再評估'),
 ('6770','力積電','盤前 101 分；今日 -1.20%；🔔美光今日財報 → 不開新倉'),
 ('2337','旺宏','盤前 97 分；今日 -0.82%；🔔美光今日財報 → 不開新倉'),
 ('2344','華邦電','盤前 89 分；今日 +0.28%；🔔美光今日財報 → 不開新倉'),
 ('2303','聯電','盤前 106 分；今日 +3.24% ≥3% 已反映；②外資近 5 天 -8,338 未過'),
 ('6239','力成','盤前 91 分；今日 +0.52%；②外資近 5 天 -1,676 未過'),
 ('8150','南茂','盤前 93 分；今日 0.00%；5 日 +11.2% 已大漲；處置倒數最快剩 2 天'),
 ('2892','第一金','盤前 93 分；今日 -0.65%；①未過（金融未點名）'),
 ('1314','中石化','盤前 86 分；今日 -1.11%；①未過、營收連衰 -5'),
 ('1718','中纖','盤前 76 分；今日 -2.30%；①未過'),
 ('6116','彩晶','盤前 87 分；今日 -4.59%；5 日 +10.5% 已大漲、①②未過'),
 ('2409','友達','盤前 83 分；今日 -0.52%；5 日 +15.6% 已大漲、①未過；處置倒數'),
 ('1709','和益','今日 +9.92% 已反映；反轉狀態不明、5 日已大漲'),
 ('2340','台亞','今日 +8.21% 已反映；動能否決'),
 ('2317','鴻海','盤前 65 分 <70；今日 +0.80%；②③未過'),
 ('2354','鴻準','盤前 71 分；今日 +0.15%；動能 +500% 無覆寫、①未過'),
 ('2002','中鋼','盤前 63 分；今日 -1.56%；動能 +166% 否決'),
 ('1605','華新','盤前 67 分；今日 -0.65%；動能 +500% 否決'),
 ('1101','台泥','盤前 50 分；今日 -2.47%；動能否決、cold -5'),
 ('2618','長榮航','盤前 66 分；今日 -1.05%；動能否決（中東鏈利空方向）'),
 ('2610','華航','盤前 61 分；今日 -0.98%；動能否決'),
 ('3576','聯合再生','今日 -5.33%；動能否決、5 日已大漲'),
 ('2887','台新新光金','盤前 76 分；今日 -2.74%；②③未過'),
 ('1802','台玻','盤前 74 分；今日 -2.17%；②③未過'),
 ('2323','中環','今日 -9.98%（Yahoo 時間戳 13:30 異常，價格未確認）；動能否決'),
]
t['track_b_observations']=[]
for a,b,n in obs:
    v=pb.get(a) or {}
    t['track_b_observations'].append({'stock_code':a,'stock_name':b,'intraday_price':v.get('price'),'intraday_change_pct':v.get('chg'),'note':n})
t['intraday']={
 'time':'2026-10-01 12:30','taiex':48119.96,'taiex_change_pct':round((48119.96/47940.13-1)*100,2),'taiex_base':'09-30 收盤 47,940.13（Yahoo ^TWII curl，12:11 報價；chartPreviousClose 48,157.29 為 09-23 舊值，不採用）',
 'preflight':{'warnings':1,'errors':1,'l4_error_verdict':'13 檔逐檔對照：2886 兆豐金／2376 技嘉 為已決事項今日開盤出場；2395 研華 為 v8.3.3 待複核（第一次 7.5% 成立）；4938 和碩 為 my_holdings.yaml 仍列 1 張但流程紀錄 09-21 已出場（yaml 未更新，若實際仍持有 L4 41.7% 適用）；其餘 9 檔（2891/2884/3583/6669/2356/2382/2345/3717/2454）為盤前候選池排除股，非 holding → 追蹤部位無漏出場'},
 'exit_rules':{'stop_loss_hits':0,'two_day_drawdown_hits':0,'reversal_l3_l4_new':0,'pending_review':1,
   'closest_to_stop':'5876 上海商銀 48.25，距停損 44.82 還有 +7.65%（已決出場的 2886 兆豐金 +6.60%）','worst_two_day':'2886 兆豐金 -1.32%（09-29 收 49.1 → 48.45）'},
 'opening_exits_recheck':'2886 兆豐金 6.1%（L4）／3702 大聯大 4.0%（L2）／2376 技嘉 12.3%（L4）（09-30 T86、avg_5day_volume 分母、12:3x 取樣）；已決事項不重評',
 'pending_review_1':'2395 研華 -178 張：盤前 7.6% → 12:30 7.5%（L4），第一次複核 ≥5% 成立；盤後第二次仍 ≥5% 才於 10-02 開盤出場',
 'frozen':['2867 三商壽（序列停滯，末日 2026-08-19）'],
 'holdings_stop_loss_recheck':'0 筆新觸發；6770 力積電 74.4 > 73.26（盤中低 73.3，貼近）；2337 旺宏 121.5<147.6、2313 華通 224.5<235.98、3090 日電貿 169.5<256.5 皆為流程紀錄已出場部位（yaml 未更新）重複輸出；1301 台塑 67.0、4938 和碩 89.5 未觸發；2330 無停損欄',
 'prior_decisions_status':'已決事項 3 筆（2886/3702/2376）今日開盤出場，原樣執行不重評',
 'detector':{'scanned':679,'realtime_fetched':68,'coverage_pct':10.0,'strong':['2371 大同 95','3481 群創 90','3518 柏騰 75','7736 虎山 70','2034 允強 65','6861 睿生光電 65'],'moderate':['2231 為升 55','6142 友勁 55','2347 聯強 50','6944 兆聯實業 40']},
 'track_b_result':'今日無盤中新推薦（0 檔）；偵測器 6 檔強訊號皆未過：2371 大同 90 分但①催化對齊未過（列首要觀察）、3481 動能否決＋放量下跌、3518 已大漲＋處置倒數、7736 41 分、2034／6861 爆量急跌型態轉弱',
 'dossier_intraday':'無盤中新推薦 → 依 Step 3.5 免跑',
 'tier_from_tracker_added':0,
 'data_source_notes':['現價取 Yahoo chart meta.regularMarketPrice（12:10~12:18，約延遲 20 分鐘）','前收取 get_close_series 09-30 收盤','intraday_institutional_detector 679 檔僅取得 68 檔即時行情（TWSE MIS 限流），覆蓋率 10.0%','盤中 check_* 腳本 JSON 另存 _intraB/*_intraday.json，盤前版本已還原','法人數據為 09-30 T86（與盤前同一份），10-01 T86 盤後才公布','exit_signal_checker 逐檔帶各自推薦價執行']
}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in t['opening_exits_today']: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['intraday_price'],r['intraday_return_pct'],r['intraday_day_change_pct'])
for r in t['recommendations']+t['carry_over_recommendations']: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['target_price'],r['stop_loss'],r.get('intraday_price'),r.get('intraday_day_change_pct'),r.get('intraday_return_pct'),r.get('intraday_dist_to_stop_pct'),r.get('intraday_two_day_pct'),r.get('holding_days'),r.get('intraday_high'))
