# 台股分析執行流程（v8.0 多因子版）

**版本**：v8.0
**更新日期**：2026-04-09
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
- 盤前：`data/YYYY-MM-DD/before_market_analysis.md` + `us_asia_markets.json` + `us_leader_alerts.json` + `tw_market_news.json` + `catalyst_preposition_scan.json` + `catalyst_theme_signals.json` + `tracking_YYYY-MM-DD.json` + `before_market_line.txt`
- 盤中：`data/YYYY-MM-DD/intraday_analysis.md` + `intraday_line.txt` + 更新 `tracking_YYYY-MM-DD.json`
- 盤後：`data/YYYY-MM-DD/after_market_analysis.md` + `after_market_line.txt` + 更新 `tracking_YYYY-MM-DD.json` + 更新 `predictions.json`

**如果檔案不存在 = 步驟未執行 = 違規**

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

步驟清單：Step 1（國際市場）→ 1.5（龍頭預警）→ 2（台股時事）→ 3（即時股價）→ 4（歷史驗證）→ 5（法人TOP50）→ 5.5（Module A 預埋掃描）→ 5.7（Module B 催化主題）→ 6（雙軌候選）→ 7（五維度評分）→ 8（籌碼分析）→ 9（產業分散）→ 10（建檔）

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
- 持續性「超強」→ Step 6 展開 depth 3 + Step 7 反轉降級（L3→L1, L4→L2）+ 時事+15分
- 持續性「強」→ Step 6 展開 depth 2 + 時事+10分
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

**v7.9 多日追蹤結算制度**：

| 條件 | 判定 |
|------|------|
| 收盤價 ≥ 目標價 | ✅ **成功（success）** |
| 收盤價 ≤ 停損價 | ❌ **失敗（fail）** |
| 推薦後第7個交易日 | 收盤>推薦價=成功，≤推薦價=失敗 |
| 以上皆未發生 | 📍 **持有中（holding）**，不判定 |

**🔴 禁止當天判定成敗**：未觸停損就是 holding，繼續追蹤

**檢查項目**：
1. 已結算：成功/失敗統計 + 特徵延續/避開
2. 持有中：距目標/停損 + 法人態度 + 催化劑狀態 + 是否續推
3. 到期：滿7交易日以收盤價結算

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

**B-2**：動態展開（三層）：
1. 法人 TOP50 中找該產業股票
2. Claude 知識補充相關股票
3. `data/industry_chains.json` 補漏（可用 `expand_industry.py` 輔助）

**輸出**：`industry_expanded_stocks.json` + `industry_stock_codes.txt`
```json
{
  "date": "2026-02-26",
  "method": "dynamic",
  "industries_expanded": ["AI伺服器", "塑化"],
  "stocks": [
    {"code": "2382", "name": "廣達", "category": "AI伺服器", "tier": "tier_1", "source": "TOP50+催化劑"}
  ]
}
```

**🔴 規則**：不限 `industry_chains.json`、每方向至少 3-5 檔、代號寫入 `industry_stock_codes.txt`

**B-3**：批次籌碼分析
```bash
python3 scripts/chip_analysis.py $(cat data/$(date +%Y-%m-%d)/industry_stock_codes.txt | tr '\n' ' ') --days 10
```

#### 🔄 合併去重

```bash
python3 scripts/merge_candidates.py $(date +%Y-%m-%d)
```

**Module A 整合**：L3→🔥強制進入 | L2→🟢進入 | L1→🟡觀察 | 追高→❌排除

**Module B 整合**：
- 讀取 `catalyst_theme_signals.json` 的 `preposition_candidates`（前10檔）
- **必須加入 `industry_stock_codes.txt`，與 B 組一起跑 chip_analysis + reversal_alert**
- 篩選條件：Level 0-1 + 動能≤100% + 累計為正
- 🟢早期→+5分 | 🟡中期→標註 | 🔴成熟→標註追高風險
- **🔴 禁止跳過**：必須逐檔列出排除原因

**驗證**：✅ `industry_expanded_stocks.json` + `industry_stock_codes.txt` 必須存在

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

**評分維度**：時事現況 30% | 法人數據 30% | 產業邏輯 20% | 價格位置 10% | 技術面 10%

---

**法人數據（30分）— 以 avg_rank（平均排名 = 張數排名+金額排名/2）為依據**：

| 平均排名 | 基礎分 |
|---------|-------|
| TOP10 (avg_rank ≤ 10) | 25-30分 |
| TOP11-20 | 20-25分 |
| TOP21-35 | 15-20分 |
| TOP36-50 | 10-15分 |
| 不在 TOP50 | 5-10分 |

