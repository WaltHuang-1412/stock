import json
f='data/tracking/tracking_2026-10-02.json'
t=json.load(open(f,encoding='utf-8'))
rows=json.load(open('data/2026-10-02/_after/holding_rows.json',encoding='utf-8'))
E=lambda c,reason:{'stock_code':c,'stock_name':rows[c]['name'],'category':'鐵律③ L4','recommend_date':rows[c]['date'],'recommend_price':rows[c]['p'],
   'last_close':rows[c]['cl'],'return_pct_at_close':rows[c]['ret'],'reason':reason,'decided_on':'2026-10-02 盤後（10-02 T86 於 16:14 公布後掃描）'}
t['tomorrow_opening_exits']=[
 E('3231','10-02 T86 賣超 -22,097 張（外資 -21,169／投信 -1,345／自營 +417）＝68.8%（≥8%）；D0 即轉 L4（🔥超強催化覆寫推薦）；10-05 開盤出場，入帳價用 10-05 收盤（v8.3.2）'),
 E('2330','10-02 T86 賣超 -5,344 張（外資 -5,914／投信 +253／自營 +316）＝24.9%（≥8%）；D0 即轉 L4；10-05 開盤出場，入帳價用 10-05 收盤（v8.3.2）。my_holdings.yaml 列本股零股 0.15 張：若實際持有同樣適用鐵律③'),
 E('2344','10-02 T86 賣超 -7,123 張（外資 +2,135／投信 -10,190／自營 +931）＝11.4%（≥8%）；D0 即轉 L4（🔥超強催化覆寫推薦）；10-05 開盤出場，入帳價用 10-05 收盤（v8.3.2）'),
 E('2379','10-02 T86 賣超 -285 張（外資 -400／投信 +72／自營 +42）＝9.2%（≥8%，不受 v8.3.3 待複核保護）；D0 即轉 L4；10-05 開盤出場，入帳價用 10-05 收盤（v8.3.2）'),
 {'stock_code':'4938','stock_name':'和碩','category':'鐵律③ L4（my_holdings.yaml 持倉，不進 predictions）','recommend_date':None,'recommend_price':None,'last_close':89.2,'return_pct_at_close':None,
  'reason':'my_holdings.yaml 持倉 1 張（成本 85.0、停損 76.5）：10-02 T86 賣超 -2,218 張（外資 -2,405／投信 -68／自營 +254）＝23.5%（≥8%）→ 鐵律③ L4，10-05 開盤出場；停損價未觸及（89.2 > 76.5）。此為持倉決議，流程不代改 yaml',
  'decided_on':'2026-10-02 盤後（10-02 T86 於 16:14 公布後掃描）'}]
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(t['tomorrow_opening_exits']))
