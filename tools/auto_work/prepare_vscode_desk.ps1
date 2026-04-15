param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$ArgsFromCaller
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-CanonicalScript {
    $root1pow = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
    $rootOther = Join-Path (Split-Path $root1pow -Parent) "1other\\openclaw-front-secretary"
    return Join-Path $rootOther "tools\\auto_work\\prepare_vscode_desk.ps1"
}

$scriptPath = Resolve-CanonicalScript

if (-not (Test-Path $scriptPath)) {
    throw @"
prepare_vscode_desk canonical not found.
expected: $scriptPath
Run from C:\1other\openclaw-front-secretary or restore the extracted canonical first.
"@
}

& $scriptPath @ArgsFromCaller
exit $LASTEXITCODE
