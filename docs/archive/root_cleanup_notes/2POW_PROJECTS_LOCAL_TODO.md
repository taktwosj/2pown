# 2POW Projects Local TODO

기준일: 2026-04-14

## 목표

- `C:\2POW`에 섞여 있는 코드, runtime, secrets, assets, archive를 역할별로 분리한다.
- 최종적으로는 `2POW_프로젝트` 체계로 로컬 구조를 재정리하고, 프로젝트별로 git 기준 작업본을 명확히 한다.
- `menu34`와 office telegram bot은 정리 도중에도 계속 안전하게 유지한다.

## 최상위 방향

- 메인 작업본은 git repo 기준으로 둔다.
- live 실행본과 runtime/state/log는 작업본과 분리한다.
- OneDrive는 정본이 아니라 백업/스냅샷 용도로만 쓴다.
- `2POW` 루트는 점점 “운영 shim + launcher + runtime bridge” 역할로 줄인다.

## 제안하는 목표 구조

```text
C:\
├─ 2POW_프로젝트\
│  ├─ telegram-bot\
│  ├─ ivwith\
│  ├─ admin-bridge\
│  ├─ myhome\
│  ├─ blog\
│  └─ jogyeon\
├─ 2POW_RUNTIME\
│  ├─ telegram\
│  │  ├─ office\
│  │  └─ codex\
│  └─ ivwith\
├─ 2POW_SECRETS\
├─ 2POW_ASSETS\
└─ 2POW_ARCHIVE\
```

## 고정 원칙

- `menu34` freeze 대상은 초반에 옮기지 않는다.
  - `C:\2POW\bot.py`
  - `C:\2POW\bot_app\menus\home.py`
  - `C:\2POW\bot_app\menus\ivwith_menu.py`
  - `C:\2POW\ivwith\daily_sync.py`
  - `C:\2POW\runtime\last_sync.json`
  - `C:\2POW\runtime\root_bot\**`
  - `C:\2POW\config\canonical_map.local.json`
- telegram 구조 변경은 항상 아래 검증 세트로 닫는다.
  - `py_compile`
  - `RUN_MENU34_SHADOW_SMOKE.ps1`
  - `RUN_MENU34_GUARD.ps1`
  - office bot restart
  - heartbeat / `last_sync.json` / admin mirror 확인
- `2POW` 전체를 거대 git 하나로 묶지 않는다.
- repo 단위 기준:
  - telegram: `C:\2POW\03_telegram_py`
  - ivwith: `C:\2POW\ivwith`
  - 문서/registry: `C:\1POW_META`

## 진행 / 보고 규칙

- 이 문서를 기준 TODO로 사용한다.
- 진행 중에는 이 채팅에서 현재 단계 / 완료 항목 / 다음 항목을 계속 보고한다.
- 항목이 하나 완료될 때마다 `03_telegram_py/codex_work_status.py` 로 상태 파일을 갱신하고 텔레그램에 보고한다.
- 텔레그램 보고는 요약 위주로 한다.
  - 완료한 항목
  - 현재 진행 중 항목
  - 남은 큰 단계
- `codex_task_status.json` 의 프로젝트명은 이 작업 동안 `2POW 프로젝트 로컬 정리`로 고정한다.

## TODO

- [x] Phase 0-Setup: TODO 문서 생성 + 텔레그램 상태 보고 경로 연결
- [x] Phase 0-A: 현재 `2POW` 루트 항목 분류표 작성
  - code
  - runtime
  - secrets
  - assets
  - docs
  - stale/archive
- [x] Phase 0-B: `menu34` / office bot freeze 경계 재확인
  - live entry
  - restart path
  - runtime state path
  - `last_sync.json` mirror path

- [x] Phase 1-A: `2POW_프로젝트` 목표 폴더명 확정
  - `telegram-bot`
  - `ivwith`
  - `admin-bridge`
  - `myhome`
  - `blog`
  - `jogyeon`
- [x] Phase 1-B: git 작업본으로 올릴 대상 / 안 올릴 대상 구분
  - git 대상: 코드, 스크립트, 문서, 테스트
  - 비git 대상: token, allowed_chat_ids, xlsm, runtime logs, pid, lock, cache
- [x] Phase 1-C: `2POW_RUNTIME`, `2POW_SECRETS`, `2POW_ASSETS`, `2POW_ARCHIVE` 역할 정의 문서화

- [x] Phase 2-A: telegram live authority / repo worktree 관계 정리
  - 현재 live authority는 root `C:\2POW\bot.py`
  - `C:\2POW\03_telegram_py`는 git 작업본이지만 office profile은 아직 root `bot.py`를 실행
  - 비교 기준 live 표면에서는 `bot.py`만 drift, `home.py` / `ivwith_menu.py`는 동기화됨
- [x] Phase 2-B: `03_telegram_py/03_telegram_py/` stale copy 격리 계획 수립
- [x] Phase 2-C: `03_telegram_py/runtime` 같은 비live 산출물 archive 후보 정리
- [x] Phase 2-D: `admin` 중복 (`C:\2POW\admin`, `C:\2POW\03_telegram_py\admin`) 용도 표 정리

- [x] Phase 3-A: 로컬 폴더 이동 전 dry-run 목록 만들기
  - source path
  - target path
  - reason
  - rollback path
- [x] Phase 3-B: secrets / runtime / assets 먼저 분리할지, stale copy 먼저 격리할지 작업 순서 확정
- [x] Phase 3-C: 실제 이동 시 batch size를 작게 유지
  - 한 번에 한 프로젝트
  - 한 번에 한 concern

- [x] Phase 4-A: 프로젝트별 git 반영 순서 확정
  - 1순위: telegram-bot
  - 2순위: admin-bridge
  - 3순위: ivwith
  - 4순위 이후: blog / jogyeon / myhome
- [x] Phase 4-B: repo-first 운영 규칙 확정
  - 수정은 repo에서 먼저
  - live 반영은 preview/apply/restart
  - root 직접 수정은 긴급 hotfix만

## 프로젝트별 초안

### telegram-bot

- 현재 기준 repo: `C:\2POW\03_telegram_py`
- 현재 live entry: `C:\2POW\bot.py`
- 핵심 리스크:
  - root / repo `bot.py` drift
  - compared live menu files는 현재 맞지만 `bot.py` authoritative path가 이원화돼 있음
  - runtime / secrets / wrappers가 루트와 repo에 걸쳐 있음
- 우선순위:
  - canonical 결정
  - `globals()` 브리지 해체
  - repo-first 배포 규칙 닫기

### ivwith

- 현재 기준 repo: `C:\2POW\ivwith`
- 핵심 리스크:
  - `admin`, `new_admin`, `admin_new_runtime`, `backups` 혼재
  - live H시트 sync는 telegram menu34와 강결합
- 우선순위:
  - active / legacy / backups 분리 기준 문서화
  - `admin_new_runtime`를 active로 고정

