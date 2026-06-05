#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manual_exit_checker.py
手動賣出確認工具 - 論點驅動框架

用法: python3 scripts/manual_exit_checker.py [股票代碼]
     python3 scripts/manual_exit_checker.py 2337
"""

import sys
import io
import json
import re
import subprocess
from pathlib import Path
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ─── 論點類型關鍵字 ───────────────────────────────────────────────────────────
THESIS_B_KEYWORDS = ['module a', 'module b', 'l2', 'l3', '連買', '預埋', '佈局型', '訊號a', '訊號b']
THESIS_C_STOCKS   = ['2330']  # 趨勢型長持

# 催化劑 → 對應 market_context 欄位（A 型用）
CATALYST_MAP = {
    'ai伺服器': ['nvda_change_pct', 'avgo_change_pct'],
    'ai散熱':   ['nvda_change_pct'],
    'pcb':      ['nvda_change_pct', 'avgo_change_pct'],
    'abf':      ['nvda_change_pct', 'avgo_change_pct'],
    'dram':     ['mu_change_pct'],
    '記憶體':   ['mu_change_pct'],
    '光通訊':   ['avgo_change_pct'],
    '網通':     ['avgo_change_pct'],
    '半導體':   ['sox_change_pct'],
    '封測':     ['nvda_change_pct'],
    '電源':     ['nvda_change_pct', 'avgo_change_pct'],
    'computex': ['nvda_change_pct'],
}


# ─── 資料讀取 ─────────────────────────────────────────────────────────────────
def find_holding(stock_code):
    try:
        import yaml
        with open('portfolio/my_holdings.yaml', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        for h in data.get('holdings', []):
            if h.get('symbol') == stock_code and h.get('quantity', 0) > 0:
                return h
    except Exception:
        pass
    return None


def find_tracking(stock_code):
    tracking_dir = Path('data/tracking')
    files = sorted(tracking_dir.glob('tracking_*.json'), reverse=True)
    for f in files[:14]:
        try:
            with open(f, encoding='utf-8') as fp:
                data = json.load(fp)
            for rec in data.get('recommendations', []) + data.get('track_b_recommendations', []):
                if rec.get('stock_code') == stock_code:
                    return rec, data, f.stem.replace('tracking_', '')
        except Exception:
            continue
    return None, None, None


def get_today_tracking():
    today = date.today().strftime('%Y-%m-%d')
    f = Path(f'data/tracking/tracking_{today}.json')
    if f.exists():
        with open(f, encoding='utf-8') as fp:
            return json.load(fp)
    return None


# ─── 論點類型推斷 ──────────────────────────────────────────────────────────────
def infer_thesis_type(stock_code, rec, holding=None):
    if stock_code in THESIS_C_STOCKS:
        return 'C'
    # 先用推薦記錄
    combined = ''
    if rec:
        combined = (rec.get('reason', '') + ' ' + ' '.join(rec.get('catalysts', []))).lower()
    # 再用持倉 notes 補充
    if holding:
        combined += ' ' + holding.get('notes', '').lower()
    if not combined:
        return 'A'
    if any(kw in combined for kw in THESIS_B_KEYWORDS):
        return 'B'
    return 'A'


def get_relevant_us_pcts(rec, market_ctx, holding=None):
    """找出與該股最相關的美股漲跌幅"""
    if not market_ctx:
        return []
    combined = ''
    if rec:
        combined = (rec.get('reason', '') + ' ' + ' '.join(rec.get('catalysts', []))).lower()
    if holding:
        combined += ' ' + holding.get('notes', '').lower()

    keys_to_check = set()
    for keyword, keys in CATALYST_MAP.items():
        if keyword in combined:
            keys_to_check.update(keys)
    if not keys_to_check:
        keys_to_check = {'nvda_change_pct', 'sox_change_pct'}

    results = []
    for k in keys_to_check:
        # 盤後數據優先（如 avgo_afterhours）
        afterhours_key = k.replace('_change_pct', '_afterhours_change_pct')
        val = market_ctx.get(afterhours_key, market_ctx.get(k))
        if isinstance(val, (int, float)):
            label = k.replace('_change_pct', '').upper()
            if afterhours_key in market_ctx:
                label += '(盤後)'
            results.append((label, val))
    return results


# ─── 籌碼解析 ─────────────────────────────────────────────────────────────────
def run_chip_analysis(stock_code):
    r = subprocess.run(
        ['python3', 'scripts/chip_analysis.py', stock_code, '--days', '10'],
        capture_output=True, encoding='utf-8', errors='replace'
    )
    return r.stdout


def run_reversal_alert(stock_code):
    r = subprocess.run(
        ['python3', 'scripts/reversal_alert.py', stock_code],
        capture_output=True, encoding='utf-8', errors='replace'
    )
    return r.stdout


def parse_reversal_level(output):
    m = re.search(r'Level\s+(\d)', output)
    return int(m.group(1)) if m else 0


def parse_consecutive_sell(output):
    """從籌碼輸出算最近連續賣超天數（從最新一天往回）"""
    sell_days = 0
    for line in output.split('\n'):
        if '🔴 賣' in line or '\U0001f534' in line:
            sell_days += 1
        elif '🟢 買' in line or '\U0001f7e2' in line:
            break
    return sell_days


def parse_consecutive_buy(output):
    m = re.search(r'真連續買超:\s*(\d+)\s*天', output)
    return int(m.group(1)) if m else 0


# ─── 框架判斷 ─────────────────────────────────────────────────────────────────
def apply_framework(thesis_type, reversal_level, consec_sell, consec_buy,
                    us_pcts, holding, rec):
    buy_price   = holding.get('buy_price', 0)
    stop_loss   = holding.get('stop_loss', buy_price * 0.9)

    # ── 先問停損 ──
    # （現價需由使用者確認，這裡只提示）

    # ── C 趨勢型 ──
    if thesis_type == 'C':
        return '不賣', '趨勢型持股，短線訊號不影響長線論點。除非產業出現結構性改變。'

    # ── B 法人佈局型 ──
    if thesis_type == 'B':
        if consec_sell >= 2:
            return '賣', f'法人連續賣超 {consec_sell} 天，佈局論點已消失。'
        if reversal_level >= 4:
            # 再看有沒有對應利空
            big_drop = [f'{name} {pct:+.1f}%' for name, pct in us_pcts if pct <= -5]
            if big_drop:
                return '賣', f'Level 4 + 美股利空（{", ".join(big_drop)}），論點消失。'
            return '觀察1天', 'Level 4 單日，無明確利空，可能是洗盤。明天若法人恢復買超則續抱；若再賣則出場。'
        if reversal_level == 3:
            return '縮倉一半', 'Level 3，論點受損，建議先縮一半倉位觀察。'
        return '不賣', f'法人佈局論點仍在（真連續買超 {consec_buy} 天），無持續賣壓。'

    # ── A 催化劑型 ──
    if thesis_type == 'A':
        if not us_pcts:
            # 沒有美股數據，退而靠籌碼
            if consec_sell >= 2 or reversal_level >= 4:
                return '賣', '催化劑型：無美股數據，但籌碼持續惡化，建議出場。'
            return '觀察', '催化劑型：無法確認美股走勢，請手動查對應龍頭。'

        worst_name, worst_pct = min(us_pcts, key=lambda x: x[1])
        us_summary = ', '.join(f'{n} {p:+.1f}%' for n, p in us_pcts)

        if worst_pct <= -10:
            return '賣', f'催化劑型：對應美股 {worst_name} 跌 {worst_pct:.1f}%，論點消失。（{us_summary}）'
        if worst_pct <= -5:
            return '縮倉一半', f'催化劑型：對應美股 {worst_name} 跌 {worst_pct:.1f}%，論點受損，縮倉觀察。（{us_summary}）'
        if worst_pct <= -3 and reversal_level >= 4:
            return '賣', f'催化劑型：Level 4 + 美股 {worst_name} {worst_pct:.1f}%，論點消失。'
        return '不賣', f'催化劑型：美股龍頭無重大下跌，論點仍在。（{us_summary}）'

    return '觀察', '無法判斷論點類型，請手動確認。'


# ─── 主程式 ───────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print('用法: python3 scripts/manual_exit_checker.py [股票代碼]')
        sys.exit(1)

    stock_code = sys.argv[1]
    SEP = '=' * 55

    print(SEP)
    print(f'  手動賣出確認：{stock_code}')
    print(SEP)

    # 持倉
    holding = find_holding(stock_code)
    if not holding:
        print(f'[X] {stock_code} 不在目前持倉（quantity > 0）')
        sys.exit(1)

    buy_price = holding.get('buy_price', 0)
    stop_loss = holding.get('stop_loss', buy_price * 0.9)
    print(f'\n[持倉]  買入 {buy_price}  停損 {stop_loss}')

    # 推薦記錄
    rec, tracking_data, rec_date = find_tracking(stock_code)
    if rec:
        print(f'   推薦日  {rec_date}')
        print(f'   理由    {rec.get("reason", "無記錄")}')

    # 今日市場 context
    today_data   = get_today_tracking()
    market_ctx   = today_data.get('market_context', {}) if today_data else {}

    # 論點類型
    thesis_type  = infer_thesis_type(stock_code, rec, holding)
    type_label   = {'A': 'A 催化劑型', 'B': 'B 法人佈局型', 'C': 'C 趨勢型'}
    print(f'\n[論點]  {type_label.get(thesis_type, "未知")}')

    # 美股對應數據
    us_pcts = get_relevant_us_pcts(rec, market_ctx, holding)
    if us_pcts:
        print(f'   對應美股：' + ', '.join(f'{n} {p:+.1f}%' for n, p in us_pcts))

    # 籌碼
    print('\n[查詢中] 籌碼...')
    chip_out     = run_chip_analysis(stock_code)
    reversal_out = run_reversal_alert(stock_code)

    reversal_level = parse_reversal_level(reversal_out)
    consec_sell    = parse_consecutive_sell(chip_out)
    consec_buy     = parse_consecutive_buy(chip_out)

    print(f'   反轉預警  Level {reversal_level}')
    print(f'   連續賣超  {consec_sell} 天')
    print(f'   真連續買超 {consec_buy} 天')

    # 框架判斷
    verdict, reason = apply_framework(
        thesis_type, reversal_level, consec_sell, consec_buy,
        us_pcts, holding, rec
    )


    tag = {'賣': '[賣]', '縮倉一半': '[縮倉]', '觀察1天': '[觀察]', '觀察': '[觀察]', '不賣': '[不賣]'}.get(verdict, '[?]')

    print(f'\n{SEP}')
    print(f'  {tag}  結論：{verdict}')
    print(f'  {reason}')
    print(SEP)

    # 停損提示
    print(f'\n  [!] 停損提醒：若現價 <= {stop_loss}，無論結論一律出場')


if __name__ == '__main__':
    main()
