import json
D='2026-11-06'
def L(p): return json.load(open(p,encoding='utf-8'))
def S(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
settle=[
 dict(code='2609',name='陽明',rd='2026-10-28',rp=63.0,px=57.1,hd='D7/10',why='鐵律③ L4 已決事項（11-05 完整T86 賣超-2,431張佔均量14.0%）→ 11-06 開盤出場；入帳收盤 57.1（v8.3.2）低於推薦價 63.0（距停損 56.7 僅 0.7%，未觸停損）。⚠️揭露：11-06 T86 已轉買 +373 張（L0），依已決事項不重評'),
 dict(code='2801',name='彰銀',rd='2026-10-28',rp=30.2,px=27.9,hd='D7/10',why='鐵律③ L4 已決事項（11-05 完整T86 賣超-5,201張佔均量21.3%）→ 11-06 開盤出場；入帳收盤 27.9（v8.3.2）低於推薦價 30.2（未觸停損 27.18）。⚠️揭露：11-06 T86 已轉買 +3,190 張（L0），依已決事項不重評'),
 dict(code='2002',name='中鋼',rd='2026-11-02',rp=19.25,px=18.55,hd='D4/10',why='鐵律③ L4 已決事項（11-05 完整T86 賣超-3,316張佔均量10.8%）→ 11-06 開盤出場；入帳收盤 18.55（v8.3.2）低於推薦價 19.25；11-06 T86 續賣 -30,689 張（佔均量85.3%），出場方向正確'),
]
sync='v8.3.7 三處同步：①來源tracking ②tracking_2026-11-06.json removed_stocks ③predictions.json'
removed=[]
for s in settle:
    ret=round((s['px']/s['rp']-1)*100,2)
    f=f"data/tracking/tracking_{s['rd']}.json"; t=L(f); hit=False
    for r in t['recommendations']:
        if r['stock_code']==s['code'] and r.get('result','holding')=='holding':
            r.update(result='fail',actual_close=s['px'],close_price=s['px'],settled_date=D,settled_price=s['px'],return_pct=ret,fail_reason=s['why'],sync_note=sync); hit=True
    assert hit,s
    S(f,t)
    removed.append(dict(stock_code=s['code'],stock_name=s['name'],track='A',recommend_date=s['rd'],recommend_price=s['rp'],settled_price=s['px'],last_close=s['px'],return_pct=ret,result='fail',holding_days=s['hd'],removal_reason=s['why'],fail_reason=s['why'],settled_by='已決事項開盤出場（v8.3.7 Step 4-0；盤後收盤價入帳 v8.3.2）',settled_date=D,sync_note=sync))
f=f'data/tracking/tracking_{D}.json'; t=L(f)
t['removed_stocks']=removed
t['phase']='after_market'
px={'2885':(66.9,'D9/10'),'3045':(133.0,'D7/10'),'2884':(47.0,'D5/10'),'2886':(53.5,'D4/10'),'2610':(21.2,'D3/10')}
for r in t['carry_over_recommendations']:
    c=r['stock_code']
    if c in px:
        p,lab=px[c]; r['current_price']=p; r['actual_close']=p; r['close_price']=p
        r['return_pct']=round((p/r['recommend_price']-1)*100,2); r['holding_days_label']=lab; r['holding_days']=int(lab[1:].split('/')[0])
t['tomorrow_opening_exits']=[dict(stock_code='2885',stock_name='元大金',category='新判定（推薦追蹤 L4，v8.3.3 不適用）',reason='11-06 完整T86 三大法人-6,393張佔均量26.8%≥8%→L4（10日累計仍+33K、外資近5日-28K、真連買0天）；收盤66.9（-6.2%，距停損64.17約4.1%）；11-09 開盤出場（亦為D10），settled_price用11-09收盤',origin_recommend_date='2026-10-22')]
t['tomorrow_recommendations']=[]
t['after_market_checks']=dict(t86_source='手動 fetch_all_institutional(20261106) 寫入 twse_t86_20261106.json（16:3x 取得，16,131 筆含 TWSE/TPEx，缺口僅為權證）',reversal_alert='15 檔含今日T86；chip_analysis 以執行期包裝從今日起算',stale_series='2867 三商壽序列仍為 None，凍結不結算',two_day_drop='無 <-10%（2885 近2日 -3.0%）',closes_date_aligned='13 檔序列末日皆 2026-11-06')
t['after_market_holding_status']={'2885':'🛑 L4 26.8%→11-09開盤出場','3045':'續抱 L0','2884':'續抱（外資近5日-19K、投信買）','2886':'續抱 真連買7天','2610':'續抱 真連買5天，Q3財報11/14前公布'}
S(f,t)
print('ok')
