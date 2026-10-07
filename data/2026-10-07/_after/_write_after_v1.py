import json
T = 'data/tracking/tracking_2026-10-07.json'
S = 'data/tracking/tracking_2026-10-06.json'
t = json.load(open(T, encoding='utf-8'))
json.dump(t, open('data/2026-10-07/_after/tracking_before_after.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

closes = {'3711': (732.0, -1.61, 4), '3035': (209.0, -0.71, 3), '1326': (75.8, 3.84, 2), '2308': (1990.0, -2.93, 1),
          '2330': (2585.0, 0.00, 1), '3443': (8460.0, 1.01, 1), '3231': (185.0, -2.37, 1), '3661': (4190.0, 0.24, 1),
          '2344': (179.5, 1.13, 1), '2404': (1330.0, -0.37, 0), '2609': (59.1, -0.17, 0)}
t86 = {'3711': '+276（L0）', '3035': '+780（L0）', '1326': '+13,567（買超中）', '2308': '+853（L0）', '2330': '-1,299（L4 6.1%）',
       '3443': '+101（L0）', '3231': '-4,981（L4 13.1%）', '3661': '+885（L0）', '2344': '-3,830（L4 5.2%）', '2404': '+571（L0）',
       '2609': '+5,303（買超中）'}


def fill(r):
    c = r['stock_code']
    if c not in closes:
        return
    close, chg, d = closes[c]
    rp = r['recommend_price']
    r['close_price'] = close
    r['actual_close'] = close
    r['change_percent'] = chg
    r['return_pct'] = round((close / rp - 1) * 100, 2)
    r['holding_days'] = d
    r['holding_days_label'] = 'D%d/10' % d
    r['result'] = 'holding'
    r['holding_status'] = ('D%d/10；10-07 收 %s（今日 %+.2f%%，相對推薦價 %+.2f%%）；距目標 %.1f%%／距停損 %.2f%%；10-06 T86 %s（10-07 T86 盤後 14:30~ 未公布）'
                           % (d, close, chg, r['return_pct'], (r['target_price'] / close - 1) * 100, (1 - r['stop_loss'] / close) * 100, t86[c]))


for r in t['recommendations']:
    fill(r)
for r in t.get('carry_over_recommendations', []):
    if r['stock_code'] == '2867':
        r['result'] = 'holding'
        r['holding_status'] = '⚠️ 序列停滯（末日 2026-08-19）凍結判定（v8.3.8）'
        continue
    fill(r)

for p in t['pending_review_v833']:
    if p['stock_code'] == '2330':
        p['review_2_result'] = '盤後 reversal_alert（完整日量，仍為 10-06 T86：10-07 T86 未公布）賣超佔比 6.1% ≥5% → 複核②成立；兩次皆 ≥5% → 10-08 開盤出場（入帳價用 10-08 收盤，v8.3.2）'
        p['review_2_price'] = 2585.0
        p['review_2_ratio'] = 6.1
    if p['stock_code'] == '2344':
        p['review_2_result'] = '盤後 reversal_alert（完整日量，仍為 10-06 T86）賣超佔比 5.2% ≥5% → 複核②成立；兩次皆 ≥5% → 10-08 開盤出場（入帳價用 10-08 收盤，v8.3.2）'
        p['review_2_price'] = 179.5
        p['review_2_ratio'] = 5.2
    p['status'] = '🛑 待複核成立（複核①②皆 ≥5%）→ 10-08 開盤出場'
    p['review_2_time'] = '2026-10-07 14:40'
    p['caveat'] = '兩次複核皆基於同一份 10-06 T86（10-07 T86 盤後尚未公布），佔比差異全來自 avg_5day_volume 分母滾動；若 10-07 T86 公布後重掃翻買，依 v8.3.7 已決事項仍於 10-08 開盤出場（已決事項不重評）'

rem = {"stock_code": "3231", "stock_name": "緯創", "track": "A", "recommend_date": "2026-10-06", "recommend_price": 189.5,
       "settled_price": 185.0, "last_close": 185.0, "return_pct": -2.37, "result": "fail", "holding_days": "D1/10",
       "removal_reason": "鐵律③ L4（10-06 T86 賣超 -4,981 張＝12.9%~13.1% ≥8% 且 10 日累計 -1,578 為負，不受 v8.3.3 保護）→ 10-06 盤後定案、10-07 開盤出場（v8.3.7 已決事項，不重評）；收盤價 185.0 入帳（v8.3.2），低於推薦價故記 fail",
       "fail_reason": "鐵律③ L4 已決事項開盤出場；10-07 收 185.0（-2.37%）",
       "settled_by": "已決事項開盤出場（v8.3.7 Step 4-0，10-06 盤後定案；盤後收盤價入帳 v8.3.2）", "settled_date": "2026-10-07",
       "sync_note": "v8.3.7 三處同步：①tracking_2026-10-06.json ②本檔 removed_stocks ③predictions.json"}
t['removed_stocks'] = [rem]
t['settlement_today'] = {"settled": [{"stock_code": "3231", "stock_name": "緯創", "recommend_date": "2026-10-06", "recommend_price": 189.5, "settled_price": 185.0, "return_pct": -2.37, "result": "fail", "settled_by": "已決事項開盤出場（鐵律③ L4）"}],
                         "holding_count": 10, "frozen": ["2867"], "d_counts_source": "settlement_checker 2026-10-07 盤後輸出照抄（序列末日 10-07）"}
t['yesterday_verification'] = {"date": "2026-10-07", "settled_count": 1, "success": 0, "fail": 1, "accuracy": 0.0,
                               "note": "今日結算 1 筆：已決事項鐵律③ L4 開盤出場 3231 緯創（10-06 盤後定案）；入帳價 10-07 收盤 185.0（v8.3.2）；settlement_checker 機械判定 0 筆（1326 台化 距目標 2.1%、3661 世芯-KY 距目標 1.8% 未達）；holding 不計入分母",
                               "results": [{"stock_code": "3231", "stock_name": "緯創", "recommend_date": "2026-10-06", "recommend_price": 189.5, "settled_price": 185.0, "return_pct": -2.37, "result": "fail", "holding_days": "D1/10", "settled_by": "已決事項開盤出場（v8.3.7 Step 4-0，10-06 盤後定案；盤後收盤價入帳 v8.3.2）"}],
                               "cumulative": None}
t['market_close'] = {"taiex": 49806.37, "taiex_change_pct": -0.03, "taiex_change": -16.18, "prev_close": 49822.55,
                     "source": "Yahoo ^TWII chart 日K 2026-10-07 09:00 列（regularMarketPrice 49,806.37，13:33）",
                     "turnover": "FMTQIK 10-07 盤後 14:3x 未公布", "institutional_total": "BFI82U 10-07 盤後 14:3x 未公布（n=9：14:30 前皆未公布）"}
t['stop_loss_check_after_v8310'] = {"time": "2026-10-07 14:33", "basis": "get_close_series 末筆＝2026-10-07 收盤（序列對齊）", "results": [
    {"stock_code": "2330", "stock_name": "台積電", "close": 2585.0, "stop_loss": None, "hit": "不適用（yaml 無 stop_loss）", "pl_pct": 24.88},
    {"stock_code": "6770", "stock_name": "力積電", "close": 72.6, "stop_loss": 73.26, "hit": "🛑 觸及停損（收盤 72.6 < 73.26，-10.81%）—— 本波首度收盤跌破（10-05 75.8／10-06 74.3）；10-05 盤後已決 L4 出場、10-06／10-07 連續 L4 13.9%", "pl_pct": -10.81},
    {"stock_code": "2337", "stock_name": "旺宏", "close": 118.0, "stop_loss": 147.6, "hit": "🛑 觸及停損（-28.05%，重複輸出：流程已出場、yaml 未更新）", "pl_pct": -28.05},
    {"stock_code": "2313", "stock_name": "華通", "close": 246.0, "stop_loss": 235.98, "hit": "✅ 未觸發（+4.25%）", "pl_pct": -6.18},
    {"stock_code": "3090", "stock_name": "日電貿", "close": 174.0, "stop_loss": 256.5, "hit": "🛑 觸及停損（-38.95%，重複輸出：yaml 未更新）", "pl_pct": -38.95},
    {"stock_code": "1301", "stock_name": "台塑", "close": 75.4, "stop_loss": 54.08, "hit": "✅ 未觸發（+39.42%）；損益 +25.49% 超過 yaml take_profit_percent 20%（無鐵律，提示）", "pl_pct": 25.49},
    {"stock_code": "4938", "stock_name": "和碩", "close": 90.0, "stop_loss": 76.5, "hit": "✅ 未觸發（+17.65%）；10-05 盤後已決 L4 出場（yaml 未更新）", "pl_pct": 5.88}],
    "new_triggers": 1, "new_trigger_codes": ["6770"]}
t['two_day_drawdown_check_after'] = {"basis": "10-05 收盤 → 10-07 收盤（get_close_series 末 3 筆）", "triggered": [],
                                     "worst": [{"stock_code": "6770", "stock_name": "力積電", "pct": -4.22}, {"stock_code": "3035", "stock_name": "智原", "pct": -3.24}, {"stock_code": "2337", "stock_name": "旺宏", "pct": -2.88}, {"stock_code": "3231", "stock_name": "緯創", "pct": -2.37}],
                                     "note": "17 檔（追蹤 11＋持倉 7，去重）無 >-10%"}
t['series_alignment_check_after_v838'] = {"expected_last_day": "2026-10-07", "aligned": ["3711", "3035", "1326", "2308", "2330", "3443", "3231", "3661", "2344", "2404", "2609", "6770", "2337", "2313", "3090", "1301", "4938"],
                                          "stale": [{"stock_code": "2867", "stock_name": "三商壽", "last_day": "2026-08-19", "action": "凍結判定：不結算、不出場、D 不推進"}]}
t['holdings_reversal_scan_after'] = {"basis": "reversal_alert 17 檔，盤後完整日量；法人資料仍為 10-06 T86（10-07 T86 未公布）", "L4": [
    {"stock_code": "2330", "stock_name": "台積電", "ratio": 6.1, "sell": -1299}, {"stock_code": "3231", "stock_name": "緯創", "ratio": 13.1, "sell": -4981},
    {"stock_code": "2344", "stock_name": "華邦電", "ratio": 5.2, "sell": -3830}, {"stock_code": "6770", "stock_name": "力積電", "ratio": 13.9, "sell": -16606}],
    "L2": [{"stock_code": "2337", "stock_name": "旺宏", "ratio": 3.4, "sell": -620}], "unknown": [{"stock_code": "4938", "stock_name": "和碩", "note": "+958，累計 -5,786"}],
    "healthy": ["1326", "2609", "2313", "1301"], "L0": ["3711", "3035", "2308", "3443", "3661", "2404", "3090"]}
t['tomorrow_opening_exits'] = [
    {"stock_code": "2330", "stock_name": "台積電", "category": "鐵律③ L4（v8.3.3 待複核兩次皆 ≥5%）", "recommend_date": "2026-10-06", "recommend_price": 2575.0, "last_close": 2585.0, "return_pct_at_close": 0.39,
     "reason": "10-06 T86 賣超 -1,299 張（外資 -1,673／投信 -22／自營 +395）；佔比 盤前 5.8% → 12:30 6.1% → 盤後 6.1%，複核①②皆 ≥5%（10 日累計 +7,571 為正，故走待複核程序而非即時出場）→ 10-08 開盤出場，入帳價用 10-08 收盤（v8.3.2）",
     "decided_on": "2026-10-07 盤後（v8.3.3 複核②）", "caveat": "複核①②皆基於同一份 10-06 T86（10-07 T86 盤後未公布）；10/8 公布 9 月營收。已決事項不重評。另：my_holdings.yaml 持倉 2330 零股 0.15 張（無 stop_loss）同樣適用本決議"},
    {"stock_code": "2344", "stock_name": "華邦電", "category": "鐵律③ L4（v8.3.3 待複核兩次皆 ≥5%）", "recommend_date": "2026-10-06", "recommend_price": 181.0, "last_close": 179.5, "return_pct_at_close": -0.83,
     "reason": "10-06 T86 賣超 -3,830 張（外資 +7,287／投信 -10,812／自營 -305）；佔比 盤前 5.4% → 12:30 5.2% → 盤後 5.2%，複核①②皆 ≥5%（10 日累計 +28,132 為正）→ 10-08 開盤出場，入帳價用 10-08 收盤（v8.3.2）；🔥覆寫型 D0 即轉 L4（第 14 筆）",
     "decided_on": "2026-10-07 盤後（v8.3.3 複核②）", "caveat": "同上；覆寫型停損 171.95 距 4.2%"},
    {"stock_code": "6770", "stock_name": "力積電", "category": "持倉 my_holdings.yaml（鐵律① 觸及停損 ＋ 已決 L4）", "recommend_date": None, "recommend_price": 81.4, "last_close": 72.6, "return_pct_at_close": -10.81,
     "reason": "10-07 收盤 72.6 < 停損 73.26（v8.3.10 Step 4-1 本波首度收盤跌破）；且 10-05 盤後已決 L4 出場、10-06／10-07 連續 L4 13.9%（-16,606 張）。不進 predictions；流程不代改 yaml，若實際仍持有 10-08 開盤出場",
     "decided_on": "2026-10-07 盤後"}]
t['tomorrow_pending_review'] = []
t['l4_exit_direction_check'] = {"note": "10-07 出場 3231 緯創（追蹤）執行日 T86 需 10-07 T86 公布後補填（v1 未公布）", "pending": ["3231"]}
t['tomorrow_recommendations'] = []
t['tomorrow_recommendation_note'] = ("v1（10-07 T86 盤後 14:30~ 未公布，法人資料＝10-06 T86，與盤前同一份）：候選池與盤前相同，盤前已於此份資料推薦 2404 漢唐／2609 陽明，觀察名單 10 檔再核：2408 南亞科 MA20 +1.0% 落 0~+5% 且不在 TOP50 買超 → 法人現身門檻仍未過，另 10/12 線上法說（窗口內）；2412 中華電／2892 第一金／2436 偉詮電／1513 中興電 ①催化未對齊；2891 中信金／2382 廣達／6505 台塑化 ②外資近 5 天 <0；3037 欣興 5 日 +12.45%／6196 帆宣 +21.9% 已大漲 → 10-08 新推薦 0 檔（寧缺勿濫）。"
                                     "10-07 T86 若公布則以 v2 重評。10/9 補假、10/10-10/12 連休，10-08 進場持有期跨長假。")
t['tomorrow_carry_over'] = [
    {"stock_code": "2404", "stock_name": "漢唐", "recommend_date": "2026-10-07", "recommend_price": 1335.0, "stop_loss": 1201.5, "target_price": 1441.8, "holding_days": "D0/10"},
    {"stock_code": "2609", "stock_name": "陽明", "recommend_date": "2026-10-07", "recommend_price": 59.2, "stop_loss": 56.24, "target_price": 63.94, "holding_days": "D0/10"},
    {"stock_code": "3711", "stock_name": "日月光投控", "recommend_date": "2026-10-01", "recommend_price": 703.0, "stop_loss": 632.7, "target_price": 759.0, "holding_days": "D4/10"},
    {"stock_code": "3035", "stock_name": "智原", "recommend_date": "2026-10-02", "recommend_price": 213.0, "stop_loss": 191.7, "target_price": 230.0, "holding_days": "D3/10"},
    {"stock_code": "1326", "stock_name": "台化", "recommend_date": "2026-10-05", "recommend_price": 71.7, "stop_loss": 64.53, "target_price": 77.4, "holding_days": "D2/10"},
    {"stock_code": "2308", "stock_name": "台達電", "recommend_date": "2026-10-06", "recommend_price": 2005.0, "stop_loss": 1804.5, "target_price": 2165.4, "holding_days": "D1/10"},
    {"stock_code": "3443", "stock_name": "創意", "recommend_date": "2026-10-06", "recommend_price": 8600.0, "stop_loss": 7740.0, "target_price": 9288.0, "holding_days": "D1/10"},
    {"stock_code": "3661", "stock_name": "世芯-KY", "recommend_date": "2026-10-06", "recommend_price": 3950.0, "stop_loss": 3555.0, "target_price": 4266.0, "holding_days": "D1/10"},
    {"stock_code": "2867", "stock_name": "三商壽", "recommend_date": "2026-08-17", "recommend_price": 9.75, "stop_loss": 8.78, "target_price": 10.73, "holding_days": "凍結（序列停滯 08-19）"}]
t['watchlist_tomorrow'] = ["2408 南亞科（門檻未過；10/12 法說）", "2412 中華電", "2436 偉詮電（營收 +5／持股比 -3）", "2892 第一金", "1513 中興電", "2891 中信金", "2382 廣達", "6505 台塑化", "3037 欣興", "6196 帆宣"]
t['disposition_after'] = {"time": "2026-10-07 14:36", "source": "reversal_alert.fetch_twse_lists()（首呼叫成功）",
                          "disposition": ["2030 彰源", "2033 佳大", "3016 嘉晶", "3055 蔚華科", "3094 聯傑", "3167 大量", "3518 柏騰", "6533 晶心科", "6672 騰輝電子-KY", "8201 無敵", "8996 高力"], "attention": [],
                          "note": "持倉／追蹤 17 檔無處置股；自算預警沿用盤中：6213 聯茂 最快明日處置、1709 和益 剩 2 天"}
t['data_quality_after'] = [
    "10-07 T86 盤後 14:30~14:40 未公布（n=9）；本檔所有反轉等級／佔比／T86 欄位皆為 10-06 T86；BFI82U／FMTQIK 10-07 亦未公布",
    "preflight_check.py 於 D10 檢查崩潰：盤前把 holding_days 寫成字串 'D2/10'（腳本以 >= 10 比較）→ 已把 tracking 內 holding_days 改為整數並另存 holding_days_label（資料修正，未改腳本）",
    "holdings_pressure_analysis 法人欄恆 0、漏 4938 和碩（已知缺陷），僅採損益欄",
    "stock_dossier_tomorrow：三來源 ok；2308 台達電 10-05 Jefferies 法說（已過）＋今日重訊（子公司 Eltek 股東臨時會）；3711 今日重訊（代子公司公告）；2408 南亞科 10-12 線上法說（5 天後）；3035 智原／2436 偉詮電／2892 第一金 mentions=0",
    "盤後因子檢查（20 檔）：營收 20/20 為 2026-08 ✅；外資持股比 as_of 09-30~10-06 ✅；價格位置以 10-07 收盤計；四份盤前 JSON 已從 _after/premarket_backup 還原"]
t['after_market_version'] = 'v1（10-07 T86 未公布）'
json.dump(t, open(T, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

s = json.load(open(S, encoding='utf-8'))
json.dump(s, open('data/2026-10-07/_after/tracking_1006_before.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
n = 0
for r in s['recommendations']:
    if r['stock_code'] == '3231':
        r.update({"result": "fail", "actual_close": 185.0, "close_price": 185.0, "settled_date": "2026-10-07", "settled_price": 185.0, "return_pct": -2.37,
                  "fail_reason": "鐵律③ L4 已決事項（10-06 盤後定案）10-07 開盤出場；入帳 10-07 收盤 185.0（v8.3.2），-2.37%",
                  "sync_note": "2026-10-07 盤後 v8.3.7 三處同步：①本檔 ②tracking_2026-10-07.json removed_stocks ③predictions.json"})
        n += 1
json.dump(s, open(S, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('source updated', n)
