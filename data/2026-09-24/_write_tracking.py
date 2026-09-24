import json, re
T = '2026-09-24'
H = json.load(open(f'data/{T}/_holdings_src.json', encoding='utf-8'))
Hd = {h['stock_code']: h for h in H}
EXITS = ['2891', '2382', '2377', '5880', '3481', '3023']


def rec(code, name, industry, price, target, score, position, reason, detail, pct=-10, rating='⭐⭐⭐⭐'):
    return dict(stock_code=code, stock_name=name, industry=industry, recommend_date=T, recommend_price=price,
                target_price=target, stop_loss_pct=pct, stop_loss=round(price * (1 + pct / 100), 2),
                settlement_days=10, position=position, score=score, rating=rating, result='holding', track='A',
                score_detail=detail, reason=reason)


HOLIDAY = '⚠️ 09-25 中秋節、09-28 教師節休市，下一交易日 09-29：持有跨 4 天連假（川習會結果、美國 PCE／殖利率走勢在休市期間發生）'

recs = [
    rec('6770', '力積電', '記憶體／DRAM 代工（industry_chains 記憶體 tier_from_tracker「DRAM 與記憶體」→ 產業邏輯以 13-16 分計）', 73.1, 79.0, 84,
        '5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
        '🛤️軌道A｜🔴超強催化『DRAM與記憶體』↑（多空分歧加劇）→ 🔥超強催化覆寫（動能 +492% 不排除；5日 +4.6% <20%、反轉 L0）｜09-23 T86 +25,105 張（TOP50 張數 #3、avg_rank 5.5、佔成交 21.3%）｜10 日累計 +101K、買7賣3、真連買 2 天、近5天三大法人 +136K／外資 +119K｜反轉 ✅法人買超中｜topic_tracker 🟡『台股市場動態』點名「力積電(6770)↑ 外資買超」｜Q2 EPS +5、外資持股比週增 +1.61% +5｜⚡MU 10/01 財報（B類，佈局窗口開啟）產業 +1｜⚠️ 龍頭預警 L1（Micron -2.22%）-5｜⚠️ 籌碼單日方向劇烈翻轉（09-15 -75K、09-18 +89K、09-21 -24K）｜⚠️ 使用者 my_holdings 部位 09-21 已依鐵律①出場，本推薦為新追蹤、非回補建議｜' + HOLIDAY,
        '五維度小計 79 ＝ 時事 20（🔴DRAM 基礎 20；本股未列 DRAM 影響鏈，取下緣；MU -2.35% 無加分）＋法人 24（avg_rank 5.5 → TOP10 基礎 22＋佔成交 21.3% >20% +2；外資+24K／投信 -11 不同步 0；真連買 2 天 0）＋產業 15（tier_from_tracker 14＋MU B類財報窗口 +1）＋技術 9（L0 正常型態；動能爆發非佈局型）＋價位 11（vs MA20 +2.79% 10＋月季雙線上 +1）｜modifiers：動能 +492% 🔥超強催化覆寫 0｜5日 +4.6% 0｜EPS Q2 +5｜外資持股比 +5（as_of 09-18）｜營收 +76.2% 未回檔 0｜龍頭預警 L1 -5｜買賣天數 3 賣 0｜模式追蹤器「記憶體/半導體代工」45.5% 非 cold 0',
        rating='⭐⭐⭐⭐'),
    rec('2408', '南亞科', '記憶體 DRAM（industry_chains 記憶體 tier_0 DRAM）', 515.0, 555.0, 83,
        '5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
        '🛤️軌道A｜🔴超強催化『DRAM與記憶體』影響鏈直接點名「南亞科(2408)↑ 8月營收YoY+719.6%」→ 🔥超強催化覆寫（動能 +235.5%；5日 +4.6% <20%、反轉 L0）｜09-23 T86 +29,607 張（外資 +29K／投信 -180）、avg_rank 2.0、佔成交 48.9%｜近5天三大法人 +39K／外資 +35K；10 日累計 +10K、買4賣6、真連買 1 天｜Q2 EPS +5、外資持股比週增 +1.04% +5｜⚡MU 10/01 財報（B類窗口開啟）產業 +1｜⚠️ 龍頭預警 L1（Micron -2.22%）-5｜⚠️ 09-22 T86 才賣超 -24K（當日 L4 53.3%），隔日翻買 +29K：籌碼單日翻轉，非連續佈局｜⚠️ 卷宗矛盾：topic_tracker 記「大賣空貝瑞加碼放空美光，以記憶體不缺為論據」vs 小摩「2026~2028 需求 CAGR 63%」—多空分歧，已反映在技術面只給 9 分｜' + HOLIDAY,
        '五維度小計 81 ＝ 時事 22（🔴DRAM 且影響鏈點名↑ 基礎 22）＋法人 20（avg_rank 2.0 → TOP10 基礎 23＋佔成交 48.9% +2＝25，10 日賣超 6 天 -5）＋產業 19（tier_0 DRAM 18＋MU B類財報窗口 +1）＋技術 9（L0；10 日 +37K／-24K 大幅震盪）＋價位 11（vs MA20 +1.13% 10＋雙線上 +1）｜modifiers：動能 +235.5% 🔥覆寫 0｜EPS Q2 +5｜外資持股比 +5（as_of 09-18）｜營收 +560.9% 未回檔 0｜龍頭預警 L1 -5｜模式追蹤器「記憶體 tier_0（DRAM）」38.5%/13 筆（未列 cold_patterns，保守比照 31-40% 級）-3',
        rating='⭐⭐⭐⭐'),
    rec('2317', '鴻海', 'AI 伺服器（industry_chains AI tier_1 AI伺服器；蘋果供應鏈 tier_0 iPhone組裝）', 256.0, 276.0, 79,
        '5-10%（🔥超強催化覆寫，倉位上限 5-10%）',
        '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』影響鏈點名「鴻海(2317)↑ AI伺服器需求」→ 🔥超強催化覆寫（動能 +220%；5日 +3.2%、反轉 L0）｜09-23 T86 +7,773 張（外資 +5,860／投信 +967 同步）、avg_rank 7.5、佔成交 22.4%｜近5天外資 +9,149／三大法人 +13K；10 日累計 +2,341、買4賣6、真連買 2 天｜Q2 EPS +3｜⚠️ 09/30 康和證券投資人會議（持有期內第 2 個交易日）｜⚠️ Google -3.80%（MI 列鴻海為 Google AI 代理供應鏈）未納入龍頭對應表，無機械扣分，人工揭露｜' + HOLIDAY,
        '五維度小計 76 ＝ 時事 21（🔴AI 影響鏈點名↑）＋法人 19（avg_rank 7.5 → TOP10 基礎 21＋佔成交 22.4% +2＋外資投信同步 +1＝24，10 日賣超 6 天 -5）＋產業 16（AI tier_1 AI 伺服器核心組裝）＋技術 9（L0 正常型態）＋價位 11（vs MA20 +1.85% 10＋雙線上 +1）｜modifiers：動能 +220% 🔥覆寫 0｜EPS Q2 +3｜外資持股比 +0.04% 0｜營收 +52.0% 未回檔 0｜模式追蹤器 AI伺服器＋蘋果鏈 45.5% 非 cold 0',
        rating='⭐⭐⭐'),
]
for code, score, note in [
        ('2892', 101, '今日評分 101：五維度 71（時事 18〔🔴聯準會，但 🟡美債殖利率主題指「曲線趨平壓抑銀行利差」→ 取區間下修〕＋法人 12〔avg_rank 38.5 → 10＋佔成交 10.7% +1＋真連買 6 天 +1〕＋產業 14〔tier_from_tracker〕＋技術 14〔L0＋動能<-30%＋連買 6 天〕＋價位 13〔+5.06%〕）＋動能 -41.8% +15＋📶訊號A L3 +15；EPS 快取停於 2025-12-31 → 0；09-23 T86 +1,867 張'),
        ('2609', 99, '今日評分 99：五維度 74（時事 21〔🔴中東航運，影響鏈點名陽明↑，美西 8,300／美東 1.25 萬美元〕＋法人 16〔avg_rank 27.0 → 14＋佔成交 11.8% +1＋外資投信同步 +1〕＋產業 14〔tier_from_tracker〕＋技術 12〔L0＋動能<0＋真連買 3 天〕＋價位 11）＋動能 -8.8% +10＋📶訊號A L2 +10＋EPS Q2 +5；09-23 T86 +3,244 張'),
        ('2886', 99, '今日評分 99：五維度 69（時事 18〔同 2892 下修〕＋法人 13〔avg_rank 34.5 → 13；外資 +4,641／投信 -3,276 不同步〕＋產業 17〔金融 tier_0 金控〕＋技術 13〔L0＋動能<-30%＋連買 3 天〕＋價位 8〔vs MA20 -0.28%〕）＋動能 -32.6% +15＋📶訊號A L3 +15；EPS 快取停於 2025-12-31 → 0'),
        ('8046', 82, '今日評分 82：五維度 82（時事 21〔🔴AI＋🟡ABF↑加速 +1〕＋法人 22〔avg_rank 10.5 → 19＋佔成交 22.3% +2＋外資投信同步 +1〕＋產業 17〔AI tier_0 晶片載板〕＋技術 9〔動能爆發〕＋價位 13〔+7.53%〕）；動能 +337.6% 🔥超強催化覆寫（🔴AI）0｜5日 +9.5% -10｜EPS +5｜外資持股比 +0.86% +5')]:
    h = dict(Hd[code]); h.pop('source_file', None)
    h.update(original_score=h['score'], score=score, score_today=score,
             position=f"⏳沿用進行中追蹤，維持原進場價 {h['recommend_price']}／停損 {h['stop_loss']} 不變，不重複建倉",
             result='holding', track='A', note=note,
             reason=f"⏳沿用進行中追蹤（原推薦日 {h['recommend_date']}）｜{note}")
    recs.append(h)
