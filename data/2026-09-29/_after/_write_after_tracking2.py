import json
f='data/tracking/tracking_2026-09-29.json'
t=json.load(open(f,encoding='utf-8'))
t['tomorrow_opening_exits']=[]
t['tomorrow_opening_exits_note']="盤後反轉掃描 16 檔（10 筆續抱＋4 筆當日出場＋8046 南電＋2867 凍結），基於 09-24 T86 以 09-29 完整日量重算：續抱 10 檔全數 L0／健康，無 L3/L4、無待複核；鐵律①停損 0 筆（最近 2454 聯發科 距停損 +3.16%）、鐵律② 2 日 -10% 0 筆（最差 2454 聯發科 -5.30%）。⚠️ 09-29 T86 於報告產出時尚未公布 → 09-30 盤前必須以 09-29 T86 重跑全部 holding 的 reversal_alert，L4 者依規則開盤出場。"
t['tomorrow_recommendations']=[]
t['tomorrow_recommendations_note']="09-30 新推薦 0 檔：候選池 49 檔（09-24 T86 TOP50 買超扣除持有中＋3045/2603/2308/2006/1708/2883）逐檔以 09-29 收盤重算 5 日漲幅／價格位置／營收／外資持股比，籌碼欄位沿用 09-24 T86（09-29 T86 未公布）；排除理由為反轉／動能一票否決／已大漲／準確率①②／法人現身門檻，無一檔翻案。依 v8.2 寧缺勿濫不湊數。09-30 盤前以 09-29 T86 完整重跑 Step 5~9。"
t['tomorrow_carry_over']=['4904','5876','2395','2412','2892','2454','2886','2609','3702','6196','2867']
t['tomorrow_watchlist']=["2308 台達電（🔴AI 影響鏈點名；5 日回落至 +5.76%，但動能 +441% 且不在 09-24 TOP50 買超 × vs MA20 +3.08% → 法人現身門檻未過，無例外）",
  "3045 台灣大（準確率①催化對齊未過；真連買 10 天、近5天外資 +8,646）",
  "2603 長榮（🔴中東影響鏈；近5天外資 -1,436，準確率②未過）",
  "2027 大成鋼（訊號A L3、動能 -39.3%；①鋼鐵僅 ⚪ 觀察＋模式 cold 33.3%）"]
t['after_market']={
 "report_time":"2026-09-29 15:00",
 "taiex_close":47631.96,"taiex_change_pct":-0.82,"taiex_change_pts":-392.64,
 "taiex_source":"TWSE MIS t00（13:33 收盤值；前收 48,024.60）；FMTQIK／BFI82U 於報告產出時尚未更新 09-29",
 "market_institutional":"BFI82U 09-29 尚未公布",
 "t86_today_published":False,
 "t86_note":"14:31 起每分鐘輪詢 09-29 T86 皆『沒有符合條件的資料』（memory project_after_market_t86_not_published，n=7）",
 "settled_today":5,"settled_win":2,"settled_loss":3,"settled_accuracy_today":40.0,
 "holdings_avg_change_pct":-1.90,"holdings_avg_return_pct":-1.63,"holdings_up":"1/10",
 "ironclad_checks":{"stop_loss":"0 筆（10 檔全檢，最近 2454 聯發科 4,910 距停損 4,759.5 +3.16%；次近 2892 第一金 +5.23%）",
   "two_day_drawdown":"0 筆（09-23 收盤→09-29 收盤；最差 2454 聯發科 -5.30%）",
   "reversal_l3_l4":"續抱 10 檔 0 筆（09-24 T86＋09-29 完整日量）；當日出場 4 檔盤後仍為 L4（21.7%／39.1%／42.1%／73.2%）","pending_review":"0 筆"},
 "holdings_stop_loss_recheck_v8310":"0 筆新觸發；6770 72.3<73.26、2337 118.5<147.6、2313 226.0<235.98、3090 161.0<256.5 為流程紀錄已出場部位（yaml 未更新）重複輸出；1301 64.6、4938 90.8 未觸發；2330 無停損欄",
 "target_near":["2395 研華 730／740（差 1.4%；盤中高 754 曾越過目標，收盤回落未結算）"],
 "close_verification":"22 檔收盤價以 Yahoo 日K 末列（09-29 13:30 時間戳）與 TWSE MIS z 值逐檔比對，全部一致",
 "disposition":{"twse_official":["2305 全友｜09/18~09/30｜第一次處置","2455 全新｜09/23~10/05｜第二次處置","2468 華經｜09/22~10/02｜第一次處置",
   "3443 創意｜09/29~10/05｜第一次處置","6168 宏齊｜09/24~10/02｜第一次處置","6226 光鼎｜09/21~10/01｜第二次處置","6715 嘉基｜09/23~10/01｜第一次處置","8021 尖點｜09/23~10/01｜第二次處置"],"twse_attention":[]},
 "tier_from_tracker_added":0}
t['yesterday_verification']={"date":"2026-09-29","settled_count":5,"success_count":2,"fail_count":3,"accuracy":40.0,
 "results":[{k:v for k,v in r.items() if k in('stock_code','stock_name','recommend_date','recommend_price','settled_price','return_pct','result','removal_reason')} for r in t['removed_stocks']]}
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
