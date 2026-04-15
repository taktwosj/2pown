# OpenClaw 자연어 코딩모드 최종안

작성일: `2026-04-07`

## 1. 문서 목적

이 문서는 현재 OpenClaw 코딩 구조와 live 상태를 정확히 고정하고,
그 위에서 `자연어 대화형 코딩모드`를 완성하기 위한 최종 실행안을 정리한다.

여기서 말하는 자연어 코딩모드는 아래를 뜻한다.

- 사용자가 `ofcgptcoder_bot` 또는 Codex 대화창에서
- 긴 자연어 코딩 지시 1문장을 보내면
- 그것이 새 코딩 task로 수렴되고
- 자동모드면 plan/review/coding/verify/final review까지 이어지며
- 상태와 할 일은 coder bot에 계속 보고되는 구조

이번 최종안은 아래 4가지를 동시에 만족하는 것을 목표로 한다.

1. 지금 live 상태를 사실대로 적는다.
2. 현재 구조와 파일 역할을 헷갈리지 않게 적는다.
3. 무엇이 이미 되고 무엇이 아직 안 되는지 분명히 적는다.
4. 추가 질문 없이 바로 구현 가능한 순서와 규칙을 고정한다.

## 2. 현재 상태

### 2-1. Telegram 런타임 상태

현재 Telegram bot은 2개가 분리돼 있다.

- office bot
  - 경로: `C:\1POW\bot_runtime_status.json`
  - 현재값:
    - `status = polling_start`
    - `bot_profile = office`
    - `bot_username = junjunofc_bot`
    - `openclaw_handler_enabled = false`
    - `pid = 7372`
    - `updated_at = 2026-04-07 20:17:30`
- coder bot
  - 경로: `C:\1POW\runtime\ofcgptcoder_bot\bot_runtime_status.json`
  - 현재값:
    - `status = polling_start`
    - `bot_profile = codex`
    - `bot_username = ofcgptcoder_bot`
    - `openclaw_handler_enabled = true`
    - `pid = 21644`
    - `updated_at = 2026-04-07 20:17:30`

현재 판정:

- `junjunofc_bot` = 사무실/고객관리 전용
- `ofcgptcoder_bot` = OpenClaw 코딩/상태 보고 전용

이 분리는 현재 live 기준으로 동작 중이다.

### 2-2. front_secretary 상태

현재 coder OpenClaw의 state 정본은 아래다.

- `C:\1other\openclaw-front-secretary\runtime\front_secretary\state.json`

현재 핵심값:

- `conversation_mode = auto`
- `vs_mode = off`
- `next_action = await_user_request`
- `summary = 자동작업 HOLD. 원래 작업 목표와 현재 산출물이 어긋나고, 자동검증도 timeout으로 실패해 진행을 멈춥니다.`
- `active_task.status = blocked`
- `active_task.title = ivwith sync updated 반복 원인 확인, 서버 csv_to_db_sync.py normalization fix 반영 여부 점검 후 필요시 배포`

즉 현재 coder 세션은 “깨끗한 신규 task 대기 상태”가 아니라,
예전 실무 task가 `blocked`로 남아 있는 상태다.

이 blocked task 점유가 지금 자연어 코딩모드의 1순위 blocker다.

### 2-3. artifact 상태

현재 blocked task 폴더에는 아래 artifact가 존재한다.

- `task_context.json`
- `task_manifest.json`
- `codex_plan_request.md`
- `codex_code_request.md`
- `claude_plan_review_a/b.md`
- `claude_plan_review_a/b.json`
- `claude_final_review_a/b.md`
- `claude_final_review_a/b.json`
- `full_verify.json`
- `review_history.jsonl`
- `verify_history.jsonl`
- `manifest_history.jsonl`

즉 구조와 저장 형식은 이미 있다.
문제는 “새 자연어 작업을 시작할 때 현재 blocked task와 어떻게 분리할지” 규칙이 아직 없다는 점이다.

## 3. 현재 구조

현재 구조는 아래 4층으로 고정해서 본다.

### Layer A. Telegram ingress/runtime

위치:

- `C:\1POW\03_telegram_py`
- `C:\1POW\bot.py`
- `C:\1POW\03_telegram_py\bot_runtime_profile.py`
- `C:\1POW\_restart_office_bot.ps1`
- `C:\1POW\_restart_codex_bot.ps1`

