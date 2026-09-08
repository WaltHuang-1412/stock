# 盤前分析自動化腳本
# 排程時間：每日 08:30（週一到週五）
# 市場狀態由 check_market_status.py 判斷：full / snapshot / skip

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# === 設定 ===
$ProjectDir = "C:\Users\walter.huang\Documents\github\stock"
$Date = Get-Date -Format "yyyy-MM-dd"
$LogDir = "$ProjectDir\automation\logs"
$LogFile = "$LogDir\${Date}_before_market.log"

# === 暫停開關檢查 ===
if (Test-Path "$ProjectDir\automation\PAUSED") {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 排程已暫停（PAUSED 檔案存在），跳過"
    exit 0
}

# === 市場狀態判斷（台股+美股行事曆）===
$MarketStatus = (python "$ProjectDir\scripts\check_market_status.py" --date $Date --mode before_market 2>$null).Trim()

if ($MarketStatus -eq "skip") {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 台股休市且美股無新交易日，跳過"
    exit 0
}

# === Auth 檢查：token 是否有效（含 retry，避免開機初期網路未就緒）===
$env:CLAUDECODE = $null
$AuthOK = $false
for ($i = 1; $i -le 3; $i++) {
    $AuthCheck = claude auth status 2>&1 | Out-String
    if ($AuthCheck -match '"loggedIn":\s*true') {
        $AuthOK = $true
        break
    }
    if ($i -lt 3) { Start-Sleep -Seconds 30 }
}
if (-not $AuthOK) {
    $msg = "排程失敗 ($Date 盤前): Claude auth token 過期，需重新登入 (claude login)"
    Write-Output "[ERROR] $msg"
    python "$ProjectDir\scripts\notify_line.py" $msg
    exit 1
}

# === 準備目錄 ===
New-Item -ItemType Directory -Force -Path "$ProjectDir\data\$Date" | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $ProjectDir

