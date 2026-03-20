執行盤前分析。

完整按照 CLAUDE.md 盤前流程（Step 0 到 Step 10）執行，不得跳過任何步驟。

市場智能資料（Step 2 和 Step 6 時使用）：
在執行 Step 2（台股時事）前，先從 GitHub 抓取 market-intelligence 的今日資料：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/$(date +%Y-%m-%d)/raw_for_claude.md --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/market_intelligence.md
```

同時抓取 topic_tracker.md（主題追蹤總表，提供多週累積脈絡）：
```bash
gh api repos/WaltHuang-1412/market-intelligence/contents/outputs/topic_tracker.md --jq '.content' | base64 -d > data/$(date +%Y-%m-%d)/topic_tracker.md
```

如果指令失敗（檔案不存在或網路問題），跳過即可，不影響後續流程。
讀取後在 Step 2 和 Step 6 參考這兩份資料，識別額外的產業催化劑和時事題材。

topic_tracker.md 的使用方式：
- 識別持續多週的主題（如記憶體連3週利多），在 Step 7 五維度評分時給予時事維度加分
- 超強催化（3週+持續利多）：時事維度+15分
- 強催化（1-2週持續利多）：時事維度+10分
- 中催化（有累積但未加速）：時事維度+5分
- 時事維度加分不超過30分上限

催化預埋掃描（Step 5.5，v7.9.3 新增）：
Step 5（法人TOP50）完成後，強制執行預埋掃描：
```bash
python3 scripts/catalyst_preposition_scan.py --date $(date +%Y-%m-%d) --lookback 7 --threshold 5
```
- 掃描結果的 L3（佈局完成）股票必須進入 Step 7 評分，即使不在 TOP20
- L2（早期佈局）股票進入候選池
- 追高排除的股票不進入評分（除非超強催化覆寫）
- 掃描結果寫入分析報告「催化預埋掃描」段落

自動化注意事項：
1. 今天日期用系統日期
2. 完成後 git add 相關檔案並 git commit，然後 git push
3. 禁止修改 scripts/ 目錄下的任何 .py 檔案，只能執行不能改
4. 禁止呼叫 notify_line.py（LINE 推送由排程腳本統一處理）
