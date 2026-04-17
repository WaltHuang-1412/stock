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

同時抓取 industry_signals.json（結構化產業信號，動態補充 industry_chains.json）：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/industry_signals.json --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/industry_signals.json
```

如果指令失敗（檔案不存在或網路問題），跳過即可，不影響後續流程。
讀取後在 Step 2 和 Step 6 參考這些資料，識別額外的產業催化劑和時事題材。

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

結構化產業信號（Step 6 產業展開時使用）：
讀取 `industry_signals.json`，這是 topic_tracker.md 的結構化版本，每個催化劑主題已拆解為可直接使用的欄位：

Step 6 產業展開補強：
- `industry_chain_key` 非 null → 直接對應 `industry_chains.json` 的產業 key，用 catalyst_level 決定展開深度：
  - 🔴 超強 → depth 3（tier 0-3 全展開）
  - 🟡 強 → depth 2（tier 0-2）
  - 🟢 中度 → depth 1（tier 0-1）
- `industry_chain_key` 為 null → 新產業（industry_chains.json 沒有），直接用 `stocks[]` 作為候選股
- `stocks[]` 中出現但不在 industry_chains.json 的股票 → 新股票，納入候選池

Step 7 方向與營收驗證加減分：
- `direction.arrow` 為 ↑（加速）且候選股在該主題中 → **+3 分**（reason 標註「催化↑加速→+3」）
- `direction.arrow` 為 ↓（減速）且候選股在該主題中 → **-3 分**（reason 標註「催化↓減速→-3」）
- `revenue_support` 為 ⚠️ → 等同「催化x營收⚠️未跟上→-3」（與既有規則合併，不重複扣分）
- 方向加減分和時事維度加分可疊加，但時事維度總計不超過 30 分上限

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

催化劑x營收交叉分析（Step 7 評分時使用）：
讀取 `market_intelligence.md` 中的「催化劑 x 營收交叉分析」區塊：
- ⚠️ 營收未跟上的產業 → 該產業候選股 **-3分**（題材炒作無基本面支撐）
- 💪 強力支撐的產業 → 標註參考（不額外加分，營收加分已在 check_revenue_yoy.py 處理）
- reason 欄標註（如「催化x營收⚠️未跟上→-3」）

PTT 散戶輿情（Step 7 評分時參考）：
讀取 `market_intelligence.md` 中的「PTT 股票板散戶輿情」區塊：
- PTT 熱門討論的個股 → 標註「散戶關注」，不自動扣分但提高警覺
- 如果候選股同時出現在 PTT 熱門 + 今日漲幅已 >3% → **-3分**（散戶追高風險）
- reason 欄標註（如「PTT熱門+已漲→-3」）

美股財報日曆（Step 7 評分時使用）：
加減分規則見 CLAUDE.md「美股財報日曆加分」段落。reason 欄標註（如「TSM法說4/16→+5」）。

法人模式追蹤（Step 5 完成後、Step 7 之前執行）：
先執行模式追蹤器更新：
```bash
python3 scripts/institutional_pattern_tracker.py
```
加減分規則見 CLAUDE.md「法人模式追蹤加減分」段落。

大盤局勢（Step 7 和 Step 9 使用）：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/market_regime.json --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/market_regime.json
```
讀取 regime 欄位判斷大盤狀態，影響 Step 9 防禦比例。如果抓取失敗，跳過即可。

價格位置判斷（Step 7 評分時強制執行）：
Step 7 開始前，對全部候選股執行：
```bash
python3 scripts/check_price_position.py [全部候選股代碼...]
```
加減分規則見 CLAUDE.md「價格位置加減分」段落。reason 欄標註（如「52週位置94%極高→-5」）。

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

LINE 摘要格式（before_market_line.txt，≤5000字元）：
```
📊 盤前分析 MM/DD（v8.0）

🌐 大盤局勢：{regime}（score={score}）防禦{defense_ratio}
VIX {vix} | 台股vs年線{vs_ma240}%

🌐 國際市場
[費半/NASDAQ/VIX/油價/關鍵個股漲跌]

🚨 龍頭預警
[L1/L2/L3 列表]

📊 催化劑
[超強/強/中度 主題列表]

⚠️ 催化x營收警告（如有）
[⚠️營收未跟上的產業]

💬 PTT 散戶輿情（如有熱門個股）
[熱門討論的股票]

📈 結算 + 準確率

🔍 Module A/B

📋 推薦N檔
每檔格式：
  代碼名稱 分數⭐ 倉位
  推{price} 目標{target} 停損{stop_loss}(-10%) Day{N}/10
  [reason 含營收/持股比/月線/模式追蹤/財報日曆]

⚠️ 風險提示
產業分散
```

注意：
- 大盤局勢放最前面（不是最後面）
- 每檔停損後面標百分比（如「停損79.2(-10%)」）
- 每檔標 Day{N}/10（如「Day6/10」讓使用者知道還剩幾天）
- 催化x營收有⚠️的產業要獨立列出
- PTT 有熱門個股才列，沒有就省略

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py before_market $(date +%Y-%m-%d)`，通過才能 git commit + git push。驗證失敗必須修正報告後重跑
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
