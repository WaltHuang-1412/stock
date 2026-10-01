import json
TODAY='2026-10-01'
S = {  # code: (src_date, close, D, note)
 '2886': ('2026-09-23', 48.85, 'D4/10', '鐵律③ L4（v8.3.3 待複核兩次成立：09-29 T86 賣超 -1,613 張＝盤前 7.4% → 12:30 9.8% → 盤後 9.8% 皆 ≥5%；09-30 T86 再賣 -1,058 張＝6.4%／盤後 6.1%）→ 09-30 盤後定案、10-01 開盤出場（v8.3.7 已決事項）；收盤價入帳 v8.3.2'),
 '3702': ('2026-09-29', 119.0, 'D2/10', '鐵律③ L4（v8.3.3 待複核兩次成立：09-29 T86 賣超 -572 張＝盤前 5.8% → 12:30 6.3% → 盤後 6.3% 皆 ≥5%；09-30 T86 再賣 -348 張＝3.9% L2）→ 09-30 盤後定案、10-01 開盤出場（v8.3.7 已決事項，當日 +4.39% 不重評）；收盤價入帳 v8.3.2，高於推薦價故記 success'),
 '2376': ('2026-09-30', 368.5, 'D1/10', '鐵律③ L4（09-30 T86 賣超 -581 張＝盤前 9.4%／盤中 12.3%／盤後 12.3% ≥8%；10 日累計 +3,481 為正但佔比 ≥8% 不受 v8.3.3 保護）→ 09-30 盤後定案、10-01 開盤出場（v8.3.7 已決事項，當日 +2.79% 不重評）；收盤價入帳 v8.3.2，高於推薦價故記 success'),
}
out = {}
for code, (d, close, D, note) in S.items():
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
            out[code] = dict(date=d, name=r['stock_name'], price=p, close=close, ret=ret, result=result, D=D, note=note, key=key,
                             target=r.get('target_price'), stop=r.get('stop_loss'))
    assert hit == 1, (code, hit)
    json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
json.dump(out, open('data/2026-10-01/_after/settlements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v['name'], v['date'], v['key'], v['price'], v['close'], v['ret'], v['result'])
