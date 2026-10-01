import json
TODAY='2026-09-30'
S = {  # code: (src_date, close, result, D, note)
 '4904': ('2026-09-15', 103.5, None, 'D9/10', '鐵律③ L4（09-29 T86 賣超 -454 張＝盤前 9.3%／盤中 13.1%／盤後 13.1% ≥8%；10 日累計 +4,509 為正但佔比 ≥8% 不受 v8.3.3 保護）→ 09-29 盤後定案、09-30 開盤出場（v8.3.7 已決事項）；收盤價入帳 v8.3.2'),
 '2892': ('2026-09-18', 38.65, None, 'D6/10', '鐵律③ L4（09-29 T86 賣超 -3,085 張＝盤前 13.2%／盤中 16.9%／盤後 16.9% ≥8%；10 日累計 +56K 為正但佔比 ≥8% 不受 v8.3.3 保護）→ 09-29 盤後定案、09-30 開盤出場（v8.3.7 已決事項）；收盤價入帳 v8.3.2'),
 '2454': ('2026-09-22', 4920.0, None, 'D4/10', '鐵律③ L4（09-29 T86 賣超 -4,812 張＝盤前 57.0%／盤中 54.4%／盤後 54.4% ≥8%；10 日累計 +6,238 為正但佔比 ≥8% 不受 v8.3.3 保護）→ 09-29 盤後定案、09-30 開盤出場（v8.3.7 已決事項）；收盤價入帳 v8.3.2'),
 '2609': ('2026-09-23', 59.4, None, 'D3/10', '鐵律③ L4（09-29 T86 賣超 -6,231 張＝盤前 24.9%／盤中 30.7%／盤後 30.7% ≥8%；10 日累計 +34K 為正但佔比 ≥8% 不受 v8.3.3 保護）→ 09-29 盤後定案、09-30 開盤出場（v8.3.7 已決事項）；收盤價入帳 v8.3.2'),
 '6196': ('2026-09-29', 585.0, None, 'D1/10', '鐵律③ L4（09-29 T86 賣超 -346 張＝盤前 23.5%／盤中 24.1%／盤後 24.1% ≥8%；10 日累計 +1,306 為正但佔比 ≥8% 不受 v8.3.3 保護）→ 09-29 盤後定案、09-30 開盤出場（v8.3.7 已決事項，當日 +7.54% 不重評）；收盤價入帳 v8.3.2'),
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
json.dump(out, open('data/2026-09-30/_after/settlements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v['name'], v['date'], v['key'], v['price'], v['close'], v['ret'], v['result'])
