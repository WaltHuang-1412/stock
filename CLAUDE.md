# 台股分析執行流程（v7.1 精簡版）

**版本**：v7.1
**更新日期**：2026-02-03
**目的**：提供清晰、可執行的盤前/盤中/盤後分析流程

---

## ⚠️ 核心原則

### 🔴 強制執行規則

1. **所有步驟必須按順序執行，不得跳過**
2. **所有腳本執行必須保存輸出文件作為證據**
3. **禁止編造、估算、憑記憶填入任何數據**
4. **每個步驟完成後標記 TodoWrite，逐步打勾**

### 📁 驗證機制

每次分析完成後，必須存在以下文件：
- 盤前：`data/YYYY-MM-DD/before_market_analysis.md` + `us_asia_markets.json` + `tw_market_news.json` + `tracking_YYYY-MM-DD.json`
- 盤中：`data/YYYY-MM-DD/intraday_analysis.md` + 更新 `tracking_YYYY-MM-DD.json`
- 盤後：`data/YYYY-MM-DD/after_market_analysis.md` + 更新 `tracking_YYYY-MM-DD.json` + 更新 `predictions.json`

**如果檔案不存在 = 步驟未執行 = 違規**

---

## 📊 一、盤前分析流程（09:00 前執行）

**目標**：預測今日有機會的股票，給出明確進場策略
**時間**：約 60-90 分鐘

### 🔴 Step 0: 建立 TodoWrite（強制第一步）

```bash
# 建立追蹤清單，確保不跳過任何步驟
```

**TodoWrite 內容**：
```json
[
  {"content": "Step 1: 獲取國際市場數據", "status": "pending"},
  {"content": "Step 2: 獲取台股時事數據", "status": "pending"},
  {"content": "Step 3: 即時股價查詢（推薦股票）", "status": "pending"},
  {"content": "Step 4: 歷史驗證（昨日推薦表現）", "status": "pending"},
  {"content": "Step 5: 法人 TOP30 掃描", "status": "pending"},
  {"content": "Step 6: 時事展開（受惠產業代表股）", "status": "pending"},
  {"content": "Step 7: 五維度評分", "status": "pending"},
  {"content": "Step 8: 籌碼深度分析", "status": "pending"},
  {"content": "Step 9: 產業分散檢查", "status": "pending"},
  {"content": "Step 10: 建檔", "status": "pending"}
]
```

---

### 🔴 Step 1: 獲取國際市場數據（強制）

**執行命令**：
```bash
cd /c/Users/walter.huang/Documents/github/stock
python3 scripts/fetch_us_asia_markets.py > data/$(date +%Y-%m-%d)/us_asia_markets.json
```

**驗證**：
- ✅ 必須生成 `data/YYYY-MM-DD/us_asia_markets.json`
- ✅ 文件內必須包含：NASDAQ、費半、WTI原油、輝達等數據
- ❌ **如果文件不存在 = 步驟未執行 = 禁止繼續**

**數據使用**：
- 費半漲跌 → 判斷半導體股機會
- 油價漲跌 → 判斷塑化/航空股方向
- 輝達漲跌 → 判斷 AI 伺服器股機會

**完成後**：更新 TodoWrite，標記 Step 1 為 `completed`

---

### 🔴 Step 2: 獲取台股時事數據（強制）

**執行命令**：
```bash
python3 scripts/fetch_tw_market_news.py > data/$(date +%Y-%m-%d)/tw_market_news.json
```

**驗證**：
- ✅ 必須生成 `data/YYYY-MM-DD/tw_market_news.json`
- ✅ 文件內必須包含：重大訊息、法說會、熱門題材
- ❌ **如果文件不存在 = 步驟未執行 = 禁止繼續**

**數據使用**：
- 法說會日期 → 關注相關股票
- 重大訊息 → 個股利多/利空
- 熱門題材 → 產業催化劑

**完成後**：更新 TodoWrite，標記 Step 2 為 `completed`

---

### 🔴 Step 3: 即時股價查詢（可選，推薦股票時執行）

**執行時機**：在推薦股票前，必須查詢即時股價

