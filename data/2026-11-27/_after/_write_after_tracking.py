"""2026-11-27 盤後：寫入結算（2379/2610/2615）、收盤價、明日出場清單與預測（0 檔）"""
import json

T = 'data/tracking/tracking_2026-11-27.json'
S19 = 'data/tracking/tracking_2026-11-19.json'
S26 = 'data/tracking/tracking_2026-11-26.json'


def load(p):
    return json.load(open(p, encoding='utf-8'))


def save(p, d):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


SYNC = 'v8.3.7 三處同步：①來源 tracking ②tracking_2026-11-27.json removed_stocks ③predictions.json'
SETTLE = {
    '2379': dict(name='瑞昱', src=S26, rec_date='2026-11-26', price=699.0, close=755.0, ret=8.01, result='success', d=1,
                 note='收盤 755.0 ≥ 目標價 754.92，到目標價結算（settlement_checker）；當日高 755，與 TWSE 收盤一致',
                 by='settlement_checker（收盤達目標價）'),
    '2610': dict(name='華航', src=S19, rec_date='2026-11-19', price=22.9, close=21.6, ret=-5.68, result='fail', d=6,
                 note='鐵律出場：11-26 法人爆量賣超 L4（-5,380 張佔 10.4%）列 11-27 開盤出場；入帳價用當日收盤 21.6'
                      '（停損 20.61 未觸，當日低點 21.05）。今日 T86 翻買 +1,938 張，已決事項不重評',
                 by='鐵律出場（盤後以收盤價入帳）'),
    '2615': dict(name='萬海', src=S26, rec_date='2026-11-26', price=100.5, close=99.0, ret=-1.49, result='fail', d=1,
                 note='鐵律出場：11-26 法人爆量賣超 L4（-2,026 張佔 9.3%）列 11-27 開盤出場；入帳價用當日收盤 99.0'
                      '（停損 90.45 未觸，當日低點 99.0）。今日 T86 +179 張（反轉 L1），已決事項不重評',
                 by='鐵律出場（盤後以收盤價入帳）'),
}


def settle_fields(x):
    f = dict(result=x['result'], actual_close=x['close'], close_price=x['close'], settled_date='2026-11-27',
             settled_price=x['close'], return_pct=x['ret'], change_percent=x['ret'], holding_days=x['d'],
             holding_days_label=f"D{x['d']}/10", holding_status=f"已結算 {x['result']}", sync_note=SYNC)
    f['success_note' if x['result'] == 'success' else 'fail_reason'] = x['note']
    return f


# ① 來源檔回寫
for code, x in SETTLE.items():
    s = load(x['src'])
    hit = [r for r in s['recommendations'] if r['stock_code'] == code]
    assert len(hit) == 1 and hit[0]['recommend_price'] == x['price'], (code, len(hit))
    hit[0].update(settle_fields(x))
    save(x['src'], s)

t = load(T)
t['phase'] = 'after_market'

info = {
    '2880': (42.15, -4.64, 'D0；收 42.15（-4.6%）距停損 39.78 5.6%；今日法人 -5,744 張佔 5 日均量 22.1% → L4，次日開盤出場'),
    '2603': (249.0, -1.97, 'D0；收 249（-2.0%）距停損 228.6 8.2%；今日法人 -2,424 張佔 5 日均量 8.6% → L4，次日開盤出場'),
}
for r in t['recommendations']:
    c, p, st = info[r['stock_code']]
    r.update(actual_close=c, close_price=c, return_pct=p, change_percent=p, result='holding',
             holding_days=0, holding_days_label='D0/10', holding_status=st)

for r in t['carry_over_recommendations']:
    c = r['stock_code']
    if c in SETTLE:
        r.update(settle_fields(SETTLE[c]))
    elif c == '2412':
        r.update(actual_close=165.5, close_price=165.5, return_pct=-0.30, change_percent=-0.30, result='holding',
                 holding_days=5, holding_days_label='D5/10',
                 holding_status='D5；收 165.5（-0.3%）距停損 9.7%；今日法人 -609 張（外資 -24,273、投信 +22,766），反轉 L0 → 續抱不加碼')
t['carry_over'] = ['2412']

# ② removed_stocks
t['removed_stocks'] = [dict(
    stock_code=c, stock_name=x['name'], track='A', recommend_date=x['rec_date'], recommend_price=x['price'],
    settled_price=x['close'], last_close=x['close'], actual_close=x['close'], return_pct=x['ret'], result=x['result'],
    holding_days=f"D{x['d']}/10", removal_reason=x['note'], settled_by=x['by'], settled_date='2026-11-27',
    sync_note=SYNC) for c, x in SETTLE.items()]

