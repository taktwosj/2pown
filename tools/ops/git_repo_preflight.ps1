param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,
    [switch]$NoPull,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

$script:GitCommand = ""
foreach ($candidate in @("git.exe", "git")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $script:GitCommand = $cmd.Source
        break
    }
}

if (-not $script:GitCommand) {
    throw "git executable not found in current PowerShell environment"
}

function Invoke-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()

    try {
        $proc = Start-Process -FilePath $script:GitCommand -ArgumentList $Args -NoNewWindow -Wait -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        $output = @()
        if (Test-Path -LiteralPath $stdoutFile) {
            $output += Get-Content -LiteralPath $stdoutFile -Encoding UTF8
        }
        if (Test-Path -LiteralPath $stderrFile) {
            $output += Get-Content -LiteralPath $stderrFile -Encoding UTF8
        }

        return [pscustomobject]@{
            Output = @($output)
            ExitCode = $proc.ExitCode
        }
    } finally {
        Remove-Item -LiteralPath $stdoutFile, $stderrFile -ErrorAction SilentlyContinue
    }
}

$resolved = (Resolve-Path -LiteralPath $RepoPath).Path
$repoArgs = @("-C", $resolved)

$gitRootResult = Invoke-Git @($repoArgs + @("rev-parse", "--show-toplevel"))
if ($gitRootResult.ExitCode -ne 0) {
    throw "not a git repo: $resolved"
}

$gitRoot = ($gitRootResult.Output | Select-Object -First 1).Trim()
$remoteResult = Invoke-Git @($repoArgs + @("remote", "get-url", "origin"))
if ($remoteResult.ExitCode -ne 0) {
    throw "origin remote missing: $gitRoot"
}

$remote = ($remoteResult.Output | Select-Object -First 1).Trim()
$branchResult = Invoke-Git @($repoArgs + @("branch", "--show-current"))
$branch = ($branchResult.Output | Select-Object -First 1).Trim()
if (-not $branch) {
    $branch = "(detached)"
}

$fetchResult = Invoke-Git @($repoArgs + @("fetch", "origin", "--prune"))
if ($fetchResult.ExitCode -ne 0) {
    throw "git fetch failed: $gitRoot"
}

$statusResult = Invoke-Git @($repoArgs + @("status", "--short", "--branch"))
if ($statusResult.ExitCode -ne 0) {
    throw "git status failed: $gitRoot"
}

$porcelainResult = Invoke-Git @($repoArgs + @("status", "--porcelain"))
if ($porcelainResult.ExitCode -ne 0) {
    throw "git porcelain status failed: $gitRoot"
}

$dirty = ($porcelainResult.Output.Count -gt 0)

$upstreamResult = Invoke-Git @($repoArgs + @("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"))
$upstream = ""
if ($upstreamResult.ExitCode -eq 0) {
    $upstream = ($upstreamResult.Output | Select-Object -First 1).Trim()
}

$pullState = "skipped"
if ($dirty -and -not $AllowDirty) {
    $pullState = "blocked: dirty"
} elseif ($NoPull) {
    $pullState = "disabled"
} elseif (-not $upstream) {
    $pullState = "skipped: no upstream"
} elseif ($branch -eq "(detached)") {
    $pullState = "skipped: detached"
} else {
    $pullResult = Invoke-Git @($repoArgs + @("pull", "--ff-only"))
    if ($pullResult.ExitCode -ne 0) {
        throw "git pull --ff-only failed: $gitRoot"
    }
    $pullState = "ff-only ok"
    $statusResult = Invoke-Git @($repoArgs + @("status", "--short", "--branch"))
}

Write-Host "repo_path=$resolved"
Write-Host "git_root=$gitRoot"
Write-Host "origin=$remote"
Write-Host "branch=$branch"
Write-Host "upstream=$upstream"
Write-Host "dirty=$dirty"
Write-Host "pull_state=$pullState"
Write-Host "status_begin"
foreach ($line in $statusResult.Output) {
    Write-Host $line
}
Write-Host "status_end"

if ($dirty -and -not $AllowDirty) {
    throw "dirty worktree blocks default pull workflow: $gitRoot"
}
