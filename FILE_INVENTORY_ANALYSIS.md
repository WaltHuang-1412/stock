# 台股系統檔案清單分析報告
**生成時間**：2025-11-28
**總檔案數**：221個檔案

## 📊 檔案統計概覽

### 檔案類型分布
- **Python檔案**：~30個
- **Markdown文檔**：~120個
- **JSON數據檔**：~50個
- **YAML配置檔**：4個

### 目錄結構
```
stock/
├── 根目錄檔案（核心工具）
├── src/（主要程式碼）
├── data/（分析報告+追蹤數據）
├── docs/（規範文檔）
├── templates/（範本檔案）
├── scripts/（輔助腳本）
├── automation/（自動化）
└── portfolio/（持股管理）
```

---

## 🔥 **核心工具（使用中）**

### **🎯 主要指令檔案**（6個可執行檔）
| 檔案 | 用途 | 狀態 | 執行方式 |
|------|------|------|----------|
| **check_institutional.py** | 🔥 法人數據查詢核心 | ✅ 每日使用 | `python3 check_institutional.py 2330 20251127` |
| **intraday_scanner.py** | 盤中量能掃描器（舊版） | ⚠️ 備用 | `python3 intraday_scanner.py` |
| **intraday_analyzer_v2.py** | 🆕 盤中五維度分析器 | ✅ 推薦使用 | `python3 intraday_analyzer_v2.py` |
| **scripts/stock_tracker.py** | 🆕 個股追蹤系統 | ✅ 盤後執行 | `python3 scripts/stock_tracker.py` |
| automation/run_before_market.py | 盤前自動化（規劃） | ❌ 未使用 | `python3 automation/run_before_market.py` |
| automation/scheduler.py | 排程系統（規劃） | ❌ 未使用 | `python3 automation/scheduler.py` |

### **📋 核心規範檔案**
| 檔案 | 用途 | 重要度 | 最後更新 |
|------|------|--------|----------|
| **CLAUDE.md** | 🔥 主規範文檔 | ⭐⭐⭐⭐⭐ | 2025-11-27 |
| **config.yaml** | 系統配置 | ⭐⭐⭐⭐ | 穩定 |
| **portfolio/my_holdings.yaml** | 持股配置 | ⭐⭐⭐⭐ | 每日更新 |

### **📊 追蹤數據檔案**（使用中）
| 檔案 | 用途 | 狀態 |
|------|------|------|
| data/tracking/tracking_2025-11-27.json | 11/27追蹤記錄 | ✅ 使用中 |
| **data/tracking/tracking_2025-11-28_CORRECTED.json** | 🔥 11/28修正版 | ✅ **最新使用** |
| data/tracking/tracking_2025-11-29.json | 11/29追蹤記錄 | ✅ 預建 |

---

## 📚 **src/目錄分析**（舊架構，部分棄用）

### **有價值但少用的檔案**
| 檔案 | 用途 | 狀態 | 建議 |
|------|------|------|------|
| src/main.py | 股票查詢入口 | 🟡 備用 | 保留，偶爾使用 |
| src/portfolio_analyzer.py | 持股分析 | 🟡 備用 | 整合到tracking系統 |
| src/data_fetcher.py | 數據獲取 | 🟡 備用 | 功能被check_institutional取代 |
| src/analyzer.py | 多維分析引擎 | 🟡 備用 | 核心邏輯保留 |

### **可考慮清理的檔案**
| 檔案 | 原因 | 建議 |
|------|------|------|
| src/examples.py | 範例代碼 | 移至archive/ |
| src/query_parser.py | 舊查詢解析 | 功能重複 |
| src/prediction_tracker.py | 被新tracking系統取代 | 檢查後移除 |
| src/daily_summary_generator.py | 舊格式產生器 | 功能重複 |

---

## 📖 **文檔系統分析**

### **🔥 必讀核心文檔**
| 檔案 | 用途 | 重要度 | 狀態 |
|------|------|--------|------|
| **CLAUDE.md** | 主規範（1200行） | ⭐⭐⭐⭐⭐ | 使用中 |
| docs/ANALYSIS_STANDARDS_V2.md | 完整分析規範 | ⭐⭐⭐⭐ | 使用中 |
| docs/FIVE_DIMENSIONS_SCORING.md | 五維度評分系統 | ⭐⭐⭐⭐ | 使用中 |

### **🆕 強化系統文檔**
| 檔案 | 用途 | 狀態 |
|------|------|------|
| docs/ENHANCED_ANALYSIS_SYSTEM_PLAN.md | 系統規劃 | ✅ 參考用 |
| docs/ENHANCED_SYSTEM_USAGE.md | 使用指南 | ✅ 參考用 |
| docs/PREDICTION_ACCURACY_TRACKING.md | 準確率追蹤 | ✅ 使用中 |

### **📋 輔助文檔**
| 檔案 | 用途 | 狀態 |
|------|------|------|
| docs/MARKET_NEWS_CHECKLIST.md | 時事檢查清單 | 🟡 偶爾用 |
| docs/DATA_VERIFICATION_PROTOCOL.md | 數據驗證協議 | 🟡 偶爾用 |
| docs/COMMAND_REFERENCE.md | 指令參考 | 🟡 偶爾用 |

