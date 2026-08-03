#!/usr/bin/env python3
"""
逐檔資訊卷宗（Stock Dossier）v1.0

目的：盤前推薦名單定案前的「最後一哩資訊閘門」。
以股票代碼為索引，機械式彙整兩類資訊，杜絕「資料在手上卻沒寫進報告」：

1. 結構化事件日曆（線上抓取，獨立快取）
   - 法說會：MOPS ajax_t100sb02_1（上市 sii + 上櫃 otc，整年度）
   - 除權息預告：TWSE OpenAPI TWT48U_ALL
   - 當日重大訊息：TWSE t187ap04_L + TPEx mopsfin_t187ap04_O
2. 當日資料源全文掃描（本地檔案）
   - 掃 data/YYYY-MM-DD/ 下的 topic_tracker.md、market_intelligence.md、
     industry_signals.json、tw_market_news.json、us_leader_alerts.md 等，
     抽出所有提及該股票代碼或名稱的行

任何來源抓取失敗都會在輸出中顯性標註（source_status），禁止靜默略過。

使用方法：
    python3 scripts/stock_dossier.py 3231 2882 2324 --date 2026-08-03
    python3 scripts/stock_dossier.py 3231 --date 2026-08-03 --days 5

輸出：
    data/YYYY-MM-DD/stock_dossier.json
    stdout：人類可讀摘要（⚠️ 近日事件優先顯示）
"""

import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import datetime
import json
import os
import re
import time

import requests

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, 'data', 'cache')

# 本地全文掃描的目標檔案（存在才掃）
LOCAL_SCAN_FILES = [
    'topic_tracker.md',
    'market_intelligence.md',
    'industry_signals.json',
    'tw_market_news.json',
    'us_leader_alerts.md',
    'cumulative_summary.json',
]


def _load_cache(name: str, max_age_hours: float):
    path = os.path.join(CACHE_DIR, name)
    try:
        if os.path.exists(path):
            age = time.time() - os.path.getmtime(path)
            if age < max_age_hours * 3600:
                with open(path, encoding='utf-8') as f:
                    return json.load(f)
    except Exception:
        pass
    return None


def _save_cache(name: str, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def roc_to_date(s: str):
    """民國日期字串轉 date。接受 115/08/04、1150804 兩種格式。"""
    s = s.strip()
    m = re.match(r'^(\d{2,3})/(\d{1,2})/(\d{1,2})$', s)
    if not m:
        m = re.match(r'^(\d{3})(\d{2})(\d{2})$', s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)) + 1911, int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


# ─────────────────────────── 結構化事件源 ───────────────────────────

