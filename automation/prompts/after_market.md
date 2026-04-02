執行盤後分析。

完整按照 CLAUDE.md 盤後流程（Step 0 到 Step 6）執行，不得跳過任何步驟。

營收與外資持股比檢查（Step 5 明日預測評分時強制執行）：
明日推薦候選股評分前，必須執行：
```bash
python3 scripts/check_revenue_yoy.py [明日候選股代碼...]
python3 scripts/check_foreign_ratio.py [明日候選股代碼...]
```
讀取輸出的「評分建議」欄，逐檔套用加減分。推薦 reason 和 LINE 摘要必須標註。

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py after_market $(date +%Y-%m-%d)`，通過才能 git commit + git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
