import json
P='data/tracking/tracking_2026-09-23.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-09-23/_intraday_prices.json',encoding='utf-8'))
TS='2026-09-23 12:11'
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        if c=='2867': r['intraday_time']='序列停滯凍結（Yahoo 報價 9.7 為 08-19 舊值）'
for r in t['opening_exits_today']:
    p=pr[r['stock_code']]; r['intraday_price']=p['price']; r['intraday_time']=TS
    r['execution_status']='盤前已列開盤出場清單，已執行；入帳價依 v8.3.2 盤後填當日收盤價'
t['pending_review_v833'][0]['intraday_recheck_1230']={
 'time':TS,'sell':-3329,'ratio_pct':8.4,'result':'≥5%（複核①成立）',
 'note':'賣超張數與盤前相同（仍為 09-22 T86 -3,329 張），佔比 6.9%→8.4% 純屬 avg_5day_volume 分母漂移；依 v8.3.3 待複核程序，不因盤中跨過 8% 改判立即出場，盤後複核②仍 ≥5% 即 09-24 開盤出場',
 'cum10_three_inst':'+45K','intraday_price':pr['2891']['price']}
t['track_b_recommendations']=[]
obs=[
 ('2409','友達','動能 +455% 一票否決；5日 +31.4%；處置預警⏳連3天/最快剩0天；今日 -3.96%'),
 ('2449','京元電子','偵測器強訊號 80；動能 +500% 一票否決＋5日 +23.3% 已大漲；今日 -3.94%'),
 ('3189','景碩','5日 +14.3% 已大漲（>10% 預設不評分）；動能 +80.2%'),
 ('4958','臻鼎-KY','反轉狀態不明（累計 -12,098）、近5天外資 -6,192 → 準確率②③未過'),
 ('8150','南茂','動能 +500%、5日 +25.0%；處置預警⏳最快剩1天'),
 ('2327','國巨*','動能 +206% 一票否決（🟡被動元件，無超強覆寫）'),
 ('2317','鴻海','反轉狀態不明（累計 -5,432）、動能 +156%'),
 ('6168','宏齊','偵測器強訊號 90，但今日 -7.5%／量比 2.18x → 型態轉弱攔截；動能 +500%、5日 +50.4%；處置⏳最快剩0天'),
 ('2618','長榮航','動能 +254%；近5天外資 -1,958 → 準確率②未過'),
 ('6770','力積電','動能 +328%（🔴DRAM 覆寫）但盤前評分 68 <75；5日 +7.3%'),
 ('6257','矽格','動能 +461%、5日 +20.0% 已大漲'),
 ('2481','強茂','動能 +156%、5日 +11.4%'),
 ('2610','華航','動能 +204%（航空未列🔴影響鏈，不覆寫）'),
 ('6278','台表科','5日 +18.3% 已大漲'),
 ('3045','台灣大','籌碼乾淨（真連買10天、動能 -7.6%）但準確率①催化對齊未過（電信不在今日🔴影響鏈）'),
 ('6116','彩晶','動能 +269% 一票否決'),
 ('3035','智原','動能 +500% 一票否決'),
 ('2354','鴻準','準確率①未過（蘋果鏈🟢↓）；外資持股比 -0.26% -3'),
 ('2492','華新科','反轉狀態不明（累計 -12,993）'),
 ('6213','聯茂','近5天外資 -1,763 → 準確率②未過'),
 ('2379','瑞昱','🔴光通訊與網通 超強覆寫動能 +114%，五維度 74（時事21/法人17/產業15/技術10/價位11）－5日+7.4% -10－EPS 連5季YoY負 -5 ＝ 59 <75'),
 ('6674','鋐寶科技','偵測器強訊號 70；產業未分類、不在TOP50；五維度約 44＋偵測器 +5－營收連4月衰退 -5－EPS -5 ＝ 39 <75'),
 ('3037','欣興','今日 +3.57% ≥3% 已反映'),
 ('1101','台泥','今日 +4.48% ≥3% 已反映'),
 ('3016','嘉晶','今日 +9.81% 漲停 已反映'),
 ('6189','豐藝','偵測器強訊號 60；動能 +269% 一票否決、產業未分類無覆寫依據'),
]
t['track_b_observations']=[{'stock_code':a,'stock_name':b,'intraday_price':(json.load(open('data/2026-09-23/_trackb_prices.json',encoding='utf-8')).get(a) or {}).get('price'),'note':n} for a,b,n in obs]
t['intraday']={
 'time':'2026-09-23 12:30','taiex':48100.46,'taiex_change_pct':0.63,'taiex_base':'09-22 收盤 47,800.17（盤前報告 Yahoo ^TWII；本次 chart 序列 09-22 close=None）',
 'preflight':{'warnings':1,'errors':1,'l4_error_verdict':'2883/2330 為盤前已列開盤出場；2891 為 v8.3.3 待複核；2834/2408/2344/2337 為盤前候選池排除股（2337 yaml 殘留，09-11 已出場）→ 無漏出場'},
 'exit_rules':{'stop_loss_hits':0,'two_day_drawdown_hits':0,'reversal_l3_l4_new':0,'pending_review':1},
 'targets_reached_intraday_not_settled':['3042 晶技 201.5（漲停）/目標 201.0','2303 聯電 盤中高 163.0/目標 161.0（12:11 回落 159.5）','3711 日月光投控 盤中高 711.0/目標 695.0（12:11 回落 693.0）'],
 'frozen':['2867 三商壽（序列停滯，末日 2026-08-19）'],
 'holdings_stop_loss_recheck':'0 筆新觸發；2337/2313/3090 低於停損為已出場部位重複輸出（yaml 未更新）；6770 73.3 回到停損 73.26 之上（09-21 已出場）',
 'prior_decisions_status':'盤前已決事項 0 筆；當日 L4 開盤出場 2/2（2883 凱基金、2330 台積電零股）',
 'track_b_result':'今日無盤中新推薦（0 檔）；26 檔候選排除理由見 track_b_observations',
 'dossier_intraday':'無盤中新推薦 → 依 Step 3.5 免跑',
 'tier_from_tracker_added':0,
 'data_source_notes':['現價取 Yahoo chart meta.regularMarketPrice（12:07~12:11）','前收取 get_close_series 09-22 收盤','盤中分批執行 check_* 腳本的 JSON 已另存 _intraB/*_intraday.json，盤前版本以 git 還原']
}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
