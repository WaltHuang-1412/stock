import re,sys,io
t=open(sys.argv[1],encoding='utf-8',errors='replace').read()
blocks=re.split(r'\n={20,}\n📊 ',t)[1:]
print(f"{'stock':14}{'累計三大':>9}{'累計外資':>9}{'累計投信':>9}{'真連買':>6}{'買/賣':>7}{'近5三大':>9}{'近5外資':>9}{'動能':>9}")
for b in blocks:
    name=b.split('\n',1)[0].split(' 籌碼')[0]
    def g(p):
        m=re.search(p,b); return m.group(1).replace(',','') if m else '?'
    tot=g(r'累計淨買超（三大法人）:\s*([+\-\d,.]+K?)'); fo=g(r'累計淨買超（外資）\s*:\s*([+\-\d,.]+K?)'); tr=g(r'累計淨買超（投信）\s*:\s*([+\-\d,.]+K?)')
    cb=g(r'真連續買超:\s*(\d+)'); bd=g(r'買超天數:\s*(\d+)'); sd=g(r'賣超天數:\s*(\d+)')
    n5=g(r'近5天淨買超（三大法人）:\s*([+\-\d,.]+K?)'); f5=g(r'近5天淨買超（外資）\s*:\s*([+\-\d,.]+K?)'); mo=g(r'動能變化:\s*([+\-\d.]+%)')
    print(f"{name:14}{tot:>9}{fo:>9}{tr:>9}{cb:>6}{bd+'/'+sd:>7}{n5:>9}{f5:>9}{mo:>9}")
