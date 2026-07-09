# -*- coding: utf-8 -*-
"""建回測資料集:每筆已結算推薦 join 推薦當日的因子原始值"""
import json, glob, os, sys

ROOT = r'C:\Users\walter.huang\Documents\github\stock'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backtest_dataset.json')

# 1. predictions.json → 結算結果
with open(os.path.join(ROOT, 'data/predictions/predictions.json'), encoding='utf-8') as f:
    pred = json.load(f)
results = {}
for date, day in pred.items():
    if not isinstance(day, dict):
        continue
    for p in day.get('predictions', []):
        results[(date, str(p.get('symbol')))] = p

# 2. tracking → 推薦(score/industry/track/position)
rows = []
for tf in sorted(glob.glob(os.path.join(ROOT, 'data/tracking/tracking_2026-*.json'))):
    date = os.path.basename(tf)[9:19]
    try:
        with open(tf, encoding='utf-8') as f:
            t = json.load(f)
    except Exception:
        continue
    for sec in ('recommendations', 'track_b_recommendations'):
        for r in t.get(sec) or []:
            code = str(r.get('stock_code'))
            p = results.get((date, code))
            if not p or p.get('result') not in ('success', 'fail'):
                continue
            rp, sp = p.get('recommend_price'), p.get('settled_price')
            ret = (sp - rp) / rp * 100 if rp and sp else None
            rows.append({
                'date': date, 'code': code, 'name': r.get('stock_name'),
                'industry': r.get('industry'), 'score': r.get('score'),
                'track': 'B' if sec.startswith('track_b') else 'A',
                'result': p['result'], 'ret': ret,
                'recommend_price': rp, 'settled_price': sp,
                'settled_date': p.get('settled_date'),
                'holding_days': p.get('holding_days'),
            })

# 3. join 推薦當日 institutional_top50(avg_rank/buy_ratio/5day_change)
top50_cache = {}
def get_top50(date):
    if date not in top50_cache:
        path = os.path.join(ROOT, f'data/{date}/institutional_top50.json')
        m = {}
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    d = json.load(f)
                for s in d.get('stocks', []):
                    m[str(s['code'])] = s
            except Exception:
                pass
        top50_cache[date] = m
    return top50_cache[date]

# 4. join 推薦當日 price_position(vs_ma20/vs_ma60)
pp_cache = {}
def get_pp(date):
    if date not in pp_cache:
        path = os.path.join(ROOT, f'data/{date}/price_position_check.json')
        m = {}
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    d = json.load(f)
                items = d if isinstance(d, list) else d.get('results', d.get('stocks', []))
                for s in items:
                    m[str(s.get('code'))] = s
            except Exception:
                pass
        pp_cache[date] = m
    return pp_cache[date]

# 5. join 推薦當日 market_regime(taiex vs ma20 + 外資買賣文字)
regime_cache = {}
def get_regime(date):
    if date not in regime_cache:
        path = os.path.join(ROOT, f'data/{date}/market_regime.json')
        v = None
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    v = json.load(f)
            except Exception:
                pass
        regime_cache[date] = v
    return regime_cache[date]

for r in rows:
    s = get_top50(r['date']).get(r['code'])
    r['avg_rank'] = s.get('avg_rank') if s else None
    r['buy_ratio'] = s.get('buy_ratio') if s else None
    r['chg5d'] = s.get('5day_change') if s else None
    p = get_pp(r['date']).get(r['code'])
    r['vs_ma20'] = p.get('vs_ma20') if p else None
    r['vs_ma60'] = p.get('vs_ma60') if p else None
    g = get_regime(r['date'])
    if g:
        r['regime'] = g.get('regime')
        tx = g.get('taiex') or {}
        cur, ma20 = tx.get('current'), tx.get('ma20')
        r['taiex_vs_ma20'] = (cur - ma20) / ma20 * 100 if cur and ma20 else None
        r['regime_details'] = ' | '.join(g.get('details', [])) if g.get('details') else g.get('regime_detail', '')
    else:
        r['regime'] = None
        r['taiex_vs_ma20'] = None
        r['regime_details'] = None

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

n = len(rows)
print(f'總結算筆數: {n}')
print(f'有 score: {sum(1 for r in rows if r["score"] is not None)}')
print(f'有 ret: {sum(1 for r in rows if r["ret"] is not None)}')
print(f'有 avg_rank(當日在TOP50買超): {sum(1 for r in rows if r["avg_rank"] is not None)}')
print(f'有 vs_ma20: {sum(1 for r in rows if r["vs_ma20"] is not None)}')
print(f'有 regime: {sum(1 for r in rows if r["regime"] is not None)}')
print(f'日期範圍: {rows[0]["date"]} ~ {rows[-1]["date"]}')
