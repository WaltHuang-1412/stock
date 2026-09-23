import json, re
T = '2026-09-23'
H = json.load(open(f'data/{T}/_holdings_src.json', encoding='utf-8'))
Hd = {h['stock_code']: h for h in H}


def rec(code, name, industry, price, target, score, position, reason, detail, pct=-10, rating='⭐⭐⭐⭐'):
    return dict(stock_code=code, stock_name=name, industry=industry, recommend_date=T, recommend_price=price,
                target_price=target, stop_loss_pct=pct, stop_loss=round(price * (1 + pct / 100), 2),
                settlement_days=10, position=position, score=score, rating=rating, result='holding', track='A',
                score_detail=detail, reason=reason)


recs = [
    rec('2886', '兆豐金', '金融／金控（industry_chains 金融 tier_0 金控；另登錄 聯準會利率政策 tier_from_tracker）', 50.5, 54.5, 101, '10-15%',
        '🛤️軌道A｜🔴超強催化『聯準會利率政策』（升息↑轉鷹、CME 12 月升息機率 90%，利差結構利多）｜📶訊號A（預埋）L2 +10｜籌碼動能 -41.2%（<-30%）+15、10 日買7賣3、真連買 2 天、近5天外資 +18K 張｜09-22 T86 +8,422 張（外資 +12,736／投信 -4,781，非同步）avg_rank 22.0、佔成交 39.8%｜反轉 Level 0｜法人現身門檻 ✅｜vs MA20 +1.06%｜⚠️ 09-22 才因 09-21 T86 L4（5.4%）開盤出場，本筆為 09-22 T86 翻買後的新推薦，非撤銷原出場｜⚠️ EPS 快取停於 2025-12-31（金融業半年報期限 8/31 已過）視為 0｜卷宗：今日重大訊息＝子公司兆豐投信董監異動（行政事項）；當日資料源 mentions=0，依據為法人籌碼＋知識庫催化對應',
        '五維度小計 76 ＝ 時事 20＋法人 16（TOP21-35 基礎14＋佔成交>20% +2）＋產業 17（tier_0 金控）＋技術 12（L0 佈局中：動能<-30% 但真連買僅2天）＋價位 11｜modifiers：動能 +15｜訊號A L2 +10｜營收 +13.1% 不調整｜EPS 快取落後 0｜持股比 +0.03% 0｜模式追蹤器：金融 tier_0 為 hot（僅標註）',
        rating='⭐⭐⭐⭐⭐'),
    rec('8046', '南電', 'AI 晶片載板（industry_chains AI tier_0；另 ABF載板 tier_from_tracker）', 1165.0, 1260.0, 90, '10-15%',
        '🛤️軌道A｜🔴超強催化『AI伺服器與半導體』（SOX +2.06% 連六漲、MU +5.00%）＋🟡『ABF載板/PCB基板缺口擴大』↑加速｜09-22 T86 +5,982 張、avg_rank 13.0、佔成交 37.4%｜籌碼動能 -50.6%（<-30%）+15、10 日買6賣4、近5天外資 +2,252 張｜反轉 Level 0｜法人現身門檻 ✅｜營收 2026-08 YoY +40.6%、Q2 EPS +5、外資持股比週增 +0.86% +5｜⚠️ 5 日 +7.4% → -10｜⚠️ 模式追蹤器 PCB cold（38.5%／13 筆）保守套用 -3｜卷宗：窗口內無事件、當日資料源 mentions=0',
        '五維度小計 78 ＝ 時事 21（🔴20＋↑加速+1）＋法人 19（TOP11-20 基礎17＋佔成交>20% +2）＋產業 17（AI tier_0）＋技術 10（L0 正常型態，真連買1天）＋價位 11｜modifiers：動能 +15｜5日 +7.4% -10｜EPS +5｜持股比 +5｜模式 PCB cold -3',
        rating='⭐⭐⭐⭐⭐'),
    rec('2609', '陽明', '航運／貨櫃（industry_chains 中東地緣政治 tier_from_tracker → 產業邏輯以 13-16 分計）', 60.8, 65.7, 87, '10-15%',
        '🛤️軌道A｜🔴超強催化『中東地緣政治（含航運）』：亞洲-美東運價逾 1 萬美元/40呎櫃創 4 年新高、陽明 09-22 法說指四大結構性問題支撐運價（topic_tracker 影響鏈直接點名陽明↑）｜📶訊號A（預埋）L2 +10｜09-22 T86 +3,360 張（外資 +3,611／投信 +74 同步）、avg_rank 34.5、佔成交 20.4%｜10 日買7賣3、近5天外資 +38K 張、動能 +40.7%（0~50% 正常）｜反轉 Level 0｜法人現身門檻 ✅｜營收 2026-08 YoY +56.2%、Q2 EPS +5｜卷宗：法說會已於 09-22 舉行（事件已過），當日資料源提及 14 處皆為正面運價敘事｜⚠️ WTI -6.38% 對燃料成本為順風，但同時削弱「地緣風險」敘事，雙向揭露',
        '五維度小計 72 ＝ 時事 21（🔴）＋法人 16（TOP21-35 基礎13＋佔成交>20% +2＋外資投信同步 +1）＋產業 14（tier_from_tracker）＋技術 10＋價位 11｜modifiers：訊號A L2 +10｜EPS +5｜動能 0｜營收 0｜持股比 -0.08% 0｜模式追蹤器：中東航運為 hot（僅標註）'),
    rec('3023', '信邦', '連接器（industry_chains AI tier_2／蘋果供應鏈 tier_2）', 320.5, 346.0, 73, '5-10%',
        '🛤️軌道B（時事）＋📶訊號B（催化）🟢早期 +5：Apple 連漲 2 天、信邦尚未進入 TOP50｜對應🔴『AI伺服器與半導體』（AI tier_2 連接器）｜chip：10 日買8賣2、累計 +756 張、近5天外資 +391 張、動能 -25.4%（-30~0%）+10｜反轉 Level 0｜法人現身門檻：不在 TOP50，但 vs MA20 -0.86%（非 0~+5% 區）→ 不適用｜營收 2026-08 YoY +32.5%｜⚠️ 法人參與度低（不在 TOP50，法人分僅 6）＋當日資料源 mentions=0，推薦依據為訊號B＋知識庫產業對應，倉位壓在 5-10%',
        '五維度小計 58 ＝ 時事 20（AI 🔴，取最強對應）＋法人 6（不在 TOP50）＋產業 14（tier_2）＋技術 10＋價位 8｜modifiers：動能 +10｜訊號B 🟢早期 +5｜EPS 0｜營收 0｜持股比 0',
        rating='⭐⭐⭐'),
]
for code, score, note in [
        ('2892', 97, '今日評分 97：時事 20＋法人 18＋產業 14＋技術 12＋價位 13＋動能 +10＋訊號A L2 +10；09-22 T86 +9,287 張、外資投信同步'),
        ('3042', 80, '今日評分 80：時事 20（光通訊🔴）＋法人 16＋產業 14＋技術 9＋價位 11＋EPS +5＋持股比 +5；動能 +500% 走🔥超強催化覆寫不扣分')]:
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
    x = dict(h); x.pop('source_file', None)
    x['holding_days'] = dmap.get(h['stock_code'], '⏸️ 凍結')
    x['result'] = 'holding'
    carry.append(x)

