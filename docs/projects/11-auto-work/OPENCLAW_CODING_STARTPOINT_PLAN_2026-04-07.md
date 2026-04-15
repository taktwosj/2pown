# OpenClaw Coding Startpoint Plan

작성일: `2026-04-07`

## 1. 목적

앞으로 `코딩하자`, `코딩작업`, `자동작업 시작` 같은 요청이 들어왔을 때
입력 채널이 어디든 시작점이 하나로 보이게 정리한다.

목표는 아래 3가지를 동시에 만족하는 것이다.

1. 사용자가 `OpenClaw 코더 Telegram`에서 시작해도 같은 흐름을 탄다.
2. 사용자가 `Codex 대화창(여기)`에서 시작해도 같은 흐름을 탄다.
3. 자동작업이면 계획/검수/코딩/검증/최종보고가 자동으로 이어지고,
   모든 진행 상황은 `ofcgptcoder_bot`에 짧게 보고된다.

## 2. 현재 문제

지금은 구조가 아래처럼 나뉘어 있다.

- `C:\1other\openclaw-front-secretary`
  - Telegram ↔ VS ↔ runtime ↔ task/artifact 입구
- `C:\1other\openclaw-auto-coding`
  - 자동작업 엔진 / verify / review
- `C:\1POW\bot.py`
  - Telegram office/codex 봇 입구

문제는 시작점이 하나로 보이지 않는다는 점이다.

- Telegram에서 시작하면 Telegram 흐름처럼 보인다.
- Codex 채팅에서 시작하면 Codex 단독 작업처럼 보인다.
- OpenClaw 코딩 문서와 OpenClaw 대출상담 문서도 분리 기준이 아직 약하다.
- 결과적으로 “다른 코딩 작업을 시작할 때 항상 어디서부터 어떻게 들어가야 하는지”가 불분명하다.

## 3. 목표 구조

앞으로는 아래 3층으로 고정한다.

### A. OpenClaw 코딩

역할:
- 코딩 작업 시작점
- Telegram 코딩 대화창
- VS bind / VS 상태 / runtime state / task artifact 보고

정본:
- `C:\1other\openclaw-front-secretary`

책임:
- 작업 시작 요청을 받는다
- 현재 상태를 기록한다
- `ofcgptcoder_bot`에 상태 보고를 보낸다
- `openclaw-auto-coding` 엔진을 호출한다

### B. OpenClaw 대출상담

역할:
- 상담사 OpenClaw
- H시트 / 고객상태 / 상담요약 / 대출업무 문맥

정본:
- `~/.openclaw/workspace-consult`
  - 향후 필요시 `C:\1other\openclaw-consult` 계열로 명시 이전

책임:
- 코딩 작업을 시작하지 않는다
- 상담 문맥과 도메인 문서만 가진다

### C. 코딩 Repo

역할:
- 실제 작업 대상 코드

예:
- `C:\1other\openclaw-front-secretary`
- `C:\1other\openclaw-auto-coding`
- 이후 추가될 다른 repo

책임:
- 실제 구현
- 테스트
- 산출물 생성

## 4. 사용자 입장에서 보이는 시작점

앞으로 사용자가 보게 될 시작점은 아래 두 개뿐이다.

### 4-1. OpenClaw 코더 Telegram에서 시작

입력:
- `코딩작업`
- `코딩하자`
- `자동작업 시작`

응답:
1. `VS모드로 하기`
2. `자동작업`

세부:
- `1`이면 VS bind 흐름
- `2`이면 자동작업 흐름

### 4-2. Codex 대화창(여기)에서 시작

입력:
- `코딩하자`
- `이 작업 진행해`
- `자동작업으로 해`

처리 원칙:
- Codex는 직접 고립된 로컬 작업으로 끝내지 않는다.
- 먼저 `front_secretary` task/runtime 기준으로 작업을 등록한다.
- 바로 `ofcgptcoder_bot`에 “작업 시작” 보고를 보낸다.
- 자동작업이면 이후 단계별로 Telegram 보고를 이어간다.

즉 사용자는 채널이 달라도 결과적으로
`OpenClaw 코더가 관리하는 같은 작업`
으로 느껴져야 한다.

## 5. 표준 시작 흐름

### 공통 Start Contract

새 코딩 작업은 무조건 아래 정보로 시작한다.

- `task_title`
- `task_mode`
  - `manual`
  - `auto`
- `target_repo`
- `start_channel`
  - `telegram_coder`
  - `codex_chat`
- `report_channel`
  - 기본값: `ofcgptcoder_bot`

### 공통 Start Sequence

1. 작업 제목 확정
2. 대상 repo 확정
3. `front_secretary` state/task 생성
4. `ofcgptcoder_bot`에 시작 보고
5. `manual` 또는 `auto` 분기

## 6. manual / auto 정의

### manual

의미:
- 사용자가 직접 지시를 많이 주는 코딩 모드
- VS bind 중심
- Telegram에는 상태만 짧게 보고

흐름:
1. VS 프로젝트 선택
2. bind
3. Codex 구현
4. 필요 시 수동 검수
5. 결과 보고

