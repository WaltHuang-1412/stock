import re
import yaml
from datetime import datetime, timedelta

class QueryParser:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def parse_query(self, query):
        """解析用戶問題並提取關鍵信息"""
        query_info = {
            'stock_symbol': None,
            'stock_name': None,
            'analysis_type': [],
            'time_range': 'recent',
            'specific_request': query,
            'confidence': 0.0
        }
        
        # 提取股票代號或名稱
        stock_info = self._extract_stock_info(query)
        if stock_info:
            query_info.update(stock_info)
            query_info['confidence'] += 0.3
        
        # 分析請求類型
        analysis_types = self._identify_analysis_type(query)
        query_info['analysis_type'] = analysis_types
        if analysis_types:
            query_info['confidence'] += 0.4
        
        # 提取時間範圍
        time_range = self._extract_time_range(query)
        query_info['time_range'] = time_range
        query_info['confidence'] += 0.3
        
        return query_info
    
    def _extract_stock_info(self, query):
        """動態提取股票代號或名稱"""
        # 台股代號 (4位數字) - 直接支援
        tw_stock_pattern = r'(\d{4})'
        tw_match = re.search(tw_stock_pattern, query)
        if tw_match:
            symbol = tw_match.group(1)
            # 嘗試動態查詢公司名稱
            company_name = self._dynamic_lookup_company_name(symbol)
            return {
                'stock_symbol': symbol,
                'stock_name': company_name,
                'market': 'taiwan'
            }
        
        # 美股代號 (大寫字母)
        us_stock_pattern = r'([A-Z]{1,5})(?=[\s\u4e00-\u9fff]|$)'
        us_match = re.search(us_stock_pattern, query)
        if us_match:
            symbol = us_match.group(1)
            if symbol not in ['AND', 'THE', 'FOR', 'YOU', 'ARE', 'NOT', 'RSI', 'MACD', 'EPS']:
                return {
                    'stock_symbol': symbol,
                    'market': 'us'
                }
        
        # 公司名稱 - 嘗試動態查找
        company_symbol = self._dynamic_lookup_stock_symbol(query)
        if company_symbol:
            return company_symbol
        
        return None
    
    def _dynamic_lookup_company_name(self, symbol):
        """動態查詢股票代號對應的公司名稱"""
        try:
            import requests
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{symbol}.tw"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'msgArray' in data and data['msgArray']:
                    return data['msgArray'][0].get('n', symbol)  # 公司名稱
        except:
            pass
        return None
    
    def _dynamic_lookup_stock_symbol(self, query):
        """動態查詢公司名稱對應的股票代號"""
        try:
            # 從查詢中提取可能的公司名稱
            import requests
            
            # 嘗試從證交所搜尋 API
            # 這裡簡化實現，可以改用更完整的股票代碼查詢API
            possible_names = [
                query.replace('？', '').replace('?', '').strip(),
                query.replace('分析', '').replace('推薦', '').strip(),
            ]
            
            for name in possible_names:
                if len(name) >= 2:  # 至少2個字符的公司名稱
                    # 這裡可以實作更完整的動態查詢邏輯
                    # 暫時返回 None，讓系統知道需要代號
                    pass
            
        except:
            pass
        return None
    
    def _identify_analysis_type(self, query):
        """識別分析類型"""
        analysis_types = []
        
        # 股票推薦關鍵詞 (新增)
        recommendation_keywords = ['推薦', '進場', '買進', '投資', '選股', '標的', '可以買', '值得買', '建議買']
        if any(keyword in query for keyword in recommendation_keywords):
            analysis_types.append('recommendation')
        
        # 法人分析關鍵詞
        institutional_keywords = ['法人', '外資', '投信', '自營商', '三大法人', '買超', '賣超', '持股']
        if any(keyword in query for keyword in institutional_keywords):
            analysis_types.append('institutional')
        
        # 新聞分析關鍵詞
        news_keywords = ['新聞', '消息', '熱門', '話題', '討論', '最新']
        if any(keyword in query for keyword in news_keywords):
            analysis_types.append('news')
        
        # 技術分析關鍵詞
        technical_keywords = ['技術面', '走勢', '趨勢', '支撐', '壓力', '均線', '成交量', 'RSI', 'MACD']
        if any(keyword in query for keyword in technical_keywords):
            analysis_types.append('technical')
        
        # 基本面分析關鍵詞
        fundamental_keywords = ['基本面', '財報', '營收', '獲利', 'EPS', '本益比', '股利']
        if any(keyword in query for keyword in fundamental_keywords):
            analysis_types.append('fundamental')
        
        # 綜合分析關鍵詞
        general_keywords = ['分析', '看法', '建議', '評估', '怎麼看', '如何']
        if any(keyword in query for keyword in general_keywords) and not analysis_types:
            analysis_types = ['institutional', 'news', 'technical']
        
        return analysis_types if analysis_types else ['general']
    
    def _extract_time_range(self, query):
        """提取時間範圍"""
        # 具體時間關鍵詞
        time_patterns = {
            'today': ['今天', '今日'],
            'yesterday': ['昨天', '昨日'],
            'week': ['本週', '這週', '一週', '7天'],
            'month': ['本月', '這個月', '一個月', '30天'],
            'quarter': ['本季', '這季', '一季'],
            'year': ['今年', '一年']
        }
        
        for period, keywords in time_patterns.items():
            if any(keyword in query for keyword in keywords):
                return period
        
        # 數字+天數
        days_pattern = r'(\d+)天'
        days_match = re.search(days_pattern, query)
        if days_match:
            days = int(days_match.group(1))
            return f"{days}days"
        
        return 'recent'
    
    def validate_query(self, query_info):
        """驗證查詢是否有效"""
        # 推薦類型查詢不需要指定特定股票
        if 'recommendation' in query_info['analysis_type']:
            if not query_info['analysis_type']:
                return False, "無法識別分析類型"
            return True, "推薦查詢有效"
        
        # 其他類型需要指定股票
        if not query_info['stock_symbol'] and not query_info['stock_name']:
            return False, "請提供股票代號或名稱"
        
        if not query_info['analysis_type']:
            return False, "無法識別分析類型"
        
        if query_info['confidence'] < 0.5:
            return False, "查詢信心度過低，請提供更明確的資訊"
        
        return True, "查詢有效"

def test_query_parser():
    """測試查詢解析器"""
    parser = QueryParser()
    
    test_queries = [
        "台積電最近法人怎麼看？",
        "2330的新聞分析",
        "AAPL技術面分析",
        "鴻海這週的買賣超情況"
    ]
    
    for query in test_queries:
        print(f"\n查詢: {query}")
        result = parser.parse_query(query)
        is_valid, message = parser.validate_query(result)
        print(f"解析結果: {result}")
        print(f"有效性: {is_valid} - {message}")

if __name__ == "__main__":
    test_query_parser()