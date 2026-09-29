import json
f='data/tracking/tracking_2026-09-29.json'
t=json.load(open(f,encoding='utf-8'))
rows=json.load(open('data/2026-09-29/_after/holding_rows.json',encoding='utf-8'))
# code: (level, T86 total, pct, 10d cum, decision)
R={'4904':('L4',-454,9.3,'+4,509','exit'),'2892':('L4',-3085,13.2,'+56K','exit'),'2454':('L4',-4812,57.0,'+6,238','exit'),
   '2609':('L4',-6231,24.9,'+34K','exit'),'6196':('L4',-346,23.5,'+1,306','exit'),
   '2886':('L4',-1613,7.4,'+23K','pending'),'3702':('L4',-572,5.8,'+12K','pending'),
   '2412':('L2',-174,1.5,'+56K','hold'),'5876':('L0',700,None,'+13K','hold'),'2395':('L0',6,None,'+4,675','hold')}
def upd(r):
    k=r['stock_code']
    if k not in R: return
    lv,tot,pct,cum,dec=R[k]; v=rows[k]
    base=f"收盤 {v['cl']}（{v['ret']:+.2f}%）；09-29 T86 {tot:+,} 張"
    if dec=='exit':
        r['holding_status']=f"🛑 09-30 開盤出場（鐵律③ L4）：{base}＝{pct}%（≥8%，avg_5day_volume 分母、16:17 取樣），10 日累計 {cum}；不適用 v8.3.3 待複核；入帳價用 09-30 收盤（v8.3.2）"
    elif dec=='pending':
        r['holding_status']=f"⚠️ 待複核（v8.3.3）：{base}＝{pct}%（<8%）且 10 日累計 {cum} 為正 → 09-30 不開盤出場，12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-01 開盤出場"
    elif lv=='L2':
        r['holding_status']=f"續抱、不加碼：{base}＝{pct}%（L2 單日反轉，未達 L3/L4），10 日累計 {cum}；鐵律①②③ 無觸發"
    else:
        r['holding_status']=f"續抱：{base}（L0），10 日累計 {cum}；鐵律①②③ 無觸發"
    r['reversal_level_0929t86']=lv
for r in t['recommendations']: upd(r)
for r in t['carry_over_recommendations']: upd(r)
src={'4904':'2026-09-15','2892':'2026-09-18','2454':'2026-09-22','2609':'2026-09-23','6196':'2026-09-29'}
t['tomorrow_opening_exits']=[{
  'stock_code':k,'stock_name':rows[k]['name'],'category':'鐵律③ L4','recommend_date':src[k],'recommend_price':rows[k]['p'],
  'last_close':rows[k]['cl'],'return_pct_at_close':rows[k]['ret'],
  'reason':f"09-29 T86 賣超 {R[k][1]:+,} 張＝{R[k][2]}%（≥8%）；10 日累計 {R[k][3]}，但佔比 ≥8% 不受 v8.3.3 保護；09-30 開盤出場，入帳價用 09-30 收盤（v8.3.2）",
  'decided_on':'2026-09-29 盤後（09-29 T86 於 16:13 公布後重掃）'} for k in ['4904','2892','2454','2609','6196']]
t['tomorrow_opening_exits_note']="09-29 T86 於 16:13 公布後，以完整 T86 快取重跑全部 holding 的 reversal_alert（16:17）：L4 7 檔，其中 5 檔佔比 ≥8% 列 09-30 開盤出場；2886 兆豐金 7.4%／3702 大聯大 5.8% 佔比 <8% 且 10 日累計為正 → 列待複核不出場。2412 中華電 L2、5876 上海商銀／2395 研華 L0 續抱。鐵律①停損 0 筆、鐵律② 2 日 -10% 0 筆。"
t['tomorrow_pending_review']=[{
  'stock_code':k,'stock_name':rows[k]['name'],'recommend_date':rows[k]['rd'],'recommend_price':rows[k]['p'],
  't86_date':'2026-09-29','t86_total':R[k][1],'sell_ratio_pct':R[k][2],'ten_day_cum':R[k][3],
  'rule':'v8.3.3：盤前 L4 佔比 <8% 且 10 日累計為正 → 待複核；09-30 12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-01 開盤出場；任一次降級則維持追蹤'} for k in ['2886','3702']]
def rec(code,name,ind,price,score,detail,reason):
    return {'stock_code':code,'stock_name':name,'industry':ind,'recommend_date':'2026-09-30','recommend_price':price,
            'target_price':round(price*1.08/0.5)*0.5 if price>=100 else round(price*1.08,1),
            'stop_loss_pct':-10,'stop_loss':round(price*0.90,2),'settlement_days':10,'position':'5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
            'score':score,'rating':'⭐⭐⭐','track':'A','status':'預估，09-30 盤前須以隔夜美股與盤前價重驗','score_detail':detail,'reason':reason}
