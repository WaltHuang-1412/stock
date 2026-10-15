import sys, json, re
sys.path.insert(0, 'scripts')
import official_attention as oa
d = oa.load()
disposed, attention, warn = oa.get_lists(d)
names = {}
per = {}
for r in d['twse_punish']:
    if re.fullmatch(r'\d{4}', r['Code']):
        names[r['Code']] = r['Name']; per[r['Code']] = r['DispositionPeriod'] + '｜' + r.get('DispositionMeasures', '') + '｜' + r.get('ReasonsOfDisposition', '')
for r in d['tpex_punish']:
    c = r['SecuritiesCompanyCode']
    names[c] = r['CompanyName']; per[c] = r['DispositionPeriod'] + '｜' + r.get('DispositionReasons', '')
for r in d['twse_notice']:
    names.setdefault(r['code'], r['name'])
for r in d['tpex_notice']:
    names.setdefault(r['SecuritiesCompanyCode'], r['CompanyName'])
pool = open('data/2026-10-15/_score_pool.txt').read().split() + ['2867', '6770', '2337', '2313', '3090', '1301', '4938', '2330', '3035', '3037', '3023']
print('處置', sorted(disposed))
for c in sorted(disposed):
    print('  ', c, names.get(c), per.get(c))
print('注意', sorted(attention))
print('注意(含名)', [(c, names.get(c)) for c in sorted(attention)])
print('預警warn', sorted(warn), [(c, names.get(c)) for c in sorted(warn)])
print('池∩處置', sorted(set(pool) & disposed), '池∩注意', sorted(set(pool) & attention), '池∩warn', sorted(set(pool) & warn))
json.dump(dict(disposition=sorted(disposed), attention=sorted(attention), warn=sorted(warn), names={c: names.get(c) for c in set(disposed) | attention | warn}, periods={c: per.get(c) for c in disposed}),
          open('data/2026-10-15/disposition_lists.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
