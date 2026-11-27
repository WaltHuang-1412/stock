import json, sys
sys.path.insert(0, 'scripts')
import settlement_checker as sc
import twse_institutional_cache as t86
A = 'data/2026-11-27/_after'
J = lambda p: json.load(open(p, encoding='utf-8'))
chip = J(A + '/chip_pool.json')
rv = {r['stock_code']: r for r in J(A + '/pool/reversal_alerts.json')}
top = {s['code']: s for s in J('data/2026-11-27/institutional_top50.json')['stocks']}
today = t86.fetch_all_institutional('20261127')
pool = open(A + '/pool.txt').read().split()
out = {}
bad = []
for c in pool:
    r = chip.get(c)
    if not r:
        print(c, 'NO CHIP (非上市/無資料)'); continue
    rows = sorted(r['history'], key=lambda x: x['date'], reverse=True)
    if rows[0]['date'] != '20261127': bad.append((c, rows[0]['date']))
    elif c in today and rows[0]['total'] != today[c]['total']: bad.append((c, 'mismatch'))
    s = r['summary']
    f5 = s['recent_5d']['foreign']; t10 = s['total_net']; cons = s['consecutive_buy']; sd = s['sell_days']
    mom = r['momentum']['change_pct'] if r.get('momentum') else None
    ser = sc.get_close_series(c)
    if not ser:
        print(c, 'NO SERIES'); continue
    d5 = (ser[-1][1] / ser[-6][1] - 1) * 100
    vals = [v for _, v in ser]
    ma20 = sum(vals[-20:]) / 20
    v20 = (vals[-1] / ma20 - 1) * 100
    out[c] = dict(name=r['stock_name'], lv=rv.get(c, {}).get('level'), f5=f5, t10=t10, cons=cons, sd=sd, mom=mom,
                  d5=round(d5, 2), v20=round(v20, 2), today=rows[0]['total'], intop=c in top,
                  close=vals[-1], last=str(ser[-1][0]))
json.dump(out, open(A + '/pool_summary.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('T86 date mismatch:', bad)
print('stale series:', [c for c, v in out.items() if v['last'] != '2026-11-27'])
for c, v in sorted(out.items(), key=lambda kv: (kv[1]['lv'] != 0, not kv[1]['intop'])):
    if v['lv'] not in (0, 1): continue
    flags = []
    if v['mom'] is not None and v['mom'] > 100: flags.append('動能>100')
    if v['d5'] > 10: flags.append('5d>10')
    if v['f5'] < 0: flags.append('f5<0')
    if not v['intop'] and 0 <= v['v20'] <= 5: flags.append('現身門檻')
    print(c, v['name'], 'L%s' % v['lv'], 'TOP' if v['intop'] else '', 'f5=%d t10=%d cons=%d sd=%d mom=%.0f d5=%.1f v20=%.1f today=%d' % (v['f5'], v['t10'], v['cons'], v['sd'], v['mom'] or 0, v['d5'], v['v20'], v['today']), ';'.join(flags) or 'PASS')
from collections import Counter
print(Counter(v['lv'] for v in out.values()))