t['tomorrow_recommendations']=[
 rec('1303','南亞','塑化 tier_0（industry_chains；另登錄 中東地緣政治／記憶體 tier_from_tracker）',247.0,80,
  '五維度 85＝時事 20（🔴中東地緣政治：知識庫登錄於此主題，影響鏈未直接點名、當日時事資料實際提及 0 處 → 取下緣）＋法人 25（avg_rank 1.0 → 23、佔成交 42.8% +2、外資 +30,203／投信 +1,825 同步 +1，封頂 25）＋產業 17（塑化 tier_0）＋技術 10（健康、真連買 2 天、正常型態）＋價位 13（vs MA20 +5.59%、月季雙線上）｜動能 +241.9% 🔥超強催化覆寫 0｜過量買超（單日 33,821 張 ≥30K＋真連買 2 天）-5｜10 日賣超 6 天 -5｜EPS Q2 +5｜Micron L1 預警 -5（09-28 美股）｜營收 0（YoY +46.7% 未回檔）｜持股比 0',
  '🛤️軌道A｜09-29 T86 +33,821 張（TOP50 #1），全市場三大法人 -781.9 億賣超日逆勢獲外資 +30,203／投信 +1,825 同步買進｜近 5 天外資 +17,282｜🔥超強催化覆寫（動能 +241.9%）｜⚠️過量買超（30K+ 且真連買僅 2 天，回測 5 日勝率 35.2%）｜⚠️10 日買 4 賣 6、10 日外資累計 -25,892｜⚠️Micron L1 預警｜營收 2026-08 YoY +46.7% 不加分｜外資持股比 +0.20% 不調整｜EPS Q2 +5｜當日時事資料無直接提及（卷宗 7 處中 6 處為 2408 南亞科誤配）｜預估：須 09-30 盤前重驗'),
 rec('2376','技嘉','AI 伺服器（industry_chains「AI伺服器」tier_from_tracker → 產業邏輯以 13-16 分計）',362.0,78,
  '五維度 73＝時事 20（🔴AI 伺服器與半導體：影響鏈未直接點名 → 取下緣；NVDA +1.68% 無加分）＋法人 18（avg_rank 21.0 → 16、佔成交 28.1% +2；投信 +2 張不計同步）＋產業 14（tier_from_tracker）＋技術 10（L0、真連買 1 天、正常型態）＋價位 11（vs MA20 +1.51%、月季雙線上）｜動能 +500% 🔥超強催化覆寫 0｜EPS Q2 +5｜營收 0｜持股比 0｜10 日買 7 賣 3',
  '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』（MI 產業鏈 L2 一線整機「技嘉：DGX/HGX 伺服器」）｜09-29 T86 +1,947 張（外資 +1,778），市場級賣超日逆勢買超｜近 5 天外資 +3,684、10 日累計 +3,564｜🔥超強催化覆寫（動能 +500%）｜營收 2026-08 不加分｜外資持股比 不調整｜EPS Q2 +5｜⚠️Dell -3.46%／Super Micro -3.42%（09-28）未登錄龍頭對應表，無機械預警｜預估：須 09-30 盤前重驗')]
t['tomorrow_recommendations_note']="09-30 預估推薦 2 檔（皆 🔥超強催化覆寫、倉位 5-10%）。候選池 55 檔＝09-29 T86 TOP50 買超＋3045/2308/2603/2027/2404；籌碼（含 09-29 T86）、營收、外資持股比、EPS、價格位置全部以 09-29 資料重算。6505 台塑化 78 分通過全部門檻，但與 1303 南亞同屬塑化，2 檔推薦中塑化不得超過 50% → 依分數取 1303，6505 列第一遞補。停損依本次作業指示一律 -10%（CLAUDE.md 超強催化覆寫條文為 -5%，兩者不一致，已揭露）。訊號A／訊號B 未以 09-29 T86 重跑，未採計加分。"
t['tomorrow_carry_over']=['5876','2395','2412','2886','3702','2867']
t['tomorrow_watchlist']=["6505 台塑化（78 分；🔴中東影響鏈直接點名↑、09-29 T86 +16,559 張外資＋投信同步、真連買 3 天；因單一產業 ≤50% 未列入，1303 南亞盤前重驗未過時遞補）",
  "2881 富邦金（L0、近5天外資 +7,710；動能 +56% -10、營收連續衰退 -5，估 55 分未達門檻）",
  "1718 中纖（L0、動能 -26%；塑化 tier_2 化學纖維 cold 33.3%，估 68 分未達門檻）",
  "3045 台灣大（近5天外資 +8,768；催化未對齊＋不在 TOP50 買超 × 月線乖離 +0.37% 法人現身門檻未過）"]
a=t['after_market']
a.update({"report_time":"2026-09-29 16:40","t86_today_published":True,
 "t86_note":"09-29 T86 於 16:13 公布（14:31 起每分鐘輪詢）；BFI82U 約 15:12、FMTQIK 約 15:22 可取得。v1 報告（14:45，基於 09-24 T86）已於 T86 公布後全面改版",
 "market_institutional":"BFI82U 09-29：三大法人合計 -781.87 億（外資 -632.01 億、投信 +14.17 億、自營商自行 -8.09 億、避險 -155.94 億）",
 "taiex_source":"TWSE FMTQIK（成交值 8,246.9 億）；與 TWSE MIS t00 收盤值一致"})
a["ironclad_checks"]["reversal_l3_l4"]="09-29 T86：L4 7 檔（4904 遠傳 9.3%／2892 第一金 13.2%／2454 聯發科 57.0%／2609 陽明 24.9%／6196 帆宣 23.5% → 09-30 開盤出場；2886 兆豐金 7.4%／3702 大聯大 5.8% → 待複核）、L2 1 檔（2412 中華電 1.5%）、L0 2 檔（5876 上海商銀／2395 研華）"
a["ironclad_checks"]["pending_review"]="2 筆（2886 兆豐金、3702 大聯大）"
a["exited_today_recheck_0929t86"]="當日出場 4 檔的 09-29 T86：6770 力積電 +15,574（健康）／2408 南亞科 +1,608（L0）／2317 鴻海 +2,984（狀態不明，10 日累計為負）／2303 聯電 -2,149（L0）→ 皆已非 L4；僅記錄，不改判"
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in t['tomorrow_recommendations']: print(r['stock_code'],r['recommend_price'],r['target_price'],r['stop_loss'])
