param(
    [string]$IvwithMenu34BaseDir = ''
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OfficeScript = Join-Path $ScriptDir '_restart_office_bot.ps1'

if ([string]::IsNullOrWhiteSpace($IvwithMenu34BaseDir)) {
    & $OfficeScript
} else {
    & $OfficeScript -IvwithMenu34BaseDir $IvwithMenu34BaseDir
}
