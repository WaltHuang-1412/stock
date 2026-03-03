今天是台股休市日，僅執行美股快照（假日輕量模式）。

執行步驟：
1. 執行 scripts/fetch_us_asia_markets.py，儲存到 data/YYYY-MM-DD/us_asia_markets.json
2. 執行 scripts/us_leader_alert.py，儲存到 data/YYYY-MM-DD/us_leader_alerts.json
3. 讀取結果，產出一份簡短摘要 data/YYYY-MM-DD/holiday_snapshot.md，包含：
   - 美股四大指數（NASDAQ、S&P500、道瓊、費半）漲跌
   - 龍頭股漲跌（NVIDIA、Micron、Apple、AMD、Tesla）
   - 油價、金價
   - 龍頭預警等級（如有 Level 2-3 要特別標註）
   - 一句話總結：對台股開盤日的潛在影響
4. 產出 LINE 摘要 data/YYYY-MM-DD/holiday_line.txt，內容與上述摘要相同，純文字格式
5. 完成後 git add 相關檔案並 git commit，然後 git push

市場智能資料（補充分析用）：
執行步驟 1 前，先嘗試從 GitHub 抓取今日新聞資料：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/$(date +%Y-%m-%d)/raw_for_claude.md --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/market_intelligence.md
```
如果成功，在步驟 3 產出摘要時參考這份資料，讓假日快照更完整。
如果失敗，跳過即可。

注意事項：
- 今天日期用系統日期
- 不需要執行台股相關腳本（休市無數據）
- 不需要推薦股票
- 快速完成即可（目標 5 分鐘內）
