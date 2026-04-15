# 2POW 작업 규칙

## Authority
- 문서/규칙 정본(control-plane)은 `C:\2POW`다.
- `C:\2POW`가 코드 작업/실행 workspace이기도 하다.
- 프로젝트 식별 정본은 `meta/project_registry.json`이다.
- 로컬 자동화/스케줄 미러 정본은 `meta/schedule_registry.json`이다.
- `AGENTS.md = 규칙`, `docs/START.md = 시작 절차`, `GPT.md = EXEC SPEC 템플릿` 역할을 고정한다.

## Document Path Integrity
- 경로 정본(path authority)은 `C:\2POW\meta\project_registry.json`이다.
- 프로젝트 운영 정본은 프로젝트별 handover 문서 1개만 둔다.
- `README.md`와 `docs/SYSTEM_MAP.md`는 설명 문서이지 경로 정본이 아니다.
- handover 명확성을 위해 꼭 필요한 경우가 아니면 canonical 경로를 여러 마크다운 파일에 중복 기록하지 않는다.
- 문서에서는 가능하면 프로젝트별 repo-relative 경로를 우선 사용한다.
- 절대 Windows 경로는 `project_registry.json`과 프로젝트 handover처럼 운영상 꼭 필요한 문서에서만 사용한다.
- 폴더 경로가 바뀌면 최소한 아래 파일들을 함께 갱신한다.
  - `C:\2POW\meta\project_registry.json`
  - 해당 프로젝트 handover
  - `docs/SYSTEM_MAP.md`
  - 해당 프로젝트 `README.md`
- 위 4개가 같이 갱신되지 않았다면 path migration은 미완료로 본다.
- 가능하면 새 마크다운 파일을 늘리기보다 기존 authority 문서를 갱신한다.
- stale path는 병렬 truth로 남기지 말고 제거하거나 archive 처리한다.
- 문서 경로만 바꾸고 실제 코드 진입점이 옛 경로를 보고 있으면 migration 완료로 보지 않는다.

## Scope
- 먼저 현재 요청이 어느 작업 영역인지 구분한다: `myhome`, `admin`, `ivwith`, `03_telegram_py`.
- 기본 원칙은 한 번에 한 영역만 수정한다.
- 임대주택/ETL/영업리스트 요청은 기본적으로 `myhome/**`만 수정한다.
- 공통 문서화는 `docs/**`에 둔다.

## Preferred Paths
- 임대주택 작업의 기준 파일은 가능하면 `myhome/**`를 우선한다.
- `03_telegram_py/**`는 배포본이나 동기화본일 수 있으므로, 명시 요청이 없으면 기준 원본처럼 다루지 않는다.
- 백업, 압축파일, 복사본 파일은 명시 요청 없이는 수정하지 않는다.

## Git-First Workflow
- repo-backed 프로젝트는 가능하면 Git을 기준으로 작업한다.
- 시작은 항상 `C:\2POW`에서 하되, 프로젝트 식별 후 실제 nested repo에서 `fetch/pull` 상태를 먼저 확인한다.
- 기본 preflight 명령은 `C:\2POW\tools\ops\git_repo_preflight.ps1 -RepoPath <repo-root>` 이다.
- repo가 clean하고 upstream이 있으면 `pull --ff-only`까지 수행한 뒤 작업한다.
- dirty worktree, upstream 부재, `pull --ff-only` 실패가 나오면 먼저 상태를 보고하고 로컬-only 진행 여부를 분리한다.
- repo-backed 변경은 검증 후 가능하면 commit/push까지 하는 것을 기본값으로 본다.
- 아래 경우에는 자동 publish 기본값에서 제외한다.
  - 사용자가 local-only를 명시한 경우
  - 시크릿/개인정보/대용량 산출물이 섞여 commit scope가 불명확한 경우
  - unrelated dirty changes 때문에 안전한 commit 범위를 못 자르는 경우

## Live Entry Points
- `C:\2POW` 루트는 git repo가 아니다. 내부 작업 트리와 nested repo는 각각 독립적으로 본다.
- office telegram live entry chain:
  - `C:\2POW\START_TELEGRAM_BOT_NOW.bat`
  - `C:\2POW\03_telegram_py\START_TELEGRAM_BOT_NOW.bat`
  - `C:\2POW\03_telegram_py\run_office_bot.py`
  - `C:\2POW\03_telegram_py\bot_runtime_profile.py`
  - `C:\2POW\bot.py`
- 현재 live authority이자 유일한 `bot.py`는 `C:\2POW\bot.py`다.
- `C:\2POW\03_telegram_py`는 wrapper/shared helper/worktree 영역으로만 본다.
- `C:\2POW\03_telegram_py\bot.py`는 제거됐다. 옛 문서/로그에 나오는 경로는 historical reference로만 본다.
- rollback snapshot은 `C:\2POW\03_telegram_py\office_deploy\root_bot.rollback.py`만 사용한다.
- `bot.py` 후속 작업은 root `C:\2POW\bot.py` 기준으로만 진행한다.

