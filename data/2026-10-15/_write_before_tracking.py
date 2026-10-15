import json
T = '2026-10-15'


def rec(code, name, ind, price, score, pos, reason):
    return dict(stock_code=code, stock_name=name, industry=ind, recommend_date=T, recommend_price=price,
                target_price=round(price * 1.08, 2), stop_loss_pct=-10, stop_loss=round(price * 0.9, 2),
                settlement_days=10, position=pos, score=score, result="holding", reason=reason)


recs = [
    rec('3576', '聯合再生', '太陽能／能源（tier_from_tracker 待審區）', 18.65, 83, '10%',
        '🛤️軌道A 法人TOP50 #36；真連買3天、10日累計+13K、近5天外資+3,741；反轉L0；動能-62%（佈局中）；月線+4.3%且在TOP50（過法人現身門檻）；EPS YoY+46%、毛利率QoQ+38.8pp（+5）；時事：台灣能源週拍板美國廠址、訂單能見度至2030（🟢雛形，12分）。⚠️風險：營收YoY-8.3%連2月衰退、EPS仍為負、5日買超靠單日+5,162張撐起、美股AI重挫台指期夜盤一度-853點'),
    rec('2323', '中環', '被動元件（tier_from_tracker 待審區）', 11.9, 79, '5%',
        '🛤️軌道A 法人TOP50 #20；10-14三大法人+10,984張（前兩日賣超後翻買）、9日累計+12K、外資持股比週增+1.28%（+5）；反轉L0；營收YoY+35.6%＋5日回檔-2.6%（+5）；EPS YoY+154%（+5）；時事：被動元件缺貨漲價🟡但topic_tracker對中環標→中性。⚠️風險：真連買僅1天、今日重大訊息「處分有價證券」（利多利空未明）、僅9日T86資料；70-79分小倉位'),
]


def co(code, name, rd, rp, tp, sl, d, last, src, status):
    return dict(stock_code=code, stock_name=name, recommend_date=rd, recommend_price=rp, target_price=tp,
                stop_loss_pct=-10, stop_loss=sl, settlement_days=10, holding_days_label=d, last_close=last,
                source=src, status=status)


carry = [
    co('8046', '南電', '2026-10-12', 1475.0, 1593.0, 1327.5, 'D2/10', 1430.0, 'tracking_2026-10-12.json', '⏳沿用；L0、10日累計+4,493張；本日重評92分'),
    co('3189', '景碩', '2026-10-12', 1075.0, 1161.0, 967.5, 'D2/10', 1050.0, 'tracking_2026-10-12.json', '⏳沿用；L0、10日累計+5,495張；本日重評87分'),
    co('3231', '緯創', '2026-10-12', 188.5, 203.6, 169.65, 'D2/10', 187.0, 'tracking_2026-10-12.json',
       '🛑 L4 開盤出場：10-14 T86 -3,059張佔5日均量9.0%（≥8%不受待複核保護）；Super Micro -8.42%(L2)、Dell -11.27%'),
    co('3443', '創意', '2026-10-06', 8600.0, 9288.0, 7740.0, 'D5/10', 8245.0, 'tracking_2026-10-06.json',
       '⏳沿用；L0；AMD -5.73%(L2)、Marvell -8.73%；距停損6.1%最高警戒、不加碼'),
    co('2002', '中鋼', '2026-10-13', 19.2, 20.74, 17.28, 'D1/10', 19.5, 'tracking_2026-10-13.json', '⏳沿用；10-14三大法人+79,580張'),
    co('2886', '兆豐金', '2026-10-13', 50.0, 54.0, 45.0, 'D1/10', 51.1, 'tracking_2026-10-13.json', '⏳沿用；今日公告9月自結盈餘36.29億'),
    co('2892', '第一金', '2026-10-13', 39.7, 42.88, 35.73, 'D1/10', 40.65, 'tracking_2026-10-13.json', '⏳沿用；10-14三大法人+3,820張'),
    co('2867', '三商壽', '2026-08-17', 9.75, 10.73, 8.78, '凍結', 9.7, 'tracking_2026-08-17.json',
       '⚠️序列停滯（末日2026-08-19）凍結判定；併購停止買賣待公告人工結案'),
]


def ex(c, n, cat, r, decided=True):
    return dict(stock_code=c, stock_name=n, category=cat, reason=r, decided=decided)


exits = [
    ex('6770', '力積電', '持倉 my_holdings.yaml（已決 L4＋鐵律①）', '10-14收71.0<停損73.26仍破；10-14 T86+19,567張但10日累計-157,931張；yaml未更新'),
    ex('2337', '旺宏', '持倉 my_holdings.yaml（已決，鐵律①）', '10-14收110.0<停損147.6；10-14 T86+3,004張、10日累計-37,205張'),
    ex('3090', '日電貿', '持倉 my_holdings.yaml（已決，鐵律①）', '10-14收183.5<停損256.5（鐵律①，與法人無關）'),
    ex('1301', '台塑', '持倉 my_holdings.yaml（10-13 已決 L4）', '已決不重評；揭露：10-14 T86翻買+56,691張；收88.9、損益約+48%超yaml停利20%、近6日+29.8%接近注意門檻'),
    ex('2313', '華通', '持倉 my_holdings.yaml（已決 L4）', '已決不重評；揭露：10-14 T86翻買+6,286張；收250.5未觸停損235.98'),
    ex('4938', '和碩', '持倉 my_holdings.yaml（已決 L4）', '已決不重評；揭露：10-14 T86+186張L0、10日累計+27,725張；收100.0'),
    ex('2330', '台積電', '持倉 my_holdings.yaml 零股0.15張（已決）', '10-14 T86 -5,417張佔25.0%（L4再確認）；今日法說'),
    ex('3231', '緯創', '推薦追蹤 D2（今日新增 L4）', '10-14 T86 -3,059張佔9.0%≥8%，不受v8.3.3待複核保護；入帳盤後用當日收盤價', False),
]

