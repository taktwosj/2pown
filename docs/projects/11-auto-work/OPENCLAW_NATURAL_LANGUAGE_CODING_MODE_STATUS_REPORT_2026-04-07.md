# OpenClaw 자연어 코딩모드 상태 보고서

작성일: `2026-04-07`

## 1. 목적

이 문서는 현재 OpenClaw 코딩 구조가 어디까지 정리됐는지,
그리고 앞으로 `자연어 대화로 코딩 지시를 받고 자동작업까지 이어지는 코딩모드`를
어떻게 완성할지 한 번에 정리하는 상태 보고서이자 구현 계획서다.

이 문서는 아래 질문에 답하는 것을 목표로 한다.

1. 지금 live 상태가 정확히 어떤가
2. 현재 구조에서 어떤 파일이 어떤 역할을 맡고 있는가
3. 지금 자연어 코딩모드는 어디까지 되는가
4. 아직 안 되는 것은 무엇인가
5. 앞으로 어떤 순서로 붙여야 “자연어 대화형 코딩모드”가 되는가

## 2. 현재 상태 요약

### 2-1. Telegram 봇 런타임 상태

현재 live Telegram runtime은 2개로 분리돼 있다.

- office bot
  - runtime status: `C:\1POW\bot_runtime_status.json`
  - 현재 상태:
    - `status = polling_start`
    - `bot_profile = office`
    - `bot_username = junjunofc_bot`
    - `openclaw_handler_enabled = false`
    - `pid = 7372`
    - `base_dir = C:\1POW`
- coder bot
  - runtime status: `C:\1POW\runtime\ofcgptcoder_bot\bot_runtime_status.json`
  - 현재 상태:
    - `status = polling_start`
    - `bot_profile = codex`
    - `bot_username = ofcgptcoder_bot`
    - `openclaw_handler_enabled = true`
    - `pid = 21644`
    - `base_dir = C:\1POW\runtime\ofcgptcoder_bot`

즉 Telegram 입구는 현재 아래처럼 분리돼 있다.

- `junjunofc_bot` = 사무실/고객관리
- `ofcgptcoder_bot` = OpenClaw 코딩/상태 보고

### 2-2. front_secretary 상태

현재 OpenClaw 코딩 state 정본은 아래 파일이다.

- `C:\1other\openclaw-front-secretary\runtime\front_secretary\state.json`

현재 스냅샷:

- `conversation_mode = auto`
- `vs_mode = off`
- `next_action = await_user_request`
- `summary = 자동작업 HOLD. 원래 작업 목표와 현재 산출물이 어긋나고, 자동검증도 timeout으로 실패해 진행을 멈춥니다.`
- `active_task.status = blocked`
- `active_task.title = ivwith sync updated 반복 원인 확인, 서버 csv_to_db_sync.py normalization fix 반영 여부 점검 후 필요시 배포`

즉 현재 coder 쪽 OpenClaw 상태는 “완전히 비어 있는 idle 신규 코딩 세션”이 아니라,
예전 실무 task가 막힌 상태로 남아 있는 blocked task 상태다.

이 점이 지금 자연어 코딩모드를 깨끗하게 시작하는 데 가장 큰 혼선 포인트다.

### 2-3. 현재 task 산출물 상태

현재 blocked task 폴더는 아래에 있다.

- `C:\1other\openclaw-front-secretary\runtime\front_secretary\tasks\ivwith-sync-updated-반복-원인-확인-서버-csv_to_db_sync.py-normalization-fix-반영-여부-점검-후-필`

현재 들어 있는 핵심 산출물:

- `task_context.json`
- `task_manifest.json`
- `codex_plan_request.md`
- `codex_code_request.md`
- `claude_plan_review_a.md`
- `claude_plan_review_b.md`
- `claude_plan_review_a.json`
- `claude_plan_review_b.json`
- `claude_final_review_a.md`
- `claude_final_review_b.md`
- `claude_final_review_a.json`
- `claude_final_review_b.json`
- `full_verify.json`
- `review_history.jsonl`
- `verify_history.jsonl`
- `manifest_history.jsonl`

