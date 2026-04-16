# 2POW 시스템 연동 구조

> 프로젝트간 데이터 흐름과 의존 관계를 정리한 문서.
> 개별 프로젝트 상세는 각 HANDOVER.md를 본다.

## 1. 전체 데이터 흐름

```
조견표 (jogyeon, 금융상품 데이터 원본)
  │
  ↓
bankly MCP 서버 (`jogyeon/bankly`, Cafe24 target: `/srv/workspace/02_jogyeon/bankly`, 금리/수당/은행조건 API)
  │
  ├──→ 금융조견.html (BANKLY)
  ├──→ bot.py 상품 분류 (텔레그램)
  └──→ 통합관리.xlsm 상품시트 (고객관리 엑셀)
         │
         │ daily_sync.py (사무실 PC, 자동)
         ↓
텔레그램 봇 (bot.py)
  │
  ├──→ 71번 공고문 자동 게시 (external publisher)
  │       │
  │       │ C:\ONEtaktwosj\OneDrive\22blog\wordpress\publish_notice_posts.py
  │       ├──→ WordPress REST API → 포스트 생성 (jsjtaktwo.mycafe24.com/blog)
  │       └──→ wp_notice_map.json → eeem-clean.html 공고탭 링크 자동반영
  │
  │ admin접수.py / Playwright
  ↓
legacy crm-v9-site.html (archived outside active 2POW workspace) ──→ ivwith DB (premloan)
                        ↑
                        │ CSV 동기화
                        └── daily_sync.py

마이홈 뷰어 (eeem-clean.html, LHSHAPT #2)
  │ fetch wp_notice_map.json
  └──→ 공고탭 링크 컬럼 ("📝 보기" 링크)

자동작업 (#11, 서버 배치)
  └── 서버 cron/배치 스크립트 → Cafe24 런타임
```

## 2. 프로젝트 의존 관계

| 프로젝트 | 의존 대상 | 연동 방식 |
|---------|----------|----------|
| 텔레그램 봇 (#6) | 고객관리 엑셀 (#7) | daily_sync, 엑셀 COM 읽기/쓰기 |
| 텔레그램 봇 (#6) | Admin 고도화 (#9) | admin접수.py → legacy crm-v9-site.html (archived outside active 2POW workspace) → ivwith DB |
| 텔레그램 봇 (#6) | BANKLY (#3) | admin접수 시 상품 분류/금리 참조 |
| 텔레그램 봇 (#6) | 외부 공고문 게시 | 71번 메뉴 → `C:\ONEtaktwosj\OneDrive\22blog\wordpress\publish_notice_posts.py` 실행 |
| BANKLY (#3) | 고객관리 엑셀 (#7) | 금리/수당 변경 시 양쪽 동시 확인 |
| Admin 고도화 (#9) | 고객관리 엑셀 (#7) | daily_sync로 엑셀 → CSV → DB |
| 외부 공고문 게시 | LHSHAPT (#2) | wp_notice_map.json → eeem-clean.html 공고탭 링크 |
| 외부 공고문 게시 | 텔레그램 봇 (#6) | 71번 트리거로 신규 공고 자동 게시 |
| 자동작업 (#11) | Cafe24 서버 | 서버 배치 cron/스크립트 런타임 |

현재 `Admin 고도화 (#9)`의 local canonical entrypoint는 `ivwith/admin_new_runtime` in `2POW`다. legacy PHP snapshot은 `quarantine/legacy_app_copies/2026-04-10/root_ivwith-admin-new_copy/legacy-php`로 archived 됐다.
현재 `LHSHAPT (#2)`의 local canonical worktree는 `C:\2POW\myhome`이다. 텔레그램 71번 메뉴는 외부 repo `C:\ONEtaktwosj\OneDrive\22blog\wordpress\publish_notice_posts.py`를 직접 호출한다. `2POW`에는 해당 외부 게시 프로젝트의 로컬 미러를 유지하지 않는다.

## 3. 금리/수당 데이터 — MCP 기준 규칙

**bankly MCP 서버**가 금리/수당/은행조건의 유일한 기준 데이터 소스(single source of truth)다.
대출상품/금리/수당/은행조건이 관련된 작업은 **MCP 서버를 최우선으로 조회/확인**한 뒤 진행한다.
MCP 데이터와 다른 곳(금융조견.html, 엑셀 상품시트, bot.py)의 값이 다르면 MCP가 맞다.

사용 가능한 MCP 도구:
- `calc_loan_rate` — 금리 계산
- `compare_banks` — 은행 비교
- `get_bank_conditions` — 은행별 조건
- `get_commissions` — 수당률/보너스
- `list_banks` — 은행 목록
- `search_loan_products` — 상품 검색

**현재 상태**: MCP 데이터를 Claude만 사용. 운영 파일들은 각자 하드코딩.
**목표**: MCP를 single source of truth로 만들고, 나머지가 거기서 읽어가는 구조.

### 금리/수당 변경 시 영향 범위

| 변경 대상 | 영향받는 파일 | 위치 |
|----------|------------|------|
| 은행 금리 | `금융조견.html` | BANKLY |
| 수당률/보너스 | `금융조견.html` | BANKLY |
| 상품 분류 로직 | `admin접수.py`, `bot.py` | 텔레그램 |
| 상품시트 | `통합관리.xlsm` | 고객관리 엑셀 |

**금리/수당 변경 작업 시 반드시 bankly MCP 서버를 먼저 조회하고, 변경 후 위 4곳을 동시 확인해야 한다.**

## 4. 사무실 PC 전용 작업

아래는 사무실 PC에서만 실행 가능하다:
- bot.py (텔레그램 봇 상주)
- daily_sync.py (엑셀 → CSV → DB)
- admin접수.py / 키움신규접수.py / ms신규접수.py (Playwright 자동접수)
- 통합관리.xlsm (엑셀 COM 조작)
