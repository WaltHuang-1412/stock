執行盤中分析。

完整按照 CLAUDE.md 盤中流程（Step 0 到 Step 5）執行，不得跳過任何步驟。

重點（v7.8）：
1. Track A：追蹤盤前推薦股 + 出場訊號檢查（停損/連續重挫/法人反轉）
2. Track B（Step 3 前）：先執行盤中法人續買偵測器
   ```bash
   python3 scripts/intraday_institutional_detector.py
   ```
   讀取 `data/YYYY-MM-DD/intraday_detector.json`，強訊號（≥60分）的股票**必須加入 Track B 候選池**
3. Track B（Step 3）：從法人 TOP50 篩出「買了但沒漲 <3%」的候選股 + 偵測器強訊號
4. Track B（Step 3.5）：對候選股跑完整五維度評分，產出最多 3 檔盤中新推薦
   - 必須執行 chip_analysis.py + reversal_alert.py
   - 偵測器強訊號股票評分時額外 +5 分（即時量價確認法人續買）
   - 門檻 ≥75 分、倉位 5-10%、停損 -5%
   - 無符合條件時標註「今日無盤中新推薦」
5. LINE 摘要必須包含 Track B 盤中新推薦的完整進場資訊（進場/目標/停損/倉位）

營收與外資持股比檢查（Track B Step 3.5 評分時強制執行）：
Track B 候選股評分前，必須執行：
```bash
python3 scripts/check_revenue_yoy.py [Track B 候選股代碼...]
python3 scripts/check_foreign_ratio.py [Track B 候選股代碼...]
```
讀取輸出的「評分建議」欄，逐檔套用加減分。推薦 reason 和 LINE 摘要必須標註。

v8.0 關鍵數值（強制遵守）：
- 盤前推薦停損 = **-10%**（不是 -8%），盤中推薦停損 = **-5%**
- 結算天數 = **10 個交易日**（不是 7 天）
- tracking.json 每檔必須有 `stop_loss_pct` 和 `settlement_days` 欄位
- `stop_loss` 必須從 `stop_loss_pct` 計算：`stop_loss = recommend_price × (1 + stop_loss_pct / 100)`
- 如果 Track A 持有股的 stop_loss 是舊的 -8% 算的，必須用 -10% 重算

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py intraday $(date +%Y-%m-%d)`，通過才能 git commit + git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
