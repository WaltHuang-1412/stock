import json
T = '2026-10-16'


def rec(code, name, ind, price, score, pos, reason):
    return dict(stock_code=code, stock_name=name, industry=ind, recommend_date=T, recommend_price=price,
                target_price=round(price * 1.08, 2), stop_loss_pct=-10, stop_loss=round(price * 0.9, 2),
                settlement_days=10, position=pos, score=score, result="holding", reason=reason)


recs = [
    rec('6209', '今國光', '光電／LED 封裝（industry_chains 查無，未分類）', 93.0, 91, '5%',
        '🛤️軌道A 法人TOP50 #12（avg_rank 12）；📶訊號A L2（3天在TOP50、動能-23.2%、5日+2.3%，+10）；10-15 三大法人+12,250張（外資+11K）、10日累計+17K、近5天外資+7.3K；反轉L0；營收YoY+81.6%、外資持股比週增+0.51%（+5）；月線+10.9%且在TOP50（過法人現身門檻）。⚠️風險：真連買僅1天（10-14 曾 -5,478）；時事資料源 mentions=0（僅法人數據支撐）；週轉率23%、6日+6.5%/30日+17.0% 🟡接近注意門檻（非官方處置/注意股），被列注意後流動性風險；倉位依 80-89 分應 10-15%，因上述風險與大盤 -3.41% 降為 5%'),
    rec('2882', '國泰金', '金融（金控）', 113.5, 87, '5%',
        '🛤️軌道A 法人TOP50 #34（avg_rank 34）；📶訊號A L2（4天在TOP50、動能-17.6%、5日+0.4%，+10）；10-15 三大法人+2,543張、10日累計+25K、近5天外資+4.5K；反轉L0；EPS YoY+294%（+5）；月線+1.4%且在TOP50（過法人現身門檻）；時事：壽險與金融業獲利創高🟢（國泰金↑）。⚠️風險：營收YoY-41.2%連3月衰退（-5）；Fed/長債主題標「國泰金↓長債未實現損失」、台灣央行預防性升息討論，催化對齊僅部分；單日買超僅+2,543張（量小）；與沿用 2886/2892 同為金融，組合層金融集中；大盤 -3.41%'),
]


def co(code, name, rd, rp, tp, sl, d, last, src, status):
    return dict(stock_code=code, stock_name=name, recommend_date=rd, recommend_price=rp, target_price=tp,
                stop_loss_pct=-10, stop_loss=sl, settlement_days=10, holding_days_label=d, last_close=last,
                source=src, status=status)


carry = [
    co('8046', '南電', '2026-10-12', 1475.0, 1593.0, 1327.5, 'D3/10', 1345.0, 'tracking_2026-10-12.json',
       '🛑 L4 開盤出場：10-15 T86 -627張佔5日均量9.1%（≥8%不受待複核保護；10日累計仍正）；收1345距停損1.3%'),
    co('3189', '景碩', '2026-10-12', 1075.0, 1161.0, 967.5, 'D3/10', 979.0, 'tracking_2026-10-12.json',
       '🛑 L4 開盤出場：10-15 T86 -1,948張佔19.5%；收979距停損1.2%'),
    co('3576', '聯合再生', '2026-10-15', 18.65, 20.14, 16.79, 'D0/10', 17.95, 'tracking_2026-10-15.json',
       '🛑 L4 開盤出場：10-15 T86 -4,511張佔53.6%（昨日推薦、前一日+5,162張買超一日反轉）'),
    co('2323', '中環', '2026-10-15', 11.9, 12.85, 10.71, 'D0/10', 11.8, 'tracking_2026-10-15.json',
       '🛑 L4 開盤出場：10-15 T86 -998張佔11.6%（≥8%）；前一日+10,984張一日反轉'),
    co('2002', '中鋼', '2026-10-13', 19.2, 20.74, 17.28, 'D2/10', 19.25, 'tracking_2026-10-13.json',
       '⏳沿用；L0；10-15 +3,359張、10日累計+105K'),
    co('2886', '兆豐金', '2026-10-13', 50.0, 54.0, 45.0, 'D2/10', 52.5, 'tracking_2026-10-13.json',
       '⏳沿用；L0；10-15 +33,794張（單日≥30K、連買7天故不扣）；TOP50 #2；距目標2.9%'),
    co('2892', '第一金', '2026-10-13', 39.7, 42.88, 35.73, 'D2/10', 41.6, 'tracking_2026-10-13.json',
       '⏳沿用；L0；10-15 +13,788張；今日重大訊息：紐約分行轉讓聯貸案債權≤USD13.7佰萬（金額小，中性）'),
    co('2867', '三商壽', '2026-08-17', 9.75, 10.73, 8.78, '凍結', 9.7, 'tracking_2026-08-17.json',
       '⚠️序列停滯（末日2026-08-19）凍結判定；併購停止買賣待公告人工結案'),
]


