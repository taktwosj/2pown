$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$managerWindows = Join-Path $workspaceRoot '.worktrees\ivwith-modern-app\tools\ivwith_local_runtime.py'
$drive = $managerWindows.Substring(0, 1).ToLowerInvariant()
$managerWsl = "/mnt/$drive" + $managerWindows.Substring(2).Replace('\', '/')
& wsl.exe -u root -e /opt/ivwith-modern-venv/bin/python3 $managerWsl verify
if ($LASTEXITCODE -ne 0) {
    throw 'ivwith 로컬 서버 검증에 실패했습니다.'
}
Write-Output '검증 완료: http://100.102.6.112:8126/'
