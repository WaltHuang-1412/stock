import json, re
T = '2026-09-30'
H = json.load(open(f'data/{T}/_holdings_src.json', encoding='utf-8'))
EXITS = ['4904', '2892', '2454', '2609', '6196']
PENDING = ['2886', '3702']


def rec(code, name, industry, price, target, score, position, reason, detail, pct=-10, rating='⭐⭐⭐⭐'):
    return dict(stock_code=code, stock_name=name, industry=industry, recommend_date=T, recommend_price=price,
                target_price=target, stop_loss_pct=pct, stop_loss=round(price * (1 + pct / 100), 2),
                settlement_days=10, position=position, score=score, rating=rating, result='holding', track='A',
                score_detail=detail, reason=reason)


recs = [
    rec('1303', '南亞', '塑化 tier_0（industry_chains；另登錄 中東地緣政治 tier_from_tracker）', 247.0, 267.0, 81,
        '5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
        '🛤️軌道A｜🔴超強催化『中東地緣政治（含航運）』影響鏈直接點名「台塑化(6505)↑／南亞(1303)↑／台化(1326)↑ 外資調升目標價」（瑞銀目標價 300 元）；⚪觀察『塑化股逆勢走強：台塑集團電子材料布局』同點名｜09-29 T86 +33,821 張（外資 +30,203／投信 +1,825 同步）、TOP50 avg_rank 1.0、佔成交 43.5%；當日市場三大法人合計賣超 -781.9 億下逆勢列買超第 1｜10 日累計 +5,879、買4賣6、真連買 2 天、近5天外資 +17K｜🔥超強催化覆寫（動能 +241.9%）→ 倉位 5-10%｜⚠️過量買超（單日 ≥30K＋真連買 2 天）-5｜⚠️10 日賣超 6 天 -5｜EPS Q2 YoY +748% +5｜營收 2026-08 YoY +46.7%（回檔不足不加分）｜持股比 +0.20%（09-24）不調整｜vs MA20 +5.59% 月季雙線上｜模式：塑化 tier_0 hot 87.5%（僅標註）｜⚠️風險：WTI -3.62%、Brent -3.64%，Topic Tracker 註記「油價回落使短線追價力道降溫」',
        '五維度 86＝時事 21（🔴中東地緣政治影響鏈直接點名↑；方向→非加速、無美股龍頭加分）＋法人 25（avg_rank 1.0 → 23、佔成交 43.5% +2、外資＋投信同步 +1，封頂 25）＋產業 17（塑化 tier_0）＋技術 10（L0、真連買 2 天、正常型態）＋價位 13（vs MA20 +5.59% 12＋雙線上 +1）｜動能 +241.9% 🔥超強催化覆寫 0｜過量買超 -5｜10 日賣超 6 天 -5｜EPS +5｜營收 0｜持股比 0｜龍頭預警 0（Micron +1.05% 今日無預警）',
        rating='⭐⭐⭐⭐'),
    rec('2376', '技嘉', 'AI 伺服器（industry_chains「AI伺服器」tier_from_tracker → 產業邏輯以 13-16 分計）', 362.0, 391.0, 78,
        '5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
        '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』（MI 產業鏈 L2 一線整機「技嘉：DGX/HGX 伺服器」；🔴影響鏈未直接點名 → 時事取下緣）；⚪觀察『AI Factory電力架構』點名技嘉(2376)↑（10/12 OCP 展 AI 機櫃、看好下半年優於上半年）｜09-29 T86 +1,947 張（外資 +1,778）、avg_rank 21.5、佔成交 28.4%；當日市場合計賣超 -781.9 億下仍列買超名單｜10 日累計 +3,564、買7賣3、真連買 1 天、近5天外資 +3,684｜🔥超強催化覆寫（動能 +500%）→ 倉位 5-10%｜EPS Q2 YoY +117% +5｜營收 2026-08 YoY +98.4%（回檔不足不加分）｜持股比 +0.26%（09-24）不調整｜vs MA20 +1.51% 月季雙線上（在 TOP50 買超名單內，法人現身門檻通過）｜模式：AI伺服器/tier_from_tracker hot 83.3%（僅標註）｜⚠️矛盾回應：🟢『AI放空潮』點名廣達、緯穎遭放空、Super Micro -1.82%／Dell -0.71%，同族群 6669 緯穎／2356 英業達今日 L4；技嘉自身 L0 且外資近 5 天為正，故列入但倉位壓在 5-10%',
        '五維度 73＝時事 20（🔴AI 伺服器與半導體，影響鏈未直接點名 → 下緣；NVDA -0.72% 無加分）＋法人 18（avg_rank 21.5 → 16、佔成交 28.4% +2；投信 +2 張不計同步）＋產業 14（tier_from_tracker）＋技術 10（L0、真連買 1 天、正常型態）＋價位 11（vs MA20 +1.51% 10＋雙線上 +1）｜動能 +500% 🔥超強催化覆寫 0｜EPS +5｜營收 0｜持股比 0｜10 日買 7 賣 3',
        rating='⭐⭐⭐'),
]
recs_sorted = sorted(recs, key=lambda r: -r['score'])

