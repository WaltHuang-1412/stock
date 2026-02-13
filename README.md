# 台股智能分析系統 v7.3

基於真實法人數據的台股三階段分析系統，搭配 Claude Code 自動化排程，每日自動執行盤前/盤中/盤後分析。

## 核心特色

- **三階段自動分析** — 盤前(08:30) / 盤中(12:30) / 盤後(14:30) 自動排程執行
- **雙軌並行篩選** — 法人籌碼(A組) + 時事催化劑(B組) 雙重確認
- **美股龍頭預警** — NVIDIA/Micron/Apple 暴跌自動排除對應台股（一票否決）
- **法人反轉預警** — 偵測連續賣超、爆量出貨，強制排除風險股
- **假日輕量模式** — 台股休市日自動切換，只抓美股快照供開盤參考
- **動態產業分類** — 不硬編碼產業清單，新產業自動適應

## 快速開始

### 環境需求

- Python 3.9+
- Node.js（Claude Code）
- Windows 11

```bash
pip install -r requirements.txt
```

### 手動執行

```bash
# 進入 Claude Code 互動模式
claude --dangerously-skip-permissions

# 然後輸入：
# "執行盤前分析" / "執行盤中分析" / "執行盤後分析"
```

### 自動排程（推薦）

```powershell
# 以系統管理員身分開啟 PowerShell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
cd C:\Users\walter.huang\Documents\github\stock
.\automation\install_schedule.ps1

# 確認安裝
Get-ScheduledTask -TaskName "Stock_*"
```

安裝後每日自動執行：

| 排程 | 時間 | 交易日 | 休市日 |
|------|------|--------|--------|
| Stock_BeforeMarket | 08:30 | 完整盤前分析 (~25min) | 美股快照 (~2min) |
| Stock_Intraday | 12:30 | 完整盤中分析 | 跳過 |
| Stock_AfterMarket | 14:30 | 完整盤後分析 | 跳過 |

### 排程管理

```powershell
# 手動執行
Start-ScheduledTask -TaskName "Stock_BeforeMarket"

# 暫停所有排程
New-Item automation\PAUSED

# 恢復排程
Remove-Item automation\PAUSED

# 移除排程
.\automation\uninstall_schedule.ps1
```

## 目錄結構

```
stock/
├── CLAUDE.md                    # 分析流程規範 (v7.3)
├── automation/                  # 自動化排程系統
│   ├── scripts/                 #   PowerShell 排程腳本
│   ├── prompts/                 #   Claude Code prompt 檔案
│   ├── holidays.json            #   台股休市日行事曆（每年更新）
│   ├── install_schedule.ps1     #   安裝排程
│   └── uninstall_schedule.ps1   #   移除排程
├── scripts/                     # Python 分析工具
│   ├── fetch_us_asia_markets.py #   國際市場數據
│   ├── fetch_tw_market_news.py  #   台股時事數據
│   ├── us_leader_alert.py       #   美股龍頭預警
│   ├── fetch_institutional_top30.py # 法人 TOP50
│   ├── expand_industry.py       #   產業展開
│   ├── chip_analysis.py         #   籌碼分析
│   ├── reversal_alert.py        #   法人反轉預警
│   ├── merge_candidates.py      #   候選股合併
│   ├── validate_analysis.py     #   分析驗證（commit 前執行）
│   ├── my_holdings_analyzer.py  #   個人持股分析
│   └── stock_tracker.py         #   7日追蹤系統
├── data/                        # 每日分析數據
│   ├── YYYY-MM-DD/              #   每日報告 + JSON 數據
│   ├── tracking/                #   推薦追蹤記錄
│   └── predictions/             #   預測準確率記錄
├── portfolio/                   # 個人持股配置
│   └── my_holdings.yaml
├── docs/                        # 參考文件
└── notes/                       # 分析筆記
```

## 分析流程 (v7.3)

### 盤前分析（10 步驟）

```
Step 0:  建立追蹤清單
Step 1:  獲取國際市場數據（NASDAQ/費半/油價）
Step 1.5: 美股龍頭預警（NVIDIA/Micron/Apple 暴跌排除）
Step 2:  獲取台股時事數據
Step 3:  即時股價查詢
Step 4:  歷史驗證（昨日推薦表現）
Step 5:  法人 TOP50 掃描
Step 6:  雙軌並行候選股篩選（法人+時事）
Step 7:  五維度評分 + 反轉預警篩選
Step 8:  籌碼深度分析 + 反轉預警確認
Step 9:  產業分散檢查（6-8檔、≥3產業）
Step 10: 建檔 + git commit + push
```

### 五維度評分

| 維度 | 權重 |
|------|------|
| 時事現況 | 30% |
| 法人數據 | 30% |
| 產業邏輯 | 20% |
| 價格位置 | 10% |
| 技術面 | 10% |

推薦門檻：≥85分 強推 / 75-84分 推薦 / 65-74分 可考慮

## 假日行事曆

`automation/holidays.json` 包含台股休市日，每年 12 月台灣證交所公布次年行事曆後需更新。

休市日排程行為：
- 08:30 自動抓美股快照（指數 + 龍頭股 + 預警等級）
- 12:30 / 14:30 自動跳過

## 注意事項

- 所有數據來自證交所 API + Yahoo Finance，無模擬數據
- 分析完成後自動執行 `validate_analysis.py` 驗證
- 自動化過程禁止修改 `scripts/` 下的程式碼
- 進場必設停損，單檔不超過總資金 20%
- 本系統僅供研究參考，不構成投資建議

## 免責聲明

本軟體僅供教育和研究目的。所有分析結果僅供參考，使用者應自行承擔投資風險。

---

**版本**: v7.3 | **更新**: 2026-02-13 | **Python**: 3.9+ | **平台**: Windows 11
