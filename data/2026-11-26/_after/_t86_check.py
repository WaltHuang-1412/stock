import sys, json
sys.path.insert(0,'scripts')
import twse_institutional_cache as c
d = c.fetch_all_institutional('20261126')
print('fetched', len(d), 'cache path', c._cache_path('20261126'), c._cache_path('20261126').exists())
top = json.load(open('data/2026-11-26/institutional_top50.json', encoding='utf-8'))
print(list(top.keys()), top.get('date'))
for code in ['2610','2412','2886','2379','2615','6770','2337','2313','3090','1301','4938','2330']:
    r = d.get(code); print(code, r)
