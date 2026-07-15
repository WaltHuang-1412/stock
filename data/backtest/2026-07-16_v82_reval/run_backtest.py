# -*- coding: utf-8 -*-
"""v8.2 規則重驗(樣本 553 筆)+ T86 滯後盲區回測"""
import json, os, datetime
from collections import defaultdict

SP = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SP, 'backtest_dataset.json'), encoding='utf-8') as f:
    rows = json.load(f)
with open(os.path.join(SP, 'taiex_series.json'), encoding='utf-8') as f:
    taiex = json.load(f)

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
out('v8.2 規則重驗 + T86 滯後回測(2026-07-16)')
out(f'樣本:{len(rows)} 筆已結算推薦({rows[0]["date"]} ~ {rows[-1]["date"]})')
out(f'其中殭屍清理批次 {sum(1 for r in rows if r.get("zombie"))} 筆、一般結算 {sum(1 for r in rows if not r.get("zombie"))} 筆')
out('=' * 70)

# ============ 分析零:殭屍批次偏差檢查 ============
out()
out('【分析零】殭屍批次 vs 一般結算(檢查樣本擴充是否引入系統性偏差)')
zom = [r for r in rows if r.get('zombie')]
reg = [r for r in rows if not r.get('zombie')]
out('  ' + stats(zom, '殭屍批次'))
out('  ' + stats(reg, '一般結算'))

# ============ 分析一:分數帶 × 時期 ============
out()
out('【分析一】分數帶命中率 × 時期(v8.2 於 07-09 上線)')
periods = [('早期(2025-12-02~2026-01-15)', '2025-12-02', '2026-01-15'),
           ('v8.0 期(01-16~04-23)', '2026-01-16', '2026-04-23'),
           ('v8.1 期(04-24~06-24)', '2026-04-24', '2026-06-24'),
           ('過渡期(06-25~07-08)', '2026-06-25', '2026-07-08'),
           ('v8.2 期(07-09~07-14)', '2026-07-09', '2026-07-14')]
for period, lo, hi in periods:
    sub = [r for r in rows if lo <= r['date'] <= hi]
    out(f'-- {period} 共{len(sub)}筆 --')
    for b in ['90+', '80-89', '70-79', '<70']:
        bs = [r for r in sub if band(r['score']) == b]
        if bs:
            out('  ' + stats(bs, b))
out('-- 全樣本分數帶 --')
for b in ['90+', '80-89', '70-79', '<70']:
    out('  ' + stats([r for r in rows if band(r['score']) == b], b))

# ============ 分析二:法人現身門檻重驗 ============
out()
out('【分析二】法人現身門檻(v8.2:不在當日TOP50買超 × 乖離0~+5% → 不推薦)')
avail = [r for r in rows if r.get('top50_available')]
out(f'(僅取當日 institutional_top50.json 存在的 {len(avail)} 筆)')

def ma_bucket(r):
    v = r['vs_ma20']
    if v is None: return '?'
    if v > 15: return '>+15%'
    if v > 5: return '+5~15%'
    if v > 0: return '0~+5%'
    return '<0%'

out('-- 在/不在 TOP50 買超名單 × 月線乖離 --')
for in50, tag in [(True, '在TOP50買超'), (False, '不在TOP50買超')]:
    for mb in ['>+15%', '+5~15%', '0~+5%', '<0%']:
        rs = [r for r in avail if r['in_top50_buy'] is in50 and ma_bucket(r) == mb]
        if len(rs) >= 5:
            out('  ' + stats(rs, f'{tag} × {mb}'))

gate = [r for r in avail if r['in_top50_buy'] is False and ma_bucket(r) == '0~+5%']
out('-- 門檻命中區(不在TOP50買超 × 0~+5%)--')
out('  ' + stats(gate, '全樣本'))
out('  ' + stats([r for r in gate if not r.get('zombie')], '排除殭屍批次'))
out('  ' + stats([r for r in gate if r['date'] >= '2026-07-09'], 'v8.2 上線後'))
killed_winners = [r for r in gate if r['result'] == 'success' and (r['ret'] or 0) > 10]
out(f'  誤殺大贏家(賺>10%): {len(killed_winners)} 筆 ' +
    (str([f"{x['date']} {x['name']}{x['ret']:+.0f}%" for x in killed_winners[:8]]) if killed_winners else ''))

