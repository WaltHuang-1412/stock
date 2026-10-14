import json
D = '2026-10-14'
def load(d): return json.load(open(f'data/tracking/tracking_{d}.json', encoding='utf-8'))
def save(d, t): json.dump(t, open(f'data/tracking/tracking_{d}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

S = {
 '3037': ('2026-10-12', 'fail', 1185.0, 'L4：10-13 T86 -2,311 張佔 21.8%（≥8% 不受待複核保護），10-14 盤前已決開盤出場，入帳用當日收盤 1185.0（-6.69%）；收盤仍高於停損 1143（距 3.5%），非停損觸發；ABF 載板同鏈弱', '鐵律③L4（盤前已決）'),
 '3711': ('2026-10-12', 'success', 747.0, 'L4：10-13 T86 -2,546 張佔 20.3%，10-14 盤前已決開盤出場，入帳用當日收盤 747.0（+0.40%，高於推薦價）；推薦隔日即被法人反手賣超', '鐵律③L4（盤前已決）'),
}
t = load(D)
removed = []
names = {}
by = {}
for c, v in S.items():
    by.setdefault(v[0], []).append(c)
for src, codes in by.items():
    s = load(src)
    for k in ('recommendations', 'track_b_recommendations'):
        for r in s.get(k, []):
            c = r['stock_code']
            if c in codes and r.get('result', 'holding') == 'holding':
                _, res, px, why, b = S[c]
                rp = r['recommend_price']
                ret = round((px / rp - 1) * 100, 2)
                r.update({'result': res, 'actual_close': px, 'settled_date': D, 'settled_price': px, 'return_pct': ret,
                          'sync_note': f'{D} 盤後結算（{b}）；同步寫入 來源檔／tracking_{D}.removed_stocks／predictions'})
                r['fail_reason' if res == 'fail' else 'success_note'] = why
                names[c] = (r['stock_name'], rp, ret)
    save(src, s)
for c, (src, res, px, why, b) in S.items():
    n, rp, ret = names[c]
    removed.append({'stock_code': c, 'stock_name': n, 'recommend_date': src, 'recommend_price': rp, 'result': res,
                    'settled_price': px, 'last_close': px, 'return_pct': ret, 'removal_reason': why,
                    'settled_by': b, 'source_tracking': f'tracking_{src}.json'})
t['removed_stocks'] = removed
closes = {'3231': (187.0, 187.0), '8046': (1430.0, 1440.0), '3189': (1050.0, 1040.0), '2002': (19.5, 19.15), '2886': (51.1, 50.9),
          '3443': (8245.0, 8095.0), '2892': (40.65, 40.5), '3037': (1185.0, 1180.0), '3711': (747.0, 740.0)}
t['phase'] = 'after_market'
for lst in ('recommendations', 'carry_over_recommendations'):
    for r in t.get(lst, []):
        c = r['stock_code']
        if c in S:
            _, res, px, why, b = S[c]
            r.update({'result': res, 'actual_close': px, 'close_price': px, 'settled_date': D, 'settled_price': px,
                      'return_pct': round((px / r['recommend_price'] - 1) * 100, 2)})
            r['fail_reason' if res == 'fail' else 'success_note'] = why
        elif c in closes:
            px, prev = closes[c]
            r.update({'actual_close': px, 'close_price': px, 'return_pct': round((px / r['recommend_price'] - 1) * 100, 2),
                      'result': 'holding', 'change_percent': round((px / prev - 1) * 100, 2)})
t['settlement_today'] = {'settled': [{'stock_code': x['stock_code'], 'stock_name': x['stock_name'], 'result': x['result'],
                                      'settled_price': x['settled_price'], 'return_pct': x['return_pct']} for x in removed],
                         'holding_count': 8, 'frozen': ['2867'],
                         'd_counts_note': 'Yahoo 10-12 日K 今日已恢復（3443 10-12=8100），settlement_checker D 計數與實際交易日相符（3443 D5：10-07/08/12/13/14）'}
t['yesterday_verification'] = {'date': D, 'settled_count': 2, 'success': 1, 'fail': 1,
                               'note': '3711 日月光投控 L4 出場 +0.40%（success）；3037 欣興 L4 出場 -6.69%（fail）'}
t['market_close'] = {'taiex': 48625.83, 'change_pct': 0.59, 'prev': 48341.31, 'source': 'Yahoo ^TWII 13:33（volume=0 盤後即時列視同收盤）',
                     'institutional_total': 'BFI82U／T86 10-14 於 14:33 查無（n=13）'}
t['stop_loss_check_after_v8310'] = {'time': '2026-10-14 14:50', 'basis': 'get_close_series 末筆＝2026-10-14 收盤', 'results': [
    {'stock_code': '2330', 'stock_name': '台積電', 'close': 2490.0, 'stop_loss': None, 'hit': '不適用（yaml 無 stop_loss）；已決出場'},
    {'stock_code': '6770', 'stock_name': '力積電', 'close': 71.0, 'stop_loss': 73.26, 'hit': '🛑 觸及（已決，yaml 未更新）'},
    {'stock_code': '2337', 'stock_name': '旺宏', 'close': 110.0, 'stop_loss': 147.6, 'hit': '🛑 觸及（已決）'},
    {'stock_code': '2313', 'stock_name': '華通', 'close': 250.5, 'stop_loss': 235.98, 'hit': '✅ 未觸發（距 6.2%；已決 L4）'},
    {'stock_code': '3090', 'stock_name': '日電貿', 'close': 183.5, 'stop_loss': 256.5, 'hit': '🛑 觸及（已決）'},
    {'stock_code': '1301', 'stock_name': '台塑', 'close': 88.9, 'stop_loss': 54.08, 'hit': '✅ 未觸發（已決 L4 出場；損益約 +48% 遠超 yaml 停利 20%）'},
    {'stock_code': '4938', 'stock_name': '和碩', 'close': 100.0, 'stop_loss': 76.5, 'hit': '✅ 未觸發（已決）'}]}
t['two_day_drawdown_after'] = {'basis': '10-12 收盤→10-14 收盤', 'triggered': [], 'near': '3037 欣興 -5.58%（已 L4 出場）'}
t['holdings_reversal_scan'] = 'data/2026-10-14/_after/reversal_stdout.txt（17 檔；仍為 10-13 T86）'
def ex(c, n, cat, reason): return {'stock_code': c, 'stock_name': n, 'category': cat, 'reason': reason}
t['tomorrow_opening_exits'] = [
    ex('6770', '力積電', '持倉 my_holdings.yaml（已決 L4＋鐵律①）', '收 71.0 < 停損 73.26；10-13 T86 -107,315 張；yaml 未更新'),
    ex('2337', '旺宏', '持倉 my_holdings.yaml（已決，鐵律①）', '收 110.0 < 停損 147.6；10-13 T86 -19,865 張'),
    ex('3090', '日電貿', '持倉 my_holdings.yaml（已決，鐵律①）', '收 183.5 < 停損 256.5；10-13 T86 -422 張（7.5%）'),
    ex('1301', '台塑', '持倉 my_holdings.yaml（已決 L4，10-13 定案）', '10-12 T86 -18,665 張定案；10-13 T86 仍賣 -3,442；損益約 +48% 遠超 yaml 停利 20%；近 6 日 +29.8% 接近注意門檻'),
    ex('2313', '華通', '持倉 my_holdings.yaml（已決 L4）', '已決不重評；10-13 T86 -4,472 張（8.8%）；收 250.5 未觸停損 235.98'),
    ex('4938', '和碩', '持倉 my_holdings.yaml（已決 L4）', '已決不重評；10-13 T86 +16,968 張再度翻買已揭露；收 100.0'),
    ex('2330', '台積電', '持倉 my_holdings.yaml 零股 0.15 張（已決）', '10-13 T86 -20,145 張；10-15 法說')]
t['tomorrow_pending_review'] = []
t['tomorrow_recommendations'] = []
t['tomorrow_recommendation_note'] = (
    '10-14 T86／BFI82U 14:33 查無（n=13），法人資料仍為 10-13 T86；不以舊 T86 補推（比照 10-08、10-12、10-13 盤後）。'
    '觀察逐檔：2408 南亞科 營收 2026-09 +576.6%（5 日回檔 -8.5% → +5）、持股比 +0.71%（+5），但不在 TOP50 買超、利多不漲，待 10-14 T86 確認法人動向；'
    '2377 微星 營收 +1.8% 不調整；3023 信邦 營收 +25.5% 但回檔僅 0.5% 不加分；2412 中華電 營收 +20.9% 回檔僅 2.1% 不加分，催化未對齊。'
    '→ 10-15 預估新推薦 0 檔（寧缺勿濫）。10-15 台積電法說為事件日，不開新倉。')
t['tomorrow_carry_over'] = [
    {'stock_code': c, 'stock_name': n, 'recommend_date': d, 'recommend_price': p, 'target_price': tp, 'stop_loss': sl}
    for c, n, d, p, tp, sl in [
        ('8046', '南電', '2026-10-12', 1475.0, 1593.0, 1327.5), ('3231', '緯創', '2026-10-12', 188.5, 203.6, 169.65),
        ('3189', '景碩', '2026-10-12', 1075.0, 1161.0, 967.5), ('3443', '創意', '2026-10-06', 8600.0, 9288.0, 7740.0),
        ('2002', '中鋼', '2026-10-13', 19.2, 20.74, 17.28), ('2886', '兆豐金', '2026-10-13', 50.0, 54.0, 45.0),
        ('2892', '第一金', '2026-10-13', 39.7, 42.88, 35.73), ('2867', '三商壽', '2026-08-17', 9.75, 10.73, 8.78)]]
t['watchlist_tomorrow'] = ['2408 南亞科（待 10-14 T86）', '2412 中華電', '2377 微星', '3023 信邦']
t['data_quality_after'] = ['10-14 T86／BFI82U 14:33 查無（n=13）；反轉等級為 10-13 T86，與盤前、盤中同一份',
                           'Yahoo 10-12 日K 已恢復，D 計數正常',
                           '序列對齊：非停滯者末日皆 10-14；2867 三商壽停於 08-19（凍結）',
                           '營收 4 檔皆 2026-09；外資持股比 4 檔皆 ≥10-08；盤前 JSON 已還原']
t['after_market_version'] = 'v1（10-14 T86 未公布）'
save(D, t)
print('ok', [x['stock_code'] for x in removed])