즉 artifact 체계는 비어 있지 않다.
문제는 “현재 coder 세션의 대표 task가 코딩 신규 작업이 아니라 예전 blocked task를 계속 바라보고 있다”는 점이다.

### 2-4. Claude 검수 운영 기준

현재 Claude 검수는 짧은 호출보다 “검수 프롬프트”가 느려지는 경향이 있다.
운영 기준은 아래처럼 고정한다.

1. 검수 전 헬스체크를 먼저 실행한다
   - `claude -p "Respond with exactly OK" --permission-mode dontAsk`
2. 헬스체크가 느리면 capacity/rate 문제로 보고, 본 검수는 짧게 하거나 HOLD로 기록한다
3. 본 검수 프롬프트는 최대한 가볍게 유지한다
   - 변경 파일 `3개 이하`
   - 핵심 함수명만 포함
   - `도구 사용 금지`
   - `제공된 텍스트만으로 판단`
   - `JSON only`
   - `5줄 안팎 응답`
4. 검수 호출은 기본적으로 `--permission-mode dontAsk`를 사용한다
5. `45~90초` 안에 응답이 없으면 `Claude timeout`으로 기록하고 다음 판단으로 넘어간다
6. 재검수는 전체 패치가 아니라 직전 지적 포인트만 좁혀서 다시 묻는다

## 3. 현재 구조

현재 구조는 크게 4층으로 봐야 한다.

### 3-1. Layer A: Telegram ingress/runtime

위치:

- `C:\1POW\03_telegram_py`
- `C:\1POW\bot.py`
- `C:\1POW\03_telegram_py\bot_runtime_profile.py`
- `C:\1POW\_restart_office_bot.ps1`
- `C:\1POW\_restart_codex_bot.ps1`

역할:

- Telegram 메시지 수신
- office/coder profile 분리
- coder bot과 office bot 토큰/런타임 분리
- coder bot에서는 OpenClaw 관련 명령을 coder 대화창으로 받는 입구 역할

핵심 파일 설명:

- `bot.py`
  - live Telegram runtime ingress copy
  - office bot과 coder bot이 공통으로 쓰는 실행 파일
  - canonical 변경이 동기화된 결과물로 본다
- `03_telegram_py`
  - Telegram 운영 정본(canonical edit surface)
  - runtime/profile/restart/runbook 기준 경로
- `03_telegram_py/bot_runtime_profile.py`
  - office profile과 coder profile의 env/runtime root를 나누는 helper
  - coder는 `runtime/ofcgptcoder_bot` 기준으로 뜨고, office는 `C:\1POW` 기준으로 뜬다
- `_restart_office_bot.ps1`, `_restart_codex_bot.ps1`
  - profile별 restart entrypoint
  - PID/lock/port가 profile별로 분리돼 있다

### 3-2. Layer B: OpenClaw coding bridge

위치:

- `C:\1other\openclaw-front-secretary`

역할:

- OpenClaw 코딩 정본 입구
- Telegram coder 상태/state/task 관리
- VS bind/VS 관측
- start contract 등록
- task artifact 폴더 생성
- Telegram coder 보고

핵심 파일 설명:

- `tools/auto_work/front_secretary.py`
  - user-facing OpenClaw CLI/state machine 정본
  - `apply`, `telegram-apply`, `telegram-sync-inbound`, `status`, `report` 같은 명령을 가진다
- `tools/auto_work/start_coding_task.py`
  - 코딩 작업 시작을 `start contract` 형태로 등록하는 스크립트
  - task title, mode, target repo, start channel, report channel을 받아 state/task를 만든다
- `docs/start_contract.schema.json`
  - start contract 필드 정의 정본
- `runtime/front_secretary/state.json`
  - 현재 coder OpenClaw 상태 정본
- `runtime/front_secretary/tasks/<slug>/...`
  - task 단위 artifact 저장소

### 3-3. Layer C: auto-coding engine

위치:

- `C:\1other\openclaw-auto-coding`

역할:

- 자동작업 핵심 엔진
- bundle writer
- verify
- Claude 검수/최종 gate 보조

핵심 파일 설명:

- `openclaw_auto_coding/auto_work_engine.py`
  - 자동작업 state machine 쪽 핵심 엔진
- `openclaw_auto_coding/auto_work_verify.py`
  - verify runner
  - worktree snapshot/direct mode 등 검증 정책 담당
- `docs/verify-codex.md`
  - verify 문서
- `scripts/run_verify_codex.sh`
  - 로컬 verify 편의 스크립트

### 3-4. Layer D: OpenClaw consult persona

위치:

- `~/.openclaw/workspace-consult`

역할:

- 대출상담/고객관리/도메인 문맥 전용 OpenClaw
- 코딩 작업 정본이 아니라 상담사 OpenClaw 프로필

즉 현재 `1other`만으로 모든 OpenClaw를 설명하면 안 되고,
실제로는 아래처럼 분리해서 봐야 한다.

- `C:\1other\openclaw-front-secretary` = 코딩 입구
- `C:\1other\openclaw-auto-coding` = 코딩 엔진
- `~/.openclaw/workspace-consult` = 대출상담 OpenClaw

## 4. 지금 자연어 코딩모드가 되는 범위

현재 coder bot과 front_secretary 기준으로 되는 것은 “완전 자유대화형”이 아니라
“명시적 작업 트리거 + 짧은 자연어 명령형”이다.

### 4-1. 현재 되는 입력

coder bot에서 현재 직접 트리거되는 입력 예:

- `코딩작업`
- `자동작업`
- `자동모드`
- `진행해`
- `vs 붙여`
- `vs 실행`
- `코딩하자`
- `다음단계 진행1`
- `진행 2`
- `2번으로 진행`

즉 지금은 아래 쪽에 가깝다.

- “코딩작업 시작”
- “자동작업으로 가”
- “다음 단계 진행”

이런 짧은 작업 명령형은 꽤 잘 받는다.

### 4-2. 현재 안 되는 것

아직 안 되는 것은 아래다.

1. 긴 자유문장을 그대로 신규 코딩 task로 자동 수렴하는 기능
2. 현재 blocked task가 남아 있을 때 새 자연어 작업을 깨끗하게 새 task로 갈아타는 기능
3. start contract 등록 이후 plan -> Claude plan review -> coding -> verify -> final review -> close까지 완전 자동 연결되는 end-to-end 자연어 루프
4. “지금 해야 할 일”을 fully state-aware하게 매번 자연어로 재구성하는 부분

즉 사용자가 coder bot에

- `지금부터 front_secretary start contract 자동등록 흐름을 다 붙여줘`

처럼 길게 쓰면, 지금 구조에서는 바로 “신규 코딩 task 생성 + 자동 루프 시작”으로 끝까지 이어지지 않는다.

현재는 여전히 중간에 아래 중 하나가 필요하다.

- 명시적 작업 트리거
- 숫자 응답
- 수동 start contract 등록

## 5. 지금 막혀 있는 핵심 문제

현재 자연어 코딩모드를 완성하지 못한 핵심 문제는 4개다.

### 문제 1. live coder state가 이미 blocked task를 안고 있음

현재 `front_secretary/state.json`은 새 코딩 task 대기 상태가 아니라
예전 `ivwith csv_to_db_sync.py` 관련 blocked task를 들고 있다.

이 상태에서는 새 자연어 코딩 요청이 들어와도,
“새 task를 열어야 하는지”
“기존 blocked task를 이어야 하는지”
판단이 흐려진다.

### 문제 2. 자연어 시작은 부분 구현, 공통 start contract 연결은 미완성

`start_coding_task.py`는 이미 만들어졌지만,
Coder Telegram에서 들어온 모든 자연어 코딩 요청이 자동으로 이 스크립트를 타도록 완전히 연결된 상태는 아니다.

즉 구현된 것은:

- `start contract 등록 메커니즘`

아직 남은 것은:

- `Coder Telegram 자연어 입력 -> start contract 자동 등록`

이다.

### 문제 3. auto loop 전체가 끝까지 닫히지 않음

현재는 아래 조각들이 부분적으로 있다.

- start contract
- plan request 생성
- artifact gate
- review/verify 산출물 구조