def ex(c, n, cat, r, decided=True):
    return dict(stock_code=c, stock_name=n, category=cat, reason=r, decided=decided)


exits = [
    ex('6770', '力積電', '持倉 my_holdings.yaml（已決 L4＋鐵律①）', '10-15收66.2<停損73.26；10-15 T86 -95,839張佔89.5%；yaml未更新'),
    ex('2337', '旺宏', '持倉 my_holdings.yaml（已決，鐵律①）', '10-15收104.5<停損147.6；10-15 T86 -1,073張、10日累計-41,604張'),
    ex('3090', '日電貿', '持倉 my_holdings.yaml（已決，鐵律①）', '10-15收171.5<停損256.5；10-15 T86 -9,147張佔103.5%、週轉12.8%接近注意'),
    ex('1301', '台塑', '持倉 my_holdings.yaml（10-13 已決 L4）', '已決不重評；10-15 T86 -50,002張佔29.3%（與決議同向）；收81.7、損益約+36%超yaml停利20%'),
    ex('2313', '華通', '持倉 my_holdings.yaml（已決 L4＋鐵律①）', '已決不重評；10-15收228.0<停損235.98（10-14收250.5未觸）；T86 -9,513張佔26.9%'),
    ex('4938', '和碩', '持倉 my_holdings.yaml（已決 L4）', '已決不重評；揭露：10-15 T86 -216張L0、10日累計+29,727張；收98.1'),
    ex('2330', '台積電', '持倉 my_holdings.yaml 零股0.15張（已決）', '已決不重評；10-15 T86 -23,461張佔103.7%；收2,440；yaml無stop_loss'),
]
exits_new = [
    ex('8046', '南電', '追蹤部位（今日新判 L4）', '10-15 T86 -627張佔9.1%（≥8%，不受待複核保護）', False),
    ex('3189', '景碩', '追蹤部位（今日新判 L4）', '10-15 T86 -1,948張佔19.5%', False),
    ex('3576', '聯合再生', '追蹤部位（今日新判 L4，D0）', '10-15 T86 -4,511張佔53.6%', False),
    ex('2323', '中環', '追蹤部位（今日新判 L4，D0）', '10-15 T86 -998張佔11.6%', False),
]
sl = [('2330', '台積電', 2440.0, None), ('6770', '力積電', 66.2, 73.26), ('2337', '旺宏', 104.5, 147.6),
      ('2313', '華通', 228.0, 235.98), ('3090', '日電貿', 171.5, 256.5), ('1301', '台塑', 81.7, 54.08),
      ('4938', '和碩', 98.1, 76.5)]
rows = [dict(symbol=c, name=n, close=p, stop_loss=s, hit=(s is not None and p < s)) for c, n, p, s in sl]

