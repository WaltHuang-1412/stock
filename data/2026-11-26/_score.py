"""2026-11-26 盤前五維度評分（基礎分由流程判讀、加減分由當日 JSON 機械計算）"""
import json

D = 'data/2026-11-26'
J = lambda p: json.load(open(p, encoding='utf-8'))
chip = J(D + '/_chip_pool.json')
rev_lv = {r['stock_code']: r['level'] for r in J(D + '/_pool_rev/reversal_alerts.json')}
top = {s['code']: s for s in J('data/2026-11-25/institutional_top50.json')['stocks']}
prep = J(D + '/catalyst_preposition_scan.json')


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


rv = byco(D + '/revenue_check.json')
ep = byco(D + '/eps_check.json')
fr = byco(D + '/foreign_ratio_check.json')
pp = byco(D + '/price_position_check.json')

l2 = set()


def walk_prep(o, tag=''):
    if isinstance(o, dict):
        c = o.get('code')
        lv = str(o.get('level') or o.get('tier') or o.get('signal_level') or tag)
        if c and ('2' in lv):
            l2.add(str(c))
        for k, v in o.items():
            walk_prep(v, k)
    elif isinstance(o, list):
        for v in o:
            walk_prep(v, tag)


walk_prep(prep)

# code: (時事, 產業邏輯, 技術, 產業說明, 催化對齊)
B = {
    '1802': (12, 14, 11, '玻纖布/PCB(待審)', False),
    '2610': (12, 17, 12, '航空 tier_0', False),
    '2615': (22, 14, 10, '航運(中東超強↑,待審)', True),
    '2449': (21, 15, 9, 'AI封測(待審)', True),
    '6505': (22, 15, 11, '塑化(中東超強↑,待審)', True),
    '3006': (14, 10, 6, '記憶體控制IC', False),
    '2412': (16, 18, 11, '電信 tier_0', False),
    '1216': (14, 7, 13, '食品內需(未分類)', False),
    '2609': (21, 15, 9, '航運(中東超強↑)', True),
    '2323': (9, 7, 11, '未分類', False),
    '9904': (10, 13, 12, '製鞋/集團(待審)', False),
    '3706': (19, 13, 12, 'AI伺服器(今日法說)', True),
    '9933': (10, 13, 10, '統包工程(待審)', False),
    '3189': (14, 14, 6, 'ABF載板', False),
    '9945': (9, 6, 11, '未分類', False),
    '2367': (11, 10, 5, 'PCB', False),
    '2382': (17, 17, 9, 'AI伺服器龍頭', True),
    '3035': (14, 13, 6, 'ASIC設計服務', False),
    '2634': (15, 15, 10, '軍工(中度↑,待審)', False),
    '2379': (18, 15, 12, '網路晶片 tier_1', True),
    '8213': (11, 10, 6, 'PCB', False),
    '2603': (21, 15, 10, '航運(中東超強↑)', True),
    '1301': (17, 15, 4, '塑化', False),
    '2449x': (0, 0, 0, '', False),
    '4916': (11, 9, 5, '工業電腦', False),
    '1210': (9, 7, 10, '食品(今日法說)', False),
    '6108': (11, 13, 9, 'PCB(待審)', False),
    '1416': (8, 6, 9, '未分類', False),
    '8033': (15, 15, 9, '軍工無人機(待審)', False),
    '2542': (12, 13, 12, '營建(房市中度,待審)', False),
    '2597': (9, 6, 10, '未分類營建', False),
    '9939': (9, 6, 11, '未分類包材', False),
    '9910': (8, 11, 9, '製鞋(待審)', False),
    '6672': (14, 14, 9, 'CCL(待審)', False),
    '3406': (14, 14, 8, '光學/蘋果', False),
    '5608': (13, 9, 9, '航運', False),
    '5876': (14, 13, 12, '銀行防禦(待審)', False),
    '2883': (14, 13, 9, '金控', False),
    '2892': (19, 15, 11, '公股金控', True),
    '6669': (19, 15, 12, 'AI伺服器(待審)', True),
    '5880': (15, 15, 6, '公股金控', False),
    '2891': (19, 17, 5, '金控龍頭', True),
    '8046': (18, 15, 5, 'ABF載板', True),
    '2645': (14, 13, 5, '軍工航太', False),
    '3045': (16, 17, 11, '電信', False),
    '4904': (16, 17, 11, '電信', False),
    '2637': (21, 14, 10, '散裝(中東超強↑)', True),
    '1503': (14, 15, 10, '重電', False),
    '2345': (20, 17, 10, '網通龍頭', True),
}
# 以今日完整重跑的 pattern_today.json（11-26）為準：產業型 cold ＋「越買越跌」
# 「沒出貨」描述買超結束後的行為，事前無法判定 → 不套用
PATTERN = {'2382': -5, '1503': -5}
import sys
sys.path.insert(0, 'scripts')
import settlement_checker as sc
LEADER = {'6669': -5, '2382': -5}
MODB = {'6669', '8046'}
MEMO = {}


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
for c, (news, ind, tech, label, align) in B.items():
    if c.endswith('x'):
        continue
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
        t = ch.get('today') or []
        if len(t) == 3 and not t[1].startswith('-') and not t[2].startswith('-') and t[2] not in ('+0',):
            inst += 1
    if cons >= 5:
        inst += 1
    inst = min(inst, 25)
    if sd >= 7:
        inst = min(inst, 15)
    elif sd == 6:
        inst -= 5
    price = num(pp.get(c), 'adj', 'score')
    if price is None:
        price = {'1802': 3}.get(c, 0)  # 1802 腳本無資料：自算 MA20 -9.3%/MA60 -4.7% → 4-1=3
    r_adj = num(rv.get(c), 'adj', 'score_adj', 'adjustment', 'score') or 0
    e_adj = num(ep.get(c), 'adj', 'score_adj', 'adjustment', 'score') or 0
    if c == '2892':
        e_adj = 0  # EPS 快取停在 06-30
    sug = (fr.get(c) or {}).get('suggestion', '')
    f_adj = 5 if sug.startswith('+5') else -3 if sug.startswith('-3') else 0
    # 技術面機械化：反轉等級＋動能＋真連買，近5日跌≥8% 視為跳水未回補 -2
    if lv == 0:
        tech = 14 if (mom < -30 and cons >= 3) else 12 if (mom < 0 or cons >= 3) else 10
    else:
        tech = {-1: 9, 1: 8, 2: 5}.get(lv, 4)
    d5 = (rv.get(c) or {}).get('pullback_5d')
    if d5 is not None and d5 <= -8:
        tech -= 2
    m_mom = 15 if mom < -30 else 10 if mom < 0 else 0 if mom <= 50 else -10 if mom <= 100 else None
    mA = 10 if c in l2 else 0
    mB = 5 if c in MODB and lv == 0 else 0
    pat = PATTERN.get(c, 0)
    if cons >= 2:  # 追蹤器定義：連買週期(≥2天)首末日收盤漲跌 ≤ -2% = 越買越跌
        px = [v for _, v in sc.get_close_series(c)][-cons:]
        if (px[-1] / px[0] - 1) * 100 <= -2:
            pat = -5
            MEMO[c] = '越買越跌'
    led = LEADER.get(c, 0)
    r2 = -15 if lv == 2 else -5 if lv == 1 else 0
    big = -10 if s and 5 < s['5day_change'] <= 10 else 0
    excl = []
    if lv in (3, 4):
        excl.append(f'反轉L{lv}')
    if m_mom is None:
        excl.append(f'動能{mom:+.0f}%>100%')
    over = -5 if s and s['total'] >= 30_000_000 and cons < 7 and c not in () else 0
    mods = [m_mom or 0, r_adj, e_adj, f_adj, mA, mB, pat, led, r2, big, over]
    neg = sum(x for x in mods if x < 0)
    total = news + inst + ind + tech + price + sum(mods) + (max(0, -20 - neg))
    rows.append(dict(code=c, name=ch.get('name'), label=label, news=news, inst=inst, ind=ind, tech=tech,
                     price=price, mom=mom, m_mom=m_mom, rev=r_adj, eps=e_adj, fr=f_adj, modA=mA, modB=mB,
                     pattern=pat, leader=led, rev_pen=r2, big=big, total=None if excl else total,
                     lv=lv, f5=f5, f5ok=not fneg, align=align, cons=cons, sd=sd, intop=bool(s),
                     excl=excl))

