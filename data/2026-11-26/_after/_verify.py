import json

p = json.load(open('data/predictions/predictions.json', encoding='utf-8'))
for k, v in p.items():
    if not isinstance(v, dict) or 'predictions' not in v:
        continue
    for r in v['predictions']:
        if r.get('settled_date') == '2026-11-26' or k == '2026-11-26' or (r['symbol'] == '2886' and k >= '2026-11-01'):
            print(k, r['symbol'], r.get('recommend_price'), r['result'], r.get('settled_price'), r.get('return_pct'))
print({k: p[k] for k in ['settled_accuracy', 'settled_count', 'total_success', 'total_fail', 'holding_count']})
