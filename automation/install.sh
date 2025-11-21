#!/bin/bash
# 股票分析排程安裝腳本
# 使用方式：bash automation/install.sh

echo "=================================================="
echo "📅 股票分析排程安裝腳本"
echo "=================================================="
echo ""

# 檢查Python
echo "檢查Python環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到Python3，請先安裝Python"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"
echo ""

# 安裝schedule庫
echo "安裝Python schedule庫..."
pip3 install schedule --quiet
if [ $? -eq 0 ]; then
    echo "✅ schedule庫安裝成功"
else
    echo "❌ schedule庫安裝失敗"
    exit 1
fi
echo ""

# 創建logs目錄
echo "創建日誌目錄..."
mkdir -p logs
echo "✅ 日誌目錄：logs/"
echo ""

# 設定執行權限
echo "設定腳本執行權限..."
chmod +x automation/run_before_market.py
chmod +x automation/scheduler.py
echo "✅ 執行權限已設定"
echo ""

# 測試執行
echo "測試盤前數據查詢腳本..."
python3 automation/run_before_market.py
if [ $? -eq 0 ]; then
    echo "✅ 測試成功"
else
    echo "⚠️ 測試失敗，請檢查腳本"
fi
echo ""

echo "=================================================="
echo "✅ 安裝完成！"
echo "=================================================="
echo ""
echo "接下來請選擇啟動方式："
echo ""
echo "方式1（簡單）：Python排程（需保持Terminal開啟）"
echo "  執行：python3 automation/scheduler.py"
echo ""
echo "方式2（進階）：macOS launchd排程（開機自動啟動）"
echo "  請參考：automation/SCHEDULE_SETUP.md"
echo ""
echo "=================================================="
