import json, sys
sys.path.insert(0, 'scripts')
import settlement_checker as sc

f = 'data/tracking/tracking_2026-09-23.json'
t = json.load(open(f, encoding='utf-8'))
D = {'2382': 'D7/10', '2891': 'D6/10', '2377': 'D6/10', '4904': 'D6/10', '5876': 'D5/10', '2395': 'D5/10', '2412': 'D5/10',
     '5880': 'D4/10', '2303': 'D3/10', '2892': 'D3/10', '3711': 'D2/10', '3042': 'D2/10', '2883': 'D1/10', '3481': 'D1/10',
     '2454': 'D1/10', '2886': 'D0/10', '8046': 'D0/10', '2609': 'D0/10', '3023': 'D0/10'}
REV = {'2382': 'L2（-312 張＝2.1%）', '2891': 'L4 8.4%（v8.3.3 待複核②成立）', '2303': '✅健康 +60,104', '2892': '✅健康 +9,287',
       '3711': '✅健康 +10,751', '2886': '✅健康 +8,422', '8046': '✅健康 +5,982', '2609': '✅健康 +3,360',
       '3481': '❓狀態不明（今日+26,643、累計-5,196）'}


def status(code, rec):
    s = sc.get_close_series(code)
    cl = s[-1][1]
    p = rec['recommend_price']
    r = round((cl / p - 1) * 100, 2)
    rec['actual_close'] = cl
    rec['close_price'] = cl
    rec['return_pct'] = r
    rec['change_percent'] = round((cl / s[-2][1] - 1) * 100, 2)
    rec['holding_days'] = D.get(code, rec.get('holding_days'))
    lv = REV.get(code, 'L0 中性')
    if code == '2891':
        rec['holding_status'] = f'⚠️ 待複核②成立（盤後 8.4% ≥5%，12:30 複核① 8.4%）→ 09-24 開盤出場（列 tomorrow_opening_exits）；收盤 {cl}（{r:+.2f}%）'
    else:
        rec['holding_status'] = f'續抱：反轉 {lv}；鐵律①②③ 無觸發；收盤 {cl}（{r:+.2f}%）'
    rec['result'] = 'holding'


for rec in t['recommendations']:
    status(rec['stock_code'], rec)
for rec in t['carry_over_recommendations']:
    c = rec['stock_code']
    if c == '2867':
        rec['holding_status'] = '⏸️ 序列停滯凍結（末日 2026-08-19），不結算、不出場、D 不推進（v8.3.8）'
        continue
    if c == '2883':
        rec.update({'result': 'fail', 'actual_close': 39.35, 'settled_date': '2026-09-23', 'settled_price': 39.35,
                    'return_pct': -2.72, 'holding_days': 'D1/10',
                    'fail_reason': '鐵律③法人反轉 L4（09-22 T86 賣超 -28,639 張＝53.5% 5日均量）→ 09-23 開盤出場，收盤價入帳（v8.3.2）'})
        continue
    status(c, rec)

t['removed_stocks'] = [
    {"stock_code": "2883", "stock_name": "凱基金", "track": "A", "recommend_date": "2026-09-22", "recommend_price": 40.45,
     "settled_price": 39.35, "last_close": 39.35, "return_pct": -2.72, "result": "fail", "holding_days": "D1/10",
     "removal_reason": "鐵律③法人反轉 Level 4（09-22 T86 賣超 -28,639 張＝52.1%（盤前）／53.5%（盤後）5日均量，≥8% 不受 v8.3.3 待複核保護）→ 09-23 開盤出場；收盤價 39.35 入帳（v8.3.2）；非觸及停損（停損 36.41，距停損 +8.1%）",
     "settled_by": "開盤出場清單（盤前 L4，盤後收盤價入帳 v8.3.2）",
     "fail_reason": "法人反轉 L4 強制出場，D1 提前出場，帳面 -2.72%",
     "sync_note": "v8.3.7 三處已同步：①tracking_2026-09-22.json ②本檔 removed_stocks ③predictions.json"},
    {"stock_code": "2330", "stock_name": "台積電", "track": "持倉（my_holdings.yaml 零股 0.15 張）", "recommend_date": "—（yaml 無成本欄）",
     "recommend_price": None, "settled_price": 2500.0, "last_close": 2500.0, "return_pct": None, "result": "持倉出場（不進 predictions）",
     "removal_reason": "鐵律③法人反轉 Level 4（09-22 T86 賣超 -4,268 張＝21.9%／盤後 20.7%，10 日累計 -24K 為負）→ 09-23 開盤出場；收盤價 2500 入帳（v8.3.2）。⚠️ 09-11／09-14 報告已記出場、yaml 仍列 0.15 張 → 實際持有狀態請使用者確認",
     "settled_by": "開盤出場清單（盤前 L4）",
     "sync_note": "持倉部位不進 predictions.json；流程不代改 my_holdings.yaml"}]

