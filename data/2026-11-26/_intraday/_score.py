"""2026-11-26 盤中軌道B 評分：沿用盤前 _score.py 公式；基礎分（時事、產業）沿用盤前判讀，加減分取盤中重跑 JSON"""
import json, re, sys
sys.path.insert(0, 'scripts')
import settlement_checker as sc

D = 'data/2026-11-26'
I = D + '/_intraday'
J = lambda p: json.load(open(p, encoding='utf-8'))
top = {s['code']: s for s in J('data/2026-11-25/institutional_top50.json')['stocks']}
pool = {r['code']: r for r in J(I + '/pool.json')}
prices = J(I + '/prices.json')
rv_lv = {r['stock_code']: r['level'] for r in J(I + '/reversal_alerts.json')}
det = J(D + '/intraday_detector.json')

# chip.txt 解析
txt = open(I + '/chip.txt', encoding='utf-8').read()
blocks = re.split(r'📊 (.+?)\((\w+)\) 籌碼分析', txt)
chip = {}
for i in range(1, len(blocks), 3):
    name, code, b = blocks[i], blocks[i + 1], blocks[i + 2]
    g = lambda p, s=b: (re.search(p, s).group(1) if re.search(p, s) else None)
    sec5 = b.split('【近5天趨勢】')[-1]
    chip[code] = dict(name=name, cons=int(g(r'真連續買超:\s*(\d+)')), sd=int(g(r'賣超天數:\s*(\d+)')),
                      f5=g(r'近5天淨買超（外資）\s*:\s*([+\-\d,K]+)', sec5),
                      mom=float(g(r'動能變化:\s*([+\-\d.]+)%')),
                      today=re.findall(r'^\d{4}/\d\d/\d\d\s+(\S+)\s+(\S+)\s+(\S+)', b, re.M)[0])

