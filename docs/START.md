# START

This file is the startup procedure entrypoint for all `2POW` work.
Every new chat starts in `C:\2POW` and runs this sequence before edits.

## Rule references
- Global rules: `AGENTS.md`
- Harness details: `docs/HARNESS_MODE.md`
- Project identification authority: `meta/project_registry.json`
- Local automation/schedule mirror: `meta/schedule_registry.json`
- Path integrity and markdown doc length rules follow `AGENTS.md`

## Operating Model
- `C:\2POW` = canonical control-plane, Windows workspace root, and local path authority
- `Cafe24` = runtime, deploy, and verification infrastructure
- Office PC = execution node for office-auth, Telegram, and Excel-driven work

## Preparation Mode
Use read-only preparation mode when user intent is orientation only.
- Read `docs/START.md` and `meta/project_registry.json` first
- If the request is about automation/schedule, also read `meta/schedule_registry.json`
- No file edits / commit / push / deploy
- Report structure, authority, entrypoints, and unknowns

## Start Procedure (formal execution)
PowerShell:
```powershell
Set-Location C:\2POW
Test-Path "C:\2POW\AGENTS.md"
Test-Path "C:\2POW\docs\START.md"
Test-Path "C:\2POW\meta\project_registry.json"
Test-Path "C:\2POW\meta\schedule_registry.json"
```

Git Bash on Windows:
```bash
cd /c/2POW
test -f "/c/2POW/AGENTS.md"
test -f "/c/2POW/docs/START.md"
test -f "/c/2POW/meta/project_registry.json"
test -f "/c/2POW/meta/schedule_registry.json"
```

## Stop conditions
- required authority docs missing
- `meta/project_registry.json` missing
- requested project cannot be identified
- target nested repo exists but repo sync/status check fails

## Project Identification
After start procedure succeeds:
1. Read `meta/project_registry.json`
2. Identify project by `id/name/local_path/doc_canonical/authority fields`
3. Read common docs from `README.md`, `CLAUDE.md`, `GPT.md`, `docs/START.md`
4. Read project docs only through `doc_canonical`

## Nested Repo Check
If the target project lives in a git repo under `C:\2POW`, run repo checks inside that repo after project identification.

PowerShell:
```powershell
$PROJECT_ROOT = "C:\2POW\<repo>"   # replace with the identified repo root
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\2POW\tools\ops\git_repo_preflight.ps1 -RepoPath $PROJECT_ROOT
```

Git Bash on Windows:
```bash
PROJECT_ROOT="/c/2POW/<repo>"   # replace with the identified repo root
cd "$PROJECT_ROOT"
git remote get-url origin
git branch --show-current
git fetch origin --prune
git status --short --branch
git pull --ff-only
```

## First Response Format
Before code edits, report only:
- `ROOT`
- target repo branch / working-tree state / pull state (if repo-backed project)
- identified project id / name / `doc_canonical`
- Harness Mode active? (`yes/no`) + approval gate status
- what can be done now / what is unknown

## Completion Reporting
1. What changed
2. How it was verified
3. Remaining work or next work
