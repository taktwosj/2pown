# 1POW 프로젝트 맵

이 문서는 현재 `1POW` 안에서 실제로 운영하거나 자주 손대는 작업을 도메인 기준으로 정리한 맵이다.

## 한눈에 보는 큰 작업 축
1. 주택 데이터 파이프라인
2. 텔레그램/운영 자동화
3. CRM/대출상담 사이트
4. 고객관리/리포트
5. 금융조견표/레거시 참고
6. 통합관리 엑셀/업무 보조
7. 백업/복구/운영 인프라

## 현재 폴더 기준 매핑

### 1. 주택 데이터 파이프라인
- 핵심 폴더: `myhome/`, `01_lhshapt/`
- 현재 역할:
- `myhome/`는 최신 임대아파트 리스트, ETL 실행기, 영업용 산출물, 뷰어 기준본
- `01_lhshapt/`는 LH/GH/SH 통합 원형 스크립트와 초기 소스 정리
- 대표 파일:
- `myhome/run_daily_pipeline.py`
- `myhome/build_sales_ready_outputs.py`
- `myhome/eeem-clean.html`
- `01_lhshapt/hwspr_merge_020304.py`
- `01_lhshapt/housing_integrate.py`
- 판단:
- 이 둘은 하나의 제품 흐름이다. 장기적으로 같은 Git 저장소로 묶는 것이 맞다.

### 2. 텔레그램/운영 자동화
- 핵심 폴더: `03_telegram_py/`
- 현재 역할:
- 작업 완료 알림, 봇 운영, 스케줄 실행, 복구 런북
- 대표 파일:
- `bot.py`
- `03_telegram_py/codex_work_status.py`
- `03_telegram_py/work_done_notify.py`
- 판단:
- 별도 배포/실행 주기가 있으므로 주택 ETL과 분리된 저장소가 더 낫다.

### 3. CRM/대출상담 사이트
- 핵심 폴더: `admin/`
- 연관 폴더: `02_jogyeon/`
- 현재 역할:
- 대출상담 자동화 UI, CRM 사이트, 원격 브리지, 운영용 배치
- 대표 파일:
- `admin/loan-automation-v6.jsx`
- `admin/crm_bridge.py`
- `02_jogyeon/loan-automation-v6.jsx`
- 판단:
- `02_jogyeon/`은 레거시 참고 성격이 강하므로 `admin/`과 같은 저장소 안의 `legacy/` 또는 `references/` 성격으로 보는 편이 좋다.

### 4. 고객관리/리포트
- 핵심 폴더: `ivwith/`
- 현재 역할:
- 고객 DB, 고객흐름, 집계, 대시보드, CSV/XLSX 결과물
- 대표 파일:
- `ivwith/build_customer_flow_dashboard.py`
- `ivwith/build_customer_portal_data.py`
- `ivwith/build_salesperson_kpi_report.py`
- 판단:
- 데이터와 고객정보 민감도가 높고 주택/텔레그램과 목적이 다르므로 독립 저장소가 맞다.

### 5. 금융조견표/레거시 참고
- 핵심 폴더: `02_jogyeon/`
- 연관 파일: `02_jogyeon/bankly/금융조견.html`, `02_jogyeon/bankly/금융사이트.html`
- 현재 역할:
- 금융조견표, 예시 엑셀, 이전 JSX 참고본
- 판단:
- 단독 저장소로 떼기보다 `CRM/대출상담 사이트` 저장소 안의 하위 영역으로 두는 것이 현실적이다.

### 6. 통합관리 엑셀/업무 보조
- 핵심 폴더: `고객관리/`
- 대표 파일:
- `고객관리/통합관리.xlsm`
- 판단:
- 이 영역은 코드 저장소라기보다 운영 자산에 가깝다.
- Git에는 관련 스크립트, 설명 문서, 필드 매핑만 넣고 실제 대용량 `xlsm` 원본은 별도 보관하는 편이 낫다.

### 7. 백업/복구/운영 인프라
- 핵심 폴더: `_vscode_chat_sync/`
- 연관 위치: OneDrive 복구/세팅 배치, 원격 실행 스크립트 일부
- 판단:
- 개발 저장소보다 운영 인프라 문서/스크립트 영역이다.
- 처음부터 저장소를 따로 만들기보다 마지막 단계에 정리하는 편이 좋다.

