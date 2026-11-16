import json
def ld(p): return json.load(open(p,encoding='utf-8'))
def sv(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
TODAY='2026-11-16'
tp=f'data/tracking/tracking_{TODAY}.json'
t=ld(tp)
SYNC='v8.3.7 三處同步：①來源tracking_2026-11-02.json ②tracking_2026-11-16.json removed_stocks ③predictions.json'
rp,sp=54.8,54.5
ret=round((sp-rp)/rp*100,2)
reason='D10 到期，收盤 54.5 ≤ 推薦價 54.8 → fail（settlement_checker 機械判定，-0.55%）；期間未觸停損 49.32，亦未達目標 59.18；終點以 10 日收盤 vs 推薦價判定'
rm=dict(stock_code='2886',stock_name='兆豐金',track='A',recommend_date='2026-11-02',recommend_price=rp,settled_price=sp,last_close=sp,return_pct=ret,result='fail',holding_days='D10/10',removal_reason=reason,fail_reason=reason,settled_by='settlement_checker D10 到期（盤後收盤價）',settled_date=TODAY,sync_note=SYNC)
sp_path='data/tracking/tracking_2026-11-02.json'; st=ld(sp_path)
n=0
for sec in ('recommendations','track_b_recommendations','carry_over_recommendations'):
    for r in st.get(sec,[]):
        if r['stock_code']=='2886':
            r.update(result='fail',actual_close=sp,close_price=sp,settled_date=TODAY,settled_price=sp,return_pct=ret,holding_status='D10/10 結算 fail',fail_reason=reason,sync_note=SYNC); n+=1
assert n>=1
sv(sp_path,st)
t['removed_stocks']=[rm]
cl={'2884':(48.3,0.0,'D0 續抱；L0（今日 +8,819 張）；11/17 15:30 法說、11/18 法說（前一日進場，雙向波動）'),
    '4904':(109.0,-0.46,'D0 續抱；L2（前期買超 +9,796 張，今日賣超 -496 張佔 4.4%，單日反轉；未達 L3/L4 出場）；11/19 10:50 法說'),
    '5876':(53.1,4.12,'D5 續抱；L1（買超減速-44%，仍買超）；11/20 法說'),
    '2412':(163.5,1.55,'D2 續抱；L1（買超減速-50%，累計為正）；11/18 法說'),
    '2801':(28.4,0.0,'D1 續抱；L0（今日 +1,839 張，累計 +2,595 張）')}
for sec in ('recommendations','carry_over_recommendations'):
  for r in t.get(sec,[]):
    c=r['stock_code']
    if c in cl: r.update(actual_close=cl[c][0],close_price=cl[c][0],return_pct=cl[c][1],holding_status=cl[c][2])
    if c=='2886': r.update(result='fail',actual_close=sp,close_price=sp,return_pct=ret,holding_status='D10 收盤 54.5 ≤ 推薦價 54.8 → fail',fail_reason=reason)
t['phase']='after_market'
t['after_market_checks']=dict(date=TODAY,
 t86_note='11-16 T86 於 16:34 前已可取得（fetch_all_institutional 17413 筆）；籌碼/反轉含今日完整 T86（_after/_chip_incl_today.py，END=11-16）。價位/營收/EPS/持股比因盤後只對 11 檔候選重跑，已覆寫當日盤前版 JSON，盤前版備份於 _after/bak/。',
 stop_loss_check={"6770":[53.7,73.26,True],"2337":[72.0,147.6,True],"2313":[193.0,235.98,True],"3090":[122.5,256.5,True],"1301":[67.0,54.08,False],"4938":[85.7,76.5,False],"2330":[2215.0,None,None]},
 two_day_drop_check='追蹤股無 2 日累計 <-10%（2884 47.2→48.3→48.3、4904 108.0→109.5→109.0、2886 54.4→55.4→54.5、5876 52.6→53.4→53.1、2412 162.0→165.0→163.5、2801 28.4→29.0→28.4）',
 stale_series='2867 三商壽 序列查詢失敗（併購停牌），凍結（已知，非新增）',
 source_files_written_back=['tracking_2026-11-02.json'])
t['after_market_holding_status']={"2886":"D10 fail -0.55%","2884":"D0；L0","4904":"D0；L2 單日反轉，續追蹤","5876":"D5；L1；續抱","2412":"D2；L1；續抱","2801":"D1；L0；續抱"}
t['pending_review']=[]
t['tomorrow_opening_exits']=[
 dict(stock_code='6770',stock_name='力積電',category='持倉｜已決事項（鐵律①觸及停損價）',reason='11-16 收盤53.7<停損73.26；今日 L4 9.6%；原樣沿用'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉｜已決事項（鐵律①）',reason='收盤72.0<停損147.6；今日 L4 6.8%；原樣沿用'),
 dict(stock_code='2313',stock_name='華通',category='持倉｜已決事項（鐵律①）',reason='收盤193.0<停損235.98；今日 L3；原樣沿用'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉｜已決事項（鐵律①）',reason='收盤122.5<停損256.5；今日 L4；原樣沿用'),
 dict(stock_code='1301',stock_name='台塑',category='持倉｜已決事項（11-06 出場決議）',reason='原樣沿用；收盤67.0>停損54.08；今日 L4 13.7%'),
 dict(stock_code='4938',stock_name='和碩',category='持倉｜已決事項（11/12 法說會，維持已決）',reason='原樣沿用；收盤85.7>停損76.5；L1 減速'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉｜已決事項（L4）',reason='原樣沿用；今日賣超-7,672張佔23.3%')]
t['tomorrow_recommendations']=[]
t['tomorrow_observations']=[
 dict(stock_code='2609',stock_name='陽明',score=69,reason='中東地緣／貨櫃運價超強↑、TOP50 avg_rank 7.5、外資5日+9.7K、L0、EPS Q3 +208%(+5)；但動能+72.6%(-10)、月季線雙下（價位6）、連買僅2天，估分69<70'),
 dict(stock_code='9904',stock_name='寶成',score=64,reason='法人第1（+26.9K張、外資5日+28.8K、L0）但無對應強催化（準確率篩選①不過）、產業定位邊緣，估分64'),
 dict(stock_code='2891',stock_name='中信金',score=None,reason='Fed升息鏈↑、投信大買，但外資近5日-7,374（篩選②不過）、營收連3月衰退(-5)'),
 dict(stock_code='2542',stock_name='興富發',score=74,reason='房市鏈↑中度、動能-43.5%(+15)、外資5日+4K；但 L1（篩選③需L0）、月季線雙下（MA60 -10.7%），不推薦'),
 dict(stock_code='2890',stock_name='永豐金',score=None,reason='動能+500%>100%追高排除'),
 dict(stock_code='6505',stock_name='台塑化',score=None,reason='動能+273%>100%追高排除'),
 dict(stock_code='2610',stock_name='華航',score=None,reason='航空油價成本鏈↓（Brent 95）催化方向相反；2618長榮航同'),]
sv(tp,t)
print('ok')