### admin-bridge

- 현재 표면:
  - canonical 후보: `C:\2POW\admin`
  - telegram-side mirror 후보: `C:\2POW\03_telegram_py\admin`
- 우선 할 일:
  - 실제 live 참조 경로 확인
  - 중복 파일 해시 비교
  - canonical 하나만 남기는 방향 설계

### myhome / blog / jogyeon

- 각자 독립 repo 여부와 runtime 자산 섞임 정도 먼저 확인
- code / build artifact / secrets / backups 분리 기준부터 세운다

## 검증 체크리스트

- [ ] `2POW` 루트가 아닌 각 프로젝트 repo 기준으로 상태를 본다
- [ ] 로컬 이동 전 `git status` 저장
- [ ] 폴더 이동 전/후 경로 매핑표 저장
- [ ] telegram 관련 변경은 항상 `menu34` smoke + guard 재실행
- [ ] office bot heartbeat 확인
- [ ] `last_sync_run_id` mirror 일치 확인

## Phase 0 Deliverables

### 0-A. `2POW` 루트 항목 분류표

| 항목 | 종류 | 1차 분류 | git 기준 |
|------|------|-----------|-----------|
| `03_telegram_py` | dir | project/code | repo (`main`) |
| `admin` | dir | project/code | repo (`main`) |
| `blog` | dir | project/code | 내부 `blog/booyoung-landing`이 repo (`master`) |
| `ivwith` | dir | project/code | repo (`main`) |
| `jogyeon` | dir | project/code | repo (`main`) |
| `myhome` | dir | project/code | repo (`main`) |
| `runtime` | dir | runtime | 비git |
| `allowed_chat_ids.txt` | file | secrets | 비git |
| `bot_token.txt` | file | secrets | 비git |
| `office_allowed_hosts.txt` | file | secrets | 비git |
| `고객관리` | dir | assets | 비git |
| `AGENTS.md`, `CLAUDE.md`, `GPT.md`, `README.md`, `START.md` | file | docs/control | 비git 루트 pointer 문서 |
| `docs`, `meta`, `repo_blueprints` | dir | docs/control | 비git 루트 문서/registry 복제 표면 |
| `1POW_DELETE_HANDOVER_2026-04-10.md`, `루트파일정리실행표_2026-04-09.md`, `2POW_PROJECTS_LOCAL_TODO.md` | file | docs/control | 비git |
| `bot.py`, `bot_app`, `bot_runtime_polling.py`, `config`, `lockfile.py`, `tools` | mixed | live-shim | 비git |
| `_restart_bot.ps1`, `_restart_office_bot.ps1`, `START_TELEGRAM_BOT_NOW.bat` | file | live-shim | 비git |
| `kiwoom_new_capture.png`, `ms_new_capture.png` | file | stale/debug | 비git |
| `__pycache__` | dir | stale/cache | 비git |

보조 크기 기준:

- `ivwith`: `3.1G`
- `myhome`: `1.3G`
- `03_telegram_py`: `158M`
- `blog`: `86M`
- `admin`: `29M`
- `고객관리`: `4.9M`
- `runtime`: `148K`

### 0-B. `menu34` / office bot freeze 경계

live 실행선:

- `C:\2POW\START_TELEGRAM_BOT_NOW.bat`
- `C:\2POW\_restart_office_bot.ps1`
- `C:\2POW\03_telegram_py\_restart_office_bot.ps1`
- `C:\2POW\03_telegram_py\run_office_bot.py`
- `C:\2POW\03_telegram_py\bot_runtime_profile.py`
- `C:\2POW\bot.py`

현재 freeze 확인값:

- office bot heartbeat: `C:\2POW\runtime\root_bot\state\bot_heartbeat.json`
  - latest: `polling_start`
  - `ivwith_menu34_base_dir = C:\2POW`
- runtime state root:
  - `C:\2POW\runtime\root_bot\state`
- `menu34` runtime status:
  - `C:\2POW\runtime\last_sync.json`
- active admin mirror:
  - `C:\2POW\ivwith\admin_new_runtime\assets\last_sync.json`
- latest checked `last_sync_run_id`:
  - runtime: `hsheet-20260414-223722`
  - admin mirror: `hsheet-20260414-223722`

## 보류

- `1POW_META` 대규모 정리는 이 TODO의 1차 범위가 아니다.
- OneDrive 기반 실시간 작업본 운영은 하지 않는다.
- `2POW_프로젝트` 실제 생성과 대량 이동은 dry-run 표가 먼저 나온 뒤에 한다.

## Phase 1 Decisions

### 1-A. 목표 폴더명 확정

- `telegram-bot`
- `ivwith`
- `admin-bridge`
- `myhome`
- `blog`
- `jogyeon`

### 1-B. git 대상 / 비git 대상 기준

git 대상:

- 코드
- 스크립트
- 문서
- 테스트
- 설정 예시 파일
- 배포 절차 문서

비git 대상:

- `bot_token.txt`
- `allowed_chat_ids.txt`
- `office_allowed_hosts.txt`
- `runtime/**`
- `*.log`
- `pid`, `lock`, `heartbeat`, `status` JSON
- `__pycache__`, `*.pyc`
- `고객관리/*.xlsm`, 실데이터 CSV/XLSX
- OneDrive 원장/백업 파일

### 1-C. 역할 정의

#### `2POW_RUNTIME`

역할:

- 실행 중 프로세스 상태
- heartbeat / status / pid / lock
- runtime log
- 검증 산출물

현재 경로 대응:

- `C:\2POW\runtime\root_bot\state`
- `C:\2POW\runtime\root_bot\locks`
- `C:\2POW\runtime\root_bot\logs`
- `C:\2POW\runtime\verify`
- `C:\2POW\runtime\last_sync.json`

규칙:

- 소스코드를 넣지 않는다.
- git 추적 대상이 아니다.
- 운영 검증 증거는 남길 수 있지만, 배포 정본으로 취급하지 않는다.

#### `2POW_SECRETS`

역할:

- 토큰
- 허용 chat id / 허용 host
- 로컬 전용 경로 맵 / 로컬 환경 설정

현재 경로 대응 후보:

- `C:\2POW\bot_token.txt`
- `C:\2POW\allowed_chat_ids.txt`
- `C:\2POW\office_allowed_hosts.txt`
- `C:\2POW\config\canonical_map.local.json`

규칙:

- git 추적 대상이 아니다.
- 예시 파일만 git에 둔다.
  - 예: `office_allowed_hosts.example.txt`
  - 예: `canonical_map.example.json`
- 실제 값 파일은 live / local machine에서만 유지한다.

#### `2POW_ASSETS`

역할:

- 업무 원장
- 엑셀 / CSV / 실데이터 산출물
- 코드가 아닌 운영 데이터

현재 경로 대응:

