# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 系統概述

這是一個基於真實法人數據的台股智能分析系統，提供股票分析、法人投資推薦和個人持股管理功能。

## 核心架構

### 主要模組
- `main.py` - 系統入口，支援互動和單次查詢模式
- `data_fetcher.py` - 數據獲取引擎，串接證交所API和Yahoo Finance
- `analyzer.py` - 多維分析引擎，整合法人、技術、新聞分析
- `query_parser.py` - 自然語言查詢解析器
- `portfolio_analyzer.py` - 個人持股分析模組
- `utils.py` - 工具函數和裝飾器

### 配置文件
- `config.yaml` - 系統配置，包含API設定和分析權重
- `my_holdings.yaml` - 個人持股配置文件
- `requirements.txt` - Python依賴套件

## 常用命令

### 安裝依賴
```bash
pip install -r requirements.txt
```

### 運行系統
```bash
# 互動模式
python3 main.py

# 單次查詢
python3 main.py -q "台積電最近法人怎麼看？"

# 個人持股分析
python3 portfolio_analyzer.py

# 測試範例
python3 examples.py
```

### 開發和測試
```bash
# 測試數據獲取
python3 data_fetcher.py

# 測試查詢解析
python3 query_parser.py

# 測試分析器
python3 analyzer.py

# 測試工具函數
python3 utils.py
```

## 數據流架構

1. **查詢解析**: `QueryParser` 解析用戶自然語言查詢，提取股票代號、分析類型、時間範圍
2. **數據獲取**: `DataFetcher` 從多個來源獲取數據：
   - 證交所API：股價和法人買賣超數據
   - Yahoo Finance：股價和新聞數據
   - 鉅亨網：財經新聞
3. **智能分析**: `StockAnalyzer` 進行多維分析：
   - 法人分析 (40%權重)
   - 技術分析 (30%權重)
   - 新聞分析 (20%權重)
   - 基本面分析 (10%權重)
4. **結果輸出**: 格式化輸出分析結果和投資建議

## 關鍵設計模式

### 推薦系統
- `fetch_institutional_recommendations()` 動態掃描全市場1,262檔台股
- 基於法人投資評分算法：外資60% + 投信30% + 自營商10%
- 支援雙買超加分機制

### 錯誤處理
- 使用 `@retry_on_failure` 裝飾器處理網路請求失敗
- 多層備用數據源機制（證交所API → Yahoo Finance備用）
- 優雅降級：無AI時返回基礎分析結果

### 配置驅動
- 所有API endpoint、權重、超時設定都在`config.yaml`中可配置
- 支援多種分析權重組合
- 個人投資策略在`my_holdings.yaml`中設定

## 重要注意事項

### API限制和使用
- 證交所API有速率限制，已實現延遲機制
- OpenAI API key為選填，無key時系統仍可運行
- 所有外部API調用都有超時和重試機制

### 數據真實性
- 100%使用真實數據，無模擬或假數據
- 法人數據通常有1-2小時延遲
- 交易時間內查詢速度較快

### 台股特色處理
- 支援4位數台股代號格式驗證
- 股票單位以「張」為主（1張=1000股）
- 法人分類：外資、投信、自營商三大法人

### 擴展點
- 新增分析策略可在`analyzer.py`中添加分析類型
- 新增數據源可在`data_fetcher.py`中實現
- 查詢類型可在`query_parser.py`中擴展關鍵詞

## 個人持股管理

編輯`my_holdings.yaml`設定實際持股：
- 支援多檔股票追蹤
- 自動計算損益和投資報酬率
- 基於法人動向和投資策略提供離場建議
- 可設定停損停利點和風險承受度

## 開發流程規範

### 代碼修改規則
1. **先列出要修改的文件** - 任何代碼修改前必須先列出具體文件清單
2. **等待審核批准** - 獲得明確同意後才能開始開發
3. **新系統架構需詢問** - 任何架構變更都需要事先討論
4. **禁止擅自行動** - 不得直接修改文件、創建新文件或改變架構

### 修改申請格式
```
計劃修改文件：
- file1.py - 修改目的
- file2.py - 修改目的

修改範圍：
- 具體說明修改內容
- 不影響現有功能
- 保持架構穩定
```

### 當前系統架構
- **保持雙系統分離**：`main.py`(股票查詢) + `portfolio_analyzer.py`(持股管理)
- **不建議整合**：現有架構簡單有效，維護成本低
- **專注功能增強**：在現有框架內添加新功能，不改變核心架構