하지만 아래는 완전 자동으로 하나의 자연어 흐름으로 닫히지 않았다.

- plan review auto dispatch
- coding auto dispatch
- verify retry or hold guidance
- final review after auto verify
- blocked/stale task cleanup

### 문제 4. coder bot은 코딩 상태창이고, front_secretary는 state machine인데 둘의 합의가 아직 부족함

coder bot이 해야 하는 일:

- 자연어 입력을 받음
- OpenClaw 상태를 보여줌
- 숫자 응답/짧은 자연어 응답을 전달

front_secretary가 해야 하는 일:

- task/state를 만들고 관리
- next_action을 계산
- artifact와 gate를 관리

현재는 두 시스템이 연결은 돼 있지만,
“자연어로 신규 코딩 작업을 시작하는 첫 1단계”가 아직 완전히 일치하지 않는다.

## 6. 목표 상태

최종 목표는 아래다.

### 목표 1. coder bot에서 자유문장 1개로 새 코딩 task 시작

예:

- `front_secretary 자동 시작 계약을 coder bot 자연어 시작으로 붙여줘`

이 한 줄이 들어오면 내부에서 자동으로:

1. 새 task 제목 생성 또는 정규화
2. `start_contract.json` 생성
3. `task_context.json` 생성
4. `codex_plan_request.md` 생성
5. coder bot에 시작 보고 전송

까지 즉시 진행돼야 한다.

### 목표 2. auto 모드면 Claude/verify까지 자동 루프

사용자가 coder bot에서

- `자동작업으로 진행해`

라고 하면 아래가 자동으로 이어져야 한다.

1. start contract 등록
2. plan bundle 생성
3. Claude 계획 검수
4. 코딩 요청 생성
5. auto verify
6. Claude 최종 검수
7. 완료/보류/서버반영 판단 안내

### 목표 3. stale blocked task와 신규 task가 섞이지 않음

새 자연어 작업이 들어왔는데 예전 blocked task가 남아 있으면
아래 중 하나가 자동으로 돼야 한다.

1. 기존 blocked task를 archive 상태로 내림
2. 사용자에게 “이전 blocked task 유지 / 새 task 시작” 선택지 제시
3. 또는 `--force` 성격의 새 task 시작 절차로 넘어감

지금처럼 예전 task가 coder 세션을 계속 점유하면 안 된다.

## 7. 구현 계획

### Step 1. blocked task 처리 규칙 먼저 고정

목표:

- 현재 `state.json`의 blocked task를 자연어 시작의 기본 세션으로 쓰지 않게 한다

해야 할 일:

- `active_task.status in {blocked, done}`일 때 신규 자연어 작업 시작 규칙 정의
- archive 또는 replace 정책 추가
- coder bot에는 “이전 작업이 막혀 있음 / 새 작업으로 갈아탈까요?”를 숫자 대신 자연어형으로 안내

완료 기준:

- blocked task가 있어도 새 자연어 작업 시작이 깨끗하게 분기된다

### Step 2. coder bot 자연어 입력 -> start contract 자동 등록 연결

목표:

- 명시적 키워드만 아니라, coder bot에서 들어온 신규 코딩 자연어 문장을 start contract로 바로 바꾼다

해야 할 일:

- coder bot ingress에서 `idle` 또는 `blocked` 상태의 coder DM을 만나면
  - 긴 자연어 문장을 신규 코딩 후보로 간주
- `start_coding_task.py`를 내부 호출해 신규 task 생성

완료 기준:

- coder bot에서 신규 자연어 코딩 지시 1개로 `start_contract.json`이 생긴다

### Step 3. start contract 후 auto 루프 기본 연결

목표:

- `--mode auto`일 때 start contract에서 끊기지 않고 plan review까지 자동 진행

해야 할 일:

- plan bundle dispatch 자동
- Claude plan review 자동
- review artifact 저장
- 실패 시 hold 이유 자동 요약

완료 기준:

- coder bot 자연어 시작 후 `plan_review_a/b` artifact가 자동 생성된다

### Step 4. coding -> verify -> final review 자동 연결

목표:

- auto loop의 중간/후반부를 자동화한다

해야 할 일:

- code request dispatch
- verify dispatch
- verify 실패 시 retry 또는 hold 분기
- final review dispatch
- final gate 정리

완료 기준:

- 자연어 자동작업 1회가 final decision 대기까지 도달한다

### Step 5. Telegram 표시를 숫자형 선택지 중심에서 “할 일 중심”으로 개선

목표:

- 단순 `1/2/3`보다 “지금 해야 할 일”이 먼저 보이게 한다

해야 할 일:

- 현재 상태
- 지금 하는 일
- 다음 할 일
- 막힌 이유
- 지금 가능한 응답

형식으로 고정

완료 기준:

- 사용자가 coder bot에서 “지금 뭐가 문제인지”를 숫자 해석 없이 읽을 수 있다

## 8. 파일별 상세 설명

### `C:\1POW\bot.py`

현재 역할:

- Telegram live ingress canonical
- office/coder 공용 main
- office는 사무실 메뉴
- coder는 OpenClaw coder 대화

왜 중요한가:

- 자연어 코딩모드를 Telegram에서 시작하려면 결국 첫 메시지가 여기로 들어온다

### `C:\1POW\03_telegram_py\bot_runtime_profile.py`

현재 역할:

- office/coder runtime root 분리
- lock/pid/log 분리
- 토큰 분리

왜 중요한가:

- coder bot과 office bot이 섞이면 자연어 코딩모드 이전에 ingress부터 망가진다

### `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`

현재 역할:

- OpenClaw state machine
- Telegram apply
- next_action 계산
- artifact gate
- summary/operator view 생성

왜 중요한가:

- coder bot이 받은 자연어를 실제 코딩 state로 바꾸는 핵심 엔진이다

### `C:\1other\openclaw-front-secretary\tools\auto_work\start_coding_task.py`

현재 역할:

- start contract 등록
- task 폴더 생성
- task_context 생성
- 가능하면 coder Telegram 시작 보고
- auto 모드면 plan request 생성

왜 중요한가:

- 자연어 코딩모드를 구현할 때 첫 진입점으로 가장 재사용 가치가 높다

### `C:\1other\openclaw-front-secretary\runtime\front_secretary\state.json`

현재 역할:

- live coder state 정본

왜 중요한가:

- 지금 자연어 코딩이 막히는 이유도 여기 있는 blocked task 때문이다

### `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_engine.py`

현재 역할:

- 자동작업 엔진 정본

왜 중요한가:

- start contract 이후 실제 auto loop를 닫으려면 결국 이 엔진으로 수렴해야 한다

### `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_verify.py`

현재 역할:

- verify 수행
- worktree/direct mode 선택

왜 중요한가:

- 자연어 자동코딩모드가 실무적으로 믿을 수 있으려면 verify 자동화가 같이 붙어야 한다

## 9. 현재 판정

현재 상태는 아래로 보는 게 맞다.

- Telegram office/coder 분리: `OK`
- coder bot 코딩 보고 분리: `OK`
- start contract 도입: `OK`
- task/artifact 구조: `OK`
- blocked/done stale task 정리: `OK`
- 자연어 코딩 시작점: `OK`
- 텔레그램 지시모드: `OK`
- 완전 자동 자연어 코딩모드: `NOT YET`

한 줄로 요약하면:

현재는 `OpenClaw 코딩모드의 뼈대, blocked 정리, 자연어 draft, 텔레그램 지시모드까지는 정리됐지만, start contract 이후 auto plan review와 verify/final까지 끝까지 자동 루프로 닫는 단계는 아직 미완성`이다.

## 10. 바로 다음 작업

다음 작업의 우선순위는 이 순서가 맞다.

1. blocked task 정리 정책 구현
2. coder 자연어 입력 -> `start_coding_task.py` 자동 연결
3. auto mode plan review 자동 연결
4. verify/final review 자동 루프 연결
5. Telegram 상태 문구를 “지금 해야 할 일” 중심으로 고정

이 순서로 가야 “코딩 자연어대화모드로 지시를 받고 코딩하는 상태”가 된다.
