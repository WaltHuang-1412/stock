#!/usr/bin/env python3
"""
查詢個股法人買賣超
直接查證交所API，不依賴TOP50篩選
"""

import requests
import sys
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def fetch_institutional_trading(stock_code, date=None):
    """
    查詢個股法人買賣超
    
    Args:
        stock_code: 股票代號，例如 '2208'
        date: 日期，格式 'YYYYMMDD'，預設為最近交易日
    """
    if not date:
        # 預設查詢昨天
        date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    # 試試英文版API
    url = f'https://www.twse.com.tw/rwd/en/fund/T86?date={date}&selectType=ALL&response=json'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.twse.com.tw/',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and data['data']:
                # 搜尋指定股票
                for row in data['data']:
                    if row[0] == stock_code:  # 第一欄是股票代號
                        print(f'\n📊 {row[1]}({stock_code}) {date[:4]}/{date[4:6]}/{date[6:8]} 法人買賣超')
                        print('=' * 70)
                        
                        # 解析數據（單位：股）
                        foreign_net = int(row[3].replace(',', ''))  # 外資買賣超（修正：row[3]不是row[4]）
                        trust_net = int(row[9].replace(',', ''))    # 投信買賣超
                        dealer_net = int(row[10].replace(',', ''))  # 自營商買賣超
                        total_net = int(row[17].replace(',', ''))   # 三大法人合計
                        
                        # 轉換成張（1張=1000股）
                        foreign_net_k = foreign_net / 1000
                        trust_net_k = trust_net / 1000
                        dealer_net_k = dealer_net / 1000
                        total_net_k = total_net / 1000
                        
                        # 顯示結果
                        foreign_status = '🔴賣超' if foreign_net < 0 else '🟢買超' if foreign_net > 0 else '➖持平'
                        trust_status = '🔴賣超' if trust_net < 0 else '🟢買超' if trust_net > 0 else '➖持平'
                        dealer_status = '🔴賣超' if dealer_net < 0 else '🟢買超' if dealer_net > 0 else '➖持平'
                        total_status = '🔴賣超' if total_net < 0 else '🟢買超' if total_net > 0 else '➖持平'
                        
                        print(f'外資:     {foreign_net_k:>10,.0f} 張 {foreign_status}')
                        print(f'投信:     {trust_net_k:>10,.0f} 張 {trust_status}')
                        print(f'自營商:   {dealer_net_k:>10,.0f} 張 {dealer_status}')
                        print(f'三大法人: {total_net_k:>10,.0f} 張 {total_status}')
                        
                        return {
                            'foreign_net': foreign_net_k,
                            'trust_net': trust_net_k,
                            'dealer_net': dealer_net_k,
                            'total_net': total_net_k
                        }
                
                print(f'\n⚠️ {stock_code} 不在 {date} 法人買賣超名單中')
                print('可能原因: 當日無交易或買賣超量極小')
                return None
            else:
                print(f'\n❌ 無法取得 {date} 的法人數據')
                return None
        else:
            print(f'\n❌ 查詢失敗，HTTP狀態碼: {response.status_code}')
            return None
            
    except Exception as e:
        print(f'\n❌ 查詢錯誤: {e}')
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使用方式: python3 check_institutional.py <股票代號> [日期YYYYMMDD]')
        print('範例: python3 check_institutional.py 2208 20251001')
        sys.exit(1)
    
    stock_code = sys.argv[1]
    date = sys.argv[2] if len(sys.argv) > 2 else None
    
    fetch_institutional_trading(stock_code, date)
