import json
f='data/tracking/tracking_2026-10-05.json'
t=json.load(open(f,encoding='utf-8'))
rows=json.load(open('data/2026-10-05/_after/holding_rows.json',encoding='utf-8'))
DEC='2026-10-05 盤後（10-05 T86 於 16:20 公布後掃描）'
E=lambda c,cat,reason:{'stock_code':c,'stock_name':rows[c]['name'],'category':cat,'recommend_date':rows[c]['date'],'recommend_price':rows[c]['p'],
   'last_close':rows[c]['cl'],'return_pct_at_close':rows[c]['ret'],'reason':reason,'decided_on':DEC}
t['tomorrow_opening_exits']=[
 E('2609','鐵律③ L4','10-05 T86 賣超 -2,729 張（外資 -2,394／投信 -59／自營 -277）＝18.3%（≥8%，不受 v8.3.3 保護）；D2 轉 L4；10-06 開盤出場，入帳價用 10-06 收盤（v8.3.2）'),
 E('2327','鐵律③ L4','10-05 T86 賣超 -9,285 張（外資 -12,366／投信 +3,094／自營 -13）＝17.2%（≥8%）；D1 轉 L4；10-06 開盤出場，入帳價用 10-06 收盤（v8.3.2）'),
 E('6257','鐵律③ L4','10-05 T86 賣超 -1,131 張（外資 -1,557／投信 +432／自營 -7）＝8.8%（≥8%，不受 v8.3.3 保護）；D2 轉 L4；10-06 開盤出場，入帳價用 10-06 收盤（v8.3.2）。10/06 14:30 另有法說會'),
]
t['tomorrow_pending_review']=[
 dict(E('8150','⚠️ 待複核（v8.3.3）','10-05 T86 賣超 -4,355 張（外資 -4,589／投信 +396／自營 -162）＝5.7%（<8%）且 10 日累計三大法人 +70,710 張為正 → 不開盤出場，列待複核；10-06 12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-07 開盤出場，任一次降級則維持追蹤。同時觸及停損 103.95 或 2 日 -10% 則立即出場。⚠️ 自算處置預警連續達標 4 天、最快 10-06 處置'),
      sell_ratio_pct=5.7,cum10=70710,review_1='10-06 12:30',review_2='10-06 盤後',timer_started='2026-10-05 盤後'),
 dict(E('1326','⚠️ 待複核（v8.3.3）','10-05 T86 賣超 -2,094 張（外資 -1,788／投信 0／自營 -307）＝6.9%（<8%）且 10 日累計三大法人 +13,405 張為正 → 不開盤出場，列待複核；10-06 12:30 與盤後各複核一次，兩次皆 ≥5% 才於 10-07 開盤出場。🔥覆寫型推薦 D0 即轉 L4'),
      sell_ratio_pct=6.9,cum10=13405,review_1='10-06 12:30',review_2='10-06 盤後',timer_started='2026-10-05 盤後'),
]
json.dump(t,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(t['tomorrow_opening_exits']),len(t['tomorrow_pending_review']))
