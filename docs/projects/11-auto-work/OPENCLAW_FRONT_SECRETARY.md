# OpenClaw Front Secretary

프로젝트 번호: `11`  
프로젝트명: `coding`

## 목적

이 문서는 OpenClaw를 `앞단 비서 + 오케스트레이터`로 쓰기 위한 최소 제어면을 설명한다.

핵심 개념:

- 사용자는 OpenClaw에게만 자연어로 말한다.
- OpenClaw는 내부적으로 Codex / Claude / VS 상태를 조율한다.
- `front_secretary.py`는 짧은 자연어 명령을 상태 전이와 다음 액션으로 바꾼다.

이 도구는 아직 GUI 클릭기나 VS 탭 자동배치 자체를 수행하지 않는다.  
현재 버전은 `state.json v2 기반 조회/상태 저장 + 다음 행동 제안`까지를 canonical로 둔다.

## canonical

- 코드 정본: `C:\1POW\tools\auto_work\front_secretary.py`
- 실행 래퍼:
  - `C:\1POW\tools\auto_work\RUN_FRONT_SECRETARY.ps1`
  - `C:\1POW\tools\auto_work\RUN_FRONT_SECRETARY.cmd`

## 상태 단계

- `IDLE`
- `PREPARE`
- `PLAN_DRAFT`
- `PLAN_REVIEW`
- `PLAN_REVISION`
- `WAIT_USER_PLAN_CONFIRM`
- `CODING`
- `WAIT_USER_APPROVAL`
- `FINAL_REVIEW`
- `FIXUP`
- `DONE`
- `BLOCKED`

사용자 노출 단계는 더 단순하게 요약한다.

- `READY`
- `PLANNING`
- `WAITING`
- `CODING`
- `REVIEWING`
- `DONE`
- `BLOCKED`

## 자연어 예시

아래처럼 짧게 보내면 된다.

- `vs 실행하자`
- `코딩계획 잡자`
- `클로드한테 물어봐`
- `코딩해`
- `지금 뭐하는 중이야`
- `코덱스 채팅목록 보여줘`
- `승인`
- `중단해`

## 기본 사용

PowerShell:

```powershell
cd C:\1POW
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 reset
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 apply --text "vs 실행하자"
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 apply --text "코딩계획 잡자"
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 status
```

JSON 출력:

```powershell
cd C:\1POW
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 apply --text "클로드한테 물어봐" --json
```

## 상태 파일

기본 상태 파일:

- `C:\1POW\runtime\front_secretary\state.json`

여기에 아래 정보가 쌓인다.

- `heartbeat`
- `current_stage`
- `stage_entered_at`
- `user_stage`
- `active_task`
- `observed.codex_threads`
- `observed.claude_tabs`
- `observed.pending_approvals`
- `last_review_result`
- `blockers`
- `history`

중요 원칙:

1. `state.json`이 없으면 조회 명령은 차단한다.
2. `state.json`만으로 실제 GUI 상태를 보장하지 않는다.
3. `last_observed_at`이 오래됐으면 오래된 상태일 수 있다고 경고한다.

## writer 분리

이 파일은 한 주체가 다 쓰지 않는다.

- `apply/reset`:
  - OpenClaw operator 레이어가 쓴다
  - 단계 전이, 요약, 다음 행동, history 담당
- `observe/context`:
  - GUI/브리지/세션 수집기가 쓴다
  - Codex 채팅목록, Claude 탭목록, 승인대기, observed timestamp 담당
- `review`:
  - 검수 수집기가 쓴다
  - 마지막 검수결과와 blocker 담당

즉 OpenClaw가 자기 혼자 실제 GUI 상태를 상상해서 쓰는 구조를 피한다.

## observe 업데이트

나중에 GUI/브리지 계층이 붙으면 현재 열려 있는 탭 제목이나 채팅명을 아래처럼 주입할 수 있다.

```powershell
cd C:\1POW
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 observe `
  --codex-thread "Confirm system status" `
  --codex-thread "Main coding thread" `
  --claude-tab "Confirm system status" `
  --claude-tab "Code review and confirmation"
```

이렇게 넣어 두면 사용자가 `코덱스 채팅목록 보여줘`라고 물었을 때 OpenClaw가 상태 파일 기준으로 답하기 쉬워진다.

검수 결과 기록:

```powershell
cd C:\1POW
.\tools\auto_work\RUN_FRONT_SECRETARY.ps1 review `
  --reviewer claude_a `
  --verdict PASS_WITH_NOTES `
  --note "계획은 대체로 적절함" `
  --note "state 수집 stale 경고는 필요"
```

## 현재 범위와 다음 단계

현재 범위:

1. 자연어 명령 파싱
2. 상태 전이
3. 상태파일 v2 저장
4. 조회 하드 게이트
5. writer 분리 기반 observe/review 갱신

다음 단계:

1. `prepare_vscode_desk.ps1/.ahk`와 연결
2. Claude/Codex 실제 탭/스레드 상태 수집기 구현
3. 권한 요청 팝업을 `pending_approvals` writer로 연결
4. OpenClaw agent prompt에서 `front_secretary.py`를 직접 호출하도록 묶기
5. 조회 전용 3개 명령을 먼저 안정화한 뒤 실행 명령을 확장
