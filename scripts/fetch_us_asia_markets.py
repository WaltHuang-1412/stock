#!/usr/bin/env python3
"""
美國亞洲市場數據獲取工具
用於盤前分析時獲取最新的國際市場數據

功能：
- 美股市場數據（NASDAQ, S&P500, 道瓊, 費半指數）
- 台股ADR數據（台積電ADR, 聯電ADR等）
- 亞洲市場數據（日經225, 韓國KOSPI, 恆生指數等）
- 重要指標（VIX恐慌指數, 美元指數, USD/TWD匯率）
- 大宗商品（WTI原油, 黃金）

使用方法：
python3 scripts/fetch_us_asia_markets.py
"""

import yfinance as yf
import datetime
import pytz
from typing import Dict, Any, List
import json


class InternationalMarketFetcher:
    """國際市場數據獲取器"""

    def __init__(self):
        self.data = {}
        self.query_time = datetime.datetime.now(pytz.timezone('Asia/Taipei'))

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
            try:
                ticker = yf.Ticker(symbol)

                # 獲取最新價格數據
                hist = ticker.history(period='2d')
                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                    change = latest_price - prev_price
                    change_pct = (change / prev_price * 100) if prev_price else 0

                    # 獲取盤前數據（如果有）
                    try:
                        info = ticker.info
                        premarket_price = info.get('preMarketPrice')
                        premarket_change_pct = info.get('preMarketChangePercent', 0)

                        if premarket_price and premarket_change_pct:
                            us_data[name] = {
                                'symbol': symbol,
                                'close_price': round(latest_price, 2),
                                'change': round(change, 2),
                                'change_pct': round(change_pct, 2),
                                'premarket_price': round(premarket_price, 2),
                                'premarket_change_pct': round(premarket_change_pct, 2),
                                'status': 'premarket'
                            }
                        else:
                            us_data[name] = {
                                'symbol': symbol,
                                'close_price': round(latest_price, 2),
                                'change': round(change, 2),
                                'change_pct': round(change_pct, 2),
                                'status': 'closed'
                            }
                    except:
                        us_data[name] = {
                            'symbol': symbol,
                            'close_price': round(latest_price, 2),
                            'change': round(change, 2),
                            'change_pct': round(change_pct, 2),
                            'status': 'closed'
                        }

                    print(f"✅ {name}: {latest_price:.2f} ({change_pct:+.2f}%)")

            except Exception as e:
                print(f"❌ {name}: 數據獲取失敗 - {e}")
                us_data[name] = {'status': 'error', 'error': str(e)}

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
            try:
                ticker = yf.Ticker(symbol)

                # 獲取最新數據
                hist = ticker.history(period='2d')
                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                    change_pct = ((latest_price - prev_price) / prev_price * 100) if prev_price else 0

                    # 獲取盤前數據
                    try:
                        info = ticker.info
                        premarket_price = info.get('preMarketPrice')
                        premarket_change_pct = info.get('preMarketChangePercent', 0)

                        adr_data[name] = {
                            'symbol': symbol,
                            'close_price': round(latest_price, 2),
                            'change_pct': round(change_pct, 2),
                            'premarket_price': round(premarket_price, 2) if premarket_price else None,
                            'premarket_change_pct': round(premarket_change_pct, 2) if premarket_change_pct else 0,
                            'status': 'premarket' if premarket_price else 'closed'
                        }
                    except:
                        adr_data[name] = {
                            'symbol': symbol,
                            'close_price': round(latest_price, 2),
                            'change_pct': round(change_pct, 2),
                            'status': 'closed'
                        }

                    print(f"✅ {name}: ${latest_price:.2f} ({change_pct:+.2f}%)")

            except Exception as e:
                print(f"❌ {name}: 數據獲取失敗 - {e}")
                adr_data[name] = {'status': 'error', 'error': str(e)}

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
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')

                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                    change_pct = ((latest_price - prev_price) / prev_price * 100) if prev_price else 0

                    asia_data[name] = {
                        'symbol': symbol,
                        'price': round(latest_price, 0),
                        'change_pct': round(change_pct, 2),
                        'status': 'updated'
                    }

                    print(f"✅ {name}: {latest_price:,.0f} ({change_pct:+.2f}%)")

            except Exception as e:
                print(f"❌ {name}: 數據獲取失敗 - {e}")
                asia_data[name] = {'status': 'error', 'error': str(e)}

        return asia_data

    def fetch_key_indicators(self) -> Dict[str, Any]:
        """獲取關鍵指標"""
        print("📊 正在獲取關鍵指標...")

        indicators = {
            'VIX恐慌指數': '^VIX',
            '美元指數': 'DX-Y.NYB',
            'WTI原油': 'CL=F',
            '黃金': 'GC=F'
        }

        indicator_data = {}

        for name, symbol in indicators.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')

                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                    change_pct = ((latest_price - prev_price) / prev_price * 100) if prev_price else 0

                    indicator_data[name] = {
                        'symbol': symbol,
                        'price': round(latest_price, 2),
                        'change_pct': round(change_pct, 2),
                        'status': 'updated'
                    }

                    print(f"✅ {name}: {latest_price:.2f} ({change_pct:+.2f}%)")

            except Exception as e:
                print(f"❌ {name}: 數據獲取失敗 - {e}")
                indicator_data[name] = {'status': 'error', 'error': str(e)}

        # 特別處理USD/TWD匯率
        try:
            usdtwd = yf.Ticker('TWD=X')
            hist = usdtwd.history(period='5d')
            if not hist.empty:
                rate = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else rate
                change = rate - prev

                indicator_data['美元/台幣匯率'] = {
                    'symbol': 'TWD=X',
                    'rate': round(rate, 3),
                    'change': round(change, 3),
                    'status': 'updated'
                }

                print(f"✅ 美元/台幣: {rate:.3f} ({change:+.3f})")

        except Exception as e:
            print(f"❌ 美元/台幣: 數據獲取失敗 - {e}")
            indicator_data['美元/台幣匯率'] = {'status': 'error', 'error': str(e)}

        return indicator_data

    def get_market_session_info(self) -> Dict[str, str]:
        """獲取市場交易時段資訊"""
        now_ny = datetime.datetime.now(pytz.timezone('America/New_York'))
        now_taipei = self.query_time

        # 美股交易時間判斷 (EST: 9:30-16:00)
        market_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
        premarket_start = now_ny.replace(hour=4, minute=0, second=0, microsecond=0)

        if now_ny.weekday() >= 5:  # 週末
            us_session = "週末休市"
        elif premarket_start <= now_ny < market_open:
            us_session = "盤前交易"
        elif market_open <= now_ny <= market_close:
            us_session = "正常交易"
        elif market_close < now_ny:
            us_session = "盤後交易"
        else:
            us_session = "休市"

        # 台股交易時間判斷
        if now_taipei.weekday() >= 5:  # 週末
            tw_session = "週末休市"
        elif 9 <= now_taipei.hour < 13 or (now_taipei.hour == 13 and now_taipei.minute <= 30):
            tw_session = "正常交易"
        elif now_taipei.hour < 9:
            tw_session = "盤前"
        else:
            tw_session = "盤後"

        return {
            'us_session': us_session,
            'tw_session': tw_session,
            'query_time_ny': now_ny.strftime('%Y-%m-%d %H:%M:%S EST'),
            'query_time_taipei': now_taipei.strftime('%Y-%m-%d %H:%M:%S CST')
        }

    def fetch_all_data(self) -> Dict[str, Any]:
        """獲取所有國際市場數據"""
        print("🌐 開始獲取國際市場數據")
        print(f"📅 查詢時間：{self.query_time.strftime('%Y-%m-%d %H:%M:%S CST')}")
        print("=" * 60)

        # 獲取市場時段資訊
        session_info = self.get_market_session_info()

        # 獲取各市場數據
        us_data = self.fetch_us_markets()
        adr_data = self.fetch_taiwan_adrs()
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
        output.append(f"**數據更新時間**：{query_time} ({session_info['tw_session']})")
        output.append("")

        # 美股市場
        output.append("### 📊 美股表現")
        output.append(f"**美股狀態**：{session_info['us_session']} ({session_info['query_time_ny']})")
        output.append("")

        for name, info in data['us_markets'].items():
            if info.get('status') == 'error':
                output.append(f"- **{name}**：數據獲取失敗")
            else:
                close_info = f"{info['close_price']:,} ({info['change_pct']:+.2f}%)"
                if info.get('premarket_price'):
                    premarket_info = f"盤前 {info['premarket_price']:,} ({info['premarket_change_pct']:+.2f}%)"
                    output.append(f"- **{name}**：{close_info} | {premarket_info}")
                else:
                    output.append(f"- **{name}**：{close_info}")

        output.append("")

        # 台股ADR
        output.append("### 🇹🇼 台股ADR")
        for name, info in data['taiwan_adrs'].items():
            if info.get('status') == 'error':
                output.append(f"- **{name}**：數據獲取失敗")
            else:
                close_info = f"${info['close_price']:.2f} ({info['change_pct']:+.2f}%)"
                if info.get('premarket_price'):
                    premarket_info = f"盤前 ${info['premarket_price']:.2f} ({info['premarket_change_pct']:+.2f}%)"
                    output.append(f"- **{name}**：{close_info} | {premarket_info}")
                else:
                    output.append(f"- **{name}**：{close_info}")

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


def main():
    """主執行函數"""
    fetcher = InternationalMarketFetcher()

    # 獲取所有數據
    data = fetcher.fetch_all_data()

    # 保存原始數據到JSON（供其他工具使用）
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"/Users/walter/Documents/GitHub/stock/data/international_markets/{timestamp}.json"

    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n📁 原始數據已保存至：{json_filename}")

    # 輸出格式化的分析文本
    analysis_text = fetcher.format_for_analysis(data)
    print("\n" + "="*60)
    print("📋 盤前分析格式輸出：")
    print("="*60)
    print(analysis_text)

    return data, analysis_text


if __name__ == "__main__":
    main()