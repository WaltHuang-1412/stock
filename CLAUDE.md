# 台股分析執行流程（v8.0 多因子版）

**版本**：v8.1.0
**更新日期**：2026-04-24
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
- 盤前：`data/YYYY-MM-DD/before_market_analysis.md` + `us_asia_markets.json` + `us_leader_alerts.json` + `tw_market_news.json` + `catalyst_preposition_scan.json` + `catalyst_theme_signals.json` + `revenue_check.json` + `eps_check.json` + `foreign_ratio_check.json` + `price_position_check.json` + `tracking_YYYY-MM-DD.json` + `before_market_line.txt`
- 盤中：`data/YYYY-MM-DD/intraday_analysis.md` + `intraday_detector.json` + `intraday_line.txt` + 更新 `tracking_YYYY-MM-DD.json`
- 盤後：`data/YYYY-MM-DD/after_market_analysis.md` + `after_market_line.txt` + 更新 `tracking_YYYY-MM-DD.json` + 更新 `predictions.json`

**如果檔案不存在 = 步驟未執行 = 違規**

---

## 📖 名詞速查表（防混淆）

**核心口訣：Track 產出股票、Module 產出分數。**

| 名稱 | 中文別名 | 類型 | 功能 | 輸出 |
|------|---------|------|------|------|
| **Track A** | 軌道A（法人軌） | 選股管道 | 從法人 TOP50 選股 | `tracking.json → recommendations` |
| **Track B** | 軌道B（時事軌） | 選股管道 | 從今日新聞/產業展開選股 | `tracking.json → track_b_recommendations` |
| **Module A** | 訊號A（預埋訊號） | 評分因子 | 法人已在買 + 股價未反映，加 **L3 +15 / L2 +10** 分 | `catalyst_preposition_scan.json` |
| **Module B** | 訊號B（催化訊號） | 評分因子 | 美股龍頭漲 + 台股還沒跟，加 **🟢早期 +5** 分 | `catalyst_theme_signals.json` |

**互動關係**：Module B 的 `preposition_candidates` 候選股，會從 **Track B 軌道**進入 Step 7 評分。所以兩者不完全獨立，但角色不同 — Module B 是「訊號來源」、Track B 是「評分入口」。

**書寫規範**（盤前/盤中/盤後 markdown 報告）：
- 提到 Track 時，寫成「**🛤️ 軌道A（法人）**」或「**🛤️ 軌道B（時事）**」
- 提到 Module 時，寫成「**📶 訊號A（預埋）**」或「**📶 訊號B（催化）**」
- 禁止只寫「B 表現如何」這種歧義用法，必須指明是軌道 B 還是訊號 B

---

## 📊 一、盤前分析流程（09:00 前執行）

**目標**：預測今日有機會的股票，給出明確進場策略

### 🔴 前置判斷：市場狀態（強制最先執行）

```bash
python3 scripts/check_market_status.py --date $(date +%Y-%m-%d) --mode before_market --verbose
```

| 輸出 | 意義 | 動作 |
|------|------|------|
| `full` | 台股開市 | 繼續 Step 0-10 完整流程 |
| `snapshot` | 台股休市，但美股有新交易日 | 改跑假日快照（`automation/prompts/holiday_snapshot.md`） |
| `skip` | 台股+美股都沒新交易日 | 不需執行，結束 |

盤中/盤後同理：`--mode intraday` / `--mode after_market`（只區分 `full` 或 `skip`）

---

### 🔴 Step 0: 建立 TodoWrite（強制第一步）

步驟清單：Step 1（國際市場）→ 1.5（龍頭預警）→ 2（台股時事）→ 3（即時股價）→ 4（歷史驗證）→ 5（法人TOP50）→ 5.5（Module A 預埋掃描）→ 5.7（Module B 催化主題）→ 模式追蹤器 → 營收/持股比/EPS季報查詢 → 6（雙軌候選）→ 7（五維度評分+多因子加減分）→ 8（籌碼分析）→ 9（產業分散）→ 10（建檔）

---

### 🔴 Step 1: 獲取國際市場數據（強制）

```bash
cd /c/Users/walter.huang/Documents/github/stock
python3 scripts/fetch_us_asia_markets.py > data/$(date +%Y-%m-%d)/us_asia_markets.json
```

**驗證**：✅ 必須生成 `us_asia_markets.json`，包含 NASDAQ、費半、WTI原油、輝達等 | ❌ 不存在 = 禁止繼續

---

### 🟢 Step 1.2: 累積摘要檢查（自動判斷）

```bash
python3 scripts/holiday_cumulative_summary.py --date $(date +%Y-%m-%d)
```

腳本自動判斷：距上一交易日≤1天 → 不產生摘要，直接跳過

