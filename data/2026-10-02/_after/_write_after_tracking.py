import json
f='data/tracking/tracking_2026-10-02.json'
t=json.load(open(f,encoding='utf-8'))
rows=json.load(open('data/2026-10-02/_after/holding_rows.json',encoding='utf-8'))
t86=json.load(open('data/cache/twse_t86_20261002.json',encoding='utf-8'))
# code: (level, pct, decision)
R={'2330':('L4',24.9,'exit'),'2379':('L4',9.2,'exit'),'3231':('L4',68.8,'exit'),'2344':('L4',11.4,'exit'),
   '3035':('L0',None,'hold'),'2327':('L0',None,'hold'),'8150':('健康',None,'hold'),'3037':('健康',None,'hold'),
   '2609':('健康',None,'hold'),'6257':('L0',None,'hold'),'3711':('L0',None,'hold')}
SET=json.load(open('data/2026-10-02/_after/settlements.json',encoding='utf-8'))
def upd(r):
    k=r['stock_code']
    if k in SET:
        v=SET[k]
        r.update({'result':v['result'],'actual_close':v['close'],'close_price':v['close'],'current_price':v['close'],'settled_date':'2026-10-02','settled_price':v['close'],'return_pct':v['ret'],
                  'holding_days_label':v['D'],'holding_status':f"已結算（{v['result']}，{v['ret']:+.2f}%）：{v['note']}"})
        r['change_percent']=rows[k]['chg']
        if not isinstance(r.get('holding_days'),int): r['holding_days']=rows[k]['D']
        return
    if k not in R: return
    lv,pct,dec=R[k]; v=rows[k]; tot=t86[k]['total']
    r['actual_close']=v['cl']; r['close_price']=v['cl']; r['current_price']=v['cl']; r['change_percent']=v['chg']; r['return_pct_at_close']=v['ret']
    r['result']='holding'
    r['holding_days_label']=f"D{v['D']}/10"
    r['holding_days']=v['D']
    base=f"收盤 {v['cl']}（今日 {v['chg']:+.2f}%，相對推薦價 {v['ret']:+.2f}%）；10-02 T86 {tot:+,} 張"
    if dec=='exit':
        r['holding_status']=f"🛑 10-05 開盤出場（鐵律③ L4）：{base}＝{pct}%（≥8%，avg_5day_volume 分母、16:17 取樣），佔比 ≥8% 不受 v8.3.3 保護；入帳價用 10-05 收盤（v8.3.2）"
    else:
        extra=''
        if k=='8150': extra='；⚠️ 今日漲停 127.0 已越目標 124.5，D0 不結算（checker 排除 D0），10-05 D1 起收盤 ≥124.5 即由 settlement_checker 判 success；⚠️ 自算處置預警連續達標 3 天、最快剩 0 天處置'
        if k=='3037': extra='；距目標 1,312 僅 0.54%'
        if k=='6257': extra='；⚠️ 10/06 法說會（凱基聯合法說 14:30）；今日重大訊息：取得機器設備逾 5 億元（擴產，中性偏多）'
        if k=='2327': extra='；外資 -2,787／投信 +3,146（外資轉賣、投信承接）'
        r['holding_status']=f"續抱：{base}（{lv}）；鐵律①②③ 無觸發；距停損 {v['dist_stop']:+.2f}%、距目標 {v['dist_target']:.2f}%{extra}"
    r['reversal_level_1002t86']=lv; r['sell_ratio_pct_1002t86']=pct
