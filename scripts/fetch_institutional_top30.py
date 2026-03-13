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


def get_stock_market_data(code):
    """
    一次查詢取得股價、成交量、5日漲幅（Yahoo Finance range=6d）

    Returns:
        dict: {
            'close_price': float,    # 收盤價（元）
            'daily_volume': int,     # 當日成交量（股）
            '5day_change': float,    # 5日漲幅（%）
        }
        失敗返回 None
    """
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW?interval=1d&range=6d'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            return None

        result = data['chart']['result'][0]
        info = {}

        # 收盤價
        if 'meta' in result and 'regularMarketPrice' in result['meta']:
            info['close_price'] = result['meta']['regularMarketPrice']

        # 成交量 + 5日漲幅
        if 'indicators' in result and 'quote' in result['indicators']:
            quote = result['indicators']['quote'][0]

            # 成交量（最後一天）
            if 'volume' in quote:
                volumes = [v for v in quote['volume'] if v is not None]
                if volumes:
                    info['daily_volume'] = volumes[-1]

            # 5日漲幅
            if 'close' in quote:
                closes = [c for c in quote['close'] if c is not None]
                if len(closes) >= 2:
                    first = closes[0]
                    last = closes[-1]
                    info['5day_change'] = (last - first) / first * 100

        return info if 'close_price' in info else None
    except:
        return None


def get_5day_change(code):
    """取得 5 日漲幅（向下相容包裝）"""
    data = get_stock_market_data(code)
    if data and '5day_change' in data:
        return data['5day_change']
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

        # v3.0：為 TOP50 買超補充股價、成交量、金額資訊
        print('\n正在查詢股價與成交量（約需 30-60 秒）...\n')
        for s in stocks_buy:
            market_data = get_stock_market_data(s['code'])
            if market_data:
                s['close_price'] = market_data.get('close_price')
                s['daily_volume'] = market_data.get('daily_volume')
                s['5day_change'] = market_data.get('5day_change')

                # 買超金額 = 買超股數 × 收盤價
                if s['close_price']:
                    s['buy_amount'] = s['total'] * s['close_price']
                    # 當日成交金額 ≈ 成交量(股) × 收盤價
                    if s.get('daily_volume') and s['daily_volume'] > 0:
                        s['daily_turnover'] = s['daily_volume'] * s['close_price']
                        s['buy_ratio'] = abs(s['buy_amount']) / s['daily_turnover'] * 100
                    else:
                        s['daily_turnover'] = None
                        s['buy_ratio'] = None
                else:
                    s['buy_amount'] = None
                    s['daily_turnover'] = None
                    s['buy_ratio'] = None
            else:
                s['close_price'] = None
                s['daily_volume'] = None
                s['5day_change'] = None
                s['buy_amount'] = None
                s['daily_turnover'] = None
                s['buy_ratio'] = None

        # 張數排名
        for i, s in enumerate(stocks_buy, 1):
            s['volume_rank'] = i

        # 金額排名
        stocks_by_amount = sorted(
            stocks_buy,
            key=lambda x: abs(x['buy_amount']) if x.get('buy_amount') else 0,
            reverse=True
        )
        for i, s in enumerate(stocks_by_amount, 1):
            s['amount_rank'] = i

        # 平均排名（張數排名 + 金額排名）/ 2
        for s in stocks_buy:
            vr = s.get('volume_rank', 50)
            ar = s.get('amount_rank', 50)
            s['avg_rank'] = (vr + ar) / 2

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


def format_amount(amount):
    """格式化金額為億元"""
    if amount is None:
        return '--'
    v = abs(amount) / 1e8  # 轉為億
    sign = '+' if amount >= 0 else '-'
    if v >= 10:
        return f'{sign}{v:.0f}億'
    elif v >= 1:
        return f'{sign}{v:.1f}億'
    else:
        return f'{sign}{v:.2f}億'


def format_ratio(ratio):
    """格式化佔成交比例"""
    if ratio is None:
        return '--'
    return f'{ratio:.1f}%'


def format_price(price):
    """格式化股價"""
    if price is None:
        return '--'
    if price >= 100:
        return f'{price:.0f}'
    else:
        return f'{price:.1f}'


def print_buy_tier(stocks, start_rank, title, include_price=True):
    """輸出買超單一層級（v3.0 含金額排名）"""
    print(f'### {title}')
    print()
    print('| 排名(張) | 排名(額) | 平均排名 | 代號 | 名稱 | 三大法人 | 買超金額 | 佔成交% | 收盤價 | 5日漲幅 | 狀態 |')
    print('|---------|---------|---------|------|------|---------|---------|--------|-------|--------|------|')

    for i, s in enumerate(stocks, start_rank):
        if include_price:
            pct = s.get('5day_change')
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        amt_rank = s.get('amount_rank', '--')
        amt_rank_str = f'{amt_rank}' if isinstance(amt_rank, int) else '--'
        avg_rank = s.get('avg_rank')
        avg_rank_str = f'{avg_rank:.1f}' if avg_rank is not None else '--'

        print(f"| {i} | {amt_rank_str} | {avg_rank_str} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_amount(s.get('buy_amount'))} | {format_ratio(s.get('buy_ratio'))} | {format_price(s.get('close_price'))} | {pct_str} | {status} |")

    print()


def print_sell_tier(stocks, start_rank, title, include_price=True):
    """輸出賣超單一層級"""
    print(f'### {title}')
    print()
    print('| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |')
    print('|------|------|------|---------|------|------|--------|------|')

    for i, s in enumerate(stocks, start_rank):
        if include_price:
            pct = get_5day_change(s['code'])
            pct_str = f'{pct:+.1f}%' if pct is not None else '--'
            status = get_status(pct)
        else:
            pct_str = '--'
            status = '--'

        print(f"| {i} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_value(s['trust'])} | {format_value(s['foreign'])} | {pct_str} | {status} |")

    print()