**執行命令**：
```python
python3 -c "
import requests
stocks = ['2303', '2330', '3037']  # 替換為實際推薦股票
for s in stocks:
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{s}.TW?interval=1d&range=5d'
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    data = r.json()
    close = data['chart']['result'][0]['meta']['regularMarketPrice']
    print(f'{s}: 現價={close}')
"
```

**目的**：
- 確保進場價基於即時數據
- 避免使用舊價格或記憶中的價格

**完成後**：更新 TodoWrite，標記 Step 3 為 `completed`

---

### 🔴 Step 4: 歷史驗證（強制）

**執行命令**：
```bash
# 讀取昨日 tracking 記錄
cat data/tracking/tracking_$(date -d yesterday +%Y-%m-%d).json
```

**檢查項目**：
1. 昨日推薦股票表現（逐檔檢查收盤價 vs 推薦價）
2. 成功/失敗統計（X/Y = Z%）
3. 成功股票的共同特徵（延續到今日？）
4. 失敗股票的共同特徵（今日要避開？）

**輸出到分析報告**：
```markdown
## 歷史驗證

昨日推薦：X 檔
成功：Y 檔（+Z%）
失敗：W 檔（原因：...）
準確率：Y/X = ZZ%

教訓：
- 成功模式：...
- 失敗模式：...
```

**完成後**：更新 TodoWrite，標記 Step 4 為 `completed`

---

### 🔴 Step 5: 法人 TOP30 掃描（強制）

**執行命令**：
```bash
python3 scripts/fetch_institutional_top30.py $(date -d yesterday +%Y%m%d)
```

**驗證**：
- ✅ 必須輸出完整 TOP30 買超 + TOP30 賣超
- ✅ 每檔必須包含：三大法人、投信、外資、5日漲幅
- ❌ **禁止只查詢部分股票**

**輸出到分析報告**：
```markdown
## 法人買超 TOP30

| 排名 | 代號 | 名稱 | 三大法人 | 投信 | 外資 | 5日漲幅 | 狀態 |
|------|------|------|---------|------|------|--------|------|
| 1 | 2303 | 聯電 | +22K | -23K | +43K | +1.4% | ✅ 可進場 |
（完整 30 檔）
```

**完成後**：更新 TodoWrite，標記 Step 5 為 `completed`

---

### 🔴 Step 6: 時事展開（強制）

**目的**：從時事催化劑展開受惠產業代表股

**執行邏輯**：
1. 讀取 Step 1（國際市場）+ Step 2（台股時事）
2. 判斷今日催化方向（例：費半+2% → 半導體利多）
3. 查「時事→產業→代表股」對照表
4. 對代表股執行法人查詢

**時事→產業對照表**（必查）：

| 時事訊號 | 受惠產業 | 代表股（必查） |
|---------|---------|---------------|
| 費半大漲 >1% | 晶圓代工 | 台積電(2330)、聯電(2303) |
|  | 載板/PCB | 欣興(3037)、景碩(3189)、華通(2313) |
|  | 記憶體 | 南亞科(2408)、華邦電(2344)、旺宏(2337) |
|  | 封測 | 日月光(3711)、力成(6239)、京元電(2449) |
|  | 半導體設備 | 弘塑(3131)、辛耘(3583) |
| 輝達/AMD大漲 >3% | AI伺服器 | 廣達(2382)、緯創(3231)、鴻海(2317) |
| 油價大漲 >2% | 塑化（利多） | 台塑(1301)、南亞(1303)、台化(1326) |
|  | 航空（利空） | 華航(2610)、長榮航(2618) |

**執行命令**（以費半+2%為例）：
```bash
# 查詢半導體5次產業代表股
python3 scripts/chip_analysis.py 2330 2303 3037 2408 3711
```

**完成後**：更新 TodoWrite，標記 Step 6 為 `completed`

---

### 🔴 Step 7: 五維度評分（強制）

**對象**：Step 5（TOP30）+ Step 6（時事展開）合併去重後的候選股

