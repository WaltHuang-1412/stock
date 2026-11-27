"""2026-11-27 盤前五維度評分（時事/產業基礎分為流程判讀；其餘由當日 JSON 機械計算）"""
import json
import sys

sys.path.insert(0, 'scripts')
import settlement_checker as sc
from institutional_pattern_tracker import load_industry_map

D = 'data/2026-11-27'


def J(p):
    return json.load(open(p, encoding='utf-8'))


def idx(f):
    return {x['code']: x for x in J(D + '/' + f)}


chip = J(D + '/_chip_pool.json')
rev_lv = {r['stock_code']: r['level'] for r in J(D + '/_pool_rev/reversal_alerts.json')}
top = {s['code']: s for s in J('data/2026-11-26/institutional_top50.json')['stocks']}
prep = J(D + '/catalyst_preposition_scan.json')
l2 = {s['code'] for s in prep['l2_stocks']}
l3 = {s['code'] for s in prep['l3_stocks']}
rv, ep, fr, pp = [idx(f) for f in ('revenue_check.json', 'eps_check.json', 'foreign_ratio_check.json', 'price_position_check.json')]
pat = J('data/strategy/pattern_today.json')
cold = {c['value']: c for c in pat['cold_patterns'] if c['dimension'] == 'industry'}
im = load_industry_map()

# code: (時事, 產業邏輯, 催化對齊)
# 2618 催化對齊=False：中東超強鏈對航空是油價成本逆風（11-25 標↓、11-26「油價成本升」、11-27 →）；原先誤填 True，定稿前更正
B = {
    '2317': (20, 18, True), '2344': (21, 17, True), '2324': (15, 14, False), '1605': (13, 13, False), '1301': (16, 15, False),
    '6505': (19, 15, True), '2891': (20, 15, True), '6285': (21, 15, True), '1101': (10, 13, False), '2356': (16, 14, False),
    '1326': (12, 13, False), '2883': (19, 16, True), '2355': (14, 10, False), '2880': (21, 16, True), '4938': (18, 15, True),
    '1314': (10, 12, False), '2382': (18, 17, True), '2002': (12, 13, False), '4916': (10, 8, False), '5880': (12, 14, False),
    '1312': (10, 10, False), '2618': (18, 16, False), '6919': (8, 6, False), '2492': (17, 14, True), '2882': (14, 16, False),
    '3035': (14, 13, False), '2353': (14, 13, False), '6456': (10, 8, False), '1477': (9, 12, False), '3706': (21, 13, True),
    '3006': (14, 10, False), '1409': (8, 7, False), '4904': (14, 16, False), '9933': (10, 13, False), '1216': (13, 8, False),
    '1229': (9, 7, False), '2892': (19, 15, True), '3045': (14, 16, False), '4763': (8, 8, False), '3008': (19, 15, True),
    '3023': (15, 14, False), '3017': (14, 15, False), '6669': (18, 15, True), '8046': (21, 17, True), '2603': (22, 15, True),
    '2609': (22, 15, True), '2636': (21, 12, True), '1305': (17, 10, True), '3702': (17, 13, True), '2357': (19, 14, True),
    '2454': (18, 14, True), '2449': (20, 15, True), '2345': (22, 17, True), '2332': (19, 15, True), '3044': (17, 14, True),
    '2404': (18, 17, True), '6412': (17, 13, True), '2314': (12, 8, False), '3029': (17, 13, True), '6279': (15, 10, False),
    '3026': (17, 14, True), '2375': (15, 13, True), '3576': (12, 9, False), '6443': (12, 9, False), '2464': (14, 12, False),
    '2634': (14, 14, False), '1503': (13, 14, False), '1513': (13, 13, False), '1514': (12, 12, False),
    '1303': (20, 14, True), '3037': (20, 17, True),
    # 超強催化覆寫檢查（動能>100%）
    '2408': (22, 18, True), '2313': (21, 14, True), '2327': (19, 18, True), '2376': (17, 14, False), '6239': (18, 14, False),
}
OVERRIDE = {'2408', '2313', '2327', '2376', '6239'}
LEADER = {'2408': -5, '1303': -5, '2344': -5, '2337': -5, '6770': -5, '2382': -5, '3231': -5, '2324': -5, '2356': -5,
          '6669': -5, '2376': -5, '2330': -15, '3711': -15, '2303': -15}
MODB_EARLY = {'6669', '8046'}


def base_inst(r):
    if r is None:
        return 6
    for lim, v in [(1, 23), (4, 22), (7, 21), (10, 20), (13, 19), (16, 18), (18, 17), (20.9, 16), (24.9, 15),
                   (28.9, 14), (31.9, 13), (35.9, 12), (40.9, 11), (45.9, 10), (50, 8)]:
        if r <= lim:
            return v
    return 8


