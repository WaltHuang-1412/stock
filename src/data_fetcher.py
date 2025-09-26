import requests
import pandas as pd
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import yaml
import logging
from urllib.parse import urljoin
import json

class DataFetcher:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['scraping']['user_agent']
        })
        
        # 設置日誌
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_stock_data(self, symbol, market='taiwan'):
        """獲取股票基本數據"""
        try:
            if market == 'taiwan':
                return self._fetch_taiwan_stock_data(symbol)
            else:
                return self._fetch_us_stock_data(symbol)
        except Exception as e:
            self.logger.error(f"獲取股票數據失敗: {e}")
            return None
    
    def _fetch_taiwan_stock_data(self, symbol):
        """獲取台股數據"""
        try:
            # 方法1: 使用證交所即時報價API
            twse_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{symbol}.tw"
            
            response = self.session.get(twse_url, timeout=self.config['scraping']['request_timeout'])
            response.raise_for_status()
            
            data_json = response.json()
            
            if 'msgArray' in data_json and data_json['msgArray']:
                stock_info = data_json['msgArray'][0]
                
                data = {
                    'symbol': symbol,
                    'current_price': stock_info.get('z', 'N/A'),  # 成交價
                    'volume': stock_info.get('v', 'N/A'),         # 成交量
                    'high': stock_info.get('h', 'N/A'),           # 最高價
                    'low': stock_info.get('l', 'N/A'),            # 最低價
                    'open': stock_info.get('o', 'N/A'),           # 開盤價
                    'change': stock_info.get('c', 'N/A'),         # 漲跌
                    'change_percent': stock_info.get('p', 'N/A'), # 漲跌幅
                    'market': 'taiwan',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'twse_api'
                }
                
                return data
            
            # 方法2: 備用Yahoo Finance (如果證交所API失敗)
            return self._fetch_yahoo_taiwan_stock(symbol)
            
        except Exception as e:
            self.logger.error(f"獲取台股 {symbol} 數據失敗: {e}")
            # 嘗試備用方法
            return self._fetch_yahoo_taiwan_stock(symbol)
    
    def _fetch_yahoo_taiwan_stock(self, symbol):
        """備用方法: Yahoo Finance台股數據"""
        try:
            url = f"https://tw.finance.yahoo.com/quote/{symbol}.TW"
            
            response = self.session.get(url, timeout=self.config['scraping']['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 嘗試多種可能的價格選擇器
            price = None
            price_selectors = [
                'span[data-symbol$=".TW"][data-field="regularMarketPrice"]',
                'span.Fw\\(b\\).Fz\\(36px\\)',
                'fin-streamer[data-field="regularMarketPrice"]',
                '.Fw\\(b\\).Fz\\(36px\\).Mt\\(-4px\\)',
            ]
            
            for selector in price_selectors:
                try:
                    element = soup.select_one(selector)
                    if element:
                        price = element.get_text().strip()
                        break
                except:
                    continue
            
            data = {
                'symbol': symbol,
                'current_price': price or 'N/A',
                'market': 'taiwan',
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo_finance_tw_backup'
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"Yahoo備用方法也失敗: {e}")
            return {
                'symbol': symbol,
                'current_price': 'N/A',
                'market': 'taiwan',
                'timestamp': datetime.now().isoformat(),
                'source': 'failed',
                'error': str(e)
            }
    
    def _fetch_us_stock_data(self, symbol):
        """獲取美股數據"""
        try:
            # Yahoo Finance US API
            url = f"https://finance.yahoo.com/quote/{symbol}"
            
            response = self.session.get(url, timeout=self.config['scraping']['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取價格資訊
            price_element = soup.find('fin-streamer', {'data-symbol': symbol, 'data-field': 'regularMarketPrice'})
            price = price_element.get('value') if price_element else 'N/A'
            
            data = {
                'symbol': symbol,
                'current_price': price,
                'market': 'us',
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo_finance_us'
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"獲取美股 {symbol} 數據失敗: {e}")
            return None
    
    def fetch_institutional_data(self, symbol, market='taiwan'):
        """獲取法人數據"""
        try:
            if market == 'taiwan':
                return self._fetch_taiwan_institutional_data(symbol)
            else:
                return self._fetch_us_institutional_data(symbol)
        except Exception as e:
            self.logger.error(f"獲取法人數據失敗: {e}")
            return None
    
    def _fetch_taiwan_institutional_data(self, symbol):
        """獲取台股法人數據"""
        try:
            # 方法1: 嘗試證交所三大法人買賣超API
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            # 嘗試當日數據，如果是假日則往前推
            for i in range(7):  # 最多往前找7天
                check_date = (today - timedelta(days=i)).strftime('%Y%m%d')
                
                url = "https://www.twse.com.tw/rwd/zh/fund/T86"
                params = {
                    'response': 'json',
                    'date': check_date,
                    'selectType': 'ALLBUT0999'
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=self.config['scraping']['request_timeout'])
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'data' in data and data['data']:
                            for row in data['data']:
                                if len(row) > 0 and row[0] == symbol:
                                    # 成功找到數據
                                    institutional_data = {
                                        'symbol': symbol,
                                        'date': check_date,
                                        'foreign_net': self._safe_convert_to_float(row[4]) if len(row) > 4 else 0,
                                        'investment_trust_net': self._safe_convert_to_float(row[7]) if len(row) > 7 else 0,
                                        'dealer_net': self._safe_convert_to_float(row[10]) if len(row) > 10 else 0,
                                        'total_net': self._safe_convert_to_float(row[13]) if len(row) > 13 else 0,
                                        'source': 'twse',
                                        'timestamp': datetime.now().isoformat()
                                    }
                                    return institutional_data
                except:
                    continue
            
            # 如果無法獲取真實數據，返回 None
            return None
            
        except Exception as e:
            self.logger.error(f"獲取台股法人數據失敗: {e}")
            return None
    
    def _safe_convert_to_float(self, value):
        """安全轉換為浮點數"""
        try:
            if isinstance(value, str):
                # 移除千分位逗號
                value = value.replace(',', '')
            return float(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    
    def _fetch_us_institutional_data(self, symbol):
        """獲取美股法人數據（簡化版本）"""
        # 美股法人數據較複雜，這裡先返回空數據
        return {
            'symbol': symbol,
            'message': '美股法人數據需要更複雜的實現',
            'timestamp': datetime.now().isoformat()
        }
    
    def fetch_news_data(self, symbol, market='taiwan'):
        """獲取新聞數據"""
        try:
            news_data = []
            
            # 鉅亨網新聞
            cnyes_news = self._fetch_cnyes_news(symbol)
            if cnyes_news:
                news_data.extend(cnyes_news)
            
            # Yahoo財經新聞
            yahoo_news = self._fetch_yahoo_finance_news(symbol, market)
            if yahoo_news:
                news_data.extend(yahoo_news)
            
            return news_data
            
        except Exception as e:
            self.logger.error(f"獲取新聞數據失敗: {e}")
            return []
    
    def _fetch_cnyes_news(self, symbol):
        """獲取鉅亨網新聞"""
        try:
            # 方法1: 嘗試鉅亨網台股新聞
            url = "https://news.cnyes.com/api/v3/news/category/tw_stock"
            
            response = self.session.get(url, timeout=self.config['scraping']['request_timeout'])
            
            if response.status_code == 200:
                data = response.json()
                news_list = []
                
                if 'items' in data and 'data' in data['items']:
                    for article in data['items']['data'][:5]:
                        title = article.get('title', '')
                        # 簡單關鍵字過濾
                        if symbol in title or self._is_stock_related(title, symbol):
                            news_item = {
                                'title': title,
                                'summary': article.get('summary', ''),
                                'url': f"https://news.cnyes.com/news/id/{article.get('newsId', '')}",
                                'publish_time': article.get('publishAt', ''),
                                'source': 'cnyes',
                                'symbol': symbol
                            }
                            news_list.append(news_item)
                
                if news_list:
                    return news_list
            
            # 無法獲取真實新聞數據
            return []
            
        except Exception as e:
            self.logger.error(f"獲取鉅亨網新聞失敗: {e}")
            return []
    
    def _is_stock_related(self, title, symbol):
        """判斷新聞是否與股票相關"""
        # 根據股票代號獲取公司名稱
        company_names = {
            '2330': ['台積電', 'TSMC'],
            '2317': ['鴻海'],
            '2454': ['聯發科'],
        }
        
        if symbol in company_names:
            return any(name in title for name in company_names[symbol])
        
        return False
    
    
    def _fetch_yahoo_finance_news(self, symbol, market):
        """獲取Yahoo財經新聞"""
        try:
            if market == 'taiwan':
                url = f"https://tw.finance.yahoo.com/quote/{symbol}.TW/news"
            else:
                url = f"https://finance.yahoo.com/quote/{symbol}/news"
            
            response = self.session.get(url, timeout=self.config['scraping']['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取新聞標題和連結
            news_items = soup.find_all('a', {'class': lambda x: x and 'Fw(b)' in str(x)})[:5]
            
            news_list = []
            for item in news_items:
                title = item.get_text().strip()
                link = item.get('href', '')
                if link and not link.startswith('http'):
                    link = urljoin(url, link)
                
                news_item = {
                    'title': title,
                    'url': link,
                    'source': 'yahoo_finance',
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                }
                news_list.append(news_item)
            
            return news_list
            
        except Exception as e:
            self.logger.error(f"獲取Yahoo財經新聞失敗: {e}")
            return []
    
    def fetch_all_data(self, symbol, market='taiwan'):
        """獲取所有相關數據"""
        all_data = {
            'symbol': symbol,
            'market': market,
            'fetch_time': datetime.now().isoformat()
        }
        
        # 添加延遲避免過快請求
        delay = self.config['scraping']['delay_between_requests']
        
        # 獲取股票數據
        stock_data = self.fetch_stock_data(symbol, market)
        if stock_data:
            all_data['stock_data'] = stock_data
        time.sleep(delay)
        
        # 獲取法人數據
        institutional_data = self.fetch_institutional_data(symbol, market)
        if institutional_data:
            all_data['institutional_data'] = institutional_data
        time.sleep(delay)
        
        # 獲取新聞數據
        news_data = self.fetch_news_data(symbol, market)
        if news_data:
            all_data['news_data'] = news_data
        time.sleep(delay)
        
        # 獲取融資融券數據
        margin_data = self.fetch_margin_data(symbol, market)
        if margin_data:
            all_data['margin_data'] = margin_data
        
        return all_data
    
    def fetch_margin_data(self, symbol, market='taiwan'):
        """獲取融資融券數據"""
        try:
            if market != 'taiwan':
                return None
                
            # 嘗試獲取最近幾個交易日的融資融券數據
            today = datetime.now()
            
            for i in range(7):  # 最多往前找7天
                check_date = (today - timedelta(days=i)).strftime('%Y%m%d')
                
                url = "https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN"
                params = {
                    'response': 'json',
                    'date': check_date,
                    'selectType': 'ALL'  # 所有股票資料
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=self.config['scraping']['request_timeout'])
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'tables' in data and data['tables']:
                            # 解析tables結構的數據
                            for table in data['tables']:
                                if 'data' in table and table['data']:
                                    for row in table['data']:
                                        if len(row) > 0 and row[0] == symbol:
                                            # 成功找到數據
                                            margin_data = {
                                                'symbol': symbol,
                                                'name': row[1] if len(row) > 1 else '',  # 公司名稱
                                                'date': check_date,
                                                'margin_buy': self._safe_convert_to_float(row[2]) if len(row) > 2 else 0,  # 融資買進
                                                'margin_sell': self._safe_convert_to_float(row[3]) if len(row) > 3 else 0, # 融資賣出  
                                                'margin_net': self._safe_convert_to_float(row[4]) if len(row) > 4 else 0,  # 融資淨額
                                                'margin_balance': self._safe_convert_to_float(row[5]) if len(row) > 5 else 0, # 融資餘額
                                                'short_sell': self._safe_convert_to_float(row[8]) if len(row) > 8 else 0,  # 融券賣出
                                                'short_buy': self._safe_convert_to_float(row[9]) if len(row) > 9 else 0,   # 融券買進
                                                'short_net': self._safe_convert_to_float(row[10]) if len(row) > 10 else 0,  # 融券淨額
                                                'short_balance': self._safe_convert_to_float(row[11]) if len(row) > 11 else 0, # 融券餘額
                                                'source': 'twse_margin',
                                                'timestamp': datetime.now().isoformat()
                                            }
                                            
                                            # 計算籌碼面指標
                                            margin_data['margin_ratio'] = self._calculate_margin_ratio(margin_data)
                                            margin_data['short_ratio'] = self._calculate_short_ratio(margin_data)
                                            margin_data['retail_sentiment'] = self._calculate_retail_sentiment(margin_data)
                                            
                                            return margin_data
                except:
                    continue
            
            # 無法獲取數據
            return None
            
        except Exception as e:
            self.logger.error(f"獲取融資融券數據失敗: {e}")
            return None
    
    def _calculate_margin_ratio(self, margin_data):
        """計算融資比率"""
        try:
            margin_balance = margin_data.get('margin_balance', 0)
            if margin_balance > 0:
                return round(margin_balance, 2)
            return 0
        except:
            return 0
    
    def _calculate_short_ratio(self, margin_data):
        """計算融券比率"""
        try:
            short_balance = margin_data.get('short_balance', 0)
            if short_balance > 0:
                return round(short_balance, 2)
            return 0
        except:
            return 0
    
    def _calculate_retail_sentiment(self, margin_data):
        """計算散戶情緒指標"""
        try:
            margin_net = margin_data.get('margin_net', 0)
            short_net = margin_data.get('short_net', 0)
            
            # 簡化的散戶情緒計算：融資增加表示樂觀，融券增加表示悲觀
            if margin_net > 0 and short_net <= 0:
                return "樂觀"
            elif margin_net <= 0 and short_net > 0:
                return "悲觀" 
            elif margin_net > 0 and short_net > 0:
                return "混合"
            else:
                return "中性"
        except:
            return "中性"
    
    def fetch_institutional_recommendations(self, top_count=10):
        """動態獲取法人投資動向最強的股票推薦"""
        try:
            print("📊 正在動態掃描全市場法人投資動向...")
            
            # 直接從證交所API獲取所有股票的法人買賣超數據
            today = datetime.now()
            
            # 嘗試最近幾個交易日的數據
            for i in range(7):
                check_date = (today - timedelta(days=i)).strftime('%Y%m%d')
                
                url = "https://www.twse.com.tw/rwd/zh/fund/T86"
                params = {
                    'response': 'json',
                    'date': check_date,
                    'selectType': 'ALLBUT0999'
                }
                
                try:
                    response = self.session.get(url, params=params, timeout=self.config['scraping']['request_timeout'])
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'data' in data and data['data']:
                            recommendations = []
                            
                            # 處理所有股票數據
                            for row in data['data']:
                                if len(row) >= 14:  # 確保數據完整
                                    try:
                                        symbol = row[0]
                                        name = row[1]
                                        
                                        # 提取法人數據
                                        foreign_net = self._safe_convert_to_float(row[4])
                                        trust_net = self._safe_convert_to_float(row[7]) 
                                        dealer_net = self._safe_convert_to_float(row[10])
                                        total_net = self._safe_convert_to_float(row[13])
                                        
                                        # 計算推薦分數
                                        score = (foreign_net * 0.6) + (trust_net * 0.3) + (dealer_net * 0.1)
                                        
                                        # 額外加分條件
                                        if foreign_net > 0 and trust_net > 0:
                                            score += 500
                                        elif foreign_net > 1000:
                                            score += 300
                                        elif trust_net > 500:
                                            score += 200
                                        
                                        recommendation = {
                                            'symbol': symbol,
                                            'name': name,
                                            'foreign_net': foreign_net,
                                            'investment_trust_net': trust_net,
                                            'dealer_net': dealer_net,
                                            'total_net': total_net,
                                            'recommendation_score': round(score, 2),
                                            'date': check_date,
                                            'timestamp': datetime.now().isoformat(),
                                            'source': 'twse_dynamic'
                                        }
                                        
                                        recommendations.append(recommendation)
                                        
                                    except Exception as e:
                                        continue
                            
                            # 按推薦分數排序，取前N名
                            recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
                            
                            print(f"✅ 成功掃描 {len(recommendations)} 支股票，找出法人最愛前{top_count}名")
                            return recommendations[:top_count]
                
                except Exception as e:
                    continue
            
            # 如果都無法獲取，返回空數據
            print("❌ 無法獲取動態法人數據")
            return []
            
        except Exception as e:
            self.logger.error(f"動態獲取法人推薦失敗: {e}")
            return []
    
    def _calculate_recommendation_score(self, institutional_data):
        """計算推薦分數"""
        try:
            foreign_net = float(institutional_data.get('foreign_net', 0))
            trust_net = float(institutional_data.get('investment_trust_net', 0))
            dealer_net = float(institutional_data.get('dealer_net', 0))
            
            # 權重設定: 外資>投信>自營商
            score = (foreign_net * 0.6) + (trust_net * 0.3) + (dealer_net * 0.1)
            
            # 額外加分項目
            if foreign_net > 0 and trust_net > 0:  # 外資投信雙買超
                score += 500
            elif foreign_net > 1000:  # 外資大買超
                score += 300
            elif trust_net > 500:  # 投信大買超
                score += 200
            
            return round(score, 2)
            
        except (ValueError, TypeError):
            return 0
    

def test_data_fetcher():
    """測試數據獲取器"""
    fetcher = DataFetcher()
    
    # 測試台股
    print("測試台積電數據獲取:")
    data = fetcher.fetch_all_data('2330', 'taiwan')
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # 測試美股
    print("測試蘋果股票數據獲取:")
    data = fetcher.fetch_all_data('AAPL', 'us')
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_data_fetcher()