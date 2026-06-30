# 持倉出場監控
# 排程時間：每日 09:00（週一到週五）
# 持續監控到收盤 13:30，每 5 分鐘檢查一次

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectDir = "C:\Users\walter.huang\Documents\github\stock"
$Date = Get-Date -Format "yyyy-MM-dd"
$LogDir = "$ProjectDir\automation\logs"
$LogFile = "$LogDir\${Date}_holdings_monitor.log"

# 暫停開關
if (Test-Path "$ProjectDir\automation\PAUSED") {
    exit 0
}

# 週末跳過
$DayOfWeek = (Get-Date).DayOfWeek
if ($DayOfWeek -eq "Saturday" -or $DayOfWeek -eq "Sunday") {
    exit 0
}

# 假日跳過（用 check_market_status.py）
$MarketStatus = (python "$ProjectDir\scripts\check_market_status.py" --date $Date --mode intraday 2>$null).Trim()
if ($MarketStatus -eq "skip") {
    exit 0
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 持倉監控啟動" | Tee-Object -FilePath $LogFile

$env:CLAUDECODE = $null
python "$ProjectDir\scripts\holdings_exit_monitor.py" --loop 2>&1 | Tee-Object -FilePath $LogFile -Append

Write-Output "[$(Get-Date -Format 'HH:mm:ss')] 持倉監控結束" | Tee-Object -FilePath $LogFile -Append