t['tomorrow_opening_exits'] = [
    {"stock_code": "2891", "stock_name": "中信金", "category": "鐵律③法人反轉 L4（v8.3.3 待複核定案）", "recommend_date": "2026-09-15",
     "recommend_price": 68.1,
     "reason": "09-22 T86 賣超 -3,329 張；盤前 6.9%（<8% 且 10 日累計 +45K → 列待複核）→ 12:30 複核① 8.4% ≥5% → 盤後複核② 8.4% ≥5%：兩次皆 ≥5% 成立 → 09-24 開盤出場；入帳價依 v8.3.2 用 09-24 收盤價",
     "note": "⚠️ 佔比變動全來自 avg_5day_volume 分母漂移，分子（09-22 T86）一張未變；09-23 T86 於 14:45 仍未公布。依 v8.3.7 已決事項不重評；2026-08-19 否決案「待複核定案後見反向 T86 即撤銷出場」禁止再提 → 明日盤前原樣執行"}]
t['tomorrow_opening_exits_note'] = "本日盤後反轉掃描 21 檔（19 筆追蹤＋2867 凍結＋2330 零股）：L4 3 檔（2883 凱基金、2330 台積電零股已於今日出場；2891 中信金 待複核②成立→明日開盤出場）、L2 1 檔（2382 廣達 2.1%，不出場）、❓狀態不明 1 檔（3481 群創）、❓數據不足 1 檔（2867 三商壽 凍結）；鐵律①停損 0 筆、鐵律② 2 日 -10% 0 筆。⚠️ 掃描仍基於 09-22 T86（09-23 未公布），盤前須以新 T86 重跑。"

t['tomorrow_recommendations'] = [
    {"stock_code": "6770", "stock_name": "力積電",
     "industry": "記憶體／DRAM 代工（industry_chains 記憶體 tier_from_tracker，category=DRAM 與記憶體 → 產業邏輯以 13-16 分計）",
     "recommend_price": 73.1, "target_price": 79.0, "stop_loss_pct": -10, "stop_loss": 65.79, "settlement_days": 10,
     "position": "5-10%（🔥超強催化覆寫，倉位上限 5-10%）", "score": 77, "rating": "⭐⭐⭐", "result": "holding", "track": "A",
     "score_detail": "五維度小計 72 ＝ 時事 21（🔴DRAM與記憶體 基礎 20〔非今日影響鏈點名股，取區間下緣〕＋MU +5.0% 落 +3~+5% 區 +1）＋法人 17（avg_rank 18.0 → TOP11-20；buy_ratio 9.8% <10% 0；09-22 外資 +8,722／投信 -27 不同步 0；真連買 1 天 0）＋產業 14（tier_from_tracker 待審區）＋技術 9（L0 正常型態；10 日 ±75K 大幅震盪、動能爆發非佈局型）＋價位 11（vs MA20 +2.79% 10；月季雙線上 +1）｜modifiers：動能 +328.4% 🔥超強催化覆寫（🔴DRAM）不排除不扣分 0｜5 日 +4.58%（<5%）0｜EPS 2026-06-30 +5｜外資持股比 +5（as_of 09-18，週增>0.5%）｜營收 2026-08 YoY +76.2% 回檔不足 0｜模式追蹤器 記憶體/半導體代工 cold 30% -5",
     "reason": "🛤️軌道A｜🔴超強催化『DRAM與記憶體』↑加速（美光重返千美元、Q3 營收年增逾三倍）→ 🔥超強催化覆寫（動能 +328% 不排除；5日 +4.58% <20%、反轉 L0）｜09-22 T86 +9,321 張（TOP50 #14、avg_rank 18.0）｜10 日累計 +87K、近5天三大法人 +156K／外資 +137K、買7賣3｜反轉 ✅法人買超中｜vs MA20 +2.79%／MA60 +6.63%｜Q2 EPS +5、外資持股比週增>0.5% +5｜與盤前 68 分差異：盤前 5 日 +7.3% 扣 -10，今日 5 日回落至 +4.58% 解除｜⚠️ 法人數據為 09-22 T86（09-23 未公布），預估性質，盤前須重驗｜⚠️ 卷宗矛盾：topic_tracker 🟡『台股市場動態』影響鏈標『力積電↓ 外資賣超最多』（指 09-21 -24K），09-22 T86 已翻買 +9,321；DRAM 主題影響鏈未點名本股｜⚠️ 籌碼劇烈震盪（09-15 -75K、09-18 +89K、09-21 -24K），真連買僅 1 天｜⚠️ 使用者 my_holdings 部位 09-21 已依鐵律①停損出場（入帳 72.70），本推薦為新追蹤、非建議回補"}]