- `C:\2POW\고객관리\통합관리.xlsm`
- `C:\2POW\고객관리\260321_190955_통합관리.xlsm`
- `C:\2POW\고객관리\update_log.csv`
- `C:\2POW\고객관리\통합관리.xlsm.*.bak`

규칙:

- 실데이터는 git에 넣지 않는다.
- 코드가 참조하는 canonical 원장은 OneDrive 경로를 유지할 수 있지만, 로컬 구조상 자산 분류는 `ASSETS`로 본다.
- backup copy도 코드 repo가 아니라 assets/archive 쪽으로 정리한다.

#### `2POW_ARCHIVE`

역할:

- stale copy
- 과거 migration 잔재
- debug capture
- 더 이상 live가 읽지 않는 복사본

현재 경로 대응 후보:

- `C:\2POW\03_telegram_py\03_telegram_py`
- `C:\2POW\kiwoom_new_capture.png`
- `C:\2POW\ms_new_capture.png`
- `C:\2POW\__pycache__`

보류 대상:

- `C:\2POW\03_telegram_py\office_deploy`
  - 현재는 rollback snapshot 역할이 있어 즉시 archive로 밀지 않는다.

규칙:

- archive는 현역 코드 폴더와 물리적으로 분리한다.
- 삭제 전에 먼저 archive 격리 후 관찰한다.

## Phase 2 Findings

### 2-A. telegram live authority / repo worktree

현재 office bot 실행선은 아래로 닫힌다.

- `C:\2POW\START_TELEGRAM_BOT_NOW.bat`
- `C:\2POW\03_telegram_py\START_TELEGRAM_BOT_NOW.bat`
- `C:\2POW\03_telegram_py\run_office_bot.py`
- `C:\2POW\03_telegram_py\bot_runtime_profile.py`
- `runpy.run_path(os.path.join(ROOT_DIR, "bot.py"), run_name="__main__")`

즉 현재 live authority는 root `C:\2POW\bot.py`다. `C:\2POW\03_telegram_py`는 git 작업본이지만 office profile이 직접 실행하는 entrypoint는 아니다.

현재 비교 완료한 live 표면:

- `bot.py`: `diff`
- `bot_app/menus/home.py`: `same`
- `bot_app/menus/ivwith_menu.py`: `same`

임시 운영 규칙:

- `menu34` / office bot hotfix authority는 root `bot.py`를 기준으로 본다.
- 구조 정리 설계와 git 기준 작업본 판단은 `03_telegram_py` repo에서 계속 진행한다.
- `bot.py` canonical 완전 닫힘은 Phase 4에서 다룬다.

### 2-B. `03_telegram_py/03_telegram_py` stale copy

`C:\2POW\03_telegram_py\03_telegram_py`는 현재 약 `76M`이다. 내부에는 아래 같은 과거 복사본/산출물이 섞여 있다.

- `01_lhshapt/`
- `02_jogyeon/`
- 별도 `bot.py`
- `eeem-clean-data.js`, `eeem-private-data.js`
- `hwspr_020304_merged_view_with_private.csv`
- `note_1pow.zip`
- `PROJECT_INDEX_2026-03-05.md`

판정:

- 현역 telegram repo 하위에 남아 있는 migration 잔재로 본다.
- 즉시 삭제하지 않고 `2POW_ARCHIVE` 이동 후보로 먼저 분류한다.
- 실제 이동은 Phase 3 dry-run 표에 source / target / rollback을 적은 뒤 진행한다.

### 2-C. telegram repo 내부 비live 산출물

`C:\2POW\03_telegram_py` 내부에서 코드/문서 외 분리 후보로 보이는 표면:

- `runtime/`
  - 현재 `readiness_audit_menu35_part2.json`
- `office_deploy/`
  - 약 `284K`
  - rollback snapshot 성격이라 즉시 이동 보류
- `__pycache__/`
  - 약 `740K`
- `bot_watchdog.log`
- `kiwoom_new.log`
- `ms_new.log`
- `onedrive_restore.log`
- `onedrive_sync.log`
- `note_1pow.zip`

정리 원칙:

- `runtime/`, `*.log`, `__pycache__`는 `RUNTIME/ARCHIVE` 표면으로 뺀다.
- `office_deploy/`는 현재 rollback snapshot으로 간주하고 관찰 대상에 둔다.
- `zip`, 대용량 CSV/JS 산출물은 archive 후보로 본다.

### 2-D. `admin` 중복 표면

현재 표면:

- root canonical 후보: `C:\2POW\admin`
  - standalone git repo (`main`)
  - 현재 working tree 변경 없음
- telegram-side mirror 후보: `C:\2POW\03_telegram_py\admin`
  - git repo 아님

비교 결과:

- `crm_bridge.py`: 동일
- `data/crm-data.json`: 동일
- root `admin` non-git 파일 수: `40`
- repo-side `admin` non-git 파일 수: `49`
- repo-side only:
  - `HOME_1_OPEN_CRM_AND_COPY_URL.bat`
  - `crm-v7-table.jsx`
  - `crm-v8-site.backup-2026-03-03.html`
  - `수당.xlsx`, `수정2행.xlsx`, `통합문서예시.xlsx`
  - `추가 HANDOVER_ADDON.md`, `클로드작업.docx`, `123`
- `REMOTE_QUICK_START.md`는 내용 차이가 있고, repo-side는 `HOME_1_OPEN_CRM_AND_COPY_URL.bat` 절차를 추가로 안내한다.

판정:

- `admin`의 code canonical은 root `C:\2POW\admin` 쪽으로 보는 것이 자연스럽다.
- `03_telegram_py/admin`은 telegram repo 내부에 남은 runtime/helper mirror + ad-hoc docs/assets 표면으로 본다.
- Phase 3에서는 `repo-side admin` 안의 문서/실데이터/백업 HTML을 archive 또는 assets 후보로 따로 분해해서 본다.

## Phase 3 Dry-Run

### 3-A. 이동 전 source / target / rollback 표

