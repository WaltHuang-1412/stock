執行盤前分析。

> 🚫 **LINE 推送禁止事項（最優先讀取）**：**絕對不得呼叫 `scripts/notify_line.py`**，任何時間點、任何情況皆不得執行此腳本。LINE 推送由排程腳本在 Claude 執行完成後統一處理。若 Claude 也推送，使用者將收到重複通知。報告結論中也不得出現「LINE 通知已發送」等字樣。

**🛫 分析前強制執行 Pre-flight 自我檢查（不得跳過）：**
```bash
python3 scripts/preflight_check.py --fix
```
- ✅ 全部通過 → 繼續
- ⚠️ 警告 → 記錄後繼續，今日分析中必須處理警告項目
- ❌ 錯誤 → 必須修復後才能繼續（腳本已嘗試自動修復，確認修復結果）

完整按照 CLAUDE.md 盤前流程（Step 0 到 Step 10）執行，不得跳過任何步驟。

市場智能資料（Step 2 前抓取，失敗時跳過不影響後續）：
```bash
TODAY=$(date +%Y-%m-%d)

_mi=$(gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/${TODAY}/raw_for_claude.md --jq '.content' 2>/dev/null)
if echo "$_mi" | base64 -d > data/${TODAY}/market_intelligence.md 2>/dev/null && [ $(wc -c < data/${TODAY}/market_intelligence.md) -gt 500 ]; then
  echo "[OK] market_intelligence.md"
else
  rm -f data/${TODAY}/market_intelligence.md; echo "[SKIP] market_intelligence.md"
fi

_tt=$(gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/topic_tracker.md --jq '.content' 2>/dev/null)
if echo "$_tt" | base64 -d > data/${TODAY}/topic_tracker.md 2>/dev/null && [ $(wc -c < data/${TODAY}/topic_tracker.md) -gt 100 ]; then
  echo "[OK] topic_tracker.md"
else
  rm -f data/${TODAY}/topic_tracker.md; echo "[SKIP] topic_tracker.md"
fi

_is=$(gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/industry_signals.json --jq '.content' 2>/dev/null)
if echo "$_is" | base64 -d > data/${TODAY}/industry_signals.json 2>/dev/null && [ $(wc -c < data/${TODAY}/industry_signals.json) -gt 100 ]; then
  echo "[OK] industry_signals.json"
else
  rm -f data/${TODAY}/industry_signals.json; echo "[SKIP] industry_signals.json"
fi

gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/market_regime.json --jq '.content' | base64 -d > data/${TODAY}/market_regime.json 2>/dev/null || true
```

v8.0 關鍵數值（強制遵守）：
- 盤前推薦停損 = **-10%**，結算天數 = **10 個交易日**
- tracking.json 每檔必須有 `stop_loss_pct` 和 `settlement_days` 欄位
- `stop_loss` 必須從 `stop_loss_pct` 計算：`stop_loss = recommend_price × 0.90`

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

💬 PTT 散戶輿情（如有熱門個股）

📈 結算 + 準確率

🔍 Module A/B

📋 推薦N檔
每檔格式：
  代碼名稱 分數⭐ 倉位
  推{price} 目標{target} 停損{stop_loss}(-10%) Day{N}/10
  [reason 含營收/持股比/月線/模式追蹤/財報日曆]

⚠️ 風險提示 + 產業分散
```

注意：大盤局勢放最前面 | 停損標百分比（如「停損79.2(-10%)」）| 每檔標 Day{N}/10

自動化注意事項：
1. 今天日期用系統日期
2. commit 前必須先跑驗證：`python3 scripts/validate_analysis.py before_market $(date +%Y-%m-%d)`，通過才能 git commit。驗證失敗必須修正報告後重跑
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. git commit 完成後，執行 `git push`
5. 🚫 **絕對禁止執行 `scripts/notify_line.py`**（見文件最頂端說明）。違反此規則 = 使用者收到重複 LINE 通知