def print_top30_report(result, include_price=True):
    """輸出 TOP50 報告（v3.0 含金額排名）"""

    if not result:
        return

    date = result['date']
    buy_top50 = result['buy_top30']
    sell_top50 = result['sell_top30']

    # 買超 TOP50（分三層級，含金額排名）
    print(f'\n## 法人買超 TOP50（{date}）')
    print()

    print_buy_tier(buy_top50[:20], 1, '📌 TOP 1-20（優先推薦）', include_price)
    print_buy_tier(buy_top50[20:35], 21, '🔍 TOP 21-35（可考慮）', include_price)
    print_buy_tier(buy_top50[35:50], 36, '👀 TOP 36-50（觀察備用）', include_price)

    # 金額排名 TOP20（新增）
    stocks_by_amount = sorted(
        buy_top50,
        key=lambda x: abs(x['buy_amount']) if x.get('buy_amount') else 0,
        reverse=True
    )
    print('### 💰 張數排名 TOP20（法人實際買進張數）')
    print()
    # 用張數排名排序（即原始 buy_top50 順序）
    stocks_by_vol = sorted(
        buy_top50,
        key=lambda x: x.get('volume_rank', 99)
    )
    print('| 排名(張) | 排名(額) | 平均排名 | 代號 | 名稱 | 三大法人 | 買超金額 | 佔成交% | 收盤價 | 5日漲幅 | 狀態 |')
    print('|---------|---------|---------|------|------|---------|---------|--------|-------|--------|------|')

    for s in stocks_by_vol[:20]:
        pct = s.get('5day_change')
        pct_str = f'{pct:+.1f}%' if pct is not None else '--'
        status = get_status(pct)
        avg_rank = s.get('avg_rank')
        avg_rank_str = f'{avg_rank:.1f}' if avg_rank is not None else '--'

        print(f"| {s.get('volume_rank', '--')} | {s.get('amount_rank', '--')} | {avg_rank_str} | {s['code']} | {s['name']} | {format_value(s['total'])} | {format_amount(s.get('buy_amount'))} | {format_ratio(s.get('buy_ratio'))} | {format_price(s.get('close_price'))} | {pct_str} | {status} |")

    print()
    print('---')
    print()

    # 賣超 TOP50（分三層級）
    print(f'## 法人賣超 TOP50（{date}）')
    print()

    print_sell_tier(sell_top50[:20], 1, '🔴 TOP 1-20（重點避開）', include_price)
    print_sell_tier(sell_top50[20:35], 21, '⚠️ TOP 21-35（注意風險）', include_price)
    print_sell_tier(sell_top50[35:50], 36, '👁️ TOP 36-50（觀察參考）', include_price)

    print('---')
    print()
    print('**狀態標註說明**：')
    print('- [佈局中]：5日漲幅 < 0%（法人買但還沒漲，最佳）')
    print('- [可進場]：5日漲幅 0-3%（小漲，可買）')
    print('- [已小漲]：5日漲幅 3-5%（注意追高）')
    print('- [追高風險]：5日漲幅 5-8%（考慮等回檔）')
    print('- [已大漲]：5日漲幅 > 8%（不建議追）')
    print()
    print('**排名說明**：')
    print('- 排名(張)：依買超張數排序（傳統排名）')
    print('- 排名(額)：依買超金額排序（張數×股價，反映實際資金投入）')
    print('- 佔成交%：買超金額÷當日成交金額（越高=法人主導力越強）')


def print_positioning_opportunities(result):
    """輸出佈局機會（買超 + 還沒漲）"""

    if not result:
        return

    buy_top30 = result['buy_top30']

    print('\n## 佈局機會（法人買超 + 還沒漲）')
    print()
    print('| 代號 | 名稱 | 三大法人 | 買超金額 | 佔成交% | 5日漲幅 | 狀態 |')
    print('|------|------|---------|---------|--------|--------|------|')

    count = 0
    for s in buy_top30:
        pct = s.get('5day_change')
        if pct is not None and pct < 3:  # 5日漲幅 < 3%
            pct_str = f'{pct:+.1f}%'
            status = get_status(pct)
            print(f"| {s['code']} | {s['name']} | {format_value(s['total'])} | {format_amount(s.get('buy_amount'))} | {format_ratio(s.get('buy_ratio'))} | {pct_str} | {status} |")
            count += 1

    if count == 0:
        print('| -- | 無符合條件 | -- | -- | -- | -- | -- |')

    print()
    print(f'共 {count} 檔符合「佈局中」或「可進場」條件')


if __name__ == '__main__':
    import json
    from pathlib import Path
    from datetime import datetime

    # 解析命令列參數
    date = sys.argv[1] if len(sys.argv) > 1 else None

    print('=' * 60)
    print('法人買賣超 TOP30 查詢')
    print('=' * 60)

    # 查詢數據
    result = fetch_institutional_top30(date)

    if result:
        # 輸出完整報告（股價/成交量已在 fetch 階段查詢完畢）
        print_top30_report(result, include_price=True)

        # 輸出佈局機會
        print_positioning_opportunities(result)

        # 保存 JSON（供 merge_candidates.py 使用）
        if date:
            date_str = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        output_dir = Path(__file__).parent.parent / "data" / date_str
        output_dir.mkdir(parents=True, exist_ok=True)

        json_file = output_dir / "institutional_top50.json"
        json_data = {
            "date": date_str,
            "query_date": date,
            "total_buy": len(result['buy_top30']),
            "total_sell": len(result['sell_top30']),
            "stocks": result['buy_top30']  # TOP50 買超
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print()
        print(f"💾 已保存：{json_file}")