exits = [
    {'stock_code': '2880', 'stock_name': '華南金', 'category': 'Track A 追蹤（反轉 L4）',
     'reason': '11-27 L4：賣超 -5,744 張佔 5 日均量 22.1%（≥8%，不適用 v8.3.3 待複核）；10 日累計 -3,319；'
               '收 42.15>停損 39.78；次日開盤出場，入帳價用 11-30 收盤'},
    {'stock_code': '2603', 'stock_name': '長榮', 'category': 'Track A 追蹤（反轉 L4）',
     'reason': '11-27 L4：賣超 -2,424 張佔 5 日均量 8.6%（≥8%，不適用 v8.3.3 待複核；取樣 16:3x，分母為不含當日的前 5 日均量）；'
               '10 日累計 +3,223；收 249>停損 228.6；次日開盤出場，入帳價用 11-30 收盤'},
]
after = {
    '6770': ('力積電', '鐵律① 11-27 收 50.5<停損 73.26（已決沿用）'),
    '2337': ('旺宏', '鐵律① 11-27 收 65.4<停損 147.6（已決沿用）'),
    '2313': ('華通', '鐵律① 11-27 收 184.5<停損 235.98（已決沿用）'),
    '3090': ('日電貿', '鐵律① 11-27 收 107.5<停損 256.5（已決沿用）；今日另轉 L4（-230 張佔 9.7%）'),
    '1301': ('台塑', '11-06 出場決議（已決沿用）；11-27 收 60.1>停損 54.08'),
    '4938': ('和碩', '11/12 已決維持；11-27 收 84.4>停損 76.5'),
    '2330': ('台積電零股', 'L3/L4 已決沿用；11-27 L4 -7,136 張佔 13.0%；收 2,180'),
}
for c, (n, why) in after.items():
    exits.append({'stock_code': c, 'stock_name': n, 'category': '持倉（已決事項）', 'reason': why})
t['tomorrow_opening_exits'] = exits
t['pending_review'] = []

t['tomorrow_recommendations'] = []
t['tomorrow_note'] = ('盤後預測 0 檔（11-30）：147 檔候選中僅 3406 玉晶光通過準確率三篩，但 57 分未達 70；'
                      '2353 宏碁 90 分卡催化對齊（流程判讀）。11-30 盤前重新評估')
t['tomorrow_watch'] = [
    {'stock_code': '2353', 'stock_name': '宏碁', 'score': 90, 'note': '反轉 L0、外資 5 日 +1,734 張；催化對齊未過（所屬主題皆未標升溫，流程判讀）'},
    {'stock_code': '2610', 'stock_name': '華航', 'score': 83, 'note': '今日剛依鐵律出場；催化對齊未過（中東鏈標華航↓油價成本）'},
    {'stock_code': '2891', 'stock_name': '中信金', 'score': 80, 'note': '反轉 L1 未過三篩；11-30 15:00 法說；營收兩資料源衝突'},
    {'stock_code': '1229', 'stock_name': '聯華', 'score': 77, 'note': '真連買 10 天、L0；催化對齊未過'},
    {'stock_code': '1101', 'stock_name': '台泥', 'score': 77, 'note': '反轉 L1、催化對齊未過'},
    {'stock_code': '3406', 'stock_name': '玉晶光', 'score': 57, 'note': '通過三篩，分數未達 70（月線下 -15.5%、10 日 6 天賣超、5 日 +9.3%）'},
]

t['after_market_prices'] = {
    'date': '2026-11-27', 'taiex_close': 39308.08, 'taiex_pct': 0.40, 'foreign_net_100m': -296.28,
    'trust_net_100m': 85.19, 'dealer_net_100m': -1.95, 'total_net_100m': -213.04,
    '2880': 42.15, '2603': 249.0, '2412': 165.5, '2379': 755.0, '2610': 21.6, '2615': 99.0, '6770': 50.5,
    '2337': 65.4, '2313': 184.5, '3090': 107.5, '1301': 60.1, '4938': 84.4, '2330': 2180.0}
t['yesterday_verification'] = {
    'accuracy': '53.9%（422 勝／361 敗，共 783 筆）', 'settled': ['2379', '2610', '2615'],
    'results': [
        {'stock_code': '2379', 'result': 'success', 'return_pct': 8.01, 'settled_price': 755.0, 'note': '到目標價'},
        {'stock_code': '2610', 'result': 'fail', 'return_pct': -5.68, 'settled_price': 21.6, 'note': '鐵律出場'},
        {'stock_code': '2615', 'result': 'fail', 'return_pct': -1.49, 'settled_price': 99.0, 'note': '鐵律出場'},
        {'stock_code': '2412', 'result': 'holding', 'return_pct': -0.30, 'settled_price': None},
        {'stock_code': '2880', 'result': 'holding', 'return_pct': -4.64, 'settled_price': None, 'note': 'L4 次日開盤出場'},
        {'stock_code': '2603', 'result': 'holding', 'return_pct': -1.97, 'settled_price': None, 'note': 'L4 次日開盤出場'}],
    'note': '11-27 結算 3 筆（1 勝 2 敗）', 'carry': ['2412', '2880', '2603'],
    'stale_series': ['2867 三商壽（併購停牌，序列查詢失敗，凍結）']}
save(T, t)
print('ok')
