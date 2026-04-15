# HARNESS MODE

Harness Mode는 Planner / Builder / Evaluator 3-role 루프로 작업을 스프린트 단위로 수행하는 방식이다.

## Trigger phrases
- 하네스 모드 / harness mode
- Planner/Builder/Evaluator / 플래너/빌더/이밸
- PBE 루프 / 스프린트 단위로 / 하네스 방식

## Core behavior
1. 대규모 코딩 전에 하네스 문서를 준비한다.
2. `docs/codex/<project-id>-harness/` 존재 여부를 확인한다.
3. 없으면 `docs/codex/harness-template/`로 초기화한다.
4. 활성화 후에는 한 번에 1 sprint만 수행한다.

## Local-first rule
`RELEASE` 전에는 아래를 금지한다.
1. Cafe24 업로드/배포/런타임 반영
2. `origin` push
3. `main` merge
4. local commit

## Approval gate
매 sprint 종료 시 `STATUS REPORT`를 출력하고 정지한다.
사용자 명령으로만 다음 동작을 수행한다.
- `CONTINUE`: 다음 sprint 1회
- `HOLD`: 대기
- `REPLAN`: 문서 재계획만
- `RELEASE`: release sprint 실행
- `STOP`: Harness Mode 종료

## Release Sprint order
1. active harness plan/checklist 기반 전체 QA 재실행
2. `Documentation.md` 릴리즈/검증 노트 갱신
3. 로컬 릴리즈 준비 상태 정리
4. 허용된 non-FTP 경로로 배포
5. 대상 런타임 검증
6. 통과 후에만 push/PR/merge

## Non-negotiables
- FTP write는 항상 금지
- API contract/authority/permission/deploy pipeline 변경은 명시 승인 없이는 금지
