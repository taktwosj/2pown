# Git Remote Setup

현재 표준은 `origin` 하나를 기준 원격 이름으로 쓰는 것이다.
문서와 스크립트는 `origin`만 가정하고, `github` 같은 별도 원격 이름은 legacy로 본다.

## Current Standard

- Control-plane start point: `C:\2POW`
- Workspace root: `C:\2POW`
- Canonical remote name: `origin`
- Canonical Git host: GitHub
- Server role: `Cafe24` runtime / deploy / verification only

## Rules

- 새 작업은 항상 `C:\2POW`에서 시작한다.
- `git remote get-url origin`이 실패하면 먼저 상태를 보고하고 멈춘다.
- `origin` 이외의 원격 이름을 새 표준 문서에 추가하지 않는다.
- legacy remote 이름 전제가 문서나 스크립트에 남아 있으면 먼저 정리한다.
- root `C:\2POW`는 git repo가 아니므로, 원격 확인은 프로젝트 식별 뒤 target nested repo 안에서 한다.
- repo-backed 작업은 가능하면 preflight + `pull --ff-only` 후 시작한다.
- 검증 완료된 repo-backed 변경은 가능하면 commit/push까지 반영한다.

## Control-Plane Check

```powershell
Set-Location C:\2POW
Test-Path "C:\2POW\meta\project_registry.json"
Test-Path "C:\2POW\docs\START.md"
```

## Project Repo Check

After project identification, run remote checks in the actual repo root:

```powershell
$REPO = "C:\2POW\03_telegram_py"   # replace with the target repo root
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\2POW\tools\ops\git_repo_preflight.ps1 -RepoPath $REPO
```

## Project Repo Rule

- Project repos under `C:\2POW` should use their canonical Git remote as `origin`.
- `canonical_git` tells you which repo is authoritative.
- `canonical_server` is for runtime validation and deploy checks only.
- dirty worktree가 있으면 기본 pull workflow를 멈추고 먼저 범위를 정리한다.
- local-only 예외가 아니면 repo-backed 변경은 Git 반영을 기본값으로 본다.

## Notes

- Historical OneDrive mirror procedures are not the current canonical remote model.
- If an old script still assumes another remote naming scheme, fix the script before changing local remotes.