recs_sorted = sorted(recs, key=lambda r: -(r.get('score_today') or r['score']))

settle = open(f'data/{T}/_settlement.txt', encoding='utf-8').read()
dmap = {m.group(1): m.group(2) for m in re.finditer(r'  (\d{4}) \S+ \[A\] 推薦日 \S+ \| 現價 [\d.]+ \([^)]*\) \| (D\d+/10)', settle)}
carry = []
for h in H:
    if h['stock_code'] in EXITS:
        continue
    x = dict(h); x.pop('source_file', None)
    x['holding_days'] = dmap.get(h['stock_code'], '⏸️ 凍結')
    x['result'] = 'holding'
    carry.append(x)

sl = [('6770', '力積電', 73.1, 73.26, '🛑 低於停損', '09-21 已依鐵律①出場（入帳 72.70），yaml 未更新之重複輸出 → 不重複出場'),
      ('2337', '旺宏', 119.0, 147.6, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('2313', '華通', 224.0, 235.98, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('3090', '日電貿', 165.0, 256.5, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('1301', '台塑', 63.1, 54.08, '✅ 未觸發', '09-22 已依 L4 出場（入帳 64.60）'),
      ('4938', '和碩', 91.3, 76.5, '✅ 未觸發', '09-21 已依 L4 出場（入帳 90.80）'),
      ('2330', '台積電', 2500.0, None, '➖ 不適用', '零股 0.15 張、yaml 無 stop_loss；09-23 已依 L4 出場（入帳 2,500）')]

exits = [
    dict(stock_code='2891', stock_name='中信金', category='已決事項（v8.3.7）｜鐵律③ L4 待複核定案', recommend_date='2026-09-15',
         reason='tracking_2026-09-23 tomorrow_opening_exits 原樣抄入，不重評；09-22 T86 -3,329 張兩次複核 8.4% ≥5%。（參考：09-23 T86 再賣 -3,231 張＝8.2%，同屬 L4）；入帳價用 09-24 收盤（v8.3.2）'),
    dict(stock_code='3481', stock_name='群創', category='鐵律③ L4', recommend_date='2026-09-22',
         reason='09-23 T86 賣超 -57,816 張＝25.1%（>50K 張且 ≥8%），10 日累計 -64K 為負 → 不受 v8.3.3 保護'),
    dict(stock_code='2382', stock_name='廣達', category='鐵律③ L4', recommend_date='2026-09-14',
         reason='09-23 T86 賣超 -1,994 張＝13.7%（≥8%）；10 日累計 +9,551 但佔比 ≥8% 不受 v8.3.3 保護'),
    dict(stock_code='5880', stock_name='合庫金', category='鐵律③ L4', recommend_date='2026-09-17',
         reason='09-23 T86 賣超 -2,367 張＝13.3%（≥8%）；10 日累計 +34K 但佔比 ≥8% 不受保護'),
    dict(stock_code='2377', stock_name='微星', category='鐵律③ L4', recommend_date='2026-09-15',
         reason='09-23 T86 賣超 -629 張＝10.6%（≥8%）；10 日累計 +3,170 但佔比 ≥8% 不受保護'),
    dict(stock_code='3023', stock_name='信邦', category='鐵律③ L4', recommend_date='2026-09-23',
         reason='09-23 T86 賣超 -323 張＝53.9%（≥8%；本股日均量僅約 600 張，小量賣超即跨門檻）；10 日累計 +237 但佔比 ≥8% 不受保護；推薦後 D0 即觸發')]

t = dict(
    date=T, settings=dict(stop_loss_pct=-10, settlement_days=10),
    market_context=dict(regime='多頭', score=5, vix=15.18, sox=-1.21, nasdaq=-1.12, sp500=-0.75, mu=-2.22, avgo=-2.62, nvda=-1.47, wti=-2.70,
                        us10y=5.13, taiex_prev_close=48157.29,
                        note='TAIEX 09-23 收盤 48,157.29（+0.75%，取自 09-23 盤後報告／topic_tracker）；Yahoo ^TWII 09-22、09-23 兩列 close=None，market_regime taiex 校正後仍為 09-21 值 47,718.84',
                        holiday='09-25 中秋節、09-28 教師節休市（TWSE holidaySchedule），下一交易日 09-29'),
    prior_decisions_executed=dict(source='tracking_2026-09-23.json', tomorrow_opening_exits=['2891 中信金'],
                                  note='Step 4-0：原樣抄入開盤出場清單頂部，未重跑等級、未重算佔比'),
    stop_loss_check_v8310=[dict(symbol=a, name=b, date='2026-09-23', close=c, stop_loss=d, result=e, note=f) for a, b, c, d, e, f in sl],
    stop_loss_check_conclusion='0 筆新觸發；4 檔觸發者皆為已出場部位因 my_holdings.yaml 未更新之重複輸出',
    series_alignment_check_v838=dict(aligned=18, frozen=['2867 三商壽（末日 2026-08-19）'], note='19 筆 holding 中 18 筆末日＝2026-09-23；抽驗 2382/3481/6770/2408 日K 時間戳皆 09:00 真實 K 棒，無幻影列'),
    two_day_drawdown_check=dict(triggered=[], worst='3023 信邦 -2.65%'),
    opening_exits_today=exits,
    pending_review_v833=[],
    holdings_reversal_scan=dict(scanned=19, L4=['2891 中信金 8.2%（已決）', '3481 群創 25.1%', '2382 廣達 13.7%', '5880 合庫金 13.3%', '2377 微星 10.6%', '3023 信邦 53.9%'],
                                L2=['2303 聯電 4.6%（前期買超 +107,660 後單日 -10,135）'], unknown=['2867 三商壽（無數據，凍結）']),
    settlement_today=[],
    recommendations=recs_sorted,
    carry_over=[c['stock_code'] for c in carry],
    carry_over_recommendations=carry,
    carry_over_note='13 筆 holding（含 2867 凍結）照抄 settlement_checker 輸出；進場價／停損取自來源 tracking_{推薦日}.json；另 6 筆列開盤出場',
    disposition_stocks=dict(
        twse_official=['2305 全友｜09/18~09/30｜第一次處置', '2455 全新｜09/23~10/05｜第二次處置', '2468 華經｜09/22~10/02｜第一次處置',
                       '6168 宏齊｜09/24~10/02｜第一次處置（連續三次）★今日新增', '6226 光鼎｜09/21~10/01｜第二次處置',
                       '6715 嘉基｜09/23~10/01｜第一次處置', '8021 尖點｜09/23~10/01｜第二次處置'],
        twse_attention=[],
        countdown=['3605 宏致｜連續達標 6 天｜最快剩 0 天處置', '8150 南茂｜連續達標 2 天｜最快剩 1 天處置', '3016 嘉晶｜連續達標 2 天｜最快剩 1 天處置',
                   '3055 蔚華科｜連續達標 2 天｜最快剩 1 天處置', '3443 創意｜連續達標 2 天｜最快剩 1 天處置', '6456 GIS-KY｜連續 1 天｜最快剩 2 天處置',
                   '2104 國際中橡／3037 欣興／2404 漢唐／3042 晶技｜接近注意門檻']),
    module_a_result=dict(L3=['2892 第一金', '2412 中華電', '2886 兆豐金', '6213 聯茂'],
                         L2=['2609 陽明', '3045 台灣大', '2891 中信金', '2884 玉山金', '2883 凱基金', '5880 合庫金', '2382 廣達', '2027 大成鋼', '2354 鴻準'],
                         L1=['2353 宏碁', '2890 永豐金', '2103 台橡']),
    module_b_result=dict(preposition=118, institution_in=28, rallied_excluded=54, passed=[], final=[],
                         excluded=['2345 智邦 L4', '3234 光環 數據不足', '4977 眾達-KY 數據不足', '4908 前鼎 數據不足', '2455 全新 累計負＋處置股',
                                   '3406 玉晶光 L3', '2383 台光電 L4', '3044 健鼎 動能+250%', '6451 訊芯-KY L4', '7928 合聖科技 數據不足']),
    us_leader_alerts=dict(total=2, L1=['Micron -2.22%（2408/1303/2344/2337/5347/6770）', 'Broadcom -2.62%（2345/2412/3042/2449）'],
                          note='Google -3.80%、Amazon -2.24% 無台股對應，不觸發'),
    diversification=dict(ranked=7, new_recommendations=3, industries=['金融 2（⏳）', '航運 1（⏳）', '記憶體 2', 'AI 載板 1（⏳）', 'AI 伺服器 1'],
                         max_single_industry_pct=28.6, passed=True),
    defense_ratio=dict(vix=15.18, suggested='0-15%', actual='新推薦 3 檔皆進攻型（記憶體 2、AI 伺服器 1）；防禦型僅⏳沿用金融 2 檔'),
    watchlist=['3045 台灣大（準確率①未過：電信不在 🔴 影響鏈）', '2354 鴻準（①未過＋持股比 -3）', '2603 長榮（②近5天外資 -6 張）',
               '3532 台勝科（①未過：矽晶圓無對應催化）', '2351 順德（①未過：銅價線纜 tier_from_tracker）', '2883 凱基金（①矛盾：🟡美債主題點名「曲線趨平壓抑銀行利差」）'],
    tier_from_tracker_added=0,
    pattern_tracker=dict(date='2026-09-24', overall=57.6, applied=['2408 南亞科 記憶體 tier_0（DRAM）38.5%/13 保守 -3']),
    removed_stocks=[], tomorrow_opening_exits=[], track_b_recommendations=[], track_b_observations=[])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for r in recs_sorted:
    print(r['stock_code'], r.get('score_today') or r['score'], r['recommend_date'], r['recommend_price'], r['stop_loss'])
print({c['stock_code']: c['holding_days'] for c in carry})