for r in t['recommendations']: upd(r)
for r in t['carry_over_recommendations']: upd(r)
t['tomorrow_opening_exits_note']="10-02 T86 於 16:14 公布（14:31 起每 90 秒輪詢），16:16 快取落檔後重跑全部 holding 的 reversal_alert（24 檔張數與 twse_t86_20261002.json 逐筆一致，無舊值退回）：新 L4 4 檔全為今日 D0 新推薦 —— 3231 緯創 68.8%／2330 台積電 24.9%／2344 華邦電 11.4%／2379 瑞昱 9.2%，皆 ≥8% → 10-05 開盤出場；my_holdings.yaml 持倉 4938 和碩 23.5% L4 → 10-05 開盤出場（持倉決議）。待複核 0 筆。3035 智原／2327 國巨*／6257 矽格／3711 日月光投控 L0、8150 南茂／3037 欣興／2609 陽明 健康 → 續抱。鐵律①停損 0 筆、鐵律② 2 日 -10% 0 筆。"
t['tomorrow_pending_review']=[]
def rec(code,name,ind,price,tp,score,rating,pos,detail,reason):
    return {'stock_code':code,'stock_name':name,'industry':ind,'recommend_date':'2026-10-05','recommend_price':price,
            'target_price':tp,'stop_loss_pct':-10,'stop_loss':round(price*0.90,2),'settlement_days':10,'position':pos,
            'score':score,'rating':rating,'track':'A','status':'預估，10-05 盤前須以 10/02 美股（非農後）與盤前價、📶訊號A／B 重驗','score_detail':detail,'reason':reason}
t['tomorrow_recommendations']=[
 rec('2408','南亞科','記憶體 DRAM（industry_chains：半導體 tier_1 DRAM／AI tier_2 HBM、DDR5）',526.0,568.0,107,'⭐⭐⭐⭐⭐','10-15%',
  '五維度 87＝時事 22（🔴DRAM與記憶體影響鏈直接點名 南亞科(2408)↑ 進駐屏科 21、美光單日 +3.03% +1）＋法人 24（avg_rank 7.0 → 21、佔成交 23.9% +2、外資 +7,170／投信 +1,161 同步 +1）＋產業 17＋技術 13（健康、動能 <-30% 且真連買 4 天 → 佈局完成）＋價位 11（vs MA20 +4.18%、月季雙線上）｜動能 -96.6% +15｜EPS Q2 +5｜營收 0（2026-08 YoY +560.9% 未回檔）｜外資持股比 0（小增）｜模式追蹤：「記憶體 DRAM」42.9% 未達扣分線',
  '🛤️軌道A｜🔴超強催化『DRAM與記憶體』影響鏈點名↑（美光稱 2027-28 財年供需更緊、簽 26 份多年期長約；MU +3.03%）｜10-02 T86 +8,755 張（外資 +7,170／投信 +1,161 同步，買超金額 46 億）｜真連買 4 天、10 日買 7 賣 3、累計 +41,283｜近 5 天外資 +2,252｜動能 -96.6% 佈局完成 +15｜EPS Q2 +5｜營收 2026-08 YoY +560.9% 不加分｜外資持股比不調整（小增）｜月線乖離 +4.18% 落在 0~+5% 區，但在 10-02 TOP50 買超名單內 → 法人現身門檻通過｜⚠️ 卷宗矛盾點：美光下季毛利率略降、美光台灣罷工投票結果未明、⚪『記憶體缺貨衝擊終端』標 南亞科→ → 回應：tracker 主題方向仍為↑，法人連 4 日買超未見撤出；列風險不扣分｜⚠️ 09-24 推薦曾於 D1 轉 L4 出場；09-22／09-24 各有單日 -2.3 萬張賣超，籌碼大進大出｜卷宗：事件 0、提及 20 處｜預估：須 10-05 盤前重驗'),
 rec('6770','力積電','記憶體／DRAM 代工（industry_chains 記憶體 tier_from_tracker「DRAM 與記憶體」→ 產業邏輯以 13-16 分計）',76.5,82.6,98,'⭐⭐⭐⭐⭐','5-10%（單日大買型態，倉位自行壓低）',
  '五維度 86＝時事 23（🔴DRAM與記憶體影響鏈直接點名 力積電(6770)↑ 承接美光 HBM 後段 21、美光 +3.03% +1、🔴光通訊與網通亦點名↑ 共振 +1）＋法人 25（avg_rank 3.0 → 22、佔成交 28.0% +2、外資 +45,435／投信 +268 同步 +1，封頂 25）＋產業 14（tier_from_tracker 待審區）＋技術 11（健康、動能 <-30% 但真連買 1 天 → 佈局中）＋價位 13（vs MA20 +6.32%、雙線上）｜動能 -49.9% +15｜過量買超（單日 49,896 張 ≥30K、真連買 1 天 <7）-5｜外資持股比週減 -3｜EPS Q2 +5｜營收 0（YoY +76.2% 未回檔）',
  '🛤️軌道A｜🔴超強催化『DRAM與記憶體』＋『光通訊與網通』雙主題點名↑（承接美光 HBM 後段、洽 imec 授權）｜10-02 T86 +49,896 張（外資 +45,435，買超張數全市場第 2、金額 38 億）｜近 5 天外資 +62,853、10 日累計 +204,227、買 7 賣 3｜動能 -49.9% +15｜EPS Q2 +5｜⚠️ 過量買超 -5｜⚠️ 外資持股比週減 -3｜營收 2026-08 YoY +76.2% 不加分｜⚠️ 真連買僅 1 天：09-30 +61,796 → 10-01 -14,278（L4 14.1%）→ 10-02 +49,896，法人日間大進大出，與本週檢討的「單日大買隔日被賣」型態相同 → 倉位壓在 5-10%｜⚠️ 09-24 推薦曾於 D1 轉 L4 出場｜my_holdings.yaml 仍列本股 2 張（成本 81.4／停損 73.26；流程紀錄已於 L4 出場，yaml 未更新）→ 持倉加碼評估 98 分「可加碼」｜卷宗：事件 0、提及 11 處，無矛盾｜預估：須 10-05 盤前重驗')]
