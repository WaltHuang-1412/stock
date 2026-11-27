"""2026-11-27 盤後明日預測評分（沿用盤前 _score.py 公式；資料改用 11-27 T86 與盤後腳本輸出）"""
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


A = D + '/_after'
chip = {c: dict(name=v['name'], mom=v['mom'], sd=v['sd'], cons=v['cons'], f5=str(v['f5'])) for c, v in J(A + '/pool_summary.json').items()}
rev_lv = {r['stock_code']: r['level'] for r in J(A + '/pool/reversal_alerts.json')}
top = {s['code']: s for s in J(D + '/institutional_top50.json')['stocks']}
for s_ in top.values():
    s_['total_k'] = s_['total']
prep = J(A + '/catalyst_preposition_scan_after.json')
l2 = {s['code'] for s in prep['l2_stocks']}
l3 = {s['code'] for s in prep['l3_stocks']}
rv, ep, fr, pp = [idx('_after/' + f) for f in ('revenue_check_after.json', 'eps_check_after.json', 'foreign_ratio_check_after.json', 'price_position_check_after.json')]
pat = J('data/strategy/pattern_today.json')
cold = {c['value']: c for c in pat['cold_patterns'] if c['dimension'] == 'industry'}
im = load_industry_map()

# code: (時事, 產業邏輯, 催化對齊) — 流程判讀，依 11-27 topic_tracker.md
B = {
    '3481': (10, 8, False), '2353': (14, 13, False), '2610': (12, 13, False), '6116': (9, 8, False), '1229': (9, 7, False),
    '3406': (18, 14, True), '1477': (9, 12, False), '2489': (9, 8, False), '1101': (10, 13, False), '2891': (20, 15, True),
    '5880': (12, 14, False), '9904': (9, 12, False), '5876': (10, 12, False), '2501': (12, 8, False), '4763': (8, 8, False),
    '9945': (10, 8, False), '8422': (8, 6, False), '6412': (17, 13, True),
}
OVERRIDE = set()
LEADER = {}
MODB_EARLY = set()


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
json.dump(rows, open(A + '/scores.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('code name total |時 法 產 技 價 |動 營 EPS 持 A B 型 龍 反 漲| 5d ma20 cons sd f5 | fail/excl')
for r in rows:
    print(r['code'], r['name'], r['total'], 'OV' if r['override'] else '', '|', r['news'], r['inst'], r['ind'], r['tech'], r['price'], '|',
          r['m_mom'], r['rev'], r['eps'], r['fr'], r['modA'], r['modB'], r['pattern'], r['leader'], r['rev_pen'], r['big'],
          '|', r['d5'], r['vs_ma20'], r['cons'], r['sd'], r['f5'], r['close'], r['last_date'][5:10], '|',
          ';'.join(r['excl'] or r['fail']) or 'ALL PASS')
print('scored', len(rows))