역할:

- Telegram 메시지 수신
- office/coder 프로필 분리
- token/runtime root/lock/pid 분리

중요 설명:

- 정본(수정)은 `C:\1POW\03_telegram_py`다.
- 실행(running)은 `C:\1POW\bot.py`다. 이 파일은 동기화/배포본 ingress로 본다.
- root `bot.py`는 기본 수정 대상으로 보지 않는다. 공식 edit surface 확장 없이는 `03_telegram_py`와 `front_secretary` 쪽을 우선 수정한다.

### Layer B. OpenClaw coding bridge

위치:

- `C:\1other\openclaw-front-secretary`

역할:

- coder task/state/runtime 관리
- Telegram apply / inbound sync
- VS bind / VS 상태
- start contract 생성
- task artifact 생성

핵심 파일:

- `tools/auto_work/front_secretary.py`
- `tools/auto_work/start_coding_task.py`
- `docs/start_contract.schema.json`
- `runtime/front_secretary/state.json`
- `runtime/front_secretary/tasks/<slug>/...`

### Layer C. auto-coding engine

위치:

- `C:\1other\openclaw-auto-coding`

역할:

- 자동작업 엔진
- bundle 생성
- verify
- review/final gate 보조

핵심 파일:

- `openclaw_auto_coding/auto_work_engine.py`
- `openclaw_auto_coding/auto_work_verify.py`
- `docs/verify-codex.md`
- `scripts/run_verify_codex.sh`

### Layer D. consult persona

위치:

- `~/.openclaw/workspace-consult`

역할:

- 대출상담 도메인 OpenClaw
- 고객관리/H시트/상담 문맥

이 레이어는 코딩 정본이 아니다.

## 4. 지금 되는 것과 안 되는 것

### 4-1. 지금 되는 것

현재 coder bot은 아래 입력을 꽤 안정적으로 받는다.

- `코딩작업`
- `자동작업`
- `텔레그램 지시모드`
- `자동모드`
- `진행해`
- `vs 붙여`
- `vs 실행`
- `코딩하자`
- `다음단계 진행1`
- `진행 2`
- `2번으로 진행`

즉 지금은 “명시적 작업 트리거 + 짧은 자연어 명령형 + 텔레그램 지시모드 진입” 수준까지는 된다.

### 4-2. 지금 안 되는 것

아직 안 되는 것은 아래다.

1. 긴 자유문장을 신규 코딩 task로 자동 수렴
2. blocked task가 있을 때 새 작업/기존 작업을 깨끗하게 분기
3. start contract 이후 plan review 자동 연결
4. coding -> verify -> final review 자동 루프 end-to-end
5. Telegram 상태를 숫자형 중심이 아니라 “지금 해야 할 일” 중심으로 완전 고정

즉 현재 상태는:

- ingress는 정리됨
- start contract 뼈대도 있음
- artifact 구조도 있음
- 하지만 “자연어 1줄 -> 새 코딩 task 자동 시작”은 아직 미완성

## 5. 최종 규칙

이번 최종안에서 아래 규칙을 확정한다.

### 규칙 1. blocked task 처리 규칙

현재 `active_task.status in {blocked, done}`일 때,
새 자연어 코딩 요청이 들어오면 기존 task를 기본 세션으로 끌고 가지 않는다.

기본 규칙:

1. 기존 blocked/done task가 있으면 `continue_default = false`
2. 사용자가 명시적으로 “이전 작업 이어서”라고 말하지 않으면 신규 task draft를 우선 제안
3. 사용자에게 1회만 물음
   - `1. 기존 작업 이어가기`
   - `2. 새 작업 시작`
4. `2`가 선택되면 기존 task는 `archived` 성격 상태로 내리고 새 task를 연다

즉 blocked task는 “기본 세션 점유”를 못 한다.

### 규칙 2. 자연어 신규 코딩 의도 판정 규칙

`20자 이상`만으로 신규 코딩 의도를 판정하지 않는다.

신규 코딩 draft 후보로 올리는 기준:

1. 현재 채널이 coder bot 또는 codex chat
2. 현재 상태가 `idle`, `blocked`, `done` 중 하나
3. 숫자 응답이나 기존 짧은 명령형이 아님
4. 질문형만으로 끝나지 않음
5. 아래 코딩 키워드 중 하나 이상 포함

