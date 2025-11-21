# 📅 股票分析自動化排程設定指南

**目標**：自動化盤前、盤中、盤後數據查詢與提醒

---

## 🎯 排程任務總覽

| 時間 | 任務 | 說明 |
|------|------|------|
| **08:00** | 盤前數據查詢 | 查詢昨日法人數據、美股收盤，發送通知 |
| **12:30** | 盤中分析執行 | 自動執行intraday_analyzer_v2.py |
| **15:00** | 盤後數據查詢 | 查詢當日法人數據，發送通知 |

**⚠️ 重要**：
- 排程只負責「數據查詢」和「提醒」
- 實際「分析報告撰寫」仍需與Claude對話執行
- 因為分析需要判斷、推薦股票，無法完全自動化

---

## 🛠️ 方案A：macOS launchd（推薦）

### 優點
- macOS原生，穩定可靠
- 開機自動啟動
- 系統級排程，不需要Terminal開著

### 缺點
- 設定稍微複雜
- 需要管理plist文件

---

### 設定步驟

#### Step 1: 檢查文件是否存在

```bash
cd /Users/walter/Documents/GitHub/stock/automation

# 檢查配置文件
ls -la *.plist

# 應該看到：
# com.stock.before_market.plist
# com.stock.intraday.plist
```

---

#### Step 2: 設定執行權限

```bash
# 給Python腳本執行權限
chmod +x run_before_market.py

# 測試手動執行
python3 run_before_market.py
```

---

#### Step 3: 複製plist到系統目錄

```bash
# 複製盤前分析排程
cp com.stock.before_market.plist ~/Library/LaunchAgents/

# 複製盤中分析排程
cp com.stock.intraday.plist ~/Library/LaunchAgents/
```

---

#### Step 4: 載入排程

```bash
# 載入盤前分析排程
launchctl load ~/Library/LaunchAgents/com.stock.before_market.plist

# 載入盤中分析排程
launchctl load ~/Library/LaunchAgents/com.stock.intraday.plist
```

---

#### Step 5: 驗證排程是否啟用

```bash
# 檢查排程狀態
launchctl list | grep stock

# 應該看到：
# com.stock.before_market
# com.stock.intraday
```

---

### 測試排程

**手動觸發測試**：
```bash
# 測試盤前分析（不等到08:00）
launchctl start com.stock.before_market

# 測試盤中分析
launchctl start com.stock.intraday
```

**查看日誌**：
```bash
# 創建日誌目錄
mkdir -p /Users/walter/Documents/GitHub/stock/logs

# 查看盤前分析日誌
tail -f logs/before_market.log

# 查看錯誤日誌
tail -f logs/before_market.error.log
```

---

### 停用/移除排程

**暫停排程**：
```bash
# 停用盤前分析
launchctl unload ~/Library/LaunchAgents/com.stock.before_market.plist
```

**完全移除**：
```bash
# 停用並刪除
launchctl unload ~/Library/LaunchAgents/com.stock.before_market.plist
rm ~/Library/LaunchAgents/com.stock.before_market.plist
```

---

## 🛠️ 方案B：Python schedule（簡單）

### 優點
- 設定簡單，純Python
- 易於調試

### 缺點
- 需要Terminal持續開著
- 關機/休眠後停止

---

### 使用方式

#### Step 1: 安裝schedule庫

```bash
pip3 install schedule
```

---

#### Step 2: 創建排程腳本

**文件**：`automation/scheduler.py`

```python
import schedule
import time
from datetime import datetime
import subprocess

def run_before_market():
    """盤前分析任務"""
    print(f"[{datetime.now()}] 執行盤前數據查詢...")
    subprocess.run(['python3', 'automation/run_before_market.py'])

def run_intraday():
    """盤中分析任務"""
    print(f"[{datetime.now()}] 執行盤中分析...")
    subprocess.run(['python3', 'intraday_analyzer_v2.py'])

# 設定排程
schedule.every().day.at("08:00").do(run_before_market)
schedule.every().day.at("12:30").do(run_intraday)

print("📅 股票分析排程已啟動")
print("排程時間：")
print("- 08:00 盤前數據查詢")
print("- 12:30 盤中分析")
print("\n按 Ctrl+C 停止")

# 持續運行
while True:
    schedule.run_pending()
    time.sleep(60)  # 每分鐘檢查一次
```

---

#### Step 3: 執行排程

```bash
# 方式1：Terminal直接執行（需保持開啟）
python3 automation/scheduler.py

# 方式2：背景執行
nohup python3 automation/scheduler.py > logs/scheduler.log 2>&1 &

# 查看背景程序
ps aux | grep scheduler

# 停止背景程序
kill <PID>
```

---

## 🛠️ 方案C：cron（傳統）

