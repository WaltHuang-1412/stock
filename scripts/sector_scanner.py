#!/usr/bin/env python3
"""
產業驅動掃描器 - 根據費半強弱推薦全產業鏈

使用方式：
  python3 scripts/sector_scanner.py

功能：
  1. 查詢費半漲跌幅
  2. 根據費半強弱決定推薦模式
  3. 掃描全產業鏈即時行情
  4. 輸出推薦清單
"""

import sys
import requests
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# 從 industry_chains.json 動態載入產業定義
def _load_sectors_from_chains():
    """從 industry_chains.json 建立產業掃描清單"""
    chains_file = Path(__file__).parent.parent / 'data' / 'industry_chains.json'
    sectors = {}
    other_sectors = {}

    # 半導體相關產業 key → 掃描器產業名 + 優先級
    TECH_MAPPING = {
        '半導體': ('晶圓代工/封測', 1),
        '記憶體': ('記憶體', 1),
        'IC設計': ('IC設計', 2),
        'AI': ('AI伺服器', 2),
        '光通訊': ('光通訊/載板', 2),
    }
    # 非半導體產業
    OTHER_MAPPING = {
        '金融': '金融',
        '塑化': '傳產',
        '鋼鐵原物料': '傳產',
        '營建水泥': '傳產',
    }

    try:
        with open(chains_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for ind_key, ind in data.get('industries', {}).items():
            stocks = []
            names = {}
            for tier in ind.get('tiers', {}).values():
                for s in tier.get('stocks', []):
                    code = s.get('code', '')
                    name = s.get('name', '')
                    if code and code not in names:
                        stocks.append(code)
                        names[code] = name

            if not stocks:
                continue

            if ind_key in TECH_MAPPING:
                display_name, priority = TECH_MAPPING[ind_key]
                sectors[display_name] = {
                    'stocks': stocks,
                    'names': names,
                    'priority': priority,
                }
            elif ind_key in OTHER_MAPPING:
                display_name = OTHER_MAPPING[ind_key]
                if display_name in other_sectors:
                    other_sectors[display_name]['stocks'].extend(stocks)
                    other_sectors[display_name]['names'].update(names)
                else:
                    other_sectors[display_name] = {
                        'stocks': stocks,
                        'names': names,
                    }
    except Exception as e:
        print(f"⚠️ 無法載入 industry_chains.json: {e}")

    return sectors, other_sectors


SECTORS, OTHER_SECTORS = _load_sectors_from_chains()


def get_sox_change():
    """查詢費半漲跌幅"""
    try:
        url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5ESOX?interval=1d&range=2d'
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10, verify=False)
        data = r.json()
        result = data['chart']['result'][0]
        closes = result['indicators']['quote'][0]['close']
        valid_closes = [c for c in closes if c is not None]
        if len(valid_closes) >= 2:
            change = (valid_closes[-1] - valid_closes[-2]) / valid_closes[-2] * 100
            return valid_closes[-1], change
    except Exception as e:
        print(f'費半查詢錯誤: {e}')
    return None, None


def get_stock_price(stock_code):
    """查詢個股即時行情"""
    try:
        url = f'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw'
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, verify=False)
        data = r.json()

        if 'msgArray' in data and len(data['msgArray']) > 0:
            info = data['msgArray'][0]
            price = info.get('z', '-')
            yesterday = info.get('y', '-')
            name = info.get('n', stock_code)

            if price != '-' and yesterday != '-':
                change = (float(price) - float(yesterday)) / float(yesterday) * 100
                return float(price), change, name
            else:
                # 用最佳五檔估算
                bid = info.get('b', '-')
                ask = info.get('a', '-')
                if bid != '-' and yesterday != '-':
                    bid_prices = bid.split('_')
                    if bid_prices and bid_prices[0]:
                        est_price = float(bid_prices[0])
                        change = (est_price - float(yesterday)) / float(yesterday) * 100
                        return est_price, change, name
    except Exception as e:
        print(f"[sector_scanner] Failed to get price for {stock_code}: {e}", file=sys.stderr)
    return None, None, None


def scan_sector(sector_name, sector_data, all_names=None):
    """掃描單一產業"""
    results = []
    stocks = sector_data['stocks']
    names = sector_data.get('names', all_names or {})

    for code in stocks:
        price, change, name = get_stock_price(code)
        if price is not None:
            display_name = names.get(code, name or code)
            results.append({
                'code': code,
                'name': display_name,
                'price': price,
                'change': change,
            })

    # 按漲幅排序
    results.sort(key=lambda x: x['change'], reverse=True)
    return results