코딩 키워드 기본셋:

- `작업`
- `코딩`
- `구현`
- `수정`
- `추가`
- `고쳐`
- `만들어`
- `붙여`
- `자동화`
- `리팩터링`
- `fix`
- `feature`

보조 조건:

- 길이 기준은 `키워드 조건을 통과한 뒤` 보조적으로만 사용
- 키워드가 없으면 길이가 길어도 draft 후보로 올리지 않는다
- 문장 끝이 `?`이거나 `왜`, `뭐야`, `무슨 뜻`, `어디`, `어떻게 돼` 같은 질문 패턴만 있으면 draft 후보에서 제외한다
- 단, `수정해줘`, `추가해줘`, `만들어줘`, `고쳐줘`처럼 키워드가 있는 명령형이면 물음표가 있어도 draft 후보가 될 수 있다

즉 아래는 draft 후보가 아니다.

- `오늘 오전 회의 결과 정리해줘`
- `front_secretary 뭐가 문제야?`

### 규칙 3. 자연어는 바로 등록하지 않고 draft + 1회 확인

자연어 코딩 요청은 바로 `start_contract.json`으로 등록하지 않는다.

먼저 아래 절차를 탄다.

1. `start_contract_draft` 생성
2. draft는 `state.pending_draft` 또는 `draft_id` 형태로 `state.json`에 저장
3. `next_action = confirm_start_draft`로 고정해 다음 입력이 draft 확인 숫자 응답임을 명시
4. `pending_draft`가 존재하는 동안 숫자 입력 `1/2`는 오직 draft confirm에만 소비한다
5. draft TTL은 기본 `10분`으로 둔다
6. TTL 만료 체크는 별도 타이머가 아니라 `인바운드 메시지 처리 entry`에서 lazy하게 수행한다
   - 만료면 draft를 즉시 폐기한다
   - 만료 안내를 1회 남긴다
   - 그리고 그 같은 메시지를 `idle` 흐름으로 처음부터 다시 처리한다
   - 이 재처리는 내부 플래그 기준으로 1회만 수행하고, 재처리 플래그는 state에 저장하지 않는다
7. coder bot에 짧은 확인문 전송
   - `새 코딩 작업으로 시작할까요?`
   - `1. 시작`
   - `2. 취소`
8. `confirm_start_draft` 상태에서 숫자 대신 새 자연어 코딩 요청이 오면 기존 pending draft를 새 draft로 교체하고 TTL을 새로 시작한 뒤 확인 프롬프트를 다시 띄운다
9. `1`일 때만 실제 `start_coding_task.py` 실행
10. `confirm_start_draft` 상태에서 숫자도 아니고 새 코딩 요청도 아닌 문장이 오면 상태는 유지하고 `1(시작)/2(취소) 또는 새 코딩 지시를 입력하세요` 안내만 다시 보여준다

이 규칙은 오작동을 줄이기 위해 필수다.

### 규칙 4. target_repo 미확정 분기

자연어에서 `target_repo`를 추출하지 못하면 바로 실패하지 않는다.

우선순위:

1. 현재 VS bind가 있으면 그 cwd를 1순위 후보로 사용
2. active project가 있으면 그 repo를 후보로 사용
3. 명확하지 않으면 coder bot에 repo 선택지를 제시

예:

- `1. openclaw-front-secretary`
- `2. openclaw-auto-coding`
- `3. 현재 작업 폴더 직접 입력`

즉 `start_coding_task.py` 실패 경로는 아래처럼 고정한다.

- `target_repo 확정 가능` -> 실제 등록
- `target_repo 불명확` -> repo 선택 prompt

### 규칙 5. coder bot과 front_secretary 역할 고정

- coder bot 역할
  - 입력 수신
  - 현재 상태 표시
  - 숫자/짧은 응답 전달
  - start draft 확인 질문 전송

- front_secretary 역할
  - state/task/artifact 관리
  - next_action 계산
  - gate 판단
  - summary/operator view 생성

신규 코딩 시작의 첫 1단계는 반드시 아래로 고정한다.

- coder bot이 자연어를 받음
- front_secretary가 draft/task/state를 판단

즉 coder bot이 독자적으로 task를 정의하지 않는다.