sl = [dict(symbol='2330', name='台積電', close=None, note='yaml無stop_loss欄位，略過'),
      dict(symbol='6770', name='力積電', close=71.0, stop_loss=73.26, hit=True),
      dict(symbol='2337', name='旺宏', close=110.0, stop_loss=147.6, hit=True),
      dict(symbol='2313', name='華通', close=250.5, stop_loss=235.98, hit=False),
      dict(symbol='3090', name='日電貿', close=183.5, stop_loss=256.5, hit=True),
      dict(symbol='1301', name='台塑', close=88.9, stop_loss=54.08, hit=False),
      dict(symbol='4938', name='和碩', close=100.0, stop_loss=76.5, hit=False)]

t = dict(
    date=T, version='v8.3.11', phase='before_market', settings=dict(stop_loss_pct=-10, settlement_days=10),
    market_context=dict(
        taiex_prev_close=48625.83, taiex_as_of='2026-10-14', taiex_chg_pct=0.59, regime='多頭（score 3）', vix=16.87,
        us={'NASDAQ': -1.88, 'S&P500': -1.11, 'SOX': -4.30, 'NVDA': -3.16, 'AMD': -5.73, 'AVGO': -3.10, 'MU': -4.10,
            'MRVL': -8.73, 'DELL': -11.27, 'SMCI': -8.42, 'WTI': 0.71},
        note='費半連6黑、近6日累跌約10%；外資10-14賣-200.4億連賣6日、投信+161.1億；台指期夜盤一度-853點；10-15台積電法說、美PPI/華許談話；AI泡沫檢查清單升【惡化】'),
    prior_decisions_executed=dict(source='tracking_2026-10-14.json tomorrow_opening_exits',
                                  items=[f"{e['stock_code']} {e['stock_name']}" for e in exits[:7]]),
    opening_exits_today=exits,
    stop_loss_check_v8310=dict(data_day='2026-10-14', rows=sl),
    recommendations=recs, carry_over=[c['stock_code'] for c in carry], carry_over_recommendations=carry,
    module_a_result=dict(L3=[], L2=['2313 華通（持倉）', '2886 兆豐金（沿用）', '2412 中華電'],
                         L1=['1711 永光', '2855 統一證', '3231 緯創', '2344 華邦電', '2327 國巨', '2323 中環'],
                         integration='2886 +10（沿用）；2412 中華電不在TOP50且月線乖離+2.2%→法人現身門檻未過；2323 中環L1不加分；L3為0'),
    module_b_result=dict(maturity='中期（Apple連漲3天）', candidates_checked=10,
                         passed_basic=['3035 智原', '3037 欣興', '2392 正崴', '3023 信邦'],
                         excluded={'3008 大立光': 'L4', '2474 可成': '累計為負', '3673 TPK-KY': '累計為負',
                                   '6415 矽力-KY': '動能+500%', '3017 奇鋐': 'L4', '2354 鴻準': '累計為負'},
                         final='0檔：3037欣興/3023信邦未過法人現身門檻（不在TOP50且月線乖離0~+5%）；2392正崴累計僅+337張；3035智原初評82分，Marvell -8.73%未在龍頭對應表，手動比照L2 -15→67分不推薦'),
    defense_ratio=dict(vix=16.87, catalyst='超強（紅區）但美股AI鏈重挫', defense_pct='0-15%', attack_pct='85-100%', regime='多頭'),
    pattern_tracker='pattern_today.json 超過3天 → 跳過', tier_from_tracker_added='本次新增 0 筆',
    removed_stocks=[], disposition_stocks=dict(twse_disposition=21, notes='候選池無處置股'),
    track_b_recommendations=[], tomorrow_pending_review=[],
    data_quality=[
        'TOP50 以 20261014 取得（10-14 T86 已公布，n=13 後首次可用）；已複製至當日資料夾',
        'market_regime TAIEX 經 fix_market_regime_taiex 校正：MI 48,341.31→Yahoo 48,625.83（資料日2026-10-14）',
        '營收 --update-cache 後 5 檔金融股（2885/2884/2882/2891/2881）仍落後→營收因子歸零；EPS 快取Q2全部當期；外資持股比as_of≥cutoff',
        '龍頭對應表缺口：Marvell -8.73%、Dell -11.27%、Arista -4.45%、Intel -4.56%、ASML -3.94% 無L2/L3預警（手動補看）',
        'Step 1-b 判勢補充未執行（選用）', '2867 三商壽序列停滯末日2026-08-19，凍結'])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok')
