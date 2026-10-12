import json
D = '2026-10-12'
T = f'data/tracking/tracking_{D}.json'
t = json.load(open(T, encoding='utf-8'))

# (收盤, 前一交易日收盤, D, 10-08 T86)
closes = {
    '3231': (189.5, 188.5, 0, '+16,705'), '3711': (762.0, 744.0, 0, '+1,251'), '8046': (1440.0, 1475.0, 0, '+313'),
    '3042': (204.5, 211.0, 0, '+1,610'), '3026': (840.0, 877.0, 0, '+3,245'), '3189': (1060.0, 1075.0, 0, '+251'),
    '3037': (1255.0, 1270.0, 0, '+935'),
    '3035': (197.5, 202.0, 5, '-354（腳本佔比 8.4%，10 日累計 +8,233）'), '3443': (8100.0, 8360.0, 3, '+8'),
    '2404': (1235.0, 1305.0, 2, '+48'), '2609': (63.6, 59.7, 2, '+5,769'), '1312': (16.05, 15.15, 1, '+6,650'),
}


def fill(r):
    c = r['stock_code']
    if c not in closes:
        return
    close, prev, d, t86 = closes[c]
    rp = r['recommend_price']
    chg = round((close / prev - 1) * 100, 2)
    r.update({'close_price': close, 'actual_close': close, 'change_percent': chg,
              'return_pct': round((close / rp - 1) * 100, 2), 'holding_days': d, 'holding_days_label': f'D{d}/10'})
    r.setdefault('result', 'holding')
    r['holding_status'] = ("D%d/10；10-12 收 %s（今日 %+.2f%%，相對推薦價 %+.2f%%）；距目標 %.1f%%／距停損 %.2f%%；10-08 T86 %s（10-12 T86 盤後 14:30 未公布）"
                           % (d, close, chg, r['return_pct'], (r['target_price'] / close - 1) * 100, (1 - r['stop_loss'] / close) * 100, t86))


for r in t['recommendations']:
    fill(r)
for r in t.get('carry_over_recommendations', []):
    if r['stock_code'] == '2867':
        r['result'] = 'holding'
        r['holding_status'] = '⚠️ 序列停滯（末日 2026-08-19）凍結判定（v8.3.8）'
        continue
    fill(r)

t['removed_stocks'] = []
t['settlement_today'] = {'settled': [], 'holding_count': 13, 'frozen': ['2867'],
                         'note': '今日 0 筆結算：無到期 D10、無收盤越目標／停損；最接近 2609 陽明 63.6 距目標 63.94 差 0.5%、2404 漢唐 1,235 距停損 1,201.5 僅 2.7%',
                         'd_counts_source': 'settlement_checker 2026-10-12 盤後輸出照抄（序列末日 10-12）'}
t['yesterday_verification'] = {'date': D, 'settled_count': 0, 'success': 0, 'fail': 0, 'accuracy': None, 'results': [],
                               'cumulative': '55.8%（405 勝／321 敗，726 筆，不變）', 'note': '今日無結算'}
t['market_close'] = {'taiex': None, 'source': '本次盤後未取大盤收盤（以個股收盤與 settlement_checker 序列為準）',
                     'institutional_total': 'BFI82U／T86 10-12 盤後 14:30 未公布'}
t['stop_loss_check_after_v8310'] = {'time': '2026-10-12 14:40', 'basis': 'get_close_series 末筆＝2026-10-12 收盤（序列對齊，2867 除外）', 'results': [
    {'stock_code': '2330', 'stock_name': '台積電', 'close': 2540.0, 'stop_loss': None, 'hit': '不適用（yaml 無 stop_loss）；已決出場'},
    {'stock_code': '6770', 'stock_name': '力積電', 'close': 71.4, 'stop_loss': 73.26, 'hit': '🛑 觸及（重複輸出：已決，yaml 未更新）'},
    {'stock_code': '2337', 'stock_name': '旺宏', 'close': 115.5, 'stop_loss': 147.6, 'hit': '🛑 觸及（重複輸出）'},
    {'stock_code': '2313', 'stock_name': '華通', 'close': 252.0, 'stop_loss': 235.98, 'hit': '✅ 未觸發（已決 L4 出場）'},
    {'stock_code': '3090', 'stock_name': '日電貿', 'close': 171.5, 'stop_loss': 256.5, 'hit': '🛑 觸及（重複輸出）'},
    {'stock_code': '1301', 'stock_name': '台塑', 'close': 80.7, 'stop_loss': 54.08, 'hit': '✅ 未觸發'},
    {'stock_code': '4938', 'stock_name': '和碩', 'close': 98.6, 'stop_loss': 76.5, 'hit': '✅ 未觸發（已決 L4 出場）'}]}
t['two_day_drawdown_after'] = {'basis': 'get_close_series 末 3 筆（10-08→10-12）', 'worst': '3035 智原 -5.50%、2404 漢唐 -7.14%（10-07→10-12 兩日）', 'triggered': 0}
t['pending_review_result'] = {
    'stock_code': '3035', 'stock_name': '智原',
    'review_1_1230': '8.4%（≥5%）', 'review_2_after_close': '8.4%（≥5%）；賣超 -354 張未變、10 日累計 +8,233 張為正',
    'verdict': '兩次皆 ≥5% → 依 v8.3.3 次日（10-13）開盤出場',
    'disclosure': '複核①②皆讀同一份 10-08 T86（10-12 T86 未公布）且分母同為 avg_5day_volume，複核②無新資訊（同源，記入 pending_review_same_source_t86 樣本）'}

