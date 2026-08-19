#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外資資金流向預測驗證器

[實驗性 — 不屬於盤前/盤中/盤後正式流程]

- 讀同目錄的 forecasts.json，逐條驗證到期的量化預測，把結果寫回 result 欄
- 唯讀存取 data/cache 的 T86 快取與 TWSE/Yahoo 公開 API，不寫入任何流程檔案
- 與 predictions.json（個股推薦追蹤）完全分離，不影響 settled_accuracy

用法：
    python3 experiments/flow_forecast/verify.py [--date YYYY-MM-DD] [--dry-run]
"""
import json
import sys
import os
import argparse
import urllib.request
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # repo root（僅用於讀 data/cache 的 T86）
FC = os.path.join(HERE, 'forecasts.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# 半導體/記憶體代碼（用於預測 #1 的族群判定）
SEMI = {'2330', '2303', '2408', '2344', '2337', '8299', '2451', '4967', '6770',
        '3711', '2454', '3034', '3443', '2379', '6415', '3661', '5269', '2481',
        '8110', '6239', '8150', '3105', '2401'}


def closes(code, rng='3mo'):
    """取日收盤序列 [(date, close)]，自動試 .TW / .TWO"""
    for suf in ('.TW', '.TWO'):
        try:
            url = ('https://query1.finance.yahoo.com/v8/finance/chart/'
                   '{}{}?range={}&interval=1d'.format(code, suf, rng))
            d = json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=30))
            r = d['chart']['result'][0]
            ts = r['timestamp']
            q = r['indicators']['quote'][0]['close']
            out = [(time.strftime('%Y-%m-%d', time.localtime(t)), c)
                   for t, c in zip(ts, q) if c is not None]
            if out:
                return out
        except Exception:
            continue
    return []


def foreign_net_yi(date_str):
    """TWSE 三大法人買賣金額：回傳外資淨額（億元），失敗回 None"""
    ymd = date_str.replace('-', '')
    url = ('https://www.twse.com.tw/rwd/zh/fund/BFI82U'
           '?dayDate={}&type=day&response=json'.format(ymd))
    try:
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(url, headers=UA), timeout=30))
        if d.get('stat') != 'OK':
            return None
        for row in d.get('data', []):
            if row[0].startswith('外資及陸資'):
                return int(row[3].replace(',', '')) / 1e8
    except Exception:
        pass
    return None


def t86_cache(date_str):
    p = os.path.join(ROOT, 'data', 'cache',
                     'twse_t86_{}.json'.format(date_str.replace('-', '')))
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def _stock_rows(t86):
    return [(c, r) for c, r in t86.items() if len(c) == 4 and c.isdigit()]


def check_1(q, today):
    """外資賣超 > 400 億，且賣超前三名至少 2 檔半導體/記憶體"""
    d = q['resolve_date']
    if today < d:
        return None, '未到期'
    net = foreign_net_yi(d)
    if net is None:
        return None, '{} 三大法人買賣金額尚未公布'.format(d)
    t86 = t86_cache(d)
    if not t86:
        return None, ('{} T86 快取不存在（先跑 fetch_institutional_top30.py {}）'
                      .format(d, d.replace('-', '')))
    rows = _stock_rows(t86)
    top_sell = sorted(rows, key=lambda x: x[1].get('foreign', 0))[:3]
    hits = [c for c, _ in top_sell if c in SEMI]
    ok = (net < -400) and (len(hits) >= 2)
    detail = ('外資淨額 {:+.1f} 億（門檻 <-400）；賣超前三 {}；其中半導體/記憶體 {} 檔（門檻 >=2）'
              .format(net,
                      '、'.join('{}{}({:+,.0f}張)'.format(c, r.get('name', ''),
                                                         r.get('foreign', 0))
                                for c, r in top_sell),
                      len(hits)))
    return ok, detail


def check_2(q, today):
    """外資買超前 10 名中航運至少 2 檔"""
    d = q['resolve_date']
    if today < d:
        return None, '未到期'
    t86 = t86_cache(d)
    if not t86:
        return None, '{} T86 快取不存在'.format(d)
    rows = _stock_rows(t86)
    top_buy = sorted(rows, key=lambda x: -x[1].get('foreign', 0))[:10]
    ship = set(q.get('shipping_codes', []))
    hits = [c for c, _ in top_buy if c in ship]
    ok = len(hits) >= 2
    detail = ('買超前10：{}；航運 {} 檔 {}（門檻 >=2）'
              .format('、'.join('{}{}'.format(c, r.get('name', ''))
                                for c, r in top_buy),
                      len(hits), hits))
    return ok, detail


def check_3(q, today):
    """長榮 vs 南亞科 5 交易日相對報酬 > 5pp"""
    if today < q['resolve_date']:
        return None, '未到期'
    base = q['baseline_date']
    res = {}
    for code in ('2603', '2408'):
        ser = closes(code)
        bd = [c for dt, c in ser if dt == base]
        after = [(dt, c) for dt, c in ser if dt > base]
        if not bd or len(after) < 5:
            return None, ('{} 價格序列不足（基準 {} 後僅 {} 日）'
                          .format(code, base, len(after)))
        res[code] = (bd[0], after[4][1], after[4][0])
    r1 = (res['2603'][1] - res['2603'][0]) / res['2603'][0] * 100
    r2 = (res['2408'][1] - res['2408'][0]) / res['2408'][0] * 100
    ok = (r1 - r2) > 5
    detail = ('2603 {}->{} ({:+.2f}%)｜2408 {}->{} ({:+.2f}%)｜差 {:+.2f}pp（門檻 >+5pp），結算日 {}'
              .format(res['2603'][0], res['2603'][1], r1,
                      res['2408'][0], res['2408'][1], r2,
                      r1 - r2, res['2603'][2]))
    return ok, detail


def check_4(q, today):
    """力積電 5 交易日內收盤未回 78.4"""
    ser = closes('6770')
    after = [(dt, c) for dt, c in ser if dt > '2026-08-19'][:5]
    thr = q['threshold']
    hit = [(dt, c) for dt, c in after if c >= thr]
    if hit:
        return False, '已於 {} 收 {} >= {}，預測失敗'.format(hit[0][0], hit[0][1], thr)
    hi = max((c for _, c in after), default=None)
    if today < q['resolve_date'] or len(after) < 5:
        return None, ('進行中（已過 {}/5 日，最高收盤 {}，門檻 {}）'
                      .format(len(after), hi if hi is not None else '-', thr))
    return True, '5 日最高收盤 {} < {}，預測成立'.format(hi, thr)


CHECKS = {1: check_1, 2: check_2, 3: check_3, 4: check_4}
MARK = {True: '[成立]', False: '[失敗]', None: '[未定]'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    with open(FC, encoding='utf-8') as f:
        doc = json.load(f)

    changed = False
    for fc in doc['forecasts']:
        print('=' * 68)
        print('預測批次 {}（產出於 {}）'.format(fc['id'], fc['made_at']))
        print('=' * 68)
        for q in fc['quantitative']:
            fn = CHECKS.get(q['no'])
            if not fn:
                continue
            try:
                ok, detail = fn(q, a.date)
            except Exception as e:
                ok, detail = None, '驗證錯誤：{}'.format(e)
            print('\n[{}] {}'.format(q['no'], q['claim']))
            print('    {} {}'.format(MARK[ok], detail))
            if ok is not None and q.get('result') != ok:
                q['result'] = ok
                q['verified_at'] = a.date
                q['verify_detail'] = detail
                changed = True
        done = [q for q in fc['quantitative'] if q.get('result') is not None]
        if done:
            hit = sum(1 for q in done if q['result'])
            print('\n量化預測結算：{}/{} 成立（命中率 {:.0f}%）'
                  .format(hit, len(done), hit / len(done) * 100))
        print('\n質性預測（需人工判定）：')
        for q in fc['qualitative']:
            print('  {} [{}] {}（信心 {}）'
                  .format(MARK[q.get('result')], q['no'], q['claim'],
                          q['confidence']))

    if changed and not a.dry_run:
        with open(FC, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        print('\n已寫回 flow_forecasts.json')
    elif changed:
        print('\n[dry-run] 未寫檔')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
