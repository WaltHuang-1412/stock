import json
P='data/tracking/tracking_2026-09-29.json'
t=json.load(open(P,encoding='utf-8'))
pr=json.load(open('data/2026-09-29/_intraday_prices.json',encoding='utf-8'))
pb=json.load(open('data/2026-09-29/_intraday_prices_top50.json',encoding='utf-8'))
pb.update({k:v for k,v in pr.items()})
TS='2026-09-29 12:18'
def src_price(code,d):
    s=json.load(open(f'data/tracking/tracking_{d}.json',encoding='utf-8'))
    for k in ['recommendations','track_b_recommendations','carry_over_recommendations']:
        for r in s.get(k,[]) or []:
            if r.get('stock_code')==code and r.get('recommend_price'): return r['recommend_price']
for key in ['recommendations','carry_over_recommendations']:
    for r in t[key]:
        c=r['stock_code']; p=pr.get(c)
        if not p or not p['price']: continue
        if c=='2867':
            r['intraday_time']='序列停滯凍結（Yahoo 報價 9.7 為 08-19 舊值）'; continue
        r['intraday_price']=p['price']; r['intraday_time']=TS
        r['intraday_return_pct']=round((p['price']/r['recommend_price']-1)*100,2)
        r['intraday_day_change_pct']=p['chg']
        r['intraday_two_day_pct']=p['drop2d']
        r['intraday_dist_to_stop_pct']=round((p['price']/r['stop_loss']-1)*100,2)
for r in t['opening_exits_today']:
    c=r['stock_code']; p=pr[c]; rp=src_price(c,r['recommend_date'])
    r['intraday_price']=p['price']; r['intraday_time']=TS
    if rp: r['recommend_price']=rp; r['intraday_return_pct']=round((p['price']/rp-1)*100,2)
    r['execution_status']='盤前已列開盤出場清單（鐵律③ L4，佔比 ≥8%）；盤中複掃仍為 L4；入帳價依 v8.3.2 盤後填當日收盤價'
