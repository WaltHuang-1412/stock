import json
def ld(p): return json.load(open(p,encoding='utf-8'))
def sv(p,o): json.dump(o,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
TODAY='2026-11-17'
tp=f'data/tracking/tracking_{TODAY}.json'
t=ld(tp)
cl={'2886':(54.7,0.37,0,'D0 續抱；L1（買超減速 -50.5%，今日仍 +3,222 張、真連買 10 天、10 日累計 +61K）'),
    '5876':(53.3,4.51,6,'D6 續抱；L0（今日 +2,250 張、真連買 5 天、累計 +12K）；11/20 法說'),
    '2412':(164.5,2.17,3,'D3；盤後新增 L4（今日 T86 賣超 -3,151 張佔 5 日均量 26.6%，≥8% 不受待複核保護）→ 2026-11-18 開盤出場；11/18 法說'),
    '2801':(28.15,-0.88,2,'D2 續抱；L0（今日 +710 張、真連買 5 天、累計 +2,988）'),
    '2884':(46.65,-3.42,1,'D1；盤後新增 L4（今日 T86 賣超 -3,291 張佔 5 日均量 10.1%，≥8% 不受待複核保護）→ 2026-11-18 開盤出場；今日 15:30 法說後'),
    '4904':(108.5,-0.91,1,'D1 續抱；待複核結果：盤後以今日 T86 重跑為 L0（今日 +576 張、累計 +12K）→ 降級，維持追蹤；11/19 法說，不加碼')}
for sec in ('recommendations','carry_over_recommendations'):
    for r in t.get(sec,[]):
        c=r['stock_code']
        if c in cl:
            r.update(actual_close=cl[c][0],close_price=cl[c][0],return_pct=cl[c][1],holding_days=cl[c][2],holding_days_label=f'D{cl[c][2]}/10',holding_status=cl[c][3],result='holding')
t['phase']='after_market'
t['after_market_taiex']=dict(close=40092.11,prev_close=41040.08,change_pts=-947.97,change_pct=-2.31,source='Yahoo ^TWII meta.regularMarketPrice 13:33')
t['after_market_institutional']=dict(total_yi=-547.25,foreign_yi=-380.94,trust_yi=-9.35,dealer_yi=-156.96,source='TWSE BFI82U 2026-11-17')
t['after_market_checks']=dict(date=TODAY,
 t86_note='11-17 T86 於 16:36 可取得（twse_t86_20261117.json 16:37 落檔）；籌碼/反轉皆含今日完整 T86（_after/_chip_incl_today.py，END=11-17）。盤後對 12 檔候選重跑 price_position／revenue／eps／foreign_ratio 並覆寫當日 JSON，institutional_top50.json 亦改為 11-17 版；盤前版備份於 _after/bak/。',
 settlements_today=0,
 stop_loss_check={"6770":[51.5,73.26,True],"2337":[71.9,147.6,True],"2313":[184.5,235.98,True],"3090":[118.5,256.5,True],"1301":[67.5,54.08,False],"4938":[83.8,76.5,False],"2330":[2170.0,None,None]},
 two_day_drop_check='追蹤股無 2 日累計 <-10%（2886 -1.26%、5876 -0.19%、2412 -0.30%、2801 -2.93%、2884 -3.42%、4904 -0.91%）；持倉 2313 華通 -10.22%、3090 日電貿 -12.87% 觸及（本就已決出場），6770 -9.65%、2337 -9.67%',
 series_alignment='6 檔追蹤股與 7 檔持倉序列末日皆為 2026-11-17 ✓',
 stale_series='2867 三商壽 序列查詢失敗（併購停牌），凍結（已知，非新增）',
 source_files_written_back=[])
t['after_market_holding_status']={"2886":"D0；L1；續抱","5876":"D6；L0；續抱","2412":"D3；L4 26.6% → 11/18 開盤出場","2801":"D2；L0；續抱","2884":"D1；L4 10.1% → 11/18 開盤出場","4904":"D1；待複核降級 L0；續抱"}
t['pending_review_result']=[dict(stock_code='4904',stock_name='遠傳',recommend_date='2026-11-16',review_1_intraday='L4 5.2%（11/16 T86 -496 張）',review_2_after='L0（11/17 T86 +576 張，10 日累計 +11,998 張）',review_2_source='今日新公布 T86（非同源）',verdict='降級 → 不出場，維持追蹤')]
t['pending_review']=[]
t['removed_stocks']=[]
EX='原樣沿用（已決事項不重評）'
t['tomorrow_opening_exits']=[
 dict(stock_code='2412',stock_name='中華電',category='追蹤 tracking_2026-11-12（鐵律③ L4，盤後判定）',recommend_date='2026-11-12',recommend_price=161.0,reason='11-17 T86 三大法人賣超 -3,151 張（外資 -864、投信 -3,092），佔 5 日均量 26.6% ≥8%，不受 v8.3.3 待複核保護 → 次日開盤出場；11-17 收 164.5（+2.17%）；入帳價用 11-18 收盤'),
 dict(stock_code='2884',stock_name='玉山金',category='追蹤 tracking_2026-11-16（鐵律③ L4，盤後判定）',recommend_date='2026-11-16',recommend_price=48.3,reason='11-17 T86 三大法人賣超 -3,291 張（外資 +1,144、投信 -9,431），佔 5 日均量 10.1% ≥8%，不受 v8.3.3 待複核保護 → 次日開盤出場；11-17 收 46.65（-3.42%）；入帳價用 11-18 收盤'),
 dict(stock_code='6770',stock_name='力積電',category='持倉｜已決事項（鐵律①觸及停損價）',reason=f'11-17 收盤 51.5<停損 73.26；今日 L3（近2日 -12,742 張）；{EX}'),
 dict(stock_code='2337',stock_name='旺宏',category='持倉｜已決事項（鐵律①）',reason=f'收盤 71.9<停損 147.6；今日 +2,051 張但 10 日累計 -11,312（狀態不明）；{EX}'),
 dict(stock_code='2313',stock_name='華通',category='持倉｜已決事項（鐵律①）',reason=f'收盤 184.5<停損 235.98；2 日 -10.22%；今日 L3；{EX}'),
 dict(stock_code='3090',stock_name='日電貿',category='持倉｜已決事項（鐵律①）',reason=f'收盤 118.5<停損 256.5；2 日 -12.87%；今日 L1；{EX}'),
 dict(stock_code='1301',stock_name='台塑',category='持倉｜已決事項（11-06 出場決議）',reason=f'{EX}；收盤 67.5>停損 54.08；今日法人 +3,266 張（健康）'),
 dict(stock_code='4938',stock_name='和碩',category='持倉｜已決事項（11/12 法說會，維持已決）',reason=f'{EX}；收盤 83.8>停損 76.5；今日 L3（近2日 -139 張）'),
 dict(stock_code='2330',stock_name='台積電零股',category='持倉｜已決事項（L4）',reason=f'{EX}；今日賣超 -5,508 張佔 16.5%（L4）；收 2,170')]
t['tomorrow_recommendations']=[]
t['tomorrow_observations']=[
 dict(stock_code='2892',stock_name='第一金',score=76,reason='今日進 TOP50（+2,476 張、avg_rank 26）、真連買 10 天、外資5日 +25K、動能 -45.5%（+15）、Fed 升息鏈↑；但反轉 L1（買超減速 -45.5%，-5）→ 準確率篩選③需 L0 不過；月線下 -0.8%；EPS 快取 Q2 不採計；金融已追蹤 4 檔'),
 dict(stock_code='2618',stock_name='長榮航',score=75,reason='法人強（+7,768 張、avg_rank 8、真連買 10 天、外資5日 +64K、健康）、月季線雙上、EPS +2；但 topic_tracker 中東鏈標「↓ 油價成本」、資金輪動鏈標「→」，催化方向矛盾（篩選①不明確，連三日）'),
 dict(stock_code='2883',stock_name='凱基金',score=69,reason='Fed 升息鏈↑、L0、外資5日 +58K、動能 -18.4%（+10）；但投信5日 -59K（外資買投信賣）、真連買僅 1 天、avg_rank 33.5、月季線雙下（價位 3 分）、EPS 快取 Q2 不採計 → 概估 69<70'),
 dict(stock_code='2609',stock_name='陽明',score=None,reason='動能 +500%（>100%）追高排除；超強催化覆寫不成立（中東主題方向↓ 荷莫茲恢復、貨櫃運價主題僅「中 →」、無美股龍頭 >+5%）；月季線雙下'),
 dict(stock_code='2610',stock_name='華航',score=None,reason='真連買 10 天、外資5日 +74K、EPS +5；但 L1（減速 -42.4%）篩選③不過，且催化方向矛盾同長榮航'),
 dict(stock_code='2891',stock_name='中信金',score=None,reason='今日 +10,786 張（投信 +10,266）；但外資近5日 -677（篩選②不過）、營收連 3 月衰退（-5）、動能 +88.8%（-10）、5日 +5.2%（-10）'),
 dict(stock_code='5880',stock_name='合庫金',score=58,reason='L0、真連買 5 天；營收連 3 月衰退（-5）、房市信貸鏈標↓、動能 +3% 無加分 → 約 58'),
 dict(stock_code='9904',stock_name='寶成',score=55,reason='L0、外資5日 +31K；但 avg_rank 45.5、僅資金輪動「中」催化、產業定位邊緣 → 約 55')]
sv(tp,t); print('ok')
