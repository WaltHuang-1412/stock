import json
TODAY='2026-10-02'
EX='鐵律③ L4（10-01 T86 賣超 {t} 張＝{p}% ≥8%，不受 v8.3.3 保護）→ 10-01 盤後定案、10-02 開盤出場（v8.3.7 已決事項，當日 {c:+.2f}% 不重評）；收盤價入帳 v8.3.2，高於推薦價故記 success'
S = {  # code: (src_date, close, D, note, settled_by)
 '5876': ('2026-09-16', 48.95, 'D10/10', 'D10 到期：收盤 48.95 ≤ 推薦價 49.8（settlement_checker 機械判定）；持有期間未觸停損 44.82、未達目標 54.0', 'settlement_checker D10 到期'),
 '2412': ('2026-09-16', 146.0, 'D10/10', 'D10 到期：收盤 146.0 > 推薦價 143.5（settlement_checker 機械判定）；未達目標 153.0', 'settlement_checker D10 到期'),
 '2395': ('2026-09-16', 716.0, 'D10/10', 'D10 到期：收盤 716.0 > 推薦價 685.0（settlement_checker 機械判定）；同日亦為 v8.3.3 待複核兩次成立之已決事項開盤出場（09-30 T86 -178 張：7.6% → 7.5% → 7.5%），兩者同以 10-02 收盤價入帳，結果一致', 'settlement_checker D10 到期＋已決事項開盤出場（同日）'),
 '1303': ('2026-09-30', 260.0, 'D2/10', EX.format(t='-11,084', p=14.3, c=2.36), '已決事項開盤出場（v8.3.7 Step 4-0，10-01 盤後定案；盤後收盤價入帳 v8.3.2）'),
 '1301': ('2026-10-01', 68.3, 'D1/10', EX.format(t='-5,982', p=21.3, c=2.25), '已決事項開盤出場（v8.3.7 Step 4-0，10-01 盤後定案；盤後收盤價入帳 v8.3.2）'),
 '1326': ('2026-10-01', 71.7, 'D1/10', EX.format(t='-10,572', p=47.1, c=5.91), '已決事項開盤出場（v8.3.7 Step 4-0，10-01 盤後定案；盤後收盤價入帳 v8.3.2）'),
 '6505': ('2026-10-01', 100.0, 'D1/10', EX.format(t='-6,544', p=27.8, c=6.16), '已決事項開盤出場（v8.3.7 Step 4-0，10-01 盤後定案；盤後收盤價入帳 v8.3.2）'),
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
                      'return_pct': ret, 'holding_days': D,
                      'sync_note': f'v8.3.7 三處同步：①本檔 ②tracking_{TODAY}.json removed_stocks ③predictions.json'})
            r.pop('holding_status', None)
            if result == 'success': r['success_note'] = note
            else: r['fail_reason'] = note
            hit += 1
            out[code] = dict(date=d, name=r['stock_name'], price=p, close=close, ret=ret, result=result, D=D, note=note, key=key, by=by,
                             target=r.get('target_price'), stop=r.get('stop_loss'))
    assert hit == 1, (code, hit)
    json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(out, open('data/2026-10-02/_after/settlements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v['name'], v['date'], v['key'], v['price'], v['close'], v['ret'], v['result'])
# ② removed_stocks（先落檔，防流程中斷）
f='data/tracking/tracking_2026-10-02.json'
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
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(rm))
