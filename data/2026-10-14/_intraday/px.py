import json,sys,urllib.request
codes="3231 8046 3189 2002 2886 3443 2892 3037 3711 6770 2337 3090 1301 2313 4938 2330 1314 8442 1310 2867".split()
out={}
for c in codes:
    for suf in (".TW",".TWO"):
        try:
            r=urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{c}{suf}?range=5d&interval=1d",headers={"User-Agent":"Mozilla/5.0"})
            d=json.load(urllib.request.urlopen(r,timeout=15))["chart"]["result"][0]
            m=d["meta"]
            import datetime
            out[c]=[m.get("regularMarketPrice"),m.get("regularMarketTime"),datetime.datetime.fromtimestamp(m["regularMarketTime"]).strftime("%m-%d %H:%M"),m.get("regularMarketVolume")]
            break
        except Exception as e:
            err=str(e)
    else: out[c]="ERR "+err
json.dump(out,open("data/2026-10-14/_intraday_px.json","w"),ensure_ascii=False)
for k,v in out.items(): print(k,v)
