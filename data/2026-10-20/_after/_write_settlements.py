import json
D='2026-10-20'
src='data/tracking/tracking_2026-10-19.json'
s=json.load(open(src,encoding='utf-8'))
closes={'1326':73.8,'1802':67.4,'1605':37.0}
reasons={
 '1326':'鐵律③ L4（10-19 T86 賣超 -6,570 張佔 9.9% ≥8%，不受 v8.3.3 保護）→ 10-20 盤前已決開盤出場（v8.3.7 不重評）；入帳 10-20 收盤 73.8（v8.3.2），低於推薦價 78.7 記 fail',
 '1802':'鐵律③ L4（10-19 T86 賣超 -32,423 張佔 29.4% ≥8%）→ 10-20 盤前已決開盤出場（v8.3.7 不重評）；入帳 10-20 收盤 67.4（v8.3.2），高於推薦價 66.9 記 success',
 '1605':'鐵律③ L4（10-19 T86 賣超 -10,400 張佔 21.4% ≥8%）→ 10-20 盤前已決開盤出場（v8.3.7 不重評）；入帳 10-20 收盤 37.0（v8.3.2），低於推薦價 38.5 記 fail',
}
removed=[]
for r in s['recommendations']:
    c=r['stock_code']
    if c in closes and r.get('result')=='holding':
        cl=closes[c]; ret=round((cl-r['recommend_price'])/r['recommend_price']*100,2)
        res='success' if cl>r['recommend_price'] else 'fail'
        r.update(result=res,actual_close=cl,settled_date=D,settled_price=cl,return_pct=ret,
                 sync_note=f'{D} 盤後 v8.3.7 三處同步：①本檔 ②tracking_{D}.json removed_stocks ③predictions.json')
        if res=='fail': r['fail_reason']=reasons[c]; r.pop('success_note',None)
        else: r['success_note']=reasons[c]; r.pop('fail_reason',None)
        removed.append({'stock_code':c,'stock_name':r['stock_name'],'track':'A','recommend_date':'2026-10-19',
          'recommend_price':r['recommend_price'],'settled_price':cl,'last_close':cl,'return_pct':ret,'result':res,
          'holding_days':'D1/10','removal_reason':reasons[c],
          ('fail_reason' if res=='fail' else 'success_note'):reasons[c],
          'settled_by':'已決事項開盤出場（v8.3.7 Step 4-0，10-20 盤前定案；盤後收盤價入帳 v8.3.2）',
          'settled_date':D,'sync_note':f'v8.3.7 三處同步：①tracking_2026-10-19.json ②本檔 removed_stocks ③predictions.json'})
        print('settled',c,res,cl,ret)
json.dump(s,open(src,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
t=json.load(open(f'data/tracking/tracking_{D}.json',encoding='utf-8'))
t['removed_stocks']=removed
json.dump(t,open(f'data/tracking/tracking_{D}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('written',len(removed))
