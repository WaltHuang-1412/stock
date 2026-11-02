import json
p='data/tracking/tracking_2026-11-02.json'
t=json.load(open(p,encoding='utf-8'))
px={'2886':54.1,'2002':19.35,'6505':104.0,'2885':71.1,'2603':273.5,'2609':63.7,'2801':30.6,'3045':133.0,'2884':48.65}
for k in ('recommendations','carry_over_recommendations'):
    for r in t[k]:
        c=px[r['stock_code']]; r['intraday_price']=c; r['intraday_return_pct']=round((c/r['recommend_price']-1)*100,2)
        if r.get('result') is None: r['result']='holding'
t['phase']='intraday'
t['track_b_recommendations']=[]
t['track_b_observations']=[
 {'stock_code':'4737','stock_name':'華廣','note':'偵測器強訊號75，但今日-9.9%爆量(3.0x)=型態轉弱；法人僅+49張、10日累計+131張，排除'},
 {'stock_code':'6873','stock_name':'泓德能源','note':'偵測器強訊號65，但今日-9.9%放量；營收連3月衰退-5；法人僅+76張，排除'},
 {'stock_code':'9937','stock_name':'全國','note':'中訊號50，法人量微小(+2張)，觀察'},
 {'stock_code':'2433','stock_name':'互盛電','note':'中訊號50，法人量微小(+4張)，觀察'}]
t['intraday_holdings_check']={'time':'2026-11-02 12:32','prices':{'6770':65.6,'2337':96.2,'2313':204.5,'3090':150.0,'1301':73.1,'4938':102.0,'2330':2335.0},'note':'6770/2337/2313/3090 仍低於停損；已決出場待使用者確認成交'}
json.dump(t,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
