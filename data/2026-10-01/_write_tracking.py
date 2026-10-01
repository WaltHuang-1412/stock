import json
T='2026-10-01'
pt={o['code']:o for o in json.load(open(f'data/{T}/pool_table.json',encoding='utf-8'))}
y=json.load(open('data/tracking/tracking_2026-09-30.json',encoding='utf-8'))
def tp(p): return round(p*1.08/0.5)*0.5 if p>=100 else round(p*1.08*20)/20
def detail(o):
    ms='｜'.join(f"{k} {v:+d}" for k,v in o['mods'])
    return f"五維度 {o['sub']}＝時事 {o['news']}＋法人 {o['inst']}＋產業 {o['ind']}＋技術 {o['tech']}＋價位 {o['price']}｜{ms}｜{o['note']}"
def base(o):
    return (f"09-30 T86 {o['total_k']:+,} 張（avg_rank {o['avg_rank']}、佔成交 {o['buy_ratio']:.1f}%）｜10 日累計 {o['cum']}、買{o['bs'].split('/')[0]}賣{o['bs'].split('/')[1]}、真連續買超 {o['consec']} 天｜近5天外資 {o['f5']}｜動能 {o['mom']}｜vs MA20 {o['vs_ma20']:+.2f}%｜反轉 L0｜8 月營收 YoY {o['rev_yoy']:+.1f}%")
X={
'2609':('陽明','航運（industry_chains 無正式 tier；tier_from_tracker「中東地緣政治（含航運）」→ 產業邏輯以 13-16 分計）','⭐⭐⭐⭐⭐','10-15%',
  '🛤️軌道A｜🔴超強催化『中東地緣政治（含航運）』影響鏈直接點名 陽明(2609)↑ 北美線高檔｜📶訊號A L2 +10｜動能 -81.6% 佈局完成 +15｜營收 YoY +56.2%＋近5日回檔 → +5｜EPS Q2 +5｜⚠️ 本股 09-23 推薦於 09-30 依 09-29 L4（-6,231 張）開盤出場（-2.30%），09-30 T86 隨即翻買 +6,814 張 → 屬市場級巨賣→回補的 beta 型態，倉位建議取下緣｜⚠️ 真連續買超僅 1 天｜卷宗：事件 0、提及 11 處（運價吃緊、8 月營收），無矛盾'),
'6257':('矽格','封測（industry_chains「AI伺服器」tier_from_tracker → 產業邏輯以 13-16 分計）','⭐⭐⭐⭐⭐','10-15%',
  '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』（封測，未直接點名）｜📶訊號A L2 +10｜動能 -88.6% 佈局完成 +15｜EPS Q2 +5｜⚠️ 外資持股比週減 -3｜⚠️ 10/06 法說會（凱基聯合法說，3 個交易日內；法說當日不加碼，持有期跨越事件有雙向波動風險）｜⚠️ 當日時事資料無提及（mentions=0），推薦依據為法人籌碼＋訊號A｜⚠️ 真連續買超僅 1 天（09-29 為賣超）'),
'1301':('台塑','塑化 tier_0 塑化龍頭（industry_chains；另登錄 中東地緣政治 tier_from_tracker）','⭐⭐⭐⭐','5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
  '🛤️軌道A｜🔴超強催化『中東地緣政治』塑化鏈（知識庫登錄、今日影響鏈未直接點名）＋⚪「塑化股逆勢走強」點名 台塑(1301)↑（外資連 3 買、電子級硫酸/鹽酸合資）｜外資 +29,049／投信 +486 同步｜🔥超強催化覆寫（動能 +500%）｜⚠️過量買超 -5（單日 30,582 張 ≥30K、真連買 3 天 <7；回測 5 日勝率 35.2%）｜EPS Q2 +5｜卷宗：事件 0、提及 19 處，無矛盾｜本股 my_holdings.yaml 仍列 1 張（流程紀錄已依 L4 出場、yaml 未更新）→ 若實際仍持有即為「加碼評估：可加碼 5-10%」'),
'1326':('台化','塑化 tier_0 化纖（industry_chains；另登錄 中東地緣政治 tier_from_tracker）','⭐⭐⭐','5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
  '🛤️軌道A｜🔴超強催化『中東地緣政治』影響鏈直接點名 台化(1326)↑ 油價高檔受惠｜🔥超強催化覆寫（動能 +241%）｜⚠️ 10 日買 3 賣 7、累計僅 +1,888 → 法人分數上限 15，籌碼以 09-30 單日買超為主｜EPS Q2 +5｜卷宗：事件 0、提及 11 處，無矛盾'),
'6505':('台塑化','塑化／煉油（industry_chains「塑化」tier_from_tracker → 產業邏輯以 13-16 分計）','⭐⭐⭐','5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
  '🛤️軌道A｜🔴超強催化『中東地緣政治』影響鏈直接點名 台塑化(6505)↑ 油價高檔受惠（Brent +1.17%、WTI +0.62%）｜外資 +3,074／投信 +6,162 同步、真連買 4 天｜🔥超強催化覆寫（動能 +390%）｜⚠️ 5 日 +9.94% -10（貼近 10% 不評分線，追高風險）｜EPS Q2 +5｜卷宗：事件 0、提及 11 處，無矛盾'),
'3711':('日月光投控','AI tier_0 CoWoS 先進封裝／半導體 tier_1 封測（industry_chains）','⭐⭐⭐','5-10%',
  '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』影響鏈直接點名 日月光投控(3711)↑＋方向↑加速 +1｜⚠️ 5 日 +6.0% -10｜EPS Q2 +5｜⚠️ 隔夜日月光 ADR -1.88%（開盤有壓）｜⚠️ 投信 09-30 賣 -401 張、真連買 1 天｜今日重大訊息 2 則（子公司環維電子取得不動產使用權、矽品取得廠務工程 → 擴產，中性偏多）｜卷宗：提及 6 處，無矛盾'),
}
recs=[]
for c in ['2609','6257','1301','1326','6505','3711']:
    o=pt[c]; nm,ind,rating,pos,why=X[c]; p=round(o['close'],2)
    recs.append({'stock_code':c,'stock_name':nm,'industry':ind,'recommend_date':T,'recommend_price':p,'target_price':tp(p),
      'stop_loss_pct':-10,'stop_loss':round(p*0.90,2),'settlement_days':10,'position':pos,'score':o['total'],'rating':rating,
      'result':'holding','track':'A','holding_days':'D0/10','score_detail':detail(o),'reason':why+'｜'+base(o)})
