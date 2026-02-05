@echo off
chcp 65001 >nul
echo ============================================================
echo 盤前檢查系統 v1.0
echo 執行時間: %date% %time%
echo ============================================================
echo.

cd /d "C:\Users\walter.huang\Documents\github\stock"

echo [1/3] 檢查持股法人反轉預警...
echo.
python scripts/reversal_alert.py
echo.

echo [2/3] 分析持股健康度...
echo.
python scripts/my_holdings_analyzer.py
echo.

echo [3/3] 查詢昨日法人數據（主要持股）...
echo.
python scripts/check_institutional.py 2344 %DATE:~0,4%%DATE:~5,2%%DATE:~8,2%
python scripts/check_institutional.py 3481 %DATE:~0,4%%DATE:~5,2%%DATE:~8,2%
python scripts/check_institutional.py 1303 %DATE:~0,4%%DATE:~5,2%%DATE:~8,2%
echo.

echo ============================================================
echo 盤前檢查完成！請根據以上資訊決定今日操作。
echo ============================================================
echo.
pause