if ($MarketStatus -eq "snapshot") {
    # ========== 假日輕量模式：只抓美股快照 ==========
    $StartTime = Get-Date
    Write-Output "========================================" | Tee-Object -FilePath $LogFile
    Write-Output "假日美股快照 - $Date" | Tee-Object -FilePath $LogFile -Append
    Write-Output "開始時間: $(Get-Date -Format 'HH:mm:ss')" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

    $Prompt = Get-Content "$ProjectDir\automation\prompts\holiday_snapshot.md" -Raw -Encoding UTF8

    $MaxRetries = 2
    $RetryDelay = 120
    $MainOutputFile = "$ProjectDir\data\$Date\us_asia_markets.json"

    for ($attempt = 1; $attempt -le ($MaxRetries + 1); $attempt++) {
        if ($attempt -gt 1) {
            Write-Output "" | Tee-Object -FilePath $LogFile -Append
            Write-Output "[RETRY] 第 $attempt 次嘗試（等待 ${RetryDelay} 秒後重跑）" | Tee-Object -FilePath $LogFile -Append
            Start-Sleep -Seconds $RetryDelay
            $env:CLAUDECODE = $null
        }

        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Claude 執行中（第 $attempt 次）..." | Tee-Object -FilePath $LogFile -Append
        claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

        if (Test-Path $MainOutputFile) {
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 主要輸出檔已產生，成功" | Tee-Object -FilePath $LogFile -Append
            break
        } else {
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 主要輸出檔未產生" | Tee-Object -FilePath $LogFile -Append
            if ($attempt -le $MaxRetries) {
                Write-Output "[WARN] 將重試..." | Tee-Object -FilePath $LogFile -Append
            } else {
                Write-Output "[ERROR] 已達最大重試次數 ($MaxRetries)，放棄" | Tee-Object -FilePath $LogFile -Append
            }
        }
    }

    # 驗證
    Write-Output "" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
    $RequiredFiles = @(
        "$ProjectDir\data\$Date\us_asia_markets.json",
        "$ProjectDir\data\$Date\us_leader_alerts.json"
    )
    $AllExist = $true
    foreach ($f in $RequiredFiles) {
        if (Test-Path $f) {
            Write-Output "[OK] $f" | Tee-Object -FilePath $LogFile -Append
        } else {
            Write-Output "[MISSING] $f" | Tee-Object -FilePath $LogFile -Append
            $AllExist = $false
        }
    }

    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    Write-Output "" | Tee-Object -FilePath $LogFile -Append
    if ($AllExist) {
        Write-Output "假日快照完成 (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        $LineFile = "$ProjectDir\data\$Date\holiday_line.txt"
        if (Test-Path $LineFile) {
            python "$ProjectDir\scripts\notify_line.py" --file $LineFile 2>&1 | Tee-Object -FilePath $LogFile -Append
        } else {
            Write-Output "[WARN] holiday_line.txt 不存在，略過 LINE 推送" | Tee-Object -FilePath $LogFile -Append
        }
        Write-Output "" | Tee-Object -FilePath $LogFile -Append
        Write-Output "[git] 檢查未 commit 資料..." | Tee-Object -FilePath $LogFile -Append
        git -C $ProjectDir add data/ 2>&1 | Out-Null
        $GitStatus = git -C $ProjectDir status --porcelain 2>&1
        if ($GitStatus) {
            Write-Output "[git] 補 commit 未提交資料..." | Tee-Object -FilePath $LogFile -Append
            git -C $ProjectDir commit -m "auto: 假日快照 $Date（排程補 commit）" 2>&1 | Tee-Object -FilePath $LogFile -Append
        }
        Write-Output "[git] 推送至 remote..." | Tee-Object -FilePath $LogFile -Append
        git -C $ProjectDir push 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -eq 0) {
            Write-Output "[git] push 成功" | Tee-Object -FilePath $LogFile -Append
        } else {
            Write-Output "[git] push 失敗（exit $LASTEXITCODE），請手動確認" | Tee-Object -FilePath $LogFile -Append
        }
    } else {
        Write-Output "假日快照有缺漏！(耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        python "$ProjectDir\scripts\notify_line.py" "假日美股快照失敗 ($Date) 請檢查 log"
    }
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

} else {
    # ========== 正常模式：完整盤前分析 ==========
    $StartTime = Get-Date
    Write-Output "========================================" | Tee-Object -FilePath $LogFile
    Write-Output "盤前分析自動化 - $Date" | Tee-Object -FilePath $LogFile -Append
    Write-Output "開始時間: $(Get-Date -Format 'HH:mm:ss')" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

    # === 累積摘要檢查（交易日間隔 > 1 天時自動觸發）===
    python "$ProjectDir\scripts\holiday_cumulative_summary.py" --date $Date 2>&1 | Tee-Object -FilePath $LogFile -Append
    if (Test-Path "$ProjectDir\data\$Date\cumulative_summary.json") {
        Write-Output "[OK] 累積摘要已產生" | Tee-Object -FilePath $LogFile -Append
    }

    $Prompt = Get-Content "$ProjectDir\automation\prompts\before_market.md" -Raw -Encoding UTF8

    $MaxRetries = 2
    $RetryDelay = 120
    $MainOutputFile = "$ProjectDir\data\$Date\before_market_analysis.md"

    for ($attempt = 1; $attempt -le ($MaxRetries + 1); $attempt++) {
        if ($attempt -gt 1) {
            Write-Output "" | Tee-Object -FilePath $LogFile -Append
            Write-Output "[RETRY] 第 $attempt 次嘗試（等待 ${RetryDelay} 秒後重跑）" | Tee-Object -FilePath $LogFile -Append
            Start-Sleep -Seconds $RetryDelay
            $env:CLAUDECODE = $null
        }

        Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Claude 執行中（第 $attempt 次）..." | Tee-Object -FilePath $LogFile -Append
        claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

        if (Test-Path $MainOutputFile) {
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 主要輸出檔已產生，成功" | Tee-Object -FilePath $LogFile -Append
            break
        } else {
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 主要輸出檔未產生" | Tee-Object -FilePath $LogFile -Append
            if ($attempt -le $MaxRetries) {
                Write-Output "[WARN] 將重試..." | Tee-Object -FilePath $LogFile -Append
            } else {
                Write-Output "[ERROR] 已達最大重試次數 ($MaxRetries)，放棄" | Tee-Object -FilePath $LogFile -Append
            }
        }
    }

    # 驗證
    Write-Output "" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
    Write-Output "驗證輸出檔案" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

    $RequiredFiles = @(
        "$ProjectDir\data\$Date\before_market_analysis.md",
        "$ProjectDir\data\$Date\us_asia_markets.json",
        "$ProjectDir\data\$Date\us_leader_alerts.json"
    )

    $AllExist = $true
    foreach ($f in $RequiredFiles) {
        if (Test-Path $f) {
            Write-Output "[OK] $f" | Tee-Object -FilePath $LogFile -Append
        } else {
            Write-Output "[MISSING] $f" | Tee-Object -FilePath $LogFile -Append
            $AllExist = $false
        }
    }

    # LINE 摘要「訊號A／訊號B」機械式補寫（內容 100% 取自 Step 5.5／5.7 的 JSON，
    # 不依賴模型手抄；已存在則不動檔案）
    Write-Output "[ensure] 檢查 LINE 摘要訊號A／訊號B 區塊..." | Tee-Object -FilePath $LogFile -Append
    python "$ProjectDir\scripts\ensure_line_modules.py" --date $Date 2>&1 | Tee-Object -FilePath $LogFile -Append

    Write-Output "" | Tee-Object -FilePath $LogFile -Append
    Write-Output "[validate] 執行 validate_analysis.py before_market..." | Tee-Object -FilePath $LogFile -Append
    $ValidateOut = python "$ProjectDir\scripts\validate_analysis.py" before_market $Date 2>&1
    $ValidatePassed = ($LASTEXITCODE -eq 0)
    $ValidateOut | Tee-Object -FilePath $LogFile -Append

    # 驗證未過 → 讓 Claude 針對錯誤只做修復，再驗一次（不重跑全流程）
    if (-not $ValidatePassed) {
        Write-Output "" | Tee-Object -FilePath $LogFile -Append
        Write-Output "[validate] 未通過 → 啟動自動修復（最多 1 次）" | Tee-Object -FilePath $LogFile -Append
        $ErrLines = ($ValidateOut | Out-String)
        $FixPrompt = "盤前分析 $Date 的 validate_analysis.py 驗證未通過。驗證輸出：" + [Environment]::NewLine + "" + $ErrLines + "" + [Environment]::NewLine + "請只做修復，不要重跑整個盤前流程：" + [Environment]::NewLine + "1. 逐條修正 data/$Date/before_market_analysis.md、data/$Date/before_market_line.txt、data/tracking/tracking_$Date.json" + [Environment]::NewLine + "2. 內容一律取自今日既有的 JSON 與 md 報告，禁止編造；LINE 摘要須 <=5000 字元" + [Environment]::NewLine + "3. 若錯誤為「LINE 摘要缺少 Module A/B」，把 md 報告中的訊號A（預埋掃描）與訊號B（催化主題）兩節摘要抄進 LINE 摘要；即使 L3=0 或通過 0 檔也必須寫出並註明 0 檔" + [Environment]::NewLine + "4. 修完執行 python3 scripts/validate_analysis.py before_market $Date，必須顯示「可以 commit」才算完成" + [Environment]::NewLine + "5. 絕對禁止執行 scripts/notify_line.py"
        $env:CLAUDECODE = $null
        claude -p $FixPrompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

        Write-Output "[validate] 修復後重驗..." | Tee-Object -FilePath $LogFile -Append
        python "$ProjectDir\scripts\validate_analysis.py" before_market $Date 2>&1 | Tee-Object -FilePath $LogFile -Append
        $ValidatePassed = ($LASTEXITCODE -eq 0)
    }

    if ($ValidatePassed) {
        Write-Output "[validate] 通過" | Tee-Object -FilePath $LogFile -Append
    } else {
        Write-Output "[validate] 自動修復後仍未通過，資料保留但需人工修正；不推送盤前摘要" | Tee-Object -FilePath $LogFile -Append
        python "$ProjectDir\scripts\notify_line.py" "⚠️ before_market 驗證未通過 ($Date)，自動修復失敗，已停止推送盤前摘要，請檢查 log"
    }

    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    Write-Output "" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
    if ($AllExist) {
        Write-Output "盤前分析完成 (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        $LineFile = "$ProjectDir\data\$Date\before_market_line.txt"
        if (-not $ValidatePassed) {
            Write-Output "[LINE] 驗證未通過，略過盤前摘要推送（已另發警示）" | Tee-Object -FilePath $LogFile -Append
        } elseif (Test-Path $LineFile) {
            python "$ProjectDir\scripts\notify_line.py" --file $LineFile 2>&1 | Tee-Object -FilePath $LogFile -Append
        } else {
            Write-Output "[WARN] before_market_line.txt 不存在，略過 LINE 推送" | Tee-Object -FilePath $LogFile -Append
        }
        Write-Output "" | Tee-Object -FilePath $LogFile -Append
        Write-Output "[git] 檢查未 commit 資料..." | Tee-Object -FilePath $LogFile -Append
        git -C $ProjectDir add data/ 2>&1 | Out-Null
        $GitStatus = git -C $ProjectDir status --porcelain 2>&1
        if ($GitStatus) {
            Write-Output "[git] 補 commit 未提交資料..." | Tee-Object -FilePath $LogFile -Append
            git -C $ProjectDir commit -m "auto: 盤前分析 $Date（排程補 commit）" 2>&1 | Tee-Object -FilePath $LogFile -Append
        }
        Write-Output "[git] 推送至 remote..." | Tee-Object -FilePath $LogFile -Append
        git -C $ProjectDir push 2>&1 | Tee-Object -FilePath $LogFile -Append
        if ($LASTEXITCODE -eq 0) {
            Write-Output "[git] push 成功" | Tee-Object -FilePath $LogFile -Append
        } else {
            Write-Output "[git] push 失敗（exit $LASTEXITCODE），請手動確認" | Tee-Object -FilePath $LogFile -Append
        }
    } else {
        Write-Output "盤前分析有缺漏檔案！請檢查 log (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        python "$ProjectDir\scripts\notify_line.py" "盤前分析失敗 ($Date) 有缺漏檔案，請檢查 log"
    }
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
}