t['tomorrow_recommendations_note']="10-05 預估推薦 2 檔（2408 南亞科 107／6770 力積電 98）。候選池 63 檔＝10-02 T86 TOP50 買超 50 檔＋續抱與持倉 13 檔；籌碼（含 10-02 T86，執行期包裝）、營收（63/63 為 2026-08）、外資持股比（63/63 ≥09-29）、EPS（--update-cache）、價格位置全部以 10-02 資料重算，盤前四份 JSON 已 git 還原。今日 TOP50 買超以塑化、面板、傳產為主：16 檔 5 日 >10% 已大漲、13 檔動能 >100% 無覆寫依據、9 檔反轉狀態不明、8 檔近 5 天外資為負 → 通過全部門檻者僅 2 檔，依 v8.2 寧缺勿濫不湊數。停損依本次作業指示一律 -10%。📶訊號A／📶訊號B 未以 10-02 T86 重跑，未採計加分。"
t['tomorrow_carry_over']=['2609','6257','3711','3035','2327','8150','3037','2867']
t['tomorrow_watchlist']=[
 "2337 旺宏（65 分；🔴DRAM 點名↑、10-02 T86 +3,326 張；動能 +69.7% -10、模式追蹤 cold「記憶體-NOR Flash」18.2%（n=11）-5 → <70 不列；yaml 持倉且低於停損）",
 "2886 兆豐金（10-02 T86 +17,610 張、佔成交 63.3%、真連買 2 天、近 5 天外資 +21,266；金融無 🔴／🟡 影響鏈點名 → ①未過；EPS 快取 2025-12 視為 0）",
 "1326 台化／1301 台塑／1303 南亞／6505 台塑化（今日依已決事項出場，當日 T86 翻買 +23,062／+15,625／+6,909／+8,024 張；動能 +500%／+500%／+374% 需覆寫或 5 日 +14% 已大漲 → 不列；近 10 筆覆寫推薦全數 D0-D1 轉 L4）",
 "2412 中華電（今日 D10 結算 success；T86 +2,577、真連買 3 天、買 9 賣 1；①催化未對齊）",
 "2303 聯電（+7,837 張、真連買 3 天；近 5 天外資 -19,395 → ②未過）",
 "2883 凱基金（+21,145 張、營收 +5；近 5 天外資 -16,944 → ②未過；動能 +500%；現增稀釋疑慮）",
 "2409 友達（+91,289 張全市場第 1；5 日 +16.57% 已大漲 → 不評分）"]
