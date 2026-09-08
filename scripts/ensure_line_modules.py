#!/usr/bin/env python3
"""LINE 盤前摘要「訊號A／訊號B」區塊自動補寫（機械式，不依賴模型抄寫）

背景：
    before_market_line.txt 長期漏寫 Module A/B 區塊 —— 回溯近 45 個交易日，
    缺 Module B 達 19 天、缺 Module A 達 6 天；2026-09-07／09-08 連兩個交易日
    validate_analysis.py 驗證失敗。該段內容 100% 來自
    catalyst_preposition_scan.json 與 catalyst_theme_signals.json，
    本來就不該靠人／模型每天手抄。

行為：
    - 已有區塊（關鍵字齊全）→ 不動檔案，exit 0
    - 缺區塊 → 從兩份 JSON 生成並插入，exit 0
    - --check → 只檢查不寫入，缺就 exit 1
    - JSON 缺檔 → exit 2（此時應該去修產生 JSON 的步驟，不是硬補一段假的）

用法：
    python3 scripts/ensure_line_modules.py --date 2026-09-08
    python3 scripts/ensure_line_modules.py --date 2026-09-08 --check
"""

import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

MAX_LINE_CHARS = 5000

# 與 validate_analysis.py:302-313 的檢查關鍵字一致
KEYS_A = ('Module A', '訊號A', '催化預埋')
KEYS_B = ('Module B', '訊號B', '催化主題')

# 插入位置：命中第一個就插在它前面；都沒有就附加在檔尾
ANCHORS = ('🚫 分數夠卻被擋下', '🚫 主要落榜', '🚫 落榜', '🚨 處置股',
           '⚠️ 處置股', '📌 資料品質', '📅 本週事件')

SEP = '━' * 14


def _fmt(stocks, limit=None):
    """[{code,name}] → '2886 兆豐金、1301 台塑'"""
    items = ['%s %s' % (s.get('code', '?'), s.get('name', '')) for s in stocks]
    if limit is not None and len(items) > limit:
        return '、'.join(items[:limit]) + ' 等 %d 檔' % len(items)
    return '、'.join(items) if items else '無'


def build_block(date, data_dir, compact=False):
    pa = os.path.join(data_dir, 'catalyst_preposition_scan.json')
    pb = os.path.join(data_dir, 'catalyst_theme_signals.json')
    for p in (pa, pb):
        if not os.path.exists(p):
            print('[ERROR] 缺少 %s → 無法生成訊號A/B 區塊。'
                  '請先確認 Step 5.5／5.7 是否執行成功' % p)
            return None

    with open(pa, encoding='utf-8') as f:
        a = json.load(f)
    with open(pb, encoding='utf-8') as f:
        b = json.load(f)

    l3 = a.get('l3_stocks', []) or []
    l2 = a.get('l2_stocks', []) or []
    l1 = a.get('l1_stocks', []) or []
    lim = 6 if compact else None

    lines = [SEP, '📶 訊號A（催化預埋，Module A）']
    if l3:
        lines.append('🔥L3 佈局完成 %d 檔：%s → +15 分，強制進入評分'
                     % (len(l3), _fmt(l3, lim)))
    else:
        lines.append('🔥L3 佈局完成 0 檔 → 無強制進入評分者')
    lines.append('🟢L2 早期佈局 %d 檔：%s%s'
                 % (len(l2), _fmt(l2, lim), ' → +10 分' if l2 else ''))
    lines.append('🟡L1 態度轉變 %d 檔：%s%s'
                 % (len(l1), _fmt(l1, lim), ' → 不加分' if l1 else ''))
    lines.append('（掃描 %s 檔／過濾後 %s 檔）'
                 % (a.get('total_scanned', '?'), a.get('total_filtered', '?')))

    cand = b.get('preposition_candidates', []) or []
    intop = b.get('already_in_top50', []) or []
    moved = b.get('already_moved_count', 0)
    mat = {'early': '🟢早期', 'mid': '🟡中期', 'mature': '🔴成熟'}

    lines += ['', '📶 訊號B（催化主題預警，Module B）',
              '預先佈局 %d 檔／法人已進場 %d 檔／已大漲排除 %d 檔'
              % (len(cand), len(intop), moved)]
    if cand:
        top = cand[:6 if compact else 10]
        for s in top:
            lines.append('・%s %s｜%s｜對應 %s｜%s%s'
                         % (s.get('code', '?'), s.get('name', ''),
                            s.get('tw_industry', '未分類'),
                            s.get('us_leader', '-'),
                            mat.get(s.get('maturity'), s.get('maturity', '-')),
                            '｜已在TOP50' if s.get('in_top50') else ''))
        if len(cand) > len(top):
            lines.append('・…另 %d 檔見報告' % (len(cand) - len(top)))
        lines.append('➡️ 是否進入最終推薦以 Step 7 評分為準（🟡中期僅標註不加分）')
    else:
        lines.append('➡️ 本日 0 檔候選，無一檔以訊號B 進入推薦')
    lines.append('')
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--check', action='store_true', help='只檢查不寫入')
    args = ap.parse_args()

    data_dir = os.path.join('data', args.date)
    line_file = os.path.join(data_dir, 'before_market_line.txt')
    if not os.path.exists(line_file):
        print('[ERROR] 找不到 %s' % line_file)
        return 2

    with open(line_file, encoding='utf-8') as f:
        content = f.read()

    has_a = any(k in content for k in KEYS_A)
    has_b = any(k in content for k in KEYS_B)
    if has_a and has_b:
        print('[OK] LINE 摘要已含訊號A／訊號B，不需補寫')
        return 0

    missing = ('訊號A ' if not has_a else '') + ('訊號B' if not has_b else '')
    print('[MISSING] LINE 摘要缺少：%s' % missing.strip())
    if args.check:
        return 1

    block = build_block(args.date, data_dir)
    if block is None:
        return 2

    # 超過字元上限先改用精簡版；仍超過就不寫，交給人處理（禁止截斷成半截摘要）
    if len(content) + len(block) > MAX_LINE_CHARS:
        block = build_block(args.date, data_dir, compact=True)
        if len(content) + len(block) > MAX_LINE_CHARS:
            print('[ERROR] 補寫後將超過 %d 字元上限（現有 %d + 區塊 %d），'
                  '請先精簡 LINE 摘要其他段落'
                  % (MAX_LINE_CHARS, len(content), len(block)))
            return 2

    pos = -1
    for anchor in ANCHORS:
        i = content.find(anchor)
        if i >= 0:
            # 連同該段上方的分隔線一起讓開
            sep_i = content.rfind(SEP, 0, i)
            pos = sep_i if sep_i >= 0 and i - sep_i < 40 else i
            break

    if pos >= 0:
        content = content[:pos] + block + content[pos:]
    else:
        content = content.rstrip('\n') + '\n\n' + block

    with open(line_file, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print('[FIXED] 已補寫訊號A／訊號B 區塊，檔案現為 %d 字元' % len(content))
    return 0


if __name__ == '__main__':
    sys.exit(main())
