#!/usr/bin/env python3
"""
美國亞洲市場數據獲取工具 (v2.0 - 使用 requests)
用於盤前分析時獲取最新的國際市場數據

功能：
- 美股市場數據（NASDAQ, S&P500, 道瓊, 費半指數）
- 台股ADR數據（台積電ADR, 聯電ADR等）
- 亞洲市場數據（日經225, 韓國KOSPI, 恆生指數等）
- 重要指標（VIX恐慌指數, 美元指數, USD/TWD匯率）
- 大宗商品（WTI原油, 黃金）

使用方法：
python scripts/fetch_us_asia_markets.py
"""

import sys
import io

# Windows 環境 stdout 編碼修正（避免 emoji 輸出時 cp950 報錯）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests
import datetime
import json
import os
from typing import Dict, Any

# 設定 requests headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def _prev_trading_close(result: Dict[str, Any], meta: Dict[str, Any]):
    """從日 K 收盤序列取「前一交易日」收盤價。

    Yahoo chart API 的 chartPreviousClose 是圖表區間起點的前收——range=5d 時
    等於 5 個交易日前的收盤，拿來當基準會把單日漲跌算成 5 日累計漲幅
    （2026-07-09 起盤前費半/MSFT 等連續誤報的根因）。
    正確基準：最後一根 K 棒若屬於當前交易時段（日期 >= regularMarketTime 的
    日期，如盤中即時棒或今日剛收盤的棒），前收取倒數第二根；否則取最後一根。
    無法判斷時回傳 None，由呼叫端 fallback。
    """
    try:
        timestamps = result.get('timestamp') or []
        closes = result['indicators']['quote'][0].get('close') or []
        market_time = meta.get('regularMarketTime')
        if market_time is None:
            return None
        offset = meta.get('gmtoffset', 0)
        valid = [(t, c) for t, c in zip(timestamps, closes) if c is not None]
        if len(valid) < 2:
            return None

        def to_local_date(ts):
            return datetime.datetime.fromtimestamp(
                ts + offset, tz=datetime.timezone.utc).date()

        if to_local_date(valid[-1][0]) >= to_local_date(market_time):
            return valid[-2][1]
        return valid[-1][1]
    except Exception:
        return None


