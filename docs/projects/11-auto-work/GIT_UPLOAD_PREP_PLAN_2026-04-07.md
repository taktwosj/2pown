# Git Upload Prep Plan

작성일: `2026-04-07`

## 1. 목적

지금 작업 결과를 Git에 올릴 때,

- 어느 repo를 먼저 올릴지
- 어디까지를 이번 업로드 범위로 볼지
- 어떤 파일은 절대 올리지 말아야 하는지

를 미리 고정한다.

이번 계획의 핵심은 아래 2가지다.

1. `1other`의 코딩 정본 2개 repo는 작업 단위대로 분리해서 올린다.
2. `1POW`는 현재 worktree 오염 범위가 크므로, 지금 상태 그대로 한 번에 올리지 않는다.

## 2. 현재 판단

### A. `C:\1other\openclaw-front-secretary`

성격:
- OpenClaw 코딩 입구
- Telegram/VS/runtime/task/artifact 관리

현재 변경 특징:
- 변경 범위가 비교적 명확하다
- start contract, start task 등록, 상태/프롬프트 정리, 문서 반영 중심이다
- 현재 `git status` 기준으로 업로드 후보를 파일 단위로 추릴 수 있다

현재 보이는 업로드 후보:
- `README.md`
- `TOOLS.md`
- `docs/HANDOVER.md`
- `tools/auto_work/front_secretary.py`
- `tools/auto_work/start_coding_task.py`
- `docs/start_contract.schema.json`
- `tests/test_front_secretary_auto_work.py`
- `tests/test_start_coding_task.py`
- `tests/test_verify_smoke.py`

### B. `C:\1other\openclaw-auto-coding`

성격:
- 자동코딩 엔진
- verify/review/worktree/engine

현재 변경 특징:
- 엔진 쪽 변경이 상대적으로 응집돼 있다
- 다만 `README`, `HANDOVER`, `verify-codex`, `engine`, `verify`가 같이 바뀌어 있어 업로드 전에 묶음 판단이 필요하다
- `.claude/`, `scripts/` 같은 새 폴더는 포함 여부를 먼저 판단해야 한다

현재 보이는 업로드 후보:
- `README.md`
- `docs/HANDOVER.md`
- `docs/verify-codex.md`
- `openclaw_auto_coding/auto_work_engine.py`
- `openclaw_auto_coding/auto_work_verify.py`
- `tests/test_auto_work_verify.py`

보류 후보:
- `.claude/`
- `scripts/`

### C. `C:\1POW`

성격:
- 사무실 Telegram bot 런타임/입구
- 여러 프로젝트가 한 repo에 섞인 메타 저장소

현재 변경 특징:
- 변경 파일이 매우 많다
- unrelated change가 대량으로 섞여 있다
- 지금 상태 그대로 push하면 범위를 통제하기 어렵다

판단:
- 이번 업로드의 1차 대상은 아니다
- `1POW`는 별도 cleanup 또는 path-limited commit 계획이 있어야 한다

## 3. 이번 업로드 원칙

### 원칙 1. `1other` 먼저

이번에 Git 업로드 준비의 우선순위는 아래 순서다.

1. `openclaw-front-secretary`
2. `openclaw-auto-coding`
3. `1POW`는 나중

이유:
- `1other`는 코딩 정본이다
- `1POW`는 런타임/사무실 봇/메타 변경이 섞여 있다
- 현재 시점에서 핵심 산출물은 `1other`에 있다

### 원칙 2. `1POW`는 부분 업로드만 허용

`1POW`를 올리게 되더라도 아래 범위만 후보로 본다.

- `bot.py`
- `03_telegram_py/**`
- `docs/projects/11-auto-work/**`
- 관련 runbook/handover 문서

이번 범위에서 제외:
- `tesla/**`
- 외부 공고문 게시 repo 관련 경로
- `src/**`
- `chart/**`
- 대량의 unrelated meta 변경
- runtime 생성물

### 원칙 3. 시크릿/런타임은 절대 제외

절대 commit 금지:
- `03_telegram_py/bot_token.txt`
- `runtime/**/bot_token.txt`
- `03_telegram_py/allowed_chat_ids.txt`
- `runtime/**/allowed_chat_ids.txt`
- `runtime/**`
- `*.pid`
- `locks/**`
- `logs/**`
- state/task artifact JSON

## 4. repo별 업로드 계획

