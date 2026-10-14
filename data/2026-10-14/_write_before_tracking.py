import json, copy
T = '2026-10-14'
y = json.load(open('data/tracking/tracking_2026-10-13.json', encoding='utf-8'))
yr = {r['stock_code']: r for r in y['recommendations']}
yc = {r['stock_code']: r for r in y['carry_over_recommendations']}
close = {'3443': 8095.0, '3231': 187.0, '3711': 740.0, '8046': 1440.0, '3189': 1040.0, '3037': 1180.0,
         '2002': 19.15, '2886': 50.9, '2892': 40.5, '2867': 9.7}
dn = {'3443': 4, '3231': 1, '3711': 1, '8046': 1, '3189': 1, '3037': 1, '2002': 0, '2886': 0, '2892': 0}
dl = {c: f'D{n}/10' for c, n in dn.items()}; dl['2867'] = '凍結'

def src(c): return copy.deepcopy(yr.get(c) or yc[c])

def carry_rec(c, score, sb, reason, risks, pos, note=None):
    s = src(c); r = copy.deepcopy(s)
    rd = s.get('recommend_date') or '2026-10-12'
    r.update(score=score, rating='⭐⭐⭐⭐⭐' if score >= 90 else '⭐⭐⭐⭐' if score >= 80 else '⭐⭐⭐', recommend_date=rd,
             position=pos, reason=reason, risks=risks, score_breakdown=sb, result='holding', last_close=close[c],
             holding_days=dn[c], holding_days_label=dl[c],
             status=note or '⏳沿用進行中追蹤（%s），維持原進場價 %s／停損 %s 不變，不重複建倉' % (dl[c], s['recommend_price'], s['stop_loss']))
    for k in ['intraday_price', 'close_price', 'actual_close', 'change_percent', 'holding_status', 'fail_reason', 'settled_date', 'settled_price']:
        r.pop(k, None)
    r['return_pct'] = round((close[c] / s['recommend_price'] - 1) * 100, 2)
    return r

def carry(c, status, result='holding'):
    s = src(c); rd = s.get('recommend_date') or '2026-10-12'
    return dict(stock_code=c, stock_name=s['stock_name'], recommend_date=rd, recommend_price=s['recommend_price'],
                target_price=s['target_price'], stop_loss_pct=s.get('stop_loss_pct', -10), stop_loss=s['stop_loss'],
                settlement_days=10, holding_days_label=dl[c], last_close=close[c], source=f'tracking_{rd}.json',
                result=result, status=status, return_pct=round((close[c] / s['recommend_price'] - 1) * 100, 2))

