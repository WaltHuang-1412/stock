import json
f='data/tracking/tracking_2026-10-05.json'
t=json.load(open(f,encoding='utf-8'))
rows=json.load(open('data/2026-10-05/_after/holding_rows.json',encoding='utf-8'))
EXTRA={'8150':'；盤中高 133.0 曾越目標 124.5，收盤 124.0 低於目標 0.5 元 → 不結算（checker 以收盤價判定）；⚠️ 自算處置預警連續達標 4 天、最快 10-06 處置',
 '6257':'；盤中高 275.0 曾越目標 274.5 後回落；⚠️ 10/06 法說會（凱基聯合法說 14:30），當日不加碼',
 '3711':'；盤中高 758.0，距目標 759.0 差 1 元',
 '2327':'；盤中高 658.0 曾越目標 650.0，收平盤 626.0',
 '1326':'；D0 當日不判定；🔥覆寫型推薦，不加碼'}
def upd(r):
    k=r['stock_code']
    if k not in rows: return
    v=rows[k]
    r['actual_close']=v['cl']; r['close_price']=v['cl']; r['current_price']=v['cl']; r['change_percent']=v['chg']; r['return_pct_at_close']=v['ret']
    r['result']='holding'; r['holding_days']=v['D']; r['holding_days_label']=f"D{v['D']}/10"
    r['holding_status']=f"續抱：收盤 {v['cl']}（今日 {v['chg']:+.2f}%，相對推薦價 {v['ret']:+.2f}%）；鐵律①停損、②2 日 -10% 無觸發（2 日 {v['two']:+.2f}%）；距停損 {v['dist_stop']:+.2f}%、距目標 {v['dist_target']:.2f}%{EXTRA.get(k,'')}；鐵律③待 10-05 T86 公布後重掃"
for r in t['recommendations']: upd(r)
for r in t['carry_over_recommendations']:
    if r['stock_code'] in ('3037',): 
        r.update({'result':'success','actual_close':1325.0,'close_price':1325.0,'current_price':1325.0,'change_percent':rows['3037']['chg'],'settled_date':'2026-10-05','settled_price':1325.0,'return_pct':9.05,'holding_days':1,'holding_days_label':'D1/10','holding_status':'已結算（success，+9.05%）：D1 收盤 1325.0 ≥ 目標價 1312.0'})
    else: upd(r)
t['yesterday_verification']={"date":"2026-10-05","settled_count":5,"success_count":3,"fail_count":2,"accuracy":60.0,
 "results":[{"stock_code":r['stock_code'],"stock_name":r['stock_name'],"recommend_date":r['recommend_date'],"recommend_price":r['recommend_price'],"settled_price":r['settled_price'],"return_pct":r['return_pct'],"result":r['result'],"removal_reason":r['removal_reason']} for r in t['removed_stocks']],
 "note":"1 筆為 settlement_checker 機械判定觸及目標價（3037 欣興 success），4 筆為 10-02 盤後定案的鐵律③ L4 開盤出場（v8.3.7 已決事項：2330 台積電／2344 華邦電 success、3231 緯創／2379 瑞昱 fail），入帳價皆用 10-05 收盤"}
t.setdefault('tomorrow_recommendations',[])
t['tomorrow_recommendations_note']="v1（14:4x）：10-05 T86 尚未公布，明日推薦暫列 0 檔；T86 公布後重掃改寫"
t['after_market']={"report_time":"2026-10-05 14:45（v1，10-05 T86 未公布）","taiex_close":49712.04,"taiex_change_pct":2.55,"taiex_change_pts":1236.30,
 "taiex_source":"Yahoo ^TWII 日K 10-05 收盤與 regularMarketPrice（13:33）一致；基準 10-02 收 48,475.74",
 "t86_today_published":False,"settled_today":5,"settled_win":3,"settled_loss":2,"settled_accuracy_today":60.0}
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
for r in t['recommendations']+t['carry_over_recommendations']: print(r['stock_code'],r.get('result'),r.get('holding_days'),r.get('close_price'),str(r.get('holding_status'))[:50])
