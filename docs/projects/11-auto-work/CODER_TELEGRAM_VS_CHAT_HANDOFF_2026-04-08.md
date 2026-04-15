# ofcgptcoder_bot Telegram↔VS Codex Relay 인수인계서

작성일: `2026-04-08`
상태: `HANDOFF_RESET`
판정: `LIVE_SMOKE_FAIL`

## 0. 목적

목표는 1개다.

- `ofcgptcoder_bot = Telegram↔VS Codex 대화 릴레이`

원하는 UX는 3줄이다.

1. Telegram 평문 입력
2. VS에 붙은 Codex 세션으로 전달
3. Codex 답변 1건만 Telegram으로 반환

## 1. 방향 리셋

이전 접근은 너무 무거웠다.

- OpenClaw workflow
- 단계 카드
- 자동 검수
- worker tick
- state report
- deploy/final review guard

이 기능들이 coder bot 목표를 흐렸다.

이제 coder bot 범위는 최소화한다.

- `bind`
- `unbind`
- `status`
- `plain relay`

그 외는 coder bot 범위에서 제거하거나 완전 비활성화한다.

## 2. 최종 정책

### 2-1. 평문 정책

- 바인딩 후 평문은 전부 Codex relay
- 예:
  - `상태`
  - `다음단계 진행해줘`
  - `이 함수 왜 이래`
  - `고쳐줘`
  - `테스트 돌려봐`

### 2-2. 로컬 명령 정책

최소만 남긴다.

- `.bind` 또는 bind 계열
- `.unbind` 또는 off 계열
- `.상태`

다음은 coder bot에서 빼는 쪽이 기본 방침이다.

- `.다음`
- `.검수`
- workflow 숫자 선택
- deploy/final review 유도

### 2-3. 응답 정책

- relay 성공: Codex 답변 1건만 전송
- relay 실패: 에러 1건만 전송
- 금지:
  - `[OpenClaw]` 카드
  - 상태카드
  - 단계카드
  - 자동 검수 안내
  - worker tick 기반 자동 메시지

## 3. 현재 상태 요약

### 3-1. 작업 경로

- 주 수정 대상:
  - `C:\1other\openclaw-front-secretary`
- 핵심 파일:
  - `C:\1other\openclaw-front-secretary\tools\auto_work\front_secretary.py`
  - `C:\1other\openclaw-front-secretary\tests\test_front_secretary_auto_work.py`
- 보조 확인:
  - `C:\1other\openclaw-auto-coding\openclaw_auto_coding\auto_work_bundles.py`
- 정본 문서:
  - `C:\1POW\docs\projects\11-auto-work\CODER_TELEGRAM_VS_CHAT_HANDOFF_2026-04-08.md`

### 3-2. 이미 한 것

다음은 코드상 반영됨.

- codex_bound relay-first 조건 보강
- stale next_action / pending prompt 회피
- binding wobble prune 보호
- formal-task stale-meta guard 확장
- inbound duplicate 처리 보호
- worker auto-report 일부 억제
- 관련 unittest 다수 추가

테스트는 로컬에서 통과했다.

- `python3 -m unittest tests.test_front_secretary_auto_work`
- 최근 결과: `114 tests OK`

중요:

- 로컬 green은 신뢰 보조 자료일 뿐이다.
- 최종 판정은 live smoke 기준이다.

## 4. live smoke 결과

실운영 기준 아직 실패다.

### 4-1. 실제 관측 실패

1. plain `상태`
   - 기대: Codex relay
   - 실제: 로컬 상태성 응답
   - 판정: `FAIL`

2. `.상태`
   - 기대: 필요 시 로컬 status 1건
   - 실제: 뒤에 `[OpenClaw] 코딩 진행` 카드 추가
   - 판정: `FAIL`

3. plain `다음단계 진행해줘`
   - 기대: Codex relay
   - 실제: workflow/control처럼 처리됨
   - 추가로 중복 반응 정황 존재
   - 판정: `FAIL`

4. `.다음`
   - 로컬 차단은 됨
   - 하지만 새 목표에서는 아예 coder bot 범위에서 제거/비활성화 대상

5. `.검수`
   - 로컬 차단은 됨
   - 하지만 새 목표에서는 아예 coder bot 범위에서 제거/비활성화 대상

6. plain `이 메시지는 릴레이 실패 확인용 일반 평문입니다.`
   - 실제: `코덱스답변: 일반 평문 수신됨.`
   - 판정: `일반 relay 자체는 일부 성공`

## 5. 핵심 원인 가설

### 5-1. relay 대상 세션이 틀릴 가능성 높음

live state에서 확인된 사실:

- `active_task.status = codex_bound`
- 그런데 `active_task.codex_binding`은 사실상 비어 있음
- `thread-bindings-coder.json`도 비어 있었음
- `last_codex_relay`는 실제 VS child binding이 아니라 parent coder Telegram session 쪽을 사용한 정황이 있었음

의미:

- 현재 relay가 `VS에 붙은 Codex child session`으로 확정 전송되지 않을 수 있다.
- fallback parent session relay는 원래 목표와 다르다.

### 5-2. inbound 처리 경로가 1개가 아닐 가능성 높음

live monitor에서 plain `다음단계 진행해줘` 처리 중 아래 정황이 있었다.

- 한 번은 `last_delivery.reason = apply`
- 이후 또 `codex_bound_relay`

의미:

