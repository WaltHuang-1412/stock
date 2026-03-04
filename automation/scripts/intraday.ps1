# 盤中分析自動化腳本
# 排程時間：每日 12:30（週一到週五）
# 假日/週末自動跳過

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# === 設定 ===
$ProjectDir = "C:\Users\walter.huang\Documents\github\stock"
$Date = Get-Date -Format "yyyy-MM-dd"
$LogDir = "$ProjectDir\automation\logs"
$LogFile = "$LogDir\${Date}_intraday.log"

# === 暫停開關檢查 ===
if (Test-Path "$ProjectDir\automation\PAUSED") {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 排程已暫停（PAUSED 檔案存在），跳過"
    exit 0
}

# === 市場狀態判斷（台股行事曆）===
$MarketStatus = (python "$ProjectDir\scripts\check_market_status.py" --date $Date --mode intraday 2>$null).Trim()
if ($MarketStatus -ne "full") {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 台股休市，跳過盤中分析"
    exit 0
}

# === Auth 檢查：token 是否有效 ===
$env:CLAUDECODE = $null
$AuthCheck = claude auth status 2>&1 | Out-String
if ($AuthCheck -notmatch '"loggedIn":\s*true') {
    $msg = "排程失敗 ($Date 盤中): Claude auth token 過期，需重新登入 (claude login)"
    Write-Output "[ERROR] $msg"
    python "$ProjectDir\scripts\notify_line.py" $msg
    exit 1
}

# === 前置檢查：盤前分析是否完成 ===
$BeforeMarketFile = "$ProjectDir\data\$Date\before_market_analysis.md"
if (!(Test-Path $BeforeMarketFile)) {
    Write-Output "[ERROR] 盤前分析未完成，跳過盤中分析"
    Write-Output "缺少: $BeforeMarketFile"
    exit 1
}

# === 準備目錄 ===
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# === 記錄開始 ===
$StartTime = Get-Date
Write-Output "========================================" | Tee-Object -FilePath $LogFile
Write-Output "盤中分析自動化 - $Date" | Tee-Object -FilePath $LogFile -Append
Write-Output "開始時間: $(Get-Date -Format 'HH:mm:ss')" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

# === 執行 Claude Code（含重試機制）===
# 清除 CLAUDECODE 環境變數，避免巢狀 session 檢查
$env:CLAUDECODE = $null
Set-Location $ProjectDir
$Prompt = Get-Content "$ProjectDir\automation\prompts\intraday.md" -Raw -Encoding UTF8

$MaxRetries = 2
$RetryDelay = 120  # 秒
$MainOutputFile = "$ProjectDir\data\$Date\intraday_analysis.md"

for ($attempt = 1; $attempt -le ($MaxRetries + 1); $attempt++) {
    if ($attempt -gt 1) {
        Write-Output "" | Tee-Object -FilePath $LogFile -Append
        Write-Output "[RETRY] 第 $attempt 次嘗試（等待 ${RetryDelay} 秒後重跑）" | Tee-Object -FilePath $LogFile -Append
        Start-Sleep -Seconds $RetryDelay
        $env:CLAUDECODE = $null
    }

    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] Claude 執行中（第 $attempt 次）..." | Tee-Object -FilePath $LogFile -Append
    claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

    # 檢查主要輸出檔是否產生
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

# === 驗證輸出檔案 ===
Write-Output "" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
Write-Output "驗證輸出檔案" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

$RequiredFiles = @(
    "$ProjectDir\data\$Date\intraday_analysis.md"
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

# === 結果 ===
$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Output "" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
if ($AllExist) {
    Write-Output "盤中分析完成 (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
    # LINE 推送（Claude 分析時已產出 LINE 摘要檔）
    $SummaryFile = "$ProjectDir\data\$Date\intraday_line.txt"
    if ((Test-Path $SummaryFile) -and (Get-Item $SummaryFile).Length -gt 0) {
        python "$ProjectDir\scripts\notify_line.py" --file $SummaryFile
    } else {
        python "$ProjectDir\scripts\notify_line.py" "盤中分析完成 ($Date) 耗時$($Duration.ToString('hh\:mm\:ss'))，詳見 GitHub"
    }
} else {
    Write-Output "盤中分析有缺漏檔案！請檢查 log (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
    python "$ProjectDir\scripts\notify_line.py" "盤中分析失敗 ($Date) 有缺漏檔案，請檢查 log"
}
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
