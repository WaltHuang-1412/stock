#!/bin/bash

# 完整盤中分析執行腳本
# 用於產生與手動執行相同品質的分析報告

cd /Users/walter/Documents/GitHub/stock

# 設定環境變數
export PATH="/Users/walter/.nvm/versions/node/v20.11.1/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="/Users/walter"

# 執行完整盤中分析
/opt/homebrew/bin/claude --print --dangerously-skip-permissions "$(cat automation/intraday_prompt.txt)"