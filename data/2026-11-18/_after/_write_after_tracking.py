import json
D='2026-11-18'
def lj(p): return json.load(open(p,encoding='utf-8'))
def sj(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
SYNC="v8.3.7 三處同步：①來源tracking ②tracking_2026-11-18.json removed_stocks ③predictions.json"
# --- source tracking writebacks
def wb(src,code,upd):
    p=f'data/tracking/tracking_{src}.json'; t=lj(p)
    for k in ('recommendations','track_b_recommendations','carry_over_recommendations'):
        for r in t.get(k,[]) or []:
            if isinstance(r,dict) and r.get('stock_code')==code and r.get('result','holding')=='holding':
                r.update(upd); sj(p,t); return True
    return False
u1=dict(result='fail',actual_close=42.15,settled_date=D,settled_price=42.15,return_pct=-12.73,
 fail_reason='收盤 42.15 ≤ 停損 43.47（settlement_checker 機械判定，D2，-12.73%）；2 日累計 -12.73%、11-17 L4（10%）／11-18 T86 賣超 -46,813 張（佔日均量 129%）',sync_note=SYNC)
u2=dict(result='success',actual_close=164.5,settled_date=D,settled_price=164.5,return_pct=2.17,
 success_note='已決事項（11-17 T86 L4 26.6% 鐵律③）→ 11-18 開盤出場，入帳價用收盤 164.5（v8.3.2）高於推薦價 161.0；今日 T86 仍 -986 張（7.8% L4）',sync_note=SYNC)
print('2884',wb('2026-11-16','2884',u1),'2412',wb('2026-11-12','2412',u2))
# --- today's tracking
p=f'data/tracking/tracking_{D}.json'; t=lj(p)
closes={'2886':52.6,'2892':41.0,'5876':52.9,'2412':164.5,'2801':27.55,'4904':109.0,'2884':42.15}
labels={'2886':'D1/10','2892':'D0/10','5876':'D7/10','2412':'D4/10','2801':'D3/10','4904':'D2/10','2884':'D2/10'}
status={
'2886':'D1；11-18 T86 -2,348 張 L4（佔均量 9.0%≥8%，不受待複核保護；10日累計 +48K 為正但佔比≥8%）→ 次日 11-19 開盤出場；今日 Q3 財報日、收 52.6（-3.5%）',
'2892':'D0；L1（買超減速 -55.5%；今日 T86 仍買超，真連買 10 天、累計 +37K）→ 續抱不加碼；收 41.0（-2.6%），距停損 37.89 約 7.6%',
'5876':'D7；L0（今日 +1,800 張、真連買 6 天、累計 +11.8K）→ 續抱；11/20 法說（D9），法說前評估減碼；距目標 4.1%',
'2412':'D4；已決事項 11-18 開盤出場，入帳收盤 164.5，+2.17% → 結算 success（鐵律③ L4）',
'2801':'D3；11-18 T86 -5,431 張 L4（佔均量 28.4%≥8%；10日累計 -5,743 為負）→ 次日 11-19 開盤出場；收 27.55（-3.0%）',
'4904':'D2；L0（今日 +1,217 張、累計 +9.6K）→ 續抱不加碼；11/19 法說（前一日，雙向波動）',
'2884':'D2；收盤 42.15 ≤ 停損 43.47 → fail（鐵律①②③）'}
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
 dict(stock_code='2884',stock_name='玉山金',track='A',recommend_date='2026-11-16',recommend_price=48.3,settled_price=42.15,last_close=42.15,return_pct=-12.73,result='fail',holding_days='D2/10',removal_reason=u1['fail_reason'],fail_reason=u1['fail_reason'],settled_by='settlement_checker 停損（盤後收盤價）',settled_date=D,sync_note=SYNC),
 dict(stock_code='2412',stock_name='中華電',track='A',recommend_date='2026-11-12',recommend_price=161.0,settled_price=164.5,last_close=164.5,return_pct=2.17,result='success',holding_days='D4/10',removal_reason=u2['success_note'],success_note=u2['success_note'],settled_by='已決事項鐵律③出場（入帳用盤後收盤價）',settled_date=D,sync_note=SYNC)]
t['tomorrow_opening_exits']=[
 dict(stock_code='2886',stock_name='兆豐金',category='追蹤（新決議）',reason='鐵律③ L4：11-18 T86 -2,348 張，佔日均量 9.0%≥8%；今日 Q3 財報日；收 52.6（-3.5%）；次日 11-19 開盤出場，入帳價用 11-19 收盤'),
 dict(stock_code='2801',stock_name='彰銀',category='追蹤（新決議）',reason='鐵律③ L4：11-18 T86 -5,431 張，佔日均量 28.4%；10日累計 -5,743 為負；次日 11-19 開盤出場，入帳價用 11-19 收盤'),
 dict(stock_code='6770',stock_name='力積電',category='持倉（已決事項）',reason='鐵律① 收盤 51.9<停損 73.26；今日 L4（-6,115 張，6.5%）'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉（已決事項）',reason='鐵律① 收盤 69.9<停損 147.6；今日 L4（-9,712 張，23.3%）'),
 dict(stock_code='2313',stock_name='華通',category='持倉（已決事項）',reason='鐵律① 收盤 187.5<停損 235.98；TWSE 注意股'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉（已決事項）',reason='鐵律① 收盤 116.0<停損 256.5；今日 L2'),
 dict(stock_code='1301',stock_name='台塑',category='持倉（已決事項）',reason='11-06 出場決議原樣沿用；收盤 64.4>停損 54.08；今日 L4（-2,789 張，9.1%）'),
 dict(stock_code='4938',stock_name='和碩',category='持倉（已決事項）',reason='11/12 法說後維持已決；收盤 85.4>停損 76.5'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉（已決事項）',reason='L4（-6,896 張，18.4%）；原樣沿用')]
t['tomorrow_recommendations']=[]
t['tomorrow_note']='0 檔：2610 華航／2618 長榮航雖法人連買 10 天，但篩選①催化對立（Brent 93、油價成本↑）；其餘動能>+100% 追高或外資近5日為負；空頭局勢、金融股追蹤集中'
t['watchlist']=[
 dict(stock_code='2610',stock_name='華航',note='真連買10天、累計 +210K、EPS YoY+47%（+5）、月季線雙上；L1 買超減速、油價成本對立；今日 14:00 法說後再評'),
 dict(stock_code='2618',stock_name='長榮航',note='真連買10天、累計 +120K、EPS +2、月季線雙上；L1；油價成本對立'),
 dict(stock_code='9933',stock_name='中鼎',note='真連買7天、累計 +55K、外資持股比 +1.83%（+5）；動能 +106% 追高排除')]
t['after_market_note']='盤後 T86（16:32 公布）已手工寫入快取後以含今日資料重跑 reversal_alert／chip_analysis'
t['phase']='after_market'
sj(p,t); print('ok')
