import json
def ld(p): return json.load(open(p,encoding='utf-8'))
def sv(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
TODAY='2026-11-12'
tp=f'data/tracking/tracking_{TODAY}.json'
t=ld(tp)
SYNC='v8.3.7 三處同步：①來源tracking_2026-11-11.json ②tracking_2026-11-12.json removed_stocks ③predictions.json'
reason='收盤 81.7 ≥ 目標 75.38（settlement_checker 機械判定，D1）。⚠️揭露：推薦進場條件「11-11 開盤>71.9 不買」，D0 開盤即漲停 76.7，系統帳面成功但依進場條件並未實際可買；今日法人 +144K 張（TOP1），5 日 +35.9%、週轉偏高，接近處置門檻'
rp,sp=69.8,81.7
ret=round((sp-rp)/rp*100,2)
rm=[dict(stock_code='1802',stock_name='台玻',track='A',recommend_date='2026-11-11',recommend_price=rp,settled_price=sp,last_close=sp,return_pct=ret,result='success',holding_days='D1/10',removal_reason=reason,success_note=reason,settled_by='settlement_checker 目標價達成（盤後收盤價）',settled_date=TODAY,sync_note=SYNC)]
sp_path='data/tracking/tracking_2026-11-11.json'; st=ld(sp_path)
for sec in ('recommendations','track_b_recommendations','carry_over_recommendations'):
    for r in st.get(sec,[]):
        if r['stock_code']=='1802':
            r.update(result='success',actual_close=sp,close_price=sp,settled_date=TODAY,settled_price=sp,return_pct=ret,holding_status='D1/10 結算 success',success_note=reason,sync_note=SYNC)
sv(sp_path,st)
t['removed_stocks']=rm
cl={'5876':(52.6,3.14,'D3 續抱；11-12 T86 +1,3xx 見報告；L1 買超減速'),'2884':(47.2,-3.67,'D9；明日 11-13 為 D10 收盤結算；L1（今日 T86 買超、累計 +26.8K）；11/17 法說在持有期外'),'2886':(54.4,-0.73,'D8 續抱；真連買10天，累計 +76K，L0'),'2412':(162.0,0.62,'D0 續抱；L1（買超減速-50%，累計 +39K）；D0 不結算')}
for sec in ('recommendations','carry_over_recommendations'):
  for r in t.get(sec,[]):
    c=r['stock_code']
    if c in cl: r.update(actual_close=cl[c][0],close_price=cl[c][0],return_pct=cl[c][1],holding_status=cl[c][2])
    if c=='1802': r.update(result='success',actual_close=81.7,close_price=81.7,return_pct=ret,holding_status='D1 收盤 81.7 ≥ 目標 75.38 → success')
t['phase']='after_market'
t['after_market_checks']=dict(date=TODAY,
 t86_note='11-12 T86 於 16:35 前已可取得；fetch_all_institutional 19763 筆成功；反轉/籌碼皆含今日完整 T86（_after/_chip_incl_today.py）。institutional_top50 另存 _after/institutional_top50_after.json；盤前版 price_position/revenue/eps/foreign_ratio/catalyst_preposition_scan/stock_dossier/reversal_alerts 已備份於 _after/bak/。',
 stop_loss_check={"6770":[56.1,73.26,True],"2337":[78.4,147.6,True],"2313":[196.0,235.98,True],"3090":[132.5,256.5,True],"1301":[68.3,54.08,False],"4938":[92.2,76.5,False],"2330":[2340.0,None,None]},
 two_day_drop_check='追蹤股無 2 日累計 <-10%（2884 47.6→47.2、2886 54.2→54.4、5876 51.8→52.6、2412 161→162）',
 stale_series='2867 三商壽 序列查詢失敗/停滯，凍結（已知，非新增）',
 source_files_written_back=['tracking_2026-11-11.json'])
t['after_market_holding_status']={
 "1802":"D1 success +17.05%（收盤81.7≥目標75.38）",
 "2884":"D9；L1；明日 D10 收盤結算",
 "2886":"D8；L0；續抱",
 "5876":"D3；L1；續抱",
 "2412":"D0；L1（買超減速）；續抱，D0 不結算"}
t['pending_review']=[]
t['tomorrow_opening_exits']=[
 dict(stock_code='6770',stock_name='力積電',category='持倉｜已決事項（鐵律①觸及停損價）',reason='11-12 收盤56.1<停損73.26；今日 L4 8.1%；原樣沿用'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉｜已決事項（鐵律①）',reason='收盤78.4<停損147.6；原樣沿用'),
 dict(stock_code='2313',stock_name='華通',category='持倉｜已決事項（鐵律①）',reason='收盤196.0<停損235.98；原樣沿用'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉｜已決事項（鐵律①）',reason='收盤132.5<停損256.5；今日 L4 6.6%；原樣沿用'),
 dict(stock_code='1301',stock_name='台塑',category='持倉｜已決事項（11-06 出場決議）',reason='原樣沿用；收盤68.3>停損54.08'),
 dict(stock_code='4938',stock_name='和碩',category='持倉｜已決事項（11/12 法說會，維持已決）',reason='原樣沿用；今日 L4 8.9%'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉｜已決事項（L4 7.8%）',reason='原樣沿用；今日 L4 9.1%')]
t['tomorrow_recommendations']=[dict(stock_code='2618',stock_name='長榮航',industry='航空（tier 未驗證，依 topic_tracker「中東地緣（含航運）」影響鏈）',recommend_price=46.9,
 target_price=50.65,stop_loss_pct=-10,stop_loss=42.21,settlement_days=10,position='5-10%',score=76,track='A',result='holding',recommend_date='2026-11-13',
 entry_condition='開盤價>48.31（+3%）不買，不追高',
 reason='🛤️軌道A｜法人 TOP50 買超第14（avg_rank 20.5，今日+4,770張）；真連買10天、10日累計三大法人 +121K 張、外資近5日 +62K；反轉L0；動能+19%（佈局中）；月季線雙上（MA20 +7.4%）；5日 +4.0%；Q3 EPS YoY+15.6%、毛利率QoQ +6.8pp +2；營收10月 YoY+22.6%（回檔僅4%不加分）。⚠️航空油價敏感：topic_tracker 稱中東談判分歧、油價自低點反彈；5日內曾有單日買超 +29K 張；與華航同為航空，故僅推此一檔',
 score_breakdown={"時事":18,"法人":18,"產業":14,"技術":11,"價格位置":13,"動能":0,"EPS":2,"營收":0,"外資持股比":0})]
t['tomorrow_observations']=[dict(stock_code='2610',stock_name='華航',score=74,reason='法人與籌碼更強（連買9天、10日累計+210K）但5日+5.3%（-10）、同為航空不重複推薦')]
sv(tp,t)
print('ok')
