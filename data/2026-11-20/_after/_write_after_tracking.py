import json
D='2026-11-20'
def lj(p): return json.load(open(p,encoding='utf-8'))
def sj(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
SYNC="v8.3.7 三處同步：①來源tracking ②tracking_2026-11-20.json removed_stocks ③predictions.json"
p='data/tracking/tracking_2026-11-18.json'; t=lj(p); ok=False
reason='收盤 37.6 ≤ 停損 37.89（鐵律停損，-10.69%）；2 日累計 41.0→37.6 = -8.3%；今日 T86 仍買 +7,673 張，但金融股同步重挫、價格先破停損'
u=dict(result='fail',actual_close=37.6,settled_date=D,settled_price=37.6,return_pct=-10.69,fail_reason=reason,sync_note=SYNC)
for k in ('recommendations','track_b_recommendations','carry_over_recommendations'):
    for r in t.get(k,[]) or []:
        if isinstance(r,dict) and r.get('stock_code')=='2892' and r.get('result','holding')=='holding' and not ok:
            r.update(u); ok=True
sj(p,t); print('source written',ok)
p=f'data/tracking/tracking_{D}.json'; t=lj(p)
closes={'5876':49.6,'4904':103.0,'2610':21.3,'1101':24.35,'2412':162.5,'2886':51.8,'2892':37.6}
labels={'5876':'D9/10','4904':'D4/10','2610':'D1/10','1101':'D1/10','2412':'D0/10','2886':'D0/10','2892':'D2/10'}
status={
'5876':'D9；Level 0（今日 +1,259 張、真連買 8 天、累計 +14.7K）；收 49.6（-2.8%）低於推薦價 51.0，11/20 14:30 法說已過；明日 D10 依收盤 vs 推薦價 51.0 結算 → 續抱至結算',
'4904':'D4；🔴 L4（今日賣超 -2,011 張，佔日均量 21.2%≥8%；10 日累計 +5.9K 但佔比遠離門檻，不適用待複核）→ 次日開盤出場；收 103.0（-5.9%）',
'2610':'D1；L1 買超減速 -66%，今日仍買超、真連買 10 天、累計 +164K；收 21.3（-7.0%），距停損 20.61 約 3.3% → 續抱，收盤≤20.61 即鐵律停損',
'1101':'D1；🔴 L4（今日賣超 -7,088 張，佔日均量 23.2%≥8%）→ 次日開盤出場；收 24.35（-7.2%）',
'2412':'D0；L0 持續買超 +6,259 張、動能 +17.3% → 續抱；收 162.5（-2.1%）',
'2886':'D0；L1 買超減速 -35%，今日仍 +4,926 張 → 續抱；收 51.8（-3.0%），距停損 48.06 約 7.2%；11/24 14:30 法說',
'2892':'D2；收盤 37.6 ≤ 停損 37.89 → 結算 fail'}
for k in ('recommendations','carry_over_recommendations'):
    for r in t.get(k,[]) or []:
        c=r['stock_code']
        if c in closes:
            r['actual_close']=closes[c]; r['close_price']=closes[c]
            r['return_pct']=round((closes[c]/r['recommend_price']-1)*100,2)
            r['holding_days_label']=labels[c]; r['holding_days']=int(labels[c].split('/')[0][1:])
            r['holding_status']=status[c]
            if c=='2892': r.update(u)
t['removed_stocks']=[dict(stock_code='2892',stock_name='第一金',track='A',recommend_date='2026-11-18',recommend_price=42.1,settled_price=37.6,last_close=37.6,return_pct=-10.69,result='fail',holding_days='D2/10',removal_reason=reason,fail_reason=reason,settled_by='settlement_checker 機械判定（收盤≤停損）',settled_date=D,sync_note=SYNC)]
t['tomorrow_opening_exits']=[
 dict(stock_code='4904',stock_name='遠傳',category='追蹤（L4）',reason='今日 T86 賣超 -2,011 張，佔日均量 21.2%（≥8%，不適用待複核）；累計 +5.9K 張'),
 dict(stock_code='1101',stock_name='台泥',category='追蹤（L4）',reason='今日 T86 賣超 -7,088 張，佔日均量 23.2%（≥8%）'),
 dict(stock_code='6770',stock_name='力積電',category='持倉（已決事項）',reason='鐵律① 收盤 44.1<停損 73.26'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉（已決事項）',reason='鐵律① 收盤 58.9<停損 147.6'),
 dict(stock_code='2313',stock_name='華通',category='持倉（已決事項）',reason='鐵律① 收盤 152.5<停損 235.98'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉（已決事項）',reason='鐵律① 收盤 95.0<停損 256.5'),
 dict(stock_code='1301',stock_name='台塑',category='持倉（已決事項）',reason='11-06 出場決議原樣沿用；收盤 56.1>停損 54.08（距 3.7%）'),
 dict(stock_code='4938',stock_name='和碩',category='持倉（已決事項）',reason='11/12 已決維持；收盤 78.1>停損 76.5（距 2.1%）'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉（已決事項）',reason='L4 已決沿用；收 2,000')]
t['tomorrow_recommendations']=[]
t['tomorrow_note']='0 檔：候選池（11-20 TOP35）可用者僅 2883 凱基金／5880 合庫金／6505 台塑化／2489 瑞軒／2880 華南金／6672 騰輝-KY；價位皆為月季雙線下（1~3 分）、2883 營收 -51%、5880 營收連衰 -5、6505 外資近5日 -1.6K 未過篩選②、2880 外資近5日 -6.1K 未過、2489 真連買僅 1 天且外資持股比週減；其餘動能>+100% 追高或累計為負且處置預警；空頭局勢、限空令、金融追蹤集中'
t['watchlist']=[]
t['stale_series']=t.get('stale_series')
t['after_market_note']='T86（16:32 公布）已寫入快取後以含今日資料重跑 reversal_alert／chip_analysis（_after/_chip_incl_today.py）'
t['phase']='after_market'
sj(p,t); print('ok')
