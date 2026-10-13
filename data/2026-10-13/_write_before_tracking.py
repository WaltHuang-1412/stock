import json, copy
T = '2026-10-13'
y = json.load(open('data/tracking/tracking_2026-10-12.json', encoding='utf-8'))
yr = {r['stock_code']: r for r in y['recommendations']}
yc = {r['stock_code']: r for r in y['carry_over_recommendations']}
close = {'3035': 197.5, '3443': 8100.0, '2404': 1235.0, '2609': 63.6, '1312': 16.05, '3231': 189.5, '3711': 762.0,
         '8046': 1440.0, '3042': 204.5, '3026': 840.0, '3189': 1060.0, '3037': 1255.0, '2867': 9.7}
dlabel = {'3035': 'D5/10', '3443': 'D3/10', '2404': 'D2/10', '2609': 'D2/10', '1312': 'D1/10', '3231': 'D0/10',
          '3711': 'D0/10', '8046': 'D0/10', '3042': 'D0/10', '3026': 'D0/10', '3189': 'D0/10', '3037': 'D0/10',
          '2867': '凍結'}


def src(c):
    return copy.deepcopy(yr.get(c) or yc[c])


def carry(c, status):
    r = src(c)
    rd = r.get('recommend_date') or '2026-10-12'
    return dict(stock_code=c, stock_name=r['stock_name'], recommend_date=rd, recommend_price=r['recommend_price'],
                target_price=r['target_price'], stop_loss_pct=r.get('stop_loss_pct', -10), stop_loss=r['stop_loss'],
                settlement_days=10, holding_days_label=dlabel[c], last_close=close[c], source=f'tracking_{rd}.json',
                result='holding', status=status,
                return_pct=round((close[c] / r['recommend_price'] - 1) * 100, 2))


def new(c, n, price, score, pos, track, reason, risks, sb, industry):
    return dict(stock_code=c, stock_name=n, industry=industry, recommend_date=T, recommend_price=price,
                target_price=round(price * 1.08, 2), stop_loss_pct=-10, stop_loss=round(price * 0.9, 3),
                settlement_days=10, position=pos, score=score,
                rating='⭐⭐⭐⭐⭐' if score >= 90 else '⭐⭐⭐⭐', track=track, result='holding',
                reason=reason, risks=risks, score_breakdown=sb)


def carry_rec(c, score, sb, reason, risks, pos):
    s = src(c)
    r = copy.deepcopy(s)
    rd = s.get('recommend_date') or '2026-10-12'
    r.update(score=score, rating='⭐⭐⭐⭐⭐' if score >= 90 else '⭐⭐⭐⭐', recommend_date=rd, position=pos,
             reason=reason, risks=risks, score_breakdown=sb, result='holding', last_close=close[c],
             holding_days_label=dlabel[c],
             status='⏳沿用進行中追蹤（%s），維持原進場價 %s／停損 %s 不變，不重複建倉' % (dlabel[c], s['recommend_price'], s['stop_loss']))
    for k in ['intraday_price', 'close_price', 'actual_close', 'change_percent', 'holding_status']:
        r.pop(k, None)
    r['return_pct'] = round((close[c] / s['recommend_price'] - 1) * 100, 2)
    r['holding_days'] = 0
    return r


recs = []
recs.append(new('2002', '中鋼', 19.2, 108, '12-15%', '軌道A（TOP50 avg_rank 10.5）＋訊號A L2',
                '10-12 法人 +30,628 張（外資 +29,965，佔成交 57.3%）、近5天 +27K、10日累計 +70K；動能 -32.5%（+15）；9月營收 YoY +27.1% 創28個月新高、10/11月連兩月調漲盤價；Q2 EPS YoY +217%、毛利率 QoQ +4.6pp；反轉 L0；MA20 +1.84%／MA60 +1.06%；5日 -0.3% 尚未反映',
                '真連買僅 2 天、10日 5 賣；投信 -4 張（外資單腿）；鋼鐵催化僅「中」級；10-12 外資整體 -522 億連賣 4 日；月線乖離 0~5% 區（以 TOP50 買超第 4 通過法人現身門檻）；美國 337／關稅雜音',
                {'時事': 18, '法人': 20, '產業': 17, '技術': 12, '價格位置': 11, '動能': 15, '營收': 0, 'EPS': 5, '持股比': 0, '訊號A': 10, '反轉': 0},
                '鋼鐵（industry_chains 鋼鐵原物料／tier_0 鋼鐵龍頭）'))