**如果產生了 `cumulative_summary.json`**：
- 持續性「超強」→ Step 7 反轉降級（L3→L1, L4→L2）+ 時事+15分
- 持續性「強」→ 時事+10分
- 持續性「強利空」/「超強利空」→ 對應產業 -10/-15分

---

### 🔴 Step 1.5: 美股龍頭預警（強制）

```bash
python3 scripts/us_leader_alert.py --date $(date +%Y-%m-%d) --output-dir data/$(date +%Y-%m-%d)
```

**驗證**：✅ 必須生成 `us_leader_alerts.json` | ❌ 不存在 = 禁止繼續

**預警分級處理**（龍頭→台股對應定義在 `us_leader_alert.py`）：

| 等級 | 條件 | 動作 | 評分調整 |
|------|------|------|---------|
| **Level 3** | 龍頭股暴跌（觸及門檻） | 🚫 **直接排除，不進入評分** | N/A |
| **Level 2** | 龍頭股明顯下跌（-5% ~ 門檻） | ⚠️ 降級評分 | **-15分** |
| **Level 1** | 龍頭股小跌（-2% ~ -5%） | ℹ️ 提示注意 | **-5分** |
| **Level 0** | 龍頭股正常/上漲 | ✅ 不調整 | 0分 |

**重要**：一票否決優先級：龍頭預警 > 法人數據 > 產業邏輯。**禁止忽略 Level 3**（即使法人大買超也要排除）

---

### 🔴 Step 2: 獲取台股時事數據（強制）

```bash
python3 scripts/fetch_tw_market_news.py > data/$(date +%Y-%m-%d)/tw_market_news.json
```

**驗證**：✅ 必須生成 `tw_market_news.json` | ❌ 不存在 = 禁止繼續

---

### 🔴 Step 3: 即時股價查詢（推薦股票前執行）

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

---

### 🔴 Step 4: 歷史驗證 + 持有中追蹤（強制）

```bash
# 讀取昨日 tracking + 近7天 tracking 中 result="holding" 的股票
cat data/tracking/tracking_$(date -d yesterday +%Y-%m-%d).json
```

**多日追蹤結算制度**：

| 條件 | 判定 |
|------|------|
| 收盤價 ≥ 目標價 | ✅ **成功（success）** |
| 收盤價 ≤ 停損價 | ❌ **失敗（fail）** |
| 推薦後第10個交易日 | 收盤>推薦價=成功，≤推薦價=失敗 |
| 以上皆未發生 | 📍 **持有中（holding）**，不判定 |

**🔴 禁止當天判定成敗**：未觸停損就是 holding，繼續追蹤

**檢查項目**：
1. 已結算：成功/失敗統計 + 特徵延續/避開
2. 持有中：距目標/停損 + 法人態度 + 催化劑狀態 + 是否續推
3. 到期：滿10交易日以收盤價結算

---

### 🔴 Step 5: 法人 TOP50 掃描（強制）

```bash
python3 scripts/fetch_institutional_top30.py $(date -d yesterday +%Y%m%d)
```

**驗證**：✅ 完整 TOP50 買超+賣超，每檔含三大法人/投信/外資/5日漲幅 | ❌ 禁止只查部分

**層級**：TOP 1-20 優先評分 | TOP 21-35 強催化可納入 | TOP 36-50 觀察備用

---

### 🔴 Step 5.5: 催化預埋掃描（Module A，強制）

```bash
python3 scripts/catalyst_preposition_scan.py --date $(date +%Y-%m-%d) --lookback 7 --threshold 5
```

**驗證**：✅ 必須生成 `catalyst_preposition_scan.json` | ❌ 不存在 = 禁止繼續

**三層分級**：

| 層級 | 條件 | 倉位 |
|------|------|------|
| **🔥 L3 佈局完成** | 連3+天買超 + 動能<-30% + 漲幅<5% | 15-20% |
| **🟢 L2 早期佈局** | 連2+天買超（或≥6天）+ 動能<+50% + 漲幅<5% | 5-10% |
| **🟡 L1 態度轉變** | 在TOP50 + 漲幅<3% + 動能<+100% | 觀察 |
| **⚠️ 追高排除** | 動能>+100% | 不推薦 |

**Step 7 整合**：L3→+15分+強制評分（即使不在TOP20）| L2→+10分 | L1→不加分 | 追高→不評分（除非超強催化覆寫）

---

### 🔴 Step 5.7: 催化主題預警（Module B，強制）

**與 Module A 差異**：A = 法人已在買（跟法人）| B = 催化劑升溫但法人還沒買（搶在法人前面）

```bash
python3 scripts/catalyst_theme_detector.py --date $(date +%Y-%m-%d) --lookback 7
```

