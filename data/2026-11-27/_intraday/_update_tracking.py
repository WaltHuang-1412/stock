"""盤中更新 tracking（只加盤中欄位，不改 result／進場價／停損）"""
import json

P = 'data/tracking/tracking_2026-11-27.json'
I = 'data/2026-11-27/_intraday'
t = json.load(open(P, encoding='utf-8'))
px = json.load(open(I + '/final_prices.json', encoding='utf-8'))

hold = {'2880': 0, '2603': 0, '2610': 6, '2412': 5, '2379': 1, '2615': 1}
note = {
    '2880': '續抱不加碼；開盤43.85符合進場規則；今日-6.45%，出場訊號工具列強烈建議出場（跌破MA5/MA10），三鐵律未觸發；距停損39.78僅3.8%',
    '2603': '續抱；開盤253.5符合進場規則；跌破MA10（一般訊號），反轉L0',
    '2610': '出場（盤前已決，11-26 L4）；盤中取樣佔5日均量11.3%；收盤價結算',
    '2412': '續抱不加碼；法人籌碼健康、真連買6天、動能+317%',
    '2379': '續抱；距目標754.92僅1.9%（今日高753），以收盤價判定',
    '2615': '出場（盤前已決，11-26 L4）；盤中取樣佔5日均量10.1%；收盤價結算',
}
for key in ('recommendations', 'carry_over_recommendations'):
    for r in t[key]:
        c = r['stock_code']
        r['intraday_price'] = px[c]['price']
        r['intraday_pct_vs_recommend'] = round((px[c]['price'] / r['recommend_price'] - 1) * 100, 2)
        r['intraday_time'] = px[c]['time']
        r['intraday_status'] = note[c]
        r['holding_days'] = hold[c]
        r['holding_days_label'] = f'D{hold[c]}/10'

for r in t['opening_exits_today']:
    r['intraday_price'] = px[r['stock_code']]['price']

t['phase'] = 'intraday'
t['track_b_recommendations'] = []
rows = json.load(open(I + '/scores.json', encoding='utf-8'))
obs = []
for r in rows:
    why = r['excl'] + r['fail']
    if r['code'] == '2891':
        why = ['通過分數與反轉等門檻；盤前產業上限（金融達2/3）定案列觀察、盤中資料未變（流程判斷）；11-30法說']
    obs.append(dict(stock_code=r['code'], stock_name=r['name'], score=r['total'], intraday_pct=r['chg'],
                    reason='未推薦：' + '；'.join(why)))
t['track_b_observations'] = obs
t['intraday_context'] = dict(taiex=px['t00']['price'], taiex_pct=px['t00']['chg'], quote_time=px['t00']['time'],
                             quote_source='TWSE MIS 即時報價', t86='2026-11-26',
                             detector_strong=['2880'], detector_moderate=['7835', '1453'],
                             detector_coverage='709 檔僅 76 檔取得即時行情')
json.dump(t, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for key in ('recommendations', 'carry_over_recommendations'):
    for r in t[key]:
        print(r['stock_code'], r['stock_name'], r['result'], r['intraday_price'], r['intraday_pct_vs_recommend'], r['holding_days_label'], r['stop_loss'], r.get('recommend_date'))
