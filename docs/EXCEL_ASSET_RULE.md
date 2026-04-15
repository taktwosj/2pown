# EXCEL ASSET RULE

고객관리 엑셀은 코드 repo가 아니라 업무 자산이다.

## 확정 사실

- 실제 파일명: `통합관리.xlsm`
- 고정 경로: `C:\2POW\고객관리\통합관리.xlsm`
- 집/사무실/외부 모두 이 경로를 기준으로 한다.
- 봇 설정 키:
  - `EXCEL_TARGET_PATH`
  - `EXCEL_TARGET_BASENAME` 기본값 `통합관리.xlsm`
- 서버 백업 경로: `/srv/workspace/고객관리/통합관리.xlsm`

## 봇 참조 규칙

- `C:\2POW\bot.py`는 아래 우선순위로 파일을 찾는다.
  - `EXCEL_TARGET_PATH`
  - `C:\2POW\고객관리\통합관리.xlsm`

## 동기화/백업

- 동기화 스크립트: `C:\2POW\sync_excel_to_server.ps1`
- 로컬 원본 경로: `C:\2POW\고객관리\통합관리.xlsm`
- 서버 업로드 경로: `/srv/workspace/고객관리/통합관리.xlsm`
- 로그/스탬프 파일:
  - `C:\2POW\sync_excel.log`
  - `C:\2POW\.last_excel_sync`

## 최소 검증

- 파일 존재 확인: `C:\2POW\고객관리\통합관리.xlsm`
- 시트 확인: `H` 시트 존재
- 로컬 점검 스크립트: `C:\2POW\check_excel.ps1`
  - Excel COM으로 열린 워크북 중 `H` 시트를 찾고 `C13`, `D13`, `C14`, `D14`를 읽는다.

## 운영 규칙

- OneDrive는 백업/동기화 수단일 뿐 정본 경로가 아니다.
- 서버 사본은 복구/검증 자산이고, 편집은 `C:\2POW\고객관리\` 기준으로 한다.