**驗證**：✅ 必須生成 `catalyst_theme_signals.json` | ❌ 不存在 = 禁止繼續

**催化劑成熟度**：

| 成熟度 | 條件 | 評分 |
|--------|------|------|
| 🟢 **早期** | 連漲 1-2 天 | +20 |
| 🟡 **中期** | 連漲 3-4 天 | +12 |
| 🔴 **成熟** | 連漲 5+ 天 | +3 |

**Step 7 整合**：🟢早期→時事+5分 | 🟡中期→標註 | 🔴成熟→標註追高風險 | 法人已進場→交 Module A | 已大漲→不進入

---

### 🔴 Step 6: 雙軌並行候選股篩選（強制）

#### 🔵 軌道 A：法人 TOP50（已在 Step 5 完成）

#### 🟢 軌道 B：時事驅動產業展開

**B-1**：查看 Step 1 + Step 2 數據，**動態判斷**產業方向（不限固定清單）：
- 費半 +2% → 半導體 | 油價 -2.54% → 塑化、航空 | 輝達 +5.87% → AI 伺服器
- 新聞出現的新題材也要展開
- 每方向至少 3-5 檔候選

**B-2**：候選股來源：
1. 法人 TOP50 中找該產業股票
2. Claude 知識補充相關股票
3. 可參考 `data/industry_chains.json` 補漏（非強制）

**B-3**：候選股跑 chip_analysis + reversal_alert 過濾
```bash
python3 scripts/chip_analysis.py [候選股...] --days 10
python3 scripts/reversal_alert.py [候選股...]
```

#### 🔄 合併去重

軌道 A + 軌道 B 候選股合併去重，進入 Step 7 評分。

**Module A 整合**：L3→🔥強制進入 | L2→🟢進入 | L1→🟡觀察 | 追高→❌排除

**Module B 整合**：
- 讀取 `catalyst_theme_signals.json` 的 `preposition_candidates`（前10檔）
- 候選股跑 chip_analysis + reversal_alert
- 篩選條件：Level 0-1 + 動能≤100% + 累計為正
- 🟢早期→+5分 | 🟡中期→標註 | 🔴成熟→標註追高風險
- **🔴 禁止跳過**：必須逐檔列出排除原因

**產業知識庫**（完整定義在 `data/industry_chains.json`）：
科技（10）：AI、半導體、記憶體、光通訊、網通、蘋果鏈、電動車、面板、衛星、AR/VR ｜ 傳統（5）：塑化、航空、鋼鐵、營建、生技 ｜ 金融（3）：金融、電信、綠能 ｜ 其他（2）：遊戲電競

---

### 🔴 Step 7: 五維度評分 + 反轉預警篩選（強制）

**對象**：Step 5 + Step 6 合併去重後的候選股

**🔴 強制評分規則**：
- **法人 TOP30 全部必須評分，不得跳過**
- **Step 6 Track B 時事展開的候選股全部必須評分**（不能只評 Module A/B）
- **Module A L3 股票必須評分**（與 TOP30 同等優先級）
- 評分後依總分排名，選出最終推薦 6-8 檔

**評分維度**：時事現況 25% | 法人數據 25% | 產業邏輯 20% | 技術面 15% | 價格位置 15%

---

**時事現況（25分）— 以 topic_tracker.md 催化劑等級為主依據**：

| 對應催化劑級別 | 基礎分 |
|---------------|-------|
| 🔴 超強催化（對應產業在🔴區） | 20-23 |
| 🟡 強催化 | 16-20 |
| 🟢 中度催化 | 12-16 |
| 無明顯催化對應 | 8-12 |

**加分（最多 +2，封頂 25）**：
- 美股對應龍頭單日 >+5% → +2
- 美股對應龍頭單日 +3% ~ +5% → +1
- 方向↑加速（Topic Tracker 標記升溫/加速）→ +1
- 多個超強催化共振（≥2 個對應產業在🔴）→ +1

**判斷「對應催化劑」**：
- 股票產業 → 對應到 topic_tracker.md 中的催化劑主題
- 例：2382 廣達（AI 伺服器）→ 對應「AI 伺服器與半導體供應鏈」🔴超強
- 例：2344 華邦電（DRAM）→ 對應「DRAM 與記憶體」🔴超強
- 一檔股票可能對應多個催化劑，取最強者

---

**產業邏輯（20分）— 以產業鏈位置 + 催化共振為依據**：

| 產業鏈位置 | 基礎分 |
|-----------|-------|
| 龍頭/核心（如廣達/台積電/緯創之於 AI 伺服器） | 16-20 |
| 二線/配套（如英業達/神達 ODM 代工二線） | 13-16 |
| 邊緣/題材股 | 8-13 |
| 無明顯產業定位 | 5-8 |