t['tomorrow_carry_over'] = ['2382', '2377', '4904', '5876', '2395', '2412', '5880', '2303', '2892', '3711', '3042',
                            '3481', '2454', '2886', '8046', '2609', '3023', '2867']
t['tomorrow_watchlist'] = ["3045 台灣大（準確率①催化對齊未過，籌碼乾淨：真連買 10 天）",
                           "2885 元大金（動能 +256%，覆寫後五維度仍 <70）",
                           "2354 鴻準（①未過＋外資持股比 -3）",
                           "1102 亞泥（①未過＋營收連 7 月衰退 -5＋水泥 cold）"]
t['after_market'] = {
    "taiex_close": 48157.29, "taiex_change_pct": 0.75, "taiex_source": "Yahoo ^TWII 自行校正（基準 09-22 47,800.17）",
    "t86_today_published": False,
    "t86_note": "14:31、14:45 查詢 09-23 T86 皆『查無數據』→ 明日預測法人數據取自 09-22 T86（memory project_after_market_t86_not_published，n=5）",
    "settled_today": 1, "settled_win": 0, "settled_loss": 1, "settled_accuracy_today": 0.0,
    "holdings_avg_return_pct": 1.43, "holdings_up": "10/18",
    "ironclad_checks": {"stop_loss": "0 筆（18 檔全檢，最近 3481 群創 距停損 +3.6%）",
                        "two_day_drawdown": "0 筆（最差 2883 凱基金 -2.72%）",
                        "reversal_l3_l4": "2883／2330 已於今日出場；2891 待複核②成立 → 09-24 開盤出場",
                        "pending_review": "2891 中信金 定案"},
    "holdings_stop_loss_recheck_v8310": "0 筆新觸發；6770/2337/2313/3090 低於停損為已出場部位重複輸出（yaml 未更新）",
    "target_near": ["3711 日月光投控 693.0／目標 695.0（差 0.29%）", "2303 聯電 160.0／目標 161.0（差 0.62%）",
                    "3042 晶技 198.0／目標 201.0（差 1.5%，盤中漲停 201.5 曾越目標、收盤回落）"],
    "disposition": {"twse_official": ["2305 全友｜09/18~09/30｜第一次處置", "2455 全新｜09/23~10/05｜第二次處置",
                                      "2468 華經｜09/22~10/02｜第一次處置", "6226 光鼎｜09/21~10/01｜第二次處置",
                                      "6715 嘉基｜09/23~10/01｜第一次處置", "8021 尖點｜09/23~10/01｜第二次處置"],
                    "twse_attention": [], "countdown": ["3042 晶技（追蹤中）｜週轉 9.8%｜🟡 接近注意門檻"]},
    "tier_from_tracker_added": 0,
    "diversification_tomorrow": "新推薦 1 檔（記憶體），低於 4-8 檔；依 v8.2 禁止湊數",
    "yesterday_prediction_check": "09-22 盤後預估 2885 元大金／3045 台灣大，09-23 盤前以新 T86 撤下；今日 2885 -1.42%、3045 0.00%"}
t['yesterday_verification'] = {
    "date": "2026-09-23", "accuracy": 0.0, "settled_count": 1, "success_count": 0, "fail_count": 1,
    "note": "當日結算 1 筆（2883 凱基金 L4 出場 -2.72%）；2330 台積電零股為持倉出場不計。持有中 18 筆＋2867 凍結不計入分母。",
    "results": [{"stock_code": "2883", "stock_name": "凱基金", "recommend_date": "2026-09-22", "recommend_price": 40.45,
                 "settled_price": 39.35, "return_pct": -2.72, "result": "fail", "reason": "鐵律③ L4 開盤出場，收盤價入帳；非觸及停損"}]}
json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
