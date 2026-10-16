執行盤中分析。

> 🚫 **LINE 推送禁止事項（最優先讀取）**：**絕對不得呼叫 `scripts/notify_line.py`**，任何時間點、任何情況皆不得執行此腳本。LINE 推送由排程腳本在 Claude 執行完成後統一處理。若 Claude 也推送，使用者將收到重複通知。報告結論中也不得出現「LINE 通知已發送」等字樣。

**🛫 分析前強制執行 Pre-flight 自我檢查（不得跳過）：**
```bash
python3 scripts/preflight_check.py --mode intraday --fix
```
- ✅ 全部通過 → 繼續
- ⚠️ 警告 → 記錄後繼續，今日分析中必須處理警告項目
- ❌ 錯誤 → 必須修復後才能繼續（腳本已嘗試自動修復，確認修復結果）

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
6. 🟢 **LINE 必須含「📋 推薦股現況與原因」區塊（使用者 2026-10-12 要求，強制）**：
   列出當日盤前推薦 ＋ 仍在追蹤中（holding）的全部推薦股，每檔格式：
   `代號 名稱｜推薦價→現價（±%）｜距目標 x%／距停損 y%｜D{N}/10`
   `💡 當初為什麼推：1~2 句白話（法人做了什麼、對應哪個題材、股價位置）`
   `👉 現在怎麼辦：續抱／待複核／出場，並說明依據（用白話，不只寫 L4、鐵律①這類代號）`
   - 白話：禁止只丟 L0／動能-90% 等內部術語，要寫出意思（例：「法人沒有出貨跡象」）
   - 原因取自當日 tracking.json 該檔的 reason 與盤中最新籌碼，禁止編造
   - 有盤中新推薦（Track B）時，同樣附「為什麼推」與「要注意」
   - 整份 LINE ≤5000 字元；超過時先刪次要段落（偵測器、資料缺口），推薦與原因不得刪

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
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py intraday $(date +%Y-%m-%d)`，通過才能 git commit
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. git commit 完成後，執行 `git push`
5. 🚫 **絕對禁止執行 `scripts/notify_line.py`**（見文件最頂端說明）。違反此規則 = 使用者收到重複 LINE 通知
