import json
TODAY='2026-10-06'; f=f'data/tracking/tracking_{TODAY}.json'
t=json.load(open(f,encoding='utf-8'))
DEC='2026-10-06 盤後（10-06 T86 於 16:07 公布後掃描，快取由 16:07 原始檔寫入）'
RV={'3711':(0,276,'L0，真連買 5 天，10 日累計 +24,255'),'3035':(0,780,'L0，真連買 4 天，10 日累計 +11,362'),'1326':(0,13567,'買超中 +13,567（外資 +13,370）→ 複核② 降級，維持追蹤'),
 '2308':(0,853,'L0，真連買 2 天'),'2330':(4,-1299,'L4 5.8%（<8%）且 10 日累計 +7,571 為正 → 待複核'),'3443':(0,101,'L0'),
 '3231':(4,-4981,'L4 12.9%（≥8%）且 10 日累計 -1,578 → 10-07 開盤出場'),'3661':(0,885,'L0，真連買 3 天'),'2344':(4,-3830,'L4 5.4%（<8%）且 10 日累計 +28,132 為正 → 待複核')}
for r in t['recommendations']:
    c=r['stock_code']; lv,tt,note=RV[c]
    r['reversal_level_1006']=lv; r['t86_1006_total']=tt; r['reversal_note_1006']=note
    r['holding_status']=r['holding_status'].replace('法人反轉等級待 10-06 T86（v2）',f'10-06 T86 {tt:+,} 張｜{note}')
for r in t['carry_over_recommendations']:
    c=r['stock_code']
    if c=='1326': r['status_after']='✅ 維持追蹤 D1/10：複核① 12:30 6.5% 成立、複核② 盤後 10-06 T86 翻買 +13,567 張（買超中）→ 降級，計時器結束（v8.3.3 兩次皆 ≥5% 才出場）'
    elif c in RV: r['status_after']=f'✅ 續抱｜10-06 T86 {RV[c][1]:+,}｜{RV[c][2]}'
for pr in t['pending_review_v833']:
    if pr['stock_code']=='8150': pr['review_2_result']='不適用：10-06 收盤 127.5 ≥ 目標 124.5 → settlement_checker 結算 success（D2），結算優先於待複核；10-06 T86 翻買 +8,244 張'; pr['final']='settled success +10.39%'
    if pr['stock_code']=='1326': pr['review_2_result']='盤後 10-06 T86 +13,567 張（外資 +13,370／自營 +197）→ 買超中、非 L3/L4 → 複核② 不成立'; pr['final']='降級，維持追蹤，計時器結束'; pr['review_2_price']=73.0
t['holdings_reversal_scan_after']={'t86_date':'2026-10-06','t86_published':'16:07','scanned':19,'results':{
 '3711':'L0 +276','3035':'L0 +780','1326':'買超中 +13,567','2308':'L0 +853','2330':'L4 -1,299（5.8%）','3443':'L0 +101','3231':'L4 -4,981（12.9%）','3661':'L0 +885','2344':'L4 -3,830（5.4%）',
 '6770':'L4 -16,606（14.0%）持倉已決','4938':'狀態不明 +958（10 日累計 -8,184）持倉已決','2337':'L2 -620 持倉（停損重複輸出）','3090':'L0 +547 持倉','2313':'買超中 +20,399 持倉','1301':'買超中 +4,508 持倉',
 '2609':'買超中 +5,303（今日已出場）','2327':'L3 -2,466（今日已出場）','6257':'買超中 +7,204（今日已結算）','8150':'買超中 +8,244（今日已結算）'}}
def E(c,n,cat,d,p,cl,ret,reason):
    return {'stock_code':c,'stock_name':n,'category':cat,'recommend_date':d,'recommend_price':p,'last_close':cl,'return_pct_at_close':ret,'reason':reason,'decided_on':DEC}
