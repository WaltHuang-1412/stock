import json
D='2026-11-03'
px={'2610':20.55,'2885':69.2,'2603':265.5,'2609':62.3,'2801':29.8,'3045':133.0,'2884':47.3,'2886':53.0,'2002':19.3,'6505':95.2}
dd={'2610':0,'2885':6,'2603':5,'2609':4,'2801':4,'3045':4,'2884':2,'2886':1,'2002':1,'6505':1}
p=f'data/tracking/tracking_{D}.json'
t=json.load(open(p,encoding='utf-8'))
rows=[]
for r in t['recommendations']+t['carry_over_recommendations']:
    c=r['stock_code']
    if c not in px: continue
    cur=px[c]; rp=r['recommend_price']
    r['intraday_price']=cur; r['intraday_return_pct']=round((cur/rp-1)*100,2)
    r['intraday_strategy']='續抱' if c!='6505' else '續抱（L2 密切觀察，待盤後 T86 複核）'
    rows.append((c,r['stock_name'],rp,cur,round((r['target_price']/cur-1)*100,1),round((cur/r['stop_loss']-1)*100,1),r['intraday_return_pct']))
t['phase']='intraday'
t['track_b_recommendations']=[]
t['track_b_observations']=[
 {'stock_code':'6887','stock_name':'寶綠特-KY','note':'偵測器強訊號75，但今日-8.7%爆量崩跌，型態轉弱排除'},
 {'stock_code':'6271','stock_name':'同欣電','note':'偵測器強訊號65，但今日-6.5%量比2.3x，型態轉弱排除'},
 {'stock_code':'2613','stock_name':'中櫃','note':'中訊號55，累計僅+112張，法人量微小，不進'},
 {'stock_code':'7710','stock_name':'東擎科技','note':'中訊號55，-5.1%放量、累計僅+168張，不進'}]
t['intraday_check']={'time':'12:30','price_source':'Yahoo regularMarketPrice','t86_last':'2026-11-02(今日未公布，與盤前同源)','new_recommendations':0}
json.dump(t,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
json.dump(rows,open('data/2026-11-03/_intra/rows.json','w'),ensure_ascii=False)
for r in rows: print(r)
