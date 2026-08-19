# 外資資金流向預測（實驗性）

> 🚧 **測試階段。不屬於盤前／盤中／盤後正式流程，不得被 CLAUDE.md 的任何 Step 引用。**

## 這是什麼

記錄「對外資資金走向的預測」並事後機械驗證，用來累積這類預測**到底準不準**的樣本。
目前樣本數 = 1 批，**沒有任何 track record，結論不得用於實際交易決策**。

## 為什麼跟現有系統分開

| | 個股推薦（正式） | 資金流預測（本實驗） |
|---|---|---|
| 記錄檔 | `data/predictions/predictions.json` | `experiments/flow_forecast/forecasts.json` |
| 驗證器 | `scripts/update_predictions.py`、`settlement_checker.py` | `experiments/flow_forecast/verify.py` |
| 準確率統計 | `settled_accuracy`（567 筆、56.4%） | 獨立計算，**不進入** `settled_accuracy` 分母 |

混在一起會有兩個問題：污染既有的個股準確率統計；以及讓未驗證的假說看起來像已驗證的規則。

## 用法

```bash
python3 experiments/flow_forecast/verify.py --dry-run   # 只看不寫
python3 experiments/flow_forecast/verify.py             # 驗證到期項目，寫回 result
```

驗證器只**讀取** `data/cache/twse_t86_*.json` 與 TWSE／Yahoo 公開 API，
**不寫入**任何 `data/YYYY-MM-DD/` 或 `data/tracking/` 的流程檔案。

若量化預測 #1／#2 顯示「T86 快取不存在」，先跑：

```bash
python3 scripts/fetch_institutional_top30.py YYYYMMDD
```

## 畢業條件（何時才考慮併入正式流程）

全部滿足才討論，任一未達即維持實驗狀態：

1. 累積 **≥ 10 批**預測（約 2 個月）
2. 量化預測命中率 **顯著高於 50%**（非誤差範圍內）
3. 至少一次**預測失敗後有據以修正**的記錄（證明這套有學習能力，不是事後合理化）

## 已知限制

- 質性預測（#5~#10）需人工判定，驗證器只列出不自動結算
- 預測 #1 的「半導體／記憶體」族群判定用 `verify.py` 內建代碼表，非 `industry_chains.json`
- 無期貨未平倉資料源（repo 內沒有任何 futures/OI 腳本），外資期貨部位這塊完全是盲區
