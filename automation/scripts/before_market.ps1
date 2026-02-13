# 盤前分析自動化腳本
# 排程時間：每日 08:30（週一到週五）
# 假日模式：自動切換為美股快照

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

# === 週末檢查 ===
$DayOfWeek = (Get-Date).DayOfWeek
if ($DayOfWeek -eq 'Saturday' -or $DayOfWeek -eq 'Sunday') {
    Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 週末，跳過"
    exit 0
}

# === 台股假日檢查 ===
$HolidayFile = "$ProjectDir\automation\holidays.json"
$IsHoliday = $false
if (Test-Path $HolidayFile) {
    $Holidays = Get-Content $HolidayFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $Year = (Get-Date).Year.ToString()
    if ($Holidays.holidays.PSObject.Properties.Name -contains $Year) {
        $HolidayDates = $Holidays.holidays.$Year | ForEach-Object { $_.date }
        if ($HolidayDates -contains $Date) {
            $HolidayName = ($Holidays.holidays.$Year | Where-Object { $_.date -eq $Date }).name
            $IsHoliday = $true
        }
    }
}

# === 準備目錄 ===
New-Item -ItemType Directory -Force -Path "$ProjectDir\data\$Date" | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# === 清除 CLAUDECODE 環境變數，避免巢狀 session 檢查 ===
$env:CLAUDECODE = $null
Set-Location $ProjectDir

if ($IsHoliday) {
    # ========== 假日輕量模式：只抓美股快照 ==========
    $StartTime = Get-Date
    Write-Output "========================================" | Tee-Object -FilePath $LogFile
    Write-Output "假日美股快照 - $Date ($HolidayName)" | Tee-Object -FilePath $LogFile -Append
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
        # LINE 通知
        $SnapshotFile = "$ProjectDir\data\$Date\holiday_snapshot.md"
        if (Test-Path $SnapshotFile) {
            python "$ProjectDir\scripts\notify_line.py" --file $SnapshotFile
        } else {
            python "$ProjectDir\scripts\notify_line.py" "假日美股快照完成 ($Date $HolidayName)"
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
        python "$ProjectDir\scripts\notify_line.py" "盤前分析完成 ($Date) 耗時$($Duration.ToString('hh\:mm\:ss'))，詳見 GitHub"
    } else {
        Write-Output "盤前分析有缺漏檔案！請檢查 log (耗時: $($Duration.ToString('hh\:mm\:ss')))" | Tee-Object -FilePath $LogFile -Append
        python "$ProjectDir\scripts\notify_line.py" "盤前分析失敗 ($Date) 有缺漏檔案，請檢查 log"
    }
    Write-Output "========================================" | Tee-Object -FilePath $LogFile -Append
}
