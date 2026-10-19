import json
T='2026-10-19'
def rec(code,name,ind,price,score,pos,reason):
    return dict(stock_code=code,stock_name=name,industry=ind,recommend_date=T,recommend_price=price,
        target_price=round(price*1.08,2),stop_loss_pct=-10,stop_loss=round(price*0.9,2),settlement_days=10,
        position=pos,score=score,result="holding",reason=reason)
recs=[
 rec('1326','台化','塑化（industry_chains 塑化／tier_from_tracker）',78.7,97,'10%',
  '🛤️軌道A 法人TOP50 #23（avg_rank 21）；📶訊號A L2（4天在TOP50、動能-73.9%、5日+1.4%，+10）、動能<-30% +15；10-16 三大法人+8,570張、10日累計+69K、近5天外資+12K；反轉L0；EPS YoY+190%（+5）；營收YoY+44.8%（5日未回檔故不加分）；月線+9.3%。⚠️風險：真連買僅1天；催化僅「塑化」中度（中東地緣為超強但標→）；美股對應龍頭無；週一預期跳空低開'),
 rec('1802','台玻','PCB材料／玻纖布（industry_chains 查無，topic_tracker ABF載板/PCB 強催化）',66.9,90,'10%',
  '🛤️軌道A 法人TOP50 #7（avg_rank 8.0）；📶訊號A L2（2天在TOP50、動能+45.5%，+10）；10-16 三大法人+18K、10日累計+73K、近5天外資+39K、外資持股比週增+0.48%；反轉L0；EPS YoY+247%、毛利率QoQ+4.1pp（+5）；營收YoY+34.1%連7月成長；月線+9.9%。⚠️風險：「玻纖布漲停」已列MI投機末段訊號、真連買僅1天、10日內賣超4天、費半連8黑'),
 rec('1605','華新','電線電纜／鋼鐵（tier_from_tracker）',38.5,83,'5-10%',
  '🛤️軌道A 法人TOP50 #17（avg_rank 25）；📶訊號A L2（2天在TOP50、動能-44.0%、5日-1.5%，+10）、動能<-30% 區間+10；10-16 三大法人+9,561張、10日累計+49K、近5天外資+11K；反轉L0；EPS YoY+1600%（+5）；營收YoY+10.3%；外資持股比週減-0.15%（-3）；月線+1.0%但在TOP50（過法人現身門檻）。⚠️風險：催化僅中度（鋼鐵／能源週）、法人排名偏後'),
]
carry=[
 dict(stock_code='2002',stock_name='中鋼',recommend_date='2026-10-13',recommend_price=19.2,target_price=20.74,stop_loss_pct=-10,stop_loss=17.28,settlement_days=10,holding_days_label='D3/10',last_close=19.55,source='tracking_2026-10-13.json',status='⏳沿用；L0；10-16 +44,262張（TOP50 #1）'),
 dict(stock_code='2886',stock_name='兆豐金',recommend_date='2026-10-13',recommend_price=50.0,target_price=54.0,stop_loss_pct=-10,stop_loss=45.0,settlement_days=10,holding_days_label='D3/10',last_close=53.7,source='tracking_2026-10-13.json',status='⏳沿用；L0；10-16 +12,090張；距目標0.6%'),
 dict(stock_code='2892',stock_name='第一金',recommend_date='2026-10-13',recommend_price=39.7,target_price=42.88,stop_loss_pct=-10,stop_loss=35.73,settlement_days=10,holding_days_label='D3/10',last_close=41.5,source='tracking_2026-10-13.json',status='⏳沿用；L0（中性）；10-16 +1,478張、10日累計+40K'),
 dict(stock_code='6209',stock_name='今國光',recommend_date='2026-10-16',recommend_price=93.0,target_price=100.44,stop_loss_pct=-10,stop_loss=83.7,settlement_days=10,holding_days_label='D0/10',last_close=100.5,source='tracking_2026-10-16.json',status='⏳沿用；L0；10-16 +6,368張；已收在目標價上方但D0不結算；🟡週轉30.4%、近6日累積週轉97.8%接近注意門檻（自算）'),
 dict(stock_code='2882',stock_name='國泰金',recommend_date='2026-10-16',recommend_price=113.5,target_price=122.58,stop_loss_pct=-10,stop_loss=102.15,settlement_days=10,holding_days_label='D0/10',last_close=116.0,source='tracking_2026-10-16.json',status='⏳沿用；L0；10-16 +7,402張'),
 dict(stock_code='2867',stock_name='三商壽',recommend_date='2026-08-17',recommend_price=9.75,target_price=10.73,stop_loss_pct=-10,stop_loss=8.78,settlement_days=10,holding_days_label='凍結',last_close=9.7,source='tracking_2026-08-17.json',status='⚠️序列停滯（末日2026-08-19）凍結判定；併購停止買賣待公告人工結案'),
]
for c in carry: c['recommend_date_note']=c['recommend_date']
def ex(c,n,cat,r): return dict(stock_code=c,stock_name=n,category=cat,reason=r,decided=True)
exits=[
 ex('6770','力積電','持倉 my_holdings.yaml（已決 L4＋鐵律①）','10-16收67.3<停損73.26；10-16 T86 +5,441張但10日累計-281K；已決不重評；yaml未更新'),
 ex('2337','旺宏','持倉 my_holdings.yaml（已決，鐵律①）','10-16收107.0<停損147.6；10-16 T86 +4,148張、10日累計-36K'),
 ex('3090','日電貿','持倉 my_holdings.yaml（已決，鐵律①）','10-16收170.5<停損256.5；10-16 T86 -1,805張佔13.4% L4（與決議同向）'),
 ex('1301','台塑','持倉 my_holdings.yaml（已決 L4）','已決不重評；10-16 T86 -15,095張佔8.5% L4（同向）；收82.1；損益約+36%超yaml停利20%'),
 ex('2313','華通','持倉 my_holdings.yaml（已決 L4＋鐵律①）','已決不重評；揭露：10-16收248.0已站回停損235.98、T86 +16,859張翻買（不改變已決事項）'),
 ex('4938','和碩','持倉 my_holdings.yaml（已決 L4）','已決不重評；揭露：10-16 T86 +6,413張翻買、收102.0'),
 ex('2330','台積電','持倉 my_holdings.yaml 零股0.15張（已決）','已決不重評；10-16 T86 -22,372張佔76.2% L4（同向）'),
]
t=dict(date=T,version='v8.3.11',phase='before_market',settings=dict(stop_loss_pct=-10,settlement_days=10),
 market_context=dict(taiex_10_16=47111.26,vs_ma20=-2.1,vs_ma240=24.24,vix=21.45,sox=-3.83,nasdaq=-2.15,sp500=-1.09,night_futures='-1,144點',foreign='連賣8日，上週-5,862億史上最大單週賣超',ai_bubble_stage='惡化'),
 prior_decisions_executed=exits,opening_exits_today=exits,
 stop_loss_check_v8310=[dict(code='6770',close=67.3,stop=73.26,hit=True),dict(code='2337',close=107.0,stop=147.6,hit=True),dict(code='3090',close=170.5,stop=256.5,hit=True),dict(code='2313',close=248.0,stop=235.98,hit=False),dict(code='1301',close=82.1,stop=54.08,hit=False),dict(code='4938',close=102.0,stop=76.5,hit=False)],
 recommendations=recs,carry_over=[c['stock_code'] for c in carry],carry_over_recommendations=carry,
 module_a_result=dict(L3=0,L2=['1314','2313','1326','4958','1802','1605'],L1=['2883','3702']),
 module_b_result=dict(preposition=0,institutional_in=0,excluded_surge=0,note='美股龍頭7日全面下跌，無預先佈局候選'),
 defense_ratio=dict(vix=21.45,catalyst='超強但AI鏈重挫',defense_pct='15-25%',note='3檔新推薦偏防禦（塑化／材料／電纜），已揭露'),
 removed_stocks=[],disposition_stocks=dict(twse_disposition=14,note='候選池與持倉無官方處置股；6209 今國光為自算接近注意門檻（非官方）'),
 track_b_recommendations=[],tomorrow_pending_review=[],tomorrow_opening_exits=[],tomorrow_recommendations=[])
json.dump(t,open('data/tracking/tracking_2026-10-19.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
