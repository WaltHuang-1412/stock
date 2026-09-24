import json
P='data/tracking/tracking_2026-09-24.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-09-24/_intraday_prices.json',encoding='utf-8'))
pb=json.load(open('data/2026-09-24/_trackb_prices.json',encoding='utf-8'))
TS='2026-09-24 12:12'
def src_price(code,d):
    s=json.load(open(f'data/tracking/tracking_{d}.json',encoding='utf-8'))
    for k in ['recommendations','track_b_recommendations','carry_over_recommendations']:
        for r in s.get(k,[]) or []:
            if r.get('stock_code')==code and r.get('recommend_price'): return r['recommend_price']
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        r['intraday_day_change_pct']=p['chg']
        if c=='2867':
            r['intraday_time']='序列停滯凍結（Yahoo 報價 9.7 為 08-19 舊值）'; r.pop('intraday_return_pct',None); r.pop('intraday_day_change_pct',None)
for r in t['opening_exits_today']:
    c=r['stock_code']; p=pr[c]; rp=src_price(c,r['recommend_date'])
    r['intraday_price']=p['price']; r['intraday_time']=TS
    if rp: r['recommend_price']=rp; r['intraday_return_pct']=round((p['price']/rp-1)*100,2)
    r['execution_status']='盤前已列開盤出場清單，已執行；入帳價依 v8.3.2 盤後填當日收盤價'
t['track_b_recommendations']=[]
obs=[
 ('6838','台新藥','偵測器強訊號 75（連買6天、量比4.41x、今日 -2.5%）；產業未分類（industry_chains 查無）、不在 TOP50、10日累計僅 +141 張；五維度 時事8＋法人5＋產業5＋技術9＋價位13＝40，偵測器 +5、EPS YoY -205%／毛利率 QoQ -240pp -5、營收快取落後至 2026-05 不採計 → 40 分 <75'),
 ('6443','元晶','偵測器中訊號 40；反轉狀態不明（10日累計 -8,658 張為負）→ 準確率③未過；營收連續衰退16個月 -5'),
 ('3045','台灣大','L0、真連買10天、今日 -0.81%；準確率①催化對齊未過（電信不在今日🔴影響鏈），同盤前'),
 ('2603','長榮','L0；近5天外資 -6 張 → 準確率②未過，同盤前'),
 ('2351','順德','L0、今日 -3.32%；準確率①未過（僅登錄銅價線纜 tier_from_tracker），同盤前'),
 ('2027','大成鋼','L0、今日 +2.36%；準確率①未過（鋼鐵無🔴對應）＋模式 cold 33%，同盤前'),
 ('2104','國際中橡','今日 -4.72%；動能 +500% 一票否決（無🔴覆寫依據）'),
 ('1314','中石化','今日 -2.0%；動能 +500% 一票否決；營收 -5'),
 ('1101','台泥','今日 -1.95%；動能 +249% 一票否決（水泥⚪、模式 cold 30%）'),
 ('2618','長榮航','今日 -2.33%；動能 +500%，🔴中東影響鏈為負向不構成覆寫'),
 ('2610','華航','今日 -1.71%；動能 +355% 一票否決；EPS -5'),
 ('3016','嘉晶','今日 +9.97% 漲停 ≥3% 已反映；5日 +26% 已大漲'),
 ('3189','景碩','今日 +5.3% ≥3% 已反映'),
 ('8150','南茂','今日 +4.21% ≥3% 已反映；處置預警⏳最快剩1天'),
 ('2344','華邦電','反轉狀態不明（10日累計 -71K）'),
 ('2330','台積電','反轉狀態不明（10日累計 -15K）'),
 ('2379','瑞昱','動能 +146%（網路晶片不在今日🔴影響鏈點名，不覆寫）；EPS -5'),
 ('9904','寶成','動能 +155% 一票否決'),
 ('1216','統一','動能 +233% 一票否決'),
 ('1102','亞泥','動能 +153% 一票否決；營收連續衰退 -5'),
]
t['track_b_observations']=[{'stock_code':a,'stock_name':b,'intraday_price':(pb.get(a) or {}).get('price'),'intraday_change_pct':(pb.get(a) or {}).get('chg'),'note':n} for a,b,n in obs]
t['intraday']={
 'time':'2026-09-24 12:30','taiex':47871.06,'taiex_change_pct':-0.59,'taiex_base':'09-23 收盤 48,157.29（Yahoo ^TWII curl，12:13 報價）',
 'preflight':{'warnings':1,'errors':1,'l4_error_verdict':'2891/3481/2382/5880/2377/3023 為盤前已列開盤出場（已執行）；2890/2615/1326/4958/2327/2492/2345/2881/2882/2885 為盤前候選池排除股，非持有 → 無漏出場'},
 'exit_rules':{'stop_loss_hits':0,'two_day_drawdown_hits':0,'reversal_l3_l4_new':0,'pending_review':0},
 'targets_reached_intraday_not_settled':['3042 晶技 盤中高 212.0／12:12 報 201.0＝目標 201.0（收盤≥201 才結算）','3711 日月光投控 盤中高 697.0／目標 695.0（12:12 回落 693.0）'],
 'frozen':['2867 三商壽（序列停滯，末日 2026-08-19）'],
 'holdings_stop_loss_recheck':'0 筆新觸發；6770 70.7<73.26、2337 116.0<147.6、2313 221.5<235.98、3090 165.0<256.5 皆為已出場部位（yaml 未更新）重複輸出；1301 63.8、4938 91.5 未觸發；2330 無停損欄',
 'prior_decisions_status':'已決事項 1/1（2891 中信金）＋當日 L4 開盤出場 5/5（3481/2382/5880/2377/3023）',
 'track_b_result':'今日無盤中新推薦（0 檔）；偵測器唯一強訊號 6838 台新藥 40 分 <75',
 'dossier_intraday':'無盤中新推薦 → 依 Step 3.5 免跑',
 'tier_from_tracker_added':0,
 'data_source_notes':['現價取 Yahoo chart meta.regularMarketPrice（12:11~12:15）','前收取 get_close_series 09-23 收盤','intraday_institutional_detector 535 檔連買股僅取得 41 檔即時行情（TWSE MIS 限流），偵測覆蓋率 7.7%','盤中 check_* 腳本 JSON 另存 _intraB/*_intraday.json，盤前版本已還原']
}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
for r in t['opening_exits_today']: print(r['stock_code'],r.get('recommend_price'),r['intraday_price'],r.get('intraday_return_pct'))
for r in t['carry_over_recommendations']+t['recommendations']: print(r['stock_code'],r['recommend_price'],r.get('intraday_price'),r.get('intraday_return_pct'))
