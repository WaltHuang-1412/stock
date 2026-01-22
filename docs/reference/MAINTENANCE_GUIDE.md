# CLAUDE.md 維護指南

**版本**: v1.0
**最後更新**: 2026-01-22

---

## 一、文件架構原則

```
CLAUDE.md（主文件，~1000行以內）
├─ 強制執行規範（必讀）
├─ 核心流程（盤前/盤中/盤後步驟）
├─ 核心規則提醒（簡短）
└─ 參考文件連結

docs/reference/（詳細參考）
├─ SCORING_SYSTEM.md      → 評分系統詳細說明
├─ TOOLS_GUIDE.md         → 腳本工具使用指南
├─ INDUSTRY_NEWS_MAPPING.md → 時事產業對照表
├─ HISTORICAL_LESSONS.md  → 歷史教訓彙整
└─ MAINTENANCE_GUIDE.md   → 本文件
```

---

## 二、新增內容時的判斷流程

### Step 1: 判斷內容類型

| 內容類型 | 放哪裡 | 範例 |
|---------|--------|------|
| **核心流程步驟** | CLAUDE.md | Step 1.8 持股法人追蹤 |
| **強制規則/禁令** | CLAUDE.md | ❌ 絕對禁止事後諸葛 |
| **評分細則/權重表** | SCORING_SYSTEM.md | 投信20分評分標準 |
| **工具使用說明** | TOOLS_GUIDE.md | chip_analysis.py 用法 |
| **時事產業對照** | INDUSTRY_NEWS_MAPPING.md | 費半利多→半導體展開 |
| **歷史教訓案例** | HISTORICAL_LESSONS.md | 2026/01/21 陽明佈局失敗 |

### Step 2: 判斷是否為「核心」還是「詳細」

**放 CLAUDE.md 的標準**（必須全部符合）：
- ✅ 每次分析都會用到
- ✅ 屬於強制流程的一部分
- ✅ 忘記會導致嚴重錯誤
- ✅ 需要在流程中看到（不是查閱用）

**放 docs/reference/ 的標準**（符合任一）：
- ⚪ 詳細的評分標準/數值表格
- ⚪ 工具使用範例和參數說明
- ⚪ 歷史案例的詳細分析
- ⚪ 產業股票清單
- ⚪ 偶爾查閱的參考資料

---

## 三、更新 CLAUDE.md 的標準做法

### 情況 A：新增教訓/規則

**範例**：發現新的失敗模式

```markdown
# 在 CLAUDE.md 中：
**⚠️ 警告：避開「只有法人買、無產業催化」**
- 01/21教訓：陽明法人買超但-0.36%
- 規則：**無產業催化劑的佈局股 = 不推薦**

# 同時在 HISTORICAL_LESSONS.md 中新增詳細記錄：
| 2026/01/21 | 陽明法人買但-0.36% | 只有法人買無產業催化 | 佈局股雙重驗證 |
```

### 情況 B：新增工具

**範例**：新增 reversal_alert.py

```markdown
# 在 CLAUDE.md 中（簡短）：
- 🆕 **v5.7 法人反轉預警工具**
  - 用法：`python3 scripts/reversal_alert.py`

# 在 TOOLS_GUIDE.md 中（詳細）：
### reversal_alert.py - 法人反轉預警

**用途**: 偵測「連續買超後突然賣超」的股票
**執行方式**:
```bash
python3 scripts/reversal_alert.py [日期]
```
**輸出**:
- 反轉股票清單
- 連續買超天數
- 反轉幅度
```

### 情況 C：新增評分規則

**範例**：新增佈局股評分表

```markdown
# 在 CLAUDE.md 中（簡要版）：
**佈局股門檻**：≥60分 才能標註為「佈局股」

# 在 SCORING_SYSTEM.md 中（完整版）：
### 佈局股評分表
| 條件 | 標準 | 分數 |
|------|------|------|
| 連續買超天數 | ≥3日 | +20分 |
| 累計買超量 | >5K張 | +20分 |
（完整表格...）
```