recs.append(carry_rec('3037', 97,
                      {'時事': 19, '法人': 9, '產業': 17, '技術': 14, '價格位置': 13, '動能': 15, '營收': 5, 'EPS': 5, '持股比': 0, '訊號A': 0, '反轉': 0},
                      '10-12 +476 張（小量買超）、真連買 8 天、10日累計 +13,804；動能 -36.3%（+15）；9月營收 YoY +64.7%（+5）、Q2 EPS +5；ABF載板缺口加速（🟡強催化）、訊號B 🟢早期；反轉 L0；MA20 +11.1%',
                      '今日不在 TOP50 買超（買超僅 +476 張，分數靠動能與營收加減分撐）；沿用 D0 現價 1,255（-1.2%）；ABF 3 檔同鏈合計倉位建議 ≤25%；10/15 台積電法說',
                      '10%'))
recs.append(new('2886', '兆豐金', 50.0, 96, '10%', '軌道A（TOP50 avg_rank 30.5）＋訊號A L3',
                '10-12 法人 +4,172 張（外資 +7,867、佔成交 27.0%）、近5天 +41K、10日累計 +46K、真連買 4 天；動能 -37.4%（+15）；訊號A L3 佈局完成（+15）；公股金控投信四合一（10/22 記者會）＋定期定額公股金控大增；反轉 L0；5日 +0.9% 尚未反映',
                '投信今日 -4,882 張（外資單腿撐盤）；催化僅「觀察中／中」級；MA20 -0.39%（價位分 8）；營收快取落後（2026-08）因子歸零；聯準會鷹派／美債殖利率 5.2%；10/15 金控前三季獲利公布',
                {'時事': 13, '法人': 16, '產業': 16, '技術': 13, '價格位置': 8, '動能': 15, '營收': 0, 'EPS': 0, '持股比': 0, '訊號A': 15, '反轉': 0},
                '金融（industry_chains 金融／tier_0 金控）'))
recs.append(new('2892', '第一金', 39.7, 93, '10%', '軌道A（TOP50 avg_rank 26.5）＋訊號A L2',
                '10-12 法人 +6,051 張（外資 +5,561、佔成交 35.9%）、近5天 +8,284、10日累計 +17K、真連買 2 天；動能 -38.2%（+15）；訊號A L2（+10）；Q2 EPS YoY +43.5%（+3）；公股金控投信四合一＋定期定額；反轉 L0；5日 +0.3% 尚未反映',
                '真連買僅 2 天；投信僅 +15 張；產業分數屬待審區 tier_from_tracker（13 分）；催化僅「觀察中／中」級；營收快取落後（2026-08）因子歸零；與兆豐金同屬金融（同族群合計倉位建議 ≤20%）',
                {'時事': 13, '法人': 16, '產業': 13, '技術': 12, '價格位置': 11, '動能': 15, '營收': 0, 'EPS': 3, '持股比': 0, '訊號A': 10, '反轉': 0},
                '金融（公股金控；industry_chains tier_from_tracker）'))
recs.append(carry_rec('8046', 88,
                      {'時事': 19, '法人': 8, '產業': 17, '技術': 11, '價格位置': 13, '動能': 15, '營收': 0, 'EPS': 5, '持股比': 0, '訊號A': 0, '反轉': 0},
                      '10-12 -4 張（小量賣超）、10日累計 +10K；動能 -72.4%（+15）；ABF載板缺口加速（強催化）；Q2 EPS +5；反轉 L0；MA20 +14.7%',
                      '不在 TOP50 買超；真連買 0 天；9月營收 YoY +57.8% 未達加分門檻；沿用 D0 現價 1,440（-2.4%）；ABF 同鏈 ≤25%',
                      '10%'))
recs.append(carry_rec('3231', 87,
                      {'時事': 20, '法人': 16, '產業': 15, '技術': 10, '價格位置': 11, '動能': 0, '營收': 0, 'EPS': 5, '持股比': 0, '訊號A': 10, '反轉': 0},
                      '10-12 +4,423 張（外資 +3,858、佔成交 14.3%）、10日累計 +53K、近5天 +31K；訊號A L2（+10）；AI伺服器（🔴超強）；9月營收 YoY +87.2%、Q2 EPS +5；反轉 L0；MA20 +2.1%；今日重大訊息：新增資本支出（南科廠）',
                      '真連買僅 2 天、10日 6買4賣；動能 +31.6% 為正常區（不再有昨日 -90% 的 +15 加分，分數由 103 降為 87）；Dell 預警對應表缺口；10/15 台積電法說；337 調查被訴方不含緯創',
                      '10%'))
