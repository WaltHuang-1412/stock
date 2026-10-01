import json
f='data/tracking/tracking_2026-09-30.json'
t=json.load(open(f,encoding='utf-8'))
S=json.load(open('data/2026-09-30/_after/settlements.json',encoding='utf-8'))
rm=[]
for c,v in S.items():
    d={"stock_code":c,"stock_name":v['name'],"track":"A","recommend_date":v['date'],"recommend_price":v['price'],
       "settled_price":v['close'],"last_close":v['close'],"return_pct":v['ret'],"result":v['result'],"holding_days":v['D'],
       "removal_reason":v['note'],"settled_by":"已決事項開盤出場（v8.3.7 Step 4-0，09-29 盤後定案；盤後收盤價入帳 v8.3.2）",
       "sync_note":f"v8.3.7 三處同步：①tracking_{v['date']}.json ②本檔 removed_stocks ③predictions.json"}
    if v['result']=='fail': d['fail_reason']=v['note']
    rm.append(d)
t['removed_stocks']=rm
for r in t.get('opening_exits_today',[]):
    v=S.get(r['stock_code'])
    if v: r.update({'executed':True,'settled_price':v['close'],'return_pct':v['ret'],'result':v['result'],'settled_date':'2026-09-30'})
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(rm))
