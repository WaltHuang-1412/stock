import json
T='2026-10-05'
def L(p): return json.load(open(p,encoding='utf-8'))
prev=L('data/tracking/tracking_2026-10-02.json')
pool={o['code']:o for o in L(f'data/{T}/pool_table.json')}
src={}
for d in ['2026-10-01','2026-10-02']:
    for r in L(f'data/tracking/tracking_{d}.json')['recommendations']:
        if r.get('recommend_date',d)==d: src[r['stock_code']]=(d,r)

# ---- 已決事項（Step 4-0）----
exits=[]
for r in prev['tomorrow_opening_exits']:
    r=dict(r); r['status']='已決事項（v8.3.7 Step 4-0）：原樣抄入、不重評；入帳價用 10-05 收盤（v8.3.2）'
    o=pool[r['stock_code']]; r['premarket_rescan']=f"10-05 盤前重掃仍為 L{o['level']}（{(o['alert'] or '')[:40]}）→ 無衝突"
    exits.append(r)

# ---- 新推薦 ----
o=pool['1326']
rec=dict(stock_code='1326',stock_name='台化',industry='塑化 tier_0（industry_chains；另登錄 中東地緣政治 tier_from_tracker）',
    recommend_date=T,recommend_price=71.7,target_price=77.4,stop_loss_pct=-10,stop_loss=64.53,settlement_days=10,
    position='5-10%（🔥超強催化覆寫上限；建議取 5% 下緣）',score=73,rating='⭐⭐⭐',result='holding',track='A',holding_days=0,
    score_detail='五維度 83＝時事 22＋法人 23＋產業 17＋技術 10＋價位 11｜賣超 6 天 -5｜🔥超強催化覆寫 0（動能 +500%）｜5 日 +9.63% -10｜EPS +5',
    reason='🛤️軌道A｜🔴超強催化『中東地緣政治（含航運）』影響鏈直接點名 台化(1326)↑（油價高檔受惠；方向↑軍事與供給風險升高 +1）｜🔥超強催化覆寫：動能 +500% >100%，因 Topic Tracker 🔴區成立改降級不排除 → 倉位上限 5-10%｜10-02 T86 +23,062 張（外資 +22,015／投信 +85；avg_rank 6.0、佔成交 41.0%；<30K 不觸過量買超）｜10 日累計 +24K、買 4 賣 6（賣超 6 天 -5）、真連續買超 1 天｜近5天外資 +20K｜5 日 +9.63%（-10，貼近 10% 不評分線）｜vs MA20 +4.33%（在 TOP50 買超名單內，法人現身門檻 ✅）｜反轉 L0｜EPS Q2 YoY +190% +5｜8 月營收 YoY +31.7%（未達回檔條件，不加分）｜卷宗：3 日內事件 0、提及 8 處，無矛盾｜⚠️ 本檔 10-01 曾推薦（69.7）、D0 即轉 L4（10-01 T86 -10,572 張＝47.1%），10-02 依已決事項出場（收 71.7，+2.87%）；10-02 T86 單日翻買 +23,062 張 → 籌碼兩日內方向相反，延續性未確認｜⚠️ 🔥覆寫推薦 09-24～10-02 共 10/10 於 D0-D1 轉 L4（未立法之統計）｜⚠️ WTI 隔夜 -0.34%（90.80），催化為地緣風險而非油價續漲')
recs=[rec]

