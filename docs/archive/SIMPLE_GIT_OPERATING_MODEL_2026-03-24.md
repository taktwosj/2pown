# 1POW Simple Git Operating Model

최종 정리일: 2026-03-24

## 한 줄 원칙

- `C:\1POW_META`는 문서 정본과 프로젝트 식별 기준 repo다.
- `C:\1POW`는 프로젝트 clone과 작업본이 있는 workspace다.
- 프로젝트 코드는 각 프로젝트 authority를 따른다.
- `Cafe24`는 실행, 검증, 배포 환경이다.
- 사무실 PC는 실행 노드다.

## 지금 기준

- 공통 작업 규칙 정본: `1pow-meta`
- 프로젝트 식별 정본: `meta/project_registry.json`
- `repo`가 없는 프로젝트 문서 정본: `docs/projects/<project-id>/`
- `repo`가 있는 프로젝트 문서 정본: 해당 repo 문서
- 서버 markdown은 canonical fallback이 아니다

## 무엇을 어디에 두는가

`C:\1POW_META`
- `README.md`
- `CLAUDE.md`
- `GPT.md`
- `docs/START.md`
- `meta/project_registry.json`
- `docs/projects/`
- `tools/1pow_meta_status.py`

`C:\1POW`
- 프로젝트 clone
- 승인된 working copy
- 런타임 복사본과 운영 보조 파일

## 사용 순서

1. `C:\1POW_META`에서 `origin` 기준으로 상태를 검증한다.
2. `meta/project_registry.json`으로 프로젝트를 식별한다.
3. `doc_canonical`을 읽는다.
4. 승인된 workspace 경로로 이동해 작업한다.
5. 가능한 로컬 검증을 먼저 한다.
6. `Cafe24`에서 runtime / deploy 확인을 한다.

## 기억할 것

- 시작은 항상 `C:\1POW_META`
- 작업은 해당 프로젝트의 `C:\1POW\...` clone에서만
- 서버 문서는 정본 fallback이 아니다
- 사무실 PC는 정본이 아니라 실행 노드다
