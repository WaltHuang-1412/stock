#!/bin/bash

# Claude Code 自動分析排程安裝腳本
# 作者：Walter + Claude Code
# 日期：2025-11-28

echo "🚀 安裝 Claude Code 自動分析排程..."

# 檢查 Claude Code 是否安裝
if ! command -v claude &> /dev/null; then
    echo "❌ 錯誤：Claude Code 未安裝"
    echo "請先安裝 Claude Code: https://claude.ai/code"
    exit 1
fi

echo "✅ Claude Code 已安裝在: $(which claude)"

# 建立 logs 目錄
LOG_DIR="$PWD/logs"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "📁 建立 logs 目錄: $LOG_DIR"
fi

# 複製 plist 檔案到 LaunchAgents
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "📝 安裝排程檔案..."
cp automation/com.stock.before_market.plist "$LAUNCH_AGENTS_DIR/"
cp automation/com.stock.intraday.plist "$LAUNCH_AGENTS_DIR/"
cp automation/com.stock.after_market.plist "$LAUNCH_AGENTS_DIR/"

echo "✅ 排程檔案已複製到: $LAUNCH_AGENTS_DIR"

# 載入排程
echo "🔄 載入排程..."
launchctl load "$LAUNCH_AGENTS_DIR/com.stock.before_market.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.stock.intraday.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.stock.after_market.plist"

echo "✅ 排程載入完成"

# 檢查排程狀態
echo "📊 檢查排程狀態..."
echo "盤前分析:"
launchctl list | grep com.stock.before_market || echo "❌ 盤前分析排程未找到"

echo "盤中分析:"
launchctl list | grep com.stock.intraday || echo "❌ 盤中分析排程未找到"

echo "盤後分析:"
launchctl list | grep com.stock.after_market || echo "❌ 盤後分析排程未找到"

echo ""
echo "🎉 Claude Code 自動分析排程安裝完成！"
echo ""
echo "📅 排程時間："
echo "  🌅 盤前分析：週一至週五 08:30"
echo "  ☀️  盤中分析：週一至週五 12:30"
echo "  🌆 盤後分析：週一至週五 15:00"
echo ""
echo "📋 日誌位置：$LOG_DIR"
echo "🔧 管理指令："
echo "  檢查狀態：launchctl list | grep stock"
echo "  停止排程：launchctl unload ~/Library/LaunchAgents/com.stock.*.plist"
echo "  重新載入：launchctl load ~/Library/LaunchAgents/com.stock.*.plist"