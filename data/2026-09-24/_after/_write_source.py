import json
S = {  # code: (src_date, close, result, D, note)
 '3711': ('2026-09-21', 699.0, 'success', 'D3/10', '收盤 699.0 ≥ 目標 695.0（settlement_checker 機械判定）'),
 '3042': ('2026-09-21', 203.0, 'success', 'D3/10', '收盤 203.0 ≥ 目標 201.0（settlement_checker 機械判定）'),
 '2891': ('2026-09-15', 68.5, None, 'D7/10', '鐵律③ L4 已決事項（v8.3.3 待複核定案：09-22 T86 -3,329 張兩次複核 8.4% ≥5%）→ 09-24 開盤出場；收盤價入帳 v8.3.2'),
 '2377': ('2026-09-15', 151.5, None, 'D7/10', '鐵律③ L4（09-23 T86 賣超 -629 張＝10.6% ≥8%）→ 09-24 開盤出場；收盤價入帳 v8.3.2'),
 '2382': ('2026-09-14', 338.5, None, 'D8/10', '鐵律③ L4（09-23 T86 賣超 -1,994 張＝13.7% ≥8%）→ 09-24 開盤出場；收盤價入帳 v8.3.2'),
 '5880': ('2026-09-17', 26.45, None, 'D5/10', '鐵律③ L4（09-23 T86 賣超 -2,367 張＝13.3% ≥8%）→ 09-24 開盤出場；收盤價入帳 v8.3.2'),
 '3481': ('2026-09-22', 49.55, None, 'D2/10', '鐵律③ L4（09-23 T86 賣超 -57,816 張＝25.1%、>50K 張、10 日累計 -64K）→ 09-24 開盤出場；收盤價入帳 v8.3.2'),
 '3023': ('2026-09-23', 311.0, None, 'D1/10', '鐵律③ L4（09-23 T86 賣超 -323 張＝53.9% ≥8%）→ 09-24 開盤出場；收盤價入帳 v8.3.2'),
}
out = {}
for code, (d, close, res, D, note) in S.items():
    f = f'data/tracking/tracking_{d}.json'
    t = json.load(open(f, encoding='utf-8'))
    hit = 0
    for r in t.get('recommendations', []):
        if r.get('stock_code') != code: continue
        p = r['recommend_price']
        ret = round((close / p - 1) * 100, 2)
        result = res or ('success' if close > p else 'fail')
        r.update({'result': result, 'actual_close': close, 'settled_date': '2026-09-24', 'settled_price': close,
                  'return_pct': ret, 'holding_days': D,
                  'sync_note': 'v8.3.7 三處同步：①本檔 ②tracking_2026-09-24.json removed_stocks ③predictions.json'})
        if result == 'success': r['success_note'] = note
        else: r['fail_reason'] = note
        hit += 1
        out[code] = dict(date=d, name=r['stock_name'], price=p, close=close, ret=ret, result=result, D=D, note=note)
    assert hit == 1, (code, hit)
    json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(out, open('data/2026-09-24/_after/settlements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v['name'], v['date'], v['price'], v['close'], v['ret'], v['result'])