## menu34 Freeze Boundary
- 아래 표면은 explicit request 없이 구조 이동/대수술하지 않는다.
  - `C:\2POW\bot.py`
    - `_BOT_ENV = load_bot_env_config()` 와 `IVWITH_MENU34_BASE_DIR` 결정부
    - `_runtime_state_path()` / secret/runtime path 처리부
  - `C:\2POW\03_telegram_py\bot_app\menus\ivwith_menu.py`
    - `run_hsheet_sync(...)` 호출부
  - `C:\2POW\ivwith\daily_sync.py`
    - `_load_bot_config()`
    - `run_hsheet_sync(...)`
- 현재 line 기준 참고값(2026-04-14):
  - `C:\2POW\bot.py` 약 `144`, `1406`
  - `C:\2POW\03_telegram_py\bot_app\menus\ivwith_menu.py` 약 `180`
  - `C:\2POW\ivwith\daily_sync.py` 약 `48`, `599`
- menu34 관련 변경 후 최소 검증:
  - `python3 -m py_compile`
  - `RUN_MENU34_SHADOW_SMOKE.ps1`
  - `RUN_MENU34_GUARD.ps1`
  - office bot heartbeat / `runtime/last_sync.json` / admin mirror 확인

## Status Reporting Format
- Codex 상태 파일은 `C:\2POW\03_telegram_py\codex_task_status.json` 하나만 쓴다.
- 가능하면 수동 JSON 편집보다 `C:\2POW\03_telegram_py\codex_work_status.py` 로 갱신한다.
- 현재 스키마:
  - `project`
  - `current`
  - `progress`
  - `total_tasks`
  - `note`
  - `done_items`
  - `remaining_items`
  - `updated_at`
- `progress`는 정수 퍼센트로 쓴다.
- `Phase n` / `Batch n` 표기는 기존 상태 파일과 같은 형식을 유지한다.
- 같은 트랙에서는 기존 `done_items` / `remaining_items` 포맷을 임의로 바꾸지 않는다.

## Parallel Session Protocol
- 작업 시작 전 `C:\2POW\03_telegram_py\codex_task_status.json` 을 먼저 읽고, 다른 세션의 현재 작업 영역이 무엇인지 확인한다.
- 다른 세션이 같은 영역(`bot.py`, `menu34`, 폴더 이동, status 파일`)을 건드리는 중이면 겹치는 수정은 멈추고 작업 영역을 분리한다.
- `codex_task_status.json` 은 한 트랙당 한 세션만 최종 write 하는 것을 기본으로 본다.
- 폴더 이동이나 root live 파일 수정 직전에는 status 파일을 다시 읽어 stale plan이 아닌지 확인한다.

## Do Not Touch Without Explicit Request
- `**/*.zip`
- `**/*복사본*`
- `C:\2POW_SECRETS\telegram\bot_token.txt`
- `C:\2POW_SECRETS\telegram\allowed_chat_ids.txt`
- `C:\2POW_SECRETS\telegram\office_allowed_hosts.txt`
- `myhome/.env`
- 대용량 원본 CSV/XLSX의 내용 자체

## Workflow
- 변경 전에 관련 파일과 경로 구조를 먼저 읽는다.
- repo-backed 프로젝트면 변경 전에 `git_repo_preflight.ps1` 또는 동등한 `git fetch/pull` 확인을 먼저 한다.
- 변경은 최소 범위로 한다.
- 코드 변경과 생성물 재생성은 구분해서 보고한다.
- 동작이나 출력이 바뀌면 관련 실행 문서도 같이 갱신한다.
- 반복 작업은 가능하면 스크립트나 문서로 남긴다.
- 사용자가 자동실행, 예약, 윈도우 작업 스케줄러, 텔레그램 자동전송, `daily_sync` 시간표를 물으면 먼저 `C:\2POW\meta\schedule_registry.json`을 읽는다.
- 최신 스냅샷이 필요하면 `C:\2POW\tools\ops\refresh_schedule_registry.ps1`로 `meta/schedule_registry.json`을 갱신한 뒤 답한다.

## Verification
- HTML/JS 변경 시 가능하면 `node --check` 또는 최소 스모크 검증을 한다.
- Python 변경 시 가능하면 `python3 -m py_compile` 또는 대상 스크립트 실행으로 확인한다.
- 데이터 파이프라인 변경 시 최소한 출력 파일과 품질 보고서 변화 여부를 확인한다.
- 검증을 못 했으면 이유를 명확히 남긴다.

## Reporting
- 최종 보고는 다음 순서를 따른다.
1. 무엇을 바꿨는지
2. 어떻게 검증했는지
3. git 반영 상태 또는 남은 publish 작업

## Safety
- 파괴적 명령은 사용하지 않는다.
- 시크릿, 토큰, 키 값은 출력하지 않는다.
- 원본 데이터와 생성 결과물을 같은 의미의 파일로 혼동하지 않는다.
- OneDrive 동기화는 백업일 뿐, 변경 이력 관리의 대체가 아니라는 점을 전제로 작업한다.
