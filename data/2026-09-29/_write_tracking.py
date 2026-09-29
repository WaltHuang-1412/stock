import json, re
T = '2026-09-29'
H = json.load(open(f'data/{T}/_holdings_src.json', encoding='utf-8'))
Hd = {h['stock_code']: h for h in H}
EXITS = ['2303', '6770', '2408', '2317']

MKT = '⚠️ 09-24 市場三大法人合計賣超 -438.7 億（外資 -338.0 億、投信 -114.1 億）；連假 4 天後復市，美股 09-28 費半 -1.61%、Qualcomm -7.17%、Intel -5.67%（兩者未登錄龍頭對應表）'


def rec(code, name, industry, price, target, score, position, reason, detail, pct=-10, rating='⭐⭐⭐⭐'):
    return dict(stock_code=code, stock_name=name, industry=industry, recommend_date=T, recommend_price=price,
                target_price=target, stop_loss_pct=pct, stop_loss=round(price * (1 + pct / 100), 2),
                settlement_days=10, position=position, score=score, rating=rating, result='holding', track='A',
                score_detail=detail, reason=reason)


recs = [
    rec('3702', '大聯大', '半導體通路（industry_chains「AI伺服器」tier_from_tracker，category「AI伺服器與半導體」→ 產業邏輯以 13-16 分計）', 117.5, 127.0, 91,
        '10-15%',
        '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』（知識庫 tier_from_tracker 登錄於此主題；影響鏈未直接點名 → 時事取下緣）｜09-24 T86 +3,451 張（外資 +2,858／投信 +414 同步）、TOP50 張數 #8、avg_rank 12.5、佔成交 43.3%｜10 日累計 +13K、買8賣2、真連買 3 天、近5天三大法人 +5,224／外資 +4,175／投信 +1,272｜動能 -33.8% 佈局完成 +15｜反轉 L0 ✅法人買超中｜Q2 EPS +5｜8 月營收 YoY +90.8%（MI 催化x營收表），但 5 日上漲未回檔 → 營收因子 0｜⚠️ 5日 +5.86% -10｜vs MA20 +9.8%、月季雙線上｜卷宗：事件 0、mentions 2（MI 產業鏈 L2 通路商、營收表），無矛盾｜' + MKT,
        '五維度小計 81 ＝ 時事 20（🔴AI 基礎下緣；NVDA +1.68% 無加分）＋法人 22（avg_rank 12.5 → TOP11-20 基礎 19＋佔成交 43.3% +2＋外資投信同步 +1；真連買 3 天 0）＋產業 14（tier_from_tracker 二線/配套）＋技術 12（L0＋佈局中：動能<0、真連買 3 天）＋價位 13（vs MA20 +9.76% 12＋雙線上 +1）｜modifiers：動能 -33.8% +15｜5日 +5.86% -10｜EPS Q2 +5｜外資持股比 +0.15% 0｜營收 +80.5%（revenue_check）未回檔 0｜買賣天數 2 賣 0｜模式追蹤器非 cold 0｜龍頭預警無對應 0',
        rating='⭐⭐⭐⭐⭐'),
    rec('6196', '帆宣', '半導體建廠工程／設備（industry_chains「AI伺服器」「台積電產能瓶頸」tier_from_tracker → 產業邏輯以 13-16 分計）', 565.0, 610.0, 72,
        '5-10%',
        '🛤️軌道B（時事）｜🔴超強催化『AI伺服器與半導體』影響鏈直接點名「漢唐(2404)↑／帆宣(6196)↑ 建廠工程」＋🟡『台積電產能瓶頸與美國第二園區』同樣點名帆宣↑（傳台積電赴德州建第二園區、6 座先進晶圓廠）｜不在 09-24 TOP50；vs MA20 +8.8%（>+5%，法人現身門檻不適用）｜10 日累計 +1,732、買7賣3、真連買 3 天、近5天外資 +807／投信 -62｜動能 -9.3% 佈局中 +10｜反轉 L0｜Q2 EPS +5｜8 月營收 YoY +101.4%，但 5 日上漲未回檔 → 0｜⚠️ 5日 +9.5% -10（接近 10% 不評分線）｜⚠️ 法人參與量小（單日百張級），籌碼分數僅 6｜卷宗：事件 0、mentions 10（topic_tracker 兩個主題皆點名↑），無矛盾｜' + MKT,
        '五維度小計 67 ＝ 時事 22（🔴AI 影響鏈點名↑ 21＋方向↑加速 +1）＋法人 6（不在 TOP50 → 4-8 中值；外資 +188／投信 0 不同步；真連買 3 天 0）＋產業 14（tier_from_tracker 二線/配套）＋技術 12（L0＋佈局中：動能<0、真連買 3 天）＋價位 13（vs MA20 +8.77% 12＋雙線上 +1）｜modifiers：動能 -9.3% +10｜5日 +9.5% -10｜EPS Q2 +5｜外資持股比 +0.08% 0｜營收 +83.9% 未回檔 0｜買賣天數 3 賣 0｜模式追蹤器非 cold 0',
        rating='⭐⭐⭐'),
]
for code, score, note in [
        ('2892', 106, '今日評分 106：五維度 76（時事 18〔🔴聯準會，但 🟡美債殖利率主題逆風銀行利差、MI 催化x營收標「⚠️營收未跟上」→ 取區間下修〕＋法人 19〔avg_rank 23.5 → 15＋佔成交 21.0% +2＋外資 +1,571／投信 +643 同步 +1＋真連買 7 天 +1〕＋產業 14〔tier_from_tracker〕＋技術 14〔L0＋動能<-30%＋真連買 7 天〕＋價位 11〔vs MA20 +3.29%〕）＋動能 -51.7% +15＋📶訊號A L3 +15；⚠️ EPS 快取停於 2025-12-31（金融業 Q2 申報期限 8/31 已過、--update-cache 未取得）→ 0；09-24 T86 +2,362 張、近5天外資 +20K'),
        ('2886', 86, '今日評分 86：五維度 61（時事 18〔同 2892 下修〕＋法人 6〔09-24 T86 -20 張、不在 TOP50 → 4-8；真連買 0〕＋產業 17〔金融 tier_0 金控〕＋技術 12〔L0＋動能<0，但真連買 0 → 佈局中〕＋價位 8〔vs MA20 -1.42%、季線撐 +1〕）＋動能 -52.9% +15＋📶訊號A L2 +10；⚠️ EPS 快取停於 2025-12-31 → 0；10 日累計 +38K、近5天外資 +21K／投信 -13K 對決')]:
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