settle = open(f'data/{T}/_settlement.txt', encoding='utf-8').read()
dmap = {m.group(1): m.group(2) for m in re.finditer(r'  (\d{4}) \S+ \[A\] 推薦日 \S+ \| 現價 [\d.]+ \([^)]*\) \| (D\d+/10)', settle)}
carry = []
for h in H:
    if h['stock_code'] in EXITS:
        continue
    x = dict(h); x.pop('source_file', None)
    x['holding_days'] = dmap.get(h['stock_code'], '⏸️ 凍結')
    x['result'] = 'holding'
    if h['stock_code'] in PENDING:
        x['status'] = '⚠️ 待複核（v8.3.3）'
    carry.append(x)

sl = [('6770', '力積電', 72.3, 73.26, '🛑 低於停損', '09-21 已依鐵律①出場（入帳 72.70），yaml 未更新之重複輸出 → 不重複出場'),
      ('2337', '旺宏', 118.5, 147.6, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('2313', '華通', 226.0, 235.98, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('3090', '日電貿', 161.0, 256.5, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('1301', '台塑', 64.6, 54.08, '✅ 未觸發', '09-22 已依 L4 出場（入帳 64.60）'),
      ('4938', '和碩', 90.8, 76.5, '✅ 未觸發', '09-21 已依 L4 出場（入帳 90.80）'),
      ('2330', '台積電', 2475.0, None, '➖ 不適用', '零股 0.15 張、yaml 無 stop_loss；09-23 已依 L4 出場（入帳 2,500）')]

Hd = {h['stock_code']: h for h in H}
ex_info = {'4904': ('-454 張＝9.3%', '+4,509'), '2892': ('-3,085 張＝13.2%', '+56K'), '2454': ('-4,812 張＝57.0%', '+6,238'),
           '2609': ('-6,231 張＝24.9%', '+34K'), '6196': ('-346 張＝23.5%', '+1,306')}
exits = [dict(stock_code=c, stock_name=Hd[c]['stock_name'], category='已決事項（鐵律③ L4，09-29 盤後定案）',
              recommend_date=Hd[c]['recommend_date'], recommend_price=Hd[c]['recommend_price'],
              reason=f"09-29 T86 賣超 {ex_info[c][0]}（≥8%）；10 日累計 {ex_info[c][1]} 但佔比 ≥8% 不受 v8.3.3 保護；今日盤前複掃佔比數值相同、仍為 L4；入帳價用 09-30 收盤（v8.3.2）",
              decided_on='2026-09-29 盤後', executed='今日開盤出場（v8.3.7 Step 4-0 原樣抄入，不重評）') for c in EXITS]

pending = [
    dict(stock_code='2886', stock_name='兆豐金', recommend_date='2026-09-23', recommend_price=50.5, t86_date='2026-09-29', t86_total=-1613,
         sell_ratio_pct_premarket=7.4, ten_day_cum='+23K', review_1='09-30 12:30', review_2='09-30 盤後',
         rule='v8.3.3：佔比 <8% 且 10 日累計為正 → 待複核不出場；兩次複核皆 ≥5% 才於 10-01 開盤出場；任一次降級則維持追蹤'),
    dict(stock_code='3702', stock_name='大聯大', recommend_date='2026-09-29', recommend_price=117.5, t86_date='2026-09-29', t86_total=-572,
         sell_ratio_pct_premarket=5.8, ten_day_cum='+12K', review_1='09-30 12:30', review_2='09-30 盤後',
         rule='v8.3.3：佔比 <8% 且 10 日累計為正 → 待複核不出場；兩次複核皆 ≥5% 才於 10-01 開盤出場；任一次降級則維持追蹤')]

t = dict(
    date=T, settings=dict(stop_loss_pct=-10, settlement_days=10),
    market_context=dict(regime='多頭', score=3, vix=16.04, sox=1.32, nasdaq=-0.09, sp500=-0.17, dow=-0.26, mu=1.05, amd=-0.05, intc=-0.09,
                        amat=5.19, asml=3.56, klac=3.89, lrcx=2.99, mrvl=4.51, avgo=1.58, meta=3.24, aapl=-2.66, nvda=-0.72,
                        tsm_adr=0.90, umc_adr=3.65, ase_adr=3.47, wti=-3.62, gold=1.15, us10y=5.29, us30y=5.62,
                        taiex_prev_close=47631.96, taiex_prev_change_pct=-0.82, taiex_vs_ma20=1.73, taiex_vs_ma240=29.3,
                        institutional_total_0929='-781.9 億（外資 -632.0 億、投信 +14.2 億、自營商 -164.0 億）',
                        note='TAIEX 09-29 收盤 47,631.96：Yahoo ^TWII 09-29 日K close=None，fix_market_regime_taiex.py 原輸出停在 09-24 的 48,024.6；今日已修腳本改以 meta.regularMarketPrice 補值（與 MI／Topic Tracker 的 47,631.96 一致）'),
    prior_decisions_executed=dict(source='tracking_2026-09-29.json', tomorrow_opening_exits=EXITS,
                                  status='5 筆全數原樣抄入今日開盤出場清單頂部，未重評；今日複掃結果與定案一致（無衝突）',
                                  holdings_yaml_decisions='0 筆（09-29 無 my_holdings.yaml 持倉出場決議）'),
    stop_loss_check_v8310=[dict(symbol=a, name=b, date='2026-09-29', close=c, stop_loss=d, result=e, note=f) for a, b, c, d, e, f in sl],
    stop_loss_check_conclusion='0 筆新觸發；4 檔觸發者皆為已出場部位因 my_holdings.yaml 未更新之重複輸出',
    series_alignment_check_v838=dict(aligned=10, frozen=['2867 三商壽（末日 2026-08-19）'], note='11 筆 holding 中 10 筆末日＝2026-09-29（前一交易日）；2867 由腳本輸出 stale_series 凍結'),
    two_day_drawdown_check=dict(triggered=[], worst='2454 聯發科 -5.30%（5185→4910）', note='門檻 -10%，0 筆觸發'),
    opening_exits_today=exits,
    pending_review_v833=pending,
    holdings_reversal_scan=dict(scanned=11, L4=['4904 遠傳 9.3%', '2892 第一金 13.2%', '2454 聯發科 57.0%', '2886 兆豐金 7.4%（待複核）', '2609 陽明 24.9%', '3702 大聯大 5.8%（待複核）', '6196 帆宣 23.5%'],
                                L2=['2412 中華電（-174 張＝1.5%）'], L0=['5876 上海商銀', '2395 研華'], unknown=['2867 三商壽（無數據，凍結）']),
    settlement_today=[],
    recommendations=recs_sorted,
    carry_over=[c['stock_code'] for c in carry],
    carry_over_recommendations=carry,
    carry_over_note='6 筆 holding（含 2867 凍結、2886／3702 待複核）D 值照抄 settlement_checker 輸出；進場價／停損取自來源 tracking_{推薦日}.json；另 5 筆列開盤出場（已決事項）',
    disposition_stocks=dict(
        twse_official=['2305 全友｜09/18~09/30｜第一次處置', '2455 全新｜09/23~10/05｜第二次處置', '2468 華經｜09/22~10/02｜第一次處置',
                       '3443 創意｜09/29~10/05｜第一次處置（連續三次）', '6168 宏齊｜09/24~10/02｜第一次處置',
                       '6226 光鼎｜09/21~10/01｜第二次處置', '6526 達發｜09/30~10/06｜第一次處置（連續三次）★今日新增',
                       '6715 嘉基｜09/23~10/01｜第一次處置', '8021 尖點｜09/23~10/01｜第二次處置'],
        tpex_official=['7792 安葆｜09/30~10/06｜連續3日達注意 ★今日新增', '3374 精材｜09/29~10/05｜30日內曾處置又10日內6日達注意',
                       '4542 科嶠｜09/29~10/05｜連續3日達注意', '4979 華星光｜09/29~10/05｜30日內曾處置又連續5日達注意',
                       '2221 大甲｜09/24~10/06｜連續3日達注意及沖銷標準', '7772 耀穎｜09/24~10/02｜30日內曾處置又達標',
                       '6218 豪勉｜09/23~10/05｜連續3日達注意及沖銷標準', '6945 圓祥生技｜09/23~10/01｜連續3日達注意',
                       '5314 世紀*｜09/22~09/30｜連續3日達注意', '3441 聯一光｜09/18~09/30｜連續5日及沖銷標準'],
        twse_attention=[],
        countdown=['6456 GIS-KY｜連續達標 3 天｜最快今日處置（剩 0 天）', '3016 嘉晶｜連續達標 4 天｜最快明日處置',
                   '2484 希華｜連續達標 1 天｜最快剩 2 天處置',
                   '2426 鼎元／3717 聯嘉投控／6133 金橋／3518 柏騰／3037 欣興｜接近注意門檻'],
        pool_hits=['3374 精材（TPEx 處置股，軌道B 設備鏈候選）→ 機械式排除']),
    module_a_result=dict(L3=[], L2=['2892 第一金', '6770 力積電', '2412 中華電', '3045 台灣大', '2609 陽明', '1718 中纖', '2886 兆豐金', '2891 中信金',
                                    '1312 國喬', '2353 宏碁', '2615 萬海', '2399 映泰', '2027 大成鋼'],
                         L1=['2408 南亞科', '2883 凱基金', '9904 寶成', '2890 永豐金'],
                         note='L2 13 檔中 7 檔今日 L4（2892/2609/2886/1312/2353/2615/2027）、2412 為 L2；其餘未過準確率篩選或法人現身門檻 → 0 檔以訊號A 進入推薦'),
    module_b_result=dict(preposition=32, institution_in=16, rallied_excluded=33, passed=[], final=[],
                         excluded=['6669 緯穎 L4＋累計負', '2356 英業達 L4＋累計負', '3017 奇鋐 L4＋累計負', '3324 雙鴻 數據不足（上櫃）', '6230 尼得科超眾 L4',
                                   '2368 金像電 L3＋累計負', '2367 燿華 動能+500%', '3234 光環 數據不足（上櫃）', '4977 眾達-KY L3＋累計負', '2392 正崴 L4＋累計負']),
    us_leader_alerts=dict(total=1, L1=['Apple -2.66%（3008 大立光／2474 可成／2317 鴻海／4938 和碩／3673 TPK-KY／2353 宏碁／6415 矽力-KY）'],
                          note='L3 0、L2 0；推薦 2 檔皆不在受影響名單'),
    diversification=dict(ranked=2, new_recommendations=2, industries=['塑化 1', 'AI 伺服器 1'], max_single_industry_pct=50.0,
                         note='6505 台塑化 78 分通過全部門檻，但與 1303 南亞同屬塑化；列入將使塑化 2/3＝67% >50% → 依分數取 1303，6505 列第一遞補。寧缺勿濫，未湊數'),
    defense_ratio=dict(vix=16.04, suggested='0-15%', actual='新推薦 2 檔皆進攻型，倉位各 5-10%（🔥超強催化覆寫上限）；防禦型僅⏳沿用之金融／電信'),
    watchlist=['6505 台塑化（78 分；🔴中東影響鏈直接點名↑、09-29 T86 +16,559 張外資＋投信同步、真連買 3 天；5 日 +9.0% -10；因單一產業 ≤50% 未列入，第一遞補）',
               '1718 中纖（75 分；📶訊號A L2、動能 -26.1%、近5天外資 +7,126；但當日時事資料提及 0 處 → ①催化對齊未過；塑化 tier_2 化學纖維 cold 33.3% -3）',
               '2881 富邦金（57 分；L0、近5天外資 +7,710；動能 +56.3% -10、營收連續衰退 6 個月 -5、EPS 快取停於 2025-12-31 未採計）',
               '2395 研華（沿用中 D7/10；L0、真連買 5 天；🟢邊緣AI 中度 → ①催化對齊未過，不重列排名）',
               '3045 台灣大（L0、近5天外資 +8,768；不在 TOP50 買超 × 月線乖離 +0.37% → 法人現身門檻未過）'],
    tier_from_tracker_added=0,
    tier_from_tracker_note='本流程未寫入；industry_chains.json 工作區既有未提交變更（+903 行、新增 87 筆 tier_from_tracker，來源為「催化劑追蹤（自動同步）」），本日一併提交並揭露',
    pattern_tracker=dict(date='2026-09-30', applied=[], note='最終推薦 2 檔皆非 cold pattern（塑化 tier_0 hot 87.5%、AI伺服器/tier_from_tracker hot 83.3%，僅標註不加分）'),
    script_fixes=['scripts/fix_market_regime_taiex.py：Yahoo 最新日K close=None 時改以 meta.regularMarketPrice 補值（09-29 實收 47,631.96；修正前輸出 09-24 的 48,024.6）'],
    removed_stocks=[], tomorrow_opening_exits=[], track_b_recommendations=[], track_b_observations=[])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for r in recs_sorted:
    print(r['stock_code'], r['score'], r['recommend_date'], r['recommend_price'], r['stop_loss'])
print({c['stock_code']: c['holding_days'] for c in carry})
