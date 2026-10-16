import json
D='2026-10-16'
S=[('8046','南電','2026-10-12',1355.0,'L4：10-15 T86 -627張佔9.1%（≥8%，不受待複核保護），盤中維持已決；收盤 1355 距停損 1327.5 仍有 2.1%，非停損觸發'),
('3189','景碩','2026-10-12',1000.0,'L4：10-15 T86 -1,948張佔19.5%，已決出場；收盤 1000 距停損 967.5 仍有 3.4%，非停損觸發'),
('3576','聯合再生','2026-10-15',17.8,'L4：10-15 T86 -4,511張佔53.6%（前日+5,162張一日反轉），D1 即出場；收盤 17.8'),
('2323','中環','2026-10-15',11.85,'L4：10-15 T86 -998張佔11.6%（≥8%，前日+10,984張一日反轉）；收盤 11.85 略低於推薦價 11.9')]
rem=[]
for code,name,rd,px,why in S:
    p=f'data/tracking/tracking_{rd}.json'
    t=json.load(open(p,encoding='utf-8'))
    for r in t['recommendations']:
        if r['stock_code']==code and r.get('result')=='holding':
            ret=round((px/r['recommend_price']-1)*100,2)
            r.update(result='fail',actual_close=px,settled_date=D,settled_price=px,return_pct=ret,
              sync_note=f'{D} 盤後結算（鐵律③L4）；同步寫入 來源檔／tracking_{D}.removed_stocks／predictions',
              fail_reason='鐵律③'+why+f'；入帳用當日收盤 {px}（{ret:+.2f}%）')
            rem.append(dict(stock_code=code,stock_name=name,recommend_date=rd,recommend_price=r['recommend_price'],result='fail',settled_price=px,last_close=px,return_pct=ret,removal_reason='鐵律③'+why,settled_by='鐵律③L4',source_tracking=f'tracking_{rd}.json'))
    json.dump(t,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
p=f'data/tracking/tracking_{D}.json'
t=json.load(open(p,encoding='utf-8'))
t['removed_stocks']=rem
t['phase']='after_market'
t['settlement_today']={'settled':[{k:r[k] for k in('stock_code','stock_name','result','settled_price','return_pct')} for r in rem],'holding_count':6,'frozen':['2867']}
t['yesterday_verification']={'date':'2026-10-16','settled_count':4,'success':0,'fail':4,'note':'4 檔皆為 10-15 T86 新判 L4 之鐵律出場，入帳用當日收盤'}
t['market_close']={'note':'今日 T86／BFI82U 14:30 後查無（n=15），籌碼沿用 10-15 資料'}
t['stop_loss_check_after_v8310']=[{'symbol':s,'close':c,'stop_loss':sl,'hit':c<sl} for s,c,sl in [('6770',67.3,73.26),('2337',107.0,147.6),('3090',170.5,256.5),('2313',248.0,235.98),('1301',82.1,54.08),('4938',102.0,76.5)]]
t['two_day_drawdown_after']={'basis':'10-14 收盤→10-16 收盤','triggered':[],'near':'8046 -5.24%、3189 -4.76%、3576 -4.56%'}
t['tomorrow_opening_exits']=[
 {'stock_code':c,'stock_name':n,'category':'持倉 my_holdings.yaml（已決，yaml 未更新）','reason':r} for c,n,r in [
 ('6770','力積電','收 67.3<停損 73.26；10-15 T86 -95,839張L4'),
 ('2337','旺宏','收 107.0<停損 147.6'),
 ('3090','日電貿','收 170.5<停損 256.5；10-15 T86 L4'),
 ('1301','台塑','已決 L4；損益約+36% 超 yaml 停利 20%'),
 ('2313','華通','已決 L4；今日收 248.0 站回停損 235.98 但籌碼決議不重評'),
 ('4938','和碩','已決 L4（10-15 T86 -216張 L0，揭露）'),
 ('2330','台積電','零股 0.15 張，已決 L4')]]
t['tomorrow_recommendations']=[]
t['tomorrow_recommendation_note']='0 檔：10-16 T86 14:30 後仍查無（n=15），不拿舊資料硬推；大盤前日 -3.41%；2408 南亞科 營收+577% 但法人 10 日累計賣超、外資持股週減 -0.40%（-3），不推；不湊數'
json.dump(t,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
