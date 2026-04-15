# 자동작업 인수인계서

프로젝트 번호: `11`  
프로젝트명: `자동작업`  
상태: `DEV`  
최종 갱신: `2026-04-16`

이 문서는 `C:\2POW\docs\projects\11-auto-work\` 아래의 canonical handover다.  
서버 `/srv/workspace/docs/AUTO_WORK_HANDOVER.md`는 migration source / deploy copy로만 취급한다.

## 1. 프로젝트 정의

`자동작업`은 1POW에서 쓰는 GPT/Codex/Claude 협업 루프를 자동화한 운영 프로젝트다.

핵심 목표는 아래 4단계를 무한루프 없이 최대 4단계로 고정해서 반복 실행하는 것이다.

1. GPT/Codex가 작업지시서(`Execution Spec`) 작성
2. Claude가 작업 실행
3. GPT/Codex가 검수
4. 필요 시 Claude가 후속작업 1회 실행

즉 이 프로젝트는 새 서비스라기보다, 기존 1POW 작업 방식을 자동으로 굴리는 오케스트레이터다.

## 2. 정본 문서와 authority

항상 아래 순서로 읽는다.

1. 공통 작업 문서 정본
   - `C:\2POW\README.md`
   - `C:\2POW\CLAUDE.md`
   - `C:\2POW\GPT.md`
   - `C:\2POW\docs\START.md`
2. 자동작업 프로젝트 정본
   - `C:\2POW\docs\projects\11-auto-work\AUTO_WORK_HANDOVER.md`

중요 원칙:

- 프로젝트 식별은 `meta/project_registry.json`을 따른다.
- 공통 규칙은 `C:\2POW` 공통 문서가 정본이다.
- 서버 `/srv/workspace/docs/AUTO_WORK_HANDOVER.md`는 정본이 아니라 migration source / deploy copy다.
- 서버는 runtime 확인과 배포, 호환 audit용으로만 사용한다.

## 3. 실제 코드 구성

이 프로젝트는 한 폴더에만 있지 않고 아래 3축으로 나뉜다.

### A. 오케스트레이터 본체

- external agent loop runtime working copy
- `tools/agent_loop.py`
- `tools/RUN_AGENT_LOOP.ps1`
- `tools/RUN_AGENT_LOOP.cmd`
- `tools/AGENT_LOOP.md`

역할:

- `--spec` 모드: 완성된 작업지시서로 바로 실행
- `--intent` 모드: 자연어 의도에서 Codex가 먼저 작업지시서 생성 후 실행
- Claude 실행 -> Codex 검수 -> Claude fixup 1회까지 자동 진행

### B. 텔레그램 봇 연결

운영 파일은 root `C:\2POW\bot.py`와 `03_telegram_py` helper/wrapper 계열에 걸쳐 있다.

역할:

- `junjunofc_bot` 메뉴 운영
- `94`로 `junofccld` 채널봇 재시작
- `000`으로 정본 동기화 후 로컬 봇 재시작

### C. Claude 답장 릴레이

운영 파일은 `claude_telegram_reply_relay.py`, `03_telegram_py/claude_telegram_reply_relay.py` 계열에 걸쳐 있다.

역할:

- Claude 채널 플러그인의 outbound가 불안정할 때 답장을 텔레그램으로 직접 릴레이
- `~/.claude/projects/**/*.jsonl`의 assistant 답변을 읽어 allowlist 채팅으로 전달

## 4. 텔레그램 봇 역할 분리

### 1) `@junofccld_bot`

역할:

- Claude 채널봇 전용
- 사용자가 직접 질문/지시를 보내는 대상
- Claude 대화/응답 전용

### 2) `junjunofc_bot`

역할:

- 사무실 메뉴/운영 봇
- 고객관리/CRM 메뉴 운영
- 자동작업 알림 수신 대상
- 자동작업 본체가 아니라 재시작/운영 보조 역할

현재 원칙:

- Claude/Codex 대화는 `@junofccld_bot`으로 보낸다.
- 작업 알림은 `junjunofc_bot`으로 보낸다.
- `junjunofc_bot`은 `94. Claude채널봇 재시작` 같은 운영 메뉴도 담당한다.

## 5. 자동 루프 규칙

### 단계 한도

한 작업은 최대 4단계까지만 진행한다.

1. GPT/Codex가 초기 작업지시서 작성
2. Claude 실행
3. GPT/Codex 검수 및 Fixup Spec 작성
4. Claude 후속작업 실행

이 4단계 이후에도 미해결이면 같은 작업으로 무한 반복하지 않고 새 작업으로 분리한다.

### 분리 원칙

- 플래너: GPT/Codex
- 실행자: Claude
- 검수자: GPT/Codex

즉 Claude가 자기 자신을 최종 판정하지 않는다.

### 결과물

실행 산출물은 external agent loop runtime의 `.agent_runs/<timestamp_uuid>/` 아래에 남는다.

중요 파일:

- `intent.txt`
- `codex_plan_prompt.txt`
- `codex_plan_payload.txt`
- `execution_spec.md`
- `claude_initial_payload.json`
- `codex_review_payload.json`
- `fixup_spec.md`
- `claude_fixup_payload.json`
- `final_summary.json`
- `loop_status.json`
- `loop_status.txt`

## 6. 실행 방법

### A. 기존 `--spec` 방식

```powershell
cd <agent-loop working copy>
.\tools\RUN_AGENT_LOOP.ps1 -Spec C:\path\to\task.md -NotifyTelegram
```

백그라운드:

```powershell
cd <agent-loop working copy>
.\tools\RUN_AGENT_LOOP.ps1 -Spec C:\path\to\task.md -NotifyTelegram -Background
```

### B. 자연어 `--intent` 방식

```powershell
cd <agent-loop working copy>
.\tools\RUN_AGENT_LOOP.ps1 -Intent "원하는 작업 내용" -NotifyTelegram
```

백그라운드:

```powershell
cd <agent-loop working copy>
.\tools\RUN_AGENT_LOOP.ps1 -Intent "원하는 작업 내용" -NotifyTelegram -Background
```

### C. 직접 Python 실행

```powershell
cd <agent-loop working copy>
py -3 tools\agent_loop.py --intent "원하는 작업 내용" --workspace <agent-loop working copy> --notify-telegram
```

## 7. 현재 모델 기본값

현재 기준 권장 분리는 아래와 같다.

- Planner: `gpt-5.4`
- Review: `gpt-5.4-mini`
- Claude Executor: `sonnet`

실사용 Claude UI에서는 `Sonnet 4.6 with high effort`로 보일 수 있다.  
CLI 쪽은 `--model sonnet` 기준으로 유지한다.

## 8. 텔레그램 알림 규칙

알림 머리글은 항상 아래 형식을 유지한다.

```text
GPT
설명문...
```

단계 변화 기반으로만 보낸다.

- 새 작업 감지
- 작업지시서 생성 시작
- 작업 시작
- 작업 진행중(단계별 1회)
- 문제 발생
- 작업 완료(미검증)
- 검증 시작
- 검증 완료
- 후속작업 시작
- 후속작업 완료(미검증)
- 최종 완료

중요:

- 검증 전 단계는 반드시 `(미검증)` 표시
- review PASS 전에는 완료처럼 보이게 쓰지 않는다
- 자동작업 알림은 `bot_token.txt` 기준으로 `junjunofc_bot`에 보낸다
- `agent_loop.py`는 더 이상 `agent_bot_token.txt`를 알림 토큰 fallback으로 사용하지 않는다

## 9. `94`와 `000`의 의미

### `94. Claude채널봇 재시작`

현재는 아래 2개를 같이 재시작한다.

1. `junofccld` Claude 채널 세션
2. `claude_telegram_reply_relay.py`

즉 단순히 Claude만 재시작하는 것이 아니라 답장 전달 경로 전체를 재시작한다.

### `000. 봇 자동 업데이트`

최소 동기화 대상은 아래를 포함해야 한다.

- `C:\2POW\bot.py`
- `03_telegram_py/run_office_bot.py`
- `03_telegram_py/bot_runtime_profile.py`
- `claude_telegram_reply_relay.py`
- `03_telegram_py/claude_telegram_reply_relay.py`

중요:

- `000` 서버 정본이 구버전이면 로컬 수정이 다시 덮일 수 있다
- 따라서 `000` 관련 수정은 항상 runtime 대상까지 같이 확인한다

## 10. 현재 확인된 이슈와 해결 메모

### 1) Claude 채널봇 입력은 되는데 답장이 안 오는 문제

확인된 사실:

- 텔레그램 입력은 Claude 세션에 들어감
- Claude는 실제 답변을 생성함
- 하지만 채널 플러그인 outbound가 불안정하게 먹통이 되는 경우가 있었음

대응:

- `claude_telegram_reply_relay.py` 추가
- Claude 세션 로그를 읽어서 답변을 허용된 채팅으로 직접 재전송

### 2) 한글 사용자 경로 때문에 `94` 재시작이 깨지던 문제

대응:

- 직접 `claude.cmd` 대신 PowerShell -> `claude.ps1` 경로 사용
- 신뢰된 작업 경로 기준으로 세션을 고정

### 3) 최신 run이 아닌 예전 run 알림이 섞이던 문제

대응 방향:

- run id 기준으로 최신 run만 유효하다는 표시 유지
- 필요하면 이후 미종료 run 차단 로직 추가

### 4) 자동작업 알림이 Claude 채널봇으로 가던 혼선

대응:

- 자동작업 알림은 `junjunofc_bot`으로 고정
- Claude 대화/응답은 `@junofccld_bot`으로 분리
- `agent_loop.py` 알림 토큰 우선순위는 `bot_token.txt` 기준으로 정리

## 11. 수정 시 체크리스트

자동작업 프로젝트를 만질 때는 아래를 같이 본다.

1. 문서
   - `C:\2POW\README.md`
   - `C:\2POW\CLAUDE.md`
   - `C:\2POW\GPT.md`
   - `C:\2POW\docs\START.md`
   - `C:\2POW\docs\projects\11-auto-work\AUTO_WORK_HANDOVER.md`
2. 실행기
   - `tools/agent_loop.py`
   - `tools/RUN_AGENT_LOOP.ps1`
   - `tools/RUN_AGENT_LOOP.cmd`
3. 텔레그램 운영
   - `C:\2POW\bot.py`
   - `03_telegram_py/run_office_bot.py`
   - `03_telegram_py/bot_runtime_profile.py`
   - `claude_telegram_reply_relay.py`
4. 검증
   - `python3 -m py_compile`
   - 실제 `.agent_runs/.../final_summary.json`
   - 텔레그램 알림 형식
   - `94`, `000` 동작 여부

## 12. 다음 작업 후보

1. `--intent` 품질 안정화
   - planner prompt를 더 짧고 견고하게 정리
2. 최신 run만 유효 표시 강화
   - 텔레그램 알림에서 이전 run 잡음 줄이기
3. 텔레그램 입력 브리지 고도화
   - 사용자가 `작업지시서 받아와 + 내용`을 보내면 자동으로 `--intent` 실행
4. 서버 copy 정리
   - `/srv/workspace/docs/AUTO_WORK_HANDOVER.md`를 호환용 스텁으로 줄일지, 완전 제거할지 승인 작업으로 분리

## 13. 한 줄 요약

`자동작업`은 1POW에서 쓰는 GPT 작업지시 -> Claude 실행 -> GPT 검수 -> Claude fixup 1회 루프를 자동화한 운영 프로젝트이며, 현재 canonical 문서는 `C:\2POW\docs\projects\11-auto-work\` 아래에 둔다.
