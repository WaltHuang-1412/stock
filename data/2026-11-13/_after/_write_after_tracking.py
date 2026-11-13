import json
def ld(p): return json.load(open(p,encoding='utf-8'))
def sv(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
TODAY='2026-11-13'
tp=f'data/tracking/tracking_{TODAY}.json'
t=ld(tp)
SYNC='v8.3.7 三處同步：①來源tracking_2026-10-30.json ②tracking_2026-11-13.json removed_stocks ③predictions.json'
reason='D10 到期，收盤 48.3 ≤ 推薦價 49.0 → fail（settlement_checker 機械判定，-1.43%）；期間未觸停損 44.1，亦未達目標 52.92；最低收盤約 47.2（11-12），終點以 10 日收盤 vs 推薦價判定'
rp,sp=49.0,48.3
ret=round((sp-rp)/rp*100,2)
rm=dict(stock_code='2884',stock_name='玉山金',track='A',recommend_date='2026-10-30',recommend_price=rp,settled_price=sp,last_close=sp,return_pct=ret,result='fail',holding_days='D10/10',removal_reason=reason,fail_reason=reason,settled_by='settlement_checker D10 到期（盤後收盤價）',settled_date=TODAY,sync_note=SYNC)
sp_path='data/tracking/tracking_2026-10-30.json'; st=ld(sp_path)
for sec in ('recommendations','track_b_recommendations','carry_over_recommendations'):
    for r in st.get(sec,[]):
        if r['stock_code']=='2884':
            r.update(result='fail',actual_close=sp,close_price=sp,settled_date=TODAY,settled_price=sp,return_pct=ret,holding_status='D10/10 結算 fail',fail_reason=reason,sync_note=SYNC)
sv(sp_path,st)
t['removed_stocks']=[rm]
# 移出追蹤清單的 carry_over
cl={'2886':(55.4,1.1,'D9 續抱；L0；真連買、累計 +74K；明日（11-16 週一）為 D10，收盤才結算'),
    '5876':(53.4,4.71,'D4 續抱；L1（買超減速-64%，今日仍買超）'),
    '2412':(165.0,2.48,'D1 續抱；L1（買超減速-64%，累計為正）'),
    '2801':(29.0,2.11,'D0 續抱；L1（買超減速，近5日 -170 張/日，累計仍為正）；D0 不結算；Q3 財報申報期限 11/14')}
for sec in ('recommendations','carry_over_recommendations'):
  for r in t.get(sec,[]):
    c=r['stock_code']
    if c in cl: r.update(actual_close=cl[c][0],close_price=cl[c][0],return_pct=cl[c][1],holding_status=cl[c][2])
    if c=='2884': r.update(result='fail',actual_close=sp,close_price=sp,return_pct=ret,holding_status='D10 收盤 48.3 ≤ 推薦價 49.0 → fail',fail_reason=reason)
t['phase']='after_market'
t['after_market_checks']=dict(date=TODAY,
 t86_note='11-13 T86 於 16:35 前已可取得（fetch_all_institutional 19022 筆）；籌碼/反轉含今日完整 T86（_after/_chip_incl_today.py）。institutional_top50 與 price_position/revenue/eps/foreign_ratio 盤後版存於 _after/*_after.json，盤前版保留原檔。',
 stop_loss_check={"6770":[57.0,73.26,True],"2337":[79.6,147.6,True],"2313":[205.5,235.98,True],"3090":[136.0,256.5,True],"1301":[71.1,54.08,False],"4938":[89.1,76.5,False],"2330":[2350.0,None,None]},
 two_day_drop_check='追蹤股無 2 日累計 <-10%（2884 47.6→48.3、2886 54.2→55.4、5876 51.8→53.4、2412 161→165、2801 28.3→29.0）',
 stale_series='2867 三商壽 序列查詢失敗（併購停牌），凍結（已知，非新增）',
 source_files_written_back=['tracking_2026-10-30.json'])
t['after_market_holding_status']={"2884":"D10 fail -1.43%","2886":"D9；L0；明日 D10","5876":"D4；L1；續抱","2412":"D1；L1；續抱","2801":"D0；L1；續抱，D0 不結算"}
t['pending_review']=[]
t['tomorrow_opening_exits']=[
 dict(stock_code='6770',stock_name='力積電',category='持倉｜已決事項（鐵律①觸及停損價）',reason='11-13 收盤57.0<停損73.26；原樣沿用'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉｜已決事項（鐵律①）',reason='收盤79.6<停損147.6；原樣沿用'),
 dict(stock_code='2313',stock_name='華通',category='持倉｜已決事項（鐵律①）',reason='收盤205.5<停損235.98；原樣沿用'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉｜已決事項（鐵律①）',reason='收盤136.0<停損256.5；原樣沿用'),
 dict(stock_code='1301',stock_name='台塑',category='持倉｜已決事項（11-06 出場決議）',reason='原樣沿用；收盤71.1>停損54.08'),
 dict(stock_code='4938',stock_name='和碩',category='持倉｜已決事項（11/12 法說會，維持已決）',reason='原樣沿用；今日 L4 28.6%（賣超-3,053張）'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉｜已決事項（L4）',reason='原樣沿用；累計-46,640張')]
t['tomorrow_recommendations']=[]
t['tomorrow_observations']=[
 dict(stock_code='2610',stock_name='華航',score=None,reason='籌碼最強（連買10天、10日+223K、外資5日+134K、L0）但 topic_tracker「中東地緣」鏈標「華航↓ 油價成本」（Brent +5.05%）＋5日+9.4%（-10）→ 催化方向相反，未過準確率篩選①'),
 dict(stock_code='2618',stock_name='長榮航',score=None,reason='同上，航空油價成本鏈↓；5日+9.5%（-10）；盤前已撤回，維持不推薦'),
 dict(stock_code='2892',stock_name='第一金',score=68,reason='L0、連買9天、外資5日+23K、動能-12%（+10）；但5日+6.1%（-10）、營收快取落後（視為0）、金融集中度高，概估68<70'),
 dict(stock_code='2887',stock_name='台新新光金',score=66,reason='外資5日+64K、動能-19%；但月季線雙下（價位6）、連買僅1天、5日+5.9%（-10），概估66<70')]
sv(tp,t)
print('ok')
