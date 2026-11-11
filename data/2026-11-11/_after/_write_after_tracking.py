import json
def ld(p): return json.load(open(p,encoding='utf-8'))
def sv(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
TODAY='2026-11-11'
tp=f'data/tracking/tracking_{TODAY}.json'
t=ld(tp)
SYNC='v8.3.7 三處同步：①來源tracking ②tracking_2026-11-11.json removed_stocks ③predictions.json'
settle=[
 dict(code='3045',name='台灣大',rd='2026-10-28',rp=134.5,sp=129.0,res='fail',days='D10/10',
  reason='D10 到期，收盤 129.0 ≤ 推薦價 134.5（未觸停損 121.05）；到期結算',by='settlement_checker D10 到期（盤後收盤價）',src='2026-10-28'),
 dict(code='6239',name='力成',rd='2026-11-10',rp=223.5,sp=242.0,res='success',days='D1/10',
  reason='收盤 242.0 ≥ 目標 241.38（settlement_checker 機械判定）；原決議 11-10 T86 L4 18.3% 開盤出場，入帳用收盤（v8.3.2）。⚠️揭露：11-11 T86 +2,278 張，今日反轉為狀態不明（累計-306張）',by='settlement_checker 目標價達成（盤後收盤價）＋已決事項出場',src='2026-11-10'),
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
    sp=f"data/tracking/tracking_{s['src']}.json"; st=ld(sp)
    for sec in ('recommendations','track_b_recommendations','carry_over_recommendations'):
        for r in st.get(sec,[]):
            if r['stock_code']==s['code']:
                r.update(result=s['res'],actual_close=s['sp'],close_price=s['sp'],settled_date=TODAY,settled_price=s['sp'],return_pct=ret,
                         holding_status=f"{s['days']} 結算",sync_note=SYNC)
                if s['res']=='fail': r['fail_reason']=s['reason']
                else: r['success_note']=s['reason']
    sv(sp,st)
t['removed_stocks']=rm
cl={'1802':(76.7,9.9),'5876':(51.8,1.57),'2884':(47.6,-2.86),'2886':(54.2,-1.09)}
for sec in ('recommendations','carry_over_recommendations'):
  for r in t.get(sec,[]):
    c=r['stock_code']
    if c in cl: r.update(actual_close=cl[c][0],close_price=cl[c][0],return_pct=cl[c][1])
    if c=='1802': r['holding_status']='D0 收盤漲停 76.7，高於進場上限 71.9，未追；D1 起判定'
    if c=='5876': r['holding_status']='D2 待複核②：11-11 T86 轉 L1（買超減速），降級 → 維持追蹤'
    if c=='2884': r['holding_status']='D8 待複核②：11-11 T86 +2,169 張 L0（累計+31K），降級 → 維持追蹤'
    if c=='2886': r['holding_status']='D7 續抱；11-11 T86 +10,539 張'
    if c in('3045','6239'): r.update(result='fail' if c=='3045' else 'success',actual_close=129.0 if c=='3045' else 242.0)
t['phase']='after_market'
t['after_market_checks']=dict(date=TODAY,
 t86_note='11-11 T86 於 16:3x 前已可取得；fetch_institutional_top30 成功；反轉/籌碼皆含今日完整 T86（_after/_chip_incl_today.py）。institutional_top50/catalyst_preposition_scan/stock_dossier 已還原為盤前版，盤後版在 _after/。',
 stop_loss_check={"6770":[58.5,73.26,True],"2337":[82.7,147.6,True],"2313":[192.5,235.98,True],"3090":[140.0,256.5,True],"1301":[70.2,54.08,False],"4938":[96.2,76.5,False]},
 two_day_drop_check='追蹤股無 2 日累計 <-10%',
 stale_series='2867 三商壽 序列停滯，凍結',
 source_files_written_back=['tracking_2026-10-28.json','tracking_2026-11-10.json'])
t['after_market_holding_status']={
 "3045":"D10 到期 fail -4.09%（收盤129.0≤推薦價134.5）",
 "6239":"success +8.28%（收盤242.0≥目標241.38）",
 "2884":"待複核②：L0（11-11 T86 +2,169 張，累計+31K）→ 降級，維持追蹤，不出場",
 "5876":"待複核②：L1（買超減速-74%）→ 降級，維持追蹤，不出場",
 "2886":"加速/持續買超 +10,539 張，續抱",
 "1802":"D0 收盤漲停 76.7（+9.9%），法人 +19,628 張 L0 加速；結算排除 D0；接近注意門檻（週轉9.2%、6日+13.3%、30日+31.3%）"}
t['pending_review']=[dict(stock_code='2884',stock_name='玉山金',review_2='盤後 L0（+2,169張）降級，結案維持追蹤'),dict(stock_code='5876',stock_name='上海商銀',review_2='盤後 L1 降級，結案維持追蹤')]
t['tomorrow_opening_exits']=[
 dict(stock_code='6770',stock_name='力積電',category='持倉｜已決事項（鐵律①觸及停損價）',reason='收盤58.5<停損73.26；原樣沿用'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉｜已決事項（鐵律①）',reason='收盤82.7<停損147.6；原樣沿用'),
 dict(stock_code='2313',stock_name='華通',category='持倉｜已決事項（鐵律①）',reason='收盤192.5<停損235.98；原樣沿用'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉｜已決事項（鐵律①）',reason='收盤140.0<停損256.5；原樣沿用'),
 dict(stock_code='1301',stock_name='台塑',category='持倉｜已決事項（11-06 出場決議）',reason='原樣沿用'),
 dict(stock_code='4938',stock_name='和碩',category='持倉｜已決事項（11/12 法說會，維持已決）',reason='原樣沿用'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉｜已決事項（L4 7.8%）',reason='原樣沿用')]
t['tomorrow_recommendations']=[dict(stock_code='2412',stock_name='中華電',industry='電信（tier_0 電信龍頭）',recommend_price=161.0,
 target_price=173.88,stop_loss_pct=-10,stop_loss=144.9,settlement_days=10,position='5-10%',score=79,track='A',result='holding',
 reason='🛤️軌道A｜法人 TOP50 買超第21（avg_rank 18.5，+3,501張佔成交29.8%）；外資10日+32K、近5日+17.9K；反轉L0；動能-11%（佈局中）；月季線上；營收YoY+13.4%（不加分）；EPS Q3 YoY+28.7% +3。⚠️11-09 推薦後 11-10 因 L4 邊緣值出場 fail -2.45%，T86 已翻買；與已結算 3045 台灣大同為電信',
 score_breakdown={"時事":12,"法人":18,"產業":14,"技術":11,"價格位置":11,"動能":10,"EPS":3,"營收":0,"外資持股比":0})]
sv(tp,t)
print('ok')