### 4-1. `openclaw-front-secretary`

목표:
- 코딩 시작점 수렴 구조와 front_secretary 상태/프롬프트 정리를 1차로 올린다

포함 예정:
- start contract/schema
- `start_coding_task.py`
- `front_secretary.py`
- 관련 테스트
- 관련 문서

제외 예정:
- 임시 runtime 산출물
- 현재 작업 task 폴더

예상 커밋 주제:
- `feat(front-secretary): add start contract and coding task registration`
- `fix(front-secretary): improve final prompt guidance and task start reporting`

### 4-2. `openclaw-auto-coding`

목표:
- 엔진/verify 개선분을 별도 커밋으로 올린다

포함 예정:
- `auto_work_engine.py`
- `auto_work_verify.py`
- verify 관련 테스트
- 엔진 문서

판단 보류:
- `.claude/`
- `scripts/`

이 둘은 아래 기준으로 재판단한다.
- 엔진 동작에 필수인가
- 문서/검증만으로 설명 가능한가
- repo 표준 산출물인가

예상 커밋 주제:
- `feat(auto-coding): improve verify and engine workflow artifacts`

### 4-3. `1POW`

목표:
- office/coder bot 분리 수정이 실제로 필요한 경우에만 path-limited commit을 만든다

이번 즉시 업로드 대상 아님

사유:
- 현재 `git status`가 너무 크다
- unrelated dirty change가 많다
- `1POW`는 정리 없는 즉시 push가 위험하다

향후 포함 가능 후보:
- `bot.py`
- `03_telegram_py/bot_runtime_profile.py`
- `03_telegram_py/DUAL_BOT_RUNTIME.md`
- `03_telegram_py/HANDOVER.md`
- `docs/projects/11-auto-work/*.md`

## 5. 선행 확인 사항

### A. remote 확인

현재 확인 결과:
- `C:\1other\openclaw-front-secretary` : remote 없음
- `C:\1other\openclaw-auto-coding` : remote 없음
- historical control-plane clone : `origin` configured

따라서 `1other` 두 repo는 push 전 아래 중 하나가 먼저 필요하다.

1. 새 GitHub repo 생성
2. 기존 원격 repo URL 연결

### B. branch 전략

권장:
- repo별 feature branch 1개씩 분리

예:
- `front-secretary/2026-04-07-start-contract`
- `auto-coding/2026-04-07-verify-artifacts`
- `1pow/2026-04-07-dual-bot-runtime-cleanup`

### C. 업로드 범위 freeze

commit 전에 반드시 할 것:
- `git status --short` 재확인
- 이번 커밋에 들어갈 파일 목록을 문서 또는 메모로 고정
- unrelated file이 staging에 들어가지 않았는지 다시 확인

## 6. 실제 업로드 순서

### Step 1. `openclaw-front-secretary`부터 정리

할 일:
- 포함 파일 확정
- remote 연결
- branch 생성
- commit
- push

### Step 2. `openclaw-auto-coding` 정리

할 일:
- `.claude/`, `scripts/` 포함 여부 최종 판단
- 포함 파일 확정
- remote 연결
- branch 생성
- commit
- push

### Step 3. `1POW`는 별도 cleanup 후

할 일:
- path-limited 범위만 다시 추림
- runtime/secret 생성물 완전 제외 확인
- office/coder bot 관련 파일만 따로 commit

## 7. 이번에 바꾸지 말 것

지금 계획 단계에서는 아래를 건드리지 않는다.

- `03_telegram_py/bot_token.txt`
- `03_telegram_py/allowed_chat_ids.txt`
- runtime 아래 생성물
- 대용량 데이터 파일
- unrelated repo 전반 cleanup

## 8. 완료 기준

이번 계획서 기준 완료는 아래다.

1. `openclaw-front-secretary` 업로드 파일 목록 확정
2. `openclaw-auto-coding` 업로드 파일 목록 확정
3. 각 repo remote 유무 확인 완료
4. `1POW`는 보류 또는 path-limited 범위로 분리 판단 완료
5. 실제 commit/push 순서가 문서로 고정

## 9. 한 줄 정리

지금 Git 업로드는

- `1other`의 두 코딩 정본 repo를 먼저 올리고
- `1POW`는 지금 상태 그대로 밀지 말고
- office/coder bot 관련 최소 범위만 나중에 따로 올리는 순서

로 가는 게 맞다.