**加分**：buy_ratio >20% +5 | 10-20% +3 | 外資+投信同步 +2 | 連買≥5天 +2

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

**催化劑 x 營收交叉分析**（market-intelligence 產出）：

讀取 `market_intelligence.md` 中的「催化劑 x 營收交叉分析」：

| 支撐度 | 評分調整 | 說明 |
|--------|---------|------|
| ⚠️ 營收未跟上 | **-3分** | 催化劑熱但營收衰退，題材炒作風險 |
| 💪 強力支撐 | 不加分（標註參考） | 營收加分已由 check_revenue_yoy.py 處理 |
| ✅ 有支撐 / ➡️ 溫和 | 不調整 | |

---

**PTT 散戶輿情**（market-intelligence 產出）：

讀取 `market_intelligence.md` 中的「PTT 股票板散戶輿情」：

| 條件 | 評分調整 | 說明 |
|------|---------|------|
| PTT 熱門討論 + 今日漲幅 >3% | **-3分** | 散戶追高風險 |
| PTT 熱門討論但漲幅 ≤3% | 標註「散戶關注」不扣分 | |

---

**美股財報日曆加分**：

讀取 `market_intelligence.md` 中的「美股財報日曆」：

| 條件 | 評分調整 |
|------|---------|
| 對應美股 ⚡7天內有財報 | **+5分**（法說催化提前卡位）|
| 對應美股 🔜30天內有財報 | 標註，不加分 |

對應關係：TSM→台積電供應鏈 / NVDA→AI伺服器鏈 / MU→記憶體鏈 / AVGO→網通光通訊鏈 / INTC→封測鏈 / AAPL→蘋果鏈

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

**推薦門檻**：
- ≥85分 → 強烈推薦 15-20% ⭐⭐⭐⭐⭐
- 75-84分 → 推薦 10-15% ⭐⭐⭐⭐
- 65-74分 → 可考慮 5-10% ⭐⭐⭐
- <65分 / 動能>100%（無覆寫）/ 反轉L3-4 → 不推薦

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
  "recommendations": [
    {
      "stock_code": "2303",
      "stock_name": "聯電",
      "industry": "半導體",
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

**LINE 摘要**（≤5000字元）：推薦股完整資訊 + 今日注意事項

**驗證**：✅ 三個檔案都存在 + tracking.json 含所有推薦 + LINE ≤5000字元

---

## 📊 二、盤中分析流程（12:30 執行）

**目標**：追蹤推薦股表現 + 發現盤中新機會 + 尾盤策略

### 🔴 Step 0: TodoWrite

步驟：Step 1（前置檢查）→ 2（Track A 追蹤+出場）→ 3（Track B 候選篩選）→ 3.5（Track B 評分+推薦）→ 4（整合輸出）→ 5（建檔）

---

### 🔴 Step 1: 前置檢查

```bash
ls data/tracking/tracking_$(date +%Y-%m-%d).json
```
不存在 → 禁止執行，先跑盤前

---

### 🔴 Step 2: Track A 推薦股追蹤 + 出場訊號（強制）

```bash
python3 scripts/intraday_dual_track.py
python3 scripts/exit_signal_checker.py [推薦股...] --cost [推薦價]
```

**出場訊號（任一觸發 → 🛑 強制停損，無例外）**：

| 條件 | 觸發標準 |
|------|---------|
| 觸及停損價 | 盤中/收盤 < 停損價 |
| 連續重挫 | 2天累計跌幅 > -8% |
| 法人反轉 | Level 3-4 |

**尾盤策略**：✅ 續抱 | ➕ 加碼（回檔+法人續買+無出場訊號）| 🛑 強制停損

**回檔加碼驗證**（4項全通過才可）：法人力道未減>50% | 動能未減>30% | 反轉 Level 0 | 價格位階<80%

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
| 停損 | -5% | -8% |

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

**結算規則**：收盤≥目標→success | 收盤≤停損→fail | 都沒觸→holding | 滿7日→收盤 vs 推薦價

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

---

## 🚨 違規處理

- 跳過步驟 → 立即停止、回到該步驟重新執行
- 編造數據 → 承認錯誤、重新執行腳本、記錄到 predictions.json

---

**文件導航**：`docs/README.md` | 歷史教訓：`docs/HISTORICAL_LESSONS.md` | 產業鏈：`data/industry_chains.json`

**最後更新**：2026-04-09
**版本**：v8.0