recs.sort(key=lambda r:-r['score'])
co={r['stock_code']:r for r in y['carry_over_recommendations']}
for r in y['recommendations']:
    co.setdefault(r['stock_code'],r)
D={'5876':'D8/10','2412':'D8/10','2395':'D8/10','1303':'D0/10','2867':'⏸️ 凍結'}
ST={'5876':'續抱：09-30 收 49.15（-1.3%），距停損 8.8%；09-30 T86 +1,334（L0）、真連買 10 天',
    '2412':'續抱：09-30 收 143.5（0.0%），距目標 6.6%；09-30 T86 +2,901（L0）；📶訊號A L2',
    '2395':'⚠️ 待複核（v8.3.3）：09-30 T86 -178 張＝7.6%（L4，<8%）且 10 日累計 +4,338 為正 → 今日不開盤出場，12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-02 開盤出場；09-30 收 726（+6.0%），距目標 740 僅 1.9%，收盤 ≥740 即 success 結算',
    '1303':'續抱：09-30 收 255.5（+3.4%），距目標 267 4.5%；09-30 T86 +9,701（健康）；今日重評 76 分（5 日 +6.7% -10），仍列表內排名、不重複建倉',
    '2867':'⚠️ 序列停滯（末日 2026-08-19）凍結判定：不結算、不出場、D 不推進（v8.3.8）'}
