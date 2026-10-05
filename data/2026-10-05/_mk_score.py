src=open('data/2026-10-02/_score.py',encoding='utf-8').read()
a=src.index("# code:(時事,產業,催化對齊"); b=src.index("out=[]")
M=open('data/2026-10-05/_M.py',encoding='utf-8').read()
src=src[:a]+M+src[b:]
src=src.replace("T='2026-10-02'","T='2026-10-05'").replace("data/2026-10-01/institutional_top50.json","data/2026-10-02/institutional_top50.json")
src=src.replace("    if c in DISP: excl.insert(0,DISP[c])","    if c in DISP: excl.insert(0,DISP[c])\n    if c in LEADER_L3: excl.insert(0,'🚫 龍頭預警 Level 3（Western Digital -10.22%）直接排除')")
# 非 TOP50 個股無 5day_change 欄 → 以 get_close_series 自算（_d5.json）補上「已大漲」檢查
src=src.replace("    d5=(b or {}).get('5day_change')","    d5=(b or {}).get('5day_change')\n    if d5 is None and D5.get(c): d5=D5[c]['d5']")
src=src.replace('out=[]','D5=json.load(open("data/2026-10-05/_d5.json"))\nout=[]',1)
open('data/2026-10-05/_score.py','w',encoding='utf-8').write(src)