t['tomorrow_opening_exits']=[E('3231','緯創','鐵律③ L4','2026-10-06',189.5,189.5,0.0,'10-06 T86 賣超 -4,981 張（外資 -3,551／投信 -1,146／自營 -285）＝12.9%（≥8%，不受 v8.3.3 保護）且 10 日累計 -1,578 為負；🔥覆寫型 D0 即轉 L4（第 13 筆）；10-07 開盤出場，入帳價用 10-07 收盤（v8.3.2）')]
t['tomorrow_pending_review']=[
 dict(E('2330','台積電','⚠️ 待複核（v8.3.3）','2026-10-06',2575.0,2585.0,0.39,'10-06 T86 賣超 -1,299 張（外資 -1,673／投信 -22／自營 +395）＝5.8%（<8%）且 10 日累計三大法人 +7,571 張為正 → 不開盤出場，列待複核；10-07 12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-08 開盤出場。觸及停損 2,317.5 或 2 日 -10% 則立即出場。10/08 9 月營收'),sell_ratio_pct=5.8,cum10=7571,review_1='10-07 12:30',review_2='10-07 盤後',timer_started='2026-10-06 盤後'),
 dict(E('2344','華邦電','⚠️ 待複核（v8.3.3）','2026-10-06',181.0,177.5,-1.93,'10-06 T86 賣超 -3,830 張（外資 +7,287／投信 -10,812／自營 -305）＝5.4%（<8%）且 10 日累計 +28,132 張為正 → 不開盤出場，列待複核；10-07 12:30 與盤後各複核一次。🔥覆寫型 D0 即轉 L4（第 14 筆）；停損 -5%＝171.95（距 3.1%）或 2 日 -10% 則立即出場'),sell_ratio_pct=5.4,cum10=28132,review_1='10-07 12:30',review_2='10-07 盤後',timer_started='2026-10-06 盤後')]
t['l4_exit_direction_check']={'note':'僅記錄不改判；累積樣本 18→23 筆，執行日法人翻買 16→19','rows':[
 {'stock_code':'2609','stock_name':'陽明','t86_exec_day':5303,'price_chg':0.85,'flip':True},{'stock_code':'6257','stock_name':'矽格','t86_exec_day':7204,'price_chg':10.0,'flip':True},
 {'stock_code':'4938','stock_name':'和碩','t86_exec_day':958,'price_chg':1.47,'flip':True,'source':'my_holdings.yaml'},{'stock_code':'2327','stock_name':'國巨*','t86_exec_day':-2466,'price_chg':-0.16,'flip':False,'level':'L3'},
 {'stock_code':'6770','stock_name':'力積電','t86_exec_day':-16606,'price_chg':-1.98,'flip':False,'level':'L4 14.0%','source':'my_holdings.yaml'}]}
