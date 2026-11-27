import json,sys
sys.path.insert(0,'scripts')
from institutional_pattern_tracker import load_industry_map
D='data/2026-11-27'
J=lambda p:json.load(open(p,encoding='utf-8'))
chip=J(D+'/_chip_pool.json')
lv={r['stock_code']:r['level'] for r in J(D+'/_pool_rev/reversal_alerts.json')}
top={s['code']:s for s in J('data/2026-11-26/institutional_top50.json')['stocks']}
im=load_industry_map()
idx=lambda f:{x['code']:x for x in J(D+'/'+f)}
rv,ep,fr,pp=[idx(f) for f in ('revenue_check.json','eps_check.json','foreign_ratio_check.json','price_position_check.json')]
pool=open(D+'/_pool.txt').read().split()
n=0
for c in pool:
    ch=chip.get(c,{}); l=lv.get(c); mom=float(ch.get('mom') or 0)
    if l in (3,4) or mom>100 or l is None: continue
    s=top.get(c); r=rv.get(c,{}); e=ep.get(c,{}); f=fr.get(c,{}); p=pp.get(c,{})
    n+=1
    print(c,ch.get('name'),f"L{l} mom{mom:+.0f} f5{ch.get('f5')} cons{ch.get('cons')} sd{ch.get('sd')}",
      f"| rk{s['avg_rank']} 5d{s['5day_change']:+.1f}" if s else '| -',
      f"| R{r.get('adj')} {r.get('yoy')} pb{r.get('pullback_5d')} {r.get('stale')} E{e.get('adj')} {e.get('latest_quarter')} F{(f.get('suggestion') or '')[:3]} {f.get('as_of')} P{p.get('adj')} ma20{p.get('vs_ma20')} | {im.get(c)}")
print(n)
