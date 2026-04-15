# 새 PC Git 반영 결과

작성일: 2026-04-09  
목적: 완전히 새로운 PC에서 최신 구조로 작업을 이어갈 수 있도록, 이번 정리본의 실제 push 결과를 기록

## 결론

핵심 정리본은 push됐다.  
다만 모든 repo가 GitHub remote인 것은 아니어서, 새 PC에서 `완전 무중단 복원`을 하려면 `GitHub + OneDrive mirror` 둘 다 기준으로 봐야 한다.

## 1. 실제 push 완료

### GitHub로 반영됨

- `C:\1POW` -> `https://github.com/taktwosj/1pow-meta.git`
  - pushed: `f460e7c`
- `C:\1POW\03_telegram_py` -> `https://github.com/taktwosj/1pow-03-telegram-py.git`
  - pushed: `138db3a`
- `C:\1POW\projects\blog` -> `https://github.com/taktwosj/naverblog.git`
  - pushed: `164974e` rebase 후 반영

### OneDrive mirror remote로 반영됨

- `C:\1POW\02_jogyeon` -> `C:\ONEtaktwosj\OneDrive\11AI\_git_remote_mirrors\1pow-02-jogyeon.git`
  - pushed: `39c7779`
- `C:\1POW\admin` -> `C:\ONEtaktwosj\OneDrive\11AI\_git_remote_mirrors\1pow-admin.git`
  - pushed: `de43a4b`
- `C:\1POW\ivwith` -> `C:\ONEtaktwosj\OneDrive\11AI\_git_remote_mirrors\1pow-ivwith.git`
  - pushed: `2ab9c35`

## 2. 새 PC에서 바로 받는 기준

### GitHub clone/pull 대상

- `1pow-meta.git`
- `1pow-03-telegram-py.git`
- `naverblog.git`

### OneDrive mirror 동기화가 필요한 대상

- `1pow-02-jogyeon.git`
- `1pow-admin.git`
- `1pow-ivwith.git`

즉 새 PC가 정말 완전히 비어 있다면, 아래 둘 중 하나가 필요하다.

- OneDrive를 먼저 동기화해서 mirror bare repo 경로를 살린다
- 또는 나중에 위 3개 repo도 GitHub remote로 옮긴다

## 3. 이번 push에 포함된 핵심 정리

- `02_jogyeon/bankly` 기준으로 BANKLY 이동
- `admin`에서 `_admin_new_work`, BANKLY, 구형 CRM/조견 자산 제거
- `ivwith/admin_new_runtime`로 admin-new 자산 흡수
- `03_telegram_py` office/codex runtime 분리
- root `1POW`의 bot/workspace 정리 반영
- `projects/blog` 구조 재편 반영

## 4. 새 PC에서 Git으로 안 내려오는 것

아래는 별도 복원 대상이다.

- 토큰/시크릿
  - `bot_token.txt`
  - `allowed_chat_ids.txt`
  - `office_allowed_hosts.txt`
  - `anthropic_api_key.txt`
  - `.env`
- runtime 상태파일
- 로그
- `cleanup_legacy_projects/**`
- `quarantine/**`
- `__pycache__/**`
- `.venv_live/**`

## 5. 주의할 점

- `C:\1POW_META` 로컬 clone은 현재 remote와 별도로 dirty 상태가 남아 있다.
- 이번 기준에서 `새 PC 복원 정본`은 로컬 `C:\1POW_META` 현재 작업트리 자체가 아니라, 이미 push된 remote 기준이다.
- `C:\1POW`와 `C:\1POW_META`는 현재 같은 GitHub remote를 보고 있으므로, 새 PC에서는 같은 remote를 두 번 clone하는 구조를 그대로 따라야 한다.

## 한 줄 판단

지금 시점부터는 새 PC에서 `push된 remote 기준`으로 새로 받는 것이 가능하다.  
다만 `02_jogyeon`, `admin`, `ivwith`는 아직 GitHub가 아니라 OneDrive mirror 기반이라는 점이 마지막 남은 portability 조건이다.