**評分維度**：
1. 時事現況（30%）
2. 法人數據（30%）
3. 產業邏輯（20%）
4. 價格位置（10%）
5. 技術面（10%）

**推薦門檻**：
- ≥85分 → 強烈推薦 15-20% ⭐⭐⭐⭐⭐
- 75-84分 → 推薦 10-15% ⭐⭐⭐⭐
- 65-74分 → 可考慮 5-10% ⭐⭐⭐
- <65分 → 不推薦

**完成後**：更新 TodoWrite，標記 Step 7 為 `completed`

---

### 🔴 Step 8: 籌碼深度分析（強制，對推薦股執行）

**執行命令**：
```bash
python3 scripts/chip_analysis.py [推薦股代號1] [推薦股代號2] ... --days 10
```

**檢查項目**：
1. 真連續買超天數（中間有沒有賣？）
2. 累計淨買超（10天加總多少？）
3. 外資 vs 投信（同步買？還是對決？）
4. 籌碼動能（前5日 vs 近5日，加速還是減速？）

**判斷標準**：
| 判斷 | 條件 | 建議 |
|------|------|------|
| ✅ 佈局 | 連續買超≥5天 + 累計淨買>0 | 可進場 |
| ✅ 買進 | 連續買超3-4天 + 累計淨買>0 | 可進場 |
| 🟡 偏多 | 買多於賣但不連續 | 觀察 |
| 🔴 出貨 | 累計賣超且最近在賣 | 避開 |

**完成後**：更新 TodoWrite，標記 Step 8 為 `completed`

---

### 🔴 Step 9: 產業分散檢查（強制）

**規則**：
- 推薦數量：6-8 檔
- 單一產業上限：≤50%（一般日）
- 最少產業數：≥3 個

**如果違反**：必須從其他產業補充推薦

**完成後**：更新 TodoWrite，標記 Step 9 為 `completed`

---

### 🔴 Step 10: 建檔（強制）

**建立以下檔案**：

1. **分析報告**：`data/YYYY-MM-DD/before_market_analysis.md`
2. **追蹤記錄**：`data/tracking/tracking_YYYY-MM-DD.json`

**tracking.json 格式**：
```json
{
  "date": "2026-02-02",
  "recommendations": [
    {
      "stock_code": "2303",
      "stock_name": "聯電",
      "recommend_price": 52.5,
      "target_price": 58.0,
      "stop_loss": 48.3,
      "position": "15-20%",
      "score": 88,
      "reason": "費半+2%、外資+43K、AI 需求"
    }
  ]
}
```

**驗證**：
- ✅ 兩個檔案都必須存在
- ✅ tracking.json 必須包含所有推薦股票
- ❌ **如果檔案不存在 = 分析未完成**

**完成後**：更新 TodoWrite，標記 Step 10 為 `completed`

---

## 📊 二、盤中分析流程（12:30 執行）

**目標**：追蹤推薦股表現 + 發現新機會，給出尾盤策略
**時間**：約 30-40 分鐘

### 🔴 Step 0: 建立 TodoWrite（強制第一步）

```json
[
  {"content": "Step 1: 前置檢查（確認tracking存在）", "status": "pending"},
  {"content": "Step 2: Track A 推薦股追蹤", "status": "pending"},
  {"content": "Step 3: Track B 全市場掃描", "status": "pending"},
  {"content": "Step 4: 雙軌整合輸出", "status": "pending"},
  {"content": "Step 5: 建檔", "status": "pending"}
]
```

---

### 🔴 Step 1: 前置檢查（強制）

**檢查項目**：
```bash
# 確認 tracking 檔案存在
ls data/tracking/tracking_$(date +%Y-%m-%d).json
```

**如果檔案不存在**：
- ❌ 禁止執行盤中分析
- ❌ 必須先執行盤前分析

**完成後**：更新 TodoWrite，標記 Step 1 為 `completed`

---

### 🔴 Step 2: Track A 推薦股追蹤（強制）

**執行命令**：
```bash
python3 scripts/intraday_dual_track.py
```

**檢查項目**（對每檔推薦股）：
1. 盤中價位 vs 推薦價（漲跌%）
2. 量比（今日量 vs 5日均量）
3. 買賣盤比（外盤% vs 內盤%）
4. 五維度盤中評分