# ============ 分析三:高乖離+法人前排(最強訊號重驗)============
out()
out('【分析三】高乖離+法人前排(v8.2 判定為最強訊號 81-88%,重驗)')
def rank_bucket(r):
    a = r['avg_rank']
    if a is None: return '不在TOP50買超'
    if a <= 5: return 'TOP5'
    if a <= 15: return 'TOP6-15'
    return 'TOP16+'
cell = defaultdict(list)
for r in avail:
    cell[(rank_bucket(r), ma_bucket(r))].append(r)
for rb in ['TOP5', 'TOP6-15', 'TOP16+', '不在TOP50買超']:
    for mb in ['>+15%', '+5~15%', '0~+5%', '<0%']:
        rs = cell.get((rb, mb), [])
        if len(rs) >= 5:
            out('  ' + stats(rs, f'{rb} × {mb}'))
strong = [r for r in avail if r['avg_rank'] is not None and r['avg_rank'] <= 15 and (r['vs_ma20'] or 0) > 5]
out('-- 前排(avg_rank≤15) × 乖離>+5% 合併 --')
out('  ' + stats(strong, '全樣本'))
out('  ' + stats([r for r in strong if not r.get('zombie')], '排除殭屍批次'))

# ============ 分析四:T86 滯後盲區 ============
out()
out('【分析四】T86 滯後(連假/颱風後首個交易日推薦是否更差)')
tdays = sorted(taiex.keys())

def cal_gap(date):
    """推薦日與前一交易日的日曆日差(=盤前可得 T86 的新鮮度)"""
    prior = [d for d in tdays if d < date]
    if not prior:
        return None, None
    prev = prior[-1]
    g = (datetime.date.fromisoformat(date) - datetime.date.fromisoformat(prev)).days
    return g, prev

day_gap = {}
for r in rows:
    if r['date'] not in day_gap:
        day_gap[r['date']] = cal_gap(r['date'])
    r['_gap'] = day_gap[r['date']][0]

buckets = [('正常日(gap=1)', lambda g: g == 1),
           ('週末後(gap=2-3)', lambda g: g in (2, 3)),
           ('連假/颱風後(gap≥4)', lambda g: g is not None and g >= 4)]
for name, cond in buckets:
    rs = [r for r in rows if cond(r['_gap'])]
    days = len({r['date'] for r in rs})
    out('  ' + stats(rs, f'{name} [{days}個推薦日]'))

out('-- gap≥4 各推薦日明細 --')
for d in sorted({r['date'] for r in rows if (day_gap[r['date']][0] or 0) >= 4}):
    sub = [r for r in rows if r['date'] == d]
    w = sum(1 for r in sub if r['result'] == 'success')
    g, prev = day_gap[d]
    out(f'  {d}(前一交易日 {prev},gap={g}): 推{len(sub)}筆 {w}勝{len(sub)-w}敗')

out('-- 提案模擬:gap≥4 時門檻 80→85 --')
long_gap = [r for r in rows if (r['_gap'] or 0) >= 4]
out('  ' + stats([r for r in long_gap if (r['score'] or 0) >= 85], 'gap≥4 且 score≥85(保留)'))
out('  ' + stats([r for r in long_gap if (r['score'] or 0) < 85], 'gap≥4 且 score<85(被砍)'))
out('-- 對照:正常日同分數帶 --')
normal = [r for r in rows if r['_gap'] == 1]
out('  ' + stats([r for r in normal if (r['score'] or 0) >= 85], 'gap=1 且 score≥85'))
out('  ' + stats([r for r in normal if (r['score'] or 0) < 85], 'gap=1 且 score<85'))

with open(os.path.join(SP, 'backtest_report.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(P))
print()
print('報告已存 backtest_report.txt')
