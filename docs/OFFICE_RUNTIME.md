# OFFICE RUNTIME

사무실 PC는 정본이 아니라 실행 노드다.

## 확정 사실

- 정본 repo 경로: `C:\2POW\03_telegram_py`
- Git 정본 원격: `https://github.com/taktwosj/1pow-03-telegram-py.git`
- 실제 런타임 루트: `C:\2POW`
- office 상태/로그 런타임 루트: `C:\2POW\runtime\root_bot`
- 실제 실행 파일: `C:\2POW\bot.py`
- 자동 시작 방식: Windows 작업 스케줄러
- 확인된 작업 이름:
  - `JunjunBotWatchdog_NOTE`
  - `OnePOW_OpenExcel_OnLogon`

## 텔레그램 봇 실행

- 수동 시작 스크립트: `C:\2POW\START_TELEGRAM_BOT_NOW.bat`
- 고정 Python 경로: `C:\Users\정상준\AppData\Local\Programs\Python\Python314\python.exe`
- 시작 커맨드: `C:\Users\정상준\AppData\Local\Programs\Python\Python314\python.exe bot.py`
- 작업 디렉토리: `C:\2POW`
- venv 사용 여부: 현재 시작 스크립트 기준 `미사용`

## 배포/복구 흐름

- 사무실 실행본 갱신 스크립트: `C:\2POW\03_telegram_py\office_recover_and_check.ps1`
- 이 스크립트는 `C:\2POW\03_telegram_py`의 최신 파일을 `C:\2POW`로 복사한 뒤 재시작한다.
- 따라서 `C:\2POW\03_telegram_py`는 정본 repo, `C:\2POW`는 라이브 실행 루트로 본다.

## 설정/상태 파일

- 존재 확인된 런타임 파일:
  - `C:\2POW\bot_token.txt`
  - `C:\2POW\allowed_chat_ids.txt`
  - `C:\2POW\office_allowed_hosts.txt`
- 존재 확인된 상태/로그 파일:
  - `C:\2POW\runtime\root_bot\state\bot_runtime_status.json`
  - `C:\2POW\runtime\root_bot\state\bot_heartbeat.json`
  - `C:\2POW\runtime\root_bot\state\bot.pid`
  - `C:\2POW\runtime\root_bot\logs\bot_runtime.log`
  - `C:\2POW\runtime\root_bot\logs\bot_runtime.err.log`
  - `C:\2POW\runtime\root_bot\logs\bot_watchdog.log`

## 운영 메모

- `office_allowed_hosts.txt` 또는 `BOT_ALLOWED_HOSTS` 설정이 있어야 봇이 사무실 PC에서만 실행된다.
- 텔레그램 repo의 canonical `origin`은 GitHub이고, 기존 OneDrive bare mirror는 `onedrive` 백업 remote로만 유지한다.
- `C:\2POW\03_telegram_py\START_TELEGRAM_BOT_NOW.bat` 기준으로 사무실 런타임 Python은 `Python314` 단일 경로로 고정했다.
- `C:\2POW\CLAUDE.md`는 참고용 포인터 문서일 뿐이고, 정본 시작 절차는 항상 `C:\2POW\docs\START.md`다.