**尾盤策略**：
- ✅ 續抱：表現正常，繼續持有
- ➕ 加碼：回檔+縮量+法人續買
- 🛑 停損：跌破停損價

**⚠️ 回檔股深度驗證（強制）**：

如果推薦股回檔，必須執行 4 項驗證：
```bash
# 1. 查昨日vs前日法人力道
python3 scripts/check_institutional.py [股票代號] [昨日YYYYMMDD]
python3 scripts/check_institutional.py [股票代號] [前日YYYYMMDD]

# 2. 籌碼動能分析
python3 scripts/chip_analysis.py [股票代號] --days 10

# 3. 反轉預警檢查
python3 scripts/reversal_alert.py [股票代號]

# 4. 價格位階
```

**判斷標準**：4項必須全部通過才能建議加碼
- 昨日vs前日法人力道：減少>50% → ❌ 觀望
- 籌碼動能：減弱>30% → ❌ 觀望
- 反轉預警：Level 1預警 → ❌ 觀望
- 價格位階：>80% → ❌ 觀望

**完成後**：更新 TodoWrite，標記 Step 2 為 `completed`

---

### 🔴 Step 3: Track B 全市場掃描（強制）

**目的**：發現盤前遺漏的機會

**掃描範圍**：
1. 成交量 TOP20（量大的股票 = 資金關注）
2. 量比 TOP20（今日量 vs 5日均量）
3. 買賣方向判斷（外盤% vs 內盤%）

**判斷標準**：
| 量能 | 價格 | 昨日法人 | 推測 | 策略 |
|------|------|----------|------|------|
| 爆量 | 小漲/平 | 買超 | ✅ 法人吸貨中 | 尾盤可買 |
| 爆量 | 下跌 | 賣超 | ❌ 法人出貨 | 避開 |

**⚠️ 重要**：Track B 發現的股票，僅記錄，不建議追高

**完成後**：更新 TodoWrite，標記 Step 3 為 `completed`

---

### 🔴 Step 4: 雙軌整合輸出（強制）

**輸出格式**：
```markdown
## Track A 操作建議

| 股票 | 推薦價 | 盤中價 | 漲跌% | 尾盤策略 |
|------|--------|--------|-------|----------|
| 聯電 | 52.5 | 54.2 | +3.2% | ✅ 續抱 |

## Track B 市場發現

| 股票 | 盤中價 | 漲跌% | 量比 | 備註 |
|------|--------|-------|------|------|
| 欣興 | 361.5 | +4.9% | 2.5x | 盤中發現，僅記錄 |
```

**完成後**：更新 TodoWrite，標記 Step 4 為 `completed`

---

### 🔴 Step 5: 建檔（強制）

**建立/更新以下檔案**：

1. **盤中分析報告**：`data/YYYY-MM-DD/intraday_analysis.md`
2. **更新追蹤記錄**：`data/tracking/tracking_YYYY-MM-DD.json`（加入盤中價格）

**驗證**：
- ✅ 兩個檔案都必須存在
- ✅ tracking.json 必須更新 `intraday_price` 欄位
- ❌ **如果檔案不存在 = 分析未完成**

**完成後**：更新 TodoWrite，標記 Step 5 為 `completed`

---

## 📊 三、盤後分析流程（14:30 後執行）

**目標**：驗證推薦準確率 + 預測明日機會
**時間**：約 40-50 分鐘

### 🔴 Step 0: 建立 TodoWrite（強制第一步）

```json
[
  {"content": "Step 1: 前置檢查", "status": "pending"},
  {"content": "Step 2: Track A 驗證", "status": "pending"},
  {"content": "Step 3: Track B 整合", "status": "pending"},
  {"content": "Step 4: 更新 predictions.json", "status": "pending"},
  {"content": "Step 5: 明日預測", "status": "pending"},
  {"content": "Step 6: 建檔", "status": "pending"}
]
```

---

### 🔴 Step 1: 前置檢查（強制）

