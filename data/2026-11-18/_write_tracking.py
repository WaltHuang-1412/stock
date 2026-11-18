import json, copy

D = '2026-11-18'
y = json.load(open('data/tracking/tracking_2026-11-17.json', encoding='utf-8'))
carry = {c['stock_code']: c for c in y['carry_over_recommendations']}
src_2886 = y['recommendations'][0]

upd = {
    '5876': (6, 'D6/10', 'D6；L0（今日 +2,250 張、真連買 5 天、10日累計 +10,002 張）；11/20 法說（D9）→ 續抱，法說前評估減碼', 'L0', '續抱'),
    '2412': (3, 'D3/10', 'D3；L4（11-17 T86 -3,151 張，佔日均量 26.6%≥8%）→ 已決事項：11/18 開盤出場，入帳價用 11-18 收盤', 'L4', '開盤出場（已決事項）'),
    '2801': (2, 'D2/10', 'D2；reversal 狀態不明（今日 +710 張、累計 -312 張）；距停損 9.2%、未觸鐵律 → 續抱並列觀察', '狀態不明', '續抱（觀察）'),
    '2884': (1, 'D1/10', 'D1；L4（11-17 T86 -3,291 張，佔日均量 10.1%≥8%）→ 已決事項：11/18 開盤出場；11/18 16:30 法說', 'L4', '開盤出場（已決事項）'),
    '4904': (1, 'D1/10', 'D1；L0（11-17 T86 +576 張、10日累計 +11,998 張；待複核已降級）；11/19 法說（明日）→ 續抱，法說前後雙向波動', 'L0', '續抱'),
}
settle_px = {'5876': 53.3, '2412': 164.5, '2801': 28.15, '2884': 46.65, '4904': 108.5}
co = []
for k, (d, lab, st, rev, strat) in upd.items():
    c = copy.deepcopy(carry[k])
    for f in ['intraday_price', 'intraday_change_pct', 'intraday_return_pct', 'intraday_time',
              'intraday_reversal', 'intraday_strategy', 'actual_close', 'close_price', 'return_pct', 'change_percent']:
        c.pop(f, None)
    c['holding_days'] = d
    c['holding_days_label'] = lab
    c['holding_status'] = st
    c['reversal_today'] = rev
    c['strategy_today'] = strat
    c['prev_close'] = settle_px[k]
    c['prev_close_return_pct'] = round((settle_px[k] / c['recommend_price'] - 1) * 100, 2)
    c['result'] = 'holding'
    co.append(c)

r2886 = {k: src_2886[k] for k in ['stock_code', 'stock_name', 'industry', 'recommend_date', 'recommend_price',
                                   'target_price', 'stop_loss_pct', 'stop_loss', 'settlement_days', 'position',
                                   'track', 'entry_condition']}
r2886.update({
    'score': 106, 'result': 'holding', 'carry_over': True,
    'reason': '⏳沿用進行中追蹤（維持原進場價 54.5／停損 49.05 不變，不重複建倉；D 天數照抄 settlement_checker：D0，11-17 收盤計）。今日重評 106 分：TOP50 第12（avg_rank 18.0，今日 +3,555 張）、真連買 10 天、10日累計 +61K、外資5日 +41K、L0；Fed 升息金融鏈＋「AI以外資金輪動」中↑；月線上 +1.0%。⚠️ 今日（11/18）公告 Q3 財報（財報公布日，不加碼）；投信近期賣超；空頭局勢。',
    'score_breakdown': {'時事': 15, '法人': 19, '產業': 17, '技術': 14, '價格位置': 11, '動能': 15,
                        '訊號A_L3': 15, 'EPS': 0, '營收': 0, '外資持股比': 0},
    'holding_days': 0, 'holding_days_label': 'D0/10',
    'holding_status': 'D0；L0（今日 +3,222 張、真連買 10 天、10日累計 +61K）→ 續抱；11/18 公告 Q3 財報',
    'prev_close': 54.7, 'prev_close_return_pct': 0.37, 'reversal_today': 'L0', 'strategy_today': '續抱'})

r2892 = {
    'stock_code': '2892', 'stock_name': '第一金',
    'industry': '金融（金控；industry_chains 僅登錄 tier_from_tracker 待審區，產業邏輯一律 13-16）',
    'recommend_date': D, 'recommend_price': 42.1, 'target_price': 45.47, 'stop_loss_pct': -10, 'stop_loss': 37.89,
    'settlement_days': 10, 'position': '5%', 'score': 99, 'track': 'A', 'result': 'holding',
    'entry_condition': '開盤價>43.36（+3%）不買',
    'reason': '🛤️軌道A（法人）＋📶訊號A（預埋）L3｜TOP50 第20（avg_rank 26.0，今日 +2,475 張）；真連買 10 天、10日累計三大 +41K、外資5日 +25K、10日賣超 0 天；反轉 L0；動能 -45.5%（佈局完成）；Fed 升息金控鏈（超強）↑；月線 -0.8%、季線上 +6.7%。基礎五維度 69（<70），總分靠動能 +15 與訊號A L3 +15 兩項達 99（結構性膨脹，已知）。⚠️ 投信近5日 -16K 且今日 -6,922 張、外資撐盤；營收年減 3.2%；EPS 快取為 Q2（金融 Q3 未公布，視為0）；金融集中（追蹤 5876/2801/2886）；空頭局勢降倉 5%；賺賠比 0.8:1（開盤高3%才買剩 +4.8%）',
    'score_breakdown': {'時事': 20, '法人': 14, '產業': 14, '技術': 13, '價格位置': 8, '動能': 15,
                        '訊號A_L3': 15, 'EPS': 0, '營收': 0, '外資持股比': 0},
    'dossier': '法說會／除權息／重大訊息無事件，三來源 ok；mentions 皆為產業鏈名單／MI 表格列，無利空'}