**加分（最多 +3，封頂 20）**：
- 龍頭多點共振（同產業鏈 ≥3 家美股龍頭 >+5%）→ +2
- 法說/財報近 7 天內明確催化 → +2
- 美股財報日曆 7 天內有對應公司（⚡催化）→ +1

**扣分**：
- 催化劑 x 營收交叉分析標註「⚠️營收未跟上」→ -3
- 產業僅 🟢中度催化或以下 → 基礎分自動對應低區間

---

**技術面（15分）— 以量價型態 + 籌碼健康度為依據**：

| 型態判斷 | 基礎分 |
|---------|-------|
| 反轉 Level 0 + 佈局完成（動能<-30% + 連買≥3 天）| 13-15 |
| 反轉 Level 0 + 佈局中（動能<0% 或連買 3-4 天）| 11-13 |
| 反轉 Level 0-1 + 正常型態 | 9-11 |
| 反轉 Level 1 + 單日爆量未漲 | 6-9 |
| 反轉 Level 2 以上或短線型態轉弱 | 3-6 |

**加分（封頂 15）**：
- 量價配合（上漲放量 或 整理縮量）→ +1

**扣分**：
- 短期跳水未回補 → -2
- 連續放量但股價未跟進（疑似出貨徵兆）→ -2

**注意**：技術面不與「動能一票否決」「反轉預警篩選」「月線價格位置」重複扣分 — 那些是獨立 modifier，本維度只做型態判斷。

---

**法人數據（25分）— 以 avg_rank（平均排名 = 張數排名+金額排名/2）為依據**：

| 平均排名 | 基礎分 |
|---------|-------|
| TOP10 (avg_rank ≤ 10) | 20-23分 |
| TOP11-20 | 16-20分 |
| TOP21-35 | 12-16分 |
| TOP36-50 | 8-12分 |
| 不在 TOP50 | 4-8分 |

**加分**：buy_ratio >20% +2 | 10-20% +1 | 外資+投信同步 +1 | 連買≥5天 +1（封頂 25）

**過量買超警告**（單日三大法人合計買超 ≥ 30K 張）：

| 條件 | 評分調整 | 說明 |
|------|---------|------|
| 單日 ≥ 30K + 連買 < 7天 | ⚠️ **-5分** + 標註「過量買超」 | 消息已公開，散戶追進風險 |
| 單日 ≥ 30K + 連買 ≥ 7天 | ✅ 不調整 | 長期佈局，非短線炒作 |
| 單日 ≥ 30K + Module A L3 | ✅ 不調整 | 預埋佈局完成，不受懲罰 |

> 依據：回測 29 交易日數據，30K+ 單日買超後 5 日勝率僅 35.2%（平均 -1.21%），遠低於微量佈局的 48.7%（+1.52%）。大量買超常為法人出貨前的最後一波，散戶跟進易被套。

**買賣天數比警告**：

| 10天賣超天數 | 評分調整 |
|-------------|---------|
| **≥ 7天** | 🔴 法人分數上限15分 |
| **6天** | ⚠️ -5分 |
| **≤ 5天** | ✅ 不調整 |

須綜合檢視三大法人合計、外資、投信三者的買賣天數與累計方向。

---

**營收加減分**（月頻數據，每月 10 號後更新）：

```bash
python3 scripts/check_revenue_yoy.py [候選股...]
```

| 條件 | 評分調整 | 說明 |
|------|---------|------|
| 營收年增 ≥30% + 近5日回檔 ≥2% | **+5分** | 基本面強+股價回檔=黃金買點 |
| 營收年增 ≥10% + 近5日回檔 ≥5% | **+5分** | 成長股深度回檔 |
| 營收連續衰退 ≥3個月 | **-5分** | 基本面惡化 |
| 其他 | 不調整 | |

> 依據：回測 176 檔股票，營收年增≥30% 後 20 日勝率 70.2%（+8.81%）；營收成長+近5日回檔2-5% 勝率 69.9%（+4.82%），為所有因子中最強訊號。

---

**EPS 季報加減分**（季頻數據，季報公布後更新）：

```bash
python3 scripts/check_eps_quarterly.py [候選股...]
```

| 條件 | 評分調整 | 說明 |
|------|---------|------|
| EPS YoY ≥ +50% | **+5分** | 高成長，盈利大幅改善 |
| EPS YoY +20% ~ +49% | **+3分** | 穩健成長 |
| EPS YoY -20% ~ +19% | 不調整 | 持平範圍 |
| EPS YoY ≤ -20% | **-3分** | 盈利衰退 |
| EPS 連續 2 季 YoY 負成長 | **-5分** | 盈利惡化（覆蓋上述） |
| 毛利率 QoQ 上升 ≥ +2pp | **+2分** | 獲利能力改善 |
| 毛利率 QoQ 下降 ≥ -3pp | **-2分** | 獲利能力惡化 |
| 無季報數據 | 不調整 | 跳過 |

