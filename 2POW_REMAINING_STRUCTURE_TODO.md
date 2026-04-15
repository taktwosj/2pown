# 2POW 남은 구조 정리 TODO

기준일: 2026-04-15

## 현재 기준선

- live telegram 본체는 `C:\2POW\bot.py` 하나다.
- `C:\2POW\03_telegram_py`는 wrapper/helper/worktree 영역이다.
- secret canonical 경로는 `C:\2POW_SECRETS\telegram\*` 이다.
- runtime 상태파일은 `C:\2POW\runtime\**` 아래에 둔다.
- archive 성격 파일은 `C:\2POW_ARCHIVE\**` 로 분리하기 시작했다.
- `03_telegram_py`와 `ivwith` git 작업트리는 현재 clean 상태다.

## 이번 TODO의 목적

- `03_telegram_py` 안에 남은 역사 폴더와 잡자산을 더 납작하게 만든다.
- root `C:\2POW` 와 nested repo 경계를 더 명확하게 만든다.
- stale 문서/캐시/복사본 때문에 다시 헷갈릴 표면을 줄인다.

## Freeze / 주의

- `menu34` 경계는 그대로 유지한다.
  - `C:\2POW\bot.py`
  - `C:\2POW\03_telegram_py\bot_app\menus\ivwith_menu.py`
  - `C:\2POW\ivwith\daily_sync.py`
- telegram 구조 변경이 포함되면 최소 검증은 아래를 다시 돈다.
  - `python3 -m py_compile`
  - `RUN_MENU34_SHADOW_SMOKE.ps1`
  - `RUN_MENU34_GUARD.ps1`
  - heartbeat 확인

## Phase R1. 03_telegram_py 내부 납작화

- [x] `03_telegram_py/01_lhshapt` 를 `C:\2POW_ARCHIVE\telegram\legacy_roots` 로 이동
- [x] `03_telegram_py/02_jogyeon` 를 `C:\2POW_ARCHIVE\telegram\legacy_roots` 로 이동
- [x] `03_telegram_py/admin` mirror를 `C:\2POW_ARCHIVE\telegram\legacy_roots\admin_mirror` 로 이동
- [x] `03_telegram_py` 루트의 주택 데이터/산출물 미러 정리
  - `eeem-clean.html`
  - `eeem-clean-data.js`
  - `eeem-private-data.js`
  - `hwspr_*.csv`
- [x] root 의미 없는 잔파일 정리
  - `a.txt`
  - `bot_capture.png`
  - `office_allowed_hosts.txt`

## Phase R2. office_deploy 표면 축소

- [x] `03_telegram_py/office_deploy` 안에서 진짜 필요한 롤백 자산만 남기기
- [x] 현재 남아 있는 deploy 복사 스크립트/문서가 helper 인지 stale 인지 판정
  - `OFFICE_TOMORROW_RUNBOOK.md`
  - `README_NOTEBOOK_SETUP.txt`
  - `RUN_TELEGRAM_MENU_RUNTIME_AUDIT.bat`
  - `START_TELEGRAM_BOT_NOW.bat`
  - `_restart_bot.ps1`
  - `office_recover_and_check.ps1`
  - `bot_watchdog.ps1`
- [x] `office_deploy`는 `root_bot.rollback.py` + 최소 README 수준까지 축소

## Phase R3. stale 문서 참조 정리

- [x] `HANDOVER.md` 상단에 historical reference 범위 명시
- [x] `PROJECT_INDEX_2026-03-05.md` stale 운영 기준 갱신
- [x] `익시오_파싱_지침서_v3.md` 의 옛 `1POW/repo-side working copy bot.py (removed 2026-04-15)` 경로 정리
- [x] root 문서와 meta redirect 문서에서 주요 운영 참조 갱신

## Phase R4. 캐시 / 생성물 위생 정리

- [x] root `C:\2POW\__pycache__` 정리
- [x] `03_telegram_py/__pycache__` 정리
- [x] `runtime/verify/pycache_temp` 정리
- [x] `.gitignore` 로 막아야 할 캐시/산출물 재점검

## Phase R5. root 2POW 문서/경계 슬림화

- [x] root one-off 정리 문서 archive 이동
  - `1POW_DELETE_HANDOVER_2026-04-10.md`
  - `루트파일정리실행표_2026-04-09.md`
  - `2POW_PROJECTS_LOCAL_TODO.md`
- [x] `2POW` 루트에는 현재 운영 문서와 실행 파일만 남기기
- [x] 장기 과제 메모는 이 TODO로 단일화

## 권장 실행 순서

1. `Phase R3` 문서 stale 참조 정리
2. `Phase R4` 캐시/pycache 정리
3. `Phase R1` 의 명확한 역사 폴더/산출물 분리
4. `Phase R2` office_deploy 축소
5. `Phase R5` root 경계 슬림화

## 완료 기준

- `03_telegram_py` 는 telegram helper/worktree 역할만 남는다.
- 주택/조견표/admin mirror/history 자산은 archive 로 이동한다.
- `bot.py` / secret / runtime authority 문서가 현재 구조와 충돌하지 않는다.
- root `C:\2POW` 는 active control doc + live runtime 진입점만 남긴다.
- 각 phase 종료 시 git 상태와 `menu34` 검증 결과를 함께 남긴다.

## 완료 상태

- `Phase R1`, `Phase R2`, `Phase R5` 실행 완료
- telegram repo 구조 정리 커밋: `23e45c4` `Archive legacy mirrors and slim deploy surface`
- 문서 stale 참조 정리 커밋: `33692cb` `Clean stale bot path references in docs`
- 남은 후속은 새 요청이 있을 때만 연다
