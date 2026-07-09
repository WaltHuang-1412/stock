# -*- coding: utf-8 -*-
"""主回測:分數帶分辨力、擁擠度懲罰規則、大盤短期降級規則"""
import json, os
from collections import defaultdict

SP = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SP, 'backtest_dataset.json'), encoding='utf-8') as f:
    rows = json.load(f)
with open(os.path.join(SP, 'taiex_series.json'), encoding='utf-8') as f:
    taiex = json.load(f)
with open(os.path.join(SP, 'foreign_flows.json'), encoding='utf-8') as f:
    flows = json.load(f)

rows = [r for r in rows if r['result'] in ('success', 'fail')]

def stats(rs, label=''):
    n = len(rs)
    if n == 0:
        return f'{label}: 0筆'
    w = sum(1 for r in rs if r['result'] == 'success')
    rets = [r['ret'] for r in rs if r['ret'] is not None]
    avg = sum(rets) / len(rets) if rets else None
    avg_s = f' 平均報酬{avg:+.2f}%({len(rets)}筆有價格)' if avg is not None else ''
    return f'{label}: {n}筆 {w}勝{n-w}敗 命中率{w/n*100:.0f}%{avg_s}'

def band(score):
    if score is None: return '?'
    if score >= 90: return '90+'
    if score >= 80: return '80-89'
    if score >= 70: return '70-79'
    return '<70'

P = []
def out(s=''):
    P.append(s)
    print(s)

out('=' * 70)
out('回測報告:評分分辨力 + 擁擠度規則 + 大盤降級規則')
out(f'樣本:{len(rows)} 筆已結算推薦({rows[0]["date"]} ~ {rows[-1]["date"]})')
out('=' * 70)

# ============ 分析一:分數帶 × 時期 ============
out()
out('【分析一】分數帶命中率(v8.1 於 04-24 上線,分開看)')
for period, lo, hi in [('v8.0 期(01-16~04-23)', '2026-01-16', '2026-04-23'),
                        ('v8.1 期(04-24~06-24)', '2026-04-24', '2026-06-24'),
                        ('近期(06-25~07-07)', '2026-06-25', '2026-07-07')]:
    sub = [r for r in rows if lo <= r['date'] <= hi]
    out(f'-- {period} --')
    for b in ['90+', '80-89', '70-79', '<70']:
        bs = [r for r in sub if band(r['score']) == b]
        if bs:
            out('  ' + stats(bs, b))

# ============ 分析二:擁擠度(avg_rank × vs_ma20)============
out()
out('【分析二】擁擠度:法人排名 × 月線乖離(全樣本)')
def rank_bucket(r):
    a = r['avg_rank']
    if a is None: return '不在TOP50買超'
    if a <= 5: return 'TOP5'
    if a <= 15: return 'TOP6-15'
    return 'TOP16+'
def ma_bucket(r):
    v = r['vs_ma20']
    if v is None: return '?'
    if v > 15: return '>+15%'
    if v > 5: return '+5~15%'
    if v > 0: return '0~+5%'
    return '<0%'

out('-- 單看月線乖離(現行 v8.1 給 >+15% 最高 14 分)--')
for mb in ['>+15%', '+5~15%', '0~+5%', '<0%']:
    out('  ' + stats([r for r in rows if ma_bucket(r) == mb], mb))

out('-- 單看法人排名 --')
for rb in ['TOP5', 'TOP6-15', 'TOP16+', '不在TOP50買超']:
    out('  ' + stats([r for r in rows if rank_bucket(r) == rb], rb))

out('-- 交叉:排名 × 乖離 --')
cell = defaultdict(list)
for r in rows:
    cell[(rank_bucket(r), ma_bucket(r))].append(r)
for rb in ['TOP5', 'TOP6-15', 'TOP16+', '不在TOP50買超']:
    for mb in ['>+15%', '+5~15%', '0~+5%', '<0%']:
        rs = cell.get((rb, mb), [])
        if len(rs) >= 5:
            out('  ' + stats(rs, f'{rb} × {mb}'))

