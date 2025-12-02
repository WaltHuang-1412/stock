# 股票分析系統工具狀態報告

## 報告時間：2025-12-02 16:35

---

## 一、系統總覽

### 📊 工具清單
```
scripts/
├── check_institutional.py         (4,419 bytes) ✅ 正常
├── intraday_analyzer_v2.py       (15,712 bytes) ✅ 正常
├── institutional_positioning_detector.py (8,814 bytes) ✅ 正常
├── stock_tracker.py               (13,300 bytes) ⚠️ 已修復
└── archive/
    └── archive_intraday_scanner.py (舊版，已停用)
```

---

## 二、各工具狀態詳情

### 1. check_institutional.py ✅ 正常運作
- **功能**：查詢單一股票法人買賣超數據
- **狀態**：正常
- **測試結果**：成功查詢台積電(2330) 12/01法人數據
- **用法**：`python3 scripts/check_institutional.py 2330 20251201`

### 2. intraday_analyzer_v2.py ✅ 正常運作
- **功能**：盤中五維度分析，驗證盤前推薦表現
- **狀態**：正常
- **執行時機**：12:30
- **今日執行結果**：成功分析，準確率33%（廣達符合預期）
- **注意事項**：需要tracking.json檔案存在才能執行

### 3. institutional_positioning_detector.py ✅ 正常運作
- **功能**：法人佈局偵測器，全市場掃描
- **狀態**：正常
- **執行時機**：12:30
- **今日執行結果**：僅發現2檔觀察股（廣達、永豐金）
- **特色**：全市場視野，不限於盤前推薦

### 4. stock_tracker.py ⚠️ 已修復
- **功能**：7日追蹤系統，驗證推薦準確率
- **原問題**：ImportError - `cannot import name 'get_institutional_data'`
- **錯誤原因**：
  - 嘗試從 src.data_fetcher 導入不存在的 `get_institutional_data` 函數
  - 實際函數名稱是 `fetch_institutional_data`
- **修復內容**：
  ```python
  # 原本（錯誤）
  from src.data_fetcher import get_institutional_data

  # 修正後
  from src.data_fetcher import DataFetcher
  # 使用 fetcher.fetch_institutional_data(stock_code)
  ```
- **其他問題**：
  - 舊版tracking檔案使用 `symbol` 而非 `stock_code` 欄位
  - 需要統一格式或加入相容性處理
- **當前狀態**：程式碼已修復，但執行時可能遇到舊檔案格式問題

---

## 三、共通問題

### 1. SSL警告（所有工具）
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+
```
- **影響**：不影響功能，僅為警告訊息
- **原因**：系統使用 LibreSSL 2.8.3 而非 OpenSSL
- **解決**：可忽略或升級 SSL 庫

### 2. Yahoo Finance API 問題
- **症狀**：部分股票顯示 "possibly delisted"
- **受影響股票**：3697.TW, 2823.TW, 4000.TW 等
- **原因**：可能是股票代碼變更或 API 暫時性問題
- **影響**：無法獲取這些股票的即時價格

### 3. Tracking檔案格式不一致
- **問題**：
  - 舊檔案（11/26前）：使用 `symbol` 欄位
  - 新檔案（12/02後）：使用 `stock_code` 欄位
- **影響**：stock_tracker.py 執行時會報 KeyError
- **建議解決方案**：
  1. 更新 stock_tracker.py 支援兩種格式
  2. 或批次轉換舊檔案格式

---

## 四、建議優先修復項目

### 🔴 高優先級
1. **stock_tracker.py 格式相容性**
   - 讓程式同時支援 `symbol` 和 `stock_code` 欄位
   - 避免因格式不同導致追蹤失敗

### 🟡 中優先級
2. **Yahoo Finance API 錯誤處理**
   - 加入更完善的錯誤處理機制
   - 建立股票代碼對照表

### 🟢 低優先級
3. **SSL 警告處理**
   - 可選擇性升級或抑制警告訊息

---

## 五、工具使用建議

### 每日執行流程
```bash
# 09:00 盤前分析
撰寫盤前分析報告 → 建立 tracking_YYYY-MM-DD.json

# 12:30 盤中分析（兩個工具並行）
python3 scripts/intraday_analyzer_v2.py        # 驗證推薦
python3 scripts/institutional_positioning_detector.py  # 發現機會

# 14:30 盤後分析
python3 scripts/stock_tracker.py --date YYYYMMDD  # 追蹤更新（需修復）
撰寫盤後分析報告

# 隨時可用
python3 scripts/check_institutional.py [股票代碼] [日期]  # 查詢法人
```

---

## 六、總結

### ✅ 正常運作工具（3/4）
- check_institutional.py
- intraday_analyzer_v2.py
- institutional_positioning_detector.py

### ⚠️ 需要完善的工具（1/4）
- stock_tracker.py（已修復程式碼，但需處理格式相容性）

### 系統整體狀態
- **可用性**：75%（主要功能正常）
- **穩定性**：中等（存在格式不一致問題）
- **建議**：優先修復 stock_tracker.py 的格式相容性問題

---

**報告產生時間**：2025-12-02 16:35
**下次檢查建議**：修復 tracking 格式問題後