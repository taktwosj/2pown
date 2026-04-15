# 1POW Workspace Audit

작성일: 2026-04-09  
대상 경로: `C:\1POW`  
목적: 현재 `1POW` 전체 폴더를 전수 스캔해, 실제로 쓰는 영역과 정리 후보를 분리하고 정리 우선순위를 제안한다.

업데이트: 2026-04-10 기준 top-level `ivwith-admin-new`는 `C:\1POW\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy`로 archived 됐다. 아래 용량/경로 표는 archive 전 스냅샷을 포함한다.

## 1. 결론 요약

현재 `C:\1POW`는 "한 프로젝트의 작업 폴더"가 아니라 아래가 한곳에 겹쳐 있는 상태다.

- 실제 운영 중인 Git 저장소
- 심볼릭 링크 기반 경로 별칭
- 배포/런타임 복사본
- 대용량 산출물과 원본 데이터
- 임시 캐시, 백업, 과거 실험본
- Codex/Claude 작업용 임시 worktree

핵심 진단은 다음 5가지다.

1. `projects/`는 대부분 실제 저장 공간이 아니라 심볼릭 링크다. 용량이 커 보여도 상당수는 중복 저장이 아니라 "같은 경로를 다른 이름으로 본 것"이다.
2. `admin/_admin_new_work`와 `ivwith` 사이에 대형 동일 자산이 중복 보관돼 있다. 이 구간이 가장 먼저 정리해야 할 실중복 영역이다.
3. `03_telegram_py` 안에는 다시 `03_telegram_py`, `01_lhshapt`, `admin`, `02_jogyeon`가 들어 있다. 이건 저장소라기보다 배포/미러/작업 복사본 구조에 가깝다.
4. `myhome`에는 대용량 원본 CSV/ZIP과 `tmp_*` 캐시가 같이 섞여 있다. 정리 가능 항목과 보존해야 할 원본 데이터가 혼재돼 있다.
5. `.claude/worktrees`, `__pycache__`, `tmp_*`, `.bak`, `runtime` 백업류, `quarantine`, 이상한 루트 잔재 폴더는 정리 후보가 명확하다.

## 2. 정본 기준과 활성 영역

`meta/project_registry.json` 기준으로 현재 정본 판단에 참고할 수 있는 활성 영역은 아래와 같다.

| 영역 | 현재 기준 경로 | 비고 |
|---|---|---|
| LHSHAPT | `myhome` | runtime은 Cafe24, Git canonical은 아직 미확정 |
| BANKLY | `02_jogyeon/bankly` | canonical local worktree가 이쪽으로 적혀 있음 |
| 텔레그램 운영 | `03_telegram_py` | GitHub 연결 있음, office PC runtime + Cafe24 deploy copy |
| ivwith 구 admin/고객관리 | `ivwith` | `docs/projects/9-admin-new/`와 강하게 연결 |
| 새 admin 계획 영역 | `ivwith-admin-new` | 문서 정본은 `docs/projects/9-admin-new/` |
| 외부 공고문 게시 | 별도 외부 repo | 현재 canonical repo는 `C:\ONEtaktwosj\OneDrive\22blog` |

반대로, 아래는 "보이는 위치는 크지만 정본처럼 취급하면 안 되는" 영역이다.

- `projects/02_jogyeon`
- `projects/03_telegram_py`
- `projects/admin`
- `projects/ivwith`
- `projects/ivwith-admin-new`
- `projects/myhome`
- `projects/고객관리`

이 7개는 모두 심볼릭 링크다. 즉 `projects/` 아래의 이 항목들은 별도 복사본이 아니라 원본 폴더를 가리키는 경로 별칭이다.

## 3. 최상위 용량 현황

상위 폴더 중 용량이 큰 항목은 다음과 같다.