exits = [
    ('2412', '中華電', '追蹤（已決事項）', '鐵律③ L4（11-17 T86 -3,151 張，26.6%）'),
    ('2884', '玉山金', '追蹤（已決事項）', '鐵律③ L4（11-17 T86 -3,291 張，10.1%）'),
    ('6770', '力積電', '持倉（已決事項）', '鐵律① 收盤 51.5<停損 73.26；今日仍 L3（近2日 -12,742 張）'),
    ('2337', '旺宏', '持倉（已決事項）', '鐵律① 收盤 71.9<停損 147.6；今日 +2,051 張但 10 日累計為負、狀態不明'),
    ('2313', '華通', '持倉（已決事項）', '鐵律① 收盤 184.5<停損 235.98；今日 L3、TWSE 注意股'),
    ('3090', '日電貿', '持倉（已決事項）', '鐵律① 收盤 118.5<停損 256.5；今日 L0'),
    ('1301', '台塑', '持倉（已決事項）', '11-06 出場決議原樣沿用；收盤 67.5>停損 54.08；今日法人 +3,266 張（健康）'),
    ('4938', '和碩', '持倉（已決事項）', '11/12 法說會後維持已決；收盤 83.8>停損 76.5；今日 L3（近2日 -139 張）'),
    ('2330', '台積電零股', '持倉（已決事項）', 'L4（今日賣超 -5,508 張，16.5%）；原樣沿用'),
]

t = {
    'date': D, 'version': 'v8.3.11', 'phase': 'before_market',
    'settings': {'stop_loss_pct': -10, 'settlement_days': 10},
    'market_context': '美股 11/17：S&P -1.03%（連四黑、跌破200日線）、NASDAQ -0.74%、費半 +0.34%（止跌）、VIX 水位 25.46（+11.13%，連四日創高；us_asia_markets.json 的 VIX=11.13 是漲跌幅非水位，已於源頭新增 VIX水位 欄）；台積電 ADR -4.45%；NVDA 盤後財報 Q3 營收 1,158 億美元，盤後 +2~4%。台股 11/17 收 40,092（-948 點、-2.31%；兩日 -3,583 點），外資 -380.9 億。MI regime=空頭(score -3)，月線乖離 -8.85%、季線 -12.93%、年線 +2.10%。11/18 為台指期結算日、台積電新加坡／日月光投控等法說。AI泡沫階段（MI）破裂確認，不參與評分。',
    'defense_ratio': '空頭局勢防禦 40-60%（VIX 25.5＋超強催化依表為 15-25%，取較嚴者）；今日推薦皆為金融防禦型，單一產業 100% 偏離 ≤50% 規則（寧缺勿濫、不湊數）',
    'recommendations': [r2886, r2892],
    'carry_over': ['5876', '2412', '2801', '2884', '4904'],
    'carry_over_recommendations': co,
    'opening_exits_today': [{'stock_code': a, 'stock_name': b, 'category': c, 'reason': d} for a, b, c, d in exits],
    'removed_stocks': [],
    'track_b_recommendations': [],
    'track_b_observations': [
        '軌道B 展開（Fed 升息金控鏈／中東航運／電信防禦）：2881、2615、3045、2834 為 L4；2890、2885、6505、2880、2603 動能>100% 或累計為負；2637 累計僅 +840 張；0 檔可推'],
    'stale_series': [{'symbol': '2867', 'name': '三商壽', 'note': '推薦日 2026-08-17；get_close_series 查詢失敗（併購停牌），凍結判定、不結算、D 計數不推進'}],
    'pending_review': [],
    'tomorrow_opening_exits': [],
    'watchlist': [
        {'stock_code': '2610', 'stock_name': '華航', 'note': '訊號A L3、真連買10天、外資5日 +74K、L0；但 11/18 14:00 法說會（當日不開新倉）；估分約 110（基礎 75＋動能15＋L3 15＋EPS 5）'},
        {'stock_code': '2618', 'stock_name': '長榮航', 'note': '訊號A L2；篩選①催化對立（中東鏈標「↓ 油價成本」，今日 Brent +1.77%）；估分約 90'},
        {'stock_code': '2887', 'stock_name': '台新新光金', 'note': '昨日 L4、今日 L0（+6,763 張）反覆；月季線雙下、營收年減 14.6%；基礎約 60'},
        {'stock_code': '2883', 'stock_name': '凱基金', 'note': '昨日 L4、今日 L0；月季線雙下、營收年減 51%；基礎約 62'},
        {'stock_code': '1101', 'stock_name': '台泥', 'note': '動能 -78%、EPS +5，但基礎約 68、外資5日僅 +987 張、催化僅中度'}],
    'data_quality': {
        'vix_field_fix': 'fetch_us_asia_markets.py 新增 VIX水位 欄（原 VIX 欄為漲跌幅%）',
        'eps_cache_financials': '金融股 EPS 快取為 Q2，視為 0',
        'revenue_cache': '15 檔皆 2026-10',
        'foreign_ratio': '15 檔皆 ≥2026-11-11'},
}
json.dump(t, open(f'data/tracking/tracking_{D}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(t['recommendations']), len(co))
