import sys,yaml; sys.path.insert(0,'scripts')
import settlement_checker as sc
d=yaml.safe_load(open('portfolio/my_holdings.yaml',encoding='utf-8'))
for h in d.get('holdings',[]):
    if not h.get('quantity'): continue
    if not h.get('stop_loss'): print(h['symbol'],h['name'],'無停損欄 qty',h['quantity']); continue
    s=sc.get_close_series(h['symbol'])
    if not s: print(h['symbol'],h['name'],'序列查詢失敗'); continue
    day,close=s[-1]
    print(f"{h['symbol']} {h['name']}｜{day} 收盤 {close}｜停損 {h['stop_loss']}｜{'TOUCH' if close<h['stop_loss'] else 'ok'}")
