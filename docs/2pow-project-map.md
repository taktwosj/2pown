# 2POW 프로젝트 맵

이 문서는 현재 `2POW` 안에서 실제로 운영하거나 자주 손대는 작업을 도메인 기준으로 정리한 맵이다.

## 한눈에 보는 큰 작업 축
1. 주택 데이터 / 공고 / 영업리스트
2. 텔레그램 / 준준오피스 운영
3. CRM / 대출상담 / BANKLY
4. 고객관리 / 리포트
5. 통합관리 엑셀 / 업무자산
6. 공통 문서 / 운영 인프라

## 현재 폴더 기준 매핑

### 1. 주택 데이터 / 공고 / 영업리스트
- 핵심 폴더: `myhome/`
- 연동 대상: 외부 게시 repo `22blog`
- 현재 역할:
- `myhome/`는 최신 임대아파트 리스트, ETL 실행기, 영업용 산출물, 뷰어 기준본
- 공고문 notice 집계, 누락 보강, sales-ready 산출물 생성까지 이 축에서 다룬다.
- 대표 파일:
- `myhome/run_daily_pipeline.py`
- `myhome/build_sales_ready_outputs.py`
- `myhome/eeem-clean.html`
- `myhome/notice_detail_enricher.py`
- 판단:
- 현재 주택 데이터 정본 worktree는 `myhome/`다.

### 2. 텔레그램 / 준준오피스 운영
- 핵심 폴더: `03_telegram_py/`
- 연관 진입점: root `bot.py`, `START_TELEGRAM_BOT_NOW.bat`
- 현재 역할:
- 작업 완료 알림, 봇 운영, 스케줄 실행, 복구 런북
- 대표 파일:
- `bot.py`
- `03_telegram_py/codex_work_status.py`
- `03_telegram_py/work_done_notify.py`
- 판단:
- 텔레그램 런타임은 root `bot.py`와 `03_telegram_py/` wrapper 영역이 함께 움직이는 운영 묶음이다.

### 3. CRM / 대출상담 / BANKLY
- 핵심 폴더: `admin/`
- 연관 폴더: `jogyeon/`
- 현재 역할:
- 대출상담 자동화 UI, CRM 사이트, 원격 브리지, 운영용 배치
- 대표 파일:
- `admin/loan-automation-v6.jsx`
- `admin/crm_bridge.py`
- `jogyeon/bankly/`
- 판단:
- `admin/`과 `jogyeon/`은 업무 흐름상 강하게 연결돼 있지만, 현재는 별도 영역으로 보고 참조 관계를 명시적으로 관리하는 편이 안전하다.

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

### 5. 통합관리 엑셀 / 업무자산
- 핵심 폴더: `고객관리/`
- 대표 파일:
- `고객관리/통합관리.xlsm`
- 판단:
- 이 영역은 코드 저장소라기보다 운영 자산에 가깝다.
- Git에는 관련 스크립트, 설명 문서, 필드 매핑만 넣고 실제 대용량 `xlsm` 원본은 별도 보관하는 편이 낫다.

### 6. 공통 문서 / 운영 인프라
- 핵심 경로: `docs/`, `meta/`, `tools/`, `runtime/`
- 연관 위치: OneDrive 미러, 작업 스케줄러, 서버 런타임
- 판단:
- `2POW` 루트는 control-plane과 운영 래퍼를 담는 영역으로 본다.

## 현재 권장 Git 단위

1. `2pown` root control-plane repo
2. `myhome`
3. `03_telegram_py`
4. `ivwith`
5. `jogyeon`
6. `admin`
7. 외부 repo `22blog`

## 작업 묶음 기준

### 1. 주택 데이터 묶음
- 중심: `myhome/`
- 이유:
- 현재 가장 활발하게 작업 중이고, 코드/문서/결과 검증 흐름이 가장 명확하다.

### 2. 텔레그램 운영 묶음
- 중심: root `bot.py`, `03_telegram_py/`
- 이유:
- 배포 단위와 운영 단위가 분리되어 있고, wrapper와 live entrypoint가 같이 관리돼야 한다.

### 3. CRM / 조견 묶음
- 중심: `admin/`, `jogyeon/`
- 이유:
- 대출상담 사이트, 금융조견표, CRM 브리지, 참고 자산이 하나의 업무 흐름으로 이어진다.

### 4. 고객관리 / 리포트 묶음
- 중심: `ivwith/`
- 이유:
- 고객정보 민감도와 데이터 구조가 독립적이다.

### 5. 엑셀 / 사무자산 묶음
- 중심: `고객관리/`
- 이유:
- 코드보다 운영 자산 관리 성격이 강하다.

## 우선순위

### P1. 바로 Git 시작
- `2pown` root control-plane + `myhome`
- 이유:
- 현재 실제로 계속 수정 중이고, 변경 이력 관리 효과가 가장 크다.

### P2. 다음으로 시작
- `03_telegram_py`
- 이유:
- 운영 중요도가 높고, wrapper/worktree 기준 정리가 필요하다.

### P3. 그다음
- `ivwith`, `jogyeon`
- 이유:
- 데이터 민감도와 포함 범위를 조심스럽게 정해야 한다.

### P4. 이후
- `admin`
- 이유:
- 레거시 자산과 중복 산출물 정리가 선행돼야 한다.

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
- `myhome`는 주택 데이터 정본 worktree로 본다.
- root `bot.py`와 `03_telegram_py/`는 운영 묶음으로 본다.
- `admin`, `jogyeon`, `ivwith`는 서로 연관되지만 별도 작업 영역으로 다룬다.
- `고객관리`는 코드 repo보다 운영 자산으로 취급한다.

## 추천 시작 순서
1. root `2pown` 기준 문서와 control-plane부터 유지
2. `myhome/`
3. `03_telegram_py/`
4. `ivwith/`
5. `jogyeon/`
6. `admin/`

## 한 줄 요약
- `2POW`는 루트 control-plane + 개별 nested repo가 함께 있는 작업공간이고, 각 영역의 정본 경계를 문서로 먼저 분명히 하는 것이 중요하다.