**檢查項目**：
```bash
# 確認盤中分析已完成
ls data/$(date +%Y-%m-%d)/intraday_analysis.md
```

**如果檔案不存在**：
- ❌ 禁止執行盤後分析
- ❌ 必須先執行盤中分析

**完成後**：更新 TodoWrite，標記 Step 1 為 `completed`

---

### 🔴 Step 2: Track A 驗證（強制）

**檢查項目**：
1. 逐檔推薦股驗證（推薦價 vs 收盤價）
2. 成功/失敗統計（X/Y = Z%）
3. 失敗原因分析（法人反轉？產業邏輯失效？）
4. 成功經驗總結（可延續到明日？）

**輸出格式**：
```markdown
## 今日驗證

| 股票 | 推薦價 | 收盤價 | 漲跌% | 驗證 |
|------|--------|--------|-------|------|
| 聯電 | 52.5 | 54.8 | +4.4% | ✅ 成功 |
| 南亞 | 75.0 | 70.3 | -6.3% | ❌ 失敗 |

準確率：4/5 = 80%

失敗原因：
- 南亞：油價數據錯誤（編造+5.06%，實際-4.71%）
```

**完成後**：更新 TodoWrite，標記 Step 2 為 `completed`

---

### 🔴 Step 3: Track B 整合（強制）

**檢查項目**：
1. 盤中 Track B 發現的 TOP5 深度分析
2. 遺漏機會根本原因（為什麼盤前沒推薦？）
3. 策略盲點檢討（五維度評分哪裡失效？）

**輸出格式**：
```markdown
## 遺漏機會檢討

| 股票 | 收盤漲幅 | 盤前為何沒推薦 | 改進方向 |
|------|---------|---------------|----------|
| 欣興 | +9.5% | 不在 TOP30，時事展開遺漏 | 擴大時事展開範圍 |
```

**完成後**：更新 TodoWrite，標記 Step 3 為 `completed`

---

### 🔴 Step 4: 更新 predictions.json（強制）

**執行命令**：
```bash
# 手動更新 data/predictions/predictions.json
```

**格式**：
```json
{
  "2026-02-02": {
    "date": "2026-02-02",
    "predictions": [
      {
        "symbol": "2303",
        "name": "聯電",
        "recommend_price": 52.5,
        "actual_close": 54.8,
        "result": "success"
      }
    ],
    "accuracy": 0.80,
    "notes": "油價數據編造錯誤導致南亞失敗"
  }
}
```

**完成後**：更新 TodoWrite，標記 Step 4 為 `completed`

---

### 🔴 Step 5: 明日預測（強制）

**執行內容**：
1. 基於今日發現調整明日策略
2. 延續成功模式
3. 避開失敗模式
4. 推薦明日股票（6-8檔）

**輸出格式**：
```markdown
## 明日預測（2026-02-03）

### ⭐⭐⭐⭐⭐ 強烈推薦

**聯電(2303)** - 總分：88分
- 進場價：54.0-55.0元
- 倉位：15-20%
- 停損：52.0元
- 目標：58.0元
```

**完成後**：更新 TodoWrite，標記 Step 5 為 `completed`

---

### 🔴 Step 6: 建檔（強制）

**建立/更新以下檔案**：

1. **盤後分析報告**：`data/YYYY-MM-DD/after_market_analysis.md`
2. **更新追蹤記錄**：`data/tracking/tracking_YYYY-MM-DD.json`（加入收盤價+結果）
3. **更新預測記錄**：`data/predictions/predictions.json`

**驗證**：
- ✅ 三個檔案都必須存在/更新
- ✅ tracking.json 必須包含收盤價和驗證結果
- ❌ **如果檔案不存在 = 分析未完成**

**完成後**：更新 TodoWrite，標記 Step 6 為 `completed`

---

## 🛠️ 四、隨時可用工具

以下工具不限於特定分析階段，隨時可用：

---

### 1. **my_holdings_analyzer.py** - 個人持股分析

**用途**：分析個人持股健康度，整合四維度評分

**執行時機**：
- 盤前分析 Step 3.5（可選）
- 任何時候想了解持股狀況