**防護**：單檔合計上限 `[-5, +5]`，EPS + 毛利率加減分總和不超過此範圍。

結果存入 `data/YYYY-MM-DD/eps_check.json`。

---

**外資持股比加減分**（週頻數據，每週五更新）：

```bash
python3 scripts/check_foreign_ratio.py [候選股...]
```

| 條件 | 評分調整 | 說明 |
|------|---------|------|
| 外資持股比週增 >0.5% | **+5分** | 外資持續加碼，籌碼安定 |
| 外資持股比週減 ≥0.1% | **-3分** | 外資減碼，留意風險 |
| 其他（小增、持平、微減<0.1%） | 不調整 | 微減屬噪音，不扣分 |

> 依據：回測 60 檔股票 29 交易日，法人買+外資持股比大增(>0.5%) 勝率 57.5%（+2.51%）；持股比減少勝率僅 33.3%（-2.07%）。差距 +13.3% 為所有交叉因子中最大。

---

**反轉預警篩選**：

```bash
python3 scripts/reversal_alert.py [候選股...] > data/$(date +%Y-%m-%d)/reversal_alerts.json
```

| 預警等級 | 動作 | 評分調整 |
|---------|------|---------|
| **Level 4** | 🚫 直接排除 | N/A |
| **Level 3** | 🚫 直接排除 | N/A |
| **Level 2** | ⚠️ 降級 | -15分 |
| **Level 1** | ⚠️ 降級 | -5分 |
| **Safe** | ✅ 正常 | 0分 |

**驗證**：✅ 必須生成 `reversal_alerts.json` | ❌ 不存在 = 禁止繼續

---

**動能一票否決**：

| 動能區間 | 評分調整 | 策略 |
|---------|---------|------|
| **<-30%** | +15分 | 🔥 佈局完成 |
| -30% ~ 0% | +10分 | ✅ 佈局中 |
| 0% ~ +50% | 正常 | ⚠️ 小倉位 |
| +50% ~ +100% | -10分 | ⚠️ 謹慎 |
| **>+100%** | ❌ 直接排除 | 🚫 追高（見超強催化覆寫） |

**例外**：超強催化（費半>+3%、油價>+5%、Micron>+10%）| 單日爆買>30K | 用戶已持股

---

**超強催化覆寫（動能>100%不排除，改降級）**：

觸發條件（任一）：Topic Tracker 🔴超強區 | 美股龍頭單日>+5% | cumulative_summary「超強」

覆寫後：不扣分 | 倉位 5-10% | 停損 -5% | 標註「🔥 超強催化覆寫」

**禁止濫用**：條件不成立→仍排除 | 反轉L3-4→不受保護 | 5日>20%→不受保護

**🔴 準確率篩選（三項全通過才推薦）**：
1. **催化對齊**：在今日最強催化產業鏈中（Topic Tracker + us_asia_markets）
2. **法人沒出貨**：外資近5天≥0（chip_analysis.py）
3. **反轉 Level 0**（reversal_alert.py）

---

**「已大漲」規則**：
- 5日 >10% → 預設不評分 | 5日 5-10% → -10分
- **催化脈絡例外**：漲幅來自催化劑A，今日新增催化劑B → 可評分 -10分+小倉位
- 新催化認定：48小時內首次 + 直接相關 + Topic Tracker 強/超強
- 5日>20% / 反轉L3-4 → 不受例外保護 | 同樣須通過準確率篩選

---

**法人模式追蹤加減分**（每日盤前更新）：

讀取 `data/strategy/pattern_today.json`：

| 條件 | 評分調整 |
|------|---------|
| hot_patterns | **不加分**（僅標註參考，回測顯示 HOT 無預測力） |
| cold_patterns 勝率 ≤30% 且樣本 ≥5 | **-5分** |
| cold_patterns 勝率 31-40% 且樣本 ≥5 | **-3分** |
| worst_combos 勝率 ≤30% 且樣本 ≥5 | **-5分** |
| best_combos / hot | 僅標註，不加分 |
| 檔案不存在或超過 3 天 | 跳過，不扣 |

> 依據：回測驗證（前16天訓練→後17天測試），HOT 選股準確率 67% 低於基準 69%（無預測力），COLD 選股 33% 遠低於基準（有效避開虧損）。模式追蹤器適合「避開什麼」而非「追什麼」。

---

**催化劑 x 營收交叉分析**（market-intelligence 產出，僅標註不加減分）：

讀取 `market_intelligence.md` 中的「催化劑 x 營收交叉分析」：
- ⚠️ 營收未跟上 → **標註「⚠️營收未跟上」**（不扣分，營收加減分已由 check_revenue_yoy.py 處理）