recs.append(carry_rec('3711', 85,
                      {'時事': 21, '法人': 20, '產業': 17, '技術': 9, '價格位置': 13, '動能': 0, '營收': 0, 'EPS': 5, '持股比': 0, '訊號A': 0, '反轉': 0},
                      '10-12 +3,222 張（外資 +2,159、投信 +814、佔成交 20.3%）、10日累計 +8,025；9月營收 881.3 億 YoY +45.5%、明年先進封測倍增；AI伺服器與半導體（🔴超強）；Q2 EPS +5；反轉 L0；MA20 +11.9%',
                      '動能 +156% >100，僅憑🔴超強催化覆寫保留（不扣分、倉位降）；Lam Research -2.91%（半導體設備）；10/15 台積電法說；今日重大訊息為取得廠務工程',
                      '5-10%'))

exits_today = [
    dict(stock_code='3035', stock_name='智原', category='追蹤 tracking_2026-10-02（已決，v8.3.3 待複核定案）',
         reason='10-08 T86 -354 張 8.4%，複核①②皆 ≥5%；10-12 T86 -336 張（7.9%）同向；已決事項不重評；收 197.5 距停損 191.7 僅 2.9%', decided=True),
    dict(stock_code='6770', stock_name='力積電', category='持倉 my_holdings.yaml（已決 L4＋鐵律①）',
         reason='收 71.4 < 停損 73.26；10-12 T86 -23,224 張（20.2%）', decided=True),
    dict(stock_code='2313', stock_name='華通', category='持倉 my_holdings.yaml（已決 L4，10-08 盤前定案）',
         reason='已決不重評；10-08 +5,020、10-12 +7,324 連兩日 T86 翻買已揭露；收 252.0 未觸停損', decided=True),
    dict(stock_code='4938', stock_name='和碩', category='持倉 my_holdings.yaml（已決 L4）',
         reason='已決不重評；10-12 T86 +14,599 翻買已揭露；收 98.6', decided=True),
    dict(stock_code='2337', stock_name='旺宏', category='持倉 my_holdings.yaml（鐵律①）',
         reason='收 115.5 < 停損 147.6；10-12 T86 -2,329 張（10.7%）', decided=True),
    dict(stock_code='3090', stock_name='日電貿', category='持倉 my_holdings.yaml（鐵律①）',
         reason='收 171.5 < 停損 256.5；10-12 T86 -556 張（7.8%）', decided=True),
    dict(stock_code='2330', stock_name='台積電', category='持倉 my_holdings.yaml 零股 0.15 張（已決）',
         reason='追蹤部位已結算；10-12 T86 -7,464 張（40.9%）', decided=True),
    dict(stock_code='1301', stock_name='台塑', category='持倉 my_holdings.yaml（今日新判 L4）',
         reason='10-12 T86 -18,665 張（佔日均量 21.2% ≥8%）；收 80.7、損益約 +34% 已超 yaml 停利 20%；不受待複核保護', decided=False),
    dict(stock_code='2404', stock_name='漢唐', category='追蹤 tracking_2026-10-07（今日新判 L4）',
         reason='10-12 T86 -420 張（29.8% ≥8%）；D2/10 收 1,235（-7.5%）距停損 2.7%', decided=False),
    dict(stock_code='3042', stock_name='晶技', category='追蹤 tracking_2026-10-12（今日新判 L4）',
         reason='10-12 T86 -2,212 張（8.6% ≥8%，不受待複核保護）；D0 收 204.5（-3.1%）', decided=False),
    dict(stock_code='3026', stock_name='禾伸堂', category='追蹤 tracking_2026-10-12（今日新判 L4）',
         reason='10-12 T86 -1,941 張（15.6%）；D0 收 840.0（-4.2%）；另有處置預警', decided=False),
]
carry_list = [
    carry('3035', '🛑 已決 L4 開盤出場'), carry('2404', '🛑 L4 開盤出場'),
    carry('3042', '🛑 L4 開盤出場'), carry('3026', '🛑 L4 開盤出場'),
    carry('3189', '⚠️ L2 單日反轉（-441 張 2.8%）→ 反轉 -15 後約 63 分 <70；續追蹤、不加碼、準備停損'),
    carry('3443', '✅ 續抱（L0，+318 張；動能 +500% 不加碼）'),
    carry('2609', '✅ 續抱（+25,714 張；距目標僅 0.5%）'),
    carry('1312', '✅ 續抱（+10,645 張；🟡處置預警）'),
    carry('2867', '🧊 序列停滯（末日 2026-08-19）凍結判定'),
]
t = dict(
    date=T, version='v8.3.11', phase='before_market', settings={'stop_loss_pct': -10, 'settlement_days': 10},
    market_context={'taiex_prev_close': 49301.96, 'taiex_as_of': '2026-10-12', 'regime': '多頭（score 3）', 'vix': 15.21,
                    'us': {'NASDAQ': -0.44, 'S&P500': -0.06, 'SOX': -2.67, 'NVDA': -1.29, 'AMD': -2.28, 'AVGO': -1.88,
                           'MU': -3.88, 'TSM_ADR': -1.97, 'WTI': 1.46},
                    'institutional_1012_yi': {'total': -593.68, 'foreign': -521.98, 'trust': 71.24, 'dealer': -142.94},
                    'note': '外資連賣 4 日；KOSPI -3.65%；10/15 台積電法說'},
    prior_decisions_executed={'source': 'tracking_2026-10-12.json tomorrow_opening_exits',
                              'items': [f"{e['stock_code']} {e['stock_name']}" for e in exits_today if e['decided']]},
    opening_exits_today=exits_today, tomorrow_opening_exits=[],
    stop_loss_check_v8310={'data_day': '2026-10-12', 'rows': [
        {'symbol': '6770', 'name': '力積電', 'close': 71.4, 'stop_loss': 73.26, 'hit': True},
        {'symbol': '2337', 'name': '旺宏', 'close': 115.5, 'stop_loss': 147.6, 'hit': True},
        {'symbol': '2313', 'name': '華通', 'close': 252.0, 'stop_loss': 235.98, 'hit': False},
        {'symbol': '3090', 'name': '日電貿', 'close': 171.5, 'stop_loss': 256.5, 'hit': True},
        {'symbol': '1301', 'name': '台塑', 'close': 80.7, 'stop_loss': 54.08, 'hit': False},
        {'symbol': '4938', 'name': '和碩', 'close': 98.6, 'stop_loss': 76.5, 'hit': False},
        {'symbol': '2330', 'name': '台積電', 'note': 'yaml 無 stop_loss 欄位，略過'}]},
    recommendations=recs, carry_over=[c['stock_code'] for c in carry_list], carry_over_recommendations=carry_list,
    module_a_result={'L3': ['2886 兆豐金'], 'L2': ['2412 中華電', '3231 緯創', '2002 中鋼', '2801 彰銀', '2892 第一金'],
                     'L1': ['1314 中石化', '1605 華新', '3481 群創'],
                     'integration': '2886 +15、2002/2892/3231 +10；2412 法說當日(10/13)不開新倉；2801 彰銀 71 分邊緣且金融已 2 檔不推薦；L1 不加分'},
    module_b_result={'maturity': '🟢早期（Dell／Tesla 連漲 0-1 天）', 'candidates_checked': 10,
                     'passed_basic': ['1513 中興電', '3037 欣興'],
                     'excluded': {'1519 華城': '累計為負', '1504 東元': '動能+114%', '1503 士電': '動能+500%',
                                  '2049 上銀': '動能+150%', '2231 為升': '累計為負／數據不足', '5284 jpp-KY': 'L4',
                                  '2371 大同': 'L4', '8111 至上': '數據不足'},
                     'final': '3037 欣興（沿用 D0）；1513 中興電 MA20 +1.78% 且不在 TOP50 → 觸法人現身門檻不推薦'},
    defense_ratio={'vix': 15.21, 'catalyst': '超強（🔴 區）', 'defense_pct': '0-15%', 'attack_pct': '85-100%', 'regime': '多頭'},
    pattern_tracker='pattern_today.json 日期 2026-10-05（距今 8 天，逾 3 天）→ 跳過，不扣分',
    tier_from_tracker_added='本次新增 0 筆', tomorrow_pending_review=[], removed_stocks=[],
    disposition_stocks={'twse_disposition': '25 檔，詳 disposition_lists.json', 'pool_hit': '2492 華新科已處置（機械排除）',
                        'warnings': '1301 台塑、1312 國喬、3026 禾伸堂、3605 宏致、6278 台表科 接近注意門檻（自算）'},
    data_quality=['TOP50 以 20261012 取得（fetch_institutional_top30 原寫入 data/2026-10-12/，已 git checkout 還原，副本於當日資料夾）；twse_t86_20261012.json 以 fetch_all_institutional 補寫落檔',
                  'Yahoo 10-12 日K close=None（全持倉）→ 已修 yahoo_finance_api.get_history 以 meta.regularMarketPrice 補值並重跑結算',
                  'fetch_institutional_top30 首次 DNS 失敗、重跑成功',
                  'EPS 快取 Q2（2026-06-30）全部當期；營收快取落後者因子歸零（stale 旗標）；外資持股比 as_of ≥10-06'])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(recs), len(carry_list))
