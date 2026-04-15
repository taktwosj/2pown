# Git 분류 상태 보고

작성일: 2026-04-09  
대상: `C:\1POW`, `C:\1POW_META`, `C:\1other`, `C:\senior`, `C:\헬스유튜브`

## 결론

지금 상태에서 바로 "폴더별로 깔끔하게 분류해서 전부 push" 하려면, 먼저 remote 설계를 바로잡아야 한다.

- `1POW`와 `1POW_META`는 현재 서로 다른 폴더인데도 같은 GitHub remote를 가리킨다.
- `1other`는 상위 폴더 하나가 아니라, 하위의 독립 repo 3개로 분류하는 것이 맞다.
- `senior`, `헬스유튜브`는 현재 확인된 경로에 존재하지 않는다.

즉 지금 당장 안전하게 말할 수 있는 분류는 아래와 같다.

## 1. 이미 git repo인 폴더

### `C:\1POW`

- git repo: 예
- 현재 remote:
  - `origin = https://github.com/taktwosj/1pow-meta.git`
- 현재 상태:
  - `main...origin/main`
  - 수정 파일과 미추적 파일 다수 존재

판단:

- repo 자체는 이미 존재
- 하지만 remote 이름상 `1POW_META`와 분리되지 않음
- 지금처럼 같은 remote를 공유하면 "1POW 코드 workspace"와 "1POW_META control-plane" 분리가 무너짐

### `C:\1POW_META`

- git repo: 예
- 현재 remote:
  - `origin = https://github.com/taktwosj/1pow-meta.git`
- 현재 상태:
  - `main...origin/main [ahead 1, behind 3]`
  - 수정 파일 다수 존재

판단:

- repo 자체는 이미 존재
- remote는 `1POW_META` 용도로 자연스럽지만,
- 문제는 `C:\1POW`도 같은 remote를 보고 있다는 점
- 게다가 현재 branch가 `ahead 1, behind 3`라서 바로 push하면 충돌/혼합 위험이 큼

## 2. `1other`는 상위 폴더가 아니라 하위 repo 3개로 분류

### `C:\1other`

- 상위 폴더 자체는 git repo 아님
- 하위 독립 repo:
  - `C:\1other\codex-telegram-relay`
  - `C:\1other\openclaw-auto-coding`
  - `C:\1other\openclaw-front-secretary`

### `C:\1other\codex-telegram-relay`

- git repo: 예
- 현재 remote: 없음
- 현재 상태:
  - `main`
  - 수정 파일 존재

### `C:\1other\openclaw-auto-coding`

- git repo: 예
- 현재 remote: 없음
- 현재 상태:
  - `main`

### `C:\1other\openclaw-front-secretary`

- git repo: 예
- 현재 remote: 없음
- 현재 상태:
  - `main`

판단:

- `1other`는 통으로 올리는 게 아니라, 위 3개를 각각 독립 GitHub repo로 만드는 게 맞다
- 현재는 remote가 없어서 로컬 repo 상태만 존재

## 3. 현재 경로에서 확인되지 않은 폴더

### `C:\senior`

- 현재 경로 존재 여부: 없음

### `C:\헬스유튜브`

- 현재 경로 존재 여부: 없음

판단:

- 실제 폴더명이 다르거나 다른 드라이브/하위 경로에 있을 가능성이 높음
- 현재 확인된 경로 기준으로는 업로드 작업을 진행할 수 없음

## 4. 지금 바로 push하면 안 되는 이유

### High: `1POW`와 `1POW_META`가 같은 remote를 사용 중

- `C:\1POW -> https://github.com/taktwosj/1pow-meta.git`
- `C:\1POW_META -> https://github.com/taktwosj/1pow-meta.git`

이 구조에서는 "폴더별 분류 업로드"가 아니라, 서로 다른 작업영역이 같은 원격으로 섞이는 상태다.

### High: `1POW_META`는 branch가 diverged 상태

- 현재 `ahead 1, behind 3`

즉 pull/rebase/merge 정리 없이 바로 push하면 충돌 또는 의도치 않은 혼합 가능성이 높다.

### Medium: `1other` 3개는 remote가 아직 없음

- local repo는 있으나, 어디로 push할지 원격 저장소가 없다.

## 5. 권장 분류

### A. `1POW`

- 용도: 실행 workspace
- 권장: `1POW` 전용 remote로 분리

### B. `1POW_META`

- 용도: 규칙/문서/control-plane 정본
- 권장: 현재 `1pow-meta` remote는 여기만 사용

### C. `1other`

- 상위 폴더 자체는 remote 대상 아님
- 아래 3개를 각각 별도 remote로 분리
  - `codex-telegram-relay`
  - `openclaw-auto-coding`
  - `openclaw-front-secretary`

### D. `senior`, `헬스유튜브`

- 실제 경로 확인 후 별도 repo 여부 판단

## 6. 다음 작업 순서

1. `1POW`와 `1POW_META`의 remote를 분리한다.
2. `1POW_META`의 `ahead/behind` 상태를 먼저 정리한다.
3. `1other` 하위 3개 repo에 각각 remote를 만든다.
4. `senior`, `헬스유튜브`의 실제 폴더 경로를 확인한다.
5. 그 다음 repo별 commit/push를 진행한다.