**執行命令**：
```bash
python3 scripts/my_holdings_analyzer.py
```

**功能**：
1. 讀取 `portfolio/my_holdings.yaml`
2. 四維度評分：
   - 價格表現（30%）
   - 法人態度（30%）
   - 時事相關（20%）
   - 產業邏輯（20%）
3. 健康度評分：0-100分
4. 操作建議：續抱/加碼/減碼/停損

**輸出範例**：
```markdown
## 個人持股分析

**聯電(2303)** - 健康度：85分
- 價格：+4.2%（✅ 表現良好）
- 法人：外資+43K、投信-23K（⚠️ 分歧）
- 時事：費半+2%（✅ 利多）
- 建議：續抱

**南亞(1303)** - 健康度：45分
- 價格：-6.3%（❌ 表現不佳）
- 法人：三大法人-8K（❌ 賣超）
- 時事：油價-4.7%（❌ 利空）
- 建議：停損
```

**觸發關鍵詞**：
- 「個人持股分析」
- 「持股健康度」
- 「我的股票表現如何」

---

### 2. **holdings_analysis.py** - 持股水位分析

**用途**：分析法人持股水位，判斷出場壓力

**執行時機**：
- 看到法人大賣超時
- 判斷是短期調整還是長期出場

**執行命令**：
```bash
python3 scripts/holdings_analysis.py 2330
python3 scripts/holdings_analysis.py 2886 1303 3481  # 多檔同時分析
```

**功能**：
1. 查詢外資持股量（張數）
2. 查詢外資持股比例（%）
3. 計算「賣超佔持股比例」（關鍵指標）
4. 評估出場壓力等級

**出場壓力等級**：
| 賣超佔持股比例 | 壓力等級 | 說明 |
|-------------|---------|------|
| > 10% | 🔴 高壓 | 大規模出貨 |
| 5-10% | 🟠 中高壓 | 明顯減碼 |
| 2-5% | 🟡 中壓 | 調節持股 |
| 0-2% | ⚪ 低壓 | 小幅調整 |
| < 0%（買超） | 🟢 吸籌 | 持續加碼 |

**輸出範例**：
```markdown
## 台積電(2330) 持股水位分析

外資持股：1,234,567張（持股比例：47.8%）
昨日賣超：-12,345張
賣超佔持股比例：1.0%

評估：⚪ 低壓（小幅調整）
說明：外資持股水位仍高，賣超<2%屬正常調節
```

**觸發關鍵詞**：
- 「出場壓力分析」
- 「持股水位」
- 「外資持股比例」
- 「法人手上有多少」

---

### 3. **stock_tracker.py** - 7日追蹤系統

**用途**：追蹤推薦股票7日表現，驗證準確率

**執行時機**：
- 盤後分析 Step 4（每日14:30後）
- 自動追蹤推薦後的7日表現

**執行命令**：
```bash
python3 scripts/stock_tracker.py
```

**功能**：
1. 自動讀取所有 `tracking_YYYY-MM-DD.json`
2. 更新每檔股票的價格 + 法人數據
3. 計算推薦後N日漲跌幅
4. 7日後自動產生追蹤報告

**輸出**：
- 更新 `tracking_YYYY-MM-DD.json`（加入最新價格）
- 產生 `data/tracking/reports/YYYY-MM-DD_[股票代號]_7day_report.md`（7日後）

**7日報告內容**：
```markdown
## 聯電(2303) 7日追蹤報告

推薦日期：2026-02-02
推薦價格：52.5元
7日後價格：58.2元
漲跌幅：+10.9%

法人7日累計：
- 外資：+85,234張
- 投信：-12,345張
- 總計：+72,889張

結論：✅ 推薦成功
```

---

### 4. **validate_analysis.py** - 分析驗證工具

**用途**：驗證分析是否符合標準，commit前強制執行

**執行時機**：
- 盤前分析完成後（Step 10.5）
- 盤中分析完成後（Step 5.5）
- 盤後分析完成後（Step 7.5）

