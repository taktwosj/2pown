param(
    [string]$IvwithMenu34BaseDir = ''
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OfficeScript = Join-Path $ScriptDir '03_telegram_py\_restart_office_bot.ps1'

if ([string]::IsNullOrWhiteSpace($IvwithMenu34BaseDir)) {
    $DefaultMenu34ShadowBase = 'C:\2POW'
    if (Test-Path -LiteralPath (Join-Path $DefaultMenu34ShadowBase 'ivwith\daily_sync.py')) {
        $IvwithMenu34BaseDir = $DefaultMenu34ShadowBase
    }
}

if ([string]::IsNullOrWhiteSpace($IvwithMenu34BaseDir)) {
    & $OfficeScript
} else {
    & $OfficeScript -IvwithMenu34BaseDir $IvwithMenu34BaseDir
}