---

**PTT 散戶輿情**（market-intelligence 產出，僅標註不加減分）：

讀取 `market_intelligence.md` 中的「PTT 股票板散戶輿情」：
- PTT 熱門討論 → **標註「散戶關注」**（不扣分）

---

**美股財報日曆**（僅標註不加減分）：

讀取 `market_intelligence.md` 中的「美股財報日曆」：
- 對應美股 7天內有財報 → **標註「⚡財報催化」**（不加分）

對應關係：TSM→台積電供應鏈 / NVDA→AI伺服器鏈 / MU→記憶體鏈 / AVGO→網通光通訊鏈 / INTC→封測鏈 / AAPL→蘋果鏈

---

**價格位置（15分）**（每日盤前查詢）：

```bash
python3 scripts/check_price_position.py [候選股代碼...]
```

**Step 1：MA20 基礎分（0-14）**

| vs MA20 | 基礎分 |
|---------|-------|
| >+15% | 14 |
| +5% ~ +15% | 12 |
| 0% ~ +5% | 10 |
| -5% ~ 0% | 7 |
| -10% ~ -5% | 4 |
| <-10% | 2 |

**Step 2：MA60 修正（-1 ~ +1），封頂 15**

| 條件 | 修正 | 說明 |
|------|------|------|
| 月線上 + 季線上 | **+1** | 雙線確認，趨勢最強 |
| 月線下 + 季線上 | **+1** | 短線回調，季線仍支撐 |
| 月線上 + 季線下 | **0** | 月線上但季線壓頂，偏弱反彈 |
| 月線下 + 季線下 | **-1** | 雙線惡化，趨勢最弱 |

> 依據：MA20 回測 282 筆，月線上 67.9% vs 月線下 60.4%，差距 7.5%。MA60 作為趨勢確認修正，±1 分。52 週高低位置回測無效，不採用。結果存入 `data/YYYY-MM-DD/price_position_check.json`（欄位 `adj` = 最終得分）。

---

**大盤局勢參考**（market-intelligence 產出 `market_regime.json`）：

| 局勢 | 影響 |
|------|------|
| 多頭/偏多 | Step 9 防禦比例可降低 |
| 修正 | Step 9 防禦比例提高 |
| 空頭/恐慌 | Step 9 防禦比例大幅提高，減少推薦檔數 |

---

**評分防護機制**：

| 規則 | 說明 |
|------|------|
| 法人數據維度上限 **30分** | 基礎分+所有加分不超過30 |
| 單檔總扣分上限 **-20分** | 避免多重扣分疊加導致負分 |
| 直接排除不受上限保護 | 反轉L3-4、動能>100% 仍直接排除 |

---

**單位備註**：T86 快取的 foreign/trust/dealer/total 單位為**千張**（即「張」）。chip_analysis.py 輸出的累計買超同為張。CLAUDE.md 中的「30K」= 30,000 張 = T86 值 30,000。

---

**推薦門檻**（v8.1 配分調整後，價格位置升為正式維度，基礎分上限由 90→100，門檻同步上調）：
- ≥90分 → 強烈推薦 15-20% ⭐⭐⭐⭐⭐
- 80-89分 → 推薦 10-15% ⭐⭐⭐⭐
- 70-79分 → 可考慮 5-10% ⭐⭐⭐
- <70分 / 動能>100%（無覆寫）/ 反轉L3-4 → 不推薦

---

### 🔴 Step 8: 籌碼深度分析 + 反轉預警確認（強制）

```bash
python3 scripts/chip_analysis.py [推薦股...] --days 10
python3 scripts/reversal_alert.py [推薦股...]
```

**檢查**：連續買超天數 | 累計淨買超 | 外資 vs 投信 | 籌碼動能 | 反轉預警等級

| 判斷 | 條件 | 反轉預警 | 建議 |
|------|------|---------|------|
| ✅ 佈局 | 連買≥5天+累計>0 | Level 0 | 可進場 |
| ✅ 買進 | 連買3-4天+累計>0 | Level 0-1 | 可進場 |
| 🟡 偏多 | 買多賣少但不連續 | Level 0-1 | 觀察 |
| ⚠️ 預警 | 動能減弱 | Level 1-2 | 降低倉位 |
| 🔴 出貨 | 累計賣超 | Level 3-4 | **移除推薦** |

---

### 🔴 Step 9: 產業分散檢查 + 動態防禦比例（強制）

**基本規則**：推薦 6-8 檔 | 單一產業 ≤50% | ≥3 個產業

**動態防禦比例**：