**執行命令**：
```bash
python3 scripts/validate_analysis.py before_market 2026-02-03
python3 scripts/validate_analysis.py intraday 2026-02-03
python3 scripts/validate_analysis.py after_market 2026-02-03
```

**驗證項目**：

**盤前分析驗證**：
- ✅ 版本是否為 v7.1
- ✅ 推薦數量是否 6-8 檔
- ✅ 產業是否至少 4 個
- ✅ 單一產業是否 ≤50%
- ✅ 檔案是否完整建立（before_market_analysis.md + tracking.json）

**盤中分析驗證**：
- ✅ 是否包含 Track A 和 Track B
- ✅ 是否給出尾盤策略
- ✅ 檔案是否建立（intraday_analysis.md）

**盤後分析驗證**：
- ✅ 是否計算準確率
- ✅ tracking.json 是否包含收盤價
- ✅ predictions.json 是否更新
- ✅ 檔案是否完整（after_market_analysis.md + tracking.json + predictions.json）

**返回值**：
- `0` = 驗證通過 → ✅ 允許 commit
- `1` = 驗證失敗 → ❌ 禁止 commit，必須修正

**範例**：
```bash
$ python3 scripts/validate_analysis.py before_market 2026-02-03
✅ 版本檢查：v7.1
✅ 推薦數量：7檔
✅ 產業數量：5個
✅ 產業分散：最大40%
✅ 檔案完整：before_market_analysis.md + tracking.json

驗證通過！
```

**⚠️ 重要**：如果驗證失敗，必須修正後重新驗證，禁止直接commit

---

### 5. **institutional_positioning_detector.py** - 法人佈局偵測器

**用途**：全市場掃描，偵測法人佈局機會

**執行時機**：
- 盤中12:30（可選，不強制）
- 想尋找盤前遺漏的機會時

**執行命令**：
```bash
python3 scripts/institutional_positioning_detector.py
```

**功能**：
1. 全市場掃描500檔重點股票
2. 偵測「法人連續買超 + 盤中爆量 + 還沒大漲」的股票
3. 量能異動分析（量比>1.5x）
4. 買賣方向判斷（外盤% vs 內盤%）

**偵測訊號**：
| 條件組合 | 訊號 | 操作建議 |
|---------|------|---------|
| 連續買超≥3日 + 今日爆量 + 漲幅<2% | ⭐ 強佈局 | 可進場 |
| 連續買超≥3日 + 今日爆量 + 漲幅2-5% | 🟡 佈局中 | 觀察 |
| 連續買超≥3日 + 今日爆量 + 漲幅>5% | ⚠️ 已反映 | 不追高 |

**輸出範例**：
```markdown
## 盤中佈局偵測（12:30）

⭐ 強佈局訊號：
- 廣達(2382)：連3日+17K、今日量比2.5x、漲幅+0.5%
- 聯電(2303)：連3日+85K、今日量比1.8x、漲幅+1.2%
```

**⚠️ 注意**：
- 此工具為輔助工具，不強制執行
- 偵測到的股票仍需五維度評分
- 不能直接推薦，僅供參考

---

## 🚨 違規處理

### 如果發現跳過步驟

1. **立即停止分析**
2. **標註違規步驟**
3. **回到該步驟重新執行**
4. **記錄違規到 predictions.json**

### 如果發現編造數據

1. **立即承認錯誤**
2. **重新執行該步驟腳本**
3. **記錄失誤到 predictions.json**
4. **分析報告中標註「數據修正」**

---

## 📝 附註

### 關於簡化流程

**不再提供簡化流程。**
- 要麼完整執行所有步驟
- 要麼不執行

**理由**：簡化流程容易導致跳過關鍵步驟，造成數據錯誤。

### 關於評分系統、歷史教訓等

這些內容已移至：
- `docs/reference/SCORING_SYSTEM.md`（評分系統）
- `docs/reference/HISTORICAL_LESSONS.md`（歷史教訓）
- `docs/reference/TOOLS_GUIDE.md`（工具指南）

本文件**只專注於執行流程**。

---

**最後更新**：2026-02-03
**版本**：v7.1（精簡版 + 隨時可用工具章節）
