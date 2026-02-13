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

# === 週末檢查 ===
$DayOfWeek = (Get-Date).DayOfWeek
if ($DayOfWeek -eq 'Saturday' -or $DayOfWeek -eq 'Sunday') {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 週末，跳過盤中分析"
    exit 0
}

# === 台股假日檢查（假日不跑盤中） ===
$HolidayFile = "$ProjectDir\automation\holidays.json"
if (Test-Path $HolidayFile) {
    $Holidays = Get-Content $HolidayFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $Year = (Get-Date).Year.ToString()
    if ($Holidays.holidays.PSObject.Properties.Name -contains $Year) {
        $HolidayDates = $Holidays.holidays.$Year | ForEach-Object { $_.date }
        if ($HolidayDates -contains $Date) {
            $HolidayName = ($Holidays.holidays.$Year | Where-Object { $_.date -eq $Date }).name
            Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 台股休市 ($HolidayName)，跳過盤中分析"
            exit 0
        }
    }
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

# === 執行 Claude Code ===
# 清除 CLAUDECODE 環境變數，避免巢狀 session 檢查
$env:CLAUDECODE = $null
Set-Location $ProjectDir
$Prompt = Get-Content "$ProjectDir\automation\prompts\intraday.md" -Raw -Encoding UTF8
claude -p $Prompt --dangerously-skip-permissions 2>&1 | Tee-Object -FilePath $LogFile -Append

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
    # LINE 推送盤中追蹤摘要
    $Summary = python "$ProjectDir\scripts\generate_line_summary.py" intraday $Date 2>&1
    if ($Summary) {
        python "$ProjectDir\scripts\notify_line.py" $Summary
    } else {
        python "$ProjectDir\scripts\notify_line.py" "盤中分析完成 ($Date) 耗時$($Duration.ToString('hh\:mm\:ss'))，詳見 GitHub"
    }
} else {
    Write-Output "盤中分析有缺漏檔案！請檢查 log (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
    python "$ProjectDir\scripts\notify_line.py" "盤中分析失敗 ($Date) 有缺漏檔案，請檢查 log"
}
Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