# ---- 沿用追蹤 ----
D={'2609':1,'6257':1,'3711':1,'3035':0,'2327':0,'8150':0,'3037':0}
note={
'2609':'續抱；L0（10-02 T86 +5,135 張）；📶訊號A L2；今日重評 105 分，三項篩選全過（列榜）',
'3711':'續抱；L0（+775 張）、真連買 3 天；日月光 ADR +6.08%；今日重評 94 分，三項篩選全過（列榜）',
'3035':'續抱；L0（+1,164 張）、真連買 2 天；今日重評 83 分（5 日 +5.64% -10），三項篩選全過（列榜）',
'6257':'續抱；L0（+2,030 張，L2 解除）；②外資近 5 天 -2,770 為負（今日重評 83 分不列榜）；⚠️ 10/06 法說會（3 個交易日內）→ 法說當日不加碼',
'3037':'續抱；L0（+6,042 張）、真連買 3 天；10-02 收 1305.0 距目標 1312.0 僅 0.5%；5 日 +12.5% 已大漲（今日重評 107 分不列榜）',
'8150':'續抱；L0（+6,268 張）；⚠️ 10-02 收 127.0 已越目標 124.5（D0 不結算）→ 今日收盤 ≥124.5 即盤後結算 success；⚠️ 處置預警連續達標 3 天、最快今日公告處置；5 日 +18.7%（今日重評 104 分不列榜）',
'2327':'續抱；L0（+2,497 張）；10-02 收 626.0（+4.0%）；今日重評 64 分（<70，不列榜）',
}
carry=[]
for c in ['2609','3711','3035','6257','3037','8150','2327']:
    d,r=src[c]; p=pool[c]
    e={k:r[k] for k in ['stock_code','stock_name','industry','recommend_price','target_price','stop_loss_pct','stop_loss','settlement_days','score']}
    e.update(recommend_date=d,result='holding',holding_days=D[c],holding_days_label=f'D{D[c]}/10',today_score=p['total'],
        last_close=p['close'],return_pct_at_close=round((p['close']/r['recommend_price']-1)*100,2),
        reversal_level=f"L{p['level']}",holding_status=note[c],source_file=f'tracking_{d}.json')
    carry.append(e)
z=[x for x in prev['carry_over_recommendations'] if x['stock_code']=='2867'][0]
z={k:z[k] for k in ['stock_code','stock_name','industry','recommend_date','recommend_price','target_price','stop_loss_pct','stop_loss','settlement_days','score','result']}
z.update(holding_days='⏸️ 凍結',holding_status='⚠️ 序列停滯（末日 2026-08-19，市場最新 2026-10-02）凍結判定：不結算、不出場、D 不推進（v8.3.8）',today_score=None,source_file='tracking_2026-08-17.json')
carry.append(z)

