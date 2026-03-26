執行盤中分析。

完整按照 CLAUDE.md 盤中流程（Step 0 到 Step 5）執行，不得跳過任何步驟。

重點（v7.8）：
1. Track A：追蹤盤前推薦股 + 出場訊號檢查（停損/連續重挫/法人反轉）
2. Track B（Step 3）：從法人 TOP50 篩出「買了但沒漲 <3%」的候選股
3. Track B（Step 3.5）🆕：對候選股跑完整五維度評分，產出最多 3 檔盤中新推薦
   - 必須執行 chip_analysis.py + reversal_alert.py
   - 門檻 ≥75 分、倉位 5-10%、停損 -5%
   - 無符合條件時標註「今日無盤中新推薦」
4. LINE 摘要必須包含 Track B 盤中新推薦的完整進場資訊（進場/目標/停損/倉位）

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py intraday $(date +%Y-%m-%d)`，通過才能 git commit + git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