### 優點
- Unix標準工具
- 簡單易用

### 缺點
- macOS可能需要額外權限設定
- 不如launchd穩定

---

### 使用方式

```bash
# 編輯crontab
crontab -e

# 加入以下內容：
0 8 * * 1-5 cd /Users/walter/Documents/GitHub/stock && python3 automation/run_before_market.py
30 12 * * 1-5 cd /Users/walter/Documents/GitHub/stock && python3 intraday_analyzer_v2.py

# 說明：
# 0 8 * * 1-5  = 每週一到週五早上08:00
# 30 12 * * 1-5 = 每週一到週五中午12:30

# 查看crontab
crontab -l

# 刪除crontab
crontab -r
```

---

## 📱 通知設定

### macOS 通知

**腳本已內建通知功能**：
- 數據查詢完成後自動發送通知
- 使用macOS原生通知中心
- 聲音提示：Glass

**通知內容**：
```
📊 盤前分析準備就緒
數據已更新，請執行盤前分析
```

---

### LINE 通知（進階）

**需要申請LINE Notify Token**：

1. 前往：https://notify-bot.line.me/
2. 登入並生成Token
3. 修改`run_before_market.py`加入：

```python
def send_line_notify(message):
    """發送LINE通知"""
    token = 'YOUR_LINE_NOTIFY_TOKEN'
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {token}'}
    data = {'message': message}

    import requests
    requests.post(url, headers=headers, data=data)

# 在main()最後加入
send_line_notify("📊 盤前分析準備就緒")
```

---

## 🎯 推薦使用流程

### 方式1：全自動提醒（推薦新手）

```
08:00 → launchd自動查詢數據 → macOS通知
      → 你打開Claude Code → 說「開始盤前分析」
      → Claude執行分析並撰寫報告

12:30 → launchd自動執行盤中分析 → 查看報告

15:00 → launchd自動查詢數據 → macOS通知
      → 你打開Claude Code → 說「開始盤後分析」
```

---

### 方式2：半自動（推薦進階）

```
早上起床 → 直接打開Claude Code → 說「開始盤前分析」
         → Claude自動查詢數據並分析

12:30 → 手動執行 python3 intraday_analyzer_v2.py

晚上   → 打開Claude Code → 說「開始盤後分析」
```

---

### 方式3：完全手動（目前模式）

```
需要分析時 → 打開Claude Code → 說「開始盤前/盤中/盤後分析」
          → Claude執行所有步驟
```

---

## 🚨 注意事項

### 1. 排程無法完全自動化分析

**原因**：
- 分析報告需要「判斷」和「推薦股票」
- 新系統強制要求「必須推薦3-5檔」
- 這些決策無法完全自動化，需要AI判斷

**排程只能做**：
- ✅ 自動查詢數據（法人、美股）
- ✅ 自動發送提醒通知
- ✅ 自動執行盤中分析工具（intraday_analyzer_v2.py）

**排程無法做**：
- ❌ 自動撰寫盤前分析報告
- ❌ 自動推薦股票
- ❌ 自動創建tracking.json

---

### 2. 電腦需要開機

**launchd/cron都要求**：
- macOS系統正在運行
- 如果關機/休眠 → 排程不執行

**解決方案**：
- 設定macOS「電源小憩」（允許休眠時執行排程）
- 或使用雲端伺服器（AWS/GCP）持續運行

---

### 3. 網路連線

**排程需要網路**：
- 查詢證交所API
- 查詢Yahoo Finance
- 發送LINE通知（若有）

---

## ✅ 快速開始（最簡單方式）

**推薦：方案B（Python schedule）**

```bash
# 1. 安裝schedule
pip3 install schedule

# 2. 測試手動執行
python3 automation/run_before_market.py

# 3. 啟動排程（保持Terminal開啟）
python3 automation/scheduler.py

# 4. 看到通知後，與Claude對話
# 說：「開始盤前分析」
```

---

## 🔧 故障排除

### 問題1：排程沒有執行

**檢查**：
```bash
# launchd
launchctl list | grep stock

# Python schedule
ps aux | grep scheduler

# cron
crontab -l
```

---

### 問題2：執行失敗

**查看日誌**：
```bash
# launchd
tail -f logs/before_market.error.log

# Python schedule
tail -f logs/scheduler.log

# cron
tail -f /var/log/system.log
```

---

### 問題3：通知沒有收到

**檢查macOS通知權限**：
1. 系統偏好設定 → 通知
2. 找到「終端機」或「Python」
3. 允許通知

---

## 📚 更多資源

- [macOS launchd官方文檔](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Python schedule文檔](https://schedule.readthedocs.io/)
- [LINE Notify API](https://notify-bot.line.me/doc/en/)

---

**最後更新**：2025-11-20
**版本**：v1.0
