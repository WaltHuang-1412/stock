import json
def ld(p): return json.load(open(p,encoding='utf-8'))
def sv(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
TODAY='2026-11-10'
tp=f'data/tracking/tracking_{TODAY}.json'
t=ld(tp)
SYNC='v8.3.7 三處同步：①來源tracking ②tracking_2026-11-10.json removed_stocks ③predictions.json'
settle=[
 dict(code='2610',name='華航',rd='2026-11-03',rp=20.6,sp=22.8,res='success',days='D5/10',
  reason='收盤 22.8 ≥ 目標 22.25（settlement_checker 機械判定）；法人 11-10 加速買超 +54,953 張，L0',by='settlement_checker 目標價達成（盤後收盤價）',src='2026-11-03'),
 dict(code='1101',name='台泥',rd='2026-11-09',rp=26.75,sp=27.3,res='success',days='D1/10',
  reason='已決事項（11-09 L4 賣超-5,016張佔均量9.2%）→ 11-10 開盤出場，入帳收盤 27.3（v8.3.2）高於推薦價 26.75。⚠️揭露：11-10 T86 已翻買 +3,802 張（L0），依已決事項不重評',by='已決事項開盤出場（v8.3.7 Step 4-0；盤後收盤價入帳 v8.3.2）',src='2026-11-09'),
 dict(code='2412',name='中華電',rd='2026-11-09',rp=163.5,sp=159.5,res='fail',days='D1/10',
  reason='已決事項（11-09 L4 邊緣 6.0%）→ 11-10 開盤出場，入帳收盤 159.5（v8.2→v8.3.2）低於推薦價 163.5（未觸停損 147.15）。⚠️揭露：11-10 T86 +1,133 張（L0），邊緣值誤殺可能性高，依已決事項不重評',by='已決事項開盤出場（v8.3.7 Step 4-0；盤後收盤價入帳 v8.3.2）',src='2026-11-09'),
]
rm=[]
for s in settle:
    ret=round((s['sp']-s['rp'])/s['rp']*100,2)
    rec=dict(stock_code=s['code'],stock_name=s['name'],track='A',recommend_date=s['rd'],recommend_price=s['rp'],
      settled_price=s['sp'],last_close=s['sp'],return_pct=ret,result=s['res'],holding_days=s['days'],
      removal_reason=s['reason'],settled_by=s['by'],settled_date=TODAY,sync_note=SYNC)
    if s['res']=='fail': rec['fail_reason']=s['reason']
    else: rec['success_note']=s['reason']
    rm.append(rec)
    # 來源檔回寫
    sp=f"data/tracking/tracking_{s['src']}.json"; st=ld(sp)
    for sec in ('recommendations','track_b_recommendations'):
        for r in st.get(sec,[]):
            if r['stock_code']==s['code']:
                r.update(result=s['res'],actual_close=s['sp'],close_price=s['sp'],settled_date=TODAY,settled_price=s['sp'],return_pct=ret,
                         holding_status=f"{s['days']} 結算",sync_note=SYNC)
                if s['res']=='fail': r['fail_reason']=s['reason']
                else: r['success_note']=s['reason']
    sv(sp,st)
t['removed_stocks']=rm
# 今日 recommendations 內更新
for r in t['recommendations']:
    c=r['stock_code']
    if c=='5876': r.update(actual_close=51.0,close_price=51.0,change_pct=0.0,return_pct=0.0,holding_status='D1 待複核（L4 5.6%<8%，10日累計+15K）')
    if c=='6239': r.update(actual_close=230.0,close_price=230.0,change_pct=2.91,return_pct=2.91,holding_status='D0 L4 賣超-1,895張佔18.3%≥8% → 次日開盤出場',recommend_date='2026-11-10')
t['phase']='after_market'
t['after_market_checks']=dict(date=TODAY,
 t86_note='11-10 T86 於 16:34 首次可取得（probe）；fetch_institutional_top30 成功；反轉/籌碼皆含今日完整 T86（_after/_chip_incl_today.py 執行期包裝）。盤後重跑會覆蓋盤前檔，已還原為盤前版，盤後版存 _after/*_after.json',
 stop_loss_check={"6770":[59.2,73.26,True],"2337":[82.1,147.6,True],"2313":[182.5,235.98,True],"3090":[136.0,256.5,True],"1301":[69.9,54.08,False],"4938":[96.2,76.5,False],"2330":[2285.0,None,None]},
 two_day_drop_check='追蹤股無 2 日累計 <-10%（3045 2日 -3.7%最大）',
 stale_series='2867 三商壽 序列停滯，凍結',
 source_files_written_back=['tracking_2026-11-03.json','tracking_2026-11-09.json'],
 attribution='2610/1101/2412 → predictions date_key 為各自推薦日（待 update_predictions 後核對）')
t['after_market_holding_status']={
 "2610":"success 結算（收盤22.8≥目標22.25）","1101":"已決出場，收盤27.3結算 success +2.06%","2412":"已決出場，收盤159.5結算 fail -2.44%",
 "3045":"D9 L2（-254張佔2.2%），續抱；明日 D10 到期結算（現價128.0<推薦價134.5，不高於推薦價將 fail）；11/12 法說在到期之後",
 "2884":"L4 -2,698張佔均量7.5%（<8%）、10日累計+20K為正 → ⚠️待複核（盤後完整T86為首次含今日資料；12:30 與次日盤後各複核，兩次皆≥5%才出場）",
 "5876":"L4 -474張佔均量5.6%（<8%）、10日累計+15K為正 → ⚠️待複核（同上；連買10天已斷）",
 "2886":"加速買超 +9,991 張，真連買9天，續抱",
 "6239":"🛑 L4 -1,895張佔均量18.3%≥8%（不適用待複核）→ 次日開盤出場，入帳用次日收盤"}
t['tomorrow_opening_exits']=[
 dict(stock_code='6239',stock_name='力成',category='新判定（推薦追蹤 D0，反轉 L4）',reason='11-10 完整T86 三大法人-1,895張佔均量18.3%≥8%→L4（不適用v8.3.3待複核）；收盤230.0；11-11 開盤出場，入帳用11-11收盤',origin_recommend_date='2026-11-10'),
 dict(stock_code='6770',stock_name='力積電',category='持倉｜已決事項（鐵律①觸及停損價）',reason='收盤59.2<停損73.26；今日L4 10.2%；原樣沿用'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉｜已決事項（鐵律①觸及停損價）',reason='收盤82.1<停損147.6；今日L4 24.8%；原樣沿用'),
 dict(stock_code='2313',stock_name='華通',category='持倉｜已決事項（鐵律①）',reason='收盤182.5<停損235.98；原樣沿用'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉｜已決事項（鐵律①）',reason='收盤136.0<停損256.5；原樣沿用'),
 dict(stock_code='2330',stock_name='台積電',category='持倉（零股）｜已決事項＋今日L4 7.8%',reason='原樣沿用'),
 dict(stock_code='1301',stock_name='台塑',category='持倉｜已決事項',reason='收盤69.9>停損54.08未觸發；沿用11-06 出場決議'),
 dict(stock_code='4938',stock_name='和碩',category='持倉｜已決事項（維持已決）',reason='收盤96.2>停損76.5未觸發；今日L1；11/12 法說會；原樣沿用')]
t['pending_review']=[
 dict(stock_code='2884',stock_name='玉山金',first_review='11-10 盤後完整T86 L4 7.5%（<8%，10日累計+20K）',rule='次日12:30與盤後各複核一次，兩次皆≥5%才於11-12開盤出場；任一降級維持追蹤',source_note='同源T86（11-10），複核②若在T86公布前即無新資訊，須標註'),
 dict(stock_code='5876',stock_name='上海商銀',first_review='11-10 盤後完整T86 L4 5.6%（<8%，10日累計+15K）',rule='同上',source_note='同上；邊緣值（5%門檻+0.6pp）')]
t['tomorrow_recommendations']=[dict(stock_code='1802',stock_name='台玻',industry='ABF載板/PCB基板（玻纖布，tier_from_tracker 待審區）',
 recommend_price=69.8,target_price=75.38,stop_loss_pct=-10,stop_loss=62.82,settlement_days=10,position='5-10%',score=97,track='A',
 entry_condition='11-10 收盤為漲停（+9.9%）；11-11 開盤價>71.9（+3%）不買，不追高',
 reason='🛤️軌道A｜法人 TOP1（三大法人+85,285張佔成交49.6%，外資近5日+44.6K，10日累計+96K）；反轉L0；動能-13%；對應「ABF載板/PCB基板漲價」強催化（PCB輪動延伸玻纖布）；Q3 EPS 0.93（YoY+830%、毛利率QoQ+8.3pp）+5；外資持股比週增+0.64% +5；月季線雙上；營收YoY+56.5%（回檔僅3.1%不加分）。⚠️今日漲停且法人單日+85K為10日累計88%，真連買僅3天、過量買超-5；屬市場級資金日（beta）風險；今晚21:30 CPI',
 score_breakdown={"時事":17,"法人":25,"產業":14,"技術":13,"價格位置":13,"動能":10,"過量買超":-5,"EPS":5,"外資持股比":5,"營收":0}, result='holding', holding_days=0)]
sv(tp,t)
print('ok')
