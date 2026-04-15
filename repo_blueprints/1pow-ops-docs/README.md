# 1pow-ops-docs Blueprint

이 디렉토리는 `1POW` 공통 운영 문서 전용 Git 저장소의 권장 구조다.

목적:

- `START.md`, `CLAUDE.md`, `GPT.md`를 코드 저장소와 분리
- 집/사무실/서버에서 같은 문서 정본을 추적 가능하게 만듦
- `repo` 없는 프로젝트의 임시 문서 정본도 함께 수용

권장 트리:

```text
1pow-ops-docs/
  START.md
  CLAUDE.md
  GPT.md
  README.md
  docs/
    project-maps/
    projects/
    templates/
  automation/
    agent_harness/
```

이 저장소에 넣을 것:

- 공통 실행 규칙 문서
- 공통 플래너/리뷰어 템플릿
- 프로젝트 인덱스, 맵, 공통 템플릿
- `repo` 없는 프로젝트용 handover / handoff / 작업 규칙
- 향후 `spec_lint`, `context_pack`, `verify_runner` 관련 문서

이 저장소에 넣지 말 것:

- 외부 독립 repo 전용 문서
- 외부 독립 repo 코드
- 프로젝트별 비공통 handover
- 고객 데이터, 시크릿, 대용량 산출물

현재 서버에 있는 공통 문서는 Git 정본으로 이관 후,
서버에는 배포 사본으로만 둔다.