t['market_close'].update({'bfi82u_total_yi':-207.9,'bfi82u':{'foreign':-66.6,'trust':-158.5,'dealer_self':36.1,'dealer_hedge':-18.9},'turnover_yi':10217.2,'volume_shares_yi':108.8,'source_bfi82u':'TWSE BFI82U 10-06（15:18 取得）','source_turnover':'TWSE FMTQIK'})
t['tomorrow_recommendations']=[]
t['tomorrow_carry_over']=[
 {'stock_code':'3711','stock_name':'日月光投控','recommend_date':'2026-10-01','recommend_price':703.0,'target_price':759.0,'stop_loss':632.7,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D3/10','last_close':744.0,'status':'✅ 續抱（L0，真連買 5）'},
 {'stock_code':'3035','stock_name':'智原','recommend_date':'2026-10-02','recommend_price':213.0,'target_price':230.0,'stop_loss':191.7,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D2/10','last_close':210.5,'status':'✅ 續抱（L0，真連買 4）'},
 {'stock_code':'1326','stock_name':'台化','recommend_date':'2026-10-05','recommend_price':71.7,'target_price':77.4,'stop_loss':64.53,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D1/10','last_close':73.0,'status':'✅ 續抱（待複核降級，買超中 +13,567）'},
 {'stock_code':'2308','stock_name':'台達電','recommend_date':'2026-10-06','recommend_price':2005.0,'target_price':2165.4,'stop_loss':1804.5,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D0/10','last_close':2050.0,'status':'✅ 續抱（L0）'},
 {'stock_code':'2330','stock_name':'台積電','recommend_date':'2026-10-06','recommend_price':2575.0,'target_price':2781.0,'stop_loss':2317.5,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D0/10','last_close':2585.0,'status':'⚠️ 待複核（L4 5.8%）'},
 {'stock_code':'3443','stock_name':'創意','recommend_date':'2026-10-06','recommend_price':8600.0,'target_price':9288.0,'stop_loss':7740.0,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D0/10','last_close':8375.0,'status':'✅ 續抱（L0）'},
 {'stock_code':'3661','stock_name':'世芯-KY','recommend_date':'2026-10-06','recommend_price':3950.0,'target_price':4266.0,'stop_loss':3555.0,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'D0/10','last_close':4180.0,'status':'✅ 續抱（L0，距目標 2.1%）'},
 {'stock_code':'2344','stock_name':'華邦電','recommend_date':'2026-10-06','recommend_price':181.0,'target_price':195.48,'stop_loss':171.95,'stop_loss_pct':-5,'settlement_days':10,'holding_days':'D0/10','last_close':177.5,'status':'⚠️ 待複核（L4 5.4%）🔥覆寫 -5%'},
 {'stock_code':'2867','stock_name':'三商壽','recommend_date':'2026-08-17','recommend_price':9.75,'target_price':10.73,'stop_loss':8.78,'stop_loss_pct':-10,'settlement_days':10,'holding_days':'凍結','last_close':9.7,'status':'⚠️ 序列停滯（末日 08-19）凍結'}]
t['tomorrow_recommendation_note']='新推薦 0 檔（寧缺勿濫）：10-06 TOP50 買超 50 檔＋軌道B 影響鏈 17 檔＋續抱／持倉 19 檔全部逐檔篩選，無一檔同時通過催化對齊①、外資近5天≥0②、反轉 L0③、動能≤100%（或🔴覆寫）、5日<10%、法人現身門檻；最接近者 2408 南亞科（🔴DRAM 覆寫、真連買 6）因不在 10-06 TOP50 買超且 vs MA20 +3.15% 落 0~+5% 區 → 法人現身門檻未過；2412 中華電（真連買 5）①未對齊；10-07 盤前以新資料重評'
t['watchlist_tomorrow']=['2408 南亞科（門檻未過：今日 +592 不在 TOP50、MA20 +3.15%）','2412 中華電（真連買 5、買 9 賣 1；①未對齊）','4906 正文（動能 -82.7%、EPS +90%；無催化提及、5 日 +6.97%）','2436 偉詮電（動能 -32.6%、營收 +32% 回檔 +5；無催化提及）','2892 第一金（10 日累計 +28,468、買 8 賣 2；無催化提及）','2301 光寶科（🔴AI 覆寫候選；今日 -269 不在 TOP50、MA20 +4.8% 門檻未過）']
t['disposition_after']={'twse_disposal_1610':['2030 彰源','2033 佳大','3016 嘉晶','3055 蔚華科','3167 大量','6526 達發','6533 晶心科','6672 騰輝電子-KY','8201 無敵','8996 高力'],'twse_attention':[],'in_pool':['3016 嘉晶（TOP50 買超第 50 名，機械排除）'],
 'self_calc_warning':['8150 南茂｜連續達標 5 天｜最快剩 0 天處置（今日已結算）','6213 聯茂｜連續達標 3 天｜最快剩 0 天','2492 華新科｜連續達標 4 天｜最快剩 1 天','4927 泰鼎-KY／1711 永光／1714 和桐｜連 1 天｜最快剩 2 天','1303 南亞／6456 GIS-KY／3094 聯傑｜接近注意門檻']}
t['data_quality_after']={'t86':'10-06 T86 16:07 公布（14:31 起每 90 秒輪詢，96 分鐘）；twse_institutional_cache.fetch_all_institutional 於 16:09 回傳 0 筆（requests 例外），改以 16:07 原始回應手工寫入 twse_t86_20261006.json（19,644 列，__cache_date__=20261006）；19 檔持倉 reversal／chip 今日張數與快取逐筆一致',
 'bfi82u':'15:18 取得','revenue':'26/26 檔 2026-08 新鮮','foreign_ratio':'26/26 檔 as_of 09-29～10-05','eps':'26/26 檔 2026Q2（2892／2884 停 2025-12-31 金控半年報→視為 0）','price_position':'序列末日 10-06','dossier':'stock_dossier_tomorrow.json 17 檔，來源三項 ok（法說會／除權息為 cache）','check_json_overwrite':'四支 check_* 腳本輸出已另存 _after/*_after.json，盤前 JSON 已還原'}
t['after_market_version']='v2（16:40，10-06 T86 16:07 公布後完整版；取代 14:45 v1）'
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok exits',len(t['tomorrow_opening_exits']),'pending',len(t['tomorrow_pending_review']),'carry',len(t['tomorrow_carry_over']))