act=['2609','6257','3711','2330','3035','2379','2327','8150','3037','3231','2344']
d0=['2330','3035','2379','2327','8150','3037','3231','2344']
avg=lambda ks,f:round(sum(rows[k][f] for k in ks)/len(ks),2)
t['after_market']={
 "report_time":"2026-10-02 16:50",
 "taiex_close":48475.74,"taiex_change_pct":0.25,"taiex_change_pts":122.25,
 "taiex_source":"TWSE FMTQIK（成交值 9,331.9 億）；Yahoo ^TWII regularMarketPrice 48,475.74 一致",
 "market_institutional":"BFI82U 10-02：三大法人合計 +95.57 億（外資 +26.22 億、投信 +49.10 億、自營商自行 +47.41 億、避險 -27.15 億）；前一日 +292.53 億",
 "t86_today_published":True,
 "t86_note":"10-02 T86 於 16:14 公布（14:31 起每 90 秒輪詢，16:13 仍查無）；16:16 快取落檔。BFI82U／FMTQIK 15:14 已可取得。本次排程仍於 14:30 啟動，等待 104 分鐘",
 "t86_consistency_check":"reversal_alert 24 檔『今日張數』與 data/cache/twse_t86_20261002.json total 欄逐筆一致，無 10-01 舊值退回",
 "settled_today":7,"settled_win":6,"settled_loss":1,"settled_accuracy_today":85.7,
 "holdings_avg_change_pct":avg(act,'chg'),"holdings_avg_return_pct":avg(act,'ret'),
 "holdings_up":f"{sum(1 for k in act if rows[k]['chg']>0)}/{len(act)}",
 "today_recommendations_d0":f"8 檔 D0：{sum(1 for k in d0 if rows[k]['chg']>0)} 漲 {sum(1 for k in d0 if rows[k]['chg']<0)} 跌，平均 {avg(d0,'chg'):+.2f}%；8150 南茂 +9.96% 漲停、3037 欣興 +7.41%、2327 國巨* +3.99%；當日 T86 有 4 檔轉 L4（3231／2330／2344／2379）",
 "ironclad_checks":{
  "stop_loss":"0 筆（續抱 11 檔全檢；最近 3231 緯創 186.5 距停損 171.45 +8.78%）",
  "two_day_drawdown":"0 筆（09-30 收盤→10-02 收盤；最差 2379 瑞昱 -0.79%、2344 華邦電 -0.28%）",
  "reversal_l3_l4":"10-02 T86（16:17 掃描）：L4 4 檔 —— 3231 緯創 68.8%／2330 台積電 24.9%／2344 華邦電 11.4%／2379 瑞昱 9.2%（皆 ≥8% → 10-05 開盤出場）；L0 4 檔 3035 智原／2327 國巨*／6257 矽格／3711 日月光投控；健康 3 檔 8150 南茂／3037 欣興／2609 陽明；凍結 1 檔 2867 三商壽",
  "pending_review":"0 筆（4 檔 L4 佔比皆 ≥8%，不適用 v8.3.3）"
 },
 "holdings_stop_loss_recheck_v8310":"0 筆新觸發；6770 力積電 76.5 > 73.26；2337 旺宏 122.0<147.6、2313 華通 226.0<235.98、3090 日電貿 173.5<256.5 為流程紀錄已出場部位（yaml 未更新）重複輸出；1301 台塑 68.3>54.08、4938 和碩 89.2>76.5 未觸發；2330 台積電 無停損欄",
 "holdings_reversal_1002t86":"4938 和碩 -2,218 張＝23.5%（L4，≥8% → 10-05 開盤出場）／2330 台積電 -5,344 張＝24.9%（L4，零股 0.15 張同適用）／6770 力積電 +49,896（健康）／2337 旺宏 +3,326（健康）／2313 華通 +2,070（狀態不明，10 日累計 -5,800）／3090 日電貿 +881（L0）／1301 台塑 +15,625（健康；追蹤部位今日已依已決事項出場）",
 "target_near":["8150 南茂 127.0／124.5（D0 已越目標，10-05 D1 起可結算）","3037 欣興 1,305／1,312（差 0.54%）","2327 國巨* 626／650（差 3.83%）"],
 "d10_tomorrow":[],
 "close_verification":"24 檔（11 檔續抱＋7 檔今日結算＋6 檔 yaml 持倉）Yahoo 日K 末列（10-02）與 TWSE MIS z 值逐檔一致；MIS 時間戳 13:30 收盤報價，非幻影列",
 "tier_from_tracker_added":0,
 "exited_today_recheck_1002t86":"當日出場 5 檔的 10-02 T86：1326 台化 +23,062／1301 台塑 +15,625／6505 台塑化 +8,024／1303 南亞 +6,909（4 檔翻買，皆健康）／2395 研華 -53（L2）。僅記錄，不改判（已決事項）",
 "exited_1001_followup":"10-01 出場 3 檔的 10-02 表現：2886 兆豐金 0.00%（T86 +17,610）／3702 大聯大 0.00%（T86 -391）／2376 技嘉 +1.36%（T86 +1,539）",
 "preflight":"首跑於【3】D10 到期結算崩潰（TypeError：盤前寫入的 recommendations.holding_days 又是字串 'D0/10'，與 10-01 相同）；以執行期包裝 _after/_preflight_wrap.py 把字串轉整數後交回原邏輯，6 項全部通過（scripts/ 未改動）；盤後已把 tracking 該欄改為整數"
}
t['after_market']['disposition']={
  "twse_official":["2030 彰源｜10/02~10/08｜第一次處置（連續三次）","2455 全新｜09/23~10/05｜第二次處置（連續五次及當沖標準）","2468 華經｜09/22~10/02｜第一次處置（連續五次及當沖標準）","3016 嘉晶｜10/01~10/12｜第一次處置（連續三次及當沖標準）","3055 蔚華科｜10/01~10/12｜第二次處置（連續五次及當沖標準）","3443 創意｜09/29~10/05｜第一次處置（連續三次）","6168 宏齊｜09/24~10/02｜第一次處置（連續三次）","6526 達發｜09/30~10/06｜第一次處置（連續三次）"],
  "tpex_official":["8084 巨虹｜10/02~10/08｜連續3個營業日","8227 巨有科技｜10/02~10/08｜連續3個營業日","2221 大甲｜10/01~10/12｜連續3個營業日及沖銷標準","3219 倚強科｜10/01~10/07｜連續3個營業日","7792 安葆｜09/30~10/06｜連續3個營業日","3374 精材｜09/29~10/05｜10 日內 6 日達注意","4542 科嶠｜09/29~10/05｜連續3個營業日","4979 華星光｜09/29~10/05｜連續5個營業日","7772 耀穎｜09/24~10/02｜連續3個營業日","6218 豪勉｜09/23~10/05｜連續3個營業日及沖銷標準"],
  "twse_attention":[],
  "fetched_at":"2026-10-02 16:29（10-02 盤後新公告可能尚未上架，10-05 盤前須重抓）",
  "in_pool":"候選池 63 檔無官方處置股",
  "self_calc_pool":["8150 南茂｜連續達標 3 天｜最快明日處置（續抱中）","1709 和益｜連續達標 3 天｜最快明日處置","2492 華新科｜連續達標 2 天｜最快剩 1 天處置","2340 台亞｜連續達標 2 天｜最快剩 1 天處置","6834 天二科技｜連續達標 2 天｜最快剩 1 天處置","1727 中華化｜連續達標 6 天｜最快剩 4 天處置","2409 友達／9933 中鼎／6120 達運／3673 TPK-KY／2342 茂矽｜接近注意門檻"]}
t['yesterday_verification']={"date":"2026-10-02","settled_count":7,"success_count":6,"fail_count":1,"accuracy":85.7,
 "results":[{"stock_code":r['stock_code'],"stock_name":r['stock_name'],"recommend_date":r['recommend_date'],"recommend_price":r['recommend_price'],"settled_price":r['settled_price'],"return_pct":r['return_pct'],"result":r['result'],"removal_reason":r['removal_reason']} for r in t['removed_stocks']],
 "note":"3 筆為 settlement_checker 機械判定的 D10 到期（5876 fail／2412、2395 success；2395 同日亦為已決事項出場），4 筆為 10-01 盤後定案的鐵律③ L4 開盤出場（塑化四檔，v8.3.7 已決事項），入帳價皆用 10-02 收盤"}
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in t['tomorrow_recommendations']: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['target_price'],r['stop_loss'],r['score'])
a=t['after_market']; print('avg',a['holdings_avg_change_pct'],a['holdings_avg_return_pct'],a['holdings_up']); print(a['today_recommendations_d0'])
for r in t['recommendations']+t['carry_over_recommendations']: print(r['stock_code'],r.get('result'),r.get('holding_days'),r.get('close_price'),str(r.get('holding_status'))[:60])
