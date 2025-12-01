#!/bin/bash

# 直接執行盤中分析，不依賴 Claude Code
# 這樣能確保與手動執行完全相同

cd /Users/walter/Documents/GitHub/stock

# 設定環境變數
export PATH="/Users/walter/.nvm/versions/node/v20.11.1/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="/Users/walter"

# 直接執行 Python 腳本
python3 scripts/intraday_analyzer_v2.py

echo "盤中分析完成：$(date)"