## 권장 Git 저장소 분리안

### 추천: 5개 저장소
1. `1pow-housing`
2. `1pow-telegram-ops`
3. `1pow-crm-loan`
4. `1pow-ivwith`
5. `1pow-office-ops`

## 저장소별 권장 범위

### 1. `1pow-housing`
- 포함:
- `myhome/`
- `01_lhshapt/`
- 이유:
- 현재 가장 활발하게 작업 중이고, 코드/문서/결과 검증 흐름이 가장 명확하다.

### 2. `1pow-telegram-ops`
- 포함:
- `03_telegram_py/`
- 이유:
- 배포 단위와 운영 단위가 분리되어 있고, 시크릿 관리도 별도로 필요하다.

### 3. `1pow-crm-loan`
- 포함:
- `admin/`
- `02_jogyeon/`
- 이유:
- 대출상담 사이트, 금융조견표, CRM 브리지, 레거시 참고본이 하나의 업무 흐름으로 이어진다.

### 4. `1pow-ivwith`
- 포함:
- `ivwith/`
- 이유:
- 고객정보 민감도와 데이터 구조가 독립적이다.

### 5. `1pow-office-ops`
- 포함:
- `고객관리/`
- `_vscode_chat_sync/`
- 향후 추가될 사무실 운영 보조 스크립트
- 이유:
- 코드보다 운영 자산 관리 성격이 강하다.
- 단, 이 저장소는 가장 마지막에 시작해도 된다.

## 우선순위

### P1. 바로 Git 시작
- `1pow-housing`
- 이유:
- 지금 실제로 계속 수정 중이다.
- Python/HTML/JS 문서화 흐름이 이미 있다.
- 가장 빨리 Git의 효과를 본다.

### P2. 다음으로 시작
- `1pow-crm-loan`
- 이유:
- 사업적으로 중요하고, 코드 변경 이력 관리가 필요하다.
- `admin/`과 `02_jogyeon/`의 기준본/레거시 구분이 필요하다.

### P3. 그다음
- `1pow-telegram-ops`
- 이유:
- 운영 중요도는 높지만 시크릿, 배포 환경, 스케줄러가 얽혀 있어 `.gitignore`를 먼저 잘 설계해야 한다.

### P4. 이후
- `1pow-ivwith`
- 이유:
- 고객 데이터 민감도가 높고, 결과물 중심 자산이 많아서 포함 범위를 조심스럽게 정해야 한다.

### P5. 마지막
- `1pow-office-ops`
- 이유:
- 엑셀 원본과 동기화 자산은 Git보다 OneDrive/백업 관리 성격이 더 강하다.

## Git에 넣을 것과 빼야 할 것

### 넣을 것
- 코드: `*.py`, `*.js`, `*.jsx`, `*.html`, `*.php`
- 문서: `README*.md`, `HANDOVER*.md`, `docs/**`
- 실행기: `*.bat`, `*.ps1`, `*.sh`
- 설정 예시: `.env.example` 같은 샘플 파일

### 빼야 할 것
- 시크릿: `.env`, `bot_token.txt`, `allowed_chat_ids.txt`
- 대용량 원본 데이터: `*.csv`, `*.xlsx`, `*.xlsm`, `*.hwpx`, `*.zip`
- 재생성 가능한 산출물
- `__pycache__/`, 로그, 임시파일

## 지금 기준 현실적인 결론
- `myhome`와 `01_lhshapt`는 하나로 묶는다.
- `admin`과 `02_jogyeon`도 하나로 묶는다.
- `03_telegram_py`와 `ivwith`는 독립시킨다.
- `고객관리`와 `_vscode_chat_sync`는 마지막에 다룬다.

## 추천 시작 순서
1. `myhome/`부터 Git 시작
2. 안정화되면 `01_lhshapt/`를 같은 저장소로 편입
3. 그다음 `admin + 02_jogyeon`
4. 이후 `03_telegram_py`
5. 이후 `ivwith`

## 한 줄 요약
- 지금 당장 필요한 저장소는 하나다: 주택 파이프라인용 저장소
- 장기적으로는 다섯 축으로 분리하는 것이 가장 관리가 쉽다
