# 2026-07-08 盤後：將 13 筆跨 tracking 檔的強制出場結算同步進 predictions.json
# （update_predictions.py 只讀當日 tracking 檔，跨檔結算需依 date_key+symbol 精準比對）
# 結算結果與 fail_reason 皆直接讀自各 tracking 檔，不另行編造
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SETTLED = [  # (date_key, symbol, rec_price, settled_price, holding_days)
    ("2026-06-25", "3045", 119.5, 113.0, 9),
    ("2026-06-29", "2618", 43.8, 39.85, 7),
    ("2026-06-29", "2472", 376.0, 351.0, 7),
    ("2026-06-30", "2409", 30.6, 29.55, 6),
    ("2026-07-01", "2449", 337.5, 305.5, 5),
    ("2026-07-01", "3711", 680.0, 625.0, 5),
    ("2026-07-01", "2618", 44.9, 39.85, 5),
    ("2026-07-01", "6285", 259.5, 251.5, 5),
    ("2026-07-01", "1301", 54.5, 58.0, 5),
    ("2026-07-02", "2303", 169.0, 163.0, 4),
    ("2026-07-03", "1301", 59.7, 58.0, 3),
    ("2026-07-03", "1326", 61.9, 64.7, 3),
    ("2026-07-07", "2301", 224.0, 214.0, 1),
]

# 讀各 tracking 檔的 fail_reason
reasons = {}
for dk, sym, rp, sp, hd in SETTLED:
    with open(f"data/tracking/tracking_{dk}.json", encoding="utf-8") as f:
        t = json.load(f)
    for key in ("recommendations", "track_b_recommendations"):
        for r in t.get(key) or []:
            if r.get("stock_code") == sym and abs(float(r.get("recommend_price") or 0) - rp) < 0.01:
                reasons[(dk, sym, rp)] = (r.get("result"), r.get("fail_reason"))

fp = "data/predictions/predictions.json"
with open(fp, encoding="utf-8") as f:
    P = json.load(f)

n = 0
for dk, sym, rp, sp, hd in SETTLED:
    day = P.get(dk)
    if not isinstance(day, dict) or "predictions" not in day:
        print(f"❌ predictions 無 {dk} key")
        continue
    found = False
    for pred in day["predictions"]:
        if pred.get("symbol") == sym and pred.get("result") == "holding" \
           and abs(float(pred.get("recommend_price") or 0) - rp) < 0.01:
            result, reason = reasons.get((dk, sym, rp), ("fail", None))
            pred["result"] = result
            pred["settled_date"] = "2026-07-08"
            pred["settled_price"] = sp
            pred["holding_days"] = hd
            if reason:
                pred["fail_reason"] = reason
            found = True
            n += 1
            print(f"✅ {dk} {sym} rec={rp} -> {result} @ {sp}")
            break
    if not found:
        print(f"⚠️ {dk} {sym} rec={rp} 找不到 holding 項目（可能已結算或價格不符）")

# 重算頂層統計（複製 update_predictions.py 的 recalculate_stats 邏輯）
ts = tf = th = 0
for key, value in P.items():
    if not isinstance(value, dict) or "predictions" not in value:
        continue
    for pred in value["predictions"]:
        r = pred.get("result")
        if r == "success": ts += 1
        elif r == "fail": tf += 1
        elif r == "holding": th += 1
sc = ts + tf
acc = round(ts / sc * 100, 1) if sc else 0
P["settled_accuracy"] = f"{acc}%"
P["settled_count"] = sc
P["total_success"] = ts
P["total_fail"] = tf
P["holding_count"] = th

with open(fp, "w", encoding="utf-8") as f:
    json.dump(P, f, ensure_ascii=False, indent=2)
print(f"\n共更新 {n} 筆 | 準確率 {acc}% ({ts}s/{tf}f/{sc}t) | holding {th}")
