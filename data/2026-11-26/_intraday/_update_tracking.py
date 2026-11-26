"""盤中更新 tracking（只加盤中欄位，不改 result／進場價／停損）"""
import json

P = 'data/tracking/tracking_2026-11-26.json'
I = 'data/2026-11-26/_intraday'
t = json.load(open(P, encoding='utf-8'))
px = {}
for line in open(I + '/prices_final.txt', encoding='utf-8'):
    parts = line.split()
    if parts and parts[1].startswith('現價='):
        px[parts[0]] = float(parts[1].split('=')[1])

hold = {'2379': ('D0/10', 0), '2615': ('D0/10', 0), '2610': ('D5/10', 5), '2412': ('D4/10', 4), '2886': ('D4/10', 4)}
note = {
    '2379': '續抱；開盤698符合進場規則，現價高於不追價720，未進場者不追',
    '2615': '續抱；跌破MA10（一般訊號），反轉L0',
    '2610': '續抱；跌破MA10（一般訊號），反轉L0',
    '2412': '續抱不加碼；真連買5天、動能+500%',
    '2886': '出場（盤前已決）；盤中另達2日累計-10.7%（55.0→49.1），反轉L4 8.6%；收盤價結算',
}
for key in ('recommendations', 'carry_over_recommendations'):
    for r in t[key]:
        c = r['stock_code']
        r['intraday_price'] = px[c]
        r['intraday_pct_vs_recommend'] = round((px[c] / r['recommend_price'] - 1) * 100, 2)
        r['intraday_time'] = '12:30-12:32'
        r['intraday_status'] = note[c]
        r['holding_days'] = hold[c][1]
        r['holding_days_label'] = hold[c][0]

for r in t['opening_exits_today']:
    r['intraday_price'] = px[r['stock_code']]

t['phase'] = 'intraday'
t['track_b_recommendations'] = []
rows = json.load(open(I + '/scores.json', encoding='utf-8'))
t['track_b_observations'] = [
    dict(stock_code=r['code'], stock_name=r['name'], score=r['total'], intraday_pct=r['chg'],
         reason='未推薦：' + '；'.join(r['fail'])) for r in rows]
t['intraday_context'] = dict(taiex=39366.06, taiex_pct=3.06, quote_time='12:31', t86='2026-11-25',
                             detector_strong=['9929'], detector_moderate=['5283'])
json.dump(t, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for key in ('recommendations', 'carry_over_recommendations'):
    for r in t[key]:
        print(r['stock_code'], r['result'], r['intraday_price'], r['intraday_pct_vs_recommend'], r['holding_days_label'], r['stop_loss'], r.get('recommend_date'))
