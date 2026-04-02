執行盤前分析。

完整按照 CLAUDE.md 盤前流程（Step 0 到 Step 10）執行，不得跳過任何步驟。

市場智能資料（Step 2 和 Step 6 時使用）：
在執行 Step 2（台股時事）前，先從 GitHub 抓取 market-intelligence 的今日資料：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/$(date +%Y-%m-%d)/raw_for_claude.md --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/market_intelligence.md
```

同時抓取 topic_tracker.md（催化劑追蹤儀表板，直接提供強度評級）：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/topic_tracker.md --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/topic_tracker.md
```

如果指令失敗（檔案不存在或網路問題），跳過即可，不影響後續流程。
讀取後在 Step 2 和 Step 6 參考這兩份資料，識別額外的產業催化劑和時事題材。

topic_tracker.md 催化劑儀表板使用方式：

儀表板已按強度分為四區，可直接對應 Step 7 時事維度加分：
- 🔴 超強催化劑（3週+）→ 時事維度 +15 分
- 🟡 強催化劑（1-2週）→ 時事維度 +10 分
- 🟢 中度催化劑 → 時事維度 +5 分
- ⚪ 觀察中 → 不加分
- 時事維度加分不超過 30 分上限

每個主題已包含結構化欄位，可直接使用：
- **台股影響鏈**：直接用於 Step 6 事件驅動選股的產業擴展
- **領頭指標**：用於 catalyst theme detector 的美股領頭羊驗證
- **關鍵轉折點**：用於 Step 5.5 催化預埋掃描的事件判斷
- **方向（↑→↓）**：判斷催化劑是加速還是減速，影響攻防比例

催化預埋掃描（Step 5.5 Module A，v7.9.3 新增）：
Step 5（法人TOP50）完成後，強制執行預埋掃描：
```bash
python3 scripts/catalyst_preposition_scan.py --date $(date +%Y-%m-%d) --lookback 7 --threshold 5
```
- L3（佈局完成）股票必須進入 Step 7 評分，即使不在 TOP20
- L2（早期佈局）股票進入候選池
- 追高排除的股票不進入評分（除非超強催化覆寫）

催化主題預警（Step 5.7 Module B，v7.9.3 新增）：
接著執行催化主題預警：
```bash
python3 scripts/catalyst_theme_detector.py --date $(date +%Y-%m-%d) --lookback 7
```
Module B 候選的後續處理（chip_analysis、reversal_alert、評分、排除原因）全部按照 CLAUDE.md Step 6「Module B 催化主題預警處理」段落執行，不得跳過。

營收與外資持股比檢查（Step 7 評分時強制執行）：
Step 7 開始前，必須對全部候選股（Step 5 + Step 6 合併後）執行以下兩個腳本：
```bash
python3 scripts/check_revenue_yoy.py [全部候選股代碼...]
python3 scripts/check_foreign_ratio.py [全部候選股代碼...]
```
讀取輸出的「評分建議」欄，逐檔套用加減分到 Step 7 評分中。
每檔推薦的 reason 欄必須標註營收/持股比調整（如「營收+43%→+5」或「持股比週減→-3」）。
LINE 摘要中每檔推薦也要帶入。
禁止用 Claude 自身知識代替腳本輸出，必須以腳本 JSON 結果為準。

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py before_market $(date +%Y-%m-%d)`，通過才能 git commit + git push。驗證失敗必須修正報告後重跑
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
