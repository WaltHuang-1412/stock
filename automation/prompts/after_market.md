執行盤後分析。

完整按照 CLAUDE.md 盤後流程（Step 0 到 Step 6）執行，不得跳過任何步驟。

營收與外資持股比檢查（Step 5 明日預測評分時強制執行）：
明日推薦候選股評分前，必須執行：
```bash
python3 scripts/check_revenue_yoy.py [明日候選股代碼...]
python3 scripts/check_foreign_ratio.py [明日候選股代碼...]
```
讀取輸出的「評分建議」欄，逐檔套用加減分。推薦 reason 和 LINE 摘要必須標註。

v8.0 關鍵數值（強制遵守）：
- 盤前推薦停損 = **-10%**（不是 -8%），盤中推薦停損 = **-5%**
- 結算天數 = **10 個交易日**（不是 7 天）
- 明日推薦的 stop_loss 必須用 -10% 計算：`stop_loss = recommend_price × 0.90`
- tracking.json 每檔必須有 `stop_loss_pct` 和 `settlement_days` 欄位

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py after_market $(date +%Y-%m-%d)`，通過才能 git commit + git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. git commit + git push 完成後，必須執行 `python3 scripts/notify_line.py --file data/$(date +%Y-%m-%d)/after_market_line.txt` 推送 LINE
