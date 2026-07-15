# -*- coding: utf-8 -*-
"""建回測資料集:每筆已結算推薦 join 推薦當日的因子原始值(v8.2 重驗版,含 2025 檔案+殭屍批次標記)"""
import json, glob, os

ROOT = '/Users/walter/Documents/GitHub/stock'
SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SP, 'backtest_dataset.json')

# 0. 殭屍清理批次 (rec_date, code) 集合
zombie_keys = set()
zpath = os.path.join(ROOT, 'data/predictions/zombie_cleanup_2026-07-13.json')
with open(zpath, encoding='utf-8') as f:
    z = json.load(f)
for s in z.get('settlements', []):
    zombie_keys.add((s.get('rec_date'), str(s.get('code'))))
for s in z.get('ghost_settled', []):
    zombie_keys.add((s.get('rec_date') or s.get('date'), str(s.get('code') or s.get('symbol'))))
print(f'殭屍批次標記: {len(zombie_keys)} 筆')

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
for tf in sorted(glob.glob(os.path.join(ROOT, 'data/tracking/tracking_20*.json'))):
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
            if not isinstance(rp, (int, float)):
                rp = r.get('recommend_price')
            ret = None
            if isinstance(rp, (int, float)) and isinstance(sp, (int, float)) and rp:
                ret = (sp - rp) / rp * 100
            rows.append({
                'date': date, 'code': code, 'name': r.get('stock_name'),
                'industry': r.get('industry'), 'score': r.get('score'),
                'track': 'B' if sec.startswith('track_b') else 'A',
                'result': p['result'], 'ret': ret,
                'recommend_price': rp, 'settled_price': sp,
                'settled_date': p.get('settled_date'),
                'holding_days': p.get('holding_days'),
                'zombie': (date, code) in zombie_keys,
            })

# 去重(同日同股票只留一筆,tracking 檔可能重複)
seen = set()
dedup = []
for r in rows:
    k = (r['date'], r['code'])
    if k in seen:
        continue
    seen.add(k)
    dedup.append(r)
rows = dedup

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

for r in rows:
    t50 = get_top50(r['date'])
    r['top50_available'] = bool(t50)
    s = t50.get(r['code'])
    # 在當日 TOP50「買超」名單 = total > 0；檔案不存在時為 None(無法判定)
    r['in_top50_buy'] = (bool(s and (s.get('total') or 0) > 0)) if t50 else None
    r['avg_rank'] = s.get('avg_rank') if s else None
    r['buy_ratio'] = s.get('buy_ratio') if s else None
    r['chg5d'] = s.get('5day_change') if s else None
    p = get_pp(r['date']).get(r['code'])
    r['vs_ma20'] = p.get('vs_ma20') if p else None
    r['vs_ma60'] = p.get('vs_ma60') if p else None

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)

n = len(rows)
print(f'總結算筆數: {n}(殭屍批次 {sum(1 for r in rows if r["zombie"])} 筆)')
print(f'有 score: {sum(1 for r in rows if r["score"] is not None)}')
print(f'有 ret: {sum(1 for r in rows if r["ret"] is not None)}')
print(f'有 avg_rank(當日在TOP50買超): {sum(1 for r in rows if r["avg_rank"] is not None)}')
print(f'有 vs_ma20: {sum(1 for r in rows if r["vs_ma20"] is not None)}')
print(f'日期範圍: {rows[0]["date"]} ~ {rows[-1]["date"]}')