- 현재 watcher queue 경로 외에 legacy `apply` 또는 동등 경로가 같은 입력을 다시 먹고 있을 수 있다.
- 즉 동일 inbound가 이중 처리될 수 있다.

### 5-3. OpenClaw state/report 계층이 coder relay UX를 계속 오염시킴

의미:

- coder bot에 남아 있는 자동 상태 보고와 workflow 해석이 plain relay 목표를 계속 깨뜨린다.

## 6. 다음 작업자 지시

### 6-1. 목표를 다시 고정

다음 문장만 기준으로 작업한다.

- `ofcgptcoder_bot은 자동작업 봇이 아니라 Telegram↔VS Codex 대화 릴레이다.`

### 6-2. coder bot에서 제거/비활성화할 것

우선순위 높음.

- workflow 단계 진행
- `.다음`
- `.검수`
- 숫자 메뉴
- plan/final review/deploy 유도
- worker tick 자동 진행
- state report 자동 전송
- `[OpenClaw]` 카드 전송

### 6-3. coder bot에 남길 것

- bind
- unbind
- status
- plain relay

### 6-4. 기술 작업 순서

1. 현재 Telegram inbound를 실제로 소비하는 경로를 전부 찾는다.
   - `telegram-route-inbound`
   - `telegram-worker-tick`
   - `telegram-apply`
   - `apply`
   - Windows 쪽 병행 watcher / runner / scheduled path
2. 같은 inbound가 두 번 처리되는 경로를 끊는다.
3. relay 대상 세션을 `VS child Codex binding`으로 강제한다.
   - fallback parent coder session 사용 금지 검토
   - binding state / thread-binding persistence 재점검
4. coder bot bound mode에서는 workflow 해석을 완전히 끈다.
   - plain text intent 분류 자체를 relay 우선으로 단순화
5. coder bot bound mode에서는 자동 보고를 완전히 끈다.
   - route 후 state report 금지
   - worker dispatched 후 report 금지
   - relay error 후에도 카드 금지
6. `.다음`, `.검수`는 유지할 이유가 없으면 제거 또는 hard-disabled 처리한다.

## 7. 먼저 읽을 함수/파일

- `should_route_telegram_inbound_text()`
- `handle_telegram_inbound_text()`
- `handle_telegram_input()`
- `apply_text_command()`
- `dispatch_next_action()`
- `normalize_telegram_control_text()`
- `normalize_progress_control_text()`
- `should_auto_report_telegram()`
- `send_state_report_to_telegram()`
- `relay_bound_codex_followup()`
- `infer_latest_coder_telegram_session()`
- `run_openclaw_agent_session()`
- `main()`의
  - `telegram-route-inbound`
  - `telegram-worker-tick`
  - `telegram-apply`
  - `apply`
- binding 관련:
  - `prune_stale_inbound_binding_for_target()`
  - state migrate / `vs_mode` 유도 함수
- 파일:
  - `runtime/front_secretary/state.json`
  - `runtime/front_secretary/thread-bindings-coder.json`
  - `/home/taktwo/.openclaw/agents/coder/sessions/sessions.json`

## 8. live monitor 참고 사실

이전 작업에서 아래를 확인했다.

- watcher는 tmux session `front_secretary_telegram_watch`로 돌고 있었음
- monitor exec session `43850`에서 `state.json` 변화 추적함
- `last_delivery.reason = apply` 정황이 실제로 보였음
- plain generic message는 `codex_bound_relay`로 성공했음
- 따라서 문제는 relay 기능 부재가 아니라 `경로 혼선 + 잘못된 세션/자동알림 누수` 쪽일 가능성이 높음

## 9. 검증 기준

### 9-1. 로컬 테스트

기존 unittest는 계속 돌리되, 통과해도 완료로 보지 않는다.

최소:

```bash
python3 -m py_compile /mnt/c/1other/openclaw-front-secretary/tools/auto_work/front_secretary.py
python3 -m py_compile /mnt/c/1other/openclaw-front-secretary/tests/test_front_secretary_auto_work.py
python3 -m unittest tests.test_front_secretary_auto_work
```

### 9-2. 최종 판정은 live smoke만 본다

순서 고정:

1. `상태`
2. `.상태`
3. `다음단계 진행해줘`
4. `.bind` 또는 실제 bind 확인 명령
5. 일반 평문 1건
6. relay failure 유도 1건

각 케이스마다 기록:

- Telegram 실제 수신 메시지 개수
- `last_inbound_sync`
- `last_delivery`
- `last_codex_relay`

실패 조건:

- `[OpenClaw]` 카드 1건이라도 끼면 실패
- 같은 입력에 메시지 2건 이상 오면 실패
- plain text가 workflow/control/status로 해석되면 실패
- relay가 VS child Codex가 아니라 parent coder session fallback이면 실패

## 10. 완료 조건

아래 4개가 동시에 만족돼야 완료다.

1. plain `상태`가 Codex로 간다.
2. plain `다음단계 진행해줘`가 Codex로 간다.
3. `.상태`에도 추가 카드가 안 붙는다.
4. 일반 평문 1건당 답변 1건만 온다.

## 11. 보고 형식

최종 보고는 3개만 적는다.

1. 끈 기능
2. 남긴 기능
3. live smoke 실제 수신 결과

한 줄 결론은 이것만 쓰면 된다.

- `coder bot를 OpenClaw에서 떼어내고 Telegram↔VS Codex relay 전용으로 단순화했다.`
