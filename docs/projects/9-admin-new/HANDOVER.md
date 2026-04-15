# Admin 고도화 인수인계서

> 이 문서는 Admin 고도화 프로젝트의 유일한 인수인계 기준 문서다.
> ivwith 레거시 CRM 운영 + Flask 이식 + 동기화 파이프라인을 모두 포함한다.
> 오래된 작업은 Git history로 확인한다.
> 작업 마무리 시 이 문서의 "최근 작업"을 최근 7일만 남기고 갱신한다.

## 1. 프로젝트 목적

ivwith.co.kr 레거시 PHP CRM을 Python Flask로 전체 이식하고, 운영 전환한다.
전환 전까지는 레거시 CRM 운영과 daily_sync 파이프라인을 이 프로젝트에서 관리한다.

## FTP 절대규칙

> 1. ivwith.co.kr FTP 수정/삭제/편집/업로드 절대 금지
> 2. 사용자 요청 시에만 읽기(다운로드) 전용으로 접속
> 3. FTP 접속정보를 어떤 파일에도 기록하지 마라

## 2. 기준 경로

| 역할 | 경로 |
|------|------|
| **레거시 운영 사이트** | `https://ivwith.co.kr` (외부 호스팅, FTP READ-ONLY) |
| 관리자 로그인 | `https://ivwith.co.kr/admin/login.php` |
| 고객관리 | `https://ivwith.co.kr/admin/imapt_list.php?toggle=4` |
| **Flask 고도화 서버** | `/srv/workspace/ivwith/admin_new/` (systemd: ivwith-admin-new) |
| Flask 고도화 URL | `https://jsjtaktwo.mycafe24.com/admin-new/` |
| 고객흐름 대시보드 | `http://jsjtaktwo.mycafe24.com/ivwith/customer_flow_dashboard.html` |
| 레거시 로컬 작업본 | `C:\2POW\ivwith` |
| 로컬 admin-new runtime 자산 | `C:\2POW\ivwith\admin_new_runtime` |
| 고도화 로컬 진입점 | `C:\2POW\ivwith\admin_new_runtime\` |
| legacy PHP snapshot | `C:\RETIRED_1POW_2026-04-10\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy\legacy-php\` (archived mirror only) |
| 서버 사본 | `/srv/workspace/ivwith/` (Cafe24, 분석/동기화용) |

## 3. 정본 / 로컬 / 런타임 구분

| 구분 | 위치 | 역할 |
|------|------|------|
| 정본 (Git) | 로컬 Git repo (`ivwith/`) | 코드/문서 원본. Flask admin entrypoint는 `ivwith/admin_new_runtime/`를 기준으로 본다. Git canonical remote 미정. OneDrive는 백업만. |
| 로컬 (레거시) | `C:\2POW\ivwith` | 분석, 동기화 스크립트, 대시보드 |
| 로컬 (고도화 진입점) | `C:\2POW\ivwith\admin_new_runtime` | Flask runtime / 현재 local canonical entrypoint |
| 로컬 (legacy snapshot) | `C:\RETIRED_1POW_2026-04-10\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy\legacy-php` | archived PHP snapshot mirror only |
| 레거시 운영 | `ivwith.co.kr` | 외부 호스팅 (FTP READ-ONLY) |
| 고도화 런타임 | Cafe24 `/srv/workspace/ivwith/admin_new/` | Flask 서버 |
| 서버 사본 | Cafe24 `/srv/workspace/ivwith/` | DB 동기화, CSV 업로드 |

## 4. 구성 요소

### 4-A. 레거시 CRM (ivwith.co.kr)

보증금 담보대출 접수/심사/가승인/기표/자서/상환/수수료/문자/본인인증 관리.
PHP 5.x + MySQL, `premloan` 테이블 중심.

- `admin/imapt_list.php` — 메인 리스트
- `admin/imapt_insert.php` — 입력/수정
- 서버 직접 수정 불가 (외부 호스팅)
- DB 직접 접속 불가 (CSV 동기화만)

### 4-B. daily_sync 파이프라인 (사무실 PC 전용)

텔레그램 봇에서 자동 실행. 사무실 PC에서만 동작. 평일 오전 자동 (토/일 제외).

**전체 데이터 흐름:**

```
① ivwith.co.kr phpMyAdmin (DB 웹관리, FTP 아님)
   │
   │ ivwith_report.sync_from_phpmyadmin()
   │ (HTTP로 DB 데이터 다운로드)
   ↓
② 사무실 PC: C:\2POW\ivwith\고객정보db_정리용.csv
   │
   │ step2: 영업자 "정상준" 필터 + 상태 판정
   │ (기표완료/가승인/부결 등 CRM 상태 분류)
   ↓
③ 사무실 PC: C:\2POW\고객관리\통합관리.xlsm (h시트)
   │ step3: 엑셀에 변경분 반영 (Excel COM)
   │
   │ step4: CSV를 SCP로 업로드
   ↓
④ Cafe24: /srv/workspace/ivwith/고객정보db_정리용.csv
   │
   │ csv_to_db_sync.py --days 60 (서버에서 실행)
   ↓
⑤ Cafe24: ivwith DB (premloan 테이블) 증분 동기화
   │
   │ step5: 엑셀+CSV+로그를 SCP로 백업
   ↓
⑥ Cafe24: /srv/workspace/고객관리/통합관리.xlsm (백업)
   │
   ↓