recs = [
 carry_rec('3231', 102, {'時事': 20, '法人': 6, '產業': 16, '技術': 14, '價格位置': 11, '動能': 15, '營收': 0, 'EPS': 5, '持股比': 0, '訊號A': 15, '反轉': 0},
   '10-13 +828 張小量買超；10 日累計 +46K、近 5 天 +3.6K；動能 -85.0%（+15）；訊號A L3 佈局完成（+15）；AI 伺服器（🔴超強）；9 月營收 YoY +87.2%（回檔不足不加分）、Q2 EPS +5；反轉 L0；MA20 +0.74%',
   '不在 TOP50 買超且月線乖離 0~5%：若為新推薦會被「法人現身門檻」擋下，故僅沿用、不加碼；真連買 3 天但 10 日 6 買 4 賣；Dell -0.74% 對應表缺口；10/15 台積電法說；10/14 20:30 美 CPI', '10%'),
 carry_rec('8046', 92, {'時事': 18, '法人': 6, '產業': 18, '技術': 12, '價格位置': 13, '動能': 15, '營收': 5, 'EPS': 5, '持股比': 0, '訊號A': 0, '反轉': 0},
   '10-13 +745 張；10 日累計 +7.0K；動能 -72.8%（+15）；ABF 載板缺口（🟡強）；9 月營收 YoY +57.8%（+5）、Q2 EPS +5；反轉 L0；MA20 +13.0%',
   '不在 TOP50 買超、真連買僅 1 天；現價 1,440（-2.4%）；同鏈欣興今日工安意外＋L4（ABF 鏈情緒風險）；10/15 台積電法說', '10%'),
 carry_rec('3189', 92, {'時事': 18, '法人': 6, '產業': 18, '技術': 12, '價格位置': 13, '動能': 15, '營收': 5, 'EPS': 5, '持股比': 0, '訊號A': 0, '反轉': 0},
   '10-13 +1,251 張；10 日累計 +8.6K；動能 -67.5%（+15）；ABF 載板缺口；9 月營收 YoY +44.5%（+5）、Q2 EPS +5；反轉由昨日 L2 回到 L0；MA20 +10.1%',
   '不在 TOP50 買超、真連買僅 1 天；現價 1,040（-3.3%）距停損 7.0%；昨日 L2 單日反轉後僅小量回補；ABF 同鏈 ≤25%', '10%'),
 carry_rec('2002', 87, {'時事': 16, '法人': 16, '產業': 17, '技術': 12, '價格位置': 11, '動能': 0, '營收': 0, 'EPS': 5, '持股比': 0, '訊號A': 10, '反轉': 0},
   '10-13 +12,623 張（TOP50 買超第 11）；近 5 天外資 +48K、10 日累計 +86K、真連買 3 天；動能 +25.6%（正常）；訊號A L2（+10）；9 月營收 YoY +27.1%、10/11 月連兩月調漲盤價；Q2 EPS +5；反轉 L0；5 日 +1.3% 未追高',
   '昨日 108 分含動能 -32.5% 的 +15，今日動能轉正常少該加分（分數差異來自動能欄）；10 日 6 買 4 賣；鋼鐵催化僅中度；外資大盤連賣 5 日', '12-15%'),
 carry_rec('2886', 84, {'時事': 15, '法人': 21, '產業': 17, '技術': 10, '價格位置': 11, '動能': 0, '營收': 0, 'EPS': 0, '持股比': 0, '訊號A': 10, '反轉': 0},
   '10-13 +12,360 張（TOP50 第 12、佔成交 46.6%）；外資+投信同步買；近 5 天外資 +54K、10 日累計 +58K、真連買 5 天；訊號A L2（+10）；公股金控投信四合一（10/22）；市場專家點名外資連日敲進；反轉 L0',
   '催化僅觀察中／中度；營收快取落後（2026-08）因子歸零；聯準會鷹派、美債殖利率 5.2%；10/15 前金控 9 月獲利公布', '10%'),
 carry_rec('3443', 76, {'時事': 20, '法人': 7, '產業': 18, '技術': 10, '價格位置': 13, '動能': 0, '營收': 5, 'EPS': 3, '持股比': 0, '訊號A': 0, '反轉': 0},
   '10-13 +145 張小量；10 日累計 +571；真連買 6 天；9 月營收 YoY +97.8%（+5）；ASIC／AI（🔴超強）；反轉 L0；MA20 +5.8%',
   '動能 +500% >100 僅沿用不加碼；不在 TOP50；現價 8,095（-5.9%）距停損 4.6%；AMD 預警（對應創意）', '沿用不加碼'),
 carry_rec('2892', 71, {'時事': 20, '法人': 21, '產業': 14, '技術': 12, '價格位置': 11, '動能': 0, '營收': 0, 'EPS': 3, '持股比': 0, '訊號A': 0, '反轉': 0, '已大漲': -10},
   '10-13 +11,936 張（TOP50 第 13、佔成交 48.3%）；近 5 天外資 +21K、10 日累計 +27K、真連買 3 天；Fed 鷹派鏈 ↑、9 月自結盈餘 28.70 億（10-13 公告）；Q2 EPS +3；反轉 L0',
   '5 日 +6.4% → 已大漲 -10；動能 +255% >100 僅沿用不加碼；產業屬待審區 tier_from_tracker（14）；與兆豐金同屬金融（合計 ≤20%）', '沿用不加碼'),
]
exits = [
 dict(stock_code='6770', stock_name='力積電', category='持倉 my_holdings.yaml（已決 L4＋鐵律①）', reason='收 67.5 < 停損 73.26；10-13 T86 -107,315 張（119.6%）；yaml 未更新', decided=True),
 dict(stock_code='2337', stock_name='旺宏', category='持倉 my_holdings.yaml（鐵律①）', reason='收 106.5 < 停損 147.6；10-13 T86 -19,865 張（84.6%）', decided=True),
 dict(stock_code='3090', stock_name='日電貿', category='持倉 my_holdings.yaml（鐵律①）', reason='收 167.0 < 停損 256.5；10-13 T86 -422 張（7.0%）', decided=True),
 dict(stock_code='1301', stock_name='台塑', category='持倉 my_holdings.yaml（10-13 已決 L4）', reason='已決；10-13 T86 -3,442 張（3.0%，L2）；收 80.9、損益約 +34.6% 已超 yaml 停利 20%', decided=True),
 dict(stock_code='2313', stock_name='華通', category='持倉 my_holdings.yaml（已決 L4，10-08 定案）', reason='已決不重評；10-13 T86 -4,472 張（8.1%）再度轉賣；收 243.5 距停損 235.98 僅 3.2%', decided=True),
 dict(stock_code='4938', stock_name='和碩', category='持倉 my_holdings.yaml（已決 L4）', reason='已決不重評；10-12 +14,599、10-13 +16,968 連兩日翻買已揭露；收 102.5；處置預警（6 日 +14.9%）', decided=True),
 dict(stock_code='2330', stock_name='台積電', category='持倉 my_holdings.yaml 零股 0.15 張（已決）', reason='10-13 T86 -20,145 張（103.0%）；10/15 法說', decided=True),
 dict(stock_code='3037', stock_name='欣興', category='追蹤 tracking_2026-10-12（今日新判 L4）', reason='10-13 T86 -2,311 張（18.0% ≥8%，不受待複核保護）；10-13 收 1,180（-7.1%）距停損 1,143 僅 3.2%；10-14 重大訊息：10/13 工安意外說明', decided=False),
 dict(stock_code='3711', stock_name='日月光投控', category='追蹤 tracking_2026-10-12（今日新判 L4）', reason='10-13 T86 -2,546 張（19.9% ≥8%，不受待複核保護）；D1 收 740.0（-0.5%）；Applied Materials -6.69%／Lam -2.73%', decided=False),
]
carry_list = [carry('3037', 'L4 開盤出場'), carry('3711', 'L4 開盤出場'), carry('2867', '序列停滯（末日 2026-08-19）凍結判定', 'holding')]
t = dict(
 date=T, version='v8.3.11', phase='before_market', settings={'stop_loss_pct': -10, 'settlement_days': 10},
 market_context={'taiex_prev_close': 48341.31, 'taiex_as_of': '2026-10-13', 'taiex_chg_pct': -1.94, 'regime': '多頭（score 3）', 'vix': 15.27,
   'us': {'NASDAQ': -0.15, 'S&P500': -0.02, 'SOX': -0.23, 'NVDA': 0.97, 'AMD': 1.9, 'AVGO': 0.73, 'MU': -3.62, 'AMAT': -6.69, 'LRCX': -2.73, 'KLAC': -3.22, 'WTI': 1.18},
   'institutional_1013_yi': {'total': -1984.5, 'foreign': -1653.4, 'trust': 238.7, 'dealer': -569.8},
   'note': '外資單日 -1,653 億（史上第 3 大賣超）連賣 5 日；台指期夜盤 48,755（+363）；10/14 20:30 美 CPI、10/15 台積電法說'},
 prior_decisions_executed={'source': 'tracking_2026-10-13.json tomorrow_opening_exits', 'items': [f"{e['stock_code']} {e['stock_name']}" for e in exits if e['decided']]},
 opening_exits_today=exits, tomorrow_opening_exits=[],
 stop_loss_check_v8310={'data_day': '2026-10-13', 'rows': [
   {'symbol': '2330', 'name': '台積電', 'close': 2490.0, 'note': 'yaml 無 stop_loss 欄位，略過'},
   {'symbol': '6770', 'name': '力積電', 'close': 67.5, 'stop_loss': 73.26, 'hit': True},
   {'symbol': '2337', 'name': '旺宏', 'close': 106.5, 'stop_loss': 147.6, 'hit': True},
   {'symbol': '2313', 'name': '華通', 'close': 243.5, 'stop_loss': 235.98, 'hit': False},
   {'symbol': '3090', 'name': '日電貿', 'close': 167.0, 'stop_loss': 256.5, 'hit': True},
   {'symbol': '1301', 'name': '台塑', 'close': 80.9, 'stop_loss': 54.08, 'hit': False},
   {'symbol': '4938', 'name': '和碩', 'close': 102.5, 'stop_loss': 76.5, 'hit': False}]},
 recommendations=recs, carry_over=[c['stock_code'] for c in carry_list] + [r['stock_code'] for r in recs],
 carry_over_recommendations=carry_list,
 module_a_result={'L3': ['3231 緯創'], 'L2': ['2412 中華電', '2886 兆豐金', '2002 中鋼', '1605 華新', '6209 今國光', '3711 日月光投控', '3481 群創'],
   'L1': ['2344 華邦電', '1313 聯成'],
   'integration': '3231 +15（沿用）、2002/2886 +10（沿用）；2412 中華電催化偏負（Starlink 衝擊）未過準確率篩選①、1605 華新 L4、3711 L4、6209 今國光 處置預警＋連買 1 天、3481 群創 狀態不明；L1 不加分'},
 module_b_result={'maturity': '早期（Apple 連漲 2 天）', 'candidates_checked': 10, 'passed_basic': ['3035 智原（L2，已決出場）', '3023 信邦'],
   'excluded': {'3008 大立光': '累計為負', '2474 可成': '累計為負', '3673 TPK-KY': '累計為負', '6415 矽力-KY': 'L3', '3037 欣興': 'L4', '2392 正崴': 'L4', '3017 奇鋐': 'L4', '2354 鴻準': 'L4'},
   'final': '0 檔：3023 信邦 68+5=73 分，催化僅中度＋10 日累計僅 +1.7K 連買 1 天，未過準確率篩選①，列觀察'},
 defense_ratio={'vix': 15.27, 'catalyst': '超強（紅區）', 'defense_pct': '0-15%', 'attack_pct': '85-100%', 'regime': '多頭'},
 pattern_tracker='pattern_today.json 日期 2026-10-05（距今 9 天，逾 3 天）→ 跳過，不扣分',
 tier_from_tracker_added='本次新增 0 筆', tomorrow_pending_review=[], removed_stocks=[],
 disposition_stocks={'twse_disposition': '25 檔，詳 disposition_lists.json', 'pool_hit': '候選池無處置股；3016 嘉晶為官方注意股（近 10 日 5 次／近 30 日 7 次，最快剩 1 個營業日處置）→ 不推薦',
   'warnings': '4938 和碩（6 日 +14.9%）、1319 東陽、1714 和桐、6209 今國光、2603 長榮 接近注意門檻（自算）'},
 track_b_recommendations=[], track_b_observations=['2377 微星（約 74 分：催化僅中度、TOP50 末位 +2.4K 張、未登錄產業）', '3023 信邦（73）', '2412 中華電（約 76：催化偏負，未過篩選①）'],
 data_quality=['TOP50 以 20261013 取得；fetch_institutional_top30.py 預設寫入 data/2026-10-13/institutional_top50.json（覆蓋昨日盤前副本），已 git checkout 還原並複製至當日資料夾',
   'twse_t86_20261013.json 08:03 已落檔（盤前可用）；reversal_alert／chip_analysis 皆含 10-13',
   'fix_market_regime_taiex：MI taiex.current 49,301.96（落後）→ Yahoo 校正 48,341.31（資料日 2026-10-13，差 -960.65 點）',
   'EPS 快取 Q2（2026-06-30）全部當期；營收 --update-cache 後 stale 旗標者（金融股落後至 2026-08）因子歸零；外資持股比 as_of 10-12 ≥ cutoff 10-07',
   'Step 1-b 判勢補充未執行（選用）'])
json.dump(t, open(f'data/tracking/tracking_{T}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('ok', len(recs), len(carry_list))

