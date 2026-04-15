# Project Doc Matrix

이 파일은 공통 운영 문서와 프로젝트 전용 문서를 분리해서 본다.

## 공통 운영 문서

아래 문서는 `1pow-ops-docs`로 가는 것이 맞다.

- `START.md`
- `CLAUDE.md`
- `GPT.md`

## 외부 독립 Repo 전용 문서

공통 문서가 아니라 특정 외부 repo에만 종속된 온보딩/워크로그/핸드오프 문서는 그 repo에 남는 것이 맞다.

## repo 없는 프로젝트 문서

아직 repo가 없는 프로젝트 문서는 `2POW/docs/projects/<project-id>/`에 둔다.

예시:

- `docs/projects/3-bankly/`
- `docs/projects/6-telegram-bot/`
- `docs/projects/11-auto-work/`

## 프로젝트 전용 handover

아래 문서는 각 프로젝트 경계에 따라 별도 저장소 또는 `docs/projects/<project-id>/`에 둔다.

- `BANKLY_HANDOVER.md`
- `TELEGRAM_HANDOVER.md`
- `IVWITH_HANDOVER.md`
- `JOGYEON_HANDOVER.md`

## 기준 원칙

1. 여러 프로젝트가 같이 쓰는 문서는 공통 문서 Git
2. 한 프로젝트 내부 구조만 다루는 문서는 해당 프로젝트 Git
3. `repo` 없는 프로젝트 문서는 `docs/projects/<project-id>/`가 정본
4. 서버 문서는 배포 사본이지 정본이 아님
5. 로컬 문서는 정본이 아니라 작업복사본