| VIX | 催化強度 | 防禦比例 | 進攻比例 |
|-----|---------|---------|---------|
| >30 | 無/弱 | 60-75% | 25-40% |
| >30 | 強/超強 | 25-40% | 60-75% |
| 20-30 | 無/弱 | 40-50% | 50-60% |
| 20-30 | 強/超強 | 15-25% | 75-85% |
| <20 | 任何 | 0-15% | 85-100% |

**催化強度**：超強=Topic Tracker 🔴區或龍頭>+5% | 強=🟡區或龍頭>+3% | 弱=🟢/⚪區

---

### 🔴 Step 10: 建檔（強制）

**建立以下檔案**：
1. `data/YYYY-MM-DD/before_market_analysis.md`
2. `data/tracking/tracking_YYYY-MM-DD.json`
3. `data/YYYY-MM-DD/before_market_line.txt`

**tracking.json 格式**：
```json
{
  "date": "2026-02-02",
  "settings": {
    "stop_loss_pct": -10,
    "settlement_days": 10
  },
  "recommendations": [
    {
      "stock_code": "2303",
      "stock_name": "聯電",
      "industry": "半導體",
      "recommend_price": 52.5,
      "target_price": 58.0,
      "stop_loss_pct": -10,
      "stop_loss": 47.25,
      "settlement_days": 10,
      "position": "15-20%",
      "score": 88,
      "reason": "費半+2%、外資+43K、AI 需求"
    }
  ]
}
```

**🔴 停損計算規則**：
- `stop_loss = recommend_price × (1 + stop_loss_pct / 100)`
- `stop_loss_pct` 和 `settlement_days` 為必填欄位
- 每天盤前讀取 tracking.json 時，必須用 `stop_loss_pct` 重算 `stop_loss`，不得沿用舊的絕對價格
- 當前設定：盤前推薦 `stop_loss_pct = -10`、盤中推薦 `stop_loss_pct = -5`、`settlement_days = 10`

**LINE 摘要**（≤5000字元）：推薦股完整資訊 + 今日注意事項

**驗證**：✅ 三個檔案都存在 + tracking.json 含所有推薦 + LINE ≤5000字元

---

## 📊 二、盤中分析流程（12:30 執行）

**目標**：追蹤推薦股表現 + 發現盤中新機會 + 尾盤策略

### 🔴 Step 0: TodoWrite

步驟：Step 1（前置檢查）→ 2（Track A 追蹤+出場）→ 2.5（盤中偵測器）→ 3（Track B 候選篩選）→ 3.5（Track B 評分+推薦）→ 4（整合輸出）→ 5（建檔）

---

### 🔴 Step 1: 前置檢查

```bash
ls data/tracking/tracking_$(date +%Y-%m-%d).json
```
不存在 → 禁止執行，先跑盤前

---

### 🔴 Step 2: Track A 推薦股追蹤 + 出場訊號（強制）

```bash
python3 scripts/exit_signal_checker.py [推薦股...] --cost [推薦價]
python3 scripts/chip_analysis.py [推薦股...] --days 10
python3 scripts/reversal_alert.py [推薦股...]
```

**出場訊號（任一觸發 → 🛑 強制停損，無例外）**：

| 條件 | 觸發標準 |
|------|---------|
| 觸及停損價 | 盤中/收盤 < 停損價 |
| 連續重挫 | 2天累計跌幅 > -10% |
| 法人反轉 | Level 3-4 |

**尾盤策略**：✅ 續抱 | 🛑 強制停損

---

### 🔴 Step 2.5: 盤中法人續買偵測（強制）

```bash
python3 scripts/intraday_institutional_detector.py
```

偵測邏輯：昨天法人連買 ≥2 天的股票，今天盤中量比 ≥1.2 + 漲幅 <5% → 法人可能正在續買

**驗證**：✅ 必須生成 `intraday_detector.json` | ❌ 不存在 = 禁止繼續

| 訊號強度 | 條件 | 動作 |
|---------|------|------|
| 強訊號 ≥60 分 | 連買多天+量比高+TOP30+未反映 | **必須加入 Track B 候選，評分+5** |
| 中訊號 40-59 分 | 部分條件符合 | 觀察，不強制進入 |

---

### 🔴 Step 3: Track B 候選股篩選（強制）

**篩選**：法人買超>5K 或 avg_rank TOP30 + 今日漲幅<3% + 不在 Track A + **偵測器強訊號**

```bash
python3 scripts/chip_analysis.py [股票清單] --days 10
python3 scripts/reversal_alert.py [股票清單]
```

**🔴 只找還沒漲的，禁止列已反映的股票當結論**

---

### 🔴 Step 3.5: Track B 五維度評分 + 盤中新推薦（強制）

與盤前 Step 7 相同五維度評分