rows = []
for c, (news, ind, align) in B.items():
    ch = chip.get(c, {})
    s = top.get(c)
    lv = rev_lv.get(c)
    mom = float(ch.get('mom') or 0)
    sd = int(ch.get('sd') or 0)
    cons = int(ch.get('cons') or 0)
    f5 = ch.get('f5') or '0'
    fneg = f5.startswith('-')
    inst = base_inst(s['avg_rank'] if s else None)
    if s:
        br = s['buy_ratio']
        inst += 2 if br > 20 else 1 if br > 10 else 0
        if s['foreign'] > 0 and s['trust'] > 0:
            inst += 1
    if cons >= 5:
        inst += 1
    inst = min(inst, 25)
    if sd >= 7:
        inst = min(inst, 15)
    elif sd == 6:
        inst -= 5
    price = pp.get(c, {}).get('adj', 0)
    ser = [v for _, v in sc.get_close_series(c)]
    d5 = (ser[-1] / ser[-6] - 1) * 100
    if lv == 0:
        tech = 14 if (mom < -30 and cons >= 3) else 12 if (mom < 0 or cons >= 3) else 10
    else:
        tech = {-1: 9, 1: 8, 2: 5}.get(lv, 4)
    if d5 <= -8:
        tech -= 2
    m_mom = 15 if mom < -30 else 10 if mom < 0 else 0 if mom <= 50 else -10 if mom <= 100 else None
    ov = False
    if m_mom is None and c in OVERRIDE and lv == 0 and d5 <= 20:
        m_mom, ov = 0, True
    r = rv.get(c, {})
    e = ep.get(c, {})
    f = fr.get(c, {})
    r_adj = 0 if r.get('stale') else (r.get('adj') or 0)
    e_adj = (e.get('adj') or 0) if e.get('latest_quarter') == '2026-09-30' else 0
    sug = f.get('suggestion', '') or ''
    f_adj = 0 if f.get('stale') else 5 if sug.startswith('+5') else -3 if sug.startswith('-3') else 0
    mA = 15 if c in l3 else 10 if c in l2 else 0
    mB = 5 if c in MODB_EARLY and lv == 0 else 0
    lab = im.get(c)
    p_adj = 0
    if lab in cold and cold[lab]['sample'] >= 5:
        a = cold[lab]['accuracy']
        p_adj = -5 if a <= 30 else -3 if a <= 40 else 0
    led = LEADER.get(c, 0)
    r2 = -15 if lv == 2 else -5 if lv == 1 else 0
    big = -10 if 5 < d5 <= 10 else 0
    over = -5 if s and s['total'] >= 30_000_000 and cons < 7 else 0
    excl = []
    if lv in (3, 4):
        excl.append(f'反轉L{lv}')
    if m_mom is None:
        excl.append(f'動能{mom:+.0f}%>100%')
    if d5 > 10:
        excl.append(f'5日{d5:+.1f}%>10%')
    mods = [m_mom or 0, r_adj, e_adj, f_adj, mA, mB, p_adj, led, r2, big, over]
    neg = sum(x for x in mods if x < 0)
    total = news + inst + ind + tech + price + sum(mods) + max(0, -20 - neg)
    v = pp.get(c, {}).get('vs_ma20')
    fail = []
    if not s and v is not None and 0 <= v <= 5:
        fail.append('法人現身門檻')
    if not align:
        fail.append('①催化未對齊')
    if fneg:
        fail.append('②外資5日賣超')
    if lv != 0:
        fail.append('③非L0' + ('(狀態不明)' if lv == -1 else f'(L{lv})'))
    rows.append(dict(code=c, name=ch.get('name'), total=None if excl else total, news=news, inst=inst, ind=ind, tech=tech,
                     price=price, m_mom=m_mom, rev=r_adj, eps=e_adj, fr=f_adj, modA=mA, modB=mB, pattern=p_adj, leader=led,
                     rev_pen=r2, big=big, over=over, mom=mom, d5=round(d5, 2), vs_ma20=v, vs_ma60=pp.get(c, {}).get('vs_ma60'),
                     lv=lv, f5=f5, cons=cons, sd=sd, intop=bool(s), override=ov, excl=excl, fail=fail, close=ser[-1],
                     last_date=str(sc.get_close_series(c)[-1][0]), label=lab))
rows.sort(key=lambda r: -(r['total'] if r['total'] is not None else -999))
json.dump(rows, open(D + '/_scores.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('code name total |時 法 產 技 價 |動 營 EPS 持 A B 型 龍 反 漲| 5d ma20 cons sd f5 | fail/excl')
for r in rows:
    print(r['code'], r['name'], r['total'], 'OV' if r['override'] else '', '|', r['news'], r['inst'], r['ind'], r['tech'], r['price'], '|',
          r['m_mom'], r['rev'], r['eps'], r['fr'], r['modA'], r['modB'], r['pattern'], r['leader'], r['rev_pen'], r['big'],
          '|', r['d5'], r['vs_ma20'], r['cons'], r['sd'], r['f5'], r['close'], r['last_date'][5:10], '|',
          ';'.join(r['excl'] or r['fail']) or 'ALL PASS')
print('2408 label', im.get('2408'), '| scored', len(rows))
