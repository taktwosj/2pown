# 1POW 삭제 인수인계 (2026-04-10)

목표: `C:\1POW`를 완전히 제거하고, 운영/문서/실자산의 canonical을 `C:\2POW`로 확정한다.

## 1) 완료한 변경

### A. canonical 경로/문서 정리
- 정본 규칙 문서 제목을 `2POW` 기준으로 전환:
  - `C:\1POW_META\AGENTS.md`
  - `C:\2POW\AGENTS.md`
  - `C:\1POW_META\CLAUDE.md`
  - `C:\1POW_META\docs/START.md`
  - `C:\2POW\docs/START.md`
  - `C:\2POW\README.md`
- `OFFICE_RUNTIME`/`EXCEL_ASSET_RULE`을 `C:\2POW` 기준으로 수정:
  - `C:\1POW_META\docs/OFFICE_RUNTIME.md`
  - `C:\2POW\docs/OFFICE_RUNTIME.md`
  - `C:\1POW_META\docs/EXCEL_ASSET_RULE.md`
  - `C:\2POW\docs/EXCEL_ASSET_RULE.md`
- `SYSTEM_MAP`에 legacy 경로를 `RETIRED_1POW_2026-04-10` 기준으로 명시:
  - `C:\1POW_META\docs/SYSTEM_MAP.md`
  - `C:\2POW\docs/SYSTEM_MAP.md`
- Office workbook handover에서 `C:\2POW\고객관리\통합관리.xlsm`로 수정:
  - `C:\1POW_META\docs/projects/7-office-workbook/HANDOVER.md`
  - `C:\2POW\docs/projects/7-office-workbook/HANDOVER.md`
- 조견/뱅클리 handover에서 legacy 경로를 retired 표기로 수정:
  - `C:\2POW\jogyeon\HANDOVER.md`
  - `C:\2POW\jogyeon\bankly\HANDOVER.md`
- `ivwith` 포인터와 WinSCP 대상 경로를 `2POW` 기준으로 수정:
  - `C:\2POW\ivwith\HANDOVER.md`
  - `C:\2POW\ivwith\admin_new_runtime\WINSCP_SYNC_TARGETS.txt`
- Admin 고도화 handover에서 legacy 스냅샷 경로를 retired 기준으로 수정:
  - `C:\1POW_META\docs/projects/9-admin-new/HANDOVER.md`
  - `C:\2POW\docs/projects/9-admin-new/HANDOVER.md`

### B. 프로젝트 레지스트리 정리
- `workspace_root`를 `C:\2POW`로 변경하고, blog/myhome local_path를 `2POW` 기준으로 정리:
  - `C:\1POW_META\meta/project_registry.json`
  - `C:\1POW\meta/project_registry.json`
  - `C:\2POW\meta/project_registry.json`
