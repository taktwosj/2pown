# Git/GitHub 적용 계획

> 이 문서는 초기 rollout 기록이다. 현재 표준 운영 규칙은 `README.md`, `docs/START.md`, `meta/project_registry.json`, `docs/git-remote-setup.md`를 따른다.

## 먼저 답
- 지금은 `OneDrive 안 bare remote`까지 push가 끝난 상태다.
- 따라서 같은 OneDrive 계정이 동기화되면 사무실 PC에서도 Git 이력과 원격 저장소를 같이 받을 수 있다.
- 사무실에서는 `clone` 또는 `pull` 하면 코드와 문서, 작업 이력을 바로 볼 수 있다.
- 하지만 `Git에 올리지 않은 원본 데이터/결과물`은 계속 OneDrive에서 봐야 한다.
- 다만 작업 루트(`C:\1POW`)와 OneDrive 미러(`...\OneDrive\11AI\1POW`)는 별개로 보고, OneDrive는 `bare remote 백업 저장소`로만 쓰는 편이 안전하다.

## 아주 쉽게 구분

### Git 원격에서 바로 보는 것
- 코드
- 문서
- 실행 스크립트
- 커밋 기록
- 언제 무엇을 왜 바꿨는지

### OneDrive에서 계속 보는 것
- 원본 CSV/XLSX/HWPX/ZIP
- 대용량 생성 결과물
- 시크릿 파일
- 로그/백업본

## 사무실에서 실제로 보이는 흐름
1. 집에서 코드 수정
2. 커밋
3. `origin`으로 push
4. OneDrive 동기화 완료 확인
5. 사무실 PC에서 `git pull`
6. 최신 코드와 작업 이력 확인
7. 필요한 원본 데이터와 결과물은 OneDrive에서 확인

## 경로 꼬임 방지 원칙
- 기준 작업 폴더는 가능하면 집/사무실 모두 `C:\1POW`
- OneDrive 안 `11AI\1POW`는 백업/미러로만 사용
- 집/사무실 OneDrive 절대경로가 달라도 `repair_git_mirror_remotes.*`가 각 PC에서 `origin`을 절대경로로 다시 맞춘 뒤 `push/pull`
- 작업 시작 전 `pull`, 작업 종료 후 `push`

## 저장소별 적용 순서

### 1. 주택 파이프라인
- 대상:
- `1POW/myhome`
- `1POW/01_lhshapt`
- 이유:
- 지금 가장 활발하게 작업 중이고, 가장 빨리 이력 관리 효과를 본다.

### 2. CRM/대출상담/금융조견표
- 대상:
- `1POW/admin`
- `1POW/02_jogyeon`

### 3. 텔레그램 운영
- 대상:
- `1POW/03_telegram_py`

### 4. 고객관리
- 대상:
- `1POW/ivwith`

### 5. 통합관리 엑셀/운영 인프라
- 대상:
- `1POW/고객관리`
- `1POW/_vscode_chat_sync`

## 첫 커밋에 넣을 것

### myhome
- `*.py`
- `*.html`
- `README_ETL.md`
- `RUN_HOUSING_ETL.*`

### 01_lhshapt
- `housing_integrate.py`
- `hwspr_merge_020304.py`
- `sh_extract_merge.js`
- `README.md`

### 03_telegram_py
- `bot.py`
- `codex_work_status.py`
- `work_done_notify.py`
- 운영 배치/런북 문서

### admin
- `crm_bridge.py`
- `loan-automation-v6.jsx`
- 운영 문서/배치

### 02_jogyeon
- `README.md`
- `_read_xlsx.py`
- `bankly/금융조견.html`
- `bankly/금융사이트.html`
- 레거시 JSX 참고본

### ivwith
- `*.py`
- `*.php`
- `*.html`
- `*.js`
- `*.md`
- 실행 배치

## 절대 첫 커밋에 넣지 말 것
- `.env`
- `bot_token.txt`
- `allowed_chat_ids.txt`
- 실제 고객 DB
- 대용량 CSV/XLSX/HWPX/ZIP
- SQLite, dump 파일
- 로그, 임시파일, 캐시

## 현실적인 운영 원칙
- Git 원격은 `작업일지` 역할을 한다.
- OneDrive는 `재료창고` 역할을 한다.
- 사무실에서 바로 확인 가능한 것은 `원격으로 push된 코드와 문서`다.
- 사무실에서 계속 필요하지만 Git에 안 올릴 것은 `OneDrive 데이터`다.

## 다음 단계
1. 각 프로젝트별 Git 저장소 초기화
2. `.gitignore` 확인
3. 첫 커밋
4. legacy mirror remote 생성
5. 첫 push
6. 사무실 PC에서 clone/pull