t=dict(date=T,settings=dict(stop_loss_pct=-10,settlement_days=10),
 market_context=dict(nasdaq=1.19,sp500=0.73,dow=0.49,sox=2.4,nvda=1.34,micron=-2.05,wdc=-10.22,amd=2.95,asml=3.25,amat=2.03,lrcx=2.17,klac=3.27,avgo=3.35,dell=3.84,smci=4.22,tsla=4.65,
    tsm_adr=2.96,umc_adr=4.2,ase_adr=6.08,vix=15.31,wti=-0.34,gold=0.19,nikkei=-0.94,kospi=0.46,hsi=-2.6,usdtwd=31.85,
    us_session='美股 10-02（五）收盤；10-03／10-04 假日快照為同一場行情，無新增美股交易日',
    taiex_prev_close=48475.74,taiex_as_of='2026-10-02',regime='多頭',regime_score=4,vs_ma20=2.93,vs_ma60=6.69,vs_ma240=30.62,
    institutional_1002='三大法人合計 +95.58 億（外資 +26.22 連買 3 日／投信 +49.10／自營 +20.26）；近 5 日合計 -445.92 億',
    t86_date='2026-10-02',cumulative_summary='gap 3 天、美股 1 個交易日；無持續性催化訊號（sustained_catalysts 空）'),
 weekly_audit=dict(run='2026-10-05（週一）audit_industry_chains.py',industries=299,stocks=1972,red_delisted=31,cold_industries=274,
    action='未執行 --fix：31 筆「下市/停牌」含多筆代碼誤植與上櫃股（Yahoo 查無報價 ≠ 下市），自動移除有誤刪風險，留待人工審核；今日推薦與沿用名單皆不在 31 筆內'),
 prior_decisions_executed=dict(source='tracking_2026-10-02.json → tomorrow_opening_exits（5 筆，機械讀取）；removed_stocks 無「次日開盤出場」標記',items=exits),
 opening_exits_today=exits,
 pending_review_v833=[],
 stop_loss_check_v8310=[
  dict(stock_code='2330',stock_name='台積電',close_date='2026-10-02',close=2500.0,result='無 stop_loss 欄位（零股 0.15）；另為已決事項鐵律③ L4 開盤出場'),
  dict(stock_code='6770',stock_name='力積電',close_date='2026-10-02',close=76.5,stop_loss=73.26,result='✅ 未觸發（差 4.4%）；10-02 T86 +49,897 張 L0；⚠️ 龍頭預警 Level 3（WDC -10.22%）→ 最高警戒、不加碼'),
  dict(stock_code='2337',stock_name='旺宏',close_date='2026-10-02',close=122.0,stop_loss=147.6,result='🛑 觸及停損（流程紀錄已出場，yaml 未更新；若實際仍持有 → 鐵律①開盤出場）'),
  dict(stock_code='2313',stock_name='華通',close_date='2026-10-02',close=226.0,stop_loss=235.98,result='🛑 觸及停損（同上）'),
  dict(stock_code='3090',stock_name='日電貿',close_date='2026-10-02',close=173.5,stop_loss=256.5,result='🛑 觸及停損（同上）'),
  dict(stock_code='1301',stock_name='台塑',close_date='2026-10-02',close=68.3,stop_loss=54.08,result='✅ 未觸發；10-02 已決事項出場日（流程紀錄），yaml 未更新'),
  dict(stock_code='4938',stock_name='和碩',close_date='2026-10-02',close=89.2,stop_loss=76.5,result='✅ 未觸發；惟已決事項鐵律③ L4（23.5%）→ 開盤出場')],
 stop_loss_check_conclusion='新觸發 0 筆；2337／2313／3090 為既有重複輸出（yaml 未更新）',
 series_alignment_check_v838=dict(expected_last_day='2026-10-02',stale=['2867 三商壽（末日 2026-08-19）'],ok='其餘 11 筆末日皆 2026-10-02',query_failed=0),
 two_day_drawdown_check=dict(window='09-30 收盤→10-02 收盤',triggered=[],worst='2379 瑞昱 -0.79%／4938 和碩 -0.67%'),
 holdings_reversal_scan=dict(scanned=['2867','2609','6257','3711','2330','3035','2379','2327','8150','3037','3231','2344','6770','2337','2313','3090','1301','4938'],
    L4=['2330 台積電 24.9%（已決出場）','3231 緯創 68.8%（已決出場）','2344 華邦電 11.4%（已決出場）','2379 瑞昱 9.2%（已決出場）','4938 和碩 23.5%（yaml 持倉，已決出場）'],
    L0=['2609 陽明','6257 矽格','3711 日月光投控','3035 智原','2327 國巨*','8150 南茂','3037 欣興','6770 力積電','2337 旺宏','2313 華通','3090 日電貿','1301 台塑'],
    new_exits=0,frozen=['2867 三商壽']),
 settlement_today=[],
 yesterday_settlement='10-02 結算 7 筆 6 勝 1 敗：5876 上海商銀 -1.71% fail／2412 中華電 +1.74%／2395 研華 +4.53%／1303 南亞 +5.26%／1326 台化 +2.87%／6505 台塑化 +2.77%／1301 台塑 +0.29%',
 recommendations=recs,
 carry_over=[c['stock_code'] for c in carry],
 carry_over_recommendations=carry,
 carry_over_note='沿用追蹤 8 筆（不含今日開盤出場 4 筆推薦部位），進場價/停損照抄來源 tracking_{推薦日}.json；D 值照抄 settlement_checker（盤前以 10-02 收盤計）',
 disposition_stocks=dict(
    twse_official=['2030 彰源｜10/02~10/08｜第一次處置（連續三次）','2455 全新｜09/23~10/05｜第二次處置（連續五次及當沖標準）','3016 嘉晶｜10/01~10/12｜第一次處置（連續三次及當沖標準）','3055 蔚華科｜10/01~10/12｜第二次處置（連續五次及當沖標準）','3167 大量｜10/05~10/12｜第一次處置（10 日內 6 次）（今日新增）','3443 創意｜09/29~10/05｜第一次處置（連續三次）（在候選池 → 排除）','6526 達發｜09/30~10/06｜第一次處置（連續三次）','8996 高力｜10/05~10/12｜第二次處置（10 日內 6 次）（今日新增）'],
    tpex_official=['8084 巨虹｜10/02~10/08｜連續3個營業日','8227 巨有科技｜10/02~10/08｜連續3個營業日','2221 大甲｜10/01~10/12｜連續3個營業日及沖銷標準','3219 倚強科｜10/01~10/07｜連續3個營業日','7792 安葆｜09/30~10/06｜連續3個營業日','3374 精材｜09/29~10/05｜10 日內 6 日','4542 科嶠｜09/29~10/05｜連續3個營業日','4979 華星光｜09/29~10/05｜連續5個營業日','6218 豪勉｜09/23~10/05｜連續3個營業日及沖銷標準'],
    twse_attention=[],
    self_warning=['8150 南茂｜6 日 +20.4%／30 日 +45.5%／週轉 14.1%｜連續達標 3 天｜最快今日處置（沿用追蹤中）','1709 和益｜6 日 +27.3%／30 日 +79.7%｜連續達標 3 天｜最快今日處置','3026 禾伸堂｜週轉 10.1%｜連續達標 2 天｜最快明日處置','2492 華新科｜6 日 +16.2%／週轉 11.3%｜連續達標 2 天｜最快明日處置','2340 台亞｜6 日 +34.2%／30 日 +53.0%｜連續達標 2 天｜最快明日處置','3042 晶技｜6 日 +25.6%／週轉 12.6%｜連續達標 2 天｜最快明日處置','8046 南電｜6 日 +25.3%｜連續達標 2 天｜最快明日處置','6672 騰輝電子-KY｜6 日 +45.4%／週轉 20.1%｜連續達標 2 天｜最快明日處置','6213 聯茂｜6 日 +25.8%／30 日 +41.1%｜連續達標 1 天｜最快剩 2 天處置','1727 中華化｜30 日 +32.7%／週轉 27.8%｜連續達標 6 天｜最快剩 4 天處置','2481 強茂／2409 友達／9933 中鼎／6120 達運／3673 TPK-KY／2342 茂矽｜接近注意門檻']),
 module_a_result=dict(l3=['2892 第一金','2412 中華電','2408 南亞科','2303 聯電','3045 台灣大','1102 亞泥'],
    l2=['6770 力積電','1718 中纖','2609 陽明','1312 國喬','3035 智原','2855 統一證','1314 中石化','2618 長榮航','2884 玉山金','2379 瑞昱','2330 台積電'],
    l1=['2886 兆豐金','2337 旺宏','2610 華航','1402 遠東新'],entered=[],
    l3_excluded=['2408 南亞科（123 分；🚫 龍頭預警 Level 3 WDC -10.22% 直接排除）','2303 聯電（121 分；②外資近 5 天 -20K 為負）','2412 中華電（100 分；①催化未對齊）','2892 第一金（92 分；①未對齊＋②外資近 5 天 -4,211）','3045 台灣大（91 分；①未對齊＋法人現身門檻未過）','1102 亞泥（81 分；①未對齊＋法人現身門檻未過）'],
    note='L2 之 2609 陽明／3035 智原為沿用追蹤（+10 已計入今日重評）；6770 力積電 Level 3 排除；2330／2379 L4 已決出場'),
 module_b_result=dict(preposition=111,in_top50=30,moved=44,passed=[],
    excluded=['3661 世芯-KY（🟢早期；累計 -263 為負）','2449 京元電子（🟢早期；L4）','2313 華通（🟢早期；累計 -10,153 為負）','6488 環球晶（🟢早期；上櫃，數據不足）','2383 台光電（🟢早期；累計 -2,032 為負、1 買 9 賣）','3131 弘塑（🟢早期；上櫃，數據不足）','3583 辛耘（🟢早期；累計 -161 為負）','3680 家登（🟢早期；上櫃，數據不足）','2382 廣達（🟡中期；L4、累計 -4,687）','2356 英業達（🟡中期；L4、0 買 10 賣）'],
    final=0,final_note='修正週末重複計數後重跑（見 script_fixes）；修正前名單（3008 大立光等蘋果鏈／電動車鏈 10 檔，僅 1513 中興電過基礎篩選、評分 68 不推薦）亦為 0 檔'),
 us_leader_alerts=dict(total=2,level3=1,level2=0,level1=1,detail='Level 3 Western Digital -10.22% → NAND/儲存：2408 南亞科／2344 華邦電／2337 旺宏／6770 力積電 直接排除；Level 1 Micron -2.05% → 2408／1303 南亞／2344／2337／5347 世界／6770 各 -5 分'),
 diversification=dict(recommend_count=1,industries={'塑化':['1326']},max_industry_pct=100.0,note='僅 1 檔新推薦，單一產業 100% 為寧缺勿濫之必然結果；未為湊分散拉入未過門檻標的'),
 defense_ratio=dict(vix=15.31,catalyst='超強',defense='0-15%',offense='85-100%'),
 watchlist=['2303 聯電（121 分；📶訊號A L3、ADR +4.20%；②外資近 5 天 -20K 為負）','2404 漢唐（90 分；②外資近 5 天 -910 為負）','1301 台塑（77 分；動能 +500% 且未被🔴影響鏈直接點名 → 覆寫不採）','3189 景碩（74）／8046 南電（74）／6196 帆宣（71）：其餘門檻全過，惟自算 5 日 +15.9%／+20.7%／+12.6% >10% 已大漲','2615 萬海（79 分；③反轉狀態不明）'],
 tier_from_tracker_added=0,
 pattern_tracker=dict(file_date='2026-10-05',cold_applied=['2337 旺宏 記憶體-NOR Flash 18.2% -5','2002 中鋼 鋼鐵 tier_0 30.0% -5','1102 亞泥 水泥 30.0% -5','2317 鴻海 AI伺服器 tier_1／iPhone 組裝 33.3% -3','1310 台苯／1312 國喬 石化（ABS、SM）33.3% -3'],note='1326 台化屬「塑化 tier_0」hot（87.5%，n=8）僅標註不加分'),
 script_fixes=['catalyst_theme_detector.py get_available_dates()：週六／週日假日快照與週一盤前的 us_asia_markets.json 為同一場美股行情，原邏輯逐檔累計 → 同一日漲跌重複計 3 次（WDC -10.22% 累計成 -29.38%、Tesla 單日 +4.65% 判「連漲 3 天」）。改為美股欄位相同者只計一次；驗證：重跑後 lookback_dates 不含 10-03／10-04，WDC 累計 -12.4%、Tesla 連漲 1 天'],
 data_quality=dict(revenue='111/112 檔 2026-08（新鮮）；2867 三商壽 2026-07 未採計',eps='--update-cache 已跑；102 檔 2026Q2、10 檔金融停於 2025Q4 → EPS 因子視為 0',
    foreign_ratio='as_of 10-02×10／10-01×58／09-30×17／09-29×26，皆本週期內照常採計；2867 三商壽 08-31 stale 不採計',
    dossier='來源三項 ok（法說會、除權息為 cache）',tw_market_news='證交所新聞 10、公告 8、鉅亨網 1、經濟日報法說 1；MOPS／Yahoo 0 則 → 覆蓋有限',
    d5_fill='非 TOP50 個股無 5day_change 欄 → 本次以 get_close_series 自算補上「已大漲」檢查（_d5.json），攔下 3189 景碩／8046 南電／6196 帆宣'),
 removed_stocks=[],tomorrow_opening_exits=[],track_b_recommendations=[],track_b_observations=[])
json.dump(t,open(f'data/tracking/tracking_{T}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok',len(carry),[ (c['stock_code'],c['recommend_date'],c['recommend_price'],c['stop_loss'],c.get('today_score')) for c in carry])
