#!/usr/bin/env python3
"""
股票分析排程腳本（簡單版）

使用Python schedule庫實現自動化排程

執行方式：
- python3 automation/scheduler.py

排程時間：
- 08:00 盤前數據查詢
- 12:30 盤中分析執行
"""

import schedule
import time
from datetime import datetime
import subprocess
import os

# 工作目錄
WORK_DIR = '/Users/walter/Documents/GitHub/stock'
os.chdir(WORK_DIR)

def log(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def run_before_market():
    """盤前數據查詢任務"""
    log("=" * 60)
    log("開始執行盤前數據查詢...")
    log("=" * 60)

    try:
        result = subprocess.run(
            ['python3', 'automation/run_before_market.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘timeout
        )

        # 輸出結果
        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            log("✅ 盤前數據查詢完成")
        else:
            log(f"❌ 盤前數據查詢失敗：{result.stderr}")

    except subprocess.TimeoutExpired:
        log("❌ 盤前數據查詢超時（超過5分鐘）")
    except Exception as e:
        log(f"❌ 盤前數據查詢錯誤：{e}")

    log("=" * 60)

def run_intraday():
    """盤中分析任務"""
    log("=" * 60)
    log("開始執行盤中分析...")
    log("=" * 60)

    try:
        result = subprocess.run(
            ['python3', 'intraday_analyzer_v2.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘timeout
        )

        # 輸出結果
        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            log("✅ 盤中分析完成")
        else:
            log(f"❌ 盤中分析失敗：{result.stderr}")

    except subprocess.TimeoutExpired:
        log("❌ 盤中分析超時（超過5分鐘）")
    except Exception as e:
        log(f"❌ 盤中分析錯誤：{e}")

    log("=" * 60)

def setup_schedule():
    """設定排程"""
    # 盤前數據查詢：每天早上08:00
    schedule.every().day.at("08:00").do(run_before_market)

    # 盤中分析：每天中午12:30
    schedule.every().day.at("12:30").do(run_intraday)

    log("📅 股票分析排程已啟動")
    log("")
    log("排程時間：")
    log("  - 08:00  盤前數據查詢（法人數據、美股收盤）")
    log("  - 12:30  盤中分析執行（intraday_analyzer_v2.py）")
    log("")
    log("提醒：")
    log("  - 排程只負責「數據查詢」和「提醒」")
    log("  - 實際「分析報告」需與Claude對話執行")
    log("  - 請保持此Terminal開啟")
    log("")
    log("按 Ctrl+C 停止排程")
    log("=" * 60)

def main():
    """主程式"""
    # 設定排程
    setup_schedule()

    # 測試：立即執行一次（可選）
    # run_before_market()

    # 持續運行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
    except KeyboardInterrupt:
        log("")
        log("=" * 60)
        log("📅 股票分析排程已停止")
        log("=" * 60)

if __name__ == '__main__':
    main()
