# GovProcu 일일 ETL Windows Task Scheduler 등록
# 사용자가 PowerShell 관리자 권한으로 실행:
#   .\deploy\scheduler\setup-windows-task.ps1

$projectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$pythonExe = (Get-Command python).Source
$etlScript = Join-Path $projectRoot "scripts\etl_daily.py"
$logPath = Join-Path $projectRoot "logs\etl.log"

# 매일 03:00 KST 실행
$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$etlScript`"" `
    -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger -Daily -At 3:00am

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName "GovProcuDailyETL" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "GovProcu 일일 낙찰 데이터 증분 ETL" `
    -Force

Write-Host "OK Windows Task Scheduler 등록 완료: GovProcuDailyETL"
Write-Host "   매일 03:00 실행, 로그: $logPath"
Write-Host ""
Write-Host "확인: schtasks /Query /TN GovProcuDailyETL"
Write-Host "삭제: schtasks /Delete /TN GovProcuDailyETL /F"
