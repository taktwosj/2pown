param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsFromCaller
)

$scriptPath = Join-Path $PSScriptRoot "front_secretary.py"
$python314 = Join-Path $env:LocalAppData "Programs\Python\Python314\python.exe"

if (Test-Path $python314) {
    & $python314 $scriptPath @ArgsFromCaller
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $scriptPath @ArgsFromCaller
    exit $LASTEXITCODE
}

& python $scriptPath @ArgsFromCaller
exit $LASTEXITCODE
