"""
工具函數模組
包含各種輔助功能
"""

import re
import time
import requests
from datetime import datetime, timedelta
import logging
from functools import wraps
from typing import Dict, List, Optional, Any

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """重試裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logging.warning(f"重試 {func.__name__} (第 {attempt + 1} 次): {e}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logging.error(f"{func.__name__} 重試失敗: {e}")
            
            raise last_exception
        return wrapper
    return decorator

def validate_stock_symbol(symbol: str, market: str = 'taiwan') -> bool:
    """驗證股票代號格式"""
    if not symbol:
        return False
    
    if market == 'taiwan':
        # 台股代號：4位數字
        return bool(re.match(r'^\d{4}$', symbol))
    elif market == 'us':
        # 美股代號：1-5位大寫字母
        return bool(re.match(r'^[A-Z]{1,5}$', symbol))
    
    return False

def format_number(num: Any, decimal_places: int = 2) -> str:
    """格式化數字顯示"""
    try:
        if num is None or num == '':
            return 'N/A'
        
        num_float = float(num)
        
        if abs(num_float) >= 1e9:
            return f"{num_float/1e9:.{decimal_places}f}B"
        elif abs(num_float) >= 1e6:
            return f"{num_float/1e6:.{decimal_places}f}M"
        elif abs(num_float) >= 1e3:
            return f"{num_float/1e3:.{decimal_places}f}K"
        else:
            return f"{num_float:,.{decimal_places}f}"
    
    except (ValueError, TypeError):
        return str(num)

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """安全獲取字典值"""
    try:
        return dictionary.get(key, default)
    except AttributeError:
        return default

def clean_text(text: str) -> str:
    """清理文本，移除多餘空白和特殊字符"""
    if not text:
        return ""
    
    # 移除多餘空白
    text = re.sub(r'\s+', ' ', text)
    # 移除開頭結尾空白
    text = text.strip()
    # 移除特殊字符但保留中文、英文、數字和基本標點
    text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?()-]', '', text)
    
    return text

def parse_date(date_str: str) -> Optional[datetime]:
    """解析各種日期格式"""
    if not date_str:
        return None
    
    date_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y%m%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def get_trading_days_range(days: int = 30) -> List[str]:
    """獲取交易日範圍（排除周末）"""
    trading_days = []
    current_date = datetime.now()
    
    while len(trading_days) < days:
        # 排除周末 (0=Monday, 6=Sunday)
        if current_date.weekday() < 5:
            trading_days.append(current_date.strftime('%Y%m%d'))
        current_date -= timedelta(days=1)
    
    return trading_days

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """計算百分比變化"""
    try:
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    except (TypeError, ZeroDivisionError):
        return 0.0

def is_market_open(market: str = 'taiwan') -> bool:
    """檢查市場是否開盤"""
    now = datetime.now()
    
    if market == 'taiwan':
        # 台股交易時間：週一到週五 9:00-13:30
        if now.weekday() > 4:  # 周末
            return False
        
        market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=13, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    elif market == 'us':
        # 美股交易時間：週一到週五 9:30-16:00 (EST)
        # 這裡簡化處理，實際需要考慮時區轉換
        if now.weekday() > 4:  # 周末
            return False
        
        return True  # 簡化實現
    
    return False

def get_market_status(market: str = 'taiwan') -> str:
    """獲取市場狀態"""
    if is_market_open(market):
        return "開盤中"
    else:
        now = datetime.now()
        if now.weekday() > 4:
            return "週末休市"
        else:
            return "收盤"

def log_function_call(func):
    """函數調用日誌裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logging.info(f"{func.__name__} 執行成功 (耗時: {execution_time:.2f}s)")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"{func.__name__} 執行失敗 (耗時: {execution_time:.2f}s): {e}")
            raise
    
    return wrapper

def build_headers(user_agent: str = None) -> Dict[str, str]:
    """構建HTTP請求頭"""
    default_headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    return default_headers

def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """將列表分割為指定大小的塊"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def ensure_list(item: Any) -> List[Any]:
    """確保項目為列表格式"""
    if item is None:
        return []
    elif isinstance(item, list):
        return item
    else:
        return [item]

class RateLimiter:
    """速率限制器"""
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """檢查是否可以發起調用"""
        now = time.time()
        
        # 清理過期的調用記錄
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        return len(self.calls) < self.max_calls
    
    def make_call(self):
        """記錄一次調用"""
        if self.can_make_call():
            self.calls.append(time.time())
            return True
        return False
    
    def wait_time(self) -> float:
        """計算需要等待的時間"""
        if not self.calls:
            return 0.0
        
        oldest_call = min(self.calls)
        wait_time = self.time_window - (time.time() - oldest_call)
        return max(0.0, wait_time)

def test_utils():
    """測試工具函數"""
    print("測試工具函數:")
    
    # 測試股票代號驗證
    print(f"驗證台股代號 '2330': {validate_stock_symbol('2330', 'taiwan')}")
    print(f"驗證美股代號 'AAPL': {validate_stock_symbol('AAPL', 'us')}")
    
    # 測試數字格式化
    print(f"格式化大數字 1500000: {format_number(1500000)}")
    print(f"格式化小數字 123.45: {format_number(123.45)}")
    
    # 測試市場狀態
    print(f"台股市場狀態: {get_market_status('taiwan')}")
    
    # 測試速率限制器
    limiter = RateLimiter(max_calls=3, time_window=5)
    for i in range(5):
        if limiter.make_call():
            print(f"調用 {i+1}: 成功")
        else:
            print(f"調用 {i+1}: 被限制，需等待 {limiter.wait_time():.1f} 秒")

if __name__ == "__main__":
    test_utils()