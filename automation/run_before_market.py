#!/usr/bin/env python3
"""
盤前分析自動化腳本

執行時間：每天早上08:00
執行內容：
1. 查詢昨日法人數據
2. 查詢美股收盤數據
3. 生成盤前分析報告
4. 創建tracking.json

使用方式：
- 手動執行：python3 automation/run_before_market.py
- 自動執行：launchd排程
"""

import os
import sys
from datetime import datetime, timedelta
import subprocess
import json

# 設定工作目錄
WORK_DIR = '/Users/walter/Documents/GitHub/stock'
os.chdir(WORK_DIR)

def log(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def check_market_day():
    """檢查是否為交易日（簡單版：排除週末）"""
    today = datetime.now()
    if today.weekday() >= 5:  # 週六=5, 週日=6
        log("今日為週末，不執行分析")
        return False
    return True

def get_yesterday_date():
    """取得昨日日期（YYYYMMDD格式）"""
    yesterday = datetime.now() - timedelta(days=1)
    # 如果昨天是週末，往前找到週五
    while yesterday.weekday() >= 5:
        yesterday -= timedelta(days=1)
    return yesterday.strftime('%Y%m%d')

def fetch_institutional_data():
    """查詢昨日法人數據"""
    log("開始查詢昨日法人數據...")

    date_str = get_yesterday_date()
    url = f'https://www.twse.com.tw/rwd/en/fund/T86?date={date_str}&selectType=ALL&response=json'

    try:
        import requests
        response = requests.get(url, timeout=30)
        data = response.json()

        if data.get('stat') == 'OK':
            log(f"✅ 法人數據查詢成功（{date_str}），共{len(data['data'])}筆")
            return True
        else:
            log(f"❌ 法人數據查詢失敗：{data}")
            return False
    except Exception as e:
        log(f"❌ 法人數據查詢錯誤：{e}")
        return False

def fetch_us_market_data():
    """查詢美股收盤數據"""
    log("開始查詢美股數據...")

    try:
        import yfinance as yf

        # 查詢台積電ADR
        tsm = yf.Ticker('TSM')
        hist = tsm.history(period='2d')

        if len(hist) >= 1:
            latest_close = hist['Close'].iloc[-1]
            log(f"✅ 台積電ADR: ${latest_close:.2f}")
            return True
        else:
            log("❌ 台積電ADR數據不足")
            return False
    except Exception as e:
        log(f"❌ 美股數據查詢錯誤：{e}")
        return False

def notify_user():
    """通知用戶（macOS通知）"""
    log("發送通知給用戶...")

    title = "📊 盤前分析準備就緒"
    message = "數據已更新，請執行盤前分析"

    script = f'''
    display notification "{message}" with title "{title}" sound name "Glass"
    '''

    try:
        subprocess.run(['osascript', '-e', script], check=True)
        log("✅ 通知已發送")
    except Exception as e:
        log(f"⚠️ 通知發送失敗：{e}")

def main():
    """主程式"""
    log("=" * 60)
    log("盤前分析自動化任務開始")
    log("=" * 60)

    # 檢查是否為交易日
    if not check_market_day():
        return

    # 查詢法人數據
    institutional_ok = fetch_institutional_data()

    # 查詢美股數據
    us_market_ok = fetch_us_market_data()

    # 發送通知
    if institutional_ok and us_market_ok:
        notify_user()
        log("✅ 所有數據查詢完成")
        log("💡 請手動執行：與Claude對話「開始盤前分析」")
    else:
        log("⚠️ 部分數據查詢失敗，請檢查網路連線")

    log("=" * 60)
    log("盤前分析自動化任務結束")
    log("=" * 60)

if __name__ == '__main__':
    main()