t = dict(
    date=T, version='v8.3.11', phase='before_market', settings=dict(stop_loss_pct=-10, settlement_days=10),
    market_context=dict(
        taiex_prev_close=46969.87, taiex_as_of='2026-10-15', taiex_chg_pct=-3.41,
        regime='MI標「多頭(score 3)」；校正後 TAIEX 收46,969.87，月線-2.23%（跌破）、季線+2.3%', vix=16.46,
        us={'NASDAQ': 0.08, 'S&P500': 0.33, 'DOW': 1.08, 'SOX': -0.88, 'TSM_ADR': -1.80, 'MU': 1.87, 'DELL': -6.80,
            'ANET': -5.04, 'CSCO': -3.34, 'INTC': -2.80, 'AMAT': -3.72, 'LRCX': -3.30, 'WTI': 1.14},
        asia={'Nikkei': -4.90, 'KOSPI': -7.57},
        note='10-15 外資現貨-3,025.6億史上最大賣超連賣7日、期貨空單開97,582口；投信+283億、0050單日申購378億；台指期夜盤+435點；費半連7黑；AI泡沫檢查清單【惡化】；10-20 鴻海法說'),
    prior_decisions_executed=dict(source='tracking_2026-10-15.json tomorrow_opening_exits',
                                  items=[e['stock_code'] + ' ' + e['stock_name'] for e in exits]),
    opening_exits_today=exits + exits_new,
    stop_loss_check_v8310=dict(data_day='2026-10-15', rows=rows),
    recommendations=recs,
    carry_over=['8046', '3189', '3576', '2323', '2002', '2886', '2892', '2867'],
    carry_over_recommendations=carry,
    module_a_result=dict(L3=[], L2=['2883 凱基金', '2882 國泰金', '6209 今國光'], L1=['3702 大聯大', '2377 微星'],
                         integration='2882/6209 +10；2883 因單一產業≤50%未入選；L3=0'),
    module_b_result=dict(early=[], note='預先佈局 0 檔／法人已進場 0 檔／已大漲排除 0 檔'),
    defense_ratio=dict(vix=16.46, catalyst='超強（紅區）但 AI 鏈重挫、金融逆勢', defense_pct='0-15%',
                       note='實際新推薦 2 檔偏防禦（金融／低動能），與規定比例有落差，已揭露'),
    pattern_tracker='pattern_today.json 日期 2026-10-05 超過 3 天 → 跳過不扣分',
    tier_from_tracker_added='本次新增 0 筆',
    removed_stocks=[],
    disposition_stocks=dict(twse_disposition=17, note='候選池與持倉皆無官方處置/注意股；6209 今國光、6456 GIS-KY 為自算「接近注意門檻」（非官方）；3090 日電貿週轉12.8%接近'),
    track_b_recommendations=[],
    tomorrow_pending_review=[],
    data_quality=[
        'TOP50 取自 20261015（10-15 T86 已公布，結束 n=14 缺資料）；反轉掃描為 10-15 T86 新鮮值（持倉買賣超方向與昨日不同，確認非前日回退）',
        'market_regime TAIEX 經 fix_market_regime_taiex 校正：MI 48,625.83→Yahoo 46,969.87（資料日 2026-10-15）；原月線乖離符號反向',
        '營收 44/44 檔皆 2026-09；EPS 快取 Q2（Q3 申報期限 11/14 未到）；外資持股比 ≥2026-10-09',
        'topic_tracker／market_regime／industry_signals 遠端 gh api 回 0 bytes（未產出），改用本機 market-intelligence/outputs（07:38 版）',
        '龍頭對應表缺口：Dell -6.80%、Arista -5.04%、Cisco -3.34%、Intel -2.80% 無預警；候選池無 AI 伺服器／網通個股故未改分；微星/宏碁以 Intel L1 手動 -5',
        'preflight 2 項 ERROR：必要輸入檔缺失為後續步驟產出（已補齊）；daily.sh git add 為已知字面誤報',
        '2867 三商壽序列停滯（末日 08-19），凍結'])
json.dump(t, open('data/tracking/tracking_2026-10-16.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
