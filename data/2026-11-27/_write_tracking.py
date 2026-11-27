"""建立 2026-11-27 盤前 tracking（已決事項與沿用追蹤自前一日檔案抄錄）"""
import json

D = '2026-11-27'
prev = json.load(open('data/tracking/tracking_2026-11-26.json', encoding='utf-8'))


def rec(code, name, ind, price, score, pos, reason, entry, breakdown):
    return {
        'stock_code': code, 'stock_name': name, 'industry': ind, 'recommend_price': price,
        'target_price': round(price * 1.08, 2), 'stop_loss_pct': -10, 'stop_loss': round(price * 0.9, 2),
        'settlement_days': 10, 'position': pos, 'score': score, 'result': 'holding', 'holding_days': 0,
        'holding_days_label': 'D0/10', 'entry_rule': entry, 'score_breakdown': breakdown, 'reason': reason,
    }


recs = [
    rec('2880', '華南金', '金融', 44.2, 90, '5-10%',
        '11-26 三大法人 +3,257 張（外資 +10,234、投信 -9,665），外資 5 日 +14K 張、10 日累計 +9,052 張；反轉 L0、動能 -104.6%(+15)；'
        '訊號A L2(+10)；聯準會利率超強催化影響鏈↑、11-26 法說：前 10 月稅後 284.56 億（年增 +26.85%）超越去年全年；'
        'MA20 -9.2%／MA60 -6.5%、5 日 -9.5%。弱點：真連買僅 1 天、投信 5 日 -29K 張、11-25 才爆量賣超 -8,594 張、'
        '10 月營收年增僅 +2.8%、所屬金控壽險主題標營收未跟上、90 分中 25 分來自加減分',
        '參考昨收；開盤高於 45.5（+3%）不追；開盤低於停損價 39.78 不進場',
        {'時事': 21, '法人': 15, '產業': 16, '技術': 10, '價格位置': 3, '動能': 15, '營收': 0, 'EPS': 0, '外資持股比': 0, '訊號A': 10}),
    rec('2603', '長榮', '航運', 254.0, 78, '5-10%',
        '中東地緣超強催化航運鏈↑、油價續揚；外資 5 日 +39K 張、三大法人真連買 3 天；反轉 L0、動能 -15%(+10)；'
        '10 月營收年增 +96.1%（回檔不足不加分）、Q3 EPS 21.53 年增 +114%(+5)；MA20 -0.4%／MA60 +2.4%。'
        '弱點：11-26 三大法人僅 +76 張（外資 +13,006、投信 -13,284 對作）、投信 5 日 -38K 張、不在 TOP50 買超、法人分數僅 6、11-29 OPEC+ 會議',
        '參考昨收；開盤高於 261.5（+3%）不追；開盤低於停損價 228.6 不進場',
        {'時事': 22, '法人': 6, '產業': 15, '技術': 12, '價格位置': 8, '動能': 10, '營收': 0, 'EPS': 5, '外資持股比': 0}),
]

# 沿用追蹤：自推薦日來源檔抄錄進場價／停損，D 照抄 settlement_checker
SRC = [('2610', '2026-11-19', 5, '已決：次日開盤出場（11-26 L4）'),
       ('2412', '2026-11-20', 4, '續抱不加碼'),
       ('2379', '2026-11-26', 0, '續抱'),
       ('2615', '2026-11-26', 0, '已決：次日開盤出場（11-26 L4）')]
carry = []
for code, rd, days, action in SRC:
    src = json.load(open(f'data/tracking/tracking_{rd}.json', encoding='utf-8'))
    r = next(x for x in src['recommendations'] if x['stock_code'] == code)
    carry.append({
        'stock_code': code, 'stock_name': r['stock_name'], 'recommend_date': rd,
        'recommend_price': r['recommend_price'], 'target_price': r['target_price'],
        'stop_loss_pct': r['stop_loss_pct'], 'stop_loss': r['stop_loss'], 'settlement_days': r['settlement_days'],
        'score': r.get('score'), 'result': 'holding', 'holding_days': days, 'holding_days_label': f'D{days}/10',
        'note': f'⏳沿用 D{days}/10（settlement_checker 輸出），維持原進場價與停損價，不重複建倉；{action}',
    })

exits = prev['tomorrow_opening_exits']

watch = [
    ('2618', '長榮航', 95, '催化對齊未過：中東超強鏈對航空是油價成本逆風（流程判讀）；若認定對齊則為今日最高分'),
    ('2891', '中信金', 87, '通過三篩，單一產業≤50% 由 2880 取代；11-30 法說；營收兩資料源衝突'),
    ('2636', '台驊控股', 83, '法人現身門檻（不在 TOP50 買超且月線乖離 +0.4%）'),
    ('3706', '神達', 82, '11-27 除權（現金增資認股 8.22%、認購價 52），盤前不建檔'),
    ('8046', '南電', 82, '11-27 14:30 法說，當天不開新倉'),
]

t = {
    'date': D, 'version': 'v8.3.11', 'phase': 'before_market',
    'settings': {'stop_loss_pct': -10, 'settlement_days': 10},
    'market_context': {
        'regime': '恐慌', 'score': -5, 'defense_ratio': '60-75%', 'taiex_1126_close': 39151.81, 'taiex_1126_pct': 2.5,
        'vs_ma240_pct': -1.13, 'vs_ma20_pct': -4.87, 'vix': 26.8, 'foreign_1126_net_100m': -491.81,
        'total_inst_1126_net_100m': -132.65, 'us_session': '2026-11-25（11-26 感恩節休市）', 'bubble_stage': '惡化',
    },
    'recommendations': recs,
    'carry_over': [c['stock_code'] for c in carry],
    'carry_over_recommendations': carry,
    'opening_exits_today': exits,
    'track_b_recommendations': [],
    'stale_series': ['2867 三商壽（併購停牌，序列查詢失敗，凍結判定）'],
    'watchlist': [{'stock_code': a, 'stock_name': b, 'score': c, 'reason': d} for a, b, c, d in watch],
    'not_recommended_reasons': {
        '6505': '②外資5日賣超', '9933': '①催化未對齊', '2317': '②外資5日賣超;③非L0', '2883': '②外資5日賣超',
        '2609': '②外資5日賣超', '1101': '①②', '3045': '①②', '1301': '已決出場', '3006': '①②③', '2382': '②外資5日賣超',
    },
    'data_quality': {
        't86': '2026-11-26（11-27 08 時依 TWSE 修訂版刷新 11-09～11-26 快取）', 'revenue_month': '2026-10',
        'eps': '2026-09-30；2882 國泰金、2892 第一金停在 06-30，EPS 視為 0', 'foreign_ratio': '2026-11-20～11-26',
        'script_fix': 'twse_institutional_cache.py：資料日當天寫入的初版快取，隔日起重抓一次',
        'conflict': '2891 中信金營收：check_revenue_yoy 10 月年增 -27.2%，market_intelligence 表列 +12.8%',
    },
    'preflight_notes': '缺檔 8 項為分析前正常狀態（已補齊）；daily.sh 字面比對誤報（已知）；軌道B 深度展開缺席警告（本日已展開）',
}
json.dump(t, open(f'data/tracking/tracking_{D}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('recs', [(r['stock_code'], r['score'], r['target_price'], r['stop_loss']) for r in recs])
print('exits', [e['stock_code'] for e in exits])
print('carry', [(c['stock_code'], c['recommend_price'], c['stop_loss'], c['holding_days_label']) for c in carry])