| 경로 | 파일 수 | 크기 |
|---|---:|---:|
| `projects` | 77,544 | 2863.58 MB |
| `ivwith` | 2,350 | 2541.99 MB |
| `myhome` | 433 | 1258.32 MB |
| `admin` | 214 | 888.64 MB |
| `.claude` | 1,335 | 777.59 MB |
| `ivwith-admin-new` | 630 | 195.22 MB |
| `03_telegram_py` | 456 | 158.04 MB |

주의할 점:

- `projects`는 실사용 저장량처럼 보이지만 대부분 심볼릭 링크를 포함한 수치다.
- 실제로 큰 정리 포인트는 `ivwith`, `myhome`, `admin`, `.claude`, `03_telegram_py`다.

## 4. 가장 큰 파일

용량 상위 파일은 대부분 데이터베이스, 대형 산출물, 원본 데이터다.

| 파일 | 크기 | 판단 |
|---|---:|---|
| `admin/_admin_new_work/customer_flow_data/customer_portal.sqlite` | 553.88 MB | `ivwith/customer_portal.sqlite`와 실중복 가능성 매우 높음 |
| `ivwith/customer_portal.sqlite` | 553.88 MB | 운영/정본 후보 |
| `myhome/한국토지주택공사 주택 평면도 현황_20210826.zip` | 340.20 MB | 원본 데이터 가능성 높음, 확인 전 삭제 금지 |
| `ivwith/2026-03-06.dump` | 258.07 MB | DB dump 백업류 |
| `ivwith/백업.zip` | 165.83 MB | 백업 파일 |
| `myhome/hwspr_020304_merged_view_with_private_full_enriched_dates.csv` | 157.14 MB | 대형 산출물/원본 중간결과 |
| `myhome/hwspr_020304_merged_view_with_private_full.csv` | 156.82 MB | 대형 산출물/원본 중간결과 |
| `admin/_admin_new_work/customer_flow_assets/customer_flow_dashboard_data.js` | 148.42 MB | `ivwith` 동일 자산과 중복 가능성 매우 높음 |
| `ivwith/customer_flow_dashboard_data.js` | 148.42 MB | 운영/정본 후보 |
| `myhome/국토교통부_등록민간임대주택 데이터_20250930.csv` | 139.13 MB | 원본 데이터 가능성 높음 |
| `ivwith/고객정보db_정리용.csv` | 134.15 MB | 활성 데이터, 최근 수정됨 |
| `ivwith/new_admin/customer_portal_data.js` | 132.32 MB | 새 admin 데이터 산출물 |
| `myhome/tmp_nationwide_cache.json` | 105.72 MB | 임시 캐시 성격 강함 |

## 5. 구조상 큰 문제 구간

### 5.1 `admin`은 거의 전부 `_admin_new_work`가 차지

`admin` 내부 용량 분해:

| 하위 경로 | 파일 수 | 크기 |
|---|---:|---:|
| `_admin_new_work` | 27 | 858.34 MB |
| `.git` | 130 | 26.45 MB |
| `data` | 26 | 2.19 MB |
| `123` | 2 | 0.43 MB |

해석:

- 현재 `admin`의 실제 문제는 거의 `_admin_new_work` 하나다.
- `123`, `crm-v8-site.backup-2026-03-03.html`, `portal_index_backup.html` 같은 항목은 정리 후보 성격이 강하다.
- 별도 문서로 만든 `ADMIN_FOLDER_RESTRUCTURE_PLAN_2026-04-09.md`와 연결해 단계 정리가 가능하다.

### 5.2 `admin/_admin_new_work`와 `ivwith`의 중복

파일명과 크기 비교 결과, 아래 자산은 동일 복사본일 가능성이 매우 높다.

- `customer_portal.sqlite` 553.88 MB
- `customer_flow_dashboard_data.js` 148.42 MB
- `customer_flow_dashboard.html`
- `customer_flow_strategy_report_data.js`
- 다수의 `고객흐름_*.xlsx`

판단:

- 이건 "유사본"이 아니라 사실상 같은 산출물을 다른 폴더에 이중 저장한 패턴으로 보인다.
- `admin/_admin_new_work`를 실운영 정본으로 계속 둘 이유가 약하다.
- 정리 1순위는 `ivwith` 또는 `ivwith-admin-new` 쪽 정본을 확정한 뒤 `admin/_admin_new_work`를 archive 또는 제거 후보로 돌리는 것이다.

### 5.3 `03_telegram_py`는 배포/미러 복사 구조가 섞여 있음

`03_telegram_py` 내부 용량 분해:

| 하위 경로 | 파일 수 | 크기 |
|---|---:|---:|
| `03_telegram_py` | 50 | 75.18 MB |
| `01_lhshapt` | 25 | 28.69 MB |
| `admin` | 50 | 3.73 MB |
| `office_deploy` | 11 | 0.86 MB |
| `02_jogyeon` | 7 | 0.14 MB |

판단:

- 저장소 안에 다시 프로젝트 이름 폴더가 들어 있는 구조라, 배포 복사본/실행 복사본 가능성이 높다.
- `03_telegram_py`는 정본 repo로 유지하되, 내부의 nested copy는 장기적으로 분리해야 한다.
- 특히 `01_lhshapt`, `admin`, `02_jogyeon`가 텔레그램 실행에 필요한 최소 파일인지 확인이 필요하다.

### 5.5 `myhome`은 원본 데이터와 임시 캐시가 혼재

`myhome` 내부 폴더 용량:

| 하위 경로 | 파일 수 | 크기 |
|---|---:|---:|
| `tmp_manual_pdfs` | 8 | 52.69 MB |
| `.venv_manual` | 4 | 22.95 MB |
| `.git` | 199 | 8.93 MB |
| `reports` | 11 | 8.16 MB |

추가 특징:

- 루트에 `tmp_nationwide_cache.json` 105.72 MB
- `tmp_gyeonggi_cache.json`, `tmp_sh_houseinfo_cache.json`, 다수 `tmp_*.py`, `tmp_*.sh`, `tmp_js_check.js`
- 동시에 대형 CSV/ZIP 원본도 존재

판단:

- `tmp_*`는 정리 후보가 많다.
- 반면 대형 CSV/ZIP는 데이터 원본일 수 있으므로, cache와 source를 구분하지 않으면 사고 난다.

### 5.6 `.claude/worktrees`는 거의 전부 임시 작업 흔적

`.claude/worktrees` 내부:

| worktree | 파일 수 | 크기 |
|---|---:|---:|
| `charming-edison` | 328 | 156.94 MB |
| `serene-gates` | 255 | 155.21 MB |
| `silly-haslett` | 248 | 155.14 MB |
| `cranky-golick` | 248 | 155.14 MB |
| `pedantic-khayyam` | 248 | 155.14 MB |

판단:

- Codex/Claude 세션용 임시 worktree 잔재로 보인다.
- 현재 열려 있는 세션/에이전트가 없다는 전제에서 가장 안전하게 용량을 줄일 수 있는 영역 중 하나다.

## 6. 정리 후보 분류

### A. 우선 정리 후보

사람 확인은 필요하지만, 일반적으로 정리해도 될 가능성이 높은 항목이다.

- `.claude/worktrees/*`
- 전역 `__pycache__` 폴더 44개
- `myhome/tmp_*`
- `myhome/.venv_manual`
- `runtime/cache`
- `runtime/root_archive`
- `runtime/verify/root_dirty_backup_20260404`
- `docs/archive`
- `quarantine` 내부 오래된 격리 파일
- `admin/123`
- `*.bak` 12개
- `*.backup*` 2개
- `*backup*` 이름 파일 17개
- `*_old*` 이름 파일 7개

### B. 실중복 가능성 매우 높음

정본만 확정하면 빠르게 줄일 수 있다.

- `admin/_admin_new_work/customer_flow_data/customer_portal.sqlite`
- `ivwith/customer_portal.sqlite`
- `admin/_admin_new_work/customer_flow_assets/customer_flow_dashboard_data.js`
- `ivwith/customer_flow_dashboard_data.js`
- `admin/_admin_new_work` 내부 고객흐름 산출물 전반