t['track_b_recommendations']=[]
obs=[
 ('2031','新光鋼','偵測器強訊號 65（量比 1.8x、今日 -1.84%）；chip_analysis 真連買 3 天（偵測器稱 5 天，以 chip 為準）、動能 +500% → 動能一票否決（鋼鐵僅⚪觀察，無🔴覆寫依據）；另不在 TOP50 × vs MA20 +1.2% → 法人現身門檻未過。EPS +5／營收 0／持股比 0'),
 ('2027','大成鋼','L0、真連買 3 天、動能 -39.3%、今日 -0.74%；五維度 64（時事 10＋法人 20＋產業 13＋技術 13＋價位 8）＋動能 +15＋訊號A L3 +15＋EPS +5＋模式 cold 鋼鐵 33.3% -3＝96；但準確率①催化對齊未過（鋼鐵僅⚪觀察中）→ 不推薦，同盤前'),
 ('2351','順德','L0、真連買 3 天、動能 +24.7%、今日 -2.05%；五維度 54（時事 9＋法人 17＋產業 13＋技術 10＋價位 5）＋營收 +5＋EPS +5＋持股比 +5＝69 <75；準確率①未過（銅價線纜主題今日 topic_tracker 無對應）'),
 ('1708','東鹼','L0、真連買 3 天、動能 +27.0%、今日 -0.19%；industry_chains 查無＝未分類；五維度 51（時事 8＋法人 16＋產業 6＋技術 10＋價位 11）＋EPS +5＋持股比 +5＝61 <75'),
 ('2010','春源','偵測器中訊號 50；動能 +271.6% 一票否決；營收連續衰退 3 個月 -5'),
 ('6698','旭暉應材','偵測器中訊號 50；10 日累計僅 +166 張；營收連續衰退 7 個月 -5、EPS 連 4 季負成長 -5'),
 ('1303','南亞','TOP50 #1、今日 +2.73%；反轉狀態不明（10 日累計 -42K）、近 5 天外資 -24K → 準確率②③未過；Micron L1 預警'),
 ('3231','緯創','今日 +0.81%；反轉狀態不明（10 日累計 -46K）、近 5 天外資 -29K → 準確率②③未過'),
 ('9105','泰金寶-DR','今日 +2.97%；反轉狀態不明（10 日累計 -9,159）、近 5 天外資 -3,143；EPS 無數據'),
 ('2492','華新科','今日 -3.37%；反轉狀態不明（10 日累計 -13K）＋動能 +124.1% 一票否決'),
 ('3026','禾伸堂','今日 -2.35%；動能 +152.1% 一票否決；近 5 天外資 -457'),
 ('2615','萬海','今日 -3.03%；近 5 天外資 -1,544 → 準確率②未過'),
 ('6285','啟碁','今日 -1.68%；動能 +199.8% 一票否決；10 日累計 -3'),
 ('2034','允強','今日 +2.19%；動能 +259.1% 一票否決；處置預警：6日+10.7%／30日+17.1%／週轉2.9% 接近注意門檻'),
 ('2327','國巨*','今日 -5.17%；動能 +225.6% 一票否決；EPS 連 8 季負成長 -5'),
 ('3016','嘉晶','今日 +6.25% ≥3% 已反映；5 日 +38.5% 已大漲；處置預警'),
 ('8028','昇陽半導體','今日 +7.99% ≥3% 已反映'),
 ('6533','晶心科','今日 +9.96% ≥3% 已反映；處置預警'),
 ('2030','彰源','今日 +9.87% ≥3% 已反映；5 日 +29.4%；處置預警'),
 ('3518','柏騰','今日 +10.0% ≥3% 已反映'),
 ('2436','偉詮電','今日 +3.04% ≥3% 已反映；動能 +224%'),
]
t['track_b_observations']=[{'stock_code':a,'stock_name':b,'intraday_price':(pb.get(a) or {}).get('price'),'intraday_change_pct':(pb.get(a) or {}).get('chg'),'note':n} for a,b,n in obs]
t['intraday']={
 'time':'2026-09-29 12:30','taiex':47668.86,'taiex_change_pct':-0.74,'taiex_base':'09-24 收盤 48,024.6（Yahoo ^TWII curl，12:19 報價）',
 'preflight':{'warnings':1,'errors':1,'l4_error_verdict':'22 檔逐檔對照：2303/6770/2408/2317 為盤前已列開盤出場；2330/2337/2313/3090 為 my_holdings.yaml 仍列 quantity>0 但流程紀錄已於 09-11~09-23 出場之部位（yaml 未更新）；其餘 14 檔（2891/5880/1102/2605/2103/2834/2344/2345/2882/2383/1717/3661/2382/2881）為盤前候選池排除股，非 holding → 追蹤部位無漏出場'},
 'exit_rules':{'stop_loss_hits':0,'two_day_drawdown_hits':0,'reversal_l3_l4_new':0,'pending_review':0,
   'closest_to_stop':'2454 聯發科 4,940，距停損 4,759.5 還有 +3.79%','worst_two_day':'2454 聯發科 -4.73%（09-23 收 5,185 → 4,940）'},
 'opening_exits_recheck':'2303 聯電 21.7%／6770 力積電 39.1%／2408 南亞科 42.1%／2317 鴻海 73.2%（avg_5day_volume 分母，12:33 取樣），全部 ≥8% 仍為 L4',
 'targets_reached_intraday_not_settled':['8046 南電 12:19 報 1,275.0 ≥ 目標 1,260.0（收盤 ≥1,260 才結算）','2395 研華 盤中高 754.0 ≥ 目標 740.0（12:17 回落 738.0）'],
 'frozen':['2867 三商壽（序列停滯，末日 2026-08-19）'],
 'holdings_stop_loss_recheck':'0 筆新觸發；6770 72.3<73.26、2337 117.5<147.6、2313 226.0<235.98、3090 161.5<256.5 皆為流程紀錄已出場部位（yaml 未更新）重複輸出；1301 65.1、4938 91.0 未觸發；2330 無停損欄',
 'prior_decisions_status':'已決事項 0 筆；當日 L4 開盤出場 4 檔（2303/6770/2408/2317）',
 'detector':{'scanned':389,'realtime_fetched':40,'coverage_pct':10.3,'strong':['2031 新光鋼 65'],'moderate':['2010 春源 50','6698 旭暉應材 50']},
 'track_b_result':'今日無盤中新推薦（0 檔）；偵測器唯一強訊號 2031 新光鋼 動能 +500% 一票否決',
 'dossier_intraday':'無盤中新推薦 → 依 Step 3.5 免跑',
 'tier_from_tracker_added':0,
 'data_source_notes':['現價取 Yahoo chart meta.regularMarketPrice（12:17~12:19，約延遲 20 分鐘）','前收取 get_close_series 09-24 收盤','intraday_institutional_detector 389 檔連買股僅取得 40 檔即時行情（TWSE MIS 限流），覆蓋率 10.3%','盤中 check_* 腳本 JSON 另存 _intraB/*_intraday.json，盤前版本已還原','法人數據為 09-24 T86（與盤前同一份），今日 T86 盤後才公布']
}
json.dump(t,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('ok')
for r in t['opening_exits_today']: print(r['stock_code'],r.get('recommend_price'),r['intraday_price'],r.get('intraday_return_pct'))
for r in t['recommendations']+t['carry_over_recommendations']: print(r['stock_code'],r['stock_name'],r['recommend_price'],r['stop_loss'],r.get('intraday_price'),r.get('intraday_day_change_pct'),r.get('intraday_return_pct'),r.get('intraday_dist_to_stop_pct'),r.get('intraday_two_day_pct'),r.get('holding_days'))
