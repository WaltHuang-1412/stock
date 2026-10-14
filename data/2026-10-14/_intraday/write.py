import json
px={k:v[0] for k,v in json.load(open('data/2026-10-14/_intraday_px.json')).items()}
p='data/tracking/tracking_2026-10-14.json'
t=json.load(open(p,encoding='utf-8'))
D={'3443':5,'3231':2,'3711':2,'8046':2,'3189':2,'3037':2,'2002':1,'2886':1,'2892':1}
why={
'3231':('法人10日累計仍買超約4.6萬張、股價還在低檔整理，且是AI伺服器大廠','法人沒有出貨跡象、離停損還有9.5%，續抱'),
'8046':('ABF載板缺貨題材＋9月營收年增58%，法人持續小量買進','今日跌至-4.4%、離停損僅5.9%；法人未賣，續抱但不加碼，收盤再看'),
'3189':('同為ABF載板缺貨題材，營收年增44%，法人10日累計買超','跌幅-3.3%、法人仍小買，續抱不加碼（同族群3檔勿再加）'),
'2002':('外資近5天買超約4.8萬張、鋼價連兩月調漲，股價還沒漲多','今日+1.6%、法人續買，續抱'),
'2886':('外資＋投信同步連買5天，公股金控合併題材，價位不高','法人續買、略漲，續抱；金融股同族群不再加碼'),
'3443':('AI客製化晶片(ASIC)題材，9月營收年增近1倍，法人連買6天','今日自低點回升，離停損5.9%；法人買超量小，續抱觀察、不加碼'),
'2892':('外資近5天買超2.1萬張，9月獲利公告亮眼，價位低','法人續買、小漲，續抱；金融股同族群不再加碼'),
'3037':('ABF載板題材，原本法人小幅買超','法人10-13改為大賣（賣超佔比約18%）＋工安意外公告，已被判定出場；現價離停損1143僅3.2%，開盤已決出場，尚未賣者今天先處理'),
'3711':('AI封測題材，法人原本小買','法人10-13轉賣（佔比約20%，遠超門檻）、美股設備股重挫，已決出場；今日小漲不改決議'),
}
recs={r['stock_code']:r for r in t['recommendations']}
lines=[];rows=[]
for c,r in recs.items():
    now=px[c];rp=r['recommend_price']
    r['intraday_price']=now;r['intraday_change_pct']=round((now/rp-1)*100,2)
    r['intraday_note']='盤中12:12 Yahoo regularMarketPrice；D{}/10 照抄 settlement_checker'.format(D[c])
    if r.get('result') is None: r['result']='holding'
    r['to_target']=round((r['target_price']/now-1)*100,1);r['to_stop']=round((now/r['stop_loss']-1)*100,1)
    rows.append(f"| {c} {r['stock_name']} | {rp}→{now}（{r['intraday_change_pct']:+.1f}%） | {r['to_target']}%／{r['to_stop']}% | D{D[c]}/10 |")
    lines.append((c,r))
t['intraday_status']={'time':'2026-10-14 12:30','price_source':'Yahoo regularMarketPrice 12:12','track_b_note':'今日無盤中新推薦','holdings_stop_check':{'6770':'71.0<73.26 觸及','2337':'110.0<147.6 觸及','3090':'183.5<256.5 觸及','2313':'246.0>235.98 未觸發','1301':'88.9>54.08 未觸發','4938':'100.0>76.5 未觸發','2330':'無停損欄'}}
t['track_b_recommendations']=t.get('track_b_recommendations') or []
t['tomorrow_opening_exits']=t.get('tomorrow_opening_exits') or []
json.dump(t,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
open('data/2026-10-14/_intraday/rows.txt','w',encoding='utf-8').write('\n'.join(rows))
# LINE
L=["【盤中 10/14 12:30】","大盤多頭；今日無盤中新推薦（偵測器強訊號 1314 中石化+3.2%、1310 台苯+4.4% 已漲、8442 威宏法人僅買7張，皆不符）","",
"🛑 已決出場（沿用不重評）：","・持倉 6770 力積電 71.0／2337 旺宏 110.0／3090 日電貿 183.5：仍低於停損（73.26／147.6／256.5）","・2313 華通 246（距停損4.2%）、4938 和碩 100、2330 台積電零股、1301 台塑 88.9（+9.9%今日，獲利約+38%超停利20%）依10-13定案出場","・追蹤 3037 欣興、3711 日月光投控：法人10-13大賣（約18%／20%）→出場","","📋 推薦股現況與原因"]
for c,r in lines:
    w=why[c]
    L+=[f"{c} {r['stock_name']}｜{r['recommend_price']}→{px[c]}（{r['intraday_change_pct']:+.1f}%）｜距目標 {r['to_target']}%／距停損 {r['to_stop']}%｜D{D[c]}/10",f"💡 當初為什麼推：{w[0]}",f"👉 現在怎麼辦：{w[1]}",""]
L+=["2867 三商壽：價格資料停在08-19，判定凍結。","⚠️ 風險：10/15台積電法說，AI/載板/封測族群同步波動；今日T86下午4點後才公布，以上法人數據為10-13。"]
s='\n'.join(L)
open('data/2026-10-14/intraday_line.txt','w',encoding='utf-8').write(s);print(len(s))
