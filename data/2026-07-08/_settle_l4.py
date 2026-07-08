# 2026-07-08 盤後：結算今日觸發強制出場的 tracking 追蹤股
# 依 CLAUDE.md 出場硬規則（停損價/連續重挫/法人反轉L3-4 任一觸發＝強制出場）
# 反轉數據 = 最新官方 T86 2026-07-07（07/08 尚未公布）
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SETTLE = {
    # code: (file, close, fail_reason)
    "2618": ("2026-07-01", 39.85, "D5觸停損：收盤39.85 ≤ 停損40.41（-11.2%），盤中最低39.55；記憶體/半導體國際Level3賣壓外溢，航空隨大盤重挫"),
    "2449": ("2026-07-01", 305.5, "D5強制出場：盤中303.50跌破停損303.75觸發（盤中/收盤<停損任一即出場）+反轉Level4爆量賣超-14,249張（佔日均量54.0%，T86 07/07），收盤305.5（-9.5%）"),
    "3711": ("2026-07-01", 625.0, "D5強制出場：反轉Level4爆量賣超-2,626張（佔日均量9.9%，T86 07/07），距停損僅2.1%；半導體設備/製造國際Level3預警未解除，收盤625（-8.1%）"),
    "6285": ("2026-07-01", 251.5, "D5強制出場：反轉Level4爆量賣超-1,200張（佔日均量26.8%，T86 07/07），法人反轉L3-4無例外規則，收盤251.5（-3.1%）"),
    "2303": ("2026-07-02", 163.0, "D4強制出場：反轉Level4爆量賣超-19,810張（佔日均量23.9%，T86 07/07）+已列TWSE處置股（近60日+171%）流動性風險，收盤163（-3.6%）"),
    "2409": ("2026-06-30", 29.55, "D6強制出場：反轉Level4爆量賣超-80,361張（佔日均量30.5%，T86 07/07，全場最大量出貨），收盤29.55（-3.4%）"),
    "3045": ("2026-06-25", 113.0, "D9強制出場：反轉Level4爆量賣超-3,093張（佔日均量14.3%，T86 07/07），收盤113（-5.4%），明日D10到期原亦低於推薦價"),
    "2301": ("2026-07-07", 214.0, "D1強制出場：反轉Level4爆量賣超-3,408張（佔日均量26.6%，T86 07/07），推薦次日即法人爆量出貨+連2日收黑破MA5，收盤214（-4.5%）"),
    "1326": ("2026-07-03", 64.7, "D3強制出場：反轉Level4爆量賣超-7,134張（佔日均量9.6%，T86 07/07），出場價64.7（+4.5%）未達目標，依L4無例外規則出場"),
    "1301": ("2026-07-03", 58.0, "D3強制出場：反轉Level4爆量賣超-5,662張（佔日均量12.7%，T86 07/07）+連續賣超3天+manual_exit_checker結論「賣」，收盤58（-2.8%）"),
}

for code, (day, close, reason) in SETTLE.items():
    fp = f"data/tracking/tracking_{day}.json"
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    hit = False
    for key in ("recommendations", "track_b_recommendations"):
        for r in d.get(key) or []:
            if r.get("stock_code") == code and r.get("result") == "holding":
                rec = float(r["recommend_price"])
                chg = round((close - rec) / rec * 100, 2)
                r["result"] = "fail"
                r["fail_reason"] = reason
                r["settled_date"] = "2026-07-08"
                r["settled_price"] = close
                r["actual_close"] = close
                r["close_price"] = close
                r["change_percent"] = chg
                r.pop("holding_status", None)
                hit = True
                print(f"✅ {code} {r.get('stock_name','')} @{fp} rec={rec} close={close} chg={chg}% -> fail")
    if not hit:
        print(f"❌ {code} 在 {fp} 找不到 holding 記錄")
        continue
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