carry=[]
for c in ['5876','2412','2395','1303','2867']:
    r=co[c]
    carry.append({'stock_code':c,'stock_name':r['stock_name'],'industry':r['industry'],'recommend_date':r['recommend_date'],'recommend_price':r['recommend_price'],
      'target_price':r['target_price'],'stop_loss_pct':-10,'stop_loss':r['stop_loss'],'settlement_days':10,'score':r.get('score'),'result':'holding',
      'holding_days':D[c],'holding_status':ST[c],'today_score':pt[c]['total'] if c in pt else None})
exits=[dict(e,status='已決事項（v8.3.7 Step 4-0）：原樣抄入、不重評；入帳價用 10-01 收盤（v8.3.2）') for e in y['tomorrow_opening_exits']]
t={
 'date':T,'settings':{'stop_loss_pct':-10,'settlement_days':10},
 'market_context':{'nasdaq':0.24,'sp500':-0.25,'dow':-0.86,'sox':-0.00,'nvda':0.51,'micron':0.00,'micron_after_hours':'+0.37%（1069.0，Q4 財報後盤後，07:59 取樣）','intel':3.71,'avgo':-1.10,'tsm_adr':-0.16,'ase_adr':-1.88,
   'vix':16.34,'wti':0.62,'nikkei':1.94,'kospi':-0.48,'taiex_prev_close':47940.13,'taiex_as_of':'2026-09-30','regime':'多頭','regime_score':5,'vs_ma20':2.19,'vs_ma240':29.82,
   'institutional_0930':'三大法人合計 +386.57 億（外資 +296.36／投信 +77.81／自營 +12.40）；前一日 -781.87 億'},
 'prior_decisions_executed':{'source':'tracking_2026-09-30.json → tomorrow_opening_exits（09-30 盤後 16:41 產生之寫檔腳本未執行，10-01 盤前 08:0x 原樣補執行後讀取）','items':exits,
   'note':'09-30 盤後流程未完成：after_market_analysis.md／after_market_line.txt 未產出、未 commit；結算三處同步（5 筆）與 predictions 已於 14:3x 寫入。決議內容與證據檔 data/2026-09-30/_after/_reversal_holding_0930t86.txt、_reversal_holding_pre_t86.txt 一致'},
 'stop_loss_check_v8310':[
   {'stock_code':'2330','stock_name':'台積電','result':'無 stop_loss 欄位（零股 0.15）'},
   {'stock_code':'6770','stock_name':'力積電','close_date':'2026-09-30','close':75.3,'stop_loss':73.26,'result':'✅ 未觸發'},
   {'stock_code':'2337','stock_name':'旺宏','close_date':'2026-09-30','close':122.5,'stop_loss':147.6,'result':'🛑 觸及停損（流程紀錄已出場，yaml 未更新）'},
   {'stock_code':'2313','stock_name':'華通','close_date':'2026-09-30','close':226.5,'stop_loss':235.98,'result':'🛑 觸及停損（流程紀錄已出場，yaml 未更新）'},
   {'stock_code':'3090','stock_name':'日電貿','close_date':'2026-09-30','close':161.0,'stop_loss':256.5,'result':'🛑 觸及停損（流程紀錄已出場，yaml 未更新）'},
   {'stock_code':'1301','stock_name':'台塑','close_date':'2026-09-30','close':68.1,'stop_loss':54.08,'result':'✅ 未觸發'},
   {'stock_code':'4938','stock_name':'和碩','close_date':'2026-09-30','close':89.8,'stop_loss':76.5,'result':'✅ 未觸發（惟 09-30 T86 -4,059 張＝47.4% L4）'}],
 'stop_loss_check_conclusion':'新觸發 0 筆；2337 旺宏／2313 華通／3090 日電貿 為流程紀錄已出場部位重複輸出（yaml 未更新）。若實際仍持有 → 鐵律①，今日開盤出場',
 'series_alignment_check_v838':{'expected_last_day':'2026-09-30','stale':['2867 三商壽（末日 2026-08-19）'],'ok':'其餘 7 筆末日皆 2026-09-30'},
 'two_day_drawdown_check':{'window':'09-24 收盤→09-30 收盤','triggered':[],'worst':'3702 大聯大 -2.98%'},
 'opening_exits_today':exits,
 'pending_review_v833':[{'stock_code':'2395','stock_name':'研華','recommend_date':'2026-09-16','t86_date':'2026-09-30','t86_total':-178,'sell_ratio_pct_premarket':7.6,'ten_day_cum':'+4,338',
   'rule':'L4 佔比 <8% 且 10 日累計為正 → 待複核；10-01 12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-02 開盤出場','review_1_result':None,'review_2_result':None}],
 'holdings_reversal_scan':{'scanned':['5876','2395','2412','2886','3702','1303','2376','2867'],'L4':['2395 研華 7.6%（待複核）','2886 兆豐金 6.4%（已決出場）','2376 技嘉 9.4%（已決出場）'],'L2':['3702 大聯大 3.9%（已決出場）'],'L0':['5876 上海商銀','2412 中華電'],'healthy':['1303 南亞'],'unknown':['2867 三商壽（數據不足，凍結）']},
 'settlement_today':[],
 'recommendations':recs,
 'carry_over':['5876','2412','2395','1303','2867'],
 'carry_over_recommendations':carry,
 'carry_over_note':'沿用追蹤 5 筆，進場價/停損照抄來源 tracking_{推薦日}.json；D 值照抄 settlement_checker（盤前以 09-30 收盤計）',
 'disposition_stocks':{'twse_official':['2455 全新｜09/23~10/05｜連續五次及當沖標準','2468 華經｜09/22~10/02｜連續五次及當沖標準','3016 嘉晶｜10/01~10/12｜連續三次及當沖標準','3055 蔚華科｜10/01~10/12｜連續五次及當沖標準','3443 創意｜09/29~10/05｜連續三次','6168 宏齊｜09/24~10/02｜連續三次','6226 光鼎｜09/21~10/01｜連續三次及當沖標準','6526 達發｜09/30~10/06｜連續三次','6715 嘉基｜09/23~10/01｜連續三次','8021 尖點｜09/23~10/01｜連續五次'],
   'twse_attention':[],'in_pool':'候選池 88 檔無官方處置股',
   'self_calc_pool':['3717 聯嘉投控｜連續達標 1 天｜最快剩 2 天處置','2409 友達｜連續達標 1 天｜最快剩 2 天處置（6 日 +27.0%）','8150 南茂｜連續達標 1 天｜最快剩 2 天處置','6456 GIS-KY｜連續達標 4 天｜最快明日處置','1709 和益｜連續達標 1 天｜最快明日處置','3576 聯合再生｜接近注意門檻','2340 台亞｜接近注意門檻']},
 'module_a_result':{'l3':[],'l2':['2892 第一金','6770 力積電','2412 中華電','3045 台灣大','2303 聯電','2344 華邦電','2408 南亞科','1314 中石化','2337 旺宏','6257 矽格','1718 中纖','2609 陽明','2891 中信金'],'l1':['1312 國喬','2886 兆豐金','2884 玉山金'],'entered':['2609 陽明（+10）','6257 矽格（+10）']},
 'module_b_result':{'preposition':42,'in_top50':24,'moved':32,'passed':[],'excluded':['6488 環球晶（上櫃，T86 數據不足）','3661 世芯-KY（累計 -1,082 為負、動能 +115%）','2383 台光電（L3、0買10賣）','3131 弘塑（上櫃，數據不足）','3583 辛耘（L4）','3680 家登（上櫃，數據不足）','6669 緯穎（L4、0買10賣）','2356 英業達（L4、累計 -20,926）','3017 奇鋐（狀態不明、外資近5天為負）','3324 雙鴻（上櫃，數據不足）'],'final':0},
 'us_leader_alerts':{'total':0,'level3':0,'level2':0,'level1':0},
 'diversification':{'recommend_count':6,'industries':{'塑化':['1301','1326','6505'],'半導體封測':['6257','3711'],'航運':['2609']},'max_industry_pct':50.0,'note':'塑化 3/6＝50%（上限）；組合層另有沿用 1303 南亞 → 塑化合計 4 檔，不再加塑化'},
 'defense_ratio':{'vix':16.34,'catalyst':'超強','defense':'0-15%','offense':'85-100%'},
 'watchlist':[
   '2408 南亞科（113 分；🔴DRAM 點名↑、📶訊號A L2、動能 -108%；🔔美光今日財報 → 當日不開新倉，10/02 視美股正式盤反應再評估）',
   '6770 力積電（101 分；TOP50 avg_rank 3.5 +61,797 張；過量買超 -5；🔔美光今日財報 → 不開新倉）',
   '2337 旺宏（97 分；cold「記憶體-NOR Flash」18.2% -5；🔔美光今日財報 → 不開新倉）',
   '2344 華邦電（89 分；過量買超 -5；🔔美光今日財報 → 不開新倉）',
   '2303 聯電（106 分；🔴AI 點名↑、📶訊號A L2；②外資近 5 天 -8,338 為負 → 未過）',
   '1314 中石化（86 分；📶訊號A L2、動能 -98.5%；①未直接點名＋新聞「核心產品 CPL 逆風」＋營收連衰 -5 → 未過）',
   '2371 大同（85 分；⚪AI Factory 電力架構點名↑、模組化資料中心首筆訂單；催化僅「觀察中」→ ①未過）',
   '6196 帆宣（70 分；🔴AI 建廠點名↑、門檻邊緣；法人量僅千張級、09-30 才依 L4 出場 → 不列）',
   '6239 力成（91 分；②外資近 5 天 -1,676 為負）'],
 'tier_from_tracker_added':0,'tier_from_tracker_note':'本次未新增',
 'pattern_tracker':{'file_date':'2026-10-01','cold_applied':['1101 台泥 水泥 30.0% -5','2337 旺宏 記憶體-NOR Flash 18.2% -5'],'note':'推薦 6 檔皆未命中 cold／worst（半導體 tier_1 封測 57.1% 不達扣分門檻）'},
 'script_fixes':[{'file':'scripts/fetch_us_asia_markets.py','function':'_prev_trading_close','issue':'亞股盤前 Yahoo 於上一交易日棒後另附今日空棒，取 bars[-2] 拿到 regularMarketTime 當日棒 → 漲跌恆 0.00%（日經實際 +1.94%、KOSPI -0.48% 皆報 0.00%）','fix':'改取「日期 < regularMarketTime 日期」的最後一根為前收','verify':'修後重跑：日經 +1.94%（66,753.72 vs 09-29 收 65,481.27）、KOSPI -0.48%；美股各檔數值不變'}],
 'data_quality':{'revenue':'88/88 檔 2026-08（新鮮）','eps':'79 檔 2026Q2；9 檔金融停於 2025Q4 → EPS 因子視為 0','foreign_ratio':'as_of 09-24×44／09-29×32／09-30×12（皆本週內）','dossier':'來源三項 ok','micron':'MI 行事曆標「10/01 今日財報」；topic_tracker 已載 Q4 營收 542.3 億美元，盤後 +0.37%'},
 'removed_stocks':[],'tomorrow_opening_exits':[],'track_b_recommendations':[],'track_b_observations':[]}
json.dump(t,open(f'data/tracking/tracking_{T}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in recs: print(r['stock_code'],r['stock_name'],r['score'],r['recommend_price'],r['target_price'],r['stop_loss'],r['position'])
for r in carry: print('carry',r['stock_code'],r['stock_name'],r['recommend_date'],r['recommend_price'],r['target_price'],r['stop_loss'],r['holding_days'],r['today_score'])
for c in ['2609','6257','1301','1326','6505','3711','1303']: print(c,base(pt[c]))
