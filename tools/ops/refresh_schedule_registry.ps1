param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

function Convert-ToIsoString {
    param([object]$Value)

    if ($null -eq $Value) {
        return ""
    }

    try {
        $dt = [datetime]$Value
    } catch {
        return [string]$Value
    }

    if ($dt.Year -lt 2000) {
        return ""
    }

    return $dt.ToString("yyyy-MM-ddTHH:mm:ss")
}

function Convert-TriggerInfo {
    param([object]$Trigger)

    $repetitionInterval = ""
    $repetitionDuration = ""
    if ($Trigger.Repetition) {
        $repetitionInterval = [string]$Trigger.Repetition.Interval
        $repetitionDuration = [string]$Trigger.Repetition.Duration
    }

    return [ordered]@{
        type = [string]$Trigger.CimClass.CimClassName
        enabled = [bool]$Trigger.Enabled
        start_boundary = Convert-ToIsoString $Trigger.StartBoundary
        end_boundary = Convert-ToIsoString $Trigger.EndBoundary
        days_interval = [int]($Trigger.DaysInterval | ForEach-Object { $_ })
        weeks_interval = [int]($Trigger.WeeksInterval | ForEach-Object { $_ })
        repetition_interval = $repetitionInterval
        repetition_duration = $repetitionDuration
        random_delay = [string]$Trigger.RandomDelay
    }
}

function Convert-ActionInfo {
    param([object]$Action)

    return [ordered]@{
        type = [string]$Action.CimClass.CimClassName
        execute = [string]$Action.Execute
        arguments = [string]$Action.Arguments
        working_directory = [string]$Action.WorkingDirectory
    }
}

$rootDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $OutputPath) {
    $OutputPath = Join-Path $rootDir "meta\schedule_registry.json"
}

$trackedTasks = @(
    [ordered]@{
        id = "office_telegram_bot"
        task_path = "\"
        task_name = "1POW_TelegramBot"
        project = "03_telegram_py"
        purpose = "Office Telegram bot bootstrap"
        notes = @(
            "Current Windows action still points to C:\1POW\03_telegram_py\START_TELEGRAM_BOT_NOW.bat."
        )
    },
    [ordered]@{
        id = "ivwith_daily_sync"
        task_path = "\"
        task_name = "DailySyncIvwith"
        project = "ivwith"
        purpose = "Office H-sheet daily_sync batch"
        notes = @(
            "Current Windows action still points to C:\1POW\ivwith\daily_sync.py."
        )
    },
    [ordered]@{
        id = "excel_sync_to_server"
        task_path = "\"
        task_name = "SyncExcelToServer"
        project = "ivwith"
        purpose = "Excel sync to server batch"
        notes = @(
            "Current Windows action still points to C:\1POW\sync_excel_to_server.ps1."
        )
    },
    [ordered]@{
        id = "myhome_daily_refresh"
        task_path = "\2POW\"
        task_name = "myhome_daily_refresh_0700"
        project = "myhome"
        purpose = "myhome notice/data daily refresh"
        notes = @(
            "This task is already registered under the \\2POW\\ Task Scheduler path."
        )
    }
)

$taskRows = @()

foreach ($spec in $trackedTasks) {
    $row = [ordered]@{
        id = $spec.id
        task_path = $spec.task_path
        task_name = $spec.task_name
        project = $spec.project
        purpose = $spec.purpose
        notes = @($spec.notes)
        found = $false
        state = ""
        last_run_time = ""
        next_run_time = ""
        last_task_result = ""
        actions = @()
        triggers = @()
    }

    try {
        $task = Get-ScheduledTask -TaskPath $spec.task_path -TaskName $spec.task_name -ErrorAction Stop
        $taskInfo = Get-ScheduledTaskInfo -TaskPath $spec.task_path -TaskName $spec.task_name -ErrorAction Stop

        $row.found = $true
        $row.state = [string]$task.State
        $row.last_run_time = Convert-ToIsoString $taskInfo.LastRunTime
        $row.next_run_time = Convert-ToIsoString $taskInfo.NextRunTime
        $row.last_task_result = [string]$taskInfo.LastTaskResult
        $row.actions = @($task.Actions | ForEach-Object { Convert-ActionInfo $_ })
        $row.triggers = @($task.Triggers | ForEach-Object { Convert-TriggerInfo $_ })
    } catch {
        $row.notes += "Task not found in current Windows Task Scheduler snapshot."
    }

    $taskRows += [pscustomobject]$row
}

$payload = [ordered]@{
    version = 1
    generated_at = Convert-ToIsoString (Get-Date)
    source = "Windows Task Scheduler mirror for 2POW local workspace"
    refresh_command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\2POW\tools\ops\refresh_schedule_registry.ps1"
    authority_note = "Read this file first for schedule questions before querying Windows Task Scheduler directly."
    tasks = @($taskRows)
}

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$json = $payload | ConvertTo-Json -Depth 8
Set-Content -LiteralPath $OutputPath -Value $json -Encoding UTF8
Write-Host "schedule_registry_out=$OutputPath"
Write-Host "schedule_registry_tasks=$($taskRows.Count)"
