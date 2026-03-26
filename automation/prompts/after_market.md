執行盤後分析。

完整按照 CLAUDE.md 盤後流程（Step 0 到 Step 6）執行，不得跳過任何步驟。

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py after_market $(date +%Y-%m-%d)`，通過才能 git commit + git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
