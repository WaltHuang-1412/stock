#!/usr/bin/env python3
"""
法人買賣超 TOP50 查詢工具（v2.0 擴大掃描範圍）

功能：
- 查詢證交所法人買賣超數據
- 計算 5 日漲幅
- 標註狀態（佈局中/可進場/已小漲/追高風險/已大漲）
- 🆕 擴大為 TOP50，分三層級輸出

使用方式：
    python3 scripts/fetch_institutional_top30.py [日期YYYYMMDD]

範例：
    python3 scripts/fetch_institutional_top30.py           # 查詢最近交易日
    python3 scripts/fetch_institutional_top30.py 20251216  # 查詢指定日期

修改日期：2026-02-03（TOP30→TOP50 擴大掃描）
"""

import sys
import io

# Windows 環境 stdout 編碼修正（避免中文輸出時 cp950 報錯）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from datetime import datetime, timedelta
import warnings
import urllib3
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 股票名稱對照表
STOCK_NAMES = {
    # 半導體
    '2330': '台積電', '2303': '聯電', '2454': '聯發科', '3711': '日月光',
    '2408': '南亞科', '6770': '力積電', '2344': '華邦電', '2337': '旺宏',
    '3037': '欣興', '3189': '景碩', '8150': '南茂', '5469': '瀚宇博',

    # 電子
    '2317': '鴻海', '2382': '廣達', '3231': '緯創', '2324': '仁寶',
    '2353': '宏碁', '2356': '英業達', '2377': '微星', '2409': '友達',
    '3481': '群創', '2327': '國巨', '8039': '台虹', '6282': '康舒',
    '2312': '金寶', '2313': '華通', '2323': '中環', '2349': '錸德',
    '2402': '毅嘉', '2485': '兆赫',

    # 金融
    '2882': '國泰金', '2881': '富邦金', '2886': '兆豐金', '2891': '中信金',
    '2883': '凱基金', '2884': '玉山金', '2880': '華南金', '2885': '元大金',
    '2887': '台新金', '2890': '永豐金', '2892': '第一金', '2888': '新光金',
    '2801': '彰銀', '5880': '合庫金', '2867': '三商壽', '5876': '上海商銀',

    # 傳產
    '1303': '南亞', '1301': '台塑', '1326': '台化', '1314': '中石化',
    '1101': '台泥', '1102': '亞泥', '1216': '統一', '2105': '正新',
    '1605': '華新', '1802': '台玻', '1504': '東元',
    '2002': '中鋼', '2014': '中鴻', '2009': '第一銅', '2027': '大成鋼',

    # 航運
    '2618': '長榮航', '2610': '華航', '2615': '萬海', '2603': '長榮',
    '2609': '陽明', '2605': '新興', '2606': '裕民',

    # 其他
    '8110': '華東', '8422': '可寧衛', '6443': '元晶', '2371': '大同',
    '2515': '中工',
    '5521': '工信', '5522': '遠雄', '5871': '中租-KY', '9105': '泰金寶',
    '9904': '寶成', '4916': '事欣科', '4927': '泰鼎', '6191': '精成科',
    '6257': '矽格', '2329': '華泰', '2449': '京元電', '2481': '強茂',
    '2457': '飛宏', '2498': '宏達電',
}


def get_5day_change(code):
    """取得 5 日漲幅（使用 Yahoo Finance）"""
    try:
        import yfinance as yf
        stock = yf.Ticker(f'{code}.TW')
        hist = stock.history(period='5d')
        if len(hist) >= 2:
            first = hist['Close'].iloc[0]
            last = hist['Close'].iloc[-1]
            pct = (last - first) / first * 100
            return pct
    except:
        pass
    return None


def get_status(pct):
    """根據 5 日漲幅判斷狀態"""
    if pct is None:
        return '--'
    if pct < 0:
        return '[佈局中]'
    elif pct < 3:
        return '[可進場]'
    elif pct < 5:
        return '[已小漲]'
    elif pct < 8:
        return '[追高風險]'
    else:
        return '[已大漲]'


