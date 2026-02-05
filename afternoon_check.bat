@echo off
chcp 65001 >nul
echo ============================================================
echo 盤後檢查系統 v1.0
echo 執行時間: %date% %time%
echo ============================================================
echo.

cd /d "C:\Users\walter.huang\Documents\github\stock"

echo [1/3] 檢查今日法人反轉預警（關鍵！）...
echo.
python scripts/reversal_alert.py
echo.

echo [2/3] 查詢今日法人數據（主要持股）...
echo.
for /f "tokens=1-3 delims=/" %%a in ("%date%") do set TODAY=%%a%%b%%c
python scripts/check_institutional.py 2344 %TODAY%
python scripts/check_institutional.py 3481 %TODAY%
python scripts/check_institutional.py 1303 %TODAY%
python scripts/check_institutional.py 2886 %TODAY%
python scripts/check_institutional.py 3231 %TODAY%
echo.

echo [3/3] 籌碼動能分析...
echo.
python scripts/chip_analysis.py 2344 3481 1303 --days 10
echo.

echo ============================================================
echo 盤後檢查完成！
echo.
echo 如果出現 Level 2-4 反轉警示 → 明日開盤考慮出場
echo ============================================================
echo.
pause
