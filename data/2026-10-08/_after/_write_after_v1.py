import json
D = '2026-10-08'
T = f'data/tracking/tracking_{D}.json'
A = f'data/{D}/_after/'
t = json.load(open(T, encoding='utf-8'))
json.dump(t, open(A + 'tracking_before_after.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

closes = {'1312': (15.15, 0.67, 0), '3035': (202.0, -3.35, 4), '3443': (8360.0, -1.18, 2), '3661': (4345.0, 3.68, 2), '1326': (77.6, 2.37, 3),
          '2404': (1305.0, -1.88, 1), '2609': (59.7, 1.02, 1), '3711': (744.0, 1.64, 5), '2308': (1965.0, -1.27, 2), '2330': (2550.0, -1.35, 2), '2344': (177.0, -1.39, 2)}
t86 = {'3035': '+715', '3443': '+81', '3661': '+748', '1326': '+16,150', '2404': '+175', '2609': '+429', '1312': '+7,005',
       '3711': '-1,352（L4 12.7%）', '2308': '-1,981（L4 20.2%）', '2330': '-650（L2 3.6%）', '2344': '+12,918（翻買）'}


def fill(r):
    c = r['stock_code']
    if c not in closes:
        return
    close, chg, d = closes[c]
    rp = r['recommend_price']
    r.update({'close_price': close, 'actual_close': close, 'change_percent': chg, 'return_pct': round((close / rp - 1) * 100, 2),
              'holding_days': d, 'holding_days_label': f'D{d}/10'})
    r.setdefault('result', 'holding')
    r['holding_status'] = ("D%d/10；10-08 收 %s（今日 %+.2f%%，相對推薦價 %+.2f%%）；距目標 %.1f%%／距停損 %.2f%%；10-07 T86 %s（10-08 T86 盤後 14:30 未公布）"
                           % (d, close, chg, r['return_pct'], (r['target_price'] / close - 1) * 100, (1 - r['stop_loss'] / close) * 100, t86[c]))


for r in t['recommendations']:
    fill(r)
for r in t.get('carry_over_recommendations', []):
    if r['stock_code'] == '2867':
        r['result'] = 'holding'
        r['holding_status'] = '⚠️ 序列停滯（末日 2026-08-19）凍結判定（v8.3.8）'
        continue
    fill(r)

SET = {
    '1326': ('台化', '2026-10-05', 71.7, 77.6, 'success', 'settlement_checker 機械判定：D3 收盤 77.6 ≥ 目標 77.4'),
    '3661': ('世芯-KY', '2026-10-06', 3950.0, 4345.0, 'success', 'settlement_checker 機械判定：D2 收盤 4,345 ≥ 目標 4,266'),
    '2330': ('台積電', '2026-10-06', 2575.0, 2550.0, 'fail', '已決事項開盤出場（v8.3.3 待複核①②皆 ≥5%，10-07 盤後定案；入帳收盤價 v8.3.2）'),
    '2344': ('華邦電', '2026-10-06', 181.0, 177.0, 'fail', '已決事項開盤出場（v8.3.3 待複核①②皆 ≥5%；10-07 T86 已翻買 +12,918 揭露不重評；入帳收盤價 v8.3.2）'),
    '3711': ('日月光投控', '2026-10-01', 703.0, 744.0, 'success', '鐵律③ L4 開盤出場（10-07 T86 -1,352 張佔 12.7% ≥8%，不受待複核保護；入帳收盤價 v8.3.2）'),
    '2308': ('台達電', '2026-10-06', 2005.0, 1965.0, 'fail', '鐵律③ L4 開盤出場（10-07 T86 -1,981 張佔 20.2% ≥8%；入帳收盤價 v8.3.2）'),
}
rem = []
res = []
for c, (n, src, rp, cl, rs, by) in SET.items():
    ret = round((cl / rp - 1) * 100, 2)
    d = closes[c][2]
    rem.append({'stock_code': c, 'stock_name': n, 'track': 'A', 'recommend_date': src, 'recommend_price': rp, 'settled_price': cl, 'last_close': cl,
                'return_pct': ret, 'result': rs, 'holding_days': f'D{d}/10', 'removal_reason': by, 'settled_by': by, 'settled_date': D,
                'sync_note': f'v8.3.7 三處同步：①tracking_{src}.json ②本檔 removed_stocks ③predictions.json'})
    res.append({k: rem[-1][k] for k in ['stock_code', 'stock_name', 'recommend_date', 'recommend_price', 'settled_price', 'return_pct', 'result', 'holding_days', 'settled_by']})
t['removed_stocks'] = rem
t['settlement_today'] = {'settled': res, 'holding_count': 5, 'frozen': ['2867'], 'd_counts_source': 'settlement_checker 2026-10-08 盤後輸出照抄（序列末日 10-08）'}
for r in t['recommendations'] + t.get('carry_over_recommendations', []):
    c = r['stock_code']
    if c in SET and r.get('recommend_price') == SET[c][2]:
        n, src, rp, cl, rs, by = SET[c]
        r['result'] = rs
        r['settled_date'] = D
        r['settled_price'] = cl
        r['return_pct'] = round((cl / rp - 1) * 100, 2)
        r['holding_status'] = None
        r['success_note' if rs == 'success' else 'fail_reason'] = by
ok = sum(1 for x in res if x['result'] == 'success')
ng = len(res) - ok
t['yesterday_verification'] = {'date': D, 'settled_count': len(res), 'success': ok, 'fail': ng, 'accuracy': round(ok / len(res) * 100, 1), 'results': res, 'cumulative': None,
                               'note': '今日結算 6 筆：settlement_checker 機械判定 2 筆（1326 台化、3661 世芯-KY 收盤越目標）＋鐵律③ L4 開盤出場 4 筆（2330、2344 已決；3711、2308 新 L4），入帳價一律 10-08 收盤（v8.3.2）'}
t['market_close'] = {'taiex': 49313.44, 'taiex_change_pct': -0.99, 'taiex_change': -492.93, 'prev_close': 49806.37,
                     'source': 'Yahoo ^TWII 日K 2026-10-08 09:00 列（regularMarketPrice 49,313.44）', 'turnover': 'FMTQIK 10-08 盤後 14:30 未公布', 'institutional_total': 'BFI82U 10-08 盤後 14:30 未公布'}
t['stop_loss_check_after_v8310'] = {'time': '2026-10-08 14:35', 'basis': 'get_close_series 末筆＝2026-10-08 收盤（序列對齊）', 'results': [
    {'stock_code': '2330', 'stock_name': '台積電', 'close': 2550.0, 'stop_loss': None, 'hit': '不適用（yaml 無 stop_loss）；已決出場'},
    {'stock_code': '6770', 'stock_name': '力積電', 'close': 72.2, 'stop_loss': 73.26, 'hit': '🛑 觸及停損（-11.30%，重複輸出：10-07 已決，yaml 未更新）', 'pl_pct': -11.30},
    {'stock_code': '2337', 'stock_name': '旺宏', 'close': 116.0, 'stop_loss': 147.6, 'hit': '🛑 觸及停損（-29.27%，重複輸出）', 'pl_pct': -29.27},
    {'stock_code': '2313', 'stock_name': '華通', 'close': 248.0, 'stop_loss': 235.98, 'hit': '✅ 未觸發（距停損 +5.1%）；新 L4 16.9% 已列開盤出場', 'pl_pct': -5.41},
    {'stock_code': '3090', 'stock_name': '日電貿', 'close': 174.0, 'stop_loss': 256.5, 'hit': '🛑 觸及停損（-38.95%，重複輸出）', 'pl_pct': -38.95},
    {'stock_code': '1301', 'stock_name': '台塑', 'close': 81.3, 'stop_loss': 54.08, 'hit': '✅ 未觸發；損益約 +35.3% 超過 yaml take_profit_percent 20%（無鐵律，提示）', 'pl_pct': 35.3},
    {'stock_code': '4938', 'stock_name': '和碩', 'close': 89.7, 'stop_loss': 76.5, 'hit': '✅ 未觸發；已決 L4（yaml 未更新）', 'pl_pct': 5.55}], 'new_triggers': 0}
t['two_day_drawdown_check_after'] = {'basis': '10-06 收盤 → 10-08 收盤（get_close_series 末 3 筆）', 'triggered': [],
                                     'worst': [{'stock_code': '2308', 'stock_name': '台達電', 'pct': -4.15}, {'stock_code': '3035', 'stock_name': '智原', 'pct': -4.04}, {'stock_code': '6770', 'stock_name': '力積電', 'pct': -2.83}],
                                     'note': '追蹤＋持倉無 2 日累計 <-10%（人工自算）'}
t['series_alignment_check_after_v838'] = {'expected_last_day': D, 'stale': [{'stock_code': '2867', 'stock_name': '三商壽', 'last_day': '2026-08-19', 'action': '凍結判定'}], 'aligned': '其餘 17 檔末日皆 2026-10-08'}
t['l4_exit_direction_check'] = {'note': '執行日 T86 對照（10-07 T86 已落檔）：3231 緯創 -10,887 續賣（出場正確）、6770 力積電 -39,660 續賣（出場正確）；10-08 執行日 T86 待公布後補填：2330、2344、3711、2308',
                                'cumulative_note': '定案→執行日樣本 23 筆／19 翻買 → 25 筆／19 翻買（10-07 兩筆皆續賣）'}
t['tomorrow_opening_exits'] = [
    {'stock_code': '6770', 'stock_name': '力積電', 'category': '持倉 my_holdings.yaml（已決 L4＋鐵律①，yaml 未更新重複）', 'reason': '10-08 收 72.2 < 停損 73.26；10-07 T86 -39,660 張佔 35.9%；若實際仍持有 10-12 開盤出場'},
    {'stock_code': '2313', 'stock_name': '華通', 'category': '持倉 my_holdings.yaml（已決 L4，10-08 盤前定案）', 'reason': '10-07 T86 -7,433 張佔 16.9% ≥8%；收 248.0 未觸停損'},
    {'stock_code': '4938', 'stock_name': '和碩', 'category': '持倉 my_holdings.yaml（已決 L4）', 'reason': '10-07 T86 -753 張佔 15.2%'},
    {'stock_code': '2337', 'stock_name': '旺宏', 'category': '持倉 my_holdings.yaml（鐵律①，重複）', 'reason': '收 116.0 < 停損 147.6'},
    {'stock_code': '3090', 'stock_name': '日電貿', 'category': '持倉 my_holdings.yaml（鐵律①，重複）', 'reason': '收 174.0 < 停損 256.5'},
    {'stock_code': '2330', 'stock_name': '台積電', 'category': '持倉 my_holdings.yaml 零股 0.15 張（已決）', 'reason': '追蹤部位已於 10-08 結算，零股同決議'}]
t['tomorrow_pending_review'] = []
t['tomorrow_recommendations'] = []
t['tomorrow_recommendation_note'] = ('v1（10-08 T86 盤後 14:30 未公布 n=10；法人資料＝10-07 T86，與盤前同一份）：候選池與盤前相同。盤前已推薦 1312 國喬；觀察名單再核（營收/持股比/價位 10-08 收盤）：'
                                     '1102 亞泥 營收連衰 -5 且催化未對齊；3042 晶技 盤前 66 分<70；2408 南亞科 MA20 +4.5% 落 0~+5% 且不在 TOP50 買超 → 法人現身門檻未過，10/12 線上法說；'
                                     '2412 中華電、2892 第一金 催化未對齊；2436 偉詮電 營收 +5／持股比 -3；6505 台塑化 外資近 5 天為負、5 日已大漲。→ 10-12 預估新推薦 0 檔（寧缺勿濫），10-12 盤前以 10-08 T86 重評。'
                                     '10/9 補假休市、10/10-10/11 週末，下一交易日 10-12（週一）。')
t['tomorrow_carry_over'] = [
    {'stock_code': '1312', 'stock_name': '國喬', 'recommend_date': '2026-10-08', 'recommend_price': 15.05, 'stop_loss': 13.545, 'target_price': 16.25, 'holding_days': 'D0/10（10-12 盤前以 checker 為準）'},
    {'stock_code': '2404', 'stock_name': '漢唐', 'recommend_date': '2026-10-07', 'recommend_price': 1335.0, 'stop_loss': 1201.5, 'target_price': 1441.8, 'holding_days': 'D1/10'},
    {'stock_code': '2609', 'stock_name': '陽明', 'recommend_date': '2026-10-07', 'recommend_price': 59.2, 'stop_loss': 56.24, 'target_price': 63.94, 'holding_days': 'D1/10'},
    {'stock_code': '3035', 'stock_name': '智原', 'recommend_date': '2026-10-02', 'recommend_price': 213.0, 'stop_loss': 191.7, 'target_price': 230.0, 'holding_days': 'D4/10'},
    {'stock_code': '3443', 'stock_name': '創意', 'recommend_date': '2026-10-06', 'recommend_price': 8600.0, 'stop_loss': 7740.0, 'target_price': 9288.0, 'holding_days': 'D2/10'},
    {'stock_code': '2867', 'stock_name': '三商壽', 'recommend_date': '2026-08-17', 'recommend_price': 9.75, 'stop_loss': 8.78, 'target_price': 10.73, 'holding_days': '凍結（序列停滯 08-19）'}]
t['watchlist_tomorrow'] = ['2408 南亞科（門檻未過；10/12 法說）', '2412 中華電', '2436 偉詮電', '2892 第一金', '1102 亞泥', '3042 晶技', '6505 台塑化', '6213 聯茂（處置預警）']
t['data_quality_after'] = ['10-08 T86 盤後 14:30 查無（n=10）；反轉等級/佔比皆為 10-07 T86；BFI82U/FMTQIK 未公布',
                           '10-07 T86 已落檔：回補 3231 緯創 -10,887、6770 力積電 -39,660 續賣；2344 華邦電 +12,918 翻買',
                           '盤後因子檢查 9 檔：營收 9/9 為 2026-08、持股比 as_of 10-01~10-07；四份盤前 JSON 已還原',
                           'holding_days 全程整數（preflight 相容）']
t['after_market_version'] = 'v1（10-08 T86 未公布）'
json.dump(t, open(T, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

n = 0
for c, (nm, src, rp, cl, rs, by) in SET.items():
    f = f'data/tracking/tracking_{src}.json'
    s = json.load(open(f, encoding='utf-8'))
    hit = 0
    for r in s['recommendations']:
        if r['stock_code'] == c and r.get('recommend_price') == rp:
            r.update({'result': rs, 'actual_close': cl, 'close_price': cl, 'settled_date': D, 'settled_price': cl, 'return_pct': round((cl / rp - 1) * 100, 2),
                      'sync_note': '2026-10-08 盤後 v8.3.7 三處同步：①本檔 ②tracking_2026-10-08.json removed_stocks ③predictions.json'})
            r['success_note' if rs == 'success' else 'fail_reason'] = by
            hit += 1
    print(c, src, 'hit', hit)
    n += hit
    json.dump(s, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('source updated', n)