def fetch_yahoo_quote(symbol: str) -> Dict[str, Any]:
    """從 Yahoo Finance API 獲取報價"""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d'
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()

        result = data['chart']['result'][0]
        meta = result['meta']

        current_price = meta.get('regularMarketPrice', 0)
        prev_close = _prev_trading_close(result, meta)
        if not prev_close:
            prev_close = meta.get('chartPreviousClose', meta.get('previousClose', current_price))

        if prev_close and prev_close > 0:
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
        else:
            change = 0
            change_pct = 0

        return {
            'price': round(current_price, 2),
            'prev_close': round(prev_close, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'status': 'ok'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


class InternationalMarketFetcher:
    """國際市場數據獲取器"""

    def __init__(self):
        self.data = {}
        self.query_time = datetime.datetime.now()

    def fetch_us_markets(self) -> Dict[str, Any]:
        """獲取美股市場數據"""
        print("🇺🇸 正在獲取美股市場數據...")

        us_symbols = {
            'NASDAQ綜合指數': '^IXIC',
            'S&P 500': '^GSPC',
            '道瓊工業指數': '^DJI',
            '費城半導體指數': '^SOX'
        }

        us_data = {}

        for name, symbol in us_symbols.items():
            result = fetch_yahoo_quote(symbol)
            if result['status'] == 'ok':
                us_data[name] = {
                    'symbol': symbol,
                    'close_price': result['price'],
                    'change': result['change'],
                    'change_pct': result['change_pct'],
                    'status': 'closed'
                }
                print(f"✅ {name}: {result['price']:,.2f} ({result['change_pct']:+.2f}%)")
            else:
                print(f"❌ {name}: 數據獲取失敗 - {result.get('error', 'Unknown')}")
                us_data[name] = result

        return us_data

    def fetch_taiwan_adrs(self) -> Dict[str, Any]:
        """獲取台股ADR數據"""
        print("🇹🇼 正在獲取台股ADR數據...")

        adr_symbols = {
            '台積電ADR': 'TSM',
            '聯電ADR': 'UMC',
            '日月光ADR': 'ASX',
            '中華電ADR': 'CHT'
        }

        adr_data = {}

        for name, symbol in adr_symbols.items():
            result = fetch_yahoo_quote(symbol)
            if result['status'] == 'ok':
                adr_data[name] = {
                    'symbol': symbol,
                    'close_price': result['price'],
                    'change_pct': result['change_pct'],
                    'status': 'closed'
                }
                print(f"✅ {name}: ${result['price']:.2f} ({result['change_pct']:+.2f}%)")
            else:
                print(f"❌ {name}: 數據獲取失敗 - {result.get('error', 'Unknown')}")
                adr_data[name] = result

        return adr_data

    def fetch_asia_markets(self) -> Dict[str, Any]:
        """獲取亞洲市場數據"""
        print("🌏 正在獲取亞洲市場數據...")

        asia_symbols = {
            '日經225': '^N225',
            '韓國KOSPI': '^KS11',
            '香港恆生': '^HSI',
            '上證指數': '000001.SS',
            '新加坡STI': '^STI'
        }

        asia_data = {}

        for name, symbol in asia_symbols.items():
            result = fetch_yahoo_quote(symbol)
            if result['status'] == 'ok':
                asia_data[name] = {
                    'symbol': symbol,
                    'price': round(result['price'], 0),
                    'change_pct': result['change_pct'],
                    'status': 'updated'
                }
                print(f"✅ {name}: {result['price']:,.0f} ({result['change_pct']:+.2f}%)")
            else:
                print(f"❌ {name}: 數據獲取失敗 - {result.get('error', 'Unknown')}")
                asia_data[name] = result

        return asia_data

    def fetch_semiconductor_stocks(self) -> Dict[str, Any]:
        """獲取半導體/科技關鍵個股（v2.1 新增）"""
        print("🔬 正在獲取半導體/科技關鍵個股...")

        # 7大產業、20檔關鍵美股
        stocks = {
            # 記憶體 → 南亞科、華邦電、旺宏
            'Micron': 'MU',
            'Western Digital': 'WDC',

            # AI/晶片 → 聯發科、IC設計
            'AMD': 'AMD',
            'Intel': 'INTC',

            # 設備 → 弘塑、辛耘、家登
            'ASML': 'ASML',
            'Applied Materials': 'AMAT',
            'Lam Research': 'LRCX',
            'KLA': 'KLAC',

            # 網通 → 智邦、啟碁
            'Broadcom': 'AVGO',
            'Marvell': 'MRVL',
            'Cisco': 'CSCO',
            'Arista': 'ANET',

            # 消費電子 → 鴻海、大立光、和碩
            'Apple': 'AAPL',
            'Qualcomm': 'QCOM',

            # AI伺服器/雲端 → 廣達、緯創、緯穎
            'Super Micro': 'SMCI',
            'Dell': 'DELL',
            'Amazon': 'AMZN',
            'Microsoft': 'MSFT',
            'Google': 'GOOGL',
            'Meta': 'META',

            # 電動車 → 鴻海、和大、貿聯
            'Tesla': 'TSLA',
        }

        stock_data = {}

        for name, symbol in stocks.items():
            result = fetch_yahoo_quote(symbol)
            if result['status'] == 'ok':
                change_pct = result['change_pct']
                # 標註漲跌幅度
                if change_pct >= 5:
                    emoji = '🔥'
                elif change_pct >= 2:
                    emoji = '⭐'
                elif change_pct > 0:
                    emoji = '✅'
                elif change_pct > -2:
                    emoji = '➖'
                else:
                    emoji = '🔴'

                stock_data[name] = {
                    'symbol': symbol,
                    'price': result['price'],
                    'change_pct': change_pct,
                    'status': 'ok',
                    'emoji': emoji
                }
                print(f"{emoji} {name}({symbol}): ${result['price']:.2f} ({change_pct:+.2f}%)")
            else:
                print(f"❌ {name}({symbol}): 數據獲取失敗")
                stock_data[name] = {'status': 'error', 'symbol': symbol}

        return stock_data

    def fetch_key_indicators(self) -> Dict[str, Any]:
        """獲取關鍵指標"""
        print("📊 正在獲取關鍵指標...")

        indicators = {
            'VIX恐慌指數': '^VIX',
            '美元指數': 'DX-Y.NYB',
            'WTI原油': 'CL=F',
            '黃金': 'GC=F',
            '輝達': 'NVDA'
        }

        indicator_data = {}

        for name, symbol in indicators.items():
            result = fetch_yahoo_quote(symbol)
            if result['status'] == 'ok':
                indicator_data[name] = {
                    'symbol': symbol,
                    'price': result['price'],
                    'change_pct': result['change_pct'],
                    'status': 'updated'
                }
                print(f"✅ {name}: {result['price']:.2f} ({result['change_pct']:+.2f}%)")
            else:
                print(f"❌ {name}: 數據獲取失敗 - {result.get('error', 'Unknown')}")
                indicator_data[name] = result

        # 特別處理USD/TWD匯率
        result = fetch_yahoo_quote('TWD=X')
        if result['status'] == 'ok':
            indicator_data['美元/台幣匯率'] = {
                'symbol': 'TWD=X',
                'rate': round(result['price'], 3),
                'change': result['change'],
                'status': 'updated'
            }
            print(f"✅ 美元/台幣: {result['price']:.3f} ({result['change']:+.3f})")
        else:
            print(f"❌ 美元/台幣: 數據獲取失敗")
            indicator_data['美元/台幣匯率'] = result

        return indicator_data

    def get_market_session_info(self) -> Dict[str, str]:
        """獲取市場交易時段資訊"""
        now = self.query_time

        # 簡單判斷 (台北時間)
        hour = now.hour
        weekday = now.weekday()

        if weekday >= 5:  # 週末
            tw_session = "週末休市"
            us_session = "週末休市"
        elif 9 <= hour < 14:
            tw_session = "正常交易"
            us_session = "休市"
        elif hour < 9:
            tw_session = "盤前"
            us_session = "盤後交易" if hour >= 5 else "正常交易"
        else:
            tw_session = "盤後"
            us_session = "盤前" if hour >= 21 else "休市"

        return {
            'us_session': us_session,
            'tw_session': tw_session,
            'query_time_taipei': now.strftime('%Y-%m-%d %H:%M:%S CST')
        }

    def fetch_all_data(self) -> Dict[str, Any]:
        """獲取所有國際市場數據"""
        print("🌐 開始獲取國際市場數據")
        print(f"📅 查詢時間：{self.query_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 獲取市場時段資訊
        session_info = self.get_market_session_info()

        # 獲取各市場數據
        us_data = self.fetch_us_markets()
        adr_data = self.fetch_taiwan_adrs()
        semiconductor_data = self.fetch_semiconductor_stocks()  # v2.1 新增
        asia_data = self.fetch_asia_markets()
        indicators = self.fetch_key_indicators()

        # 整合所有數據
        all_data = {
            'query_info': {
                'query_time': self.query_time.isoformat(),
                'session_info': session_info
            },
            'us_markets': us_data,
            'taiwan_adrs': adr_data,
            'semiconductor_stocks': semiconductor_data,  # v2.1 新增
            'asia_markets': asia_data,
            'key_indicators': indicators
        }

        print("\n" + "=" * 60)
        print("✅ 國際市場數據獲取完成")

        return all_data

    def format_for_analysis(self, data: Dict[str, Any]) -> str:
        """格式化數據供盤前分析使用"""
        session_info = data['query_info']['session_info']
        query_time = data['query_info']['query_time']

        output = []
        output.append(f"## 🌐 國際市場概況")
        output.append(f"**數據更新時間**：{query_time}")
        output.append("")

        # 美股市場
        output.append("### 📊 美股表現")
        output.append("")

        for name, info in data['us_markets'].items():
            if info.get('status') == 'error':
                output.append(f"- **{name}**：數據獲取失敗")
            else:
                output.append(f"- **{name}**：{info['close_price']:,} ({info['change_pct']:+.2f}%)")

        output.append("")

        # 台股ADR
        output.append("### 🇹🇼 台股ADR")
        for name, info in data['taiwan_adrs'].items():
            if info.get('status') == 'error':
                output.append(f"- **{name}**：數據獲取失敗")
            else:
                output.append(f"- **{name}**：${info['close_price']:.2f} ({info['change_pct']:+.2f}%)")

        output.append("")

        # 半導體/科技關鍵個股 (v2.1 新增)
        if 'semiconductor_stocks' in data:
            output.append("### 🔬 半導體/科技關鍵個股")
            output.append("")

            # 按產業分組顯示
            categories = {
                '記憶體': ['Micron', 'Western Digital'],
                'AI/晶片': ['AMD', 'Intel'],
                '設備': ['ASML', 'Applied Materials', 'Lam Research', 'KLA'],
                '網通': ['Broadcom', 'Marvell', 'Cisco', 'Arista'],
                '消費電子': ['Apple', 'Qualcomm'],
                'AI伺服器/雲端': ['Super Micro', 'Dell', 'Amazon', 'Microsoft', 'Google', 'Meta'],
                '電動車': ['Tesla'],
            }

            for category, stocks in categories.items():
                output.append(f"**{category}**：")
                for name in stocks:
                    if name in data['semiconductor_stocks']:
                        info = data['semiconductor_stocks'][name]
                        if info.get('status') == 'error':
                            output.append(f"- {name}：數據獲取失敗")
                        else:
                            emoji = info.get('emoji', '')
                            output.append(f"- {emoji} {name}({info['symbol']}): ${info['price']:.2f} ({info['change_pct']:+.2f}%)")
                output.append("")

        # 亞洲市場
        output.append("### 🌏 亞洲市場")
        for name, info in data['asia_markets'].items():
            if info.get('status') == 'error':
                output.append(f"- **{name}**：數據獲取失敗")
            else:
                output.append(f"- **{name}**：{info['price']:,} ({info['change_pct']:+.2f}%)")

        output.append("")

        # 關鍵指標
        output.append("### 📈 關鍵指標")
        for name, info in data['key_indicators'].items():
            if info.get('status') == 'error':
                output.append(f"- **{name}**：數據獲取失敗")
            elif name == '美元/台幣匯率':
                output.append(f"- **{name}**：{info['rate']:.3f} ({info['change']:+.3f})")
            else:
                output.append(f"- **{name}**：{info['price']:.2f} ({info['change_pct']:+.2f}%)")

        return "\n".join(output)


def create_simple_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    創建簡化的 JSON 格式供 identify_hotspots.py 使用

    Returns:
        簡化的 dict，包含關鍵指標的漲跌幅
    """
    simple_data = {}

    # 美股市場
    if 'us_markets' in data:
        for name, info in data['us_markets'].items():
            if info.get('status') != 'error':
                # 移除中文字，使用簡化鍵名
                key = name.replace('綜合指數', '').replace('工業指數', '').replace('指數', '').strip()
                # 特殊處理費城半導體
                if '費城半導體' in key:
                    key = '費城半導體'
                simple_data[key] = info['change_pct']

    # 台股ADR
    if 'taiwan_adrs' in data:
        for name, info in data['taiwan_adrs'].items():
            if info.get('status') != 'error':
                # ADR 數據不放入簡化 JSON（避免混淆）
                pass

    # 半導體/科技個股
    if 'semiconductor_stocks' in data:
        for name, info in data['semiconductor_stocks'].items():
            if info.get('status') != 'error':
                simple_data[name] = info['change_pct']

    # 關鍵指標
    if 'key_indicators' in data:
        for name, info in data['key_indicators'].items():
            if info.get('status') != 'error':
                # 特殊處理輝達（重要催化劑）
                if name == '輝達':
                    simple_data['NVIDIA'] = info['change_pct']
                elif name == 'WTI原油':
                    simple_data['WTI原油'] = info['change_pct']
                elif name == '黃金':
                    simple_data['黃金'] = info['change_pct']
                elif name == 'VIX恐慌指數':
                    simple_data['VIX'] = info['change_pct']

    return simple_data


def main():
    """主執行函數"""
    import argparse

    parser = argparse.ArgumentParser(description='獲取國際市場數據')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both',
                        help='輸出格式：json（JSON格式）, markdown（Markdown格式）, both（兩者都輸出）')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='輸出目錄（如果指定，會寫入文件而非stdout）')
    args = parser.parse_args()

    fetcher = InternationalMarketFetcher()

    # 獲取所有數據
    data = fetcher.fetch_all_data()

    # 創建簡化 JSON
    simple_json = create_simple_json(data)

    # 根據格式輸出
    if args.output_dir:
        # 輸出到文件
        import os
        os.makedirs(args.output_dir, exist_ok=True)

        if args.format in ['json', 'both']:
            json_file = os.path.join(args.output_dir, 'us_asia_markets.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(simple_json, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON 已保存：{json_file}", file=sys.stderr)

        if args.format in ['markdown', 'both']:
            md_file = os.path.join(args.output_dir, 'us_asia_markets.md')
            analysis_text = fetcher.format_for_analysis(data)
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(analysis_text)
            print(f"✅ Markdown 已保存：{md_file}", file=sys.stderr)
    else:
        # 輸出到 stdout
        if args.format == 'json':
            print(json.dumps(simple_json, ensure_ascii=False, indent=2))
        elif args.format == 'markdown':
            analysis_text = fetcher.format_for_analysis(data)
            print(analysis_text)
        else:  # both
            # 先輸出 JSON（供管道使用）
            print(json.dumps(simple_json, ensure_ascii=False, indent=2))
            # Markdown 輸出到 stderr（不干擾 JSON）
            analysis_text = fetcher.format_for_analysis(data)
            print("\n" + "="*60, file=sys.stderr)
            print("📋 Markdown 格式（人類閱讀）：", file=sys.stderr)
            print("="*60, file=sys.stderr)
            print(analysis_text, file=sys.stderr)

    return data, simple_json


if __name__ == "__main__":
    main()
