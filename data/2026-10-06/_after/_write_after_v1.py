import json
TODAY='2026-10-06'
f=f'data/tracking/tracking_{TODAY}.json'
t=json.load(open(f,encoding='utf-8'))
cl=json.load(open('data/2026-10-06/_after/_closes.json',encoding='utf-8'))
S=json.load(open('data/2026-10-06/_after/settlements.json',encoding='utf-8'))
DMAP={'3035':'D2/10','3711':'D3/10'}
for r in t['recommendations']:
    c=r['stock_code']; o=cl[c]
    r['close_price']=o['close']; r['actual_close']=o['close']
    r['change_percent']=round((o['close']/o['prev']-1)*100,2)
    r['return_pct']=round((o['close']/r['recommend_price']-1)*100,2)
    r['result']='holding'
    d=DMAP.get(c,'D0/10')
    r['holding_days_label']=d
    r['holding_status']=f"{'⏳沿用 ' if c in DMAP else '新推薦 '}{d}；10-06 收 {o['close']}（{r['change_percent']:+.2f}%，相對推薦價 {r['return_pct']:+.2f}%）；距目標 {round((r['target_price']/o['close']-1)*100,2)}%／距停損 {round((o['close']/r['stop_loss']-1)*100,2)}%；法人反轉等級待 10-06 T86（v2）"
for r in t['carry_over_recommendations']:
    c=r['stock_code']
    if c=='2867':
        r['close_1006']='序列停滯凍結（末日 08-19）'; continue
    o=cl[c]; r['close_1006']=o['close']; r['day_change_pct_1006']=round((o['close']/o['prev']-1)*100,2)
    r['return_pct_1006']=round((o['close']/r['recommend_price']-1)*100,2)
    if c in S: r['status_after']=f"✅ 結算 {S[c]['result']}（{S[c]['by']}）入帳 {S[c]['close']} {S[c]['ret']:+.2f}%"
    elif c in DMAP: r['status_after']=f"✅ 續抱 {DMAP[c]}（反轉等級待 10-06 T86 v2）"
    elif c=='1326': r['status_after']="⚠️ 待複核複核②待 10-06 T86（v2）；D1/10"
# stop loss after-market check
t['stop_loss_check_after_v8310']={'time':'2026-10-06 盤後（收盤價）','results':[
 {'stock_code':'2330','stock_name':'台積電','close':2585.0,'stop_loss':None,'hit':'不適用（yaml 無 stop_loss 欄位，零股 0.15 張）'},
 {'stock_code':'6770','stock_name':'力積電','close':74.3,'stop_loss':73.26,'hit':'✅ 未觸發（+1.42%）；惟已決事項 L4 今日開盤出場'},
 {'stock_code':'2337','stock_name':'旺宏','close':119.5,'stop_loss':147.6,'hit':'🛑 觸及停損（-19.04%，重複輸出；流程紀錄已出場、yaml 未更新）'},
 {'stock_code':'2313','stock_name':'華通','close':252.0,'stop_loss':235.98,'hit':'✅ 未觸發（+6.79%）'},
 {'stock_code':'3090','stock_name':'日電貿','close':173.0,'stop_loss':256.5,'hit':'🛑 觸及停損（-32.55%，重複輸出；yaml 未更新）'},
 {'stock_code':'1301','stock_name':'台塑','close':68.6,'stop_loss':54.08,'hit':'✅ 未觸發（+26.85%）'},
 {'stock_code':'4938','stock_name':'和碩','close':90.0,'stop_loss':76.5,'hit':'✅ 未觸發（+17.65%）；惟已決事項 L4 今日開盤出場'}],'new_triggers':0}
t['two_day_drawdown_check_after']={'time':'2026-10-06 收盤','rule':'10-02 收盤→10-06 收盤','triggers':0,
 'values':{c:cl[c]['d2'] for c in cl if c!='2867'}}
t['series_alignment_check_after_v838']={'expected_last_day':'2026-10-06','all_aligned_except_frozen':True,
 'frozen':['2867 三商壽（末日 2026-08-19）'],'checked':[c for c in cl]}
t['market_close']={'taiex':49822.55,'taiex_prev_close':49712.04,'taiex_change_pct':0.22,'taiex_high':49968.92,'taiex_low':49479.69,
 'source':'Yahoo ^TWII 日K 10-06 列（09:00:00 時戳，meta regularMarketPrice 49,822.55 一致）','note':'創收盤新高'}
res=[]
for c,v in S.items():
    res.append({'stock_code':c,'stock_name':v['name'],'recommend_date':v['date'],'recommend_price':v['price'],'settled_price':v['close'],'return_pct':v['ret'],'result':v['result'],'holding_days':v['D'],'settled_by':v['by']})
succ=sum(1 for v in S.values() if v['result']=='success'); n=len(S)
t['yesterday_verification']={'date':TODAY,'settled_count':n,'success':succ,'fail':n-succ,'accuracy':round(succ/n*100,1),
 'note':'今日結算 4 筆：2 筆 settlement_checker 觸及目標價（6257 矽格、8150 南茂）＋2 筆已決事項鐵律③ L4 開盤出場（2609 陽明 fail、2327 國巨* success）；入帳價一律 10-06 收盤（v8.3.2）；holding 不計入分母',
 'results':res,'cumulative':{'settled_accuracy':'55.9%','success':402,'fail':317,'settled':719,'holding':176,'source':'update_predictions.py 2026-10-06（只執行一次，執行前備份 _after/predictions_before.json）'}}
t['after_market_version']='v1（14:40，10-06 T86 未公布；法人反轉複核②、L4 方向性檢核、明日推薦待 v2）'
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok',n,succ)
