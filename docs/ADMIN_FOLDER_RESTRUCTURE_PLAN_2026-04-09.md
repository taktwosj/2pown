# admin 폴더 정리 세부계획

작성일: 2026-04-09

업데이트: 2026-04-10 기준 top-level `C:\1POW\ivwith-admin-new`는 `C:\1POW\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy`로 archived 됐다. 아래 내용은 archive 전 점검 스냅샷을 포함한다.

참고: 이 문서는 `2POW` cutover 이전 admin 재구성 계획의 historical snapshot이다. 본문의 `C:\1POW\...` 경로는 당시 기준을 그대로 둔 것이며, 현재 authority는 `C:\2POW`와 `meta/project_registry.json`을 따른다.

## 1. 목적

- `C:\1POW\admin`을 운영 가능한 구조로 다시 정리한다.
- `C:\1POW\admin`, `C:\1POW\projects\admin`, `C:\1POW\ivwith-admin-new`, `C:\1POW\02_jogyeon` 사이의 경계와 정본 경로를 분명히 한다.
- 실행 코드, 운영 스크립트, 데이터, 산출물, 백업본을 분리해서 이후 수정 위험을 낮춘다.

## 2. 이번 점검에서 확인한 사실

### 2-1. `admin` 경로가 여러 군데 존재한다

- `C:\1POW\admin`
- `C:\1POW\03_telegram_py\admin`
- `C:\1POW\ivwith\admin`
- `C:\1POW\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy\legacy-php\admin` (archived snapshot)
- `C:\1POW\projects\admin`

이번 정리의 직접 대상은 `C:\1POW\admin`이다.

### 2-2. 현재 `C:\1POW\admin` 루트에는 성격이 다른 자산이 섞여 있다

상위 구조:

- `.git`
- `123/`
- `bankly/`
- `data/`
- `tools/`
- `_admin_new_work/`
- `__pycache__/`
- 다수의 `*.html`, `*.xlsx`, `*.bat`, `*.ps1`, `*.py`, `*.docx`

점검 시점의 루트 파일 분포:

- `8`개 `*.bat`
- `5`개 `*.html`
- `4`개 `*.xlsx`
- `3`개 `*.ps1`
- `2`개 `*.py`
- `2`개 `*.md`

즉, 현재 `admin`은 하나의 앱 소스 폴더가 아니라 아래 항목이 혼재된 작업장이다.

- CRM 화면 버전 파일
- 은행/금리 관련 정적 산출물
- 원격 브리지와 운영 배치
- JSON 데이터와 백업
- 새 관리자 작업본
- 복사본과 레거시 버전

### 2-3. 경로 authority가 이미 흔들려 있다

- `C:\1POW\admin\bankly\HANDOVER.md`에는 BANKLY canonical local worktree가 `C:\1POW\projects\admin\bankly`라고 기록돼 있다.
- 반면 실제 `C:\1POW\admin` 루트에도 `금융조견.html`, `bankly_geumyeok_snapshot.js`, `crm-v9-site.html` 같은 BANKLY 성격 파일이 남아 있다.
- `C:\1POW\admin\_admin_new_work`는 내용상 `ivwith-admin-new` 또는 `9-admin-new` 쪽 임시 작업본에 가깝다.

즉, 현재 루트 `admin` 안에는 적어도 3개의 경계가 겹쳐 있다.

- 루트 CRM/원격운영
- BANKLY
- new admin/customer flow 작업본

### 2-4. 운영 참조가 이미 존재한다

점검 중 바로 확인된 운영 참조:

- `C:\1POW\admin\REMOTE_SETUP.md`
  - 데이터 파일: `admin/data/crm-data.json`
  - 백업 디렉터리: `admin/data/backups`
- `C:\2POW\docs\2pow-project-map.md`
  - `admin/`과 `02_jogyeon/`의 기준본/레거시 구분 필요
- `C:\2POW\docs\SYSTEM_MAP.md`
  - BANKLY를 금리/수당/은행조건 정본으로 취급

따라서 이번 정리는 "폴더 예쁘게 만들기"가 아니라 path authority 복구 작업으로 다뤄야 한다.

## 3. 핵심 문제 정의

### 문제 1. 프로젝트 경계가 섞여 있다

- 루트 `admin` 안에 CRM 운영물, BANKLY 산출물, new admin 실험본이 공존한다.

### 문제 2. 정본 경로가 충돌한다

- BANKLY는 handover상 `projects/admin/bankly`가 정본처럼 적혀 있지만, 루트 `admin`에도 동일 성격 파일이 남아 있다.

### 문제 3. 실행 자산과 산출물이 분리되지 않았다

- 실행 스크립트와 결과 HTML/XLSX가 같은 레벨에 놓여 있어 수정 대상과 배포 대상이 혼동된다.

### 문제 4. 백업/복사본이 런타임 루트에 남아 있다

- `123/`
- `crm-v8-site.backup-2026-03-03.html`
- `portal_index_backup.html`
- 복수의 샘플/참고 XLSX/DOCX

### 문제 5. 문서와 실제 경로가 완전히 일치하지 않는다