- ivwith(#4) authority를 `2POW`로 정리.
- legacy 복사본은 `RETIRED_1POW_2026-04-10`로 이동 예정 표기.

### C. 실행/런타임 스크립트 기본 경로 전환
- codex watchdog/restart 및 메뉴 스크립트의 기본 경로를 `C:\2POW`로 교체:
  - `C:\2POW\03_telegram_py\_restart_codex_bot.ps1`
  - `C:\2POW\03_telegram_py\codex_watchdog.ps1`
  - `C:\2POW\03_telegram_py\RUN_MOLIT_ALERT_NOW.bat`
  - `C:\2POW\03_telegram_py\RUN_MOLIT_ALERT_NOW.vbs`
  - `C:\2POW\03_telegram_py\RUN_TELEGRAM_MENU_RUNTIME_AUDIT.bat`
  - `C:\2POW\03_telegram_py\RUN_MENU34_SHADOW_SMOKE.bat`
  - `C:\2POW\03_telegram_py\RUN_MENU34_SHADOW_SMOKE.ps1`
  - `C:\2POW\03_telegram_py\install_molit_alert_task.bat`
  - `C:\2POW\03_telegram_py\office_runtime_audit.ps1`
  - `C:\2POW\03_telegram_py\office_import_smoke.ps1`
  - `C:\2POW\03_telegram_py\office_recover_and_check.ps1`
  - `C:\2POW\03_telegram_py\queue_codex_approval.py` (DEFAULT_BASE_DIR)

### D. 엑셀 경로 기본 후보 보강
- `bot.py`가 우선 `C:\2POW\고객관리\통합관리.xlsm`을 보도록 후보 추가:
  - `C:\2POW\bot.py`
  - `C:\2POW\03_telegram_py\bot.py`
- `daily_sync.py`/`ivwith_report.py` 기본 후보에 `C:\2POW\고객관리\통합관리.xlsm` 추가:
  - `C:\2POW\ivwith\daily_sync.py`
  - `C:\2POW\ivwith\ivwith_report.py`

### E. 고객관리 실자산 이동
`C:\1POW\고객관리`의 실파일을 `C:\2POW\고객관리`로 복제 완료.
- `C:\2POW\고객관리\통합관리.xlsm` (canonical 이름 추가)
- `C:\2POW\고객관리\260321_190955_통합관리.xlsm`
- `C:\2POW\고객관리\통합관리.xlsm.20260314-181208.bak`
- `C:\2POW\고객관리\README_GIT.md`, `.gitignore`, `update_log.csv`

## 2) 검증

- `python3 -m py_compile` 통과:
  - `C:\2POW\bot.py`
  - `C:\2POW\03_telegram_py\bot.py`
  - `C:\2POW\ivwith\daily_sync.py`
  - `C:\2POW\ivwith\ivwith_report.py`
  - `C:\2POW\03_telegram_py\queue_codex_approval.py`
- `project_registry.json` 3종 JSON 파싱 OK.
- 현재 실행 중 `C:\1POW` 경로 프로세스는 확인되지 않음.
- 예약 작업 스케줄러에서 `C:\1POW` 사용 흔적은 확인되지 않음.

## 3) 삭제 진행 상태

### A. 현재 상태
- `C:\1POW`는 아직 존재한다.
- `C:\RETIRED_1POW_2026-04-10` 폴더는 생성됨.
- `C:\1POW` → `C:\RETIRED_1POW_2026-04-10` **rename 시도는 Permission denied**로 실패.
- 개별 파일 이동은 일부 성공 (`README.md` 등), 하지만 `.claude` 등 일부 항목에서 권한 에러로 중단.

### B. 삭제 전 잠금 이슈
다음 항목이 이동을 막는 원인일 수 있다:
- `C:\1POW\.claude` (권한/사용 중)
- `.git`, `.vscode`, 실행 중 프로세스나 파일 핸들
- WSL에서 열려 있는 현재 작업 디렉토리

## 4) 남은 작업

1) `C:\1POW`를 현재 작업/세션에서 완전히 벗어난 뒤 재시도.
   - WSL 작업 디렉토리를 `C:\2POW` 또는 `C:\`로 이동하고 다시 이동/삭제.
2) `C:\1POW` 전체를 `C:\RETIRED_1POW_2026-04-10`로 이동:
   - `mv` 또는 `robocopy`/`move` 방식으로 전체 디렉터리 이동
3) `C:\1POW` 경로가 더 이상 존재하지 않는지 확인.
4) `C:\RETIRED_1POW_2026-04-10` 보관 여부 결정:
   - 즉시 삭제할지, 일정 기간 보관할지 사용자 결정.

## 5) 참고 파일

- 2POW 경로 정리 기록:
  - `C:\1POW\CODEX_HANDOVER_2POW_CUTOVER.md` (과거 기록)
  - `C:\2POW\docs/SYSTEM_MAP.md`
  - `C:\1POW_META\meta/project_registry.json`
  - `C:\2POW\docs/projects/7-office-workbook/HANDOVER.md`

## 6) 현재 실행 기준 요약

- Workspace root: `C:\2POW`
- 텔레그램 bot runtime: `C:\2POW\bot.py`
- 텔레그램 repo canonical: `C:\2POW\03_telegram_py`
- daily_sync canonical: `C:\2POW\ivwith\daily_sync.py`
- Excel canonical: `C:\2POW\고객관리\통합관리.xlsm`

---

이 문서는 `C:\2POW\1POW_DELETE_HANDOVER_2026-04-10.md`로 저장됨.