| source | target | reason | rollback |
|------|------|------|------|
| `C:\2POW\03_telegram_py\03_telegram_py` | `C:\2POW_ARCHIVE\telegram\stale\03_telegram_py_nested` | nested stale repo copy 격리 | `C:\2POW\03_telegram_py\03_telegram_py` |
| `C:\2POW\03_telegram_py\runtime` | `C:\2POW_RUNTIME\telegram\repo_runtime_snapshot` | repo 내부 runtime JSON 분리 | `C:\2POW\03_telegram_py\runtime` |
| `C:\2POW\03_telegram_py\bot_watchdog.log` | `C:\2POW_RUNTIME\telegram\repo_logs\bot_watchdog.log` | 로그를 repo 밖으로 분리 | `C:\2POW\03_telegram_py\bot_watchdog.log` |
| `C:\2POW\03_telegram_py\kiwoom_new.log` | `C:\2POW_RUNTIME\telegram\repo_logs\kiwoom_new.log` | 로그를 repo 밖으로 분리 | `C:\2POW\03_telegram_py\kiwoom_new.log` |
| `C:\2POW\03_telegram_py\ms_new.log` | `C:\2POW_RUNTIME\telegram\repo_logs\ms_new.log` | 로그를 repo 밖으로 분리 | `C:\2POW\03_telegram_py\ms_new.log` |
| `C:\2POW\03_telegram_py\onedrive_restore.log` | `C:\2POW_RUNTIME\telegram\repo_logs\onedrive_restore.log` | 로그를 repo 밖으로 분리 | `C:\2POW\03_telegram_py\onedrive_restore.log` |
| `C:\2POW\03_telegram_py\onedrive_sync.log` | `C:\2POW_RUNTIME\telegram\repo_logs\onedrive_sync.log` | 로그를 repo 밖으로 분리 | `C:\2POW\03_telegram_py\onedrive_sync.log` |
| `C:\2POW\03_telegram_py\__pycache__` | `C:\2POW_ARCHIVE\telegram\cache\03_telegram_py___pycache__` | 캐시 표면 격리 | `C:\2POW\03_telegram_py\__pycache__` |
| `C:\2POW\03_telegram_py\note_1pow.zip` | `C:\2POW_ARCHIVE\telegram\imports\note_1pow.zip` | repo 내부 zip 잔재 분리 | `C:\2POW\03_telegram_py\note_1pow.zip` |
| `C:\2POW\03_telegram_py\admin\crm-v8-site.backup-2026-03-03.html` | `C:\2POW_ARCHIVE\admin-bridge\telegram_admin_misc\crm-v8-site.backup-2026-03-03.html` | backup HTML을 code 표면에서 제거 | `C:\2POW\03_telegram_py\admin\crm-v8-site.backup-2026-03-03.html` |
| `C:\2POW\03_telegram_py\admin\수당.xlsx` | `C:\2POW_ASSETS\admin-bridge\examples\수당.xlsx` | 실데이터/예시 엑셀을 assets로 분리 | `C:\2POW\03_telegram_py\admin\수당.xlsx` |
| `C:\2POW\03_telegram_py\admin\수정2행.xlsx` | `C:\2POW_ASSETS\admin-bridge\examples\수정2행.xlsx` | 실데이터/예시 엑셀을 assets로 분리 | `C:\2POW\03_telegram_py\admin\수정2행.xlsx` |
| `C:\2POW\03_telegram_py\admin\통합문서예시.xlsx` | `C:\2POW_ASSETS\admin-bridge\examples\통합문서예시.xlsx` | 실데이터/예시 엑셀을 assets로 분리 | `C:\2POW\03_telegram_py\admin\통합문서예시.xlsx` |
| `C:\2POW\03_telegram_py\admin\클로드작업.docx` | `C:\2POW_ARCHIVE\admin-bridge\telegram_admin_misc\클로드작업.docx` | ad-hoc 문서를 code 표면에서 제거 | `C:\2POW\03_telegram_py\admin\클로드작업.docx` |
| `C:\2POW\kiwoom_new_capture.png` | `C:\2POW_ARCHIVE\root_debug\kiwoom_new_capture.png` | 루트 debug capture 격리 | `C:\2POW\kiwoom_new_capture.png` |
| `C:\2POW\ms_new_capture.png` | `C:\2POW_ARCHIVE\root_debug\ms_new_capture.png` | 루트 debug capture 격리 | `C:\2POW\ms_new_capture.png` |
| `C:\2POW\bot_token.txt` | `C:\2POW_SECRETS\telegram\bot_token.txt` | secret 루트 정리 | `C:\2POW\bot_token.txt` |
| `C:\2POW\allowed_chat_ids.txt` | `C:\2POW_SECRETS\telegram\allowed_chat_ids.txt` | secret 루트 정리 | `C:\2POW\allowed_chat_ids.txt` |
| `C:\2POW\office_allowed_hosts.txt` | `C:\2POW_SECRETS\telegram\office_allowed_hosts.txt` | secret 루트 정리 | `C:\2POW\office_allowed_hosts.txt` |

메모:

- `office_deploy/`는 rollback snapshot이라 이 표의 즉시 이동 대상에서 제외한다.
- `고객관리/*.xlsm`과 `runtime/last_sync.json`은 아직 freeze 범위라 dry-run 대상에만 남기고 실제 1차 이동에는 넣지 않는다.

### 3-B. 권장 작업 순서

1차 배치, 가장 안전:

- `03_telegram_py/03_telegram_py`
- repo 내부 `runtime/`, `*.log`, `__pycache__`
- root debug capture PNG
- telegram-side `admin` 안의 backup HTML / ad-hoc docs / 예시 XLSX

2차 배치, 경로 점검 후:

- root secrets 3종
  - `bot_token.txt`
  - `allowed_chat_ids.txt`
  - `office_allowed_hosts.txt`

3차 배치, 가장 민감:

- `고객관리` 자산
- root live shim 주변 경로 재배치
- `bot.py` / `bot_app` / `config/canonical_map.local.json` 을 건드리는 변경

순서 원칙:

- stale / cache / log / backup부터 먼저 뺀다.
- secrets는 예시 파일과 소비 경로를 점검한 뒤 이동한다.
- `menu34`와 office bot live entry는 마지막까지 freeze 유지한다.

### 3-C. 실제 이동 batch size 원칙

1차 실행 배치 제한:

- 한 번에 한 프로젝트만 건드린다.
- 한 번에 한 concern만 건드린다.
  - 예: `stale copy만`
  - 예: `repo logs만`
  - 예: `repo-side admin XLSX만`
- 1회 배치당 이동 항목은 최대 `5개`
- 1회 배치당 총 이동 용량은 대략 `100MB 이하`

배치 종료 체크:

- 이동 전 `git status` 저장
- 이동 후 경로 존재 여부 재확인
- telegram 관련 표면이면 `menu34` smoke / guard / heartbeat 확인
- 이상 있으면 같은 배치 안에서 rollback 경로로 즉시 복귀

금지:

- `bot.py`와 `repo-side working copy bot.py (removed 2026-04-15)` drift 해소 작업을 폴더 이동 배치와 섞지 않는다.
- `고객관리` 자산 이동을 다른 concern과 같이 묶지 않는다.

## Phase 4 Repo-First Rules

### 4-A. 프로젝트별 git 반영 순서

1순위, `telegram-bot`:

- repo: `C:\2POW\03_telegram_py`
- 이유:
  - root live shim과 가장 강하게 엮여 있음
  - `bot.py` drift와 repo 내부 stale/runtime 표면이 공존
  - `menu34` 보호선 때문에 먼저 기준을 세워야 함

2순위, `admin-bridge`:

- repo: `C:\2POW\admin`
- 이유:
  - root `admin`은 clean한 standalone repo
  - `03_telegram_py/admin` mirror를 정리하려면 canonical repo를 먼저 기준으로 잡아야 함

