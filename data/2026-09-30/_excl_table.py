import re, json
T = '2026-09-30'
NAMES = {'3374': '精材', '3680': '家登', '5347': '世界', '3324': '雙鴻', '3234': '光環'}
SPECIAL = {
    '1303': '✅ **推薦 81 分**（🔥超強催化覆寫）',
    '2376': '✅ **推薦 78 分**（🔥超強催化覆寫）',
    '6505': '🟡 78 分通過全部門檻；與 1303 南亞同屬塑化，單一產業 ≤50% → 第一遞補',
    '1718': '🟡 75 分；當日時事提及 0 處 → ①催化對齊未過，列觀察',
    '2881': '❌ 57 分 <70（動能 +56.3% -10、營收連續衰退 6 個月 -5、EPS 快取 2025-12-31 未採計）',
    '4906': '❌ 64 分 <70（🔴光通訊與網通覆寫後：5 日 +8.6% -10、持股比 -0.16% -3）',
    '3374': '🚫 TPEx 處置股（09/29~10/05）機械式排除；T86 快取亦無資料（上櫃）',
    '2395': '⏳ 沿用中 D7/10；🟢邊緣AI 僅中度 → ①催化對齊未過，不重列排名',
    '5876': '⏳ 沿用中 D7/10；不在 TOP50 買超 × 月線乖離 +1.81% → 法人現身門檻未過，不重列排名',
    '2412': '⏳ 沿用中 D7/10；今日 L2（-174 張＝1.5%）→ ③未過，續抱觀察',
    '2886': '⚠️ 待複核（L4 7.4% <8% 且 10 日累計 +23K）',
    '3702': '⚠️ 待複核（L4 5.8% <8% 且 10 日累計 +12K）',
    '2892': '🛑 已決事項開盤出場（L4 13.2%）',
    '2609': '🛑 已決事項開盤出場（L4 24.9%）',
    '2454': '🛑 已決事項開盤出場（L4 57.0%）',
    '2484': '❌ 知識庫未分類、時事提及 0 處 → ①未過；5 日 +9.2%、處置預警（最快剩 2 天）',
    '2399': '❌ 知識庫未分類、時事提及 0 處 → ①未過（📶訊號A L2）',
    '6133': '❌ 知識庫未分類、時事提及 0 處 → ①未過；接近注意門檻',
}
MEMORY = {'6770', '2344', '2408', '2337', '3006', '2426'}
OVERRIDE_OK = {'1303', '2376', '6505', '4906'}
rows = []
for line in open(f'data/{T}/_table.txt', encoding='utf-8').read().splitlines()[1:]:
    p = line.split('|')
    if len(p) < 9:
        continue
    code, name = p[0].split(' ', 1)
    name = NAMES.get(code, name)
    lv = re.match(r'L(-?\d+)', p[1]).group(1)
    rk = p[2].split()
    avg_rank, tot, br, d5 = rk[0], rk[1], rk[2], rk[3]
    m = re.match(r'(\S+) (\S+)/(\S+) c(\S+) f5(\S+) m(\S+)', p[3])
    cum, bd, sd, consec, f5, mom = m.groups()
    ma20 = p[4].split()[0]
    in_top = avg_rank != '-'

    def num(s):
        if s in ('None', '-'):
            return None
        s = s.replace(',', '').replace('+', '').replace('%', '')
        if s.endswith('K'):
            return float(s[:-1]) * 1000
        return float(s)
    f5n, momn, d5n, ma = num(f5), num(mom), num(d5), num(ma20)
    sell_ratio = re.search(r'佔日均量([\d.]+)%', p[1])
    if code in SPECIAL:
        why = SPECIAL[code]
    elif cum == 'None':
        why = '❌ 數據不足（上櫃，T86 快取無資料）→ 無法評分'
    elif lv in ('3', '4'):
        why = f"🚫 反轉 L{lv}" + (f"（賣超佔比 {sell_ratio.group(1)}%）" if sell_ratio else '（連續賣超、累計轉負）')
    elif lv == '-1':
        why = '❌ 狀態不明（10 日累計為負）→ ③非 Level 0'
    elif lv in ('1', '2'):
        why = f'❌ 反轉 L{lv} → ③非 Level 0'
    elif d5n is not None and d5n > 10:
        why = f'❌ 5 日 +{d5n:.1f}% >10% 已大漲，不評分'
    elif f5n is not None and f5n < 0:
        why = f'❌ ②外資近 5 天 {f5} <0' + ('；MU 10/01 財報⏰不開新倉' if code in MEMORY else '')
    elif momn is not None and momn > 100 and code not in OVERRIDE_OK:
        why = f'❌ 動能 {mom} >100%，無 🔴 催化對應 → 不適用覆寫'
    elif not in_top and ma is not None and 0 <= ma <= 5:
        why = f'❌ 法人現身門檻未過（不在 TOP50 買超 × 月線乖離 +{ma}%）'
    else:
        why = '❌ ①催化對齊未過（知識庫未分類／時事無對應）'
    lvs = {'-1': '❓', '0': 'L0', '1': 'L1', '2': 'L2', '3': 'L3', '4': 'L4'}[lv]
    rows.append(f"| {code} {name} | {lvs} | {avg_rank} | {tot if in_top else '—'} | {d5 if in_top else '—'} | {cum} | {bd}/{sd} | {consec} | {f5} | {mom} | {ma20} | {why} |")
hdr = '| 股票 | 反轉 | avg_rank | 09-29 T86(張) | 5日% | 10日累計 | 買/賣天 | 真連買 | 近5天外資 | 動能 | vs MA20% | 結論 |\n|---|---|---|---|---|---|---|---|---|---|---|---|'
open(f'data/{T}/_excl_table.md', 'w', encoding='utf-8').write(hdr + '\n' + '\n'.join(rows) + '\n')
print(len(rows))
from collections import Counter
print(Counter(r.split('|')[-2].strip()[:12] for r in rows).most_common())
