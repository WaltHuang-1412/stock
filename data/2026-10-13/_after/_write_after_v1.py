import json
D = '2026-10-13'
def load(d): return json.load(open(f'data/tracking/tracking_{d}.json', encoding='utf-8'))
def save(d, t): json.dump(t, open(f'data/tracking/tracking_{d}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# code: (來源檔, result, settled_price, reason, by)
S = {
 '2404': ('2026-10-07','fail',1140.0,'D2 收 1140.0 ≤ 停損 1201.5（鐵律①）；另 10-08→10-13 兩日 -12.64%（鐵律②）；10-12 T86 -420 張佔 33.7% L4（鐵律③）。三條同時觸發','settlement_checker＋鐵律'),
 '2609': ('2026-10-07','success',64.5,'D2 收 64.5 ≥ 目標 63.94（+8.95%）；外資連買、10-12 +25,714 張，航運催化延續','settlement_checker'),
 '1312': ('2026-10-08','success',17.65,'D1 收 17.65 ≥ 目標 16.25（+17.28%）；10-12 +10,645 張，石化催化；已近處置注意門檻','settlement_checker'),
 '3035': ('2026-10-02','fail',192.0,'v8.3.3 待複核定案（10-08 T86 -354 張 8.2~8.4%，複核①②皆 ≥5%）→ 10-13 開盤出場，入帳用當日收盤 192.0（-9.86%）；收盤仍高於停損 191.7 僅 0.16%，非停損觸發','鐵律③L4 已決（v8.3.3）'),
 '3042': ('2026-10-12','fail',195.5,'L4：10-12 T86 -2,212 張佔 10.4%（≥8% 不受待複核保護，10-13 盤前定案開盤出場），入帳用當日收盤 195.5（-7.35%）；推薦隔日即被法人反手賣超','鐵律③L4（盤前定案）'),
 '3026': ('2026-10-12','fail',806.0,'L4：10-12 T86 -1,941 張佔 17.1%（10-13 盤前定案開盤出場），入帳用當日收盤 806.0（-8.10%）；推薦隔日即被法人反手賣超；另有處置預警','鐵律③L4（盤前定案）'),
}
t13 = load(D)
removed = []
by_src = {}
for c, v in S.items():
    by_src.setdefault(v[0], []).append(c)
names = {}
for src, codes in by_src.items():
    t = load(src)
    for k in ('recommendations', 'track_b_recommendations'):
        for r in t.get(k, []):
            if r['stock_code'] in codes:
                c = r['stock_code']
                _, res, px, why, by = S[c]
                rp = r['recommend_price']
                ret = round((px / rp - 1) * 100, 2)
                r.update({'result': res, 'actual_close': px, 'settled_date': D, 'settled_price': px, 'return_pct': ret,
                          'sync_note': f'{D} 盤後結算（{by}）；同步寫入 來源檔／tracking_{D}.removed_stocks／predictions'})
                if res == 'fail':
                    r['fail_reason'] = why
                else:
                    r['success_note'] = why
                names[c] = (r['stock_name'], rp, ret)
    save(src, t)
for c, (src, res, px, why, by) in S.items():
    n, rp, ret = names[c]
    removed.append({'stock_code': c, 'stock_name': n, 'recommend_date': src, 'recommend_price': rp, 'result': res,
                    'settled_price': px, 'last_close': px, 'return_pct': ret, 'removal_reason': why,
                    'settled_by': by, 'source_tracking': f'tracking_{src}.json'})
t13['removed_stocks'] = removed

closes = {'3037': (1180.0, 1255.0), '8046': (1440.0, 1440.0), '3231': (187.0, 189.5), '3711': (740.0, 762.0),
          '2002': (19.15, None), '2886': (50.9, None), '2892': (40.5, None), '3189': (1040.0, 1060.0), '3443': (8095.0, 8100.0)}
t13['phase'] = 'after_market'
for lst in ('recommendations', 'carry_over_recommendations'):
    for r in t13.get(lst, []):
        c = r['stock_code']
        if c in S:
            _, res, px, why, by = S[c]
            r.update({'result': res, 'actual_close': px, 'close_price': px, 'settled_date': D, 'settled_price': px,
                      'return_pct': round((px / r['recommend_price'] - 1) * 100, 2)})
            r['fail_reason' if res == 'fail' else 'success_note'] = why
        elif c in closes:
            px, prev = closes[c]
            r.update({'actual_close': px, 'close_price': px, 'return_pct': round((px / r['recommend_price'] - 1) * 100, 2), 'result': 'holding'})
            if prev:
                r['change_percent'] = round((px / prev - 1) * 100, 2)
t13['settlement_today'] = {
    'settled': [{'stock_code': x['stock_code'], 'stock_name': x['stock_name'], 'result': x['result'], 'settled_price': x['settled_price'], 'return_pct': x['return_pct']} for x in removed],
    'holding_count': 10, 'frozen': ['2867'],
    'd_counts_note': 'settlement_checker 的 D 計數少計 10-12（Yahoo 10-12 日K close/volume=None 被略過）：3035 實為 D6、2404/2609 實為 D3、1312 實為 D2；沿用腳本值，D10 日期須人工 +1 交易日'}
t13['yesterday_verification'] = {'date': D, 'settled_count': 6, 'success': 2, 'fail': 4,
    'note': '2 勝（陽明、國喬，D1-D2 達標）／4 負（漢唐停損＋三鐵律；智原、晶技、禾伸堂為 L4 出場）'}
t13['market_close'] = {'taiex': 48341.31, 'change_pct': -1.94, 'prev': 49301.96, 'source': 'Yahoo ^TWII（13:33 報價，volume=0 為盤後即時列，視同收盤）',
                       'institutional_total': 'BFI82U／T86 10-13 於 14:31 查無（n=12）'}
t13['stop_loss_check_after_v8310'] = {'time': '2026-10-13 14:40', 'basis': 'get_close_series 末筆＝2026-10-13 收盤', 'results': [
    {'stock_code': '2330', 'stock_name': '台積電', 'close': 2490.0, 'stop_loss': None, 'hit': '不適用（yaml 無 stop_loss）；已決出場'},
    {'stock_code': '6770', 'stock_name': '力積電', 'close': 67.5, 'stop_loss': 73.26, 'hit': '🛑 觸及（已決，yaml 未更新）'},
    {'stock_code': '2337', 'stock_name': '旺宏', 'close': 106.5, 'stop_loss': 147.6, 'hit': '🛑 觸及（已決）'},
    {'stock_code': '2313', 'stock_name': '華通', 'close': 243.5, 'stop_loss': 235.98, 'hit': '✅ 未觸發（距 3.2%；已決 L4 出場）'},
    {'stock_code': '3090', 'stock_name': '日電貿', 'close': 167.0, 'stop_loss': 256.5, 'hit': '🛑 觸及（已決）'},
    {'stock_code': '1301', 'stock_name': '台塑', 'close': 80.9, 'stop_loss': 54.08, 'hit': '✅ 未觸發（但 L4 18.4% 今日新判出場；損益 +34.6% 超 yaml 停利 20%）'},
    {'stock_code': '4938', 'stock_name': '和碩', 'close': 102.5, 'stop_loss': 76.5, 'hit': '✅ 未觸發（已決 L4 出場）'}]}
t13['two_day_drawdown_after'] = {'basis': '10-08 收盤→10-13 收盤（10-12 收盤取自 tracking）', 'triggered': ['2404 漢唐 -12.64%（已結算）'],
                                 'near': '3026 -8.10%、3042 -7.35%（皆已 L4 出場）、3037 -7.09%（距停損 3.1%）'}
t13['holdings_reversal_scan'] = 'data/2026-10-13/_after/reversal_stdout.txt（19 檔；仍為 10-12 T86）'
t13['tomorrow_opening_exits'] = [
    {'stock_code': '6770', 'stock_name': '力積電', 'category': '持倉 my_holdings.yaml（已決 L4＋鐵律①）', 'reason': '收 67.5 < 停損 73.26；10-12 T86 -23,224 張（23.4%）；yaml 未更新'},
    {'stock_code': '2337', 'stock_name': '旺宏', 'category': '持倉 my_holdings.yaml（鐵律①）', 'reason': '收 106.5 < 停損 147.6；L4 9.7%'},
    {'stock_code': '3090', 'stock_name': '日電貿', 'category': '持倉 my_holdings.yaml（鐵律①）', 'reason': '收 167.0 < 停損 256.5；L4 8.1%'},
    {'stock_code': '1301', 'stock_name': '台塑', 'category': '持倉 my_holdings.yaml（10-13 新判 L4，已決）', 'reason': '10-12 T86 -18,665 張（18.4% ≥8%，不受待複核保護）；損益約 +34.6% 已超 yaml 停利 20%；近 6 日 +21.1% 接近注意門檻'},
    {'stock_code': '2313', 'stock_name': '華通', 'category': '持倉 my_holdings.yaml（已決 L4，10-08 定案）', 'reason': '已決不重評；10-12 T86 +7,324 翻買已揭露；收 243.5 未觸停損 235.98（距 3.2%）'},
    {'stock_code': '4938', 'stock_name': '和碩', 'category': '持倉 my_holdings.yaml（已決 L4）', 'reason': '已決不重評；10-12 T86 +14,599 翻買已揭露；收 102.5'},
    {'stock_code': '2330', 'stock_name': '台積電', 'category': '持倉 my_holdings.yaml 零股 0.15 張（已決）', 'reason': '追蹤部位已結算；10-12 T86 -7,464 張（38.6%）'}]
t13['tomorrow_pending_review'] = []
t13['tomorrow_recommendations'] = []
t13['tomorrow_recommendation_note'] = (
    '10-13 T86／BFI82U 14:31 查無（n=12），法人資料仍為 10-12 T86，與今日盤前同一份；不以舊 T86 補推（比照 10-08、10-12 盤後）。'
    '觀察逐檔：2408 南亞科 營收 2026-09 +576.6%（回檔 -7.2% → +5）、持股比 +0.71%（+5）、MA20 -3.8%（乖離 0~5% 區外，法人現身門檻不適用），但 10-12 不在 TOP50 買超、'
    'DRAM「利多不漲」且美光 -3.88%／KOSPI -3.65%，待 10-13 T86 確認法人動向；2885 元大金 營收落後至 2026-08 歸零且動能 +252% 追高排除；2412 中華電 營收 +20.9% 但回檔僅 1.4% 不加分；'
    '1519 華城 -7.7% 型態轉弱；2516 新建 營收連 11 月衰退 -5。→ 10-14 預估新推薦 0 檔（寧缺勿濫），盤前以 10-13 T86 重評。')
t13['tomorrow_carry_over'] = [
    {'stock_code': c, 'stock_name': n, 'recommend_date': d, 'recommend_price': p, 'target_price': tp, 'stop_loss': sl}
    for c, n, d, p, tp, sl in [('3037', '欣興', '2026-10-12', 1270.0, 1371.6, 1143.0), ('8046', '南電', '2026-10-12', 1475.0, 1593.0, 1327.5),
                               ('3231', '緯創', '2026-10-12', 188.5, 203.6, 169.65), ('3711', '日月光投控', '2026-10-12', 744.0, 803.5, 669.6),
                               ('3189', '景碩', '2026-10-12', 1075.0, 1161.0, 967.5), ('3443', '創意', '2026-10-06', 8600.0, 9288.0, 7740.0),
                               ('2002', '中鋼', '2026-10-13', 19.2, 20.74, 17.28), ('2886', '兆豐金', '2026-10-13', 50.0, 54.0, 45.0),
                               ('2892', '第一金', '2026-10-13', 39.7, 42.88, 35.73), ('2867', '三商壽', '2026-08-17', 9.75, 10.73, 8.78)]]
t13['watchlist_tomorrow'] = ['2408 南亞科（待 10-13 T86）', '2412 中華電', '1519 華城（型態待修復）']
t13['data_quality_after'] = [
    '10-13 T86／BFI82U 14:31 查無（n=12）；所有反轉等級／賣超佔比與盤前、盤中同為 10-12 T86',
    'Yahoo 10-12 日K close/volume=None 未補：get_close_series 序列缺 10-12，settlement_checker D 計數全體少 1 天（3035 實 D6），不影響今日結算判定；10-12 收盤取自 tracking_2026-10-12',
    '序列對齊：17 檔末日 10-13；2867 三商壽停於 08-19（凍結）',
    '營收 2885 落後 2026-08 歸零；外資持股比 5 檔皆 ≥10-08；盤前 JSON 已還原']
t13['after_market_version'] = 'v1（10-13 T86 未公布）'
save(D, t13)
print('ok', [x['stock_code'] for x in removed])