def main():
    print('=' * 70)
    print('🔍 產業驅動掃描器')
    print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    # 1. 查詢費半
    sox_price, sox_change = get_sox_change()

    if sox_change is not None:
        print(f'\n📊 費城半導體指數: {sox_price:,.2f}')
        if sox_change >= 2:
            print(f'🔥 漲跌幅: {sox_change:+.2f}% → 全產業鏈模式！')
            mode = 'full'
        elif sox_change >= 1:
            print(f'🟢 漲跌幅: {sox_change:+.2f}% → 正常模式')
            mode = 'normal'
        elif sox_change >= 0:
            print(f'⚪ 漲跌幅: {sox_change:+.2f}% → 保守模式')
            mode = 'conservative'
        else:
            print(f'🔴 漲跌幅: {sox_change:+.2f}% → 防禦模式（金融/傳產）')
            mode = 'defensive'
    else:
        print('\n⚠️ 無法取得費半數據，使用正常模式')
        mode = 'normal'

    # 2. 根據模式掃描產業
    print('\n' + '=' * 70)

    if mode in ['full', 'normal']:
        print('📊 半導體產業鏈掃描')
        print('=' * 70)

        all_results = []

        for sector_name, sector_data in SECTORS.items():
            priority = sector_data.get('priority', 9)

            # 全產業鏈模式：全部掃描
            # 正常模式：只掃描優先級1-2
            if mode == 'full' or priority <= 2:
                results = scan_sector(sector_name, sector_data)

                if results:
                    print(f'\n【{sector_name}】')
                    for r in results:
                        emoji = '🔥' if r['change'] > 3 else '🟢' if r['change'] > 0 else '🔴'
                        print(f"  {emoji} {r['code']} {r['name']:8s}: {r['price']:8.2f} ({r['change']:+.2f}%)")
                        all_results.append({**r, 'sector': sector_name})
                else:
                    print(f'\n【{sector_name}】(尚未成交)')

        # 輸出總排行
        all_results.sort(key=lambda x: x['change'], reverse=True)
        print('\n' + '=' * 70)
        print('🔥 漲幅TOP15')
        print('=' * 70)
        for i, r in enumerate(all_results[:15], 1):
            emoji = '🔥' if r['change'] > 3 else '🟢' if r['change'] > 0 else '🔴'
            print(f"{i:2d}. {emoji} {r['code']} {r['name']:8s} [{r['sector']}]: {r['price']:8.2f} ({r['change']:+.2f}%)")

        # 推薦清單
        print('\n' + '=' * 70)
        print('📋 推薦清單（不看法人，純時事驅動）')
        print('=' * 70)

        if mode == 'full':
            print('\n🔥 費半 ≥ +2%，全產業鏈買進：')
            print('-' * 50)
            for sector_name in ['晶圓代工', '封測', '記憶體', 'IC設計', '載板PCB', 'AI伺服器']:
                sector_stocks = [r for r in all_results if r['sector'] == sector_name]
                if sector_stocks:
                    top = sector_stocks[0]  # 取該產業漲幅最高的
                    print(f"  {sector_name:10s}: {top['code']} {top['name']} ({top['change']:+.2f}%)")
        else:
            print('\n🟢 費半 +1~2%，優先推薦：')
            for r in all_results[:5]:
                print(f"  {r['code']} {r['name']} [{r['sector']}] ({r['change']:+.2f}%)")

    elif mode == 'defensive':
        print('📊 防禦產業掃描（金融/航運/傳產）')
        print('=' * 70)

        all_results = []
        for sector_name, sector_data in OTHER_SECTORS.items():
            results = scan_sector(sector_name, sector_data)

            if results:
                print(f'\n【{sector_name}】')
                for r in results[:5]:  # 每產業只顯示前5
                    emoji = '🟢' if r['change'] > 0 else '🔴'
                    print(f"  {emoji} {r['code']} {r['name']:8s}: {r['price']:8.2f} ({r['change']:+.2f}%)")
                    all_results.append({**r, 'sector': sector_name})

        # 推薦清單
        all_results.sort(key=lambda x: x['change'], reverse=True)
        print('\n' + '=' * 70)
        print('📋 防禦型推薦')
        print('=' * 70)
        for r in all_results[:5]:
            print(f"  {r['code']} {r['name']} [{r['sector']}] ({r['change']:+.2f}%)")

    print('\n' + '=' * 70)
    print('💡 使用說明：')
    print('   費半 ≥ +2%  → 全產業鏈模式，每個產業買龍頭')
    print('   費半 +1~2%  → 正常模式，選漲幅前5')
    print('   費半 0~1%   → 保守模式，觀望為主')
    print('   費半 < 0%   → 防禦模式，看金融/傳產')
    print('=' * 70)


if __name__ == '__main__':
    main()
