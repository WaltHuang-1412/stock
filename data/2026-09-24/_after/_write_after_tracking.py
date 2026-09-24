import json
f='data/tracking/tracking_2026-09-24.json'
t=json.load(open(f,encoding='utf-8'))
c=json.load(open('data/2026-09-24/_after/closes.json'))
D={'4904':'D7/10','5876':'D6/10','2395':'D6/10','2412':'D6/10','2303':'D4/10','2892':'D4/10','2454':'D2/10',
   '2886':'D1/10','8046':'D1/10','2609':'D1/10','6770':'D0/10','2408':'D0/10','2317':'D0/10'}
REV={'2303':'L2（09-23 T86 -10,135 張＝4.5%，未達 L3/L4）','2412':'✅健康 +4,591','8046':'✅健康 +3,802','2609':'✅健康 +3,244',
     '6770':'✅健康 +25,104','2408':'✅健康 +29,607','2317':'✅健康 +7,773'}
def upd(r):
    k=r['stock_code']
    if k=='2867':
        r['holding_status']='⏸️ 序列停滯凍結（末日 2026-08-19），不結算、不出場、D 不推進（v8.3.8）'; return
    if k not in D: return
    d=dict(c[k]); cl=d['2026-09-24']; pv=d['2026-09-23']; p=r['recommend_price']
    r.update({'actual_close':cl,'close_price':cl,'change_percent':round((cl/pv-1)*100,2),'return_pct':round((cl/p-1)*100,2),
              'holding_days':D[k],'result':'holding',
              'holding_status':f"續抱：反轉 {REV.get(k,'L0 中性')}（09-23 T86，09-24 T86 未公布）；鐵律①②③ 無觸發；收盤 {cl}（{(cl/p-1)*100:+.2f}%）"})
for r in t['recommendations']: upd(r)
for r in t['carry_over_recommendations']: upd(r)
t['tomorrow_opening_exits']=[]
t['tomorrow_opening_exits_note']="盤後反轉掃描 14 檔（13 筆追蹤＋2867 凍結），基於 09-23 T86 以 09-24 完整日量重算：L4/L3 0 檔、L2 1 檔（2303 聯電 4.5%，不出場）、❓數據不足 1 檔（2867 凍結）；鐵律①停損 0 筆、鐵律② 2 日 -10% 0 筆。⚠️ 09-24 T86 於 15:27 仍未公布，且 09-24 市場三大法人合計賣超 -438.7 億（外資 -338.0 億、投信 -114.1 億）→ 09-29 盤前必須以 09-24 T86 重跑全部 holding 的 reversal_alert，L4 者依規則開盤出場。"
t['tomorrow_recommendations']=[]
t['tomorrow_recommendations_note']="09-29（下一交易日）新推薦 0 檔：候選池（09-23 T86 TOP50 買超 42 檔＋2603/2883/2884/6213）結構性排除理由（反轉、動能一票否決、準確率①②）全部源自 09-23 T86，與今日盤前相同；以 09-24 收盤重算 5 日漲幅／價格位置／營收／外資持股比後無任何一檔翻案。依 v8.2 寧缺勿濫不湊數。09-24 T86 未公布、4 天連假資訊落差大 → 09-29 盤前以新 T86 完整重跑 Step 5~9。"
t['tomorrow_carry_over']=['4904','5876','2395','2412','2303','2892','2454','2886','8046','2609','6770','2408','2317','2867']
t['tomorrow_watchlist']=["3045 台灣大（準確率①催化對齊未過；真連買 10 天、近5天外資 +7,974）",
  "2379 瑞昱（5 日回落至 +4.76%，-10 解除；但動能 +146% 無 🔴 覆寫依據，仍排除）",
  "2603 長榮（近5天外資 -6 張，準確率②未過）","2883 凱基金（①與 🟡美債主題點名矛盾）"]
t['after_market']={
 "taiex_close":48024.60,"taiex_change_pct":-0.28,"taiex_source":"TWSE FMTQIK（Yahoo ^TWII 09-24 日K close=None）",
 "market_institutional":"BFI82U：三大法人合計 -438.73 億（外資 -338.02 億、投信 -114.09 億、自營商自行 +42.36 億、避險 -28.97 億）",
 "t86_today_published":False,
 "t86_note":"14:31~15:27 每分鐘輪詢 09-24 T86 皆『查無數據』（memory project_after_market_t86_not_published，n=6）",
 "settled_today":8,"settled_win":5,"settled_loss":3,"settled_accuracy_today":62.5,
 "holdings_avg_return_pct":0.60,"holdings_up":"5/13",
 "ironclad_checks":{"stop_loss":"0 筆（13 檔全檢，最近 2892 第一金 距停損 +7.7%）","two_day_drawdown":"0 筆（最差 2303 聯電 -3.75%）",
   "reversal_l3_l4":"0 筆（09-23 T86 完整日量重算）","pending_review":"0 筆"},
 "holdings_stop_loss_recheck_v8310":"0 筆新觸發；6770 72.0<73.26、2337 117.0<147.6、2313 222.5<235.98、3090 165.0<256.5 為已出場部位（yaml 未更新）重複輸出；1301 64.1、4938 91.3 未觸發；2330 無停損欄",
 "target_near":["8046 南電 1240／1260（差 1.6%）","2454 聯發科 5285／5400（差 2.2%）","2395 研華 722／740（差 2.5%）"],
 "disposition":{"twse_official":["2305 全友｜09/18~09/30｜第一次處置","2455 全新｜09/23~10/05｜第二次處置","2468 華經｜09/22~10/02｜第一次處置",
   "6168 宏齊｜09/24~10/02｜第一次處置","6226 光鼎｜09/21~10/01｜第二次處置","6715 嘉基｜09/23~10/01｜第一次處置","8021 尖點｜09/23~10/01｜第二次處置"],"twse_attention":[]},
 "tier_from_tracker_added":0}
t['yesterday_verification']={"date":"2026-09-24","settled_count":8,"success_count":5,"fail_count":3,"accuracy":62.5,
 "results":[{k:v for k,v in r.items() if k in('stock_code','stock_name','recommend_date','recommend_price','settled_price','return_pct','result','removal_reason')} for r in t['removed_stocks']]}
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