### C. 확인 전 삭제 금지

오래됐거나 크더라도 업무 원본/정본일 수 있다.

- `myhome/*.csv`, `myhome/*.zip` 대형 원본 데이터
- `ivwith/고객정보db_정리용.csv`
- `ivwith/new_admin/*`
- `03_telegram_py` 내부 nested 프로젝트 폴더
- `고객관리/통합관리.xlsm` 계열 자산

### D. 이상 징후로 별도 처리 필요

- `C:\1POW\C1POW`
- `C:\1POW\C1POWruntime`
- `C:\1POW\OneDrive` 파일
- `\\?\C:\1POW\nul`

판단:

- 이건 일반 프로젝트 산출물보다 경로 깨짐, 복사 중 오류, 잘못된 동기화의 부산물일 가능성이 높다.
- 삭제 전 정체 파악은 필요하지만, 장기 보존할 이유는 거의 없어 보인다.

## 7. 사용 흔적 관점 요약

스캔 기준:

- 최근 7일 이내 수정 파일: 2,122개
- 7일 초과 파일: 82,671개

해석:

- 현재 작업공간 대부분은 "지금 활발히 수정 중인 코드"가 아니라 누적 보관물이다.
- 하지만 "오래됨 = 삭제 가능"은 아니다.
- 특히 `myhome`, `ivwith`, `고객관리`는 오래돼도 업무 정본일 수 있다.

## 8. 권장 정리 순서

### 1단계. 안전한 잡파일/임시물 정리

- `.claude/worktrees`
- `__pycache__`
- `tmp_*`
- `node_modules` 재설치 가능한 경로
- `runtime` 내부 캐시/검증 백업
- `quarantine` 오래된 파일

예상 효과:

- 비교적 낮은 위험으로 수백 MB에서 1GB 이상 축소 가능

### 2단계. `admin`과 `ivwith` 정본 확정

- `admin/_admin_new_work`를 계속 유지할지 결정
- `ivwith`와 중복 자산 비교표를 만든 뒤 정본 외 복사본을 `archive`로 이동
- `admin`은 UI/bridge/ops만 남기고 대형 산출물은 분리

예상 효과:

- 가장 큰 실중복 제거 가능

### 3단계. `03_telegram_py` 내부 복사 구조 정리

- nested `03_telegram_py`, `01_lhshapt`, `admin`, `02_jogyeon`가 실행 필수인지 확인
- 실행 필수본만 남기고 나머지는 참조용/배포용으로 재배치

### 5단계. `myhome` 데이터 레이어 정리

- `source/`, `outputs/`, `cache/`, `tmp/` 구분
- 대형 CSV/ZIP는 원본/중간산출물/캐시로 분류
- `tmp_*`는 삭제 또는 `tmp/`로 이동

## 9. 바로 실행해도 되는 다음 작업

1. `.claude/worktrees`와 `__pycache__`부터 정리
2. `admin/_admin_new_work` vs `ivwith` 중복 비교표 고정
3. `03_telegram_py` 내부 nested copy의 실행 의존성 확인
4. `myhome`의 `tmp_*`와 원본 데이터를 분리

## 10. 최종 판단

지금 `C:\1POW`에서 "안 쓰는 것 같아 보이는 것"은 실제로 많다. 다만 성격이 세 가지로 섞여 있다.

- 진짜 안 쓰는 임시물
- 정본은 아닌 복사본/미러
- 오래됐지만 지우면 안 되는 업무 원본

가장 먼저 칼을 대야 하는 곳은 `admin/_admin_new_work`, `.claude/worktrees`, `myhome/tmp_*`, `03_telegram_py` 내부 중첩 복사 구조다.  
반대로 `myhome` 대형 원본 CSV/ZIP, `ivwith` 고객 데이터, `고객관리` 자산은 확인 없이 건드리면 안 된다.