# 法人現身門檻 + 準確率三篩
vs20 = {c: num(pp.get(c), 'vs_ma20') for c in B}
for r in rows:
    v = vs20.get(r['code'])
    r['vs_ma20'] = v
    fail = []
    if not r['intop'] and v is not None and 0 <= v <= 5:
        fail.append('法人現身門檻')
    if not r['align']:
        fail.append('①催化未對齊')
    if not r['f5ok']:
        fail.append('②外資5日賣超')
    if r['lv'] != 0:
        fail.append('③非L0' + ('(狀態不明)' if r['lv'] == -1 else f'(L{r["lv"]})'))
    r['fail'] = fail

rows.sort(key=lambda r: -(r['total'] if r['total'] is not None else -999))
json.dump(rows, open(D + '/_scores.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('L2 set', sorted(l2))
print('code name total |時 法 產 技 價 |動 營 EPS 持 A B 型 龍 反 漲| vs20 fail/excl')
for r in rows:
    print(r['code'], r['name'], r['total'], '|', r['news'], r['inst'], r['ind'], r['tech'], r['price'], '|',
          r['m_mom'], r['rev'], r['eps'], r['fr'], r['modA'], r['modB'], r['pattern'], r['leader'], r['rev_pen'], r['big'],
          '|', r['vs_ma20'], ';'.join(r['excl'] or r['fail']) or 'ALL PASS')
