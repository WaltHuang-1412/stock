"""2026-11-26 盤後：寫入結算（2886）、收盤價、明日推薦與出場清單"""
import json

T = 'data/tracking/tracking_2026-11-26.json'
S = 'data/tracking/tracking_2026-11-20.json'


def load(p):
    return json.load(open(p, encoding='utf-8'))


def save(p, d):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


reason = ('鐵律出場：11-25 法人爆量賣超 L4（-5,930 張佔 11.1%）列今日開盤出場；盤中另達 2 日累計跌幅超過 -10%；'
          '今日 T86 續賣 -14,071 張（佔 20.4%）。入帳價用當日收盤 48.25（停損 48.06 未觸，當日低點 48.25）')
settle = dict(result='fail', actual_close=48.25, close_price=48.25, settled_date='2026-11-26', settled_price=48.25,
              return_pct=-9.64, holding_days=4, holding_days_label='D4/10', fail_reason=reason,
              holding_status='已結算 fail（鐵律出場）',
              sync_note='v8.3.7 三處同步：①tracking_2026-11-20.json ②tracking_2026-11-26.json removed_stocks ③predictions.json')

s = load(S)
hit = 0
for r in s['recommendations']:
    if r['stock_code'] == '2886':
        r.update(settle)
        r['change_percent'] = -9.64
        hit += 1
assert hit == 1
save(S, s)

t = load(T)
t['phase'] = 'after_market'

info = {
    '2379': (730.0, 4.43, 'D0；收 730（+4.4%）距目標 3.4%、距停損 13.8%；今日法人 +366 張，反轉 L1（買超減速）→ 續抱'),
    '2615': (100.0, -0.50, 'D0；收 100（-0.5%）；今日法人 -2,026 張佔 5 日均量 9.3% → L4，次日開盤出場'),
}
for r in t['recommendations']:
    c, p, st = info[r['stock_code']]
    r.update(actual_close=c, close_price=c, return_pct=p, change_percent=p, result='holding',
             holding_days=0, holding_days_label='D0/10', holding_status=st)

carry = {
    '2610': (21.8, -4.80, 5, 'D5；收 21.8（-4.8%）距停損 5.5%；今日法人 -5,380 張佔 5 日均量 10.4% → L4，次日開盤出場'),
    '2412': (166.5, 0.30, 4, 'D4；收 166.5（+0.3%）；今日法人 +7,175 張（外資賣、投信買），真連買 6 天、反轉 L0 → 續抱不加碼'),
}
for r in t['carry_over_recommendations']:
    c = r['stock_code']
    if c in carry:
        cl, p, d, st = carry[c]
        r.update(actual_close=cl, close_price=cl, return_pct=p, change_percent=p, result='holding',
                 holding_days=d, holding_days_label=f'D{d}/10', holding_status=st)
    elif c == '2886':
        r.update(settle)
        r['change_percent'] = -9.64
t['carry_over'] = ['2610', '2412']
t['removed_stocks'] = [dict(
    stock_code='2886', stock_name='兆豐金', track='A', recommend_date='2026-11-20', recommend_price=53.4,
    settled_price=48.25, last_close=48.25, actual_close=48.25, return_pct=-9.64, result='fail',
    holding_days='D4/10', removal_reason=reason, fail_reason=reason, settled_by='鐵律出場（盤後以收盤價入帳）',
    settled_date='2026-11-26', sync_note=settle['sync_note'])]


def rec(code, name, ind, price, target, stop, score, br, why):
    return dict(stock_code=code, stock_name=name, industry=ind, recommend_price=price, target_price=target,
                stop_loss_pct=-10, stop_loss=stop, settlement_days=10, position='5-10%', score=score,
                score_breakdown=br, entry_condition=f'開盤高於 {price} 的 3% 以上不追；開盤低於停損價不進場',
                reason=why, note='盤後預測，11-27 盤前重新評估後才建檔')


