"""收尾取價（唯讀）：TWSE MIS 即時報價；成交價缺值時取最佳買價（漲停鎖住 b=0 時取最高價）"""
import json, time, urllib.request, yaml

I = 'data/2026-11-27/_intraday'
codes = '2880 2603 2610 2412 2379 2615 6770 2337 2313 3090 1301 4938 2330 2891'.split()
res = {}


def f(m, k):
    v = m.get(k)
    return None if v in (None, '-', '') else float(v.split('_')[0])


for attempt in range(3):
    miss = [c for c in ['t00'] + codes if c not in res]
    if not miss:
        break
    for i in range(0, len(miss), 5):
        url = ('https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch='
               + '%7C'.join(f'tse_{c}.tw' for c in miss[i:i + 5]) + '&json=1&delay=0')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as r:
                for m in json.load(r).get('msgArray', []):
                    px = f(m, 'z') or f(m, 'b') or f(m, 'a') or f(m, 'h')
                    if px:
                        res[m['c']] = dict(price=px, open=f(m, 'o'), high=f(m, 'h'), low=f(m, 'l'), prev=f(m, 'y'), time=m.get('t'))
        except Exception as e:
            print('batch error', e)
        time.sleep(3)

pre = json.load(open(I + '/prices.json', encoding='utf-8')) if False else json.load(open('data/2026-11-27/_intraday/prices.json', encoding='utf-8'))
for c, r in res.items():
    key = '^TWII' if c == 't00' else c
    base = None
    if key in pre and pre[key].get('last3') and len(pre[key]['last3']) >= 2:
        base = pre[key]['last3'][-2][1]
    r['chg'] = round((r['price'] / r['prev'] - 1) * 100, 2)
    r['two_day'] = round((r['price'] / base - 1) * 100, 2) if base else None
    print(c, r['time'], r['price'], '開', r['open'], '高', r['high'], '低', r['low'], '昨', r['prev'], f"{r['chg']:+}%", '2日', r['two_day'])
json.dump(res, open(I + '/final_prices.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('--- 追蹤股')
t = json.load(open('data/tracking/tracking_2026-11-27.json', encoding='utf-8'))
for r in t['recommendations'] + t['carry_over_recommendations']:
    p = res.get(r['stock_code'])
    if not p:
        print(r['stock_code'], '查無')
        continue
    x = p['price']
    print(r['stock_code'], r['stock_name'], r['recommend_price'], x,
          f"損益{(x / r['recommend_price'] - 1) * 100:+.1f}% 距目標{(r['target_price'] / x - 1) * 100:.1f}% 距停損{(x - r['stop_loss']) / x * 100:.1f}% 停損{r['stop_loss']} 今日低{p['low']}")
print('--- 持倉')
d = yaml.safe_load(open('portfolio/my_holdings.yaml', encoding='utf-8'))
for h in d['holdings']:
    if not h.get('quantity'):
        continue
    c = h['symbol']
    p = res.get(c)
    if not p:
        print(c, h['name'], '查無')
        continue
    x, s = p['price'], h.get('stop_loss')
    print(c, h['name'], h['quantity'], x, s, (f"{(x / s - 1) * 100:+.1f}% vs 停損 {'觸及' if x < s else '未觸發'}" if s else '無停損欄'),
          f"成本損益{(x / h['buy_price'] - 1) * 100:+.1f}% 今日{p['chg']:+}% 2日{p['two_day']}")
print('--- 處置/注意交集')
txt = open(I + '/disposal.txt', encoding='utf-8').read().splitlines()
import ast
watch = set(codes) | set('3481 6770 2409 2317 2344 2327 2408 2324 1605 1301 2887 6505 2891 1101 2356 1326 2883 2355 4938 1303 2382 8150 4958 2492 7835 1453'.split())
for line in txt:
    k = line.split()[0]
    lst = ast.literal_eval(line[line.index('['):])
    print(k, sorted(watch & set(lst)))
