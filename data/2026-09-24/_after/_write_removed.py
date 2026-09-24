import json
f='data/tracking/tracking_2026-09-24.json'
t=json.load(open(f,encoding='utf-8'))
S=json.load(open('data/2026-09-24/_after/settlements.json',encoding='utf-8'))
by={'3711':'settlement_checker 機械判定（收盤≥目標）','3042':'settlement_checker 機械判定（收盤≥目標）',
    '2891':'已決事項（v8.3.7，09-23 待複核定案）→ 開盤出場清單；收盤價入帳 v8.3.2'}
rm=[]
for c,v in S.items():
    d={"stock_code":c,"stock_name":v['name'],"track":"A","recommend_date":v['date'],"recommend_price":v['price'],
       "settled_price":v['close'],"last_close":v['close'],"return_pct":v['ret'],"result":v['result'],"holding_days":v['D'],
       "removal_reason":v['note'],"settled_by":by.get(c,'開盤出場清單（盤前 L4，盤後收盤價入帳 v8.3.2）'),
       "sync_note":f"v8.3.7 三處同步：①tracking_{v['date']}.json ②本檔 removed_stocks ③predictions.json"}
    if v['result']=='fail': d['fail_reason']=v['note']
    rm.append(d)
t['removed_stocks']=rm
for r in t.get('carry_over_recommendations',[]):
    if r['stock_code'] in ('3711','3042'):
        v=S[r['stock_code']]
        r.update({'result':'success','actual_close':v['close'],'settled_date':'2026-09-24','settled_price':v['close'],
                  'return_pct':v['ret'],'holding_days':v['D'],'success_note':v['note']})
for r in t.get('opening_exits_today',[]):
    v=S.get(r['stock_code'])
    if v: r.update({'executed':True,'settled_price':v['close'],'return_pct':v['ret'],'result':v['result']})
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(rm))