### **🗂️ 過時文檔（可歸檔）**
| 檔案 | 原因 | 建議 |
|------|------|------|
| docs/archive/plans/*.md | 舊規劃文檔 | ✅ 已歸檔 |
| INTRADAY_SCANNER_README.md | 舊版說明 | 移至archive/ |
| CONVERSATION_START_CHECKLIST.md | 功能整合至CLAUDE.md | 移除重複 |

---

## 📁 **data/目錄分析**（221檔案中約180個）

### **🕒 歷史分析報告**（2025-09-24 ~ 2025-11-27）
**總數**：約150個分析報告檔案
- 每日3檔：before_market、intraday、after_market
- **近期使用**：2025-11-20 ~ 2025-11-27（16個檔案）
- **歷史檔案**：2025-09-24 ~ 2025-11-19（134個檔案）

### **📊 追蹤數據系統**（data/tracking/）
| 檔案 | 狀態 | 建議 |
|------|------|------|
| tracking_2025-11-21.json ~ tracking_2025-11-29.json | ✅ 使用中 | 保留 |
| tracking_2025-11-28_CORRECTED.json | 🔥 **主要使用** | 保留 |
| tracking_example.json | 範例檔案 | 保留 |
| READINESS_CHECK.md | 準備檢查 | 保留 |
| reports/ | 追蹤報告目錄 | 保留 |

### **📈 其他數據目錄**
| 目錄 | 用途 | 狀態 |
|------|------|------|
| data/weekly/ | 週報 | 🆕 準備中 |
| data/monthly/ | 月報 | 🆕 準備中 |
| data/backtest/ | 策略回測 | 🆕 規劃中 |
| data/predictions/ | 預測記錄 | 🟡 少用 |

---

## 📝 **templates/範本系統**

| 檔案 | 用途 | 狀態 | 使用頻率 |
|------|------|------|----------|
| before_market_template.md | 盤前分析範本 | ✅ 使用中 | 每日 |
| after_market_template.md | 盤後分析範本 | ✅ 使用中 | 每日 |
| weekly_report_template.md | 週報範本 | 🆕 新增 | 週五 |

---

## ⚙️ **automation/自動化系統**（未使用）

| 檔案 | 狀態 | 原因 |
|------|------|------|
| automation/scheduler.py | ❌ 未啟用 | 手動執行較靈活 |
| automation/run_before_market.py | ❌ 未啟用 | 功能重複 |
| automation/README.md | 📖 說明文檔 | 保留參考 |

---

## 🧹 **清理建議**

### **🔴 可以刪除**
1. **重複功能檔案**：
   - `src/daily_summary_generator.py` → 被tracking系統取代
   - `src/prediction_tracker.py` → 被新tracking系統取代
   - `CONVERSATION_START_CHECKLIST.md` → 功能整合至CLAUDE.md

2. **範例/測試檔案**：
   - `src/examples.py` → 移至archive/
   - `data/tracking/tracking_example.json` → 可保留作參考

### **🟡 可以歸檔**
1. **歷史分析報告**（2025-09-24 ~ 2025-11-15）：
   - 移至 `data/archive/2025-Q3/` 和 `data/archive/2025-Q4-early/`
   - 保留最近2週的分析（2025-11-15之後）

2. **舊版文檔**：
   - `INTRADAY_SCANNER_README.md` → `docs/archive/`

### **✅ 必須保留**
1. **核心工具**：check_institutional.py、intraday_analyzer_v2.py、stock_tracker.py
2. **主要規範**：CLAUDE.md、tracking數據、持股配置
3. **近期數據**：最近2週的分析報告
4. **範本檔案**：所有templates/

---

## 🎯 **每日使用指令清單**

### **盤前分析**（09:00前）
```bash
date "+%Y-%m-%d %A"  # 確認日期
python3 check_institutional.py 2330 20251127  # 查法人數據
```

### **盤中分析**（12:30）
```bash
python3 intraday_analyzer_v2.py  # 五維度分析
```

### **盤後分析**（14:30後）
```bash
python3 scripts/stock_tracker.py  # 更新追蹤數據
python3 check_institutional.py 2801 20251127  # 驗證法人數據
```

### **週報**（週五15:00後）
```bash
# 使用templates/weekly_report_template.md
```

---

## 📈 **系統健康度評估**

### **✅ 優勢**
- 核心工具穩定：check_institutional.py 100%可靠
- 追蹤系統完整：tracking + 修正機制運作正常
- 文檔系統完善：CLAUDE.md 規範明確
- 數據累積豐富：2個月完整分析記錄

### **⚠️ 需要改進**
- 檔案數量偏多：221個檔案（建議縮減至150個）
- 重複功能存在：舊版/新版工具並存
- 自動化未啟用：需要評估是否實施

### **🎯 優化建議**
1. **清理冗餘**：刪除重複功能檔案
2. **歸檔歷史**：移動舊分析報告
3. **文檔整合**：合併重複說明文檔
4. **功能評估**：決定automation是否啟用

---

**總結**：系統核心功能完整，但需要適度清理以提高維護效率。重點保留daily workflow所需的核心工具和最近數據。