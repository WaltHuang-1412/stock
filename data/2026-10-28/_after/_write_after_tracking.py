import json
D='2026-10-28'
closes={'2002':19.75,'3706':81.0,'2885':73.0,'3702':116.0,'2886':53.9,'2884':48.35,'2603':263.0,'1101':28.0,'2609':62.9,'2801':29.95,'2377':168.5,'3045':132.5}
dd={'2002':9,'3706':3,'2885':2,'3702':2,'2884':1,'2603':1}
def load(p): return json.load(open(p,encoding='utf-8'))
def save(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
src_p='data/tracking/tracking_2026-10-27.json'
src=load(src_p); t_p=f'data/tracking/tracking_{D}.json'; t=load(t_p)
info={'2886':('fail','L4（10-27 T86 賣超 -1,251 張佔 8.1%~8.5% ≥8%，不受 v8.3.3 待複核保護）','兆豐金'),
      '1101':('success','L4（10-27 T86 賣超 -8,933 張佔 20.4%~22.9% ≥8%，外資 -11K）','台泥')}
removed=[]
for r in src['recommendations']:
    c=r['stock_code']
    if c in info:
        res,why,_=info[c]
        ret=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
        cmp='低於' if res=='fail' else '高於'
        note=f"鐵律③ {why}→ 10-28 盤前已決開盤出場（v8.3.7 不重評）；入帳 10-28 收盤 {closes[c]}（v8.3.2），{cmp}推薦價 {r['recommend_price']} 記 {res}"
        r.update(result=res,actual_close=closes[c],close_price=closes[c],settled_date=D,settled_price=closes[c],return_pct=ret,
                 holding_status=f'10-28 鐵律 L4 出場結算',sync_note='v8.3.7 三處同步：①本檔 ②tracking_2026-10-28.json removed_stocks ③predictions.json')
        r['fail_reason' if res=='fail' else 'success_note']=note
        removed.append(dict(stock_code=c,stock_name=info[c][2],track='A',recommend_date=r['recommend_date'],recommend_price=r['recommend_price'],
            settled_price=closes[c],last_close=closes[c],return_pct=ret,result=res,holding_days='D1/10',removal_reason=note,
            **({'fail_reason':note} if res=='fail' else {'success_note':note}),
            settled_by='已決事項開盤出場（v8.3.7 Step 4-0，10-28 盤前定案；盤後收盤價入帳 v8.3.2）',settled_date=D,
            sync_note='v8.3.7 三處同步：①tracking_2026-10-27.json ②本檔 removed_stocks ③predictions.json'))
save(src_p,src)
t['phase']='after_market'
t['removed_stocks']=removed
for r in t['recommendations']:
    c=r['stock_code']; r['actual_close']=closes[c]; r['close_price']=closes[c]
    r['return_pct']=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
    r['holding_days']=0; r['holding_days_label']='D0/10'; r['recommend_date']=D
    r['holding_status']='續抱 D0，不判定；10-27 T86 L0（10-28 T86 盤後尚未公布）'
for r in t['carry_over_recommendations']:
    c=r['stock_code']
    if c in closes and c in dd:
        r['holding_days']=dd[c]; r['holding_days_label']=f'D{dd[c]}/10'; r['actual_close']=closes[c]; r['current_price']=closes[c]
        r['return_pct']=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
        r['holding_status']='續抱（settlement_checker 10-28 盤後輸出）'
# 2886/1101 因10-27推薦在 carry_over 中也出現者移除
t['carry_over_recommendations']=[r for r in t['carry_over_recommendations'] if r['stock_code'] not in info]
t['carry_over']=[c for c in t['carry_over'] if c not in info]
t['tomorrow_recommendations']=[]
t['tomorrow_opening_exits']=[
 {'stock_code':'2313','stock_name':'華通','category':'已決事項（v8.3.7）','reason':'收盤224.0<停損235.98；L4 賣超 -5,249 張佔16.8%'},
 {'stock_code':'2330','stock_name':'台積電零股','category':'已決事項（v8.3.7）','reason':'L4 賣超（累計 -72K）'},
 {'stock_code':'6770','stock_name':'力積電','category':'已決事項（v8.3.7）','reason':'收盤71.3<停損73.26'},
 {'stock_code':'2337','stock_name':'旺宏','category':'已決事項（v8.3.7）','reason':'收盤103.5<停損147.6'},
 {'stock_code':'3090','stock_name':'日電貿','category':'已決事項（v8.3.7）','reason':'收盤163.0<停損256.5；L4 5.5%'},
 {'stock_code':'1301','stock_name':'台塑','category':'已決事項（v8.3.7）','reason':'10-20 L4、損益>停利20%'},
 {'stock_code':'4938','stock_name':'和碩','category':'已決事項（v8.3.7）','reason':'已決不重評'}]
t['after_market_check_20261028']={'t86':'10-28 T86 未公布（14:3x），法人欄位為 10-27 T86','stale_series':['2867'],
 'holdings_stop_loss':{'6770':[71.3,73.26,True],'2337':[103.5,147.6,True],'2313':[224.0,235.98,True],'3090':[163.0,256.5,True],'1301':[75.4,54.08,False],'4938':[108.0,76.5,False]}}
save(t_p,t)
print('ok',[ (r['stock_code'],r['result'],r['return_pct']) for r in removed])
