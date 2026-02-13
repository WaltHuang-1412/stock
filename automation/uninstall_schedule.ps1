# 台股分析自動排程移除腳本
# 用法：以系統管理員身分執行 PowerShell
#
#   .\automation\uninstall_schedule.ps1
#

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Output "========================================"
Write-Output "台股分析自動排程移除器"
Write-Output "========================================"
Write-Output ""

$TaskNames = @("Stock_BeforeMarket", "Stock_Intraday", "Stock_AfterMarket")

foreach ($name in $TaskNames) {
    $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
        Write-Output "[OK] 已移除: $name"
    } else {
        Write-Output "[SKIP] 不存在: $name"
    }
}

Write-Output ""
Write-Output "========================================"
Write-Output "移除完成"
Write-Output "========================================"
