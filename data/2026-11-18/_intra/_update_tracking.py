import json
f = 'data/tracking/tracking_2026-11-18.json'
t = json.load(open(f, encoding='utf-8'))
T = "2026-11-18 12:12（Yahoo regularMarketPrice）"
px = {
    '2886': (52.0, -4.94, 'L0', '續抱（不加碼；今日 Q3 財報公告）'),
    '2892': (40.55, -3.68, 'L0', '續抱（觀察）'),
    '5876': (52.7, -1.13, 'L0', '續抱；11/20 法說'),
    '2412': (164.0, -0.30, 'L4（已決）', '開盤出場（已決事項，入帳價用收盤）'),
    '2801': (27.5, -2.31, '狀態不明（今日+710張、累計-312）', '續抱（觀察）'),
    '2884': (42.3, -9.32, 'L4（已決）', '開盤出場（已決事項）；盤中同時觸及鐵律①②'),
    '4904': (108.5, 0.0, 'L0', '續抱；11/19 法說'),
}
for lst in (t['recommendations'], t['carry_over_recommendations']):
    for r in lst:
        c = r['stock_code']
        if c in px:
            p, chg, rev, st = px[c]
            r.update(intraday_price=p, intraday_change_pct=chg,
                     intraday_return_pct=round((p / r['recommend_price'] - 1) * 100, 2),
                     intraday_time=T, intraday_reversal=rev, intraday_strategy=st)
t['phase'] = 'intraday'
t['track_b_recommendations'] = []
t['track_b_observations'] = [
    {"stock_code": "2609", "stock_name": "陽明", "score": 65, "reason": "航運催化↑超強、營收+82%、真連買3天、外資5日+14K；但動能+500%（追高排除，盤前已排）、月季線雙下（價格位置6）→ 不推"},
    {"stock_code": "2618", "stock_name": "長榮航", "score": 72, "reason": "真連買10天、累計+123K、營收+22.6%、價格位置11、動能+24%；但篩選①催化對立（中東鏈標『↓油價成本』）→ 不推，觀察"},
    {"stock_code": "2610", "stock_name": "華航", "score": 0, "reason": "真連買10天、累計+212K；今日14:00法說會，當日不開新倉（未評分）"},
    {"stock_code": "5880", "stock_name": "合庫金", "score": 62, "reason": "營收連3月衰退-5、月線下（價格位置8）、金融已集中5檔追蹤、今日金融股普遍-4%以上 → <75"},
    {"stock_code": "2486", "stock_name": "一詮", "score": 55, "reason": "偵測器強訊號60，但真連買僅1天、10日累計僅+1,500張、不在TOP50買超 → 法人現身門檻不過，不推"},
    {"stock_code": "2911", "stock_name": "麗嬰房", "score": 40, "reason": "偵測器強訊號60，但法人累計僅+134張（無實質法人）、接近注意門檻 → 排除"},
]
t['intraday_taiex'] = "加權 40,416（+324 點、+0.81%，前收 40,092）；Yahoo 12:12"
t['intraday_note'] = "無盤中新推薦；追蹤中 2884 玉山金盤中 42.3 同時觸及鐵律①（<停損43.47）與②（2日-12.4%），已是已決開盤出場；2412 已決出場；其餘未觸停損。"
json.dump(t, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok')
