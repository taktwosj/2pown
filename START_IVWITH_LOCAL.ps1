$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$managerWindows = Join-Path $workspaceRoot '.worktrees\ivwith-modern-app\tools\ivwith_local_runtime.py'
if (-not (Test-Path -LiteralPath $managerWindows)) {
    throw "최신 ivwith 로컬 실행 관리자를 찾을 수 없습니다: $managerWindows"
}
$drive = $managerWindows.Substring(0, 1).ToLowerInvariant()
$managerWsl = "/mnt/$drive" + $managerWindows.Substring(2).Replace('\', '/')
& wsl.exe -u root -e /opt/ivwith-modern-venv/bin/python3 $managerWsl restart
if ($LASTEXITCODE -ne 0) {
    throw 'ivwith 로컬 서버 재시작에 실패했습니다.'
}

$tailscale = 'C:\Program Files\Tailscale\tailscale.exe'
if (-not (Test-Path -LiteralPath $tailscale)) {
    throw 'Tailscale 실행 파일을 찾을 수 없습니다.'
}
$serve = (& $tailscale serve status --json | ConvertFrom-Json)
$forward = $serve.TCP.'8126'.TCPForward
if ($forward -ne '127.0.0.1:8124') {
    & $tailscale serve --bg --tcp 8126 tcp://127.0.0.1:8124 --yes
    if ($LASTEXITCODE -ne 0) {
        throw 'Tailscale 8126 전달 설정에 실패했습니다.'
    }
}

& wsl.exe -u root -e /opt/ivwith-modern-venv/bin/python3 $managerWsl verify
if ($LASTEXITCODE -ne 0) {
    throw 'ivwith 로컬 화면 검증에 실패했습니다.'
}

Write-Output 'ivwith 로컬 서버 정상: http://100.102.6.112:8126/'