- 문서상 권한 경로와 실제 수정 위치가 다르면 이후 변경이 다른 복사본에 반영되는 문제가 반복된다.

## 4. 정리 원칙

- 정본 경로를 먼저 확정하고 파일 이동은 그 다음에 한다.
- 한 번에 대량 이동하지 않는다.
- 원본 데이터와 산출물을 같은 단계에서 같이 건드리지 않는다.
- `xlsx`, `csv`, `docx` 같은 업무 자산은 삭제보다 보존/격리 우선으로 처리한다.
- 복사본/백업본은 바로 삭제하지 않고 `archive/`로 격리한다.
- 문서 반영은 authority 문서만 업데이트한다.
- 배치/스크립트 참조 경로를 확인하기 전에는 폴더명 변경이나 대규모 이동을 하지 않는다.

## 5. 권장 목표 구조

### 5-1. 루트 `C:\1POW\admin`의 목표 역할

루트 `admin`은 "현재 사무실에서 직접 쓰는 CRM 운영 루트"만 남기고, 다른 프로젝트 성격 폴더는 분리한다.

권장 구조:

```text
C:\1POW\admin\
  crm\
  ops\
  data\
    backups\
  tools\
  archive\
  docs\
```

### 5-2. 경계별 권장 정본

- CRM 운영 화면/브리지: `C:\1POW\admin\crm\`
- CRM 운영 스크립트/배치: `C:\1POW\admin\ops\`
- CRM 데이터/백업: `C:\1POW\admin\data\`
- BANKLY 정본: `C:\1POW\projects\admin\bankly\`
- new admin/customer flow 작업본: `C:\1POW\ivwith-admin-new\`
- 복사본/백업/참고본: `C:\1POW\admin\archive\`

### 5-3. 파일군별 권장 소속

루트 `admin`에 남길 후보:

- `crm_bridge.py`
- `REMOTE_SETUP.md`
- `REMOTE_QUICK_START.md`
- `CHECK_CRM_REMOTE_HEALTH.bat`
- `ENABLE_CRM_REMOTE_ACCESS.ps1`
- `INSTALL_CRM_BRIDGE_REMOTE_TASK.ps1`
- `START_CRM_BRIDGE*.bat`
- `RUN_CRM_REMOTE_ONCE.bat`
- `data/**`
- `tools/**`

루트 `admin`에서 분리 검토 대상:

- `bankly/`
- `금융조견.html`
- `금융조견.xlsx`
- `금융조견_매트릭스.csv`
- `bankly_geumyeok_snapshot.js`
- `crm-v9-site.html`
- `_admin_new_work/**`

즉시 `archive` 격리 대상 후보:

- `123/`
- `crm-v8-site.backup-2026-03-03.html`
- `portal_index_backup.html`
- `crm-v8-site.html`
- `crm-v7-table.jsx`
- 샘플/참고용 `xlsx`, `docx`

주의:

- `crm-v9-site.html`은 BANKLY와 CRM 사이 경계가 얽혀 있을 수 있으므로 바로 이동하지 않고 참조점 조사 후 결정한다.

## 6. 단계별 실행 계획

### Phase 0. Authority Freeze

목표:

- 경로 authority를 먼저 잠근다.

작업:

- BANKLY 정본을 `C:\1POW\projects\admin\bankly`로 확정할지 재확인
- `_admin_new_work`의 소유 프로젝트를 `ivwith-admin-new`로 확정
- 루트 `admin`은 CRM 운영 루트라는 역할만 남기도록 범위 선언

산출물:

- authority 표 1장
- 이동 대상 목록 초안

### Phase 1. Inventory and Protection

목표:

- 무엇을 옮길지, 남길지, 보관할지 먼저 고정한다.

작업:

- `C:\1POW\admin` 전체 파일 inventory 작성
- 각 파일에 `keep / move / archive / review` 태그 부여
- 루트 `admin` 내 백업본과 샘플 자산 분리 목록 작성
- 참조점이 불분명한 파일은 `review`로 남겨 즉시 이동하지 않음

핵심 확인 대상:

- `crm-v9-site.html`
- `금융조견.html`
- `bankly_geumyeok_snapshot.js`
- `_admin_new_work/app.py`
- `crm_bridge.py`

### Phase 2. BANKLY Split

목표:

- BANKLY 경계를 루트 `admin`에서 떼어낸다.

작업:

- `C:\1POW\admin\bankly`와 `C:\1POW\projects\admin\bankly`의 차이를 비교
- 어느 경로가 실제 수정본인지 최종 확정
- 루트 `admin`의 BANKLY 성격 파일을 정본 또는 배포 복사본으로 재분류
- 루트 `admin`에는 BANKLY 소스 대신 필요한 배포 산출물만 남기거나, 아예 참조 경로를 바꿔 제거

완료 기준:

- BANKLY 관련 HTML/JS/source JSON의 정본 경로가 1곳만 남음
- handover 문서와 실제 수정 경로가 일치함

### Phase 3. New Admin Workbench Split

목표:

- `_admin_new_work`를 루트 `admin`에서 분리한다.

작업:

- `_admin_new_work/**`를 `ivwith-admin-new` 또는 `9-admin-new` 소유 경로로 이동하는 계획 수립
- `customer_flow_assets`, `templates`, `app.py`의 실행 경로와 참조 경로 확인
- root `admin`와 직접 연결되지 않는다면 루트에서 제거

완료 기준:

- customer flow workbench가 루트 `admin` 밖의 자기 프로젝트 경계로 이동
- 관련 문서가 `9-admin-new` 쪽으로 정렬됨

### Phase 4. CRM Runtime Normalization

목표:

- 루트 `admin`을 실제 CRM 운영 구조로 정리한다.

작업:

- CRM 화면 파일을 `crm/`로 이동
- 원격 실행/설치/점검 배치를 `ops/`로 이동
- `crm-data.json`, `backups/`만 `data/` 밑으로 통일
- 루트 최상단에는 꼭 필요한 진입 파일만 남김

검토 포인트:

- `crm_bridge.py`
- `OFFICE_*`
- `HOME_*`
- `START_CRM_BRIDGE*`
- `RUN_CRM_REMOTE_ONCE.bat`

### Phase 5. Archive Cleanup

목표:

- 런타임 루트에서 백업/참고본을 제거한다.

작업:

- `123/` 이동
- `*.backup-*.html` 이동
- 사용하지 않는 샘플 `xlsx`, `docx`를 `archive/`로 격리
- 파일명만 보고 삭제하지 말고 참조 grep 후 처리

완료 기준:

- 루트 `admin` 최상단에 레거시 복사본이 남지 않음

### Phase 6. Verification and Documentation

목표:

- 이동 후 경로 파손이 없는지 확인한다.

작업:

- `admin` 참조 grep 재실행
- Python 스크립트 `py_compile`
- 배치/PowerShell 실행 경로 확인
- 필요한 HTML 열람/브리지 health 점검
- authority 문서 업데이트

업데이트 대상 문서:

- `C:\2POW\docs\2pow-project-map.md`
- `C:\2POW\docs\SYSTEM_MAP.md`
- `C:\1POW\admin\bankly\HANDOVER.md` 또는 최종 BANKLY handover 위치
- `C:\1POW\docs\projects\9-admin-new\HANDOVER.md`
- 필요 시 `C:\1POW\meta\project_registry.json`

## 7. 참조 경로 점검 체크리스트

정리 전에 반드시 grep/수동 확인할 대상:

- `C:\1POW\bot.py`
- `C:\1POW\03_telegram_py\bot.py`
- `C:\1POW\sync_kiwoom_public_promo.py`
- `C:\1POW\admin\REMOTE_SETUP.md`
- `C:\1POW\admin\*.bat`
- `C:\1POW\admin\*.ps1`
- `C:\1POW\admin\bankly\HANDOVER.md`
- `C:\2POW\docs\2pow-project-map.md`
- `C:\2POW\docs\SYSTEM_MAP.md`

확인할 항목:

- 하드코딩 경로 존재 여부
- 상대경로 의존 여부
- 생성물 overwrite 대상 경로
- 배포용/정본용 경로가 혼동되는지 여부

## 8. 이번 작업에서 바로 하지 않을 것

- 업무 원본 `xlsx/csv/docx` 삭제
- BANKLY와 CRM 경계를 확인하지 않은 상태에서 `crm-v9-site.html` 즉시 이동
- `_admin_new_work`를 문서 확인 없이 임의 프로젝트로 이동
- `admin` 전체를 한 번에 `projects/admin`으로 통합
- `.git` 루트 재편이나 history 정리

## 9. 주요 리스크

- 배치/PowerShell이 절대경로를 직접 참조할 수 있다.
- 루트 `admin`의 `.git` 경계 때문에 부분 이동 후 `git status`가 더 혼란스러워질 수 있다.
- BANKLY 관련 파일이 루트 `admin`과 `projects/admin/bankly`에 동시에 존재할 가능성이 높다.
- `_admin_new_work`는 이름상 임시 폴더지만 실제 운영 참조가 숨어 있을 수 있다.
- 문서만 고치고 실제 경로를 안 바꾸면 authority drift가 더 심해진다.

## 10. 완료 기준

- 루트 `admin`의 역할이 "CRM 운영 루트"로 명확해진다.
- BANKLY 정본 경로가 1곳만 남는다.
- new admin/customer flow 작업본이 자기 프로젝트 경계로 빠진다.
- 루트 `admin` 최상단에서 백업/복사본/샘플 자산이 제거된다.
- 참조 grep 결과가 새 구조와 일치한다.
- authority 문서와 실제 경로가 같은 말을 한다.

## 11. 권장 실행 순서 요약

1. authority 확정
2. inventory 작성
3. BANKLY 분리
4. `_admin_new_work` 분리
5. CRM/ops/data 재배치
6. archive 격리
7. 검증
8. authority 문서 갱신

## 12. 한 줄 결론

이번 `admin` 정리는 "폴더 정리"가 아니라, 루트 `admin`에서 BANKLY와 new admin 작업본을 떼어내고 CRM 운영 경계만 남기는 authority 복구 작업으로 수행해야 한다.