def fetch_institutional_top30(date=None):
    """查詢法人買賣超 TOP50（向下相容保留函數名）"""

    # 日期處理
    if not date:
        # 預設為昨天（或最近交易日）
        today = datetime.now()
        if today.weekday() == 0:  # 週一
            date = (today - timedelta(days=3)).strftime('%Y%m%d')
        elif today.weekday() == 6:  # 週日
            date = (today - timedelta(days=2)).strftime('%Y%m%d')
        else:
            date = (today - timedelta(days=1)).strftime('%Y%m%d')

    formatted_date = f'{date[:4]}/{date[4:6]}/{date[6:8]}'

    # 查詢證交所 API
    url = f'https://www.twse.com.tw/rwd/en/fund/T86?date={date}&selectType=ALL&response=json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept': 'application/json',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        data = response.json()

        if 'data' not in data or not data['data']:
            print(f'[錯誤] 查無 {formatted_date} 的法人數據')
            print('可能原因：非交易日或數據尚未公布')
            return None

        # 解析數據
        stocks = []
        for row in data['data']:
            try:
                code = row[0].strip()

                # 只取一般股票（4碼數字，排除 ETF）
                if not code.isdigit() or len(code) != 4 or code.startswith('0'):
                    continue

                foreign = int(row[3].replace(',', ''))   # 外資買賣超
                trust = int(row[9].replace(',', ''))     # 投信買賣超
                dealer = int(row[10].replace(',', ''))   # 自營商買賣超
                total = int(row[17].replace(',', ''))    # 三大法人合計

                name = STOCK_NAMES.get(code, code)

                stocks.append({
                    'code': code,
                    'name': name,
                    'foreign': foreign,
                    'trust': trust,
                    'dealer': dealer,
                    'total': total
                })
            except:
                continue

        # 買超 TOP50（v2.0 擴大掃描）
        stocks_buy = sorted(stocks, key=lambda x: x['total'], reverse=True)[:50]

        # 賣超 TOP50
        stocks_sell = sorted(stocks, key=lambda x: x['total'])[:50]

        return {
            'date': formatted_date,
            'buy_top30': stocks_buy,  # 保留key名稱向下相容
            'sell_top30': stocks_sell
        }

    except Exception as e:
        print(f'[錯誤] 查詢錯誤: {e}')
        return None


def format_value(v):
    """
    格式化數值
    證交所 API 回傳單位是「股」，1張=1000股
    顯示時轉換為「張」
    """
    v_lot = v // 1000  # 股 → 張
    if abs(v_lot) >= 10000:
        # 大於1萬張，顯示為 K（千張）
        v_k = v_lot // 1000
        return f'+{v_k:,}K' if v_lot >= 0 else f'{v_k:,}K'
    else:
        # 小於1萬張，直接顯示張數
        return f'+{v_lot:,}' if v_lot >= 0 else f'{v_lot:,}'


def print_top30_report(result, include_price=True):
    """輸出 TOP50 報告（v2.0 分三層級）"""

    if not result:
        return

    date = result['date']
    buy_top50 = result['buy_top30']  # 實際是TOP50，key名保留向下相容
    sell_top50 = result['sell_top30']

    # 買超 TOP50（分三層級）
    print(f'\n## 法人買超 TOP50（{date}）')
    print()

    # 第一層級：TOP20（優先推薦）
    print('### 📌 TOP 1-20（優先推薦）')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(buy_top50[:20], 1):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()

    # 第二層級：21-35（可考慮）
    print('### 🔍 TOP 21-35（可考慮）')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(buy_top50[20:35], 21):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()

    # 第三層級：36-50（觀察備用）
    print('### 👀 TOP 36-50（觀察備用）')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(buy_top50[35:50], 36):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()
    print('---')
    print()

    # 賣超 TOP50（分三層級）
    print(f'## 法人賣超 TOP50（{date}）')
    print()

    # 第一層級：TOP20（重點避開）
    print('### 🔴 TOP 1-20（重點避開）')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(sell_top50[:20], 1):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()

    # 第二層級：21-35（注意風險）
    print('### ⚠️ TOP 21-35（注意風險）')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(sell_top50[20:35], 21):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()

    # 第三層級：36-50（觀察參考）
    print('### 👁️ TOP 36-50（觀察參考）')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(sell_top50[35:50], 36):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()
    print('---')
    print()
    print('**狀態標註說明**：')
    print('- [佈局中]：5日漲幅 < 0%（法人買但還沒漲，最佳）')
    print('- [可進場]：5日漲幅 0-3%（小漲，可買）')
    print('- [已小漲]：5日漲幅 3-5%（注意追高）')
    print('- [追高風險]：5日漲幅 5-8%（考慮等回檔）')
    print('- [已大漲]：5日漲幅 > 8%（不建議追）')


def print_positioning_opportunities(result):
    """輸出佈局機會（買超 + 還沒漲）"""

    if not result:
        return

    buy_top30 = result['buy_top30']

    print('\n## 佈局機會（法人買超 + 還沒漲）')
    print()
    print('| 代號 | 名稱 | 三大法人 | 5日漲幅 | 狀態 |')
    print('|------|------|---------|--------|------|')

    count = 0
    for s in buy_top30:
        pct = get_5day_change(s['code'])
        if pct is not None and pct < 3:  # 5日漲幅 < 3%
            pct_str = f'{pct:+.1f}%'
            status = get_status(pct)
            print(f"| {s['code']} | {s['name']} | {format_value(s['total'])} | {pct_str} | {status} |")
            count += 1

    if count == 0:
        print('| -- | 無符合條件 | -- | -- | -- |')

    print()
    print(f'共 {count} 檔符合「佈局中」或「可進場」條件')


if __name__ == '__main__':
    # 解析命令列參數
    date = sys.argv[1] if len(sys.argv) > 1 else None

    print('=' * 60)
    print('法人買賣超 TOP30 查詢')
    print('=' * 60)

    # 查詢數據
    result = fetch_institutional_top30(date)

    if result:
        # 詢問是否要查詢股價（較慢）
        print('\n正在查詢 5 日漲幅（約需 20-40 秒）...\n')

        # 輸出完整報告
        print_top30_report(result, include_price=True)

        # 輸出佈局機會
        print_positioning_opportunities(result)
