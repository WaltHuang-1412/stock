# -*- coding: utf-8 -*-
"""抓 TWSE BFI82U 外資每日買賣差額序列(2026-01 ~ 2026-07)"""
import json, os, time
import requests

SP = os.path.dirname(os.path.abspath(__file__))
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

with open(os.path.join(SP, 'taiex_series.json'), encoding='utf-8') as f:
    taiex = json.load(f)
trading_days = sorted(d for d in taiex if '2026-01-01' <= d <= '2026-07-08')

OUT = os.path.join(SP, 'foreign_flows.json')
flows = {}
if os.path.exists(OUT):
    with open(OUT, encoding='utf-8') as f:
        flows = json.load(f)

def fetch(yyyymmdd):
    try:
        url = f'https://www.twse.com.tw/rwd/zh/fund/BFI82U?dayDate={yyyymmdd}&type=day&response=json'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        d = resp.json()
        if d.get('stat') != 'OK':
            return None
        for row in d.get('data', []):
            if row[0].startswith('外資及陸資('):
                return round(float(row[3].replace(',', '')) / 1e8, 1)  # 億
    except Exception:
        return None
    return None

for i, day in enumerate(trading_days):
    if day in flows:
        continue
    flows[day] = fetch(day.replace('-', ''))
    time.sleep(0.35)
    if (i + 1) % 30 == 0:
        print(f'{i+1}/{len(trading_days)}')
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(flows, f)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(flows, f)

ok = sum(1 for v in flows.values() if v is not None)
print(f'完成: {ok}/{len(trading_days)} 天有外資數據')
recent = sorted(flows.items())[-8:]
for d, v in recent:
    print(d, v)