3순위, `ivwith`:

- repo: `C:\2POW\ivwith`
- 이유:
  - 가장 크고 (`3.1G`) 민감함
  - `menu34` / H시트 / `admin_new_runtime`과 직접 연결돼 있음
  - telegram / admin 표면을 먼저 정리한 뒤 들어가는 것이 안전함

4순위 이후:

- `blog/booyoung-landing`
  - repo는 작고 단순하지만 현재 운영 핵심선과는 멀다
- `jogyeon`
  - 작고 독립적이다
- `myhome`
  - 독립 repo지만 `1.3G` 규모라 별도 자산 전략이 필요하다

### 4-B. repo-first 운영 규칙

핵심:

- 코드 수정은 repo에서 먼저 한다.
- live 반영은 repo 기준으로 preview 후 apply 한다.
- root 직접 수정은 긴급 hotfix만 허용한다.

세부 규칙:

- `telegram`
  - 작업 기준 repo: `C:\2POW\03_telegram_py`
  - live authority: 당분간 `C:\2POW\bot.py`
  - root hotfix가 생기면 같은 날 repo 쪽 문서 또는 대응 패치로 drift를 기록한다.
- `ivwith`
  - 작업 기준 repo: `C:\2POW\ivwith`
  - `admin_new_runtime`는 active runtime surface로 본다.
- `admin-bridge`
  - 작업 기준 repo: `C:\2POW\admin`
  - `03_telegram_py/admin`은 mirror/helper 표면으로 보고 code canonical로 쓰지 않는다.

배포/반영 규칙:

- 배치 시작 전:
  - 해당 repo `git status` 저장
  - 최근 커밋 hash 저장
- 배치 종료 후:
  - 경로 매핑표 갱신
  - repo status 재확인
- telegram 관련이면 추가로:
  - `RUN_MENU34_SHADOW_SMOKE.ps1`
  - `RUN_MENU34_GUARD.ps1`
  - office bot heartbeat 확인
  - `runtime/last_sync.json` / admin mirror 일치 확인

금지:

- `runtime`, `logs`, `locks`, `heartbeat`, `status`, `secrets`, `xlsm`, 실데이터 CSV/XLSX를 git 정본에 넣지 않는다.
- OneDrive를 메인 작업본으로 쓰지 않는다.
- root direct edit와 repo 구조 정리를 같은 배치에 섞지 않는다.

## Batch Execution Log

### Batch 1. telegram low-risk move

실행 시각:

- `2026-04-14 23:05` KST

이동 완료:

- `C:\2POW\03_telegram_py\03_telegram_py`
  - `C:\2POW_ARCHIVE\telegram\stale\03_telegram_py_nested`
- `C:\2POW\03_telegram_py\runtime`
  - `C:\2POW_RUNTIME\telegram\repo_runtime_snapshot\runtime`
