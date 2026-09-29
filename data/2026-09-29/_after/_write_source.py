import json
TODAY='2026-09-29'
S = {  # code: (src_date, close, result, D, note)
 '8046': ('2026-09-23', 1270.0, 'success', 'D2/10', '收盤 1270.0 ≥ 目標 1260.0（settlement_checker 機械判定）'),
 '2303': ('2026-09-18', 153.5, None, 'D5/10', '鐵律③ L4（09-24 T86 賣超 -44,181 張＝盤前 19.8%／盤中 21.7%／盤後 21.7% ≥8%）→ 09-29 開盤出場；收盤價入帳 v8.3.2'),
 '6770': ('2026-09-24', 72.3, None, 'D1/10', '鐵律③ L4（09-24 T86 賣超 -44,817 張＝盤前 37.6%／盤中 39.1%／盤後 39.1% ≥8%）→ 09-29 開盤出場；收盤價入帳 v8.3.2'),
 '2408': ('2026-09-24', 506.0, None, 'D1/10', '鐵律③ L4（09-24 T86 賣超 -22,678 張＝盤前 41.2%／盤中 42.1%／盤後 42.1% ≥8%、10 日累計為負）→ 09-29 開盤出場；收盤價入帳 v8.3.2'),
 '2317': ('2026-09-24', 250.5, None, 'D1/10', '鐵律③ L4（09-24 T86 賣超 -24,232 張＝盤前 76.5%／盤中 73.2%／盤後 73.2% ≥8%、10 日累計為負）→ 09-29 開盤出場；收盤價入帳 v8.3.2'),
}
out = {}
for code, (d, close, res, D, note) in S.items():
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
            result = res or ('success' if close > p else 'fail')
            r.update({'result': result, 'actual_close': close, 'settled_date': TODAY, 'settled_price': close,
                      'return_pct': ret, 'holding_days': D,
                      'sync_note': f'v8.3.7 三處同步：①本檔 ②tracking_{TODAY}.json removed_stocks ③predictions.json'})
            r.pop('holding_status', None)
            if result == 'success': r['success_note'] = note
            else: r['fail_reason'] = note
            hit += 1
            out[code] = dict(date=d, name=r['stock_name'], price=p, close=close, ret=ret, result=result, D=D, note=note, key=key,
                             target=r.get('target_price'), stop=r.get('stop_loss'))
    assert hit == 1, (code, hit)
    json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(out, open('data/2026-09-29/_after/settlements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v['name'], v['date'], v['key'], v['price'], v['close'], v['ret'], v['result'])
