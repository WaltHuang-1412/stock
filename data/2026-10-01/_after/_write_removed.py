import json
f='data/tracking/tracking_2026-10-01.json'
t=json.load(open(f,encoding='utf-8'))
S=json.load(open('data/2026-10-01/_after/settlements.json',encoding='utf-8'))
rm=[]
for c,v in S.items():
    d={"stock_code":c,"stock_name":v['name'],"track":"A","recommend_date":v['date'],"recommend_price":v['price'],
       "settled_price":v['close'],"last_close":v['close'],"return_pct":v['ret'],"result":v['result'],"holding_days":v['D'],
       "removal_reason":v['note'],"settled_by":"已決事項開盤出場（v8.3.7 Step 4-0，09-30 盤後定案；盤後收盤價入帳 v8.3.2）",
       "sync_note":f"v8.3.7 三處同步：①tracking_{v['date']}.json ②本檔 removed_stocks ③predictions.json"}
    if v['result']=='fail': d['fail_reason']=v['note']
    else: d['success_note']=v['note']
    rm.append(d)
t['removed_stocks']=rm
for r in t.get('opening_exits_today',[]):
    v=S.get(r['stock_code'])
    if v: r.update({'executed':True,'settled_price':v['close'],'return_pct':v['ret'],'result':v['result'],'settled_date':'2026-10-01'})
# 2395 第二次複核 → 定案（先落檔，防流程中斷）
for p in t['pending_review_v833']:
    if p['stock_code']=='2395':
        p['review_2_result']='7.5%（14:33 盤後取樣，09-30 T86 分子 -178 張未變、avg_5day_volume 分母）≥5% → 第二次複核成立'
        p['review_2_level']='L4'
        p['verdict']='兩次複核皆 ≥5% → 10-02 開盤出場（已決事項，10-02 盤前 Step 4-0 不重評）'
t['tomorrow_opening_exits']=[{'stock_code':'2395','stock_name':'研華','category':'v8.3.3 待複核兩次成立 → 鐵律③ L4','recommend_date':'2026-09-16','recommend_price':685.0,
  'last_close':723.0,'return_pct_at_close':5.55,
  'reason':'09-30 T86 -178 張：盤前 7.6%（待複核）→ 12:30 7.5% → 盤後 14:33 7.5%，兩次複核皆 ≥5%；10-02 開盤出場，入帳價用 10-02 收盤（v8.3.2）。10-02 為 D10 到期日，到期結算與出場同日、同以收盤價入帳',
  'decided_on':'2026-10-01 盤後'}]
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(rm))
