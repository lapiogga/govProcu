# GovProcu 분기별 로그·감사 archive Windows Task Scheduler 등록
# 매 분기 1일 04:00 KST 실행 (1/1, 4/1, 7/1, 10/1)
# PowerShell 관리자 권한으로:
#   .\deploy\scheduler\setup-archive-task.ps1

$projectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$pythonExe = (Get-Command python).Source
$archiveScript = Join-Path $projectRoot "scripts\archive_logs.py"

$action = New-ScheduledTaskAction `
    -Execute $pythonExe `
    -Argument "`"$archiveScript`" --days 90" `
    -WorkingDirectory $projectRoot

# 매 분기 1일 04:00
$trigger = New-ScheduledTaskTrigger -Once -At 4:00am `
    -RepetitionInterval (New-TimeSpan -Days 90) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -StartWhenAvailable `
    -RestartCount 1 `
    -RestartInterval (New-TimeSpan -Minutes 30)

Register-ScheduledTask `
    -TaskName "GovProcuQuarterlyArchive" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "GovProcu 분기별 로그·audit_log archive (90일+)" `
    -Force

Write-Host "OK Windows Task Scheduler 등록 완료: GovProcuQuarterlyArchive"
Write-Host "   90일 주기로 04:00 실행, 90일+ 로그/감사 압축 + 이관"
Write-Host ""
Write-Host "확인: schtasks /Query /TN GovProcuQuarterlyArchive"
Write-Host "삭제: schtasks /Delete /TN GovProcuQuarterlyArchive /F"
Write-Host "수동 1회: python scripts\archive_logs.py --days 90 --dry-run"
