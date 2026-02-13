# 台股分析自動排程安裝腳本
# 用法：以系統管理員身分執行 PowerShell，然後執行此腳本
#
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   .\automation\install_schedule.ps1
#

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectDir = "C:\Users\walter.huang\Documents\github\stock"

Write-Output "========================================"
Write-Output "台股分析自動排程安裝器"
Write-Output "========================================"
Write-Output ""

# === 定義排程任務 ===
$Tasks = @(
    @{
        Name        = "Stock_BeforeMarket"
        Description = "台股盤前分析 (08:30)"
        Time        = "08:30"
        Script      = "before_market.ps1"
    },
    @{
        Name        = "Stock_Intraday"
        Description = "台股盤中分析 (12:30)"
        Time        = "12:30"
        Script      = "intraday.ps1"
    },
    @{
        Name        = "Stock_AfterMarket"
        Description = "台股盤後分析 (14:30)"
        Time        = "14:30"
        Script      = "after_market.ps1"
    }
)

foreach ($task in $Tasks) {
    $ScriptPath = "$ProjectDir\automation\scripts\$($task.Script)"

    # 檢查腳本是否存在
    if (!(Test-Path $ScriptPath)) {
        Write-Output "[ERROR] 腳本不存在: $ScriptPath"
        continue
    }

    # 移除舊排程（如果存在）
    $existing = Get-ScheduledTask -TaskName $task.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $task.Name -Confirm:$false
        Write-Output "[更新] 移除舊排程: $($task.Name)"
    }

    # 建立動作：用 PowerShell 執行腳本
    $Action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
        -WorkingDirectory $ProjectDir

    # 建立觸發器：每日指定時間
    $Trigger = New-ScheduledTaskTrigger -Daily -At $task.Time

    # 設定：電腦喚醒後補執行、允許手動執行
    $Settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -DontStopOnIdleEnd `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    # 註冊排程任務
    Register-ScheduledTask `
        -TaskName $task.Name `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description $task.Description `
        -RunLevel Limited

    Write-Output "[OK] 已建立排程: $($task.Name) @ $($task.Time)"
}

Write-Output ""
Write-Output "========================================"
Write-Output "安裝完成！已建立 $($Tasks.Count) 個排程任務"
Write-Output ""
Write-Output "管理方式："
Write-Output "  查看排程：Get-ScheduledTask -TaskName 'Stock_*'"
Write-Output "  手動執行：Start-ScheduledTask -TaskName 'Stock_BeforeMarket'"
Write-Output "  移除全部：.\automation\uninstall_schedule.ps1"
Write-Output "  查看 log：ls .\automation\logs\"
Write-Output "========================================"