def byco(path):
    out = {}
    def walk(o):
        if isinstance(o, dict):
            c = o.get('code') or o.get('stock_code') or o.get('symbol')
            if c and len(o) > 2:
                out[str(c)] = o
            for k, v in o.items():
                if isinstance(v, dict) and k.isdigit():
                    out.setdefault(k, v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(J(path))
    return out

rev = byco(I + '/revenue_check_intraday.json')
eps = byco(I + '/eps_check_intraday.json')
fr = byco(I + '/foreign_ratio_check_intraday.json')
pp = byco(I + '/price_position_check_intraday.json')

l2 = set()
def walk_prep(o, tag=''):
    if isinstance(o, dict):
        c = o.get('code')
        lv = str(o.get('level') or o.get('tier') or o.get('signal_level') or tag)
        if c and '2' in lv:
            l2.add(str(c))
        for k, v in o.items():
            walk_prep(v, k)
    elif isinstance(o, list):
        for v in o:
            walk_prep(v, tag)
walk_prep(J(D + '/catalyst_preposition_scan.json'))

strong = set()
def walk_det(o):
    if isinstance(o, dict):
        c = o.get('code') or o.get('stock_code')
        s = o.get('strength') if o.get('strength') is not None else o.get('score')
        if c and isinstance(s, (int, float)) and s >= 60:
            strong.add(str(c))
        for v in o.values():
            walk_det(v)
    elif isinstance(o, list):
        for v in o:
            walk_det(v)
walk_det(det)

# (時事, 產業, 催化對齊)
B = {'1802': (12, 14, False), '5871': (9, 13, False), '1216': (14, 7, False), '2609': (21, 15, True),
     '2323': (9, 7, False), '9904': (10, 13, False), '9945': (9, 6, False), '2634': (15, 15, False),
     '2603': (21, 15, True), '9929': (9, 6, False)}

def base_inst(r):
    if r is None:
        return 6
    for lim, v in [(1, 23), (4, 22), (7, 21), (10, 20), (13, 19), (16, 18), (18, 17), (20.9, 16),
                   (24.9, 15), (28.9, 14), (31.9, 13), (35.9, 12), (40.9, 11), (45.9, 10), (50, 8)]:
        if r <= lim:
            return v
    return 8

def num(x, *keys):
    for k in keys:
        if x and k in x and isinstance(x[k], (int, float)):
            return x[k]
    return None

rows = []
for c, (news, ind, align) in B.items():
    ch = chip[c]; s = top.get(c); lv = rv_lv.get(c)
    mom, sd, cons = ch['mom'], ch['sd'], ch['cons']
    inst = base_inst(s['avg_rank'] if s else None)
    if s:
        br = s['buy_ratio']
        inst += 2 if br > 20 else 1 if br > 10 else 0
        t = ch['today']
        if not t[1].startswith('-') and not t[2].startswith('-') and t[2] != '+0':
            inst += 1
    if cons >= 5:
        inst += 1
    inst = min(inst, 25)
    if sd >= 7:
        inst = min(inst, 15)
    elif sd == 6:
        inst -= 5
    price = num(pp.get(c), 'adj', 'score')
    r_adj = num(rev.get(c), 'adj', 'score_adj', 'adjustment', 'score') or 0
    e_adj = num(eps.get(c), 'adj', 'score_adj', 'adjustment', 'score') or 0
    sug = (fr.get(c) or {}).get('suggestion', '')
    f_adj = 5 if sug.startswith('+5') else -3 if sug.startswith('-3') else 0
    if lv == 0:
        tech = 14 if (mom < -30 and cons >= 3) else 12 if (mom < 0 or cons >= 3) else 10
    else:
        tech = {-1: 9, 1: 8, 2: 5}.get(lv, 4)
    d5 = (rev.get(c) or {}).get('pullback_5d')
    if d5 is not None and d5 <= -8:
        tech -= 2
    m_mom = 15 if mom < -30 else 10 if mom < 0 else 0 if mom <= 50 else -10 if mom <= 100 else None
    mA = 10 if c in l2 else 0
    pat = 0
    if cons >= 2:
        px = [v for d, v in sc.get_close_series(c) if str(d)[:10] < '2026-11-26'][-cons:]
        if (px[-1] / px[0] - 1) * 100 <= -2:
            pat = -5
    r2 = -15 if lv == 2 else -5 if lv == 1 else 0
    big = -10 if s and 5 < s['5day_change'] <= 10 else 0
    dbonus = 5 if c in strong else 0
    excl = []
    if lv in (3, 4):
        excl.append(f'反轉L{lv}')
    if m_mom is None:
        excl.append(f'動能{mom:+.0f}%>100%')
    mods = [m_mom or 0, r_adj, e_adj, f_adj, mA, pat, r2, big, dbonus]
    neg = sum(x for x in mods if x < 0)
    total = news + inst + ind + tech + price + sum(mods) + max(0, -20 - neg)
    v20 = num(pp.get(c), 'vs_ma20')
    fail = []
    if not s and v20 is not None and 0 <= v20 <= 5:
        fail.append('法人現身門檻')
    if not align:
        fail.append('①催化未對齊')
    if (ch['f5'] or '').startswith('-'):
        fail.append('②外資5日賣超')
    if lv != 0:
        fail.append('③非L0' + ('(狀態不明)' if lv == -1 else f'(L{lv})'))
    if not excl and total < 75:
        fail.append('<75分')
    rows.append(dict(code=c, name=ch['name'], chg=pool.get(c, {}).get('chg', prices.get(c, {}).get('chg')),
                     news=news, inst=inst, ind=ind, tech=tech, price=price, mom=mom, m_mom=m_mom, rev=r_adj,
                     eps=e_adj, fr=f_adj, modA=mA, pattern=pat, rev_pen=r2, big=big, detector=dbonus,
                     total=None if excl else total, lv=lv, f5=ch['f5'], cons=cons, sd=sd, vs_ma20=v20,
                     fail=excl + fail))
rows.sort(key=lambda r: -(r['total'] if r['total'] is not None else -999))
json.dump(rows, open(I + '/scores.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('strong', strong, 'L2', sorted(l2 & set(B)))
print('code name 漲 total |時 法 產 技 價|動 營 EPS 持 A 型 反 漲 偵| mom f5 cons sd vs20 | fail')
for r in rows:
    print(r['code'], r['name'], r['chg'], r['total'], '|', r['news'], r['inst'], r['ind'], r['tech'], r['price'], '|',
          r['m_mom'], r['rev'], r['eps'], r['fr'], r['modA'], r['pattern'], r['rev_pen'], r['big'], r['detector'],
          '|', r['mom'], r['f5'], r['cons'], r['sd'], r['vs_ma20'], '|', ';'.join(r['fail']) or 'ALL PASS')