### 규칙 6. Telegram 상태 표시 형식

최종적으로 coder bot 상태 표시는 아래 형식으로 고정한다.

- 현재 상태
- 현재 계획
- 지금 하는 일
- 다음 할 일
- 막힌 이유
- 지금 가능한 응답

즉 숫자만 던지지 않는다.

### 규칙 7. artifact-gated stage 전환

중간 단계는 state 기반이어도 되지만, 완료와 배포는 artifact가 없으면 절대 못 넘어간다.

강제 게이트:

- `RELEASE` 진입 조건
  - `full_verify.json`
  - `claude_final_review_a.json`
  - `claude_final_review_b.json`
- `DONE` 진입 조건
  - `task_summary.json`
  - `verify_manifest.json`

위 artifact가 하나라도 없으면:

- stage는 유지
- summary에는 부족한 artifact 이름을 그대로 표시
- coder bot에는 `지금 해야 할 일`로 부족분을 먼저 보여준다

### 규칙 8. verify / worktree 정책

verify와 worktree는 아래처럼 강제한다.

- worktree는 verify 단계에서만 사용한다
- ingress, start draft, gate prompt 경로에서는 worktree 사용 금지
- 테스트 기본값은 `WORKTREE=0`으로 둔다
- worktree 경로는 가능하면 WSL/ext4 (`/tmp`, `/home`)를 우선 사용하고 `/mnt/c`는 피한다
- worktree나 checkout 때문에 verify가 길어지면 HOLD 사유에 그 내용을 그대로 적는다

### 규칙 9. Claude 검수 실행 정책

Claude 검수는 느려질 수 있으므로 아래 경량 표준으로 고정한다.

1. 검수 전 헬스체크를 먼저 실행한다
   - `claude -p "Respond with exactly OK" --permission-mode dontAsk`
2. 헬스체크가 평소보다 느리면 capacity/rate 이슈로 보고, 본 검수는 `HOLD` 또는 재시도로 넘긴다
3. 본 검수 프롬프트는 최대한 가볍게 유지한다
   - 변경 파일 `3개 이하`
   - 핵심 함수명만 포함
   - diff는 짧게
   - `도구 사용 금지`
   - `제공된 텍스트만으로 판단`
   - `JSON only`
   - `5줄 안팎 응답`
4. 검수 호출은 기본적으로 `--permission-mode dontAsk`를 사용한다
5. 검수 타임아웃은 기본 `45~90초`로 두고, 넘기면 `Claude timeout`을 HOLD 사유로 기록한다
6. 재검수는 전체 패치 재검토가 아니라, 직전 지적 포인트만 좁혀서 다시 묻는다
7. `--bare`는 인증 방식이 확인된 경우에만 선택적으로 쓴다. 기본 표준은 아니다

## 6. 구현 순서

우선순위는 반드시 아래 순서를 유지한다.

### Step 1. blocked task 정리 정책 구현

목표:

- blocked/done task가 새 자연어 작업을 가로채지 못하게 한다

구현 파일 후보:

- `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`

구현 내용:

- `active_task.status in {blocked, done}` 처리 분기
- `archive / continue / replace` 선택 정책
- coder bot용 확인 prompt

완료 기준:

- blocked task가 있어도 신규 task 시작이 흔들리지 않는다

### Step 2. coder 자연어 입력 -> start contract draft 자동 연결

목표:

- 긴 자연어 코딩 지시를 draft 후보로 자동 인식한다

구현 파일 후보:

- `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`
- `C:\1other\openclaw-front-secretary\tools\auto_work\start_coding_task.py`
- 필요 시 `C:\1POW\03_telegram_py` 아래 허용된 telegram 보조 파일

구현 내용:

- 코딩 키워드 + 길이 + 질문 제외 판정
- draft 생성
- `1 시작 / 2 취소` 1회 확인
- target_repo 미확정 시 repo 선택지 제시

완료 기준:

- 자연어 1문장 -> draft 생성 -> 1회 확인 -> `start_contract.json` 생성

### Step 3. start contract 후 plan review 자동 연결

목표:

- `--mode auto`이면 start contract에서 끊기지 않고 plan review까지 이어간다

구현 파일 후보:

- `C:\1other\openclaw-front-secretary\tools\auto_work\start_coding_task.py`
- `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_engine.py`