**篩選條件**（全部通過）：≥75分 + 反轉 Level 0-1 + 動能≤100% + 今日漲幅<3%

| 項目 | 盤中推薦 | 盤前推薦 |
|------|---------|---------|
| 最多檔數 | 3 檔 | 6-8 檔 |
| 最低分數 | ≥75 | ≥65 |
| 倉位上限 | 5-10% | 15-20% |
| 停損 | -5% | -10% |

無符合條件時標註「今日無盤中新推薦」

---

### 🔴 Step 4: 雙軌整合輸出

Track A 狀態表（推薦價/盤中價/漲跌%/策略）+ Track B 盤中推薦表（如有）+ 停損觸發詳情

---

### 🔴 Step 5: 建檔

1. `data/YYYY-MM-DD/intraday_analysis.md`
2. 更新 `data/tracking/tracking_YYYY-MM-DD.json`（盤中價格 + `track_b_recommendations` + `track_b_observations`）
3. `data/YYYY-MM-DD/intraday_line.txt`（≤5000字元）

---

## 📊 三、盤後分析流程（14:30 後執行）

**目標**：驗證推薦準確率 + 預測明日機會

### 🔴 Step 0: TodoWrite

步驟：Step 1（前置檢查）→ 2（Track A 驗證）→ 3（流程缺陷檢討）→ 4（更新 predictions.json）→ 5（明日預測）→ 6（建檔）

---

### 🔴 Step 1: 前置檢查

```bash
ls data/$(date +%Y-%m-%d)/intraday_analysis.md
```
不存在 → 禁止執行，先跑盤中

---

### 🔴 Step 2: Track A 追蹤更新 + 結算（強制）

**🔴 不再當天判定成敗**。盤後只做：更新收盤價 + 結算已觸及目標/停損的

```bash
cat data/tracking/tracking_$(date +%Y-%m-%d).json
python3 scripts/holdings_pressure_analysis.py [停損股...]
```

**結算規則**：收盤≥目標→success | 收盤≤停損→fail | 都沒觸→holding | 滿10日→收盤 vs 推薦價

**持股壓力等級**：

| 賣超佔持股比例 | 壓力 | 操作 |
|-------------|------|------|
| >10% | 🔴 高壓 | 避開同類 |
| 5-10% | 🟠 中高壓 | 謹慎 |
| 2-5% | 🟡 中壓 | 小倉位 |
| 0-2% | ⚪ 低壓 | 正常 |
| <0% | 🟢 吸籌 | 優先推薦 |

**🔴 禁止**：禁止對 holding 判定成敗 | 禁止當天收盤<推薦價就標 fail | holding 不計入準確率分母

---

### 🔴 Step 3: 流程缺陷檢討（強制）

**核心：不做事後諸葛，只找可修復的流程缺陷**
- 哪個步驟出問題？能否修改規則修復？
- **禁止**列「XX 漲了好可惜」| 禁止建議「下次更大膽」

---

### 🔴 Step 4: 更新 predictions.json（強制）

每日 key=日期，包含 `predictions[]`（symbol/name/recommend_price/target_price/stop_loss/result/settled_date/settled_price/holding_days）
- result：`"success"` / `"fail"` / `"holding"`（holding 不計入準確率）
- 頂層：`settled_accuracy` = success/(success+fail)、`settled_count`、`holding_count`

---

### 🔴 Step 5: 明日預測（強制）

基於今日發現：延續成功模式、避開失敗模式、推薦 6-8 檔

---

### 🔴 Step 6: 建檔（強制）

1. `data/YYYY-MM-DD/after_market_analysis.md`
2. 更新 `data/tracking/tracking_YYYY-MM-DD.json`（`actual_close` + `result` + `fail_reason`/`holding_status`）
3. 更新 `data/predictions/predictions.json`
4. `data/YYYY-MM-DD/after_market_line.txt`（≤5000字元）

**tracking.json 規則**：
- result: success/fail/holding
- fail 必須補 `fail_reason` | holding 必須補 `holding_status`
- 必須含 `tomorrow_recommendations` + `removed_stocks` 陣列
- **🔴 禁止當天就設 fail（除非真的觸停損）**
- **🔴 每檔推薦必須含 `stop_loss_pct` 和 `settlement_days` 欄位**
- **🔴 `stop_loss` 必須從 `stop_loss_pct` 計算，不得手動填寫或沿用舊值**

---

## 🚨 違規處理

- 跳過步驟 → 立即停止、回到該步驟重新執行
- 編造數據 → 承認錯誤、重新執行腳本、記錄到 predictions.json

---

**文件導航**：`docs/README.md` | 歷史教訓：`docs/HISTORICAL_LESSONS.md` | 產業鏈：`data/industry_chains.json`

**最後更新**：2026-04-24
**版本**：v8.1.0
