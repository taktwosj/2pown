# Repo-less Project Docs

이 디렉토리는 아직 독립 repo가 없는 프로젝트의 임시 문서 정본 위치다.

원칙:
- 프로젝트 식별은 `meta/project_registry.json`을 따른다
- 문서 정본은 여기 두고, 서버 문서는 배포 사본으로만 취급한다
- 프로젝트 repo가 생기면 해당 문서는 그 repo로 이동한다
- `doc_canonical = repo:*` 이면 해당 repo 문서를 우선한다
- `doc_canonical = docs/projects/...` 이면 이 디렉토리 문서를 우선한다
- 서버 markdown은 canonical fallback으로 쓰지 않는다

권장 구조:

```text
docs/projects/
  0-macmini/
  2-lhshapt/
  3-bankly/
  4-ivwith/
  5-jogyeon/
  6-telegram-bot/
  7-office-workbook/
  8-filez/
  9-admin-new/
  10-admin-codex/
  11-auto-work/
```

권장 파일:
- `README.md`
- `HANDOVER.md`
- `WORK_RULES.md`
