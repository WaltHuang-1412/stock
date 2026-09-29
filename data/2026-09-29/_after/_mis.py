import sys,json,time,urllib.request
codes=sys.argv[1].split(',')
out={}
def fetch(chs):
    url='https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch='+'|'.join(chs)+'&json=1&delay=0'
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://mis.twse.com.tw/stock/index.jsp'})
    return json.load(urllib.request.urlopen(req,timeout=15)).get('msgArray',[])
for i in range(0,len(codes),5):
    grp=codes[i:i+5]
    for attempt in range(3):
        try:
            arr=fetch([f'tse_{c}.tw' for c in grp]+[f'otc_{c}.tw' for c in grp])
            for a in arr:
                out[a['c']]=dict(name=a.get('n'),z=a.get('z'),y=a.get('y'),d=a.get('d'),t=a.get('t'),v=a.get('v'),o=a.get('o'),h=a.get('h'),l=a.get('l'))
            if all(c in out for c in grp): break
        except Exception as e:
            print('err',grp,e)
        time.sleep(2)
    time.sleep(1.5)
for c in codes: print(c,out.get(c))
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
