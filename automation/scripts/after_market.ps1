# 盤後分析自動化腳本
# 排程時間：每日 14:30（週一到週五）
# 假日/週末自動跳過

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# === 設定 ===
$ProjectDir = "C:\Users\walter.huang\Documents\github\stock"
$Date = Get-Date -Format "yyyy-MM-dd"
$LogDir = "$ProjectDir\automation\logs"
$LogFile = "$LogDir\${Date}_after_market.log"

# === 暫停開關檢查 ===
if (Test-Path "$ProjectDir\automation\PAUSED") {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 排程已暫停（PAUSED 檔案存在），跳過"
    exit 0
}

# === 週末檢查 ===
$DayOfWeek = (Get-Date).DayOfWeek
if ($DayOfWeek -eq 'Saturday' -or $DayOfWeek -eq 'Sunday') {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 週末，跳過盤後分析"
    exit 0
}

# === 台股假日檢查（假日不跑盤後） ===
$HolidayFile = "$ProjectDir\automation\holidays.json"
if (Test-Path $HolidayFile) {
    $Holidays = Get-Content $HolidayFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $Year = (Get-Date).Year.ToString()
    if ($Holidays.holidays.PSObject.Properties.Name -contains $Year) {
        $HolidayDates = $Holidays.holidays.$Year | ForEach-Object { $_.date }
        if ($HolidayDates -contains $Date) {
            $HolidayName = ($Holidays.holidays.$Year | Where-Object { $_.date -eq $Date }).name
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 台股休市 ($HolidayName)，跳過盤後分析"
            exit 0
        }
    }
}

# === 前置檢查：盤中分析是否完成 ===
$IntradayFile = "$ProjectDir\data\$Date\intraday_analysis.md"
if (!(Test-Path $IntradayFile)) {
    Write-Output "[ERROR] 盤中分析未完成，跳過盤後分析"
    Write-Output "缺少: $IntradayFile"
    exit 1
}

# === 準備目錄 ===
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# === 記錄開始 ===
$StartTime = Get-Date
Write-Output "========================================" | Tee-Object -FilePath $LogFile
Write-Output "盤後分析自動化 - $Date" | Tee-Object -FilePath $LogFile -Append
Write-Output "開始時間: $(Get-Date -Format 'HH:mm:ss')" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

# === 執行 Claude Code ===
# 清除 CLAUDECODE 環境變數，避免巢狀 session 檢查
$env:CLAUDECODE = $null
Set-Location $ProjectDir
$Prompt = Get-Content "$ProjectDir\automation\prompts\after_market.md" -Raw -Encoding UTF8
claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

# === 驗證輸出檔案 ===
Write-Output "" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
Write-Output "驗證輸出檔案" | Tee-Object -FilePath $LogFile -Append
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append

$RequiredFiles = @(
    "$ProjectDir\data\$Date\after_market_analysis.md",
    "$ProjectDir\data\predictions\predictions.json"
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
    Write-Output "盤後分析完成 (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
} else {
    Write-Output "盤後分析有缺漏檔案！請檢查 log (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
}
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