⑦ 텔레그램 보고 (각 단계마다 성공/실패 보고)
```

**핵심 파일:**
- `daily_sync.py` — 파이프라인 메인 (포트 락 46360, scp 3회 재시도)
- `csv_to_db_sync.py` — CSV → DB 증분 동기화 (서버 측)
- `export_mysql_dump_table_to_csv.py` — MySQL 덤프 → CSV
- `ivwith_report.py` — phpMyAdmin 덤프 다운로드

**실제 자동배치 진입점:**
- `C:\2POW\bot.py` 의 `_ivwith_daily_sync_loop()`
- 이 루프가 정본 `C:\2POW\ivwith\daily_sync.py` 를 직접 import/reload 해서 실행한다.
- `runtime/server_daily_sync_*.py` 같은 런타임 사본은 참고용일 수 있으나 정본 진입점이 아니다.

**동시실행 방지:** 포트 46360 뮤텍스 락. 실패 시 step별 텔레그램 보고 후 중단/속행 분기.

### 4-C. 분석 도구 (로컬)

- `customer_flow_dashboard.html` / `customer_flow_dashboard_data.js` — 고객 흐름 대시보드
- `customer_portal.sqlite` — 로컬 분석 DB
- `analyze_customer_flows.py` / `build_customer_flow_dashboard.py` — 분석 스크립트
- `2026-03-06.dump` — MySQL 덤프 (209,806건)

### 4-D. Flask 고도화 (admin_new)

레거시 PHP를 Flask로 전체 이식.
핵심 7개 카테고리 PHP 대조 검증 완료 (470/470, 10회반복 100%).
22개 라우트 HTTP 200 확인, 209,564건 실데이터 SQL 대조 일치.

검증 완료 상태. 운영 전환은 사용자 판단 후.

현재 local canonical entrypoint는 `C:\2POW\ivwith\admin_new_runtime\app.py`다.
`C:\RETIRED_1POW_2026-04-10\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy\legacy-php\admin`은 `C:\2POW\ivwith\admin`과 동일한 archived PHP snapshot이다.

**연동 관계**:
- 대출상품/금리/수당/은행조건은 **bankly MCP 서버가 유일한 정본**이다. premloan 금리 관련 작업 시 MCP를 최우선으로 조회하고, MCP 값과 다른 곳의 값이 다르면 MCP가 맞다.
- daily_sync: 고객관리 엑셀(#7) H시트 → CSV → ivwith DB
- 텔레그램 봇(#6)이 daily_sync 트리거 + 결과 보고
- admin접수.py: 과거에는 텔레그램 봇(#6) → legacy crm-v9-site.html(BANKLY #3, 현재 `C:\cleanup_legacy_projects`로 분리) → ivwith DB 흐름을 사용했다.
- 전체 연동 구조: `C:\2POW\docs\SYSTEM_MAP.md` 참조

## 5. 현재 상태

- **레거시**: ivwith.co.kr 운영 중, daily_sync 정상 가동
- **고도화**: 검증 완료, 운영 전환 대기
- **로컬 authority**: Flask admin 진입점은 `C:\2POW\ivwith\admin_new_runtime`, legacy PHP snapshot은 `C:\RETIRED_1POW_2026-04-10\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy\legacy-php`
- daily_sync.py 포트 락/재시도 적용됨
- 텔레그램 보고: 전사 summary + 자체팀(정상준) 고객 상세만 표시

## 6. 현재 리스크

- ivwith.co.kr 외부 호스팅이라 서버 직접 수정 불가
- DB 직접 접속 불가 (CSV 동기화만)
- 간헐적 `Connection closed by 172.233.88.151 port 22` — scp/ssh 3회 재시도로 대응
- premloan 필드별 업무 의미 사전 미완성
- Git canonical remote 미정

## 7. 최근 검증

- Flask 고도화: 7개 카테고리 470/470 대조 통과
- daily_sync.py 포트 락 정상 동작
- 텔레그램 DB 동기화 보고 필터링 정상
- H시트 이름행 스캔을 101행 고정이 아니라 마지막 이름행까지 읽도록 보강
- `C:\2POW\ivwith\admin` 과 archived `C:\RETIRED_1POW_2026-04-10\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy\legacy-php\admin` 이 동일한 630파일 snapshot인지 재검증 완료

## 8. 최근 작업

- `Admin 고도화(#9)` local canonical entrypoint를 `C:\2POW\ivwith\admin_new_runtime`로 formalize
- top-level `C:\RETIRED_1POW_2026-04-10\ivwith-admin-new`를 `C:\RETIRED_1POW_2026-04-10\quarantine\legacy_app_copies\2026-04-10\root_ivwith-admin-new_copy`로 archive
- `daily_sync.py`, `ivwith_report.py`에서 H시트 범위를 마지막 이름행까지 읽도록 수정
- `daily_sync.py`, `ivwith_report.py`, `send_customer_report.py`의 고객상태 규칙을 공통 모듈로 묶고 자동배치 정본 진입점을 문서화
- 고객흐름 admin helper 자산 경로를 `C:\RETIRED_1POW_2026-04-10\admin\_admin_new_work`에서 `C:\2POW\ivwith\admin_new_runtime`로 정리

## 9. 다음 액션

- 운영DB 실시간 연결
- 수수료 자동계산
- SMS 연동
- 운영 전환 판단

## 10. 업데이트 규칙

- 작업 전 이 문서를 먼저 읽는다.
- 작업 후 "최근 작업"에 **변경 / 검증 / 리스크**만 기록한다.
- 최근 7일만 남기고 오래된 항목은 제거한다. 과거 이력은 Git history로 확인한다.
- FTP 관련 판단이 있었으면 이 문서에 기록한다.
- ivwith.co.kr 코드 수정은 불가하다. 로컬 분석과 동기화 스크립트만 수정한다.