### auto

의미:
- 계획/검수/코딩/verify/최종검수를 자동 루프로 돌리는 모드

흐름:
1. 계획 번들 생성
2. Claude 계획 검수
3. 계획 승인
4. Codex 코딩
5. auto verify
6. Claude 최종 검수
7. 완료 또는 서버반영 승인 판단

원칙:
- 자동작업이면 Codex가 따로 묻지 않아도 Claude 검수를 자동으로 붙인다.
- 상태 변화는 모두 `ofcgptcoder_bot`에 짧게 보고한다.

## 7. OpenClaw 코더 Telegram 보고 규칙

자동작업에서 Telegram 코더 봇은 “실행 콘솔 + 상태창” 역할을 한다.

항상 아래 중 일부를 짧게 보여준다.

- 현재 계획
- 현재 단계
- 진행률
- 지금 하는 일
- 다음 할 일
- 다다음 할 일
- 지금 보낼 숫자 답

예:

- `현재 계획: X`
- `진척: 3/5 단계 (코딩)`
- `할 일:`
  - `지금: 코딩 진행`
  - `다음: 자동검증`
  - `다다음: 최종검수`
- `지금 보낼 답:`
  - `1. 진행`
  - `2. 보류`

## 8. Codex 대화창에서 시작했을 때의 규칙

Codex 대화창에서 시작해도 최종 운영 상태는 OpenClaw 코더 기준으로 남겨야 한다.

즉 Codex는 아래를 기본으로 수행한다.

1. 로컬 구현 전에 task/state를 만든다
2. `ofcgptcoder_bot`에 시작 보고를 올린다
3. 자동작업이면 Claude 검수와 verify를 자동으로 돌린다
4. 중간 결과를 Telegram 코더에 보고한다
5. 마지막 결과도 Telegram 코더에 남긴다

이렇게 해야 사용자가
“여기서 시작했는데 왜 Telegram에는 아무것도 안 남지?”
라는 상태를 겪지 않는다.

## 9. 문서 정리 원칙

### OpenClaw 코딩 문서

남길 것:
- `AGENTS.md`
- `README.md`
- `TOOLS.md`
- `START_VSCODE.md`
- 필요 최소한의 `SOUL.md`, `USER.md`

역할:
- 코딩 브리지 규칙
- VS bind
- Telegram coder 상태/응답 규칙

### OpenClaw 대출상담 문서

남길 것:
- `AGENTS.md`
- `DOMAIN_CONTEXT.md`
- `TOOLS.md`
- `SOUL.md`
- `USER.md`

역할:
- 대출상담/고객/H시트 문맥

### 코딩 Repo 문서

남길 것:
- repo 자체 README/HANDOVER

역할:
- 구현 정본
- 테스트/배포/구조 설명

## 10. 구현 순서

### Step 1. 시작점 계약 고정

- `코딩하자` / `코딩작업` 입력을 공통 start contract로 묶는다.
- 입력 채널과 무관하게 `front_secretary` task를 먼저 만든다.

### Step 2. Telegram 보고 의무화

- Codex 채팅에서 시작한 작업도 즉시 `ofcgptcoder_bot`에 시작 보고를 보낸다.
- 이후 단계별 보고를 자동으로 붙인다.

### Step 3. auto 모드 자동검수 고정

- auto 모드면 Claude 계획 검수 / 최종 검수 / verify를 자동으로 수행한다.
- Codex가 따로 “검수할까요?”를 반복해서 묻지 않게 한다.

### Step 4. 문서 분리

- 코딩 문서와 대출상담 문서를 분리 기준에 맞게 재배치한다.
- “코딩 전에 읽는 문서”와 “OpenClaw persona 문서”를 명확히 나눈다.

### Step 5. 운영 안내 통일

- Telegram 코더 응답
- Codex 대화창 응답
- 시작/진행/완료 문구
를 같은 체계로 맞춘다.

## 11. 완료 기준

아래가 되면 이 계획은 닫는다.

1. 사용자가 `ofcgptcoder_bot`에서 `코딩작업`을 시작하면
   - VS모드/자동작업 선택이 뜬다.
2. 사용자가 Codex 대화창에서 `코딩하자`를 말하면
   - 같은 작업이 `front_secretary` task로 기록된다.
   - `ofcgptcoder_bot`에 시작 보고가 간다.
3. 자동작업이면
   - Claude 검수
   - verify
   - 최종보고
   가 자동으로 이어진다.
4. Telegram 코더에서 현재 상태와 다음 단계가 항상 보인다.
5. 코딩 문서와 대출상담 문서가 서로 역할별로 구분된다.

## 12. 한 줄 결론

앞으로의 코딩 시작점은
`입력은 어디서 하든 -> front_secretary task 생성 -> ofcgptcoder_bot 보고 -> manual/auto 분기`
로 통일한다.

그러면 사용자는
“OpenClaw 코더 Telegram”을 기준 콘솔로 삼고,
Codex 대화창은 그 작업을 실행하는 보조 입력창처럼 쓰게 된다.