t['tomorrow_recommendations'] = [
    rec('2603', '長榮', '航運', 254.0, 274.32, 228.6, 77,
        {'時事': 21, '法人': 6, '產業': 15, '技術': 12, '價格位置': 8, '動能': 10, '營收': 0, 'EPS': 5, '外資持股比': 0},
        '中東油價/航運超強催化↑、匯兌受惠；外資近5日+39,035張、反轉L0、動能-16%；10月營收年增+96.1%（回檔不足不加分）、'
        'Q3 EPS年增+114%(+5)；持股比週增+0.22%（不調整）；MA20 -0.4%／MA60 +2.4%。弱點：今日三大法人僅+76張'
        '（外資+13,006、投信-13,284 對作）、不在TOP50買超、同業2615今日轉L4'),
    rec('8046', '南電', 'ABF載板', 731.0, 789.48, 657.9, 76,
        {'時事': 18, '法人': 15, '產業': 15, '技術': 12, '價格位置': 1, '動能': 10, '營收': 0, 'EPS': 5, '外資持股比': 0},
        'ABF載板/PCB漲價強催化↑；今日TOP50買超（+1,278張）、外資近5日+4,800張、反轉L0、動能-22%；10月營收年增+69.7%'
        '（回檔不足不加分）、Q3 EPS年增+355%(+5)；持股比週增+0.26%（不調整）。弱點：MA20 -18.4%／MA60 -35.4%下降趨勢、'
        '真連買僅1天、投信偏賣'),
]
t['tomorrow_note'] = '盤後預測 2 檔（各 5-10%）；11-27 盤前依龍頭預警、訊號A/B、跳空狀況重新評估'
t['tomorrow_watch'] = [
    {'stock_code': '1477', 'stock_name': '聚陽', 'note': '真連買6天、L0，但當日時事資料無對應催化（催化對齊未過）'},
    {'stock_code': '2344', 'stock_name': '華邦電', 'note': 'L0，但記憶體催化方向向下（催化對齊未過）'},
    {'stock_code': '2882', 'stock_name': '國泰金', 'note': 'L0，但催化鏈標↓、營收連續衰退(-5)、11-27法說'},
]

names = {x['stock_code']: x['stock_name'] for x in t['opening_exits_today']}
exits = [
    {'stock_code': '2610', 'stock_name': '華航', 'category': 'Track A 追蹤（反轉 L4）',
     'reason': '11-26 L4：賣超 -5,380 張佔 5 日均量 10.4%（≥8%，不適用 v8.3.3 待複核）；10 日累計仍 +87K；'
               '收 21.8>停損 20.61；次日開盤出場，入帳價用 11-27 收盤'},
    {'stock_code': '2615', 'stock_name': '萬海', 'category': 'Track A 追蹤（反轉 L4）',
     'reason': '11-26 L4：賣超 -2,026 張佔 5 日均量 9.3%（≥8%，不適用 v8.3.3 待複核）；10 日累計 +4,340；'
               '收 100>停損 90.45；次日開盤出場，入帳價用 11-27 收盤'},
]
after = {
    '6770': '鐵律① 11-26 收 51.5<停損 73.26（已決沿用）',
    '2337': '鐵律① 11-26 收 65.2<停損 147.6（已決沿用）',
    '2313': '鐵律① 11-26 收 168.0<停損 235.98（已決沿用）',
    '3090': '鐵律① 11-26 收 109.0<停損 256.5（已決沿用）',
    '1301': '11-06 出場決議（已決沿用）；11-26 收 60.2>停損 54.08',
    '4938': '11/12 已決維持；11-26 收 85.1>停損 76.5',
    '2330': 'L3/L4 已決沿用；11-26 L4 -15,554 張佔 27.8%；收 2,145',
}
for c, why in after.items():
    exits.append({'stock_code': c, 'stock_name': names[c], 'category': '持倉（已決事項）', 'reason': why})
t['tomorrow_opening_exits'] = exits
t['pending_review'] = []
t['after_market_prices'] = {
    'date': '2026-11-26', 'taiex_close': 39151.81, 'taiex_pct': 2.50, '2610': 21.8, '2412': 166.5, '2886': 48.25,
    '2379': 730.0, '2615': 100.0, '6770': 51.5, '2337': 65.2, '2313': 168.0, '3090': 109.0, '1301': 60.2,
    '4938': 85.1, '2330': 2145.0}
t['yesterday_verification'] = {
    'accuracy': '54.0%（421 勝／359 敗，共 780 筆）', 'settled': ['2886'],
    'results': [
        {'stock_code': '2886', 'result': 'fail', 'return_pct': -9.64, 'settled_price': 48.25, 'note': '鐵律出場'},
        {'stock_code': '2610', 'result': 'holding', 'return_pct': -4.80, 'settled_price': None, 'note': 'L4 次日開盤出場'},
        {'stock_code': '2412', 'result': 'holding', 'return_pct': 0.30, 'settled_price': None},
        {'stock_code': '2379', 'result': 'holding', 'return_pct': 4.43, 'settled_price': None},
        {'stock_code': '2615', 'result': 'holding', 'return_pct': -0.50, 'settled_price': None, 'note': 'L4 次日開盤出場'}],
    'note': '11-26 結算 1 筆 fail（2886）', 'carry': ['2610', '2412', '2379', '2615'],
    'stale_series': ['2867 三商壽（停牌）']}
save(T, t)
print('ok')
