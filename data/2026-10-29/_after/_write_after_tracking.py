import json
D='2026-10-29'
closes={'2002':19.45,'3706':79.5,'2885':73.4,'3702':110.0,'2884':49.0,'2603':261.0,'2609':62.0,'2801':30.5,'2377':160.0,'3045':134.5}
dd={'3706':4,'2885':3,'3702':3,'2884':2,'2603':2,'2609':1,'2801':1,'2377':1,'3045':1}
def load(p): return json.load(open(p,encoding='utf-8'))
def save(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
info={'2002':('success','D10 到期：收盤 19.45 > 推薦價 19.2','中鋼','tracking_2026-10-13.json','D10/10','D10 到期結算（settlement_checker）'),
      '2884':('fail','鐵律③ L4（今日 T86 末日 10-28 賣超 -7,972 張佔日均量 33.0%，≥8%）→ 10-29 盤前已決開盤出場；入帳收盤 49.0（v8.3.2），低於推薦價 49.75','玉山金','tracking_2026-10-27.json','D2/10','已決事項開盤出場（v8.3.2 收盤價入帳）')}
removed=[]
for c,(res,why,nm,srcf,dl,by) in info.items():
    sp=f'data/tracking/{srcf}'; src=load(sp)
    for r in src['recommendations']:
        if r['stock_code']==c and r.get('result','holding')=='holding':
            ret=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
            r.update(result=res,actual_close=closes[c],close_price=closes[c],settled_date=D,settled_price=closes[c],return_pct=ret,
                     holding_status=f'{D} 結算',sync_note='v8.3.7 三處同步：①本檔 ②tracking_2026-10-29.json removed_stocks ③predictions.json')
            r['fail_reason' if res=='fail' else 'success_note']=why
            removed.append(dict(stock_code=c,stock_name=nm,track='A',recommend_date=r['recommend_date'],recommend_price=r['recommend_price'],
              settled_price=closes[c],last_close=closes[c],return_pct=ret,result=res,holding_days=dl,removal_reason=why,
              **({'fail_reason':why} if res=='fail' else {'success_note':why}),settled_by=by,settled_date=D,
              sync_note=f'v8.3.7 三處同步：①{srcf} ②本檔 removed_stocks ③predictions.json'))
    save(sp,src)
tp=f'data/tracking/tracking_{D}.json'; t=load(tp)
t['phase']='after_market'; t['removed_stocks']=removed
t['carry_over_recommendations']=[r for r in t['carry_over_recommendations'] if r['stock_code'] not in info]
t['carry_over']=[c for c in t['carry_over'] if c not in info]
for r in t['carry_over_recommendations']:
    c=r['stock_code']
    r['holding_days']=dd[c]; r['holding_days_label']=f'D{dd[c]}/10'; r['actual_close']=closes[c]; r['current_price']=closes[c]
    r['return_pct']=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
    r['holding_status']='續抱（settlement_checker 10-29 盤後輸出；反轉 L0，T86 末日 10-28）'
    if c=='3702': r['holding_status']='續抱，最高警戒：單日 -5.17%，距停損 103.5 僅 5.9%；L0'
t['tomorrow_recommendations']=[]
t['tomorrow_opening_exits']=[
 {'stock_code':'2313','stock_name':'華通','category':'已決事項（v8.3.7）','reason':'收盤213.5<停損235.98'},
 {'stock_code':'2330','stock_name':'台積電零股','category':'已決事項（v8.3.7）','reason':'L4 賣超（今日 -2,069 張佔 10.4%）'},
 {'stock_code':'6770','stock_name':'力積電','category':'已決事項（v8.3.7）','reason':'收盤69.5<停損73.26'},
 {'stock_code':'2337','stock_name':'旺宏','category':'已決事項（v8.3.7）','reason':'收盤100.0<停損147.6；L4 -29,909 張佔 92.4%'},
 {'stock_code':'3090','stock_name':'日電貿','category':'已決事項（v8.3.7）','reason':'收盤158.5<停損256.5'},
 {'stock_code':'1301','stock_name':'台塑','category':'已決事項（v8.3.7）','reason':'10-20 L4、損益>停利20%'},
 {'stock_code':'4938','stock_name':'和碩','category':'已決事項（v8.3.7）','reason':'已決不重評'}]
t['after_market_check_20261029']={'t86':'10-29 T86 未公布（14:3x），法人欄位為 10-28 T86','stale_series':['2867'],
 'holdings_stop_loss':{'6770':[69.5,73.26,True],'2337':[100.0,147.6,True],'2313':[213.5,235.98,True],'3090':[158.5,256.5,True],'1301':[73.9,54.08,False],'4938':[104.5,76.5,False]}}
save(tp,t)
print('ok',[(r['stock_code'],r['result'],r['return_pct']) for r in removed])