sl = [('6770', '力積電', 72.0, 73.26, '🛑 低於停損', '09-21 已依鐵律①出場（入帳 72.70），yaml 未更新之重複輸出 → 不重複出場'),
      ('2337', '旺宏', 117.0, 147.6, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('2313', '華通', 222.5, 235.98, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('3090', '日電貿', 165.0, 256.5, '🛑 低於停損', '09-11 已出場，重複輸出'),
      ('1301', '台塑', 64.1, 54.08, '✅ 未觸發', '09-22 已依 L4 出場（入帳 64.60）'),
      ('4938', '和碩', 91.3, 76.5, '✅ 未觸發', '09-21 已依 L4 出場（入帳 90.80）'),
      ('2330', '台積電', None, None, '➖ 不適用', '零股 0.15 張、yaml 無 stop_loss；09-23 已依 L4 出場（入帳 2,500）')]

exits = [
    dict(stock_code='2303', stock_name='聯電', category='鐵律③ L4', recommend_date='2026-09-18',
         reason='09-24 T86 賣超 -44,181 張＝19.8%（≥8%）；10 日累計 +113K 但佔比 ≥8% 不受 v8.3.3 保護；入帳價用 09-29 收盤（v8.3.2）'),
    dict(stock_code='6770', stock_name='力積電', category='鐵律③ L4', recommend_date='2026-09-24',
         reason='09-24 T86 賣超 -44,817 張＝37.6%（≥8%）；10 日累計 +26K 但佔比 ≥8% 不受保護；推薦後 D1 即觸發'),
    dict(stock_code='2408', stock_name='南亞科', category='鐵律③ L4', recommend_date='2026-09-24',
         reason='09-24 T86 賣超 -22,678 張＝41.2%（≥8%）；10 日累計 -9,496 為負；推薦後 D1 即觸發'),
    dict(stock_code='2317', stock_name='鴻海', category='鐵律③ L4', recommend_date='2026-09-24',
         reason='09-24 T86 賣超 -24,232 張＝76.5%（≥8%）；10 日累計 -18K 為負；推薦後 D1 即觸發')]

t = dict(
    date=T, settings=dict(stop_loss_pct=-10, settlement_days=10),
    market_context=dict(regime='多頭', score=3, vix=16.07, sox=-1.61, nasdaq=-0.92, sp500=-0.77, mu=-2.61, amd=-3.61, intc=-5.67, qcom=-7.17,
                        meta=-4.79, nvda=1.68, tsm_adr=0.50, wti=0.91, gold=-3.82, us10y=5.24, taiex_prev_close=48024.6,
                        note='TAIEX 09-24 收盤 48,024.6（Yahoo ^TWII，fix_market_regime_taiex 校正，差額 0）；美股為 09-28（一）行情',
                        holiday='09-25 中秋節、09-28 教師節休市，前一交易日 09-24（gap 5 天，美股 1 個新交易日）'),
    prior_decisions_executed=dict(source='tracking_2026-09-24.json', tomorrow_opening_exits=[],
                                  note='Step 4-0：09-24 tomorrow_opening_exits 為空、removed_stocks 無「次日開盤出場」→ 0 筆已決事項'),
    stop_loss_check_v8310=[dict(symbol=a, name=b, date='2026-09-24', close=c, stop_loss=d, result=e, note=f) for a, b, c, d, e, f in sl],
    stop_loss_check_conclusion='0 筆新觸發；4 檔觸發者皆為已出場部位因 my_holdings.yaml 未更新之重複輸出',
    series_alignment_check_v838=dict(aligned=13, frozen=['2867 三商壽（末日 2026-08-19）'], note='14 筆 holding 中 13 筆末日＝2026-09-24（前一交易日）'),
    two_day_drawdown_check=dict(triggered=[], worst='2303 聯電 -3.75%（160.0→154.0）'),
    opening_exits_today=exits,
    pending_review_v833=[],
    holdings_reversal_scan=dict(scanned=14, L4=['2303 聯電 19.8%', '6770 力積電 37.6%', '2408 南亞科 41.2%', '2317 鴻海 76.5%'],
                                L0=['4904 遠傳', '5876 上海商銀', '2395 研華', '2412 中華電', '2892 第一金', '2454 聯發科', '2886 兆豐金', '8046 南電', '2609 陽明'],
                                unknown=['2867 三商壽（無數據，凍結）']),
    settlement_today=[],
    recommendations=recs_sorted,
    carry_over=[c['stock_code'] for c in carry],
    carry_over_recommendations=carry,
    carry_over_note='10 筆 holding（含 2867 凍結）照抄 settlement_checker 輸出；進場價／停損取自來源 tracking_{推薦日}.json；另 4 筆列開盤出場',
    disposition_stocks=dict(
        twse_official=['2305 全友｜09/18~09/30｜第一次處置', '2455 全新｜09/23~10/05｜第二次處置', '2468 華經｜09/22~10/02｜第一次處置',
                       '3443 創意｜09/29~10/05｜第一次處置（連續三次）★今日新增', '6168 宏齊｜09/24~10/02｜第一次處置',
                       '6226 光鼎｜09/21~10/01｜第二次處置', '6715 嘉基｜09/23~10/01｜第一次處置', '8021 尖點｜09/23~10/01｜第二次處置'],
        tpex_official=['2221 大甲｜09/24~10/06｜連續3日達注意', '7772 耀穎｜09/24~10/02｜30日內曾處置又達標', '6218 豪勉｜09/23~10/05｜連續3日達注意',
                       '6945 圓祥生技｜09/23~10/01｜連續3日達注意', '5314 世紀*｜09/22~09/30｜30日內曾處置又達標',
                       '6221 晉泰｜09/21~09/29｜連續3日達注意', '3441 聯一光｜09/18~09/30｜30日內曾處置又達標'],
        twse_attention=[],
        countdown=['3605 宏致｜連續達標 7 天｜最快明日處置', '8150 南茂｜連續達標 3 天｜最快明日處置', '3016 嘉晶｜連續達標 3 天｜最快明日處置',
                   '6526 達發｜連續達標 2 天｜最快剩 1 天處置', '1727 中華化｜連續達標 2 天｜最快剩 1 天處置',
                   '6672 騰輝電子-KY｜連續 1 天｜最快剩 2 天處置', '2030 彰源｜連續 1 天｜最快剩 2 天處置', '6533 晶心科｜連續 1 天｜最快剩 2 天處置',
                   '2034 允強／3037 欣興／6213 聯茂／3518 柏騰／2466 冠西電／2404 漢唐／3167 大量｜接近注意門檻']),
    module_a_result=dict(L3=['2892 第一金', '2412 中華電', '2609 陽明', '2027 大成鋼'],
                         L2=['3045 台灣大', '2884 玉山金', '2891 中信金', '2353 宏碁', '2886 兆豐金', '2615 萬海', '2890 永豐金', '1718 中纖', '5880 合庫金', '1102 亞泥'],
                         L1=['2883 凱基金', '2605 新興', '9904 寶成', '2103 台橡', '2834 臺企銀']),
    module_b_result=dict(preposition=32, institution_in=15, rallied_excluded=38, passed=[], final=[],
                         excluded=['2382 廣達 L4', '2324 仁寶 L4＋累計負', '2356 英業達 L4＋累計負', '6669 緯穎 L4＋累計負', '2376 技嘉 動能+239%',
                                   '3017 奇鋐 動能+500%', '3324 雙鴻 數據不足', '6230 超眾 L4', '2368 金像電 L4＋累計負', '2367 燿華 動能+147%']),
    us_leader_alerts=dict(total=3, L1=['Micron -2.61%（2408/1303/2344/2337/5347/6770）', 'AMD -3.61%（2454/3661/3443/3707）', 'Tesla -3.94%（2317/1513/1519/2308/1504）'],
                          note='Qualcomm -7.17%、Intel -5.67%、Meta -4.79%、Marvell -3.83% 未登錄對應表；Dell -3.46% tw_stocks 為空 → 0 預警，人工揭露'),
    diversification=dict(ranked=4, new_recommendations=2, industries=['金融 2（⏳）', '半導體通路 1', '半導體建廠工程 1'], max_single_industry_pct=50.0),
    defense_ratio=dict(vix=16.07, suggested='0-15%', actual='新推薦 2 檔皆進攻型（半導體通路、建廠工程）；防禦型僅⏳沿用金融 2 檔'),
    watchlist=['2609 陽明（法人現身門檻未過：09-24 T86 僅 +1 張、vs MA20 +0.95%；沿用追蹤續行）',
               '3045 台灣大（①未過：電信不在 🔴 影響鏈；真連買 10 天）', '2412 中華電（①未過；沿用中）',
               '2027 大成鋼（訊號A L3，但①未過：鋼鐵僅 ⚪ 觀察＋模式 cold 33.3%）', '2351 順德（①未過：銅價線纜 tier_from_tracker；營收回檔 +5／持股比 +5）',
               '2395 研華（①未過：邊緣AI 🟢；沿用中）'],
    tier_from_tracker_added=0,
    tier_from_tracker_note='本流程未寫入；industry_chains.json 於 07:39 由「催化劑追蹤（自動同步）」新增 40 筆（未 commit，本日一併提交並揭露）',
    pattern_tracker=dict(date='2026-09-29', applied=[], note='最終推薦 4 檔皆非 cold pattern'),
    removed_stocks=[], tomorrow_opening_exits=[], track_b_recommendations=[], track_b_observations=[])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for r in recs_sorted:
    print(r['stock_code'], r.get('score_today') or r['score'], r['recommend_date'], r['recommend_price'], r['stop_loss'])
print({c['stock_code']: c['holding_days'] for c in carry})