구현 내용:

- `codex_plan_request.md` 생성
- Claude plan review A/B 자동 발송
- `claude_plan_review_a/b.json` 저장
- 실패 시 HOLD 이유 자동 요약

완료 기준:

- 신규 auto task 1회 시작 후 plan review artifact가 자동 생성된다

### Step 4. coding -> verify -> final review 자동 루프 연결

목표:

- auto mode의 후반부를 닫는다

구현 파일 후보:

- `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_engine.py`
- `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_verify.py`
- `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`

구현 내용:

- code request dispatch
- verify dispatch
- verify 실패 시 `retry / hold` 분기
- final review dispatch
- final gate 정리

완료 기준:

- 자연어 auto task 1회가 `final decision` 단계까지 도달한다

### Step 5. Telegram 할 일 중심 UI 개편

목표:

- 사용자가 숫자 해석 없이 상황을 바로 이해하도록 한다

구현 파일 후보:

- `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`
- 필요 시 `C:\1POW\03_telegram_py` 아래 허용된 telegram 보조 파일

구현 내용:

- 숫자형 안내보다 `현재 상태 / 지금 하는 일 / 다음 할 일 / 막힌 이유 / 가능한 응답` 우선 표시

완료 기준:

- HOLD/blocked/final state에서 숫자보다 할 일이 먼저 보인다

## 7. 파일별 역할 상세 설명

### `C:\1POW\bot.py`

현재 역할:

- live Telegram ingress runtime copy
- office/coder 공용 main
- 현재 자연어 입력의 첫 도착 지점

이번 최종안에서 맡길 역할:

- coder 자연어 입력을 front_secretary draft 분기로 넘기는 실행 ingress
- 직접 수정 대상이 아니라, canonical 변경이 동기화된 결과물로 본다

### `C:\1POW\03_telegram_py\bot_runtime_profile.py`

현재 역할:

- office/coder runtime 분리
- token/runtime root/lock/pid 분리

이번 최종안에서 맡길 역할:

- ingress 안정성 유지
- telegram 쪽 canonical 운영 규칙 유지
- 자연어 코딩모드 본체는 여기 두지 않음

### `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`

현재 역할:

- OpenClaw state machine 정본
- next_action, summary, gate, artifact 관리

이번 최종안에서 맡길 역할:

- blocked 처리
- 자연어 draft 상태
- Telegram 상태 출력
- 신규 task/create/archive 판단

### `C:\1other\openclaw-front-secretary\tools\auto_work\start_coding_task.py`

현재 역할:

- start contract 등록
- task dir 생성
- task_context 생성
- coder Telegram 시작 보고
- auto면 plan request 생성

이번 최종안에서 맡길 역할:

- draft가 승인된 뒤 실제 task 등록을 수행하는 표준 entrypoint

### `C:\1other\openclaw-front-secretary\runtime\front_secretary\state.json`

현재 역할:

- live coder state 정본

이번 최종안에서 맡길 역할:

- blocked/done/archive/new task 상태를 명확히 분리하는 기준 파일

### `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_engine.py`

현재 역할:

- 자동작업 엔진 정본

이번 최종안에서 맡길 역할:

- plan review -> coding -> final review의 auto loop 수행

### `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_verify.py`

현재 역할:

- verify 실행

이번 최종안에서 맡길 역할:

- retry/hold 분기까지 포함한 verify 정책 엔진

## 8. 검증 완료 기준

자연어 코딩모드가 “됐다”고 말하려면 최소 아래가 통과해야 한다.

### 최소 end-to-end 기준

1. coder bot에 자연어 코딩 지시 1문장 입력
2. blocked task가 있어도 새 task draft가 생성됨
3. `1 시작` 선택 후 `start_contract.json` 생성
4. `codex_plan_request.md` 생성
5. auto mode면 `claude_plan_review_a/b.json` 생성
6. 그 다음 verify/final로 이어지거나, 실패 시 HOLD 이유가 자연어로 표시됨

### 운영 기준 추가

아래 2개는 반드시 만족해야 한다.

1. 자연어 1문장 -> 30초 내 draft 생성 + 확인 프롬프트 표시 + 승인 시 `start_contract.json` 생성
2. blocked task가 있어도 기존 task와 새 task가 섞이지 않음

