# 市場重大時事強制檢查清單

**用途**：每次盤前/盤中/盤後分析必須執行，確保不遺漏任何重大時事

**教訓**：2025/11/20盤前分析遺漏輝達財報，導致分析不完整

---

## 🚨 強制執行時機

**任何分析前必須完成**：
- ✅ 盤前分析（09:00前）
- ✅ 盤中分析（12:30）
- ✅ 盤後分析（14:30後）

---

## 📋 時事檢查清單（按優先級）

### 🔥 第一優先：美股重大事件

**必查項目**（WebSearch）：
1. **科技巨頭財報**
   ```
   查詢：NVIDIA earnings, TSMC earnings, Apple earnings, Microsoft earnings
   時間：財報季（1月、4月、7月、10月後2週）
   影響：台積電、鴻海、日月光、南亞科
   ```

2. **Fed利率決議**
   ```
   查詢：Fed interest rate decision, FOMC meeting
   時間：每6週（約2個月1次）
   影響：全市場、金融股
   ```

3. **重大經濟數據**
   ```
   查詢：US CPI, US jobs report, US GDP
   時間：每月第一週（CPI、非農）
   影響：台股開盤方向
   ```

4. **費城半導體指數異動**
   ```
   查詢：SOX index, semiconductor stocks
   條件：單日漲跌>3%
   影響：台積電、聯電、聯發科、南亞科
   ```

---

### ⚡ 第二優先：台股重大事件

**必查項目**（WebSearch）：
1. **台積電法說會**
   ```
   查詢：TSMC earnings call, 台積電法說會
   時間：每季財報後（1月、4月、7月、10月）
   影響：全台股（權重30%）
   ```

2. **產業重大新聞**
   ```
   查詢：Taiwan semiconductor news, AI chip orders
   時間：每日
   影響：半導體、AI供應鏈
   ```

3. **地緣政治**
   ```
   查詢：Taiwan strait, US-China tech war
   條件：有重大事件
   影響：全市場
   ```

---

### 📊 第三優先：個股重大事件

**必查項目**（WebSearch）：
1. **持股公司法說會**
   ```
   查詢：[公司名稱] earnings, [公司名稱] 法說會
   時間：持股期間
   影響：個股操作
   ```

2. **產業客戶動態**
   ```
   查詢：Apple iPhone, NVIDIA Blackwell, Tesla production
   時間：有重大產品發布
   影響：供應鏈股票
   ```

---

## 🤖 自動化查詢流程

### Step 1: 執行WebSearch（強制）

**每次分析前必須執行**：
```python
# 1. 美股前一日表現
WebSearch("US stock market today NASDAQ Dow S&P500")

# 2. 科技巨頭財報（財報季）
WebSearch("NVIDIA earnings latest")
WebSearch("TSMC earnings latest")

# 3. 重大經濟數據（每月第一週）
WebSearch("US CPI latest")
WebSearch("Fed interest rate latest")

# 4. 費半指數異動
WebSearch("SOX index semiconductor stocks")

# 5. 台股重大新聞
WebSearch("Taiwan stock market news semiconductor")
```

---

### Step 2: 判斷是否影響台股

**時事分類標準**：
| 時事 | 影響等級 | 受惠股票 | 操作 |
|------|---------|---------|------|
| 輝達財報超預期 | 🔥 重大利多 | 台積電、日月光、南亞科 | **必須納入分析** |
| Fed降息 | 🔥 重大利多 | 全市場、金融股 | **必須納入分析** |
| 台積電法說會 | 🔥 重大利多/利空 | 全台股 | **必須納入分析** |
| 美股小漲+0.5% | ⚡ 一般利多 | 開盤參考 | 簡短提及 |
| 個股小新聞 | ⚠️ 微小影響 | 個股 | 可忽略 |

---

### Step 3: 時事+法人數據矛盾分析（核心）

**當時事利多 vs 法人賣超**：
```
輝達財報超預期 + Blackwell爆單
→ 台積電、日月光應受惠
→ 但法人數據：投信+477 vs 外資-16,145（法人對決）

可能A：外資錯了、利多延遲反應 → 今日可能補漲
可能B：法人提前知道利多不如預期 → 謹慎觀望

→ 決策：等盤中Scanner驗證量能
```

**判斷原則**：
- ✅ 時事利多 + 法人買超 = 推薦
- ⚠️ 時事利多 + 法人賣超 = **討論矛盾、等驗證**
- ❌ 時事利空 + 法人賣超 = 避開

---

## ✅ 執行檢查表（每次分析前確認）

**盤前分析**（09:00前）：
- [ ] 執行WebSearch美股前一日表現
- [ ] 執行WebSearch科技巨頭財報（財報季）
- [ ] 執行WebSearch重大經濟數據（每月第一週）
- [ ] 執行WebSearch費半指數異動
- [ ] 執行WebSearch台股重大新聞
- [ ] 時事+法人數據矛盾分析（若有矛盾）
- [ ] 時事權重40%（CLAUDE.md規範）

**盤中分析**（12:30）：
- [ ] 執行WebSearch盤中重大突發新聞
- [ ] 執行intraday_scanner.py驗證時事利多是否發酵

**盤後分析**（14:30後）：
- [ ] 執行WebSearch當日收盤新聞
- [ ] 驗證盤前時事預測是否正確

---

## 🚨 違規處理

**若未執行此檢查清單**：
- ❌ 立即停止分析
- ❌ 補充遺漏時事
- ❌ 重新評估推薦股票
- ❌ 記錄至PREDICTION_ACCURACY_TRACKING.md

---

## 📝 範例：正確流程

```
用戶：「盤前分析」

我：「執行市場時事檢查...」

# Step 1: WebSearch
WebSearch("US stock market NASDAQ Dow")
→ NASDAQ +0.6%, Dow +0.1%

WebSearch("NVIDIA earnings latest")
→ 🔥 輝達財報超預期！EPS $1.30 vs 預期$1.25

WebSearch("Taiwan semiconductor news")
→ 台積電ADR +1.08%

# Step 2: 判斷影響
輝達財報超預期 = 🔥 重大利多
→ 台積電、日月光、南亞科直接受惠
→ 必須納入分析

# Step 3: 法人數據
台積電11/19：投信+477、外資-16,145（法人對決）

# Step 4: 矛盾分析
時事利多 vs 法人賣超 = 討論矛盾、等盤中驗證

我：「我即將執行盤前分析：

📊 時事重點：
- 🔥 輝達財報超預期（EPS +4%、Blackwell爆單）
- ✅ NASDAQ +0.6%、台積電ADR +1.08%

📊 法人數據：
- ❌ 台積電法人對決（投信+477 vs 外資-16,145）
- ❌ 金融股法人對決（富邦金投信+25K vs 外資-40K）

📋 推薦範圍：
- ❌ 無股票可推薦（即使輝達利多）
- 理由：時事利多 vs 法人賣超 = 矛盾，等盤中驗證

✋ 請確認，我再開始撰寫。」
```

---

## 📌 整合至CONVERSATION_START_CHECKLIST.md

**已整合**（待確認）：
- [ ] 在CONVERSATION_START_CHECKLIST.md增加「執行MARKET_NEWS_CHECKLIST.md」
- [ ] 每次對話開始強制提醒

---

**最後更新**：2025-11-20
**版本**：v1.0
**目的**：防止遺漏重大時事（如輝達財報）
