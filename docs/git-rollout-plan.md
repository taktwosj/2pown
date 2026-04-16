# Git/GitHub 적용 계획

> 현재 표준 운영 규칙은 `README.md`, `docs/START.md`, `meta/project_registry.json`, `docs/git-remote-setup.md`를 따른다.

## 현재 기준

- root control-plane repo: `C:\2POW` -> `https://github.com/taktwosj/2pown`
- nested project repos: `myhome`, `03_telegram_py`, `ivwith`, `jogyeon`, `admin`
- 외부 분리 repo: `22blog`
- `OneDrive`는 백업/원본 데이터 동기화 용도이지 canonical Git remote 모델이 아니다.

즉, 지금 구조는 `2POW 하나에 전부 넣는 방식`이 아니라:

1. `2POW` root repo에서 문서/규칙/control-plane 관리
2. 실제 프로젝트 코드는 각 nested repo에서 관리
3. 원본 데이터/대용량 자산/엑셀은 Git 밖에서 관리

## Git에서 바로 보는 것

- 코드
- 문서
- 공용 운영 스크립트
- 커밋 기록
- 변경 이유와 diff

## Git 밖에서 계속 보는 것

- 원본 CSV/XLSX/HWPX/ZIP
- 대용량 생성 결과물
- SQLite / dump / 고객 DB
- 시크릿 파일
- runtime 상태 파일 / 로그 / 백업본
- 통합관리 엑셀 실자산

## 사무실/다른 PC에서 작업하는 흐름

1. `C:\2POW` root repo를 `clone` 또는 `pull`
2. `docs/START.md`와 `meta/project_registry.json`으로 대상 프로젝트 식별
3. 대상이 repo-backed면 해당 nested repo에서 `fetch/pull` preflight 수행
4. 필요한 로컬 데이터와 업무 자산은 OneDrive/실자산 경로에서 확인
5. 수정 후 검증
6. repo-backed 변경은 가능하면 commit/push

## 경로 꼬임 방지 원칙

- 시작 위치는 항상 `C:\2POW`
- 기준 문서는 `docs/START.md`
- 프로젝트 식별 정본은 `meta/project_registry.json`
- 원격 이름 표준은 `origin`
- root `2POW`와 nested repo를 섞어서 다루지 않는다.
- OneDrive 경로는 backup/reference로만 보고 Git authority로 취급하지 않는다.

## 현재 Git 적용 단위

### 1. root control-plane

- 경로: `C:\2POW`
- 역할:
- 공통 문서
- project registry / schedule registry
- root wrappers
- `bot.py`
- `bot_app`
- 공용 `tools`

### 2. 주택 데이터

- 경로: `C:\2POW\myhome`
- 역할:
- ETL
- notice 보강
- sales-ready 산출물
- 뷰어

### 3. 텔레그램 운영

- 경로: `C:\2POW\03_telegram_py`
- 역할:
- wrapper
- bot runtime helper
- office deploy helper

### 4. 고객관리 / 리포트

- 경로: `C:\2POW\ivwith`

### 5. CRM / 조견

- 경로:
- `C:\2POW\jogyeon`
- `C:\2POW\admin`

### 6. 외부 게시

- 경로: `C:\ONEtaktwosj\OneDrive\22blog`
- 비고:
- `2POW` 안에 미러를 두지 않는다.

## 첫 커밋 또는 초기 push에 넣을 것

### root `2POW`

- `README.md`
- `AGENTS.md`
- `docs/**`
- `meta/**`
- `tools/**`
- `bot.py`
- `bot_app/**`
- 설정 예시 파일

### project repos

- `*.py`
- `*.js`
- `*.jsx`
- `*.html`
- `*.php`
- `*.md`
- 실행 배치/런북
- 설정 예시 파일

## 첫 커밋 또는 초기 push에 넣지 말 것

- `.env`
- 토큰 / 허용 ID / 키 파일
- 실제 고객 DB
- SQLite / dump / 대형 CSV/XLSX/HWPX/ZIP
- 재생성 가능한 캐시/산출물
- `runtime/**`
- `archive/**`
- 로그 / 임시파일 / `__pycache__`
- 통합관리 `xlsm` 실자산

## 현실적인 운영 원칙

- Git 원격은 코드와 문서의 정본 이력 관리다.
- OneDrive는 원본 데이터와 업무 자산의 보조 저장소다.
- root `2POW` repo는 nested repo를 vendoring하지 않는다.
- 프로젝트 코드 수정은 target nested repo에서 수행한다.
- `root docs 수정`과 `project code 수정`은 commit scope를 분리하는 편이 안전하다.

## 지금 바로 적용할 기본 순서

1. `C:\2POW`에서 시작
2. `docs/START.md` 읽기
3. `meta/project_registry.json` 읽기
4. 대상 repo가 있으면 `tools/ops/git_repo_preflight.ps1` 또는 동등한 `fetch/pull` 확인
5. 수정
6. 검증
7. 가능하면 commit/push

## 다음 단계

1. root `2POW` 문서와 control-plane을 계속 `2pown`에 반영
2. nested repo별 `.gitignore`와 원격 상태를 정리
3. 새 PC bootstrap 절차를 별도 문서/스크립트로 고정
4. OneDrive 의존 자산과 Git 자산의 경계를 더 명확히 문서화
