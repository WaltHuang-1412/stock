import json
D='2026-10-15'
def load(d): return json.load(open(f'data/tracking/tracking_{d}.json',encoding='utf-8'))
def save(d,t): json.dump(t,open(f'data/tracking/tracking_{d}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
S={
 '3443':('2026-10-06','fail',7670.0,'鐵律①：收盤 7670 ≤ 停損 7740（-10.81%）；10-15 台積電法說日、大盤 -3.41%、AI 供應鏈全面重挫；籌碼 L0（10-14 T86 +104 張）非法人轉賣','鐵律①觸及停損價'),
 '3231':('2026-10-12','fail',176.0,'鐵律③L4：10-14 T86 -3,059 張佔 9.3%（≥8%，不受待複核保護），盤前列開盤出場；入帳用當日收盤 176.0（-6.63%，距停損 169.65 仍有 3.7%，非停損觸發）','鐵律③L4'),
}
t=load(D)
by={}
for c,v in S.items(): by.setdefault(v[0],[]).append(c)
names={}
for src,codes in by.items():
    s=load(src)
    for k in ('recommendations','track_b_recommendations','carry_over_recommendations'):
        for r in s.get(k,[]):
            c=r['stock_code']
            if c in codes and r.get('result','holding')=='holding' and (src!=D or True):
                if k=='carry_over_recommendations' and src!=r.get('recommend_date',src): continue
                _,res,px,why,b=S[c]; rp=r['recommend_price']; ret=round((px/rp-1)*100,2)
                r.update({'result':res,'actual_close':px,'settled_date':D,'settled_price':px,'return_pct':ret,'sync_note':f'{D} 盤後結算（{b}）；同步寫入 來源檔／tracking_{D}.removed_stocks／predictions'})
                r['fail_reason']=why
                names[c]=(r['stock_name'],rp,ret)
    save(src,s)
print(names)
removed=[]
for c,(src,res,px,why,b) in S.items():
    n,rp,ret=names[c]
    removed.append({'stock_code':c,'stock_name':n,'recommend_date':src,'recommend_price':rp,'result':res,'settled_price':px,'last_close':px,'return_pct':ret,'removal_reason':why,'settled_by':b,'source_tracking':f'tracking_{src}.json'})
t=load(D)
t['removed_stocks']=removed
closes={'3576':(17.95,18.65),'2323':(11.8,11.9),'8046':(1345.0,1430.0),'3189':(979.0,1050.0),'2002':(19.25,19.5),'2886':(52.5,51.1),'2892':(41.6,40.65),'3231':(176.0,187.0),'3443':(7670.0,8245.0)}
t['phase']='after_market'
for lst in ('recommendations','carry_over_recommendations'):
    for r in t.get(lst,[]):
        c=r['stock_code']
        if c in S:
            _,res,px,why,b=S[c]
            r.update({'result':res,'actual_close':px,'close_price':px,'settled_date':D,'settled_price':px,'return_pct':round((px/r['recommend_price']-1)*100,2),'fail_reason':why})
        elif c in closes:
            px,prev=closes[c]
            r.update({'actual_close':px,'close_price':px,'return_pct':round((px/r['recommend_price']-1)*100,2),'result':'holding','change_percent':round((px/prev-1)*100,2)})
            if lst=='recommendations':
                r['holding_status']='D0 持有中'
t['settlement_today']={'settled':[{'stock_code':x['stock_code'],'stock_name':x['stock_name'],'result':x['result'],'settled_price':x['settled_price'],'return_pct':x['return_pct']} for x in removed],'holding_count':8,'frozen':['2867']}
t['yesterday_verification']={'date':D,'settled_count':2,'success':0,'fail':2,'note':'3443 創意鐵律①-10.81%；3231 緯創 L4 -6.63%'}
t['market_close']={'taiex':46969.87,'change_pct':-3.41,'prev':48625.83,'source':'Yahoo ^TWII regularMarketPrice','institutional_total':'T86／BFI82U 10-15 14:30 查無（n=14）'}
t['stop_loss_check_after_v8310']={'time':'2026-10-15 14:40','basis':'get_close_series 末筆＝2026-10-15 收盤','results':[
 {'stock_code':'2330','stock_name':'台積電','close':2440.0,'stop_loss':None,'hit':'不適用；已決出場（L4 23.9%）'},
 {'stock_code':'6770','stock_name':'力積電','close':66.2,'stop_loss':73.26,'hit':'🛑 觸及（已決，yaml 未更新）'},
 {'stock_code':'2337','stock_name':'旺宏','close':104.5,'stop_loss':147.6,'hit':'🛑 觸及（已決）'},
 {'stock_code':'2313','stock_name':'華通','close':228.0,'stop_loss':235.98,'hit':'🛑 今日新觸及（已決 L4）'},
 {'stock_code':'3090','stock_name':'日電貿','close':171.5,'stop_loss':256.5,'hit':'🛑 觸及（已決）'},
 {'stock_code':'1301','stock_name':'台塑','close':81.7,'stop_loss':54.08,'hit':'✅ 未觸發（已決；損益約 +36%）'},
 {'stock_code':'4938','stock_name':'和碩','close':98.1,'stop_loss':76.5,'hit':'✅ 未觸發（已決）'}]}
t['two_day_drawdown_after']={'basis':'10-13 收盤→10-15 收盤','triggered':[],'near':'8046 南電 -6.60%、3189 景碩 -5.87%、3231 緯創 -5.88%、3443 創意 -5.25%'}
def ex(c,n,cat,reason): return {'stock_code':c,'stock_name':n,'category':cat,'reason':reason}
t['tomorrow_opening_exits']=[
 ex('6770','力積電','持倉 my_holdings.yaml（已決 L4＋鐵律①）','收 66.2 < 停損 73.26；yaml 未更新'),
 ex('2337','旺宏','持倉 my_holdings.yaml（已決，鐵律①）','收 104.5 < 停損 147.6'),
 ex('3090','日電貿','持倉 my_holdings.yaml（已決，鐵律①）','收 171.5 < 停損 256.5'),
 ex('1301','台塑','持倉 my_holdings.yaml（10-13 已決 L4）','已決不重評；收 81.7、損益約 +36% 仍超 yaml 停利 20%'),
 ex('2313','華通','持倉 my_holdings.yaml（已決 L4＋今日新觸鐵律①）','收 228.0 < 停損 235.98'),
 ex('4938','和碩','持倉 my_holdings.yaml（已決 L4）','已決不重評；收 98.1'),
 ex('2330','台積電','持倉 my_holdings.yaml 零股 0.15 張（已決）','10-15 L4 佔 23.9%')]
t['tomorrow_pending_review']=[]
t['tomorrow_recommendations']=[]
t['tomorrow_recommendation_note']='0 檔：10-15 T86 14:30 查無（n=14）；大盤 -3.41%、費半連 6 黑、10-15 台積電法說；2408 南亞科 10-14 法人 -25,076 張、10 日累計 -36K，不推；不湊數'
save(D,t)
