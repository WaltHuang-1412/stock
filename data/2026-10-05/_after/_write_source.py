import json
TODAY='2026-10-05'
A='data/2026-10-05/_after/'
EX='鐵律③ L4（10-02 T86 賣超 {t} 張＝{p}% ≥8%，不受 v8.3.3 保護）→ 10-02 盤後定案、10-05 開盤出場（v8.3.7 已決事項，當日 {c:+.2f}% 不重評）；收盤價入帳 v8.3.2，{w}'
BY='已決事項開盤出場（v8.3.7 Step 4-0，10-02 盤後定案；盤後收盤價入帳 v8.3.2）'
S = {  # code: (src_date, close, D, note, settled_by)
 '3037': ('2026-10-02', 1325.0, 'D1/10', 'D1 收盤 1325.0 ≥ 目標價 1312.0（settlement_checker 機械判定）；10-02 D0 收 1305.0 未結算，10-05 盤中高 1,420', 'settlement_checker 觸及目標價'),
 '3231': ('2026-10-02', 189.5, 'D1/10', EX.format(t='-22,097', p=68.8, c=1.61, w='低於推薦價故記 fail'), BY),
 '2330': ('2026-10-02', 2575.0, 'D1/10', EX.format(t='-5,344', p=24.9, c=3.00, w='高於推薦價故記 success'), BY),
 '2344': ('2026-10-02', 181.0, 'D1/10', EX.format(t='-7,123', p=11.4, c=1.12, w='高於推薦價故記 success'), BY),
 '2379': ('2026-10-02', 755.0, 'D1/10', EX.format(t='-285', p=9.2, c=0.13, w='低於推薦價故記 fail'), BY),
}
out = {}
for code, (d, close, D, note, by) in S.items():
    f = f'data/tracking/tracking_{d}.json'
    t = json.load(open(f, encoding='utf-8'))
    hit = 0
    for key in ('recommendations', 'track_b_recommendations'):
        for r in t.get(key, []):
            if r.get('stock_code') != code: continue
            if r.get('recommend_date') and r['recommend_date'] != d: continue
            assert r.get('result', 'holding') == 'holding', (code, r.get('result'))
            p = r['recommend_price']
            ret = round((close / p - 1) * 100, 2)
            result = 'success' if close > p else 'fail'
            r.update({'result': result, 'actual_close': close, 'settled_date': TODAY, 'settled_price': close,
                      'return_pct': ret, 'holding_days': 1, 'holding_days_label': D,
                      'sync_note': f'v8.3.7 三處同步：①本檔 ②tracking_{TODAY}.json removed_stocks ③predictions.json'})
            r.pop('holding_status', None)
            if result == 'success': r['success_note'] = note
            else: r['fail_reason'] = note
            hit += 1
            out[code] = dict(date=d, name=r['stock_name'], price=p, close=close, ret=ret, result=result, D=D, note=note, key=key, by=by,
                             target=r.get('target_price'), stop=r.get('stop_loss'))
    assert hit == 1, (code, hit)
    json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(out, open(A+'settlements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v['name'], v['date'], v['key'], v['price'], v['close'], v['ret'], v['result'])
f=f'data/tracking/tracking_{TODAY}.json'
t=json.load(open(f,encoding='utf-8'))
rm=[]
for c,v in out.items():
    d={"stock_code":c,"stock_name":v['name'],"track":"A","recommend_date":v['date'],"recommend_price":v['price'],
       "settled_price":v['close'],"last_close":v['close'],"return_pct":v['ret'],"result":v['result'],"holding_days":v['D'],
       "removal_reason":v['note'],"settled_by":v['by'],
       "sync_note":f"v8.3.7 三處同步：①tracking_{v['date']}.json ②本檔 removed_stocks ③predictions.json"}
    d['fail_reason' if v['result']=='fail' else 'success_note']=v['note']
    rm.append(d)
t['removed_stocks']=rm
for r in t.get('opening_exits_today',[]):
    v=out.get(r['stock_code'])
    if v: r.update({'executed':True,'settled_price':v['close'],'return_pct':v['ret'],'result':v['result'],'settled_date':TODAY})
    elif r['stock_code']=='4938': r.update({'executed':'持倉決議，流程不代改 yaml；10-05 收盤 88.7（-0.56%）','last_close_1005':88.7})
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(rm))
