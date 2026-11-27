"""盤中取價（唯讀）：現價=Yahoo meta.regularMarketPrice；前收=get_close_series 中日期<今日的末根"""
import sys, json, time, datetime as dt, urllib.request
sys.path.insert(0, 'scripts')
import settlement_checker as sc

TODAY = '2026-11-27'


def meta(sym):
    for suf in (['.TW', '.TWO'] if not sym.startswith('^') else ['']):
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}{suf}?range=5d&interval=1d'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                m = json.load(r)['chart']['result'][0]['meta']
            if m.get('regularMarketPrice') is not None:
                return m
        except Exception:
            pass
    return None


out = {}
for code in sys.argv[1:]:
    m = meta(code)
    price = ts = hi = lo = None
    if m:
        price = m['regularMarketPrice']
        ts = dt.datetime.fromtimestamp(m['regularMarketTime'], dt.timezone(dt.timedelta(hours=8))).strftime('%m-%d %H:%M')
        hi, lo = m.get('regularMarketDayHigh'), m.get('regularMarketDayLow')
    prev = []
    if code.startswith('^'):
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}?range=10d&interval=1d'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            j = json.load(r)['chart']['result'][0]
        for t, c in zip(j['timestamp'], j['indicators']['quote'][0]['close']):
            d = dt.datetime.fromtimestamp(t, dt.timezone(dt.timedelta(hours=8))).strftime('%Y-%m-%d')
            if d < TODAY:
                prev.append((d, c))
    else:
        s = sc.get_close_series(code) or []
        prev = [(str(d)[:10], c) for d, c in s if str(d)[:10] < TODAY]
    last3 = prev[-3:]
    pc = last3[-1][1] if last3 else None
    chg = round((price / pc - 1) * 100, 2) if price and pc else None
    # 2日累計：以前兩個交易日的前一日收盤為基準（T-2 收盤 → 現價）
    two = round((price / last3[-2][1] - 1) * 100, 2) if price and len(last3) >= 2 and last3[-2][1] else None
    out[code] = dict(price=price, time=ts, high=hi, low=lo, prev=pc, prev_date=last3[-1][0] if last3 else None,
                     chg=chg, two_day=two, last3=last3)
    print(code, f'現價={price} ({ts}) 高={hi} 低={lo} 前收={pc} 當日={chg}% 2日={two}%', last3)
    time.sleep(0.3)

json.dump(out, open('data/2026-11-27/_intraday/prices.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
