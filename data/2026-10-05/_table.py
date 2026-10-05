import json
T='2026-10-05'
out=json.load(open(f'data/{T}/pool_table.json',encoding='utf-8'))
LAB={'1326':'✅ **推薦**','2609':'⏳ 沿用追蹤（列榜）','3711':'⏳ 沿用追蹤（列榜）','3035':'⏳ 沿用追蹤（列榜）',
'6257':'⏳ 沿用追蹤（不列榜）','3037':'⏳ 沿用追蹤（不列榜）','8150':'⏳ 沿用追蹤（不列榜）','2327':'⏳ 沿用追蹤（不列榜）',
'2330':'🛑 已決事項開盤出場','2379':'🛑 已決事項開盤出場','3231':'🛑 已決事項開盤出場','2344':'🛑 已決事項開盤出場','4938':'🛑 已決事項開盤出場（yaml 持倉）',
'2867':'⏸️ 序列停滯凍結（不評分）'}
rows=[]
for o in sorted(out,key=lambda o:-o['total']):
    lv={-1:'不明'}.get(o['level'],f"L{o['level']}")
    ms=' '.join(f'{k}{v:+d}' for k,v in o['mods']) or '—'
    ex='；'.join(o['excl'])
    lab=LAB.get(o['code'])
    if lab: concl=lab+(('；'+ex) if ex else '')
    elif ex: concl='❌ '+ex
    else: concl='✅'
    name=o['name'] if o['name']!='?' else '三商壽'
    rows.append(f"| {o['code']} {name} | {lv} | {o['avg_rank'] if o['avg_rank'] is not None else '—'} | {o['total_k']:+,} | {o['cum']} | {o['bs']} | {o['consec']} | {o['f5']} | {o['mom']} | {o['vs_ma20']} | {o['news']}/{o['inst']}/{o['ind']}/{o['tech']}/{o['price']}={o['sub']} | {ms} | {o['total']} | {concl}｜{o['note']} |")
open(f'data/{T}/_table.txt','w',encoding='utf-8').write('\n'.join(rows))
print(len(rows))
