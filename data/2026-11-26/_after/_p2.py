import json, sys
sys.path.insert(0,'scripts')
d=json.load(open('data/2026-11-26/stock_dossier_after2.json',encoding='utf-8'))
for c,v in d['stocks'].items():
    print(c,v['name'],v['events'],len(v['mentions']))
    for m in v['mentions']:
        if m['file'] in ('topic_tracker.md','tw_market_news.json','market_intelligence.md','us_leader_alerts.md'): print('  ',m['file'],m['line'],m['text'][:220])
h=json.load(open('data/2026-11-26/_after/chip_tb.json',encoding='utf-8'))['2603']['history']
for x in sorted(h,key=lambda x:x['date'],reverse=True): print(x['date'],x['total'],x['foreign'],x['trust'])
t=json.load(open('data/2026-11-26/institutional_top50.json',encoding='utf-8'))
print('2603 in top50', any(s['code']=='2603' for s in t['stocks'][:50]))


r=json.load(open('data/2026-11-26/_after/tb/reversal_alerts.json',encoding='utf-8'))
print([x for x in r if x['stock_code']=='2603'])
r=json.load(open('data/2026-11-26/_after/pool/reversal_alerts.json',encoding='utf-8'))
print([x for x in r if x['stock_code']=='8046'])