- repo log 5종
  - `bot_watchdog.log`
  - `kiwoom_new.log`
  - `ms_new.log`
  - `onedrive_restore.log`
  - `onedrive_sync.log`
  - target: `C:\2POW_RUNTIME\telegram\repo_logs\`
- `C:\2POW\03_telegram_py\__pycache__`
  - `C:\2POW_ARCHIVE\telegram\cache\03_telegram_py___pycache__`
- repo-side admin misc
  - `crm-v8-site.backup-2026-03-03.html`
  - `클로드작업.docx`
  - target: `C:\2POW_ARCHIVE\admin-bridge\telegram_admin_misc\`
- repo-side admin example assets
  - `수당.xlsx`
  - `수정2행.xlsx`
  - `통합문서예시.xlsx`
  - target: `C:\2POW_ASSETS\admin-bridge\examples\`

사전/사후 증적:

- `C:\2POW_RUNTIME\telegram\batch_logs\03_telegram_py_status_before_20260414_230539.txt`
- `C:\2POW_RUNTIME\telegram\batch_logs\03_telegram_py_status_after_20260414_230539.txt`

검증:

- source 경로 소거 확인 완료
- target 경로 생성/이동 확인 완료
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- office heartbeat 확인
  - `status = polling_start`
  - `ivwith_menu34_base_dir = C:\2POW`
- `last_sync_run_id` mirror 유지
  - runtime: `hsheet-20260414-223722`
  - admin mirror: `hsheet-20260414-223722`

다음 배치 후보:

- root debug capture PNG 2종
- root secrets 3종 경로 소비처 점검 후 이동

### Batch 2. root debug + secrets transition

실행 시각:

- `2026-04-14 23:08` KST

이동 완료:

- root debug capture
  - `C:\2POW\kiwoom_new_capture.png`
  - `C:\2POW\ms_new_capture.png`
  - target: `C:\2POW_ARCHIVE\root_debug\`

- secrets canonical relocation
  - `C:\2POW\bot_token.txt` -> `C:\2POW_SECRETS\telegram\bot_token.txt`
  - `C:\2POW\allowed_chat_ids.txt` -> `C:\2POW_SECRETS\telegram\allowed_chat_ids.txt`
  - `C:\2POW\office_allowed_hosts.txt` -> `C:\2POW_SECRETS\telegram\office_allowed_hosts.txt`

전환 방식:

- root legacy 경로는 삭제하지 않고 hard link로 유지했다.
- 따라서 현재는 아래 두 조건이 동시에 성립한다.
  - canonical storage: `C:\2POW_SECRETS\telegram\*`
  - legacy live path compatibility: `C:\2POW\*.txt`

근거:

- 세 파일 모두 root / target 링크 수 `2`
- 내용 일치 확인 완료

consumer 점검 결과:

- root `bot.py`
  - `_read_secret_file(\"bot_token.txt\")`
  - `_read_secret_file(\"allowed_chat_ids.txt\")`
  - `_read_secret_file(\"office_allowed_hosts.txt\")`
- `C:\2POW\03_telegram_py\START_TELEGRAM_BOT_NOW.bat`
  - root `office_allowed_hosts.txt` 에 현재 호스트를 stamp
- repo-side 유틸
  - `codex_work_status.py`, `work_done_notify.py`, `molit_rt_watch.py` 는 repo 로컬 파일 fallback을 여전히 기대

판정:

- 코드 수정 없이 완전 이동하면 운영선이 깨질 수 있었다.
- hard link 전환은 현재 구조에서 가장 안전한 분리 방법이었다.

검증:

- root debug PNG source 소거 확인
- archive target 존재 확인
- secrets root/target 링크 수 `2` 확인
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- office heartbeat 확인
  - `status = polling_start`
  - `ivwith_menu34_base_dir = C:\2POW`

다음 단계 후보:

- repo-side notification 유틸의 secret fallback 경로를 `2POW_SECRETS` 기준으로 정리
- root legacy hard link 제거를 위한 secret path abstraction 설계

### Batch 3. secret path abstraction

실행 시각:

- `2026-04-14 23:14` KST

변경 완료:

- 공통 resolver 추가
  - `C:\2POW\03_telegram_py\bot_security_config.py`
  - `read_secret_text(...)`
  - `resolve_secret_file_path(...)`

- repo-side notification 유틸 canonical secret fallback 적용
  - `codex_work_status.py`
  - `work_done_notify.py`
  - `molit_rt_watch.py`

- office runtime token path 정리
  - `bot_runtime_profile.py`
  - office token 비교 경로를 canonical secret path 기준으로 변경

- live/root + repo bot secret read 경로 정리
  - root `bot.py`
  - repo `repo-side working copy bot.py (removed 2026-04-15)`
  - `office` 프로필의 `bot_token.txt`, `allowed_chat_ids.txt`, `office_allowed_hosts.txt` 는 canonical secret path를 우선 사용

- host stamp write 경로 정리
  - `03_telegram_py/START_TELEGRAM_BOT_NOW.bat`
  - `03_telegram_py/office_recover_and_check.ps1`
  - canonical + legacy path 둘 다 stamp 하도록 변경

검증:

- `py_compile` 통과
- canonical secret resolver 확인
  - `bot_token.txt -> C:\2POW_SECRETS\telegram\bot_token.txt`
  - `allowed_chat_ids.txt -> C:\2POW_SECRETS\telegram\allowed_chat_ids.txt`
  - `office_allowed_hosts.txt -> C:\2POW_SECRETS\telegram\office_allowed_hosts.txt`
- `codex_work_status`, `work_done_notify`, `molit_rt_watch` 모두 canonical secret read 확인
- office bot 재기동
  - 새 PID: `28956`
  - `bot_version: 2026-04-14 23:14:08`
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- heartbeat 최종 상태
  - `polling_start`
  - `ivwith_menu34_base_dir = C:\2POW`

현재 상태:

- `C:\2POW_SECRETS\telegram\*` 이 canonical
- root `*.txt` 는 아직 hard link 기반 legacy compatibility 표면

다음 단계 후보:

- remaining root/utility consumers 최종 재점검 후 hard link 제거
- `START_TELEGRAM_BOT_NOW.bat` / `office_recover_and_check.ps1` 의 legacy stamp 제거 시점 결정

### Batch 4. hard link final sweep

실행 시각:

- `2026-04-14 23:15` KST

점검 결과:

- code-level secret reader는 canonical 쪽으로 거의 정리됨
  - root `bot.py`
  - repo `repo-side working copy bot.py (removed 2026-04-15)`
  - `bot_runtime_profile.py`
  - `codex_work_status.py`
  - `work_done_notify.py`
  - `molit_rt_watch.py`

- office host stamp는 아직 legacy path도 함께 유지
  - `03_telegram_py/START_TELEGRAM_BOT_NOW.bat`
  - `03_telegram_py/office_recover_and_check.ps1`

- codex runtime은 별도 예외
  - `_restart_codex_bot.ps1` 의 `allowed_chat_ids.txt` 는 runtime 전용 경로를 계속 사용

판정:

- 현재는 hard link를 즉시 제거하지 않는다.
- 이유:
  - legacy root path를 아직 병행 stamp 하고 있음
  - manual/ad-hoc 소비처까지 완전히 닫았다고 보기엔 이르다
  - 운영 영향 없이 한 번 더 컷오버 묶음으로 빼는 편이 안전하다

현재 결론:

- `C:\2POW_SECRETS\telegram\*` 는 canonical
- root `*.txt` hard link는 compatibility bridge
- 다음 컷오버에서 root legacy 파일 제거 여부를 결정한다

### Batch 5. daily_sync + docs/rules sync

실행 시각:

- `2026-04-14 23:20` KST

변경 완료:

- `ivwith/daily_sync.py`
  - `_load_bot_config()` 를 legacy root direct open 대신 shared secret resolver 기준으로 변경
  - `bot_token.txt`, `allowed_chat_ids.txt` 는 canonical secret path를 우선 사용

- secret authority 문서 drift 정리
  - `03_telegram_py/HANDOVER.md`
  - `03_telegram_py/DUAL_BOT_RUNTIME.md`
  - office token canonical authority를 `C:\2POW_SECRETS\telegram\bot_token.txt` 기준으로 정리
  - root `.txt` 는 compatibility bridge라고 명시

- Codex 운영 규칙 보강
  - `AGENTS.md`
  - 추가 섹션:
    - `Live Entry Points`
    - `menu34 Freeze Boundary`
    - `Status Reporting Format`
    - `Parallel Session Protocol`

검증:

- `python3 -m py_compile` 통과
- `daily_sync` import 확인
- `daily_sync._load_bot_config()` 로 token/chat id 로딩 확인
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- office heartbeat 유지
  - `polling_start`
  - `pid = 28956`
  - `ivwith_menu34_base_dir = C:\2POW`

현재 판단:

- `daily_sync.py` legacy secret read 블로커는 해소됐다
- hard link 제거는 여전히 별도 컷오버로 본다
  - 이유: legacy stamp path와 manual/ad-hoc 소비처 최종 정리가 아직 남아 있다

### Batch 6. root legacy secret cutover

실행 시각:

- `2026-04-14 23:25` KST

변경 완료:

- canonical-only host stamp 전환
  - `03_telegram_py/START_TELEGRAM_BOT_NOW.bat`
  - `03_telegram_py/office_recover_and_check.ps1`
  - `office_allowed_hosts.txt` 는 이제 canonical path만 stamp

- 운영 문서 후속 정리
  - `03_telegram_py/README_NOTEBOOK_SETUP.txt`
  - `03_telegram_py/OFFICE_TOMORROW_RUNBOOK.md`
  - `03_telegram_py/HANDOVER.md`
  - `03_telegram_py/DUAL_BOT_RUNTIME.md`
  - `AGENTS.md`

- root legacy secret path 제거
  - `C:\2POW\bot_token.txt`
  - `C:\2POW\allowed_chat_ids.txt`
  - `C:\2POW\office_allowed_hosts.txt`

검증:

- `python3 -m py_compile` 통과
- `daily_sync._load_bot_config()` 로 canonical secret read 확인
- `codex_work_status.py`, `work_done_notify.py`, `molit_rt_watch.py` canonical secret read 확인
- office bot 재기동 완료
  - 새 PID: `37508`
  - `bot_version: 2026-04-14 23:25:10`
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- heartbeat 최종 상태
  - `polling_start`
  - `ivwith_menu34_base_dir = C:\2POW`
- root legacy `.txt` 재생성되지 않음 확인

최종 상태:

- office/customer bot secret authority
  - `C:\2POW_SECRETS\telegram\bot_token.txt`
  - `C:\2POW_SECRETS\telegram\allowed_chat_ids.txt`
  - `C:\2POW_SECRETS\telegram\office_allowed_hosts.txt`
- root `C:\2POW\*.txt` secret bridge는 제거 완료

### Batch 7. 검수 보정 후속 정리

실행 시각:

- `2026-04-14 23:32` KST

변경 완료:

- `ivwith` standalone import 회귀 방지
  - `ivwith/daily_sync.py`
  - `03_telegram_py/bot_security_config.py` import 실패 시 local fallback helper로 계속 동작
  - 통합 workspace에서는 shared resolver를 그대로 사용

- office runtime 문서 오기 수정
  - `03_telegram_py/DUAL_BOT_RUNTIME.md`
  - office PID 경로를 `C:\2POW\runtime\root_bot\state\bot.pid` 로 수정
  - office lock 경로를 `C:\2POW\runtime\root_bot\locks\bot.lock` 로 수정

검증:

- `python3 -m py_compile` 통과
- `ivwith` standalone 시뮬레이션 import 확인
  - sibling `03_telegram_py` 없는 임시 checkout 구조에서 `daily_sync.py` import 성공
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- office heartbeat 유지
  - `polling_start`
  - `pid = 37508`
  - `ivwith_menu34_base_dir = C:\2POW`

현재 판단:

- `daily_sync.py` 의 standalone import 회귀는 해소됐다
- `DUAL_BOT_RUNTIME.md` 의 office PID/lock 경로 문서도 현재 runtime profile과 일치한다
- 남은 큰 정리 과제는 repo별 커밋 분리와 root/repo `bot.py` drift 판단이다

### Batch 8. standalone lockfile fallback 보강

실행 시각:

- `2026-04-14 23:35` KST

변경 완료:

- `ivwith` lockfile 의존성 fallback 추가
  - `ivwith/daily_sync.py`
  - `from lockfile import ...` 실패 시 local `LockError`, `acquire_lock`, `release_lock` fallback 사용
  - 기존 `C:\2POW` 통합 workspace에서는 shared/root shim import를 그대로 사용

검증:

- `python3 -m py_compile` 통과
- `ivwith` standalone 시뮬레이션 import 확인
  - sibling `03_telegram_py` 없음
  - root `lockfile.py` 없음
  - `daily_sync.py` import 성공
  - fallback `acquire_lock()` / `release_lock()` 동작 확인
- `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
- `RUN_MENU34_GUARD.ps1` 통과
- office heartbeat 유지
  - `polling_start`
  - `pid = 37508`
  - `ivwith_menu34_base_dir = C:\2POW`

현재 판단:

- `ivwith` standalone import 회귀는 `bot_security_config` 와 `lockfile` 둘 다 기준으로 닫혔다
- 남은 큰 정리 과제는 repo별 커밋 분리와 root/repo `bot.py` drift 판단이다

### Batch 9. repo 커밋 분리 / root-repo drift 기준선 정리

실행 시각:

- `2026-04-14 23:51` KST

사실 확인:

- `03_telegram_py` 는 현재 변경 표면이 가장 큼
  - tracked 변경 26개
  - untracked 신규 모듈 다수
  - 문서 / restart / watchdog / secret resolver / menu34 guard / `bot.py` 리팩터가 한 데 섞여 있음

- `ivwith` 는 운영 로직 + 생성물 + 신규 규칙 파일이 섞여 있음
  - tracked 변경
    - `daily_sync.py`
    - `ivwith_report.py`
    - `send_customer_report.py`
    - `HANDOVER.md`
    - `customer_flow_dashboard_data.js`
    - `new_admin/customer_portal_data.js`
    - `admin_new_runtime/WINSCP_SYNC_TARGETS.txt`
    - `admin_new_runtime/assets/last_sync.json`
  - untracked
    - `customer_status_rules.py`
    - `tests/`
    - `admin_new_runtime/README.md`

- `admin` repo는 현재 `.gitignore` 1건만 변경
- `blog/booyoung-landing` 은 현재 작업 트리 깨끗함

root/repo `bot.py` 드리프트 판단:

- live authority는 아직 root `C:\2POW\bot.py`
  - `03_telegram_py/START_TELEGRAM_BOT_NOW.bat`
  - `03_telegram_py/bot_runtime_profile.py`
  - office heartbeat 실제 출력 기준으로 root runtime chain 사용 중

- root `bot.py` 가 앞선 부분
  - `bot_runtime_polling.start_bot_runtime(...)` 사용
  - profile/runtime/state/pid/lock/allowed_chat gating 변수 연결
  - runtime heartbeat/status/pid/lock 정체성 관리가 root 쪽에 더 정리됨

- repo `repo-side working copy bot.py (removed 2026-04-15)` 에 남아 있는 부분
  - legacy `사무실코덱스대화` 프롬프트/대화 history 상태
  - `codex_task_status.json`, `codex_telegram_commands.jsonl` 직접 경로
  - legacy heartbeat/status 경로 처리 흔적

- 두 파일은 둘 다 `2026-04-14 23:13` 수정본이지만 내용은 아직 큼
  - no-index diff stat 기준
    - `482 insertions`
    - `390 deletions`
  - 즉시 한쪽을 다른 쪽으로 덮는 단계는 아님

커밋 분리 권장:

- Commit A. `ivwith` 안전 커밋 후보
  - `daily_sync.py`
  - `customer_status_rules.py`
  - `tests/`
  - `HANDOVER.md`
  - 필요 시 `admin_new_runtime/README.md`
  - 메모: `last_sync.json`, dashboard js 생성물은 별도 판단

- Commit B. `03_telegram_py` 운영 안정화 커밋 후보
  - secret authority / watchdog / restart / audit / status reporting
  - `DUAL_BOT_RUNTIME.md`, `HANDOVER.md`, `README_NOTEBOOK_SETUP.txt`, `OFFICE_TOMORROW_RUNBOOK.md`
  - `START_TELEGRAM_BOT_NOW.bat`, `_restart_*`, `office_recover_and_check.ps1`, `codex_work_status.py`, `bot_runtime_profile.py`
  - `RUN_MENU34_GUARD.ps1`, `RUN_MENU34_SHADOW_SMOKE*.ps1|.bat`

- Commit C. `03_telegram_py` 구조 리팩터 후보
  - 신규 모듈
    - `bot_security_config.py`
    - `bot_env_config.py`
    - `bot_runtime_state.py`
    - `bot_chat_state.py`
    - `bot_task_runner.py`
    - `home_dispatch.py`
    - `bot_state_*`
  - 관련 `bot.py`, `bot_app/menus/home.py`, `bot_app/menus/ivwith_menu.py`
  - 메모: 이 묶음은 root/repo `bot.py` canonical 결정 전까지 review 강도 높게 가야 함

현재 권장 다음 작업:

- 바로 커밋 가능한 건 `ivwith` 안전 커밋 후보부터
- 그 다음 `03_telegram_py` 는 운영 안정화 커밋과 구조 리팩터 커밋을 분리
- root/repo `bot.py` canonical 통합은 별도 트랙으로 다룬다

### Batch 10. ivwith 안전 커밋 분리

실행 시각:

- `2026-04-14 23:54` KST

실행 내용:

- `ivwith` 에서 생성물 3종은 제외하고 로직/문서/테스트만 staging
  - 포함:
    - `daily_sync.py`
    - `ivwith_report.py`
    - `send_customer_report.py`
    - `customer_status_rules.py`
    - `tests/test_customer_status_rules.py`
    - `HANDOVER.md`
    - `admin_new_runtime/README.md`
    - `admin_new_runtime/WINSCP_SYNC_TARGETS.txt`
  - 제외:
    - `admin_new_runtime/assets/last_sync.json`
    - `customer_flow_dashboard_data.js`
    - `new_admin/customer_portal_data.js`

- 검증:
  - `python3 -m unittest discover -s ivwith/tests -p 'test_*.py'`
  - `python3 -m py_compile daily_sync.py ivwith_report.py send_customer_report.py customer_status_rules.py`

- 커밋 완료
  - repo: `ivwith`
  - commit: `82f5b87`
  - message: `Refactor ivwith status rules and secret loading`

현재 상태:

- `ivwith` repo에는 생성물 3종만 남아 있음

### Batch 11. telegram 운영 안정화 커밋 분리

실행 시각:

- `2026-04-14 23:54` KST

실행 내용:

- `03_telegram_py` 에서 `bot.py` / menu / 신규 state 모듈은 제외하고 운영 안정화 표면만 staging
  - 포함:
    - runtime / secret / watchdog / restart / audit / status reporting / handover 문서
    - `RUN_MENU34_GUARD.ps1`
    - `RUN_MENU34_SHADOW_SMOKE.ps1`
    - `RUN_MENU34_SHADOW_SMOKE.bat`
    - `bot_security_config.py`
  - 제외:
    - `bot.py`
    - `bot_app/menus/home.py`
    - `bot_app/menus/ivwith_menu.py`
    - 신규 `bot_*` state/runtime 구조 모듈
    - `BOT_REFACTOR_TODO.md`

- 검증:
  - `python3 -m py_compile` 주요 운영 python 파일 통과
  - `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
  - `RUN_MENU34_GUARD.ps1` 통과

- 커밋 완료
  - repo: `03_telegram_py`
  - commit: `ea2fe00`
  - message: `Stabilize telegram runtime paths and secret authority`

현재 상태:

- `03_telegram_py` 작업트리에는 구조 리팩터 표면만 남음
- 남은 핵심은 `bot.py` / menu / 신규 state 모듈과 root/repo canonical 판단이다

### Batch 12. telegram 구조 리팩터 커밋 분리

실행 시각:

- `2026-04-14 23:56` KST

실행 내용:

- `03_telegram_py` 남은 구조 리팩터 표면을 한 축으로 staging
  - 포함:
    - `bot.py`
    - `bot_app/menus/home.py`
    - `bot_app/menus/ivwith_menu.py`
    - 신규 helper/state/runtime 모듈
      - `bot_chat_state.py`
      - `bot_env_config.py`
      - `bot_event_flow.py`
      - `bot_instance_guard.py`
      - `bot_message_preroute.py`
      - `bot_runtime_state.py`
      - `bot_script_runners.py`
      - `bot_state_admin_followup.py`
      - `bot_state_due_customers.py`
      - `bot_state_ms_review.py`
      - `bot_state_sales_briefing_rt.py`
      - `bot_state_wait_ixio.py`
      - `bot_task_runner.py`
      - `home_dispatch.py`
    - `BOT_REFACTOR_TODO.md`

- 검증:
  - 구조 리팩터 표면 `python3 -m py_compile` 통과
  - `RUN_MENU34_SHADOW_SMOKE.ps1` 통과
  - `RUN_MENU34_GUARD.ps1` 통과

- 커밋 완료
  - repo: `03_telegram_py`
  - commit: `06980d3`
  - message: `Refactor telegram bot into helper modules`

최종 상태:

- `03_telegram_py` 작업트리 clean
- `ivwith` 는 생성물 3종만 남음
  - `admin_new_runtime/assets/last_sync.json`
  - `customer_flow_dashboard_data.js`
  - `new_admin/customer_portal_data.js`
- 남은 큰 결정은 root live `C:\2POW\bot.py` 와 repo `repo-side working copy bot.py (removed 2026-04-15)` canonical 통합 판단뿐이다

### Batch 13. ivwith 생성물 3종 마감 커밋

실행 시각:

- `2026-04-15 00:03` KST

실행 내용:

- `ivwith` 생성물 3종을 최종 상태로 커밋
  - `admin_new_runtime/assets/last_sync.json`
  - `customer_flow_dashboard_data.js`
  - `new_admin/customer_portal_data.js`

- 커밋 완료
  - repo: `ivwith`
  - commit: `89fc2ce`
  - message: `Refresh ivwith generated dashboard assets`

현재 상태:

- `ivwith` 작업트리 clean

### Batch 14. live/repo bot authority 최종 기준선 확정

실행 시각:

- `2026-04-15 00:03` KST

실행 내용:

- `03_telegram_py` 문서 기준선 보강
  - `HANDOVER.md`
  - `DUAL_BOT_RUNTIME.md`
- root `AGENTS.md`에도 동일 원칙 반영

최종 결정:

- live runtime authority = `C:\2POW\bot.py`
- helper/worktree 영역 = `C:\2POW\03_telegram_py`
- repo-side stale `03_telegram_py\bot.py`는 제거
- 이후 `bot.py` 작업은 root 단일 authority 기준으로만 진행

- 커밋 완료
  - repo: `03_telegram_py`
  - commit: `dfa952e`
  - message: `Clarify live and repo bot authority`

정리 트랙 종료 상태:

- `ivwith` 작업트리 clean
- `03_telegram_py` 작업트리 clean
- stale `index.lock` 제거 완료
- office heartbeat 유지
  - `polling_start`
  - `pid = 37508`
  - `bot_version = 2026-04-14 23:25:10`
  - `ivwith_menu34_base_dir = C:\2POW`
- 이번 정리 트랙 기준 남은 작업 없음
- 이후 남는 일은 새 트랙인 `bot.py cutover` 또는 `생성물 추적 정책 개편`으로 분리한다

### Batch 15. `bot.py` 단일 파일 마감

실행 시각:

- `2026-04-15 00:xx` KST

실행 내용:

- stale `C:\2POW\03_telegram_py\bot.py` 제거
- rollback snapshot `C:\2POW\03_telegram_py\office_deploy\bot.py`를 `root_bot.rollback.py`로 변경
- 문서/가드/운영 규칙을 root 단일 `bot.py` 기준으로 보강

최종 상태:

- `C:\2POW` 아래 `bot.py`는 root `C:\2POW\bot.py` 하나만 남음
- `03_telegram_py`는 wrapper/helper/worktree만 유지
- rollback snapshot은 `office_deploy\root_bot.rollback.py`
