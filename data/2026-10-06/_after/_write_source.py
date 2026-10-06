import json
TODAY='2026-10-06'
A='data/2026-10-06/_after/'
BY_EXIT='已決事項開盤出場（v8.3.7 Step 4-0，10-05 盤後定案；盤後收盤價入帳 v8.3.2）'
BY_TGT='settlement_checker 觸及目標價'
S = {  # code: (src_date, close, D, note, settled_by)
 '6257': ('2026-10-01', 286.0, 'D3/10', 'D3 收盤 286.0 ≥ 目標價 274.5（settlement_checker 機械判定，結算優先）；同日亦為已決事項鐵律③ L4（10-05 T86 -1,131 張＝8.8%）開盤出場，兩者皆指向出場，入帳價一律用 10-06 收盤（v8.3.2）；當日 +10.00%（法說會日）', BY_TGT),
 '8150': ('2026-10-02', 127.5, 'D2/10', 'D2 收盤 127.5 ≥ 目標價 124.5（settlement_checker 機械判定，結算優先於 v8.3.3 待複核）；待複核計時器（10-05 盤後啟動，複核① 12:30 5.5% 成立）因結算而終止；當日 +2.82%', BY_TGT),
 '2609': ('2026-10-01', 59.2, 'D3/10', '鐵律③ L4（10-05 T86 賣超 -2,729 張＝18.3% ≥8%，不受 v8.3.3 保護）→ 10-05 盤後定案、10-06 開盤出場（v8.3.7 已決事項，當日 +0.85% 不重評）；收盤價入帳 v8.3.2，低於推薦價故記 fail', BY_EXIT),
 '2327': ('2026-10-02', 625.0, 'D2/10', '鐵律③ L4（10-05 T86 賣超 -9,285 張＝17.2% ≥8%，不受 v8.3.3 保護）→ 10-05 盤後定案、10-06 開盤出場（v8.3.7 已決事項，當日 -0.16% 不重評）；收盤價入帳 v8.3.2，高於推薦價故記 success', BY_EXIT),
}
DN={'D3/10':3,'D2/10':2}
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
                      'return_pct': ret, 'holding_days': DN[D], 'holding_days_label': D,
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
    dd={"stock_code":c,"stock_name":v['name'],"track":"A","recommend_date":v['date'],"recommend_price":v['price'],
       "settled_price":v['close'],"last_close":v['close'],"return_pct":v['ret'],"result":v['result'],"holding_days":v['D'],
       "removal_reason":v['note'],"settled_by":v['by'],
       "sync_note":f"v8.3.7 三處同步：①tracking_{v['date']}.json ②本檔 removed_stocks ③predictions.json"}
    dd['fail_reason' if v['result']=='fail' else 'success_note']=v['note']
    rm.append(dd)
t['removed_stocks']=rm
closes={'6770':74.3,'4938':90.0}
for r in t.get('opening_exits_intraday_status',[]):
    v=out.get(r['stock_code'])
    if v: r.update({'executed':True,'settled_price':v['close'],'return_pct':v['ret'],'result':v['result'],'settled_date':TODAY})
    elif r['stock_code'] in closes:
        r.update({'executed':'持倉決議，流程不代改 yaml','close_1006':closes[r['stock_code']]})
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('removed',len(rm))
