import json
D='2026-11-19'
def lj(p): return json.load(open(p,encoding='utf-8'))
def sj(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
SYNC="v8.3.7 三處同步：①來源tracking ②tracking_2026-11-19.json removed_stocks ③predictions.json"
def wb(src,code,upd):
    p=f'data/tracking/tracking_{src}.json'; t=lj(p)
    for k in ('recommendations','track_b_recommendations','carry_over_recommendations'):
        for r in t.get(k,[]) or []:
            if isinstance(r,dict) and r.get('stock_code')==code and r.get('result','holding')=='holding':
                r.update(upd); sj(p,t); return True
    return False
u1=dict(result='fail',actual_close=26.9,settled_date=D,settled_price=26.9,return_pct=-5.28,
 fail_reason='已決事項（11-18 T86 L4 28.4%、10日累計為負）→ 11-19 開盤出場，入帳價用收盤 26.9（v8.3.2）低於推薦價 28.4；今日 T86 仍 -1,441 張（L4 6.6%）',sync_note=SYNC)
u2=dict(result='fail',actual_close=53.4,settled_date=D,settled_price=53.4,return_pct=-2.02,
 fail_reason='已決事項（11-18 T86 L4 9.0%）→ 11-19 開盤出場，入帳價用收盤 53.4（v8.3.2）低於推薦價 54.5；⚠️ 今日 T86 翻為 +14,293 張（出場後法人回補，v8.3.5 提案「反向 T86 撤銷出場」n 累計中，未立法）',sync_note=SYNC)
print('2801',wb('2026-11-13','2801',u1),'2886',wb('2026-11-17','2886',u2))
p=f'data/tracking/tracking_{D}.json'; t=lj(p)
closes={'2610':22.5,'1101':25.65,'2892':40.15,'4904':108.0,'5876':53.4,'2801':26.9,'2886':53.4}
labels={'2610':'D0/10','1101':'D0/10','2892':'D1/10','4904':'D3/10','5876':'D8/10','2801':'D4/10','2886':'D2/10'}
status={
'2610':'D0；L1（買超減速 -59%，今日仍 +4,760 張、真連買 10 天、累計 +165K）→ 續抱；收 22.5（-1.8%），距停損 20.61 約 8.4%',
'1101':'D0；籌碼健康（今日 +10,496 張、真連買 4 天、累計 +31K）→ 續抱；收 25.65（-2.3%）',
'2892':'D1；L1（買超減速 -42%，今日仍買 +9,322 張、真連買 10 天、累計 +45K）→ 續抱不加碼；收 40.15（-4.6%），距停損 37.89 約 5.6%；金融股同步走弱',
'4904':'D3；L0（今日 +861 張、累計 +9.1K）→ 續抱不加碼；收 108.0（-1.4%）',
'5876':'D8；籌碼健康（今日 +4,121 張、真連買 7 天、累計 +14K）→ 續抱；11/20 14:30 法說（D9），法說前評估減碼；距目標 3.1%',
'2801':'D4；已決事項 11-19 開盤出場，入帳收盤 26.9，-5.28% → 結算 fail',
'2886':'D2；已決事項 11-19 開盤出場，入帳收盤 53.4，-2.02% → 結算 fail（今日 T86 翻買 +14,293 張）'}
def upd(r):
    c=r['stock_code']
    if c in closes:
        r['actual_close']=closes[c]; r['close_price']=closes[c]
        rp=r['recommend_price']; r['return_pct']=round((closes[c]/rp-1)*100,2)
        r['holding_days_label']=labels[c]; r['holding_days']=int(labels[c].split('/')[0][1:])
        r['holding_status']=status[c]
for k in ('recommendations','carry_over_recommendations'):
    for r in t.get(k,[]) or []: upd(r)
t['removed_stocks']=[
 dict(stock_code='2801',stock_name='彰銀',track='A',recommend_date='2026-11-13',recommend_price=28.4,settled_price=26.9,last_close=26.9,return_pct=-5.28,result='fail',holding_days='D4/10',removal_reason=u1['fail_reason'],fail_reason=u1['fail_reason'],settled_by='已決事項鐵律③出場（入帳用盤後收盤價）',settled_date=D,sync_note=SYNC),
 dict(stock_code='2886',stock_name='兆豐金',track='A',recommend_date='2026-11-17',recommend_price=54.5,settled_price=53.4,last_close=53.4,return_pct=-2.02,result='fail',holding_days='D2/10',removal_reason=u2['fail_reason'],fail_reason=u2['fail_reason'],settled_by='已決事項鐵律③出場（入帳用盤後收盤價）',settled_date=D,sync_note=SYNC)]
t['tomorrow_opening_exits']=[
 dict(stock_code='6770',stock_name='力積電',category='持倉（已決事項）',reason='鐵律① 收盤 48.9<停損 73.26；累計 -57K 張'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉（已決事項）',reason='鐵律① 收盤 64.6<停損 147.6；累計 -3.6K 張'),
 dict(stock_code='2313',stock_name='華通',category='持倉（已決事項）',reason='鐵律① 收盤 169.0<停損 235.98；今日 L4（-3,269 張，6.4%）'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉（已決事項）',reason='鐵律① 收盤 105.5<停損 256.5'),
 dict(stock_code='1301',stock_name='台塑',category='持倉（已決事項）',reason='11-06 出場決議原樣沿用；收盤 60.4>停損 54.08；今日 L4（-4,173 張，12.3%）'),
 dict(stock_code='4938',stock_name='和碩',category='持倉（已決事項）',reason='11/12 已決維持；收盤 81.9>停損 76.5；累計 -2.3K 張'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉（已決事項）',reason='L4 已決沿用；今日仍 L4（-3,218 張，8.1%）；收 2,100')]
t['tomorrow_recommendations']=[]
t['tomorrow_note']='0 檔：金融股 5880 合庫金（營收連 3 月衰退 -5）、2881 富邦金（外資5日 -20K、位置 3 分）、2880 華南金、2891 中信金（外資5日為負）未過篩選②；9933 中鼎 5日 +13.7% 已大漲且動能 +88%；其餘動能>+100% 追高或累計為負；空頭局勢、金融追蹤集中'
t['watchlist']=[dict(stock_code='9933',stock_name='中鼎',note='真連買8天、外資持股比 +1.24%（+5）、營收 +54%；5日 +13.7% 已大漲、動能 +88% → 不推')]
t['after_market_note']='盤後 T86（16:32 公布）已寫入快取後以含今日資料重跑 reversal_alert／chip_analysis'
t['phase']='after_market'
sj(p,t)
print('ok')
