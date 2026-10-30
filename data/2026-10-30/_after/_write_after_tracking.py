import json
D='2026-10-30'
closes={'3706':76.8,'2885':72.6,'3702':108.5,'2603':271.5,'2609':63.5,'2801':30.7,'2377':157.5,'3045':133.5,'2884':49.05}
dd={'3706':5,'2885':4,'3702':4,'2603':3,'2609':2,'2801':2,'2377':2,'3045':2,'2884':0}
def load(p): return json.load(open(p,encoding='utf-8'))
def save(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
pct={'3706':'65.6%','3702':'45.6%','2377':'52.9%'}
sell={'3706':'-2,515','3702':'-4,336','2377':'-3,171'}
nm={'3706':'神達','3702':'大聯大','2377':'微星'}
srcs={'3706':('tracking_2026-10-21.json','D5/10'),'3702':('tracking_2026-10-22.json','D4/10'),'2377':('tracking_2026-10-28.json','D2/10')}
removed=[]
for c,(srcf,dl) in srcs.items():
    why=f'鐵律③ L4：賣超 {sell[c]} 張佔日均量 {pct[c]}（≥8%，不適用待複核）→ 10-30 盤前已決開盤出場；入帳收盤 {closes[c]}（v8.3.2），低於推薦價'
    sp=f'data/tracking/{srcf}'; src=load(sp)
    for r in src['recommendations']:
        if r['stock_code']==c and r.get('result','holding')=='holding':
            ret=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
            r.update(result='fail',actual_close=closes[c],close_price=closes[c],settled_date=D,settled_price=closes[c],return_pct=ret,
                     holding_status=f'{D} 結算',fail_reason=why+f' {r["recommend_price"]}',
                     sync_note='v8.3.7 三處同步：①本檔 ②tracking_2026-10-30.json removed_stocks ③predictions.json')
            removed.append(dict(stock_code=c,stock_name=nm[c],track='A',recommend_date=r['recommend_date'],recommend_price=r['recommend_price'],
              settled_price=closes[c],last_close=closes[c],return_pct=ret,result='fail',holding_days=dl,removal_reason=r['fail_reason'],fail_reason=r['fail_reason'],
              settled_by='已決事項開盤出場（v8.3.2 收盤價入帳）',settled_date=D,
              sync_note=f'v8.3.7 三處同步：①{srcf} ②本檔 removed_stocks ③predictions.json'))
    save(sp,src)
tp=f'data/tracking/tracking_{D}.json'; t=load(tp)
t['phase']='after_market'; t['removed_stocks']=removed
t['carry_over_recommendations']=[r for r in t['carry_over_recommendations'] if r['stock_code'] not in srcs]
t['carry_over']=[c for c in t['carry_over'] if c not in srcs]
for r in t['carry_over_recommendations']:
    c=r['stock_code']
    r['holding_days']=dd[c]; r['holding_days_label']=f'D{dd[c]}/10'; r['actual_close']=closes[c]; r['current_price']=closes[c]
    r['return_pct']=round((closes[c]-r['recommend_price'])/r['recommend_price']*100,2)
    r['holding_status']='續抱（settlement_checker 10-30 盤後輸出；反轉 L0，T86 末日 10-29）'
for r in t['recommendations']:
    if r['stock_code']=='2884':
        r['actual_close']=49.05; r['return_pct']=round((49.05-49.0)/49.0*100,2); r['holding_status']='續抱（D0，反轉健康）'
t['tomorrow_recommendations']=[]
ex=[('2313','華通','收盤202.0<停損235.98'),('2330','台積電零股','L4 賣超（已決）'),('6770','力積電','收盤66.6<停損73.26'),
    ('2337','旺宏','收盤95.4<停損147.6；L4 -19,002 張佔 46.7%'),('3090','日電貿','收盤148.5<停損256.5；L4 8.5%'),
    ('1301','台塑','10-20 L4、損益>停利20%'),('4938','和碩','已決不重評')]
t['tomorrow_opening_exits']=[{'stock_code':a,'stock_name':b,'category':'已決事項（v8.3.7）','reason':c} for a,b,c in ex]
t['after_market_check_20261030']={'t86':'10-30 T86 未公布（14:3x），法人欄位為 10-29 T86','stale_series':['2867'],
 'holdings_stop_loss':{'6770':[66.6,73.26,True],'2337':[95.4,147.6,True],'2313':[202.0,235.98,True],'3090':[148.5,256.5,True],'1301':[72.5,54.08,False],'4938':[102.5,76.5,False]}}
save(tp,t)
print('ok',[(r['stock_code'],r['result'],r['return_pct']) for r in removed])