exits = [
    {'stock_code': '3035', 'stock_name': '智原', 'category': '追蹤 tracking_2026-10-02（v8.3.3 待複核定案）',
     'reason': '10-08 T86 -354 張佔 8.4%，複核①12:30＋複核②盤後皆 ≥5% → 10-13 開盤出場；收 197.5 距停損 191.7 僅 2.9%；同源揭露見 pending_review_result'},
    {'stock_code': '6770', 'stock_name': '力積電', 'category': '持倉 my_holdings.yaml（已決 L4＋鐵律①）', 'reason': '收 71.4 < 停損 73.26；L4 20.4%（-23,401）；yaml 未更新'},
    {'stock_code': '2313', 'stock_name': '華通', 'category': '持倉 my_holdings.yaml（已決 L4，10-08 盤前定案）', 'reason': '已決不重評；10-08 T86 +5,020 翻買已揭露，收 252.0 未觸停損'},
    {'stock_code': '4938', 'stock_name': '和碩', 'category': '持倉 my_holdings.yaml（已決 L4）', 'reason': '10-08 T86 -1,295 張（28.3%）；今日收 98.6（+9.9%）已決不重評'},
    {'stock_code': '2337', 'stock_name': '旺宏', 'category': '持倉 my_holdings.yaml（鐵律①）', 'reason': '收 115.5 < 停損 147.6；L4 72.2%'},
    {'stock_code': '3090', 'stock_name': '日電貿', 'category': '持倉 my_holdings.yaml（鐵律①）', 'reason': '收 171.5 < 停損 256.5'},
    {'stock_code': '2330', 'stock_name': '台積電', 'category': '持倉 my_holdings.yaml 零股 0.15 張（已決）', 'reason': '追蹤部位已結算；10-08 T86 -11,001 張（60.3%）'}]
t['tomorrow_opening_exits'] = exits
t['tomorrow_pending_review'] = []
t['tomorrow_recommendations'] = []
t['tomorrow_recommendation_note'] = (
    '10-12 T86 盤後 14:30 未公布（n=11），法人資料仍為 10-08 T86，與盤前同一份；不以舊 T86 補推（比照 10-08 盤後）。'
    '候選逐檔：2408 南亞科 營收 2026-09 +576.6%（回檔 0.2% 不加分）、持股比 +0.71% +5，但今日 15:00 法說會結果未知＋MA20 落 0~+5% 且不在 TOP50 買超 → 法人現身門檻未過；'
    '2412 中華電 營收落後歸零、10-13 法說、催化未對齊；2892 第一金／1102 亞泥／6505 台塑化 營收落後歸零（6505 外資近 5 天為負、5 日已大漲）；'
    '2436 偉詮電 營收 +5／持股比 -3、催化未對齊；2344 華邦電 營收 +5／持股比 -3 且盤前 L4。→ 10-13 預估新推薦 0 檔（寧缺勿濫），10-13 盤前以 10-12 T86 重評。')
t['tomorrow_carry_over'] = [
    {'stock_code': '1312', 'stock_name': '國喬', 'recommend_date': '2026-10-08', 'recommend_price': 15.05, 'stop_loss': 13.545, 'target_price': 16.25, 'holding_days': 'D1/10'},
    {'stock_code': '2404', 'stock_name': '漢唐', 'recommend_date': '2026-10-07', 'recommend_price': 1335.0, 'stop_loss': 1201.5, 'target_price': 1441.8, 'holding_days': 'D2/10'},
    {'stock_code': '2609', 'stock_name': '陽明', 'recommend_date': '2026-10-07', 'recommend_price': 59.2, 'stop_loss': 56.24, 'target_price': 63.94, 'holding_days': 'D2/10'},
    {'stock_code': '3443', 'stock_name': '創意', 'recommend_date': '2026-10-06', 'recommend_price': 8600.0, 'stop_loss': 7740.0, 'target_price': 9288.0, 'holding_days': 'D3/10'},
    {'stock_code': '2867', 'stock_name': '三商壽', 'recommend_date': '2026-08-17', 'recommend_price': 9.75, 'stop_loss': 8.78, 'target_price': 10.73, 'holding_days': '凍結（序列停滯 08-19）'}]
t['watchlist_tomorrow'] = ['2408 南亞科（今日 15:00 法說結果待看）', '2412 中華電（10-13 法說）', '2436 偉詮電', '2892 第一金', '1102 亞泥', '6505 台塑化']
t['data_quality_after'] = [
    '10-12 T86 盤後 14:31 查無（n=11）；所有反轉等級／賣超佔比與盤前、盤中同為 10-08 T86',
    '10-08 T86 回補 L4 方向：2330 -11,001 續賣、2344 -14,591 續賣、3711 +1,251 翻買、2308 -806 輕賣',
    '序列對齊：19 檔中 18 檔末日 10-12；2867 三商壽停於 08-19（凍結）',
    '營收 4/7 落後 2026-08（2412／2892／1102／6505 歸零）；外資持股比 7 檔皆 ≥10-05；盤前 JSON 已從 _after/premarket_backup 還原',
    'recommendations 盤前沿用者 carry_over_recommendations 皆帶 recommend_date']
t['after_market_version'] = 'v1（10-12 T86 未公布）'
json.dump(t, open(T, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', [r['stock_code'] for r in t['recommendations']])
