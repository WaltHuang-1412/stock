import json
D='2026-10-21'
closes={'2882':(114.0,'2026-10-16','D3/10','v8.3.3 待複核①6.4%／②33.7% 皆≥5% 定案（10-20 盤後）→ 10-21 開盤出場'),
        '2887':(41.95,'2026-10-20','D1/10','鐵律③ L4（10-20 T86 賣超 -19,629 張佔 37.6% ≥8%）→ 10-21 開盤出場')}
removed=[]
for c,(cl,rd,dl,why) in closes.items():
    src=f'data/tracking/tracking_{rd}.json'
    s=json.load(open(src,encoding='utf-8'))
    for r in s['recommendations']:
        if r['stock_code']==c and r.get('result')=='holding':
            ret=round((cl-r['recommend_price'])/r['recommend_price']*100,2)
            res='success' if cl>r['recommend_price'] else 'fail'
            txt=f"{why}，已決事項不重評（v8.3.7）；入帳 10-21 收盤 {cl}（v8.3.2），{'高於' if res=='success' else '低於'}推薦價 {r['recommend_price']} 記 {res}。10-21 T86 該股翻買（反向樣本）"
            r.update(result=res,actual_close=cl,settled_date=D,settled_price=cl,return_pct=ret,
                     sync_note=f'{D} 盤後 v8.3.7 三處同步：①本檔 ②tracking_{D}.json removed_stocks ③predictions.json')
            r['fail_reason' if res=='fail' else 'success_note']=txt
            removed.append({'stock_code':c,'stock_name':r['stock_name'],'track':'A','recommend_date':rd,
              'recommend_price':r['recommend_price'],'settled_price':cl,'last_close':cl,'return_pct':ret,'result':res,
              'holding_days':dl,'removal_reason':txt,('fail_reason' if res=='fail' else 'success_note'):txt,
              'settled_by':'已決事項開盤出場（v8.3.7 Step 4-0；盤後收盤價入帳 v8.3.2）','settled_date':D,
              'sync_note':f'v8.3.7 三處同步：①tracking_{rd}.json ②本檔 removed_stocks ③predictions.json'})
            print('settled',c,res,cl,ret); break
    else: print('NOT FOUND',c)
    json.dump(s,open(src,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
t=json.load(open(f'data/tracking/tracking_{D}.json',encoding='utf-8'))
t['removed_stocks']=removed
json.dump(t,open(f'data/tracking/tracking_{D}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