def fetch_conference_calendar():
    """MOPS 法說會整年度列表（上市+上櫃），快取 12 小時。

    回傳 (records, status)。records: [{code,name,date_start,date_end,time,location,desc,market}]
    """
    cached = _load_cache('conference_calendar.json', 12)
    if cached is not None:
        return cached, 'ok(cache)'

    year_roc = str(datetime.date.today().year - 1911)
    records = []
    errors = []
    for typek, market in [('sii', '上市'), ('otc', '上櫃')]:
        try:
            r = requests.post(
                'https://mopsov.twse.com.tw/mops/web/ajax_t100sb02_1',
                data={'encodeURIComponent': '1', 'step': '1', 'firstin': '1',
                      'off': '1', 'TYPEK': typek, 'year': year_roc},
                headers=HEADERS, timeout=60)
            r.encoding = 'utf-8'
            for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', r.text, re.S):
                tds = [re.sub(r'<[^>]+>', '', td).strip()
                       for td in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
                # 預期欄位：代號 | 名稱 | 日期(可能為區間) | 時間 | 地點 | 說明
                if len(tds) < 3 or not re.match(r'^\d{4,6}$', tds[0]):
                    continue
                date_part = tds[2]
                dates = re.findall(r'\d{2,3}/\d{1,2}/\d{1,2}', date_part)
                if not dates:
                    continue
                d_start = roc_to_date(dates[0])
                d_end = roc_to_date(dates[-1])
                if not d_start:
                    continue
                records.append({
                    'code': tds[0], 'name': tds[1],
                    'date_start': d_start.isoformat(),
                    'date_end': (d_end or d_start).isoformat(),
                    'time': tds[3] if len(tds) > 3 else '',
                    'location': tds[4] if len(tds) > 4 else '',
                    'desc': tds[5] if len(tds) > 5 else '',
                    'market': market,
                })
        except Exception as e:
            errors.append(f'{market}: {e}')

    if records:
        _save_cache('conference_calendar.json', records)
        status = 'ok' if not errors else f'partial({";".join(errors)})'
        return records, status
    return [], f'error({";".join(errors) or "no rows parsed"})'


def fetch_ex_dividend():
    """TWSE 除權息預告（TWT48U_ALL），快取 12 小時。"""
    cached = _load_cache('ex_dividend.json', 12)
    if cached is not None:
        return cached, 'ok(cache)'
    try:
        r = requests.get('https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL',
                         headers=HEADERS, timeout=30)
        rows = r.json()
        records = []
        for row in rows:
            d = roc_to_date(str(row.get('Date', '')))
            if not d:
                continue
            records.append({
                'code': str(row.get('Code', '')).strip(),
                'name': row.get('Name', ''),
                'date': d.isoformat(),
                'cash_dividend': row.get('CashDividend', ''),
                'stock_ratio': row.get('StockDividendRatio', ''),
            })
        _save_cache('ex_dividend.json', records)
        return records, 'ok'
    except Exception as e:
        return [], f'error({e})'


def fetch_material_news():
    """當日重大訊息（上市 t187ap04_L + 上櫃 mopsfin_t187ap04_O），不快取（當日即時）。"""
    records = []
    errors = []
    sources = [
        ('https://openapi.twse.com.tw/v1/opendata/t187ap04_L', '上市'),
        ('https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap04_O', '上櫃'),
    ]
    for url, market in sources:
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            rows = r.json()
            for row in rows:
                # 欄位名可能是「公司代號」；容錯取第一個含「代號」的欄位
                code = ''
                subject = ''
                for k, v in row.items():
                    if '代號' in k:
                        code = str(v).strip()
                    if '主旨' in k or '主 旨' in k:
                        subject = str(v).strip()
                if code:
                    records.append({'code': code, 'market': market, 'subject': subject})
        except Exception as e:
            errors.append(f'{market}: {e}')
    status = 'ok' if not errors else ('partial(' + ';'.join(errors) + ')' if records else 'error(' + ';'.join(errors) + ')')
    return records, status


def load_stock_names():
    """代碼→名稱對照（上市 t187ap03_L + 上櫃 mopsfin_t187ap03_O），快取 7 天。"""
    cached = _load_cache('stock_names.json', 7 * 24)
    if cached:
        return cached
    mapping = {}
    for url in ['https://openapi.twse.com.tw/v1/opendata/t187ap03_L',
                'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O']:
        try:
            rows = requests.get(url, headers=HEADERS, timeout=30).json()
            for row in rows:
                code, name = '', ''
                for k, v in row.items():
                    if '代號' in k:
                        code = str(v).strip()
                    elif '簡稱' in k and '英文' not in k:
                        name = str(v).strip()
                # 英文簡稱會讓中文全文掃描漏抓，寧缺勿錯
                if code and name and not re.match(r'^[A-Za-z0-9 .,&()-]+$', name):
                    mapping[code] = name
        except Exception:
            continue
    if mapping:
        _save_cache('stock_names.json', mapping)
    return mapping


# ─────────────────────────── 本地全文掃描 ───────────────────────────

def scan_local_mentions(date_dir: str, code: str, name: str):
    """掃當日資料目錄，回傳所有提及 code 或 name 的行（含來源檔）。"""
    mentions = []
    pattern = re.compile(re.escape(code) + (('|' + re.escape(name)) if name else ''))
    for fname in LOCAL_SCAN_FILES:
        path = os.path.join(date_dir, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                for lineno, line in enumerate(f, 1):
                    if pattern.search(line):
                        text = line.strip()
                        if len(text) > 300:
                            # JSON 長行只保留命中處前後文
                            m = pattern.search(text)
                            s = max(0, m.start() - 120)
                            text = ('…' if s else '') + text[s:m.end() + 180] + '…'
                        mentions.append({'file': fname, 'line': lineno, 'text': text})
        except Exception as e:
            mentions.append({'file': fname, 'line': 0, 'text': f'(讀取失敗: {e})'})
    return mentions


# ─────────────────────────── 主流程 ───────────────────────────

def build_dossier(codes, ref_date: datetime.date, window_days: int, date_dir: str):
    conferences, conf_status = fetch_conference_calendar()
    ex_div, exdiv_status = fetch_ex_dividend()
    news, news_status = fetch_material_news()
    names = load_stock_names()

    window_end = ref_date + datetime.timedelta(days=window_days)
    result = {
        'date': ref_date.isoformat(),
        'window_days': window_days,
        'source_status': {
            '法說會(MOPS)': conf_status,
            '除權息(TWSE)': exdiv_status,
            '重大訊息(TWSE+TPEx)': news_status,
        },
        'stocks': {},
    }

    for code in codes:
        name = names.get(code, '')
        events = []

        for c in (x for x in conferences if x['code'] == code):
            d_start = datetime.date.fromisoformat(c['date_start'])
            d_end = datetime.date.fromisoformat(c['date_end'])
            if d_end >= ref_date and d_start <= window_end:
                days_until = (d_start - ref_date).days
                events.append({
                    'type': '法說會',
                    'date': c['date_start'],
                    'days_until': days_until,
                    'detail': f"{c['time']} {c['location']} {c['desc']}".strip(),
                })

        for x in (x for x in ex_div if x['code'] == code):
            d = datetime.date.fromisoformat(x['date'])
            if ref_date <= d <= window_end:
                events.append({
                    'type': '除權息',
                    'date': x['date'],
                    'days_until': (d - ref_date).days,
                    'detail': f"現金股利 {x['cash_dividend']}｜配股率 {x['stock_ratio']}",
                })

        for x in (x for x in news if x['code'] == code):
            events.append({
                'type': '重大訊息(今日)',
                'date': ref_date.isoformat(),
                'days_until': 0,
                'detail': x['subject'],
            })

        events.sort(key=lambda e: e['days_until'])
        mentions = scan_local_mentions(date_dir, code, name)
        result['stocks'][code] = {
            'name': name,
            'events': events,
            'mentions': mentions,
        }

    return result


def print_summary(result):
    print('=' * 70)
    print(f"📋 逐檔資訊卷宗 {result['date']}（事件窗口 {result['window_days']} 天）")
    for src, st in result['source_status'].items():
        mark = '✅' if st.startswith('ok') else '🔴'
        print(f'  {mark} {src}: {st}')
    print('=' * 70)

    for code, info in result['stocks'].items():
        name = info['name'] or '?'
        print(f"\n### {code} {name}")
        if info['events']:
            for e in info['events']:
                flag = '⚠️' if e['days_until'] <= 3 else 'ℹ️'
                print(f"  {flag} [{e['type']}] {e['date']}（{e['days_until']}天後）{e['detail'][:80]}")
        else:
            print('  （事件窗口內無法說會/除權息/重大訊息）')
        if info['mentions']:
            print(f"  📎 當日資料源提及 {len(info['mentions'])} 處：")
            for m in info['mentions'][:15]:
                print(f"    - {m['file']}:{m['line']} {m['text'][:120]}")
            if len(info['mentions']) > 15:
                print(f"    …另 {len(info['mentions']) - 15} 處，詳見 stock_dossier.json")
        else:
            print('  📎 當日資料源無提及（注意：推薦理由是否有本地數據支撐？）')


def main():
    parser = argparse.ArgumentParser(description='逐檔資訊卷宗：事件日曆 + 當日資料源全文掃描')
    parser.add_argument('codes', nargs='+', help='股票代碼')
    parser.add_argument('--date', default=datetime.date.today().isoformat())
    parser.add_argument('--days', type=int, default=5, help='事件窗口天數（預設5）')
    parser.add_argument('--output-dir', default=None)
    parser.add_argument('--suffix', default='',
                        help='輸出檔名後綴，如 intraday → stock_dossier_intraday.json（避免覆蓋盤前卷宗）')
    args = parser.parse_args()

    ref_date = datetime.date.fromisoformat(args.date)
    date_dir = args.output_dir or os.path.join(BASE_DIR, 'data', args.date)

    result = build_dossier(args.codes, ref_date, args.days, date_dir)

    os.makedirs(date_dir, exist_ok=True)
    fname = f'stock_dossier_{args.suffix}.json' if args.suffix else 'stock_dossier.json'
    out_path = os.path.join(date_dir, fname)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print_summary(result)
    print(f'\n✅ 已保存：{out_path}')

    # 任一來源全掛 → 非零退出，讓流程顯性看到
    if any(st.startswith('error') for st in result['source_status'].values()):
        print('🔴 有事件來源抓取失敗，上表已標註 — 分析時必須說明該資訊缺口', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
