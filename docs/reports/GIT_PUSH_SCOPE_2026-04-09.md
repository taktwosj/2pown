# Git 업로드 범위 보고서

작성일: 2026-04-09  
기준 경로: `C:\1POW`, `C:\1POW_META`  
작성 기준: 각 repo의 `git status --short --branch`

## 결론
집에서 새 로컬을 받는 방식 자체는 맞다.  
다만 지금 상태에서 `C:\1POW`나 `C:\1POW_META`를 통째로 push하면 안 된다.
정확한 원칙은 아래와 같다.
- `바로 push 가능`: 정리 범위가 비교적 명확한 repo
- `선별 push 필요`: repo가 더러워서 의도한 파일만 골라서 올려야 하는 repo
- `지금 push 금지`: unrelated 변경이 너무 많아서 지금 그대로 올리면 안 되는 repo

## 1. 바로 push 가능

### A. `C:\1POW\02_jogyeon`
올릴 범위:
- `HANDOVER.md`
- `README.md`
- `bankly/HANDOVER.md`
- `bankly/bankly_geumyeok_snapshot.js`
- `bankly/bankly_geumyeok_source.json`
- `bankly/build_bankly_geumyeok_snapshot.py`
- `bankly/export_financial_table_xlsx.py`
- `bankly/export_geumyeok_sheet.py`
- `bankly/gen_docx.py`
- `bankly/gen_excel.py`
- `bankly/system-map.html`
- `bankly/금융사이트.html`
- `bankly/금융조견.html`
의미:
- BANKLY를 `02_jogyeon/bankly` 기준으로 옮긴 정리
- 조견표/스냅샷/생성 스크립트 최신 기준

### B. `C:\1POW\admin`
올릴 범위:
- `REMOTE_QUICK_START.md`
- 삭제 반영:
  - `HOME_1_OPEN_CRM_AND_COPY_URL.bat`
  - `_admin_new_work/**`
  - `bankly/**`
  - `bankly_geumyeok_snapshot.js`
  - `export_financial_table_xlsx.py`
  - `tools/export_geumyeok_sheet.py`
  - `crm-v7-table.jsx`
  - `crm-v8-site.html`
  - `crm-v9-site.html`
  - `금융조견.html`
의미:
- `admin`에서 BANKLY와 대형 `_admin_new_work`를 비운 정리 commit

### C. `C:\1POW\03_telegram_py`
올릴 범위:
- 수정:
  - `HANDOVER.md`
  - `OFFICE_TOMORROW_RUNBOOK.md`
  - `_restart_bot.ps1`
  - `bot.py`
  - `bot_watchdog.ps1`
- 신규:
  - `DUAL_BOT_RUNTIME.md`
  - `START_CODEX_WATCHDOG_NOW.bat`
  - `_restart_codex_bot.ps1`
  - `_restart_office_bot.ps1`
  - `bot_runtime_profile.py`
  - `codex_watchdog.ps1`
  - `run_codex_bot.py`
  - `run_office_bot.py`
의미:
- office/codex 런타임 분리와 watchdog 정리

## 2. 선별 push 필요

### A. `C:\1POW\ivwith`
지금 의도한 업로드 범위:
- `refresh_customer_flow_assets.py`
- `admin_new_runtime/**`
지금 제외 권장:
- `.venv_live/**`
- `_py_probe.txt`
- 검토 전 보류:
  - `customer_flow_dashboard_data.js`
  - `daily_sync.py`
  - `ivwith_report.py`
  - `new_admin/customer_portal_data.js`
  - `send_customer_report.py`
의미:
- `admin/_admin_new_work`를 `ivwith/admin_new_runtime`로 흡수한 부분만 올리고,
- 기존부터 있던 다른 dirty 변경은 분리해야 한다.

### B. `C:\1POW\projects\blog`
지금 의도한 업로드 범위:
- 수정:
  - `.gitignore`
  - `README.md`
- 삭제:
  - `run.py`
  - `sample.config.json`
- 신규:
  - `config/**`
  - `docs/**`
  - `drafts/**`
  - `inbox/**`
  - `references/**`
  - `scripts/**`
  - `wordpress/**`
의미:
- 블로그 구조 재편은 올릴 수 있지만 범위가 크므로 별도 commit이 안전하다.

## 3. 지금 push 금지

### A. `C:\1POW`

지금 그대로 통째 push 금지 이유:

- 루트 repo 안에 unrelated 변경, 삭제, 신규 파일이 너무 많다
- cleanup 산출물, runtime, quarantine, 문서, 루트 스크립트가 한 번에 섞여 있다
- 현재 상태로는 `정리 commit`이 아니라 `작업장 전체 dump`에 가깝다

### B. `C:\1POW_META`

지금 그대로 통째 push 금지 이유:

- 루트 docs, `wp_blog`, repo_blueprints, tesla 등 unrelated 변경이 매우 많다
- 메타 repo를 지금 그대로 올리면 정리 목적과 무관한 변경까지 같이 올라간다

## 4. Git에 올리면 안 되는 것

- `runtime/**`
- `cleanup_legacy_projects/**`
- `quarantine/**`
- `__pycache__/**`
- `.venv_live/**`
- 로그 파일 전체
- 상태 JSON 전체
- 토큰/시크릿
  - `bot_token.txt`
  - `allowed_chat_ids.txt`
  - `office_allowed_hosts.txt`
  - `anthropic_api_key.txt`
  - `.env`

## 5. 집에서 새 로컬 받을 때 기준

집에서는 아래만 최신 push 후 fresh clone/pull 받는 것이 맞다.

- `02_jogyeon`
- `admin`
- `03_telegram_py`
- `ivwith`의 선별 commit
- `projects/blog`의 선별 commit

반대로 아래는 지금 fresh clone 기준으로 삼지 않는다.

- `1POW` 루트 repo 전체
- `1POW_META` 전체

## 6. 추천 push 순서

1. `02_jogyeon`
2. `admin`
3. `03_telegram_py`
4. `ivwith` 선별 commit
5. `projects/blog` 선별 commit
6. `1POW` 루트 repo는 별도 정리 후 마지막
7. `1POW_META`는 더 강한 분리 정리 후 마지막

## 한 줄 판단

지금은 `정리된 프로젝트 repo만 선별 push`하고, 집에서는 그 repo들만 새로 받는 방식이 맞다.  
`C:\1POW`와 `C:\1POW_META`를 통째로 최신화 기준으로 쓰는 건 아직 이르다.
