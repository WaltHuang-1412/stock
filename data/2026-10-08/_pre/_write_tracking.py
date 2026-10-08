import json
P = 'data/tracking/tracking_2026-10-08.json'


def carry(code, name, rd, rp, tp, sl, d, last, status, src):
    return dict(stock_code=code, stock_name=name, recommend_date=rd, recommend_price=rp, target_price=tp, stop_loss=sl,
                stop_loss_pct=-5 if code in ('2609','2344') else -10, settlement_days=10, holding_days=d, last_close=last,
                status=status, source=src, result='holding', holding_days_label=f'D{d}/10')


t = {
    "date": "2026-10-08", "version": "v8.3.10", "phase": "before_market",
    "settings": {"stop_loss_pct": -10, "settlement_days": 10},
    "market_context": {
        "taiex_prev_close": 49806.37, "taiex_as_of": "2026-10-07", "regime": "多頭（score 4）", "vix": 15.08,
        "us": {"NASDAQ": -0.22, "S&P500": -0.22, "DJI": -0.66, "SOX": -1.15, "NVDA": -0.74, "AMD": -0.55, "AVGO": 0.19,
               "MU": 4.06, "WDC": -1.37, "AMAT": -1.81, "LRCX": -1.31, "QCOM": -2.16, "META": -2.38, "TSM_ADR": -2.09,
               "WTI": -0.56},
        "institutional_1007_yi": {"total": -212.57, "foreign": -130.44, "trust": -4.17, "dealer": -77.96},
        "holiday_note": "10/9（五）補假休市，10/10-10/12 連休；今日為連假前最後交易日，進場持有期跨 4 日長假（下一交易日 10/12）"},
    "prior_decisions_executed": {
        "source": "tracking_2026-10-07.json tomorrow_opening_exits",
        "items": [
            "2330 台積電（已決，v8.3.3 複核①②皆 ≥5%）→ 10-08 開盤出場，入帳用 10-08 收盤",
            "2344 華邦電（已決，同上）→ 10-08 開盤出場，入帳用 10-08 收盤",
            "6770 力積電（持倉，鐵律①＋已決 L4）→ 10-08 開盤出場（若實際仍持有）"],
        "new_data_disclosure": "10-07 T86 已公布（本次盤前首次可用）：2344 華邦電 +12,918 張翻買、2330 台積電 -650 張（Level 2，3.1%<5%）。已決事項不重評，仍依原決議執行；此為執行日法人翻買的對照樣本，供日後 v8.3.3 同源複核議題使用"},
    "opening_exits_today": [
        dict(stock_code="2330", stock_name="台積電", category="已決事項", reason="鐵律③ L4 待複核兩次皆 ≥5%（10-06 T86 同源）"),
        dict(stock_code="2344", stock_name="華邦電", category="已決事項", reason="鐵律③ L4 待複核兩次皆 ≥5%（10-06 T86 同源）；10-07 T86 已翻買 +12,918 張（揭露，不重評）"),
        dict(stock_code="3711", stock_name="日月光投控", category="新 L4（10-07 T86）", reason="賣超 -1,352 張佔日均量 11.4% ≥8%，不受 v8.3.3 待複核保護；D4/10 現價 732.0 (+4.1%)"),
        dict(stock_code="2308", stock_name="台達電", category="新 L4（10-07 T86）", reason="賣超 -1,981 張佔日均量 19.8% ≥8%；D1/10 現價 1,990.0 (-0.8%)；另有今日重大訊息（東莞子公司取得設備，中性）"),
        dict(stock_code="6770", stock_name="力積電", category="持倉 my_holdings.yaml（已決 L4＋鐵律①）", reason="收 72.6 < 停損 73.26；10-07 T86 賣超 -39,660 張佔 33.2%"),
        dict(stock_code="2313", stock_name="華通", category="持倉 my_holdings.yaml（新 L4）", reason="10-07 T86 賣超 -7,433 張佔 21.4% ≥8%；收 246.0 未觸停損 235.98；v8.3.3 不適用（≥8%）"),
        dict(stock_code="4938", stock_name="和碩", category="持倉 my_holdings.yaml（已決 L4，yaml 未更新）", reason="10-05 已決 L4；10-07 T86 -753 張佔 11.3%"),
        dict(stock_code="2337", stock_name="旺宏", category="持倉 my_holdings.yaml（鐵律①，yaml 未更新重複輸出）", reason="收 118.0 < 停損 147.6；今日召開法說（重大訊息）"),
        dict(stock_code="3090", stock_name="日電貿", category="持倉 my_holdings.yaml（鐵律①，yaml 未更新重複輸出）", reason="收 174.0 < 停損 256.5")],
    "stop_loss_check_v8310": {
        "time": "2026-10-08 盤前", "basis": "get_close_series 末筆＝2026-10-07 收盤（序列對齊）",
        "results": [
            dict(stock_code="2330", stock_name="台積電", close=2585.0, stop_loss=None, hit="不適用（yaml 無 stop_loss）"),
            dict(stock_code="6770", stock_name="力積電", close=72.6, stop_loss=73.26, hit="🛑 觸及停損（-10.81%，已列 10-07 盤後決議）"),
            dict(stock_code="2337", stock_name="旺宏", close=118.0, stop_loss=147.6, hit="🛑 觸及停損（重複輸出：流程已出場、yaml 未更新）"),
            dict(stock_code="2313", stock_name="華通", close=246.0, stop_loss=235.98, hit="✅ 未觸發（距停損 +4.25%）；但新 L4 21.4% 列開盤出場"),
            dict(stock_code="3090", stock_name="日電貿", close=174.0, stop_loss=256.5, hit="🛑 觸及停損（重複輸出：yaml 未更新）"),
            dict(stock_code="1301", stock_name="台塑", close=75.4, stop_loss=54.08, hit="✅ 未觸發；損益 +25.49% 超過 yaml take_profit_percent 20%（無鐵律，提示）"),
            dict(stock_code="4938", stock_name="和碩", close=90.0, stop_loss=76.5, hit="✅ 未觸發；10-05 已決 L4（yaml 未更新）")],
        "new_triggers": 0},
    "two_day_drawdown_check": "get_close_series 末3筆自算：追蹤＋持倉 19 檔最差為 3042 晶技 3日 -5.18%、6770 力積電 -4.22%，無 2 日累計 <-10%",
    "series_alignment_check_v838": "11 筆 holding 序列末日皆＝2026-10-07；唯 2867 三商壽停於 2026-08-19 → ⚠️序列停滯，凍結判定（D 不推進）",
    "holdings_reversal_scan": "全 17 檔（追蹤 11＋持倉 7，2330 重疊，2867 無數據）：L4 7 檔＝3711／2308／6770／2337／2313／3090／4938；L2 1 檔＝2330；健康 3 檔＝1326／2344／1301；L0 5 檔＝3035／3443／3661／2404／2609；2867 數據不足（不可視為安全）",
    "settlement_today": "0 筆結算（settlement_checker：11 筆 holding；無觸目標/停損；無 D10 到期）",
    "recommendations": [
        dict(stock_code="1312", stock_name="國喬",
             industry="中東地緣政治/石化（industry_chains tier_from_tracker 待審區，產業邏輯以 13 計）",
             recommend_price=15.05, target_price=16.25, stop_loss_pct=-10, stop_loss=13.545, settlement_days=10,
             position="10-15%（建議取下緣 10%）", score=96, rating="⭐⭐⭐⭐⭐",
             track="軌道A（TOP50 買超，avg_rank 30.5）＋訊號A L2", result="holding",
             reason="訊號A L2 +10；法人 10-07 +7,005 張（外資 +8,689、佔成交 39.9%）、10 日累計 +20K（外資 +22K）、7 買 3 賣、近 5 天外資 +9,978；動能 -42.8%（+15）；反轉 L0；8 月營收 YoY +89.2%、Q2 EPS 虧損收斂（YoY +44.6% +3、毛利率 QoQ +3.7pp +2）；MA20 +2.8%／MA60 +12.6% 雙線上",
             risks="⚠️ 毛利率僅 2.0%、EPS 仍為負（-0.51）；產業位置為待審區；真連買僅 2 天；今日 mentions=0（當日時事資料無提及，法人依據仍成立）；連假前最後交易日持有跨 4 日；10-07 外資整體 -130 億",
             score_breakdown=dict(時事=14, 法人=16, 產業=13, 技術=12, 價格位置=11, 動能=15, 營收=0, EPS=5, 持股比=0, 訊號A=10, 反轉=0))],
    "carry_over": ["3035", "3443", "3661", "1326", "2404", "2609", "3711", "2308", "2330", "2344", "2867"],
    "carry_over_recommendations": [
        carry("3035", "智原", "2026-10-02", 213.0, 230.0, 191.7, 3, 209.0, "✅ 續抱（L0，10-07 T86 +715 張，累計 +7,464；訊號A L2）", "tracking_2026-10-02.json"),
        carry("3443", "創意", "2026-10-06", 8600.0, 9288.0, 7740.0, 1, 8460.0, "✅ 續抱（L0，+81 張；累計 +143）", "tracking_2026-10-06.json"),
        carry("3661", "世芯-KY", "2026-10-06", 3950.0, 4266.0, 3555.0, 1, 4190.0, "✅ 續抱（L0，+748 張）；距目標 1.8%", "tracking_2026-10-06.json"),
        carry("1326", "台化", "2026-10-05", 71.7, 77.4, 64.53, 2, 75.8, "✅ 續抱（健康，+16,150 張）；距目標 2.1%；5日 +8.8%", "tracking_2026-10-05.json"),
        carry("2404", "漢唐", "2026-10-07", 1335.0, 1441.8, 1201.5, 0, 1330.0, "✅ 續抱（L0，+175 張）", "tracking_2026-10-07.json"),
        carry("2609", "陽明", "2026-10-07", 59.2, 63.94, 56.24, 0, 59.1, "✅ 續抱（L0，+429 張）；覆寫型停損 -5%", "tracking_2026-10-07.json"),
        carry("3711", "日月光投控", "2026-10-01", 703.0, 759.0, 632.7, 4, 732.0, "🛑 新 L4 11.4% → 10-08 開盤出場（入帳用 10-08 收盤）", "tracking_2026-10-01.json"),
        carry("2308", "台達電", "2026-10-06", 2005.0, 2165.4, 1804.5, 1, 1990.0, "🛑 新 L4 19.8% → 10-08 開盤出場（入帳用 10-08 收盤）", "tracking_2026-10-06.json"),
        carry("2330", "台積電", "2026-10-06", 2575.0, 2781.0, 2317.5, 1, 2585.0, "🛑 已決出場 → 10-08 開盤出場", "tracking_2026-10-06.json"),
        carry("2344", "華邦電", "2026-10-06", 181.0, 195.48, 171.95, 1, 179.5, "🛑 已決出場 → 10-08 開盤出場（10-07 T86 已翻買，不重評）", "tracking_2026-10-06.json"),
        dict(carry("2867", "三商壽", "2026-08-17", 9.75, 10.73, 8.78, 0, 9.7, "🧊 凍結（序列停滯 08-19）", "tracking_2026-08-17.json"),
             holding_days_label="凍結（序列停滯 08-19）")],
    "carry_over_note": "D{N} 全數照抄 settlement_checker 輸出；進場價／停損價取自來源 tracking 檔；沿用者皆帶 recommend_date。目標價／停損已與來源 tracking 檔逐筆核對",
    "disposition_stocks": "TWSE 處置 16 檔：2030 彰源／2033 佳大／3016 嘉晶／3055 蔚華科／3094 聯傑／3167 大量／3518 柏騰／6533 晶心科／6672 騰輝電子-KY／8201 無敵／8996 高力（昨日已在列）＋新增 1709 和益／2466 冠西電／3701 大眾控／6213 聯茂／6957 裕慶-KY（處置期間未取得：TWSE 公告 API 本次回空）；注意股 0；候選池 49 檔無處置股；預警：2481 強茂、6196 帆宣 接近注意門檻",
    "module_a_result": {
        "L3": [], "L2": ["2412 中華電", "1312 國喬", "2892 第一金", "2609 陽明（沿用）", "1102 亞泥", "3035 智原（沿用）", "2344 華邦電"],
        "L1": ["6770 力積電", "2337 旺宏", "1101 台泥"],
        "integration": "國喬通過全部門檻 +10；亞泥 ①催化對齊未過；中華電／第一金 法人現身門檻未過（不在 TOP50、MA20 +1.2%／-0.4%）"},
    "module_b_result": {
        "maturity": "全部 🟡中期（Broadcom 連漲4天 +7.6% 等），無 🟢早期 → 無 +5", "candidates_checked": 10,
        "passed_basic": ["3042 晶技"],
        "excluded": {"2345 智邦": "L4、累計負", "2449 京元電子": "L4、累計 -16K", "2455 全新": "L4", "3406 玉晶光": "累計負",
                     "4977 眾達-KY": "動能 +223%", "2383 台光電": "動能 +203%", "3044 健鼎": "動能 +140%",
                     "3234 光環": "數據不足", "4908 前鼎": "數據不足"},
        "final": "晶技 評分 66 <70（不在 TOP50、10-06 單日 -7.9%、外資 10 日 -2.3K）→ 不推薦"},
    "us_leader_alerts": "Level 3/2/1 皆 0 筆；缺口：Qualcomm -2.16%（2454 聯發科未登錄）、Meta -2.38%／Cisco 未登錄",
    "diversification": {
        "new_count": 1, "industries": {"石化": 1}, "max_share_pct": 100,
        "note": "新推薦僅 1 檔 <4 檔下限，寧缺勿濫（v8.2 禁止湊數）；49 檔候選池逐檔篩選僅 1 檔同時通過①②③＋動能＋5日＋法人現身門檻；組合層沿用追蹤以 AI/半導體為主"},
    "defense_ratio": {"vix": 15.08, "catalyst": "超強（🔴 區）", "defense_pct": "0-15%", "attack_pct": "85-100%", "regime": "多頭"},
    "watchlist": ["1102 亞泥（80 分，①催化對齊未過）", "3042 晶技（66 分）", "6505 台塑化（②外資5天 -9.1K；5日 +10%）",
                  "1101 台泥（②外資5天 -54K）", "2412 中華電（法人現身門檻）", "2892 第一金（L2、法人現身）", "1513 中興電"],
    "excluded_momentum_over_100": ["1605 華新 +101.7%", "1802 台玻 +500%", "9105 泰金寶-DR", "2883 凱基金", "2882 國泰金", "1409 新纖",
                                   "1402 遠東新", "2481 強茂", "1304 台聚", "2880 華南金", "1609 大亞", "2103 台橡", "1434 福懋",
                                   "1710 東聯", "8131 福懋科", "1504 東元", "3532 台勝科", "2515 中工", "2881 富邦金",
                                   "2891 中信金", "2885 元大金", "5880 合庫金", "2801 彰銀"],
    "excluded_5day_over_10": ["1301 台塑 +10.7%", "1303 南亞 +22.9%", "2492 華新科 +42.9%", "4958 臻鼎-KY", "2327 國巨 +18.1%",
                              "6152 百一", "6209 今國光", "6456 GIS-KY", "3037 欣興 +11.1%", "6196 帆宣 +14.5%"],
    "excluded_reversal": ["2408 南亞科 L4 28.0%", "2436 偉詮電 L4 15.8%", "6239 力成 L4 21.4%", "2892 第一金 L2"],
    "excluded_accuracy_filter": ["1314 中石化 10日累計 -9.7K、營收連16月衰退",
                                 "1216 統一／9904 寶成／2887 台新新光金／2812 台中銀／2464 盟立／2610 華航／2542 興富發／2382 廣達 10日累計為負",
                                 "3481 群創 10日 -21K"],
    "excluded_no_data": ["9105 泰金寶-DR EPS 無數據（亦動能 +500%）"],
    "holdings_evaluation": [
        "1301 台塑：健康續抱（10-07 +47,903 張）；+25.49% 超過 yaml 停利 20%（無鐵律，提示）",
        "2313 華通：新 L4 21.4% → 開盤出場", "6770 力積電／4938 和碩／2337 旺宏／3090 日電貿／2330 零股：見開盤出場清單"],
    "tier_from_tracker_added": "本次新增 0 筆",
    "pattern_tracker": "pattern_today.json 日期 2026-10-05（距今 3 天，未逾期）；hot 不加分；本次推薦未逐檔比對 cold/worst 命中（揭露）",
    "data_quality": [
        "market_regime taiex 已由 fix_market_regime_taiex.py 校正為 10-07 收 49,806.37（原 49,822.55）",
        "EPS 快取：金控 11 檔（2883/2882/2887/2885/2812/5880/2891/2881/2801/2880/2892）季別停在 2025-12-31（Q2 申報期限 8/31 已過）→ 其 EPS 加減分視為 0；其餘為 2026-06-30（Q2，當期）",
        "營收快取 49 檔全部 2026-08（10 日前應為上上月）→ 新鮮；外資持股比 49 檔皆 ≥2026-10-01，國喬 10-06",
        "10-07 T86：fetch_institutional_top30 以 20261007 取得（data/2026-10-07/institutional_top50.json），但 data/cache 尚無 twse_t86_20261007.json；reversal_alert／chip_analysis 的今日張數與 TOP50 交叉核對一致（1301 +47,903、1326 +16,150、2344 +12,918）",
        "處置期間：TWSE punish API 回空，新增 5 檔僅有名稱無期間",
        "Step 1-b 選用判勢 skill 未執行（判勢補充不可用）",
        "preflight：必要輸入檔缺失為當日產出前之預期狀態；daily.sh 錯誤為已知字面比對誤報",
        "龍頭對應缺口：Qualcomm／Meta／Cisco 未登錄"],
    "removed_stocks": [], "tomorrow_opening_exits": [], "track_b_recommendations": []
}
json.dump(t, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
