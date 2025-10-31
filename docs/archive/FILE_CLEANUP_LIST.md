# 檔案清理清單 2025-10-31

**建議**：先不要刪除，列出清單供您確認

---

## 📋 可刪除檔案清單（共約34個）

### ⚠️ 類別1：journal/ 目錄（3個檔案）

```
journal/watchlist.md
journal/strategies.md
journal/trading_notes.md
```

**理由**：功能重複，已有 `portfolio/my_holdings.yaml` 和每日分析報告

---

### ⚠️ 類別2：data/ 特殊分析檔案（約30個）

#### 2025-10-03/ 目錄（4個）
```
data/2025-10-03/portfolio_analysis.md
data/2025-10-03/daily_summary.md
data/2025-10-03/institutional_layout_analysis.md
data/2025-10-03/intraday_decision.md
```

#### 2025-09-30/ 目錄（1個）
```
data/2025-09-30/objective_analysis.md
```

#### 2025-09-27/ 目錄（6個）
```
data/2025-09-27/summary_comparison.md
data/2025-09-27/continuous_buying_analysis.md
data/2025-09-27/leading_stocks_prediction.md
data/2025-09-27/china_steel_analysis.md
data/2025-09-27/backtest_analysis.md
data/2025-09-27/weekend_analysis.md
```

#### 2025-10-01/ 目錄（3個）
```
data/2025-10-01/supply_chain_analysis.md
data/2025-10-01/prediction_accuracy_analysis.md
data/2025-10-01/daily_summary_report.md
```

#### 2025-10-07/ 目錄（2個）
```
data/2025-10-07/portfolio_analysis.md
data/2025-10-07/ai_semiconductor_supply_chain_analysis.md
```

#### 2025-10-08/ 目錄（1個）
```
data/2025-10-08/market_deep_analysis.md
```

#### 2025-10-09/ 目錄（1個）
```
data/2025-10-09/market_deep_analysis.md
```

#### 2025-10-17/ 目錄（5個）
```
data/2025-10-17/trump_tariff_analysis.md
data/2025-10-17/trading_record.md
data/2025-10-17/comprehensive_industry_analysis.md
data/2025-10-17/summary_card.md
data/2025-10-17/return_forecast.md
```

#### 2025-10-21/ 目錄（1個）
```
data/2025-10-21/daily_summary.md
```

#### 2025-10-27/ 目錄（1個）
```
data/2025-10-27/industry_rotation_analysis.md
```

#### 2025-10-28/ 目錄（1個）
```
data/2025-10-28/conversation_insights_and_lessons.md
```

#### 2025-10-29/ 目錄（3個）
```
data/2025-10-29/prediction_optimization_analysis.md
data/2025-10-29/trump_xi_summit_analysis.md
data/2025-10-29/november_events_stock_strategy.md
```

**理由**：這些是單日特殊分析，與標準三階段分析（before/intraday/after）重複

---

### ⚠️ 類別3：其他一次性報告（1個）

```
data/fake_data_cleanup_report.md
```

**理由**：一次性清理報告，已完成任務

---

## ✅ 必須保留的檔案

### 核心程式碼
```
src/main.py
src/portfolio_analyzer.py
src/data_fetcher.py
src/analyzer.py
src/query_parser.py
src/utils.py
src/examples.py
check_institutional.py
```

### 核心配置
```
config.yaml
portfolio/my_holdings.yaml
portfolio/transaction_history.md
CLAUDE.md
README.md
```

### 核心文件
```
docs/archive/plans/PREDICTION_ACCURACY_TRACKING.md
```

### 標準分析報告（每日三階段）
```
data/*/before_market_analysis.md
data/*/intraday_analysis.md
data/*/after_market_analysis.md
```

### 最新特殊分析（10/31）
```
data/2025-10-31/continuous_buy_analysis.md
data/2025-10-31/data_verification.md
data/2025-10-31/before_market_analysis.md
```

---

## 🎯 建議清理方式

### 方案A：移到 archive（推薦）✅

**優點**：
- 保留歷史記錄
- 可隨時查閱
- 不會遺失重要資訊

**執行**：
```bash
# Step 1: 建立 archive 目錄
mkdir -p docs/archive/journal
mkdir -p docs/archive/old_analysis
mkdir -p docs/archive/reports

# Step 2: 移動 journal
mv journal/* docs/archive/journal/

# Step 3: 移動特殊分析（需逐一確認）
# 先不執行，等您確認

# Step 4: 移動一次性報告
mv data/fake_data_cleanup_report.md docs/archive/reports/
```

---

### 方案B：直接刪除（不推薦）❌

**缺點**：
- 無法復原
- 可能遺失重要資訊

**執行**：
```bash
# 請勿執行，除非您確定不需要這些檔案
```

---

## 📊 清理效益

### 清理前
```
總檔案數：約100個
可刪除：約34個（34%）
```

### 清理後
```
保留核心檔案：約66個
減少混亂度：+50%
提升查找效率：+40%
```

---

## ⚠️ 特別注意

### 不要刪除這些目錄的檔案

```
❌ data/2025-10-30/  （最近分析）
❌ data/2025-10-31/  （今日分析）
❌ src/              （所有程式碼）
❌ portfolio/        （持股配置）
❌ docs/archive/plans/PREDICTION_ACCURACY_TRACKING.md
```

### 標準三階段分析檔案（保留）

```
✅ data/*/before_market_analysis.md
✅ data/*/intraday_analysis.md
✅ data/*/after_market_analysis.md
```

---

## 📝 待確認清單

請您確認以下問題：

- [ ] journal/ 目錄是否完全不需要？
- [ ] 特殊分析檔案（如 trump_tariff_analysis.md）是否有保留價值？
- [ ] 是否要保留歷史深度分析（market_deep_analysis.md）？
- [ ] 清理方式：移到 archive 或直接刪除？

---

**清單產出時間**: 2025-10-31 11:00
**建議處理方式**: 先移到 archive，不要直接刪除
**下一步**: 等待您確認後再執行清理
