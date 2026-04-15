# 2POW Workspace

`C:\2POW` is the canonical control-plane, project-registry root, and Windows workspace.

## Core Structure

- Start every new task in `C:\2POW`.
- The only canonical start procedure is `docs/START.md`.
- Identify projects only through `meta/project_registry.json`.
- Read project-specific docs only through `doc_canonical`.
- Repo-backed work should be pulled in the target nested repo before edits when possible.
- Verified repo-backed changes should usually be committed/pushed unless the task is explicitly local-only.
- This root repo is for `2POW` control-plane docs, root wrappers, and shared tooling.
- Nested project repos under `03_telegram_py`, `admin`, `ivwith`, `jogyeon`, `myhome`, `고객관리` are not vendored into this root repo.
- Treat `Cafe24` as runtime, deploy, and verification infrastructure.
- Treat the office PC as an execution node, not a source of truth.
- Treat the Excel workbook as a business asset, not a code repo.
- Server markdown files are not canonical fallback documents.

## Canonical Files

- `README.md`
- `CLAUDE.md`
- `GPT.md`
- `docs/START.md`
- `meta/project_registry.json`
- `docs/projects/README.md`
- `tools/ops/git_repo_preflight.ps1`
- `tools/ops/refresh_schedule_registry.ps1`

## Reading Order

1. `docs/START.md`
2. `meta/project_registry.json`
3. the target project's `doc_canonical`

Do not duplicate execution procedure here. `README.md` is the structure summary only.