### 情況 D：新增產業對照

**範例**：新增次產業展開表

```markdown
# 在 CLAUDE.md 中（關鍵提醒）：
**🚨 v5.7**：費半利多時，**必須掃描全部5個次產業**

# 在 INDUSTRY_NEWS_MAPPING.md 中（完整清單）：
| 次產業 | 代表股票 | 說明 |
|--------|---------|------|
| ①晶圓代工 | 台積電、聯電、世界先進 | 費半直接受惠 |
（完整5個次產業...）
```

---

## 四、CLAUDE.md 精簡技巧

### 1. 使用參考連結取代詳細內容

**Before（冗長）**：
```markdown
### 投信評分標準（20分）
| 條件 | 分數 |
|------|------|
| 買超 >10K 且連續≥3日 | 18-20 |
| 買超 >10K | 14-17 |
| 買超 5K-10K | 10-13 |
| 買超 <5K | 6-9 |
| 賣超 | 0-5 |
```

**After（精簡）**：
```markdown
### Step 5: 五維度評分
詳細評分標準 → `docs/reference/SCORING_SYSTEM.md`
```

### 2. 保留「觸發條件」，移除「執行細節」

**CLAUDE.md 保留**：
```markdown
**Step 4.3: 籌碼深度分析**
對 TOP50 篩選出的候選股，做籌碼深度分析：
```bash
python3 scripts/chip_analysis.py 2883 2887 2303
```
```

**TOOLS_GUIDE.md 放詳細**：
```markdown
### chip_analysis.py 完整說明
（參數、輸出格式、範例...）
```

### 3. 歷史教訓只保留「規則」，移除「故事」

**CLAUDE.md 保留**：
```markdown
**⚠️ 警告**：連續買超>5日 且 單日買超>30K → 警惕獲利了結
```

**HISTORICAL_LESSONS.md 放詳細**：
```markdown
### 力積電反轉案例（2025-12-10）
- 背景：連續狂買+50K...
- 結果：隔日反轉-20K...
- 教訓：...
```

---

## 五、版本更新檢查清單

當更新 CLAUDE.md 版本時：

- [ ] 新增的「教訓」是否同步到 HISTORICAL_LESSONS.md？
- [ ] 新增的「評分規則」是否同步到 SCORING_SYSTEM.md？
- [ ] 新增的「工具」是否同步到 TOOLS_GUIDE.md？
- [ ] 新增的「產業對照」是否同步到 INDUSTRY_NEWS_MAPPING.md？
- [ ] CLAUDE.md 是否仍保持精簡（核心流程+參考連結）？
- [ ] 參考文件區塊是否更新連結？

---

## 六、目標行數

| 文件 | 目標行數 | 說明 |
|------|---------|------|
| CLAUDE.md | ~1500行 | 核心流程+規則提醒 |
| SCORING_SYSTEM.md | ~400行 | 評分系統完整版 |
| TOOLS_GUIDE.md | ~300行 | 工具使用指南 |
| INDUSTRY_NEWS_MAPPING.md | ~200行 | 產業對照表 |
| HISTORICAL_LESSONS.md | ~300行 | 教訓彙整 |

**總計**：~2700行（vs 原本 CLAUDE.md 3167行 + docs/ 分散文件）

---

## 七、實際操作範例

### 假設要新增 v5.8 更新

**Step 1**: 判斷更新內容
- 新工具 `sector_momentum.py` → TOOLS_GUIDE.md
- 新教訓「ETF輪動誤判」→ HISTORICAL_LESSONS.md
- 新流程 Step 1.9 → CLAUDE.md

**Step 2**: 更新 docs/reference/ 文件

**Step 3**: 更新 CLAUDE.md
- 在流程中新增 Step 1.9
- 在版本更新區塊新增 v5.8 摘要
- 確保有連結到 reference 文件

**Step 4**: Commit
```bash
git add CLAUDE.md docs/reference/
git commit -m "feat: v5.8 - 新增 sector_momentum 工具+ETF輪動教訓"
```

