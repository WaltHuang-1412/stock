執行盤前分析。

完整按照 CLAUDE.md 盤前流程（Step 0 到 Step 10）執行，不得跳過任何步驟。

市場智能資料（Step 2 和 Step 6 時使用）：
在執行 Step 2（台股時事）前，先從 GitHub 抓取 market-intelligence 的今日資料：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/$(date +%Y-%m-%d)/raw_for_claude.md --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/market_intelligence.md
```
如果指令失敗（檔案不存在或網路問題），跳過即可，不影響後續流程。
讀取後在 Step 2 和 Step 6 參考這份資料，識別額外的產業催化劑和時事題材。

自動化注意事項：
1. 今天日期用系統日期
2. 完成後 git add 相關檔案並 git commit，然後 git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
