import json
def rec(code,name,ind,price,score,pos,reason,slp=-10,tgt_pct=10):
    sl=round(price*(1+slp/100),2); tgt=round(price*(1+tgt_pct/100),1)
    return {"stock_code":code,"stock_name":name,"industry":ind,"recommend_price":price,"target_price":tgt,
            "stop_loss_pct":slp,"stop_loss":sl,"settlement_days":10,"position":pos,"score":score,"result":"holding","reason":reason}
R=[
rec("2408","南亞科","記憶體-DRAM（industry_chains: 記憶體/tier_0 DRAM；AI/tier_2 HBM/DDR5）",517.0,114,"10-15%",
 "法人 TOP50 綜合排名第 1（+27K／+141億，佔成交 31.6%）｜DRAM 🔴超強 ↑加速：美光 10 年百億美元研發中心＋MU +3.97%、台塑證實南亞科帶頭投資逾 3,000 億建 12 吋廠｜訊號A L2 +10、動能 -78.5% +15｜Q2 EPS YoY+1,211%、毛利率 QoQ+11.6pp +5｜反轉 Level 0、10日累計 +98K、近5日外資 +16K。⚠️ 真連買僅 1 天（7買3賣）；08-20 盤前曾因 L4（賣超佔 21.7%）開盤出場，08-20 T86 翻買 +27K，本筆為新推薦非撤銷出場；⚠️ 營收快取落後 2026-02，本因子未採計；同集團 1303 南亞今日 14:00 法說會"),
rec("2002","中鋼","鋼鐵（industry_chains: 鋼鐵原物料/tier_0 鋼鐵龍頭）",19.35,103,"10-15%",
 "法人 TOP50 張數第 2（+38K，佔成交 61.9%）｜訊號A L2 +10、動能 -95.7% +15｜Q2 EPS YoY+217%、毛利率 QoQ+4.6pp +5｜營收 2026-07 YoY+21.8%（快取新鮮）｜反轉 Level 0、10日累計 +105K。⚠️ 單日 ≥30K 且真連買 1 天 → 過量買超 -5；⚠️ 矛盾：7 月稅前盈餘月減 55%（前 7 月累計 29.94 億 YoY+224%），鋼鐵主題方向→趨緩，時事僅給 16；今日重大訊息＝公告 7 月自結（內容已於 08-20 見報）；08-20 盤前曾為 L4 倒貨名單，今日翻買"),
rec("2027","大成鋼","鋼鐵-不鏽鋼/鋁（industry_chains: 鋼鐵市場需求觸底反轉 tier_from_tracker）",50.5,99,"10-15%",
 "訊號A L2（5 天在 TOP50、avg_rank 最佳 8.0）+10｜動能 -73.9% +15｜Q2 EPS YoY+360%、毛利率 QoQ+3.2pp +5｜反轉 Level 0、10日累計 +51K、近5日外資 +27K｜月線乖離 +9.2%、季線上。⚠️ 投信 10 日 -17K 與外資對作；真連買 2 天；⚠️ 營收快取落後 2026-02，本因子未採計；當日時事資料無直接提及（卷宗 4 筆 mentions 皆為『2027 年』字串誤中）"),
rec("2344","華邦電","記憶體-DRAM/Flash（industry_chains: 記憶體/tier_0）",176.5,94,"5-10%",
 "🔥 超強催化覆寫（DRAM 🔴超強 ↑加速；動能 +210.6% 不扣分，倉位 5-10%、停損 -5%）｜法人 TOP50 綜合第 3（+19K／+35億）｜Q2 EPS YoY+1,962%、毛利率 QoQ+12.9pp +5｜外資持股比週增 +0.73% +5｜反轉 Level 0、近5日外資 +66K。⚠️ 10 日賣超 6 天 -5；10 日累計僅 +4.9K（投信 -58K 與外資 +62K 對作）；⚠️ 營收快取落後 2026-02，本因子未採計",slp=-5,tgt_pct=8),
rec("2393","億光","LED/光電元件（industry_chains 未分類）",66.3,87,"10-15%",
 "訊號A L2 +10、動能 -50.8% +15｜Q2 EPS YoY+70% +5｜法人 TOP50 第 46（佔成交 59.2%）｜反轉 Level 0、10日累計 +5K｜財訊：成本壓力和緩＋新產能，H2 優於 H1。⚠️ industry_chains 未分類（產業邏輯僅 7/20）；⚠️ 營收快取落後 2026-04（原 -5 作廢，本因子未採計）；季線下（+0 修正）"),
rec("2371","大同","電動車-充電系統/重電（industry_chains: 電動車/tier_1 充電系統）",27.55,86,"10-15%",
 "訊號A L2 +10、動能 -15.0% +10｜Q2 EPS YoY+336% +5｜反轉 Level 0、10日累計 +7.5K、7買3賣｜月線乖離 +6.8%、季線上。⚠️ 無明顯對應催化（時事僅 12）；TOP50 排名 40（法人維度 11/25）；5 日漲幅 TOP50 表載 +5.0%、Yahoo 刷新 +2.9%（採刷新值，未套用已小漲扣分）；⚠️ 營收快取落後 2026-02，本因子未採計；當日時事資料無提及"),
rec("2892","第一金","金融-銀行（industry_chains: 聯準會利率／台灣ETF tier_from_tracker）",33.3,72,"5-10%",
 "🔥 超強催化覆寫（聯準會利率政策 🔴超強、台灣央行最快 9 月升息；動能 +500% 不扣分，倉位 5-10%、停損 -5%）｜真連買 8 天（8買2賣）、10日累計 +59K、近5日 +52K（投信 +44K 主導）｜法人 TOP50 第 13（佔成交 39.4%）｜反轉 Level 0。⚠️ 月線乖離 -3.5%（價格位置 8/15）；⚠️ 金融業半年報申報期限 8/31 尚未公布（EPS 快取 2025-12-31，本因子視為 0，公布日落在持有期內）；⚠️ 營收快取落後 2026-06，本因子未採計；當日時事資料無提及",slp=-5,tgt_pct=8),
rec("2426","鼎元","光通訊-PD/LED 封裝（industry_chains: 光通訊 tier_from_tracker）",74.8,72,"5%",
 "🔥 超強催化覆寫（光通訊 🔴超強 ↑加速：SK 海力士 CPO 路線圖、聯亞矽光放量；動能 +500% 不扣分，倉位 5%、停損 -5%）｜Q2 轉虧為盈、EPS YoY+414%、毛利率 QoQ+2.9pp +5｜法人 TOP50 第 25（+3,715）、反轉 Level 0｜月線乖離 +19%、季線上（價格位置 15/15）。⚠️ 08-20 跳空漲停，5 日 +9.0% 已小漲 -10；⚠️ 處置預警 🟡（6 日 +8.6%／當日週轉率 9.6% 接近 10% 門檻，今日再達標即可能列注意股）；外資持股比週減 -0.18% -3；⚠️ 營收快取落後 2026-05，本因子未採計",slp=-5,tgt_pct=8),
]
T={"date":"2026-08-21","settings":{"stop_loss_pct":-10,"settlement_days":10,"override_stop_loss_pct":-5},
 "market_context":{"regime":"多頭","regime_score":3,"vix":16.01,"defense_ratio":"0-15%","taiex_vs_ma240":29.91,"sox":0.53,"nasdaq":-1.0,"us_leader_alerts":"無預警（Level 3/2/1 皆 0 檔）","catalyst_strength":"超強（DRAM／光通訊／ASIC／軍工／中東 皆 🔴）"},
 "disposition_lists":{"source":"TWSE announcement/punish + TPEx tpex_disposal_information（2026-08-21 盤前）",
   "twse_disposal":["6225 天瀚｜08/20~08/26｜第二次處置","7795 長廣｜08/18~08/24｜處置","8033 雷虎｜08/18~08/24｜處置（軍工鏈，禁止進場）","911608 明輝-DR｜08/18~08/24｜處置"],
   "tpex_disposal":["3490 單井｜08/20~08/26｜連續3日達注意","5475 德宏｜08/20~08/26｜30日內再處置","3498 陽程｜08/19~08/25｜連續3日達注意","6716 應廣｜08/17~08/21｜連續3日達注意","3163 波若威｜08/13~08/21｜連續5日注意","4931 新盛力｜08/13~08/21｜連續3日達注意"],
   "twse_attention":[],"pool_hits":[],
   "self_computed_warnings":["3653 健策｜連續達標 2 天｜最快明日處置（6日+25.3%）","2615 萬海｜連續達標 1 天｜最快剩 2 天（6日+30.3%）","2426 鼎元｜🟡接近注意門檻（週轉9.6%）— 今日推薦已標註","2634 漢翔｜🟡接近（6日+17.2%）","2464 盟立／2455 全新／6770 力積電｜🟡接近"]},
 "recommendations":R,
 "opening_exits":[
  {"stock_code":"2301","stock_name":"光寶科","recommend_date":"2026-08-14","recommend_price":269.5,"last_close":267.0,"reason":"反轉 Level 4：08-20 賣超 -5,809 張，佔日均量 22.9%（≥8%，非分母效應）；近5日外資 -1,638","rule":"盤前 L4 開盤出場，入帳價以今日收盤價為準"},
  {"stock_code":"3017","stock_name":"奇鋐","recommend_date":"2026-08-14","recommend_price":3200.0,"last_close":2985.0,"reason":"反轉 Level 4：08-20 賣超 -308 張，佔日均量 10.3%（≥8%）；賣超÷10日累計 6.2%；現價 -6.7% 距停損 3.5%","rule":"盤前 L4 開盤出場"},
  {"stock_code":"2881","stock_name":"富邦金","recommend_date":"2026-08-19","recommend_price":129.5,"last_close":128.0,"reason":"反轉 Level 4：08-20 賣超 -1,943 張，佔日均量 10.5%（≥8%）；卷宗：聯準會主題 ⚠️營收未跟上（7 月營收 YoY-79%）","rule":"盤前 L4 開盤出場"},
  {"stock_code":"2464","stock_name":"盟立","recommend_date":"2026-08-20","recommend_price":181.5,"last_close":180.5,"reason":"反轉 Level 4：08-20 賣超 -1,017 張，佔日均量 8.2%（≥8% 門檻邊緣，但賣超÷10日累計 8.5% 亦落在真出貨帶）；🟡處置預警","rule":"盤前 L4 開盤出場"},
  {"stock_code":"2030","stock_name":"彰源","recommend_date":"2026-08-20","recommend_price":21.5,"last_close":21.85,"reason":"反轉 Level 4：08-20 賣超 -544 張，佔日均量 14.1%（≥8%）","rule":"盤前 L4 開盤出場"},
  {"stock_code":"2455","stock_name":"全新","recommend_date":"2026-08-20","recommend_price":396.5,"last_close":412.0,"reason":"反轉 Level 4：08-20 賣超 -2,277 張，佔日均量 14.0%；10 日累計 -1,330 轉負（不受待複核保護）；🟡處置預警（週轉 8.8%）","rule":"盤前 L4 開盤出場"}],
 "manual_review":[],
 "carry_over":[
  {"stock_code":"1504","stock_name":"東元","recommend_date":"2026-08-14","recommend_price":70.4,"stop_loss":63.36,"holding_days":"D4/10","today_score":89,"note":"⏳沿用進行中追蹤（D4/10），維持原進場價 70.4／停損 63.36 不變，不重複建倉。訊號A L2、真連買 6 天、Q2 EPS 創高；08-31 香港法說會（10 天後）"},
  {"stock_code":"1216","stock_name":"統一","recommend_date":"2026-08-14","recommend_price":76.3,"stop_loss":68.67,"holding_days":"D4/10","today_score":85,"note":"⏳沿用（D4/10），原進場價 76.3／停損 68.67。真連買 10 天、10日累計 +74K、訊號A L2"},
  {"stock_code":"2353","stock_name":"宏碁","recommend_date":"2026-08-20","recommend_price":30.9,"stop_loss":27.81,"holding_days":"D0/10","today_score":85,"note":"⏳沿用（D0/10），原進場價 30.9／停損 27.81。今日不在 TOP50 買超且月線乖離 +2.6% → 法人現身門檻未過，若為新股不推薦；近5日外資 -2,741"},
  {"stock_code":"3189","stock_name":"景碩","recommend_date":"2026-08-18","recommend_price":905.0,"stop_loss":814.5,"holding_days":"D2/10","today_score":65,"note":"⏳沿用（D2/10），原進場價 905／停損 814.5。Level 0 但 10 日累計 -398、近5日外資 -1,596；現價 851 距停損 4.3% → 最高警戒、不加碼"},
  {"stock_code":"2618","stock_name":"長榮航","recommend_date":"2026-08-20","recommend_price":41.6,"stop_loss":37.44,"holding_days":"D0/10","today_score":64,"note":"⏳沿用（D0/10），原進場價 41.6／停損 37.44。Q2 EPS YoY-43% -5、油價續漲逆風、動能 +459%；今日分數 <70 不加碼"},
  {"stock_code":"2606","stock_name":"裕民","recommend_date":"2026-08-18","recommend_price":68.3,"stop_loss":61.47,"holding_days":"D2/10","today_score":56,"note":"⏳沿用（D2/10），原進場價 68.3／停損 61.47。5 日 +7.2% 已小漲 -10、動能 +53.6% -10；續抱不加碼"},
  {"stock_code":"2867","stock_name":"三商壽","recommend_date":"2026-08-17","recommend_price":9.75,"stop_loss":8.78,"holding_days":"D2/10","today_score":44,"note":"⏳沿用（D2/10），原進場價 9.75／停損 8.78。不在 TOP50、動能 +85% -10、金融半年報未公布；續抱不加碼"},
  {"stock_code":"2603","stock_name":"長榮","recommend_date":"2026-08-18","recommend_price":231.5,"stop_loss":219.92,"holding_days":"D2/10","today_score":None,"note":"⏳沿用（D2/10），原進場價 231.5／停損 219.92（-5%）。5 日 +14.2% 已大漲（>10%）今日不評分；現價 246 距目標 250 僅 1.6%；籌碼健康（+17K，真連買 6 天）"},
  {"stock_code":"2637","stock_name":"慧洋-KY","recommend_date":"2026-08-19","recommend_price":88.7,"stop_loss":79.83,"holding_days":"D1/10","today_score":None,"note":"⏳沿用（D1/10），原進場價 88.7／停損 79.83。反轉 Level 2（-223 張，佔 2.4%，前期 +2,208）→ 12:30 複核、不加碼；現價 94.7 距目標 3.0%；⚠️ EPS 快取 2026-03-31，Q2 申報期限 8/14 已過仍未更新"}],
 "portfolio_add_evaluation":[
  {"symbol":"2330","name":"台積電","cost":2070,"price":2375.0,"pnl_pct":14.73,"score":108,"verdict":"🟡 續抱不加碼","note":"分數 ≥80 但不在當日 TOP50 買超且月線乖離 +0.71% → 法人現身門檻未過；近5日外資 -8.5K；⚠️ 08/24（D3）傑富瑞芝加哥法說會，雙向波動"},
  {"symbol":"2313","name":"華通","cost":262.2,"price":217.5,"pnl_pct":-17.05,"stop_loss":235.98,"score":77,"verdict":"🟡 續抱觀察｜🔴 現價已低於個人停損 235.98","note":"法人 TOP50 第 14（+10K）、光通訊 🔴；但 10 日 3買7賣（法人上限 15）、累計 -4.3K"},
  {"symbol":"1301","name":"台塑","cost":60.085,"price":57.8,"pnl_pct":-3.8,"stop_loss":54.08,"score":80,"verdict":"🟡 續抱不加碼","note":"法人現身門檻未過（不在 TOP50、乖離 +1.35%）；近5日 -4,042；集團 1303 南亞今日 14:00 法說會；卷宗 16 筆 mentions 多為『台塑化／台塑集團』子字串誤中"},
  {"symbol":"2337","name":"旺宏","cost":164.0,"price":122.0,"pnl_pct":-25.61,"stop_loss":147.6,"score":68,"verdict":"⚠️ 留意減碼｜🔴 現價已低於個人停損 147.6","note":"反轉 Level 2（-1,927 張）、近5日 -38K（投信 -21K）；DRAM 🔴 主題支撐但籌碼轉弱"},
  {"symbol":"3090","name":"日電貿","cost":285.0,"price":172.0,"pnl_pct":-39.65,"stop_loss":256.5,"score":None,"verdict":"⚠️ 留意減碼｜🔴 現價已低於個人停損 256.5","note":"❓狀態不明（累計 -9,658、2買8賣）、動能 +122% 無覆寫 → 不評分"},
  {"symbol":"6770","name":"力積電","cost":81.4,"price":67.3,"pnl_pct":-17.32,"stop_loss":73.26,"score":None,"verdict":"🛑 反轉 Level 4｜🔴 現價已低於個人停損 73.26","note":"08-20 賣超 -35,952 張（賣超榜第 1，佔日均量 21.8%）、近5日 -50K；🟡處置預警"},
  {"symbol":"4938","name":"和碩","cost":85.0,"price":89.7,"pnl_pct":5.53,"stop_loss":76.5,"score":None,"verdict":"🛑 反轉 Level 4","note":"08-20 賣超 -2,315 張（佔日均量 28.8%）、近5日 -8,989（外資 -19K）"}],
 "data_quality_flags":["pattern_today.json 日期 2026-08-17（4 天前）> 3 天 → 模式追蹤加減分跳過","營收快取：8 檔推薦中 7 檔落後（2408/2344/2027/2371 為 2026-02、2393 2026-04、2426 2026-05、2892 2026-06），僅 2002 為 2026-07","EPS：金融股快取 2025-12-31（半年報期限 8/31 未到）；2637/5871/4977 為 2026-03-31（Q2 期限 8/14 已過）","上櫃股 3081/3234/3363/5483/8299/3324 T86 無資料，reversal_alert 回報數據不足，不可視為安全","fetch_us_asia_markets 與 us_leader_alert 並行競速致 1.5 首跑失敗，已重跑成功","MI 日期目錄僅有 raw_for_claude.md，topic_tracker/industry_signals/market_regime 改由 repo 根目錄 outputs/ 取得（皆為 2026-08-21）","tier_from_tracker 本次新增 0 筆"],
 "today_events":["08-21 14:00 1303 南亞 線上法說會（推薦 2408 之母公司）","08-21 11:10 6285 啟碁／14:30 2605 新興 法說會（非持倉）","08-24 台積電美國法說會（持倉 2330，D3）","08-25 2201 裕隆除權息（已排除）","08-27 NVDA 財報（A 類，⚡佈局窗口 D6，財報日曆台股受益鏈欄為空，未套用 +2）"],
 "track_b_recommendations":[],"track_b_observations":[],"removed_stocks":[],"tomorrow_recommendations":[]}
json.dump(T,open('data/tracking/tracking_2026-08-21.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in R: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['target_price'],r['stop_loss'],r['stop_loss_pct'],r['score'])