t = dict(
    date=T, settings=dict(stop_loss_pct=-10, settlement_days=10),
    market_context=dict(regime='多頭', score=5, vix=14.21, sox=2.06, nasdaq=0.45, mu=5.0, wti=-6.38, taiex_prev_close=47800.17,
                        note='market_regime taiex 校正後仍為 09-21 值 47718.84；09-22 實際收盤 47800.17（+0.17%，取自 09-22 盤後報告 Yahoo ^TWII）'),
    prior_decisions_executed=dict(source='tracking_2026-09-22.json', tomorrow_opening_exits=[], note='09-22 盤後定案 0 筆次日開盤出場 → Step 4-0 無已決事項'),
    stop_loss_check_v8310=[
        dict(symbol='6770', name='力積電', date='2026-09-22', close=71.8, stop_loss=73.26, result='🛑 低於停損', note='09-21 已依鐵律①出場，yaml 未更新之重複輸出 → 不重複出場'),
        dict(symbol='2337', name='旺宏', date='2026-09-22', close=118.0, stop_loss=147.6, result='🛑 低於停損', note='09-11 已出場，重複輸出'),
        dict(symbol='2313', name='華通', date='2026-09-22', close=222.0, stop_loss=235.98, result='🛑 低於停損', note='09-11 已出場，重複輸出'),
        dict(symbol='3090', name='日電貿', date='2026-09-22', close=164.5, stop_loss=256.5, result='🛑 低於停損', note='09-11 已出場，重複輸出'),
        dict(symbol='1301', name='台塑', date='2026-09-22', close=64.6, stop_loss=54.08, result='✅ 未觸發', note='09-22 已依 L4 已決事項出場（64.6 入帳）'),
        dict(symbol='4938', name='和碩', date='2026-09-22', close=90.0, stop_loss=76.5, result='✅ 未觸發', note='09-21 已依 L4 出場'),
        dict(symbol='2330', name='台積電', date='2026-09-22', close=2460.0, stop_loss=None, result='➖ 不適用', note='零股 0.15 張、yaml 無 stop_loss；本日另觸發 L4 21.9%')],
    stop_loss_check_conclusion='0 筆新觸發；4 檔觸發者皆為已出場部位因 my_holdings.yaml 未更新之重複輸出（第 8 次再現）',
    series_alignment_check_v838=dict(aligned=15, frozen=['2867 三商壽（末日 2026-08-19）'], note='16 筆 holding 中 15 筆末日＝2026-09-22'),
    two_day_drawdown_check=dict(triggered=[], worst='4904 遠傳 -1.40%'),
    opening_exits_today=[
        dict(stock_code='2883', stock_name='凱基金', category='鐵律③法人反轉 L4', reason='09-22 T86 賣超 -28,639 張＝52.1% 5日均量（≥8%，不受 v8.3.3 保護）；推薦日 09-22，收盤價入帳（v8.3.2）'),
        dict(stock_code='2330', stock_name='台積電（持倉零股 0.15 張）', category='鐵律③法人反轉 L4（my_holdings.yaml）', reason='09-22 T86 賣超 -4,268 張＝21.9%（≥8%），10 日累計 -24K 為負；⚠️ 09-11/09-14 報告已記出場，yaml 仍列 0.15 張 → 若仍持有則開盤出場')],
    pending_review_v833=[dict(stock_code='2891', stock_name='中信金', ratio_pct=6.9, sell_lots=-3329, cum10='+45K', status='⚠️ 待複核（<8% 且 10 日累計為正）', next='12:30 與盤後各複核一次，兩次皆 ≥5% 才於 09-24 開盤出場')],
    holdings_reversal_scan=dict(scanned=17, L4=['2883 凱基金 52.1%', '2330 台積電 21.9%', '2891 中信金 6.9%（待複核）'], L2=['2382 廣達 2.2%'],
                                unknown=['3481 群創（今日+26,643、累計-5,196）', '2867 三商壽（無數據，凍結）']),
    settlement_today=[],
    recommendations=recs_sorted,
    carry_over=[h['stock_code'] for h in H],
    carry_over_recommendations=carry,
    carry_over_note='16 筆 holding（含 2867 凍結）照抄 settlement_checker 輸出；進場價／停損一律取自來源 tracking_{推薦日}.json',
    disposition_stocks=dict(
        twse_official=['2305 全友｜09/18~09/30｜第一次處置', '2455 全新｜09/23~10/05｜第二次處置', '2468 華經｜09/22~10/02｜第一次處置',
                       '6226 光鼎｜09/21~10/01｜第二次處置', '6715 嘉基｜09/23~10/01｜第一次處置', '8021 尖點｜09/23~10/01｜第二次處置'],
        twse_attention=[],
        countdown=['2409 友達｜連續達標 2 天｜最快剩 1 天處置', '6168 宏齊｜連續達標 4 天｜最快剩 1 天處置', '8150 南茂｜連續達標 1 天｜最快剩 2 天處置',
                   '3016 嘉晶｜連續達標 1 天｜最快剩 2 天處置', '2449 京元電子／6116 彩晶／2481 強茂｜接近注意門檻']),
    module_a_result=dict(L3=['2412 中華電', '6213 聯茂', '1102 亞泥', '5876 上海商銀'],
                         L2=['2892 第一金', '2891 中信金', '3045 台灣大', '2609 陽明', '2886 兆豐金', '5880 合庫金', '2834 臺企銀', '2382 廣達'],
                         L1=['2890 永豐金', '2889 國票金']),
    module_b_result=dict(preposition=119, institution_in=32, rallied_excluded=60, passed=['3023 信邦'], final=['3023 信邦']),
    us_leader_alerts=dict(total=0, note='Dell -4.59%、Cisco -4.50% 未對應台股（us_leader_mapping 無 tw_stocks），不觸發'),
    diversification=dict(new_recommendations=4, industries=['金融／金控', 'AI 晶片載板', '航運', '連接器'], max_single_industry_pct=25.0, passed=True),
    defense_ratio=dict(vix=14.21, suggested='0-15%', actual='新推薦 4 檔中防禦型 1 檔（2886 兆豐金）＝25%，略高於建議；進攻 3 檔'),
    watchlist=['3045 台灣大（準確率①未過）', '2354 鴻準（準確率①未過）', '6770 力積電（68 分）', '2885 元大金（68 分）'],
    tier_from_tracker_added=0,
    pattern_tracker=dict(date='2026-09-23', applied=['8046 南電 PCB cold -3']),
    removed_stocks=[], tomorrow_opening_exits=[], track_b_recommendations=[], track_b_observations=[])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
for r in recs_sorted:
    print(r['stock_code'], r.get('score_today') or r['score'], r['recommend_date'], r['recommend_price'], r['stop_loss'])
print({c['stock_code']: c['holding_days'] for c in carry})
