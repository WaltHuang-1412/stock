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
$MarketStatus = (python "$ProjectDir\scripts\check_market_status.py" --date $Date --mode before_market --verbose 2>&1 | Select-Object -Last 1).Trim()

if ($MarketStatus -eq "skip") {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 台股休市且美股無新交易日，跳過"
    exit 0
}

# === 準備目錄 ===
New-Item -ItemType Directory -Force -Path "$ProjectDir\data\$Date" | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# === 清除 CLAUDECODE 環境變數，避免巢狀 session 檢查 ===
$env:CLAUDECODE = $null
Set-Location $ProjectDir

if ($MarketStatus -eq "snapshot") {
    # ========== 假日輕量模式：只抓美股快照 ==========
    $StartTime = Get-Date
    Write-Output "========================================" | Tee-Object -FilePath $LogFile
    Write-Output "假日美股快照 - $Date" | Tee-Object -FilePath $LogFile -Append
    Write-Output "開始時間: $(Get-Date -Format 'HH:mm:ss')" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

    $Prompt = Get-Content "$ProjectDir\automation\prompts\holiday_snapshot.md" -Raw -Encoding UTF8
    claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

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
        # LINE 推送假日摘要（Claude 產出 holiday_line.txt）
        $SummaryFile = "$ProjectDir\data\$Date\holiday_line.txt"
        if ((Test-Path $SummaryFile) -and (Get-Item $SummaryFile).Length -gt 0) {
            python "$ProjectDir\scripts\notify_line.py" --file $SummaryFile
        } else {
            python "$ProjectDir\scripts\notify_line.py" "假日美股快照完成 ($Date)"
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
    claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

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

    $EndTime = Get-Date
    $Duration = $EndTime - $StartTime
    Write-Output "" | Tee-Object -FilePath $LogFile -Append
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
    if ($AllExist) {
        Write-Output "盤前分析完成 (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        # LINE 推送（Claude 分析時已產出 LINE 摘要檔）
        $SummaryFile = "$ProjectDir\data\$Date\before_market_line.txt"
        if ((Test-Path $SummaryFile) -and (Get-Item $SummaryFile).Length -gt 0) {
            python "$ProjectDir\scripts\notify_line.py" --file $SummaryFile
        } else {
            python "$ProjectDir\scripts\notify_line.py" "盤前分析完成 ($Date) 耗時$($Duration.ToString('hh\:mm\:ss'))，詳見 GitHub"
        }
    } else {
        Write-Output "盤前分析有缺漏檔案！請檢查 log (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        python "$ProjectDir\scripts\notify_line.py" "盤前分析失敗 ($Date) 有缺漏檔案，請檢查 log"
    }
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
}
