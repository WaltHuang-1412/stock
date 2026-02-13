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
4. 完成後 git add 相關檔案並 git commit，然後 git push

注意事項：
- 今天日期用系統日期
- 不需要執行台股相關腳本（休市無數據）
- 不需要推薦股票
- 快速完成即可（目標 5 分鐘內）