# 規則 B 模擬:排除「已擁擠」= vs_ma20 > +15%(乖離過大)
out()
out('-- 規則模擬:候選擁擠條件比較 --')
for cond_name, cond in [
    ('排除 vs_ma20>+15%', lambda r: (r['vs_ma20'] or 0) > 15),
    ('排除 vs_ma20>+10%', lambda r: (r['vs_ma20'] or 0) > 10),
    ('排除 TOP5+乖離>+5%', lambda r: r['avg_rank'] is not None and r['avg_rank'] <= 5 and (r['vs_ma20'] or 0) > 5),
    ('排除 5日漲>10%(已大漲)', lambda r: (r['chg5d'] or 0) > 10),
]:
    kill = [r for r in rows if cond(r)]
    keep = [r for r in rows if not cond(r)]
    out(f'  ▶ {cond_name}')
    out('    被排除的 ' + stats(kill, ''))
    out('    留下的   ' + stats(keep, ''))
    killed_winners = [r for r in kill if r['result'] == 'success' and (r['ret'] or 0) > 10]
    out(f'    誤殺大贏家(賺>10%): {len(killed_winners)} 筆 ' +
        (str([f"{x['name']}{x['ret']:+.0f}%" for x in killed_winners[:6]]) if killed_winners else ''))

# ============ 分析三:大盤降級規則 ============
out()
out('【分析三】大盤短期降級規則')
tdays = sorted(taiex.keys())

def taiex_ma20(date):
    upto = [d for d in tdays if d <= date]
    if len(upto) < 20: return None, None
    ma = sum(taiex[d] for d in upto[-20:]) / 20
    return taiex[upto[-1]], ma

fdays = sorted(d for d in flows if flows[d] is not None)
def foreign_state(date):
    """回傳 (連賣天數, 近5日累計億) 以 date 前一交易日為準(盤前可知)"""
    prior = [d for d in fdays if d < date]
    if len(prior) < 5: return None, None
    streak = 0
    for d in reversed(prior):
        if flows[d] < 0: streak += 1
        else: break
    cum5 = sum(flows[d] for d in prior[-5:])
    return streak, cum5

day_state = {}
for r in rows:
    if r['date'] not in day_state:
        cur, ma = taiex_ma20(r['date'])
        streak, cum5 = foreign_state(r['date'])
        below = (cur < ma) if cur and ma else None
        day_state[r['date']] = {'below_ma20': below, 'streak': streak, 'cum5': cum5}
    r['_ds'] = day_state[r['date']]

# 觸發條件測試
for name, trig in [
    ('外資連賣≥3日', lambda s: (s['streak'] or 0) >= 3),
    ('外資連賣≥5日', lambda s: (s['streak'] or 0) >= 5),
    ('近5日外資累計≤-1000億', lambda s: s['cum5'] is not None and s['cum5'] <= -1000),
    ('近5日累計≤-1000億 或 連賣≥4日', lambda s: (s['cum5'] is not None and s['cum5'] <= -1000) or (s['streak'] or 0) >= 4),
    ('指數跌破月線(盤前)', lambda s: s['below_ma20'] is True),
    ('雙重:外資弱(上條) 且 跌破月線', lambda s: ((s['cum5'] is not None and s['cum5'] <= -1000) or (s['streak'] or 0) >= 4) and s['below_ma20'] is True),
]:
    on = [r for r in rows if trig(r['_ds'])]
    off = [r for r in rows if not trig(r['_ds'])]
    on_days = len({r['date'] for r in on})
    out(f'  ▶ 觸發「{name}」({on_days} 個推薦日)')
    out('    觸發日推薦 ' + stats(on, ''))
    out('    正常日推薦 ' + stats(off, ''))

# 06/25 之後每天的狀態(對照近期慘況)
out()
out('-- 近期各推薦日盤前狀態 --')
for d in sorted({r['date'] for r in rows if r['date'] >= '2026-06-25'}):
    s = day_state[d]
    sub = [r for r in rows if r['date'] == d]
    w = sum(1 for r in sub if r['result'] == 'success')
    out(f"  {d}: 外資連賣{s['streak']}日 近5日{s['cum5']:+.0f}億 跌破月線={s['below_ma20']} → 推{len(sub)}筆 {w}勝{len(sub)-w}敗")

with open(os.path.join(SP, 'backtest_report.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(P))