### 시간 기준 세분화

운영 시간 기준은 아래처럼 고정한다.

1. 30초 내
   - draft 생성
   - 확인 프롬프트 표시
   - 승인 시 `start_contract.json` 생성
2. 2분 내
   - `codex_plan_request.md` 생성
3. 5분 내
   - `claude_plan_review_a.json`
   - `claude_plan_review_b.json`
   - 또는 rate/permission/timeout 이슈를 적은 HOLD 사유 표시

### target_repo 미확정 기준

자연어에서 repo가 불명확하면 아래 흐름이 떠야 한다.

- `대상 repo를 고르세요`
- `1. openclaw-front-secretary`
- `2. openclaw-auto-coding`
- `3. 직접 입력`

즉 repo 미확정은 실패가 아니라 선택 분기여야 한다.

### artifact gate 기준

아래 2개는 end-to-end 완료 판정의 강제 조건이다.

1. `RELEASE`
   - `full_verify.json`
   - `claude_final_review_a.json`
   - `claude_final_review_b.json`
2. `DONE`
   - `task_summary.json`
   - `verify_manifest.json`

없으면 stage 전환이 아니라 HOLD/대기 상태를 유지한다.

### Step 2 FAIL 기준

아래 둘 중 하나라도 어기면 Step 2는 즉시 FAIL로 본다.

1. `confirm_start_draft` 상태에서 어떤 경로로든 `start_contract.json`이 생성됨
2. TTL 만료 시 `폐기 + 안내 1회 + 동일 메시지 재처리` 3종이 동시에 충족되지 않음

### Decision Table

아래 표를 운영 기본 표로 쓴다.

| 현재 상태 | 입력 | 처리 |
| --- | --- | --- |
| `idle` | 코딩 키워드 포함 자연어 | draft 생성 + 확인 프롬프트 |
| `idle` | 질문형 일반 대화 | 일반 응답, task 생성 안 함 |
| `confirm_start_draft` | `1` | `start_contract.json` 생성 |
| `confirm_start_draft` | `2` | draft 폐기 |
| `confirm_start_draft` | TTL 초과 + 새 메시지 | draft 폐기 + 만료 안내 + 같은 메시지 재처리 |
| `confirm_start_draft` | 새 자연어 코딩 요청 | pending_draft overwrite + TTL 갱신 + 확인 프롬프트 재전송 |
| `confirm_start_draft` | 그 외 입력 | 상태 유지 + `1/2 또는 새 코딩 지시` 안내 |
| `blocked` | 명시적 이어가기 | 기존 task continue 분기 |
| `blocked` | 새 자연어 코딩 요청 | `continue vs replace` 1회 질문 |
| `blocked` + `replace` | `2` | 기존 task archived + 새 draft |
| `target_repo 불명확` | 숫자 선택 | repo 확정 후 start contract 진행 |
| `auto verify fail` | artifact 부족/timeout | HOLD 이유 요약 + 지금 할 일 표시 |

## 9. 현재 판정

현재 상태는 아래로 보는 게 맞다.

- Telegram office/coder 분리: `OK`
- coder bot 코딩 보고 분리: `OK`
- start contract 도입: `OK`
- task/artifact 구조: `OK`
- blocked task 정리: `OK`
- 자연어 코딩 draft 판정: `OK`
- 텔레그램 지시모드: `OK`
- start contract auto 연결: `PARTIAL`
- auto plan review 연결: `PARTIAL`
- coding/verify/final auto loop: `NOT YET`
- 할 일 중심 Telegram UI: `PARTIAL`

한 줄로 요약하면:

현재는 `OpenClaw 코딩모드의 입구, blocked 정리, 자연어 draft, 텔레그램 지시모드까지는 정리됐지만, start contract 이후 auto plan review와 verify/final loop를 닫는 마지막 단계가 아직 남아 있는 상태`다.

## 10. 최종 우선순위

이 순서는 바꾸지 않는다.

1. blocked task 정리
2. coder 자연어 입력 -> draft + 1회 확인
3. target_repo 미확정 분기
4. start contract 후 plan review 자동 연결
5. coding -> verify -> final review 자동 루프
6. Telegram 상태를 할 일 중심으로 정리

이 순서대로 가야 자연어 코딩모드가 실제 운영 가능한 상태로 닫힌다.
