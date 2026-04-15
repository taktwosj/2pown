# ChatGPT Web Review Bridge

프로젝트 번호: `11`  
프로젝트명: `coding`

## 목적

크롬의 ChatGPT 웹 링크(일반 ChatGPT 또는 custom GPT)에 같은 질문을 던지고,
답변을 `runtime/` 산출물로 모아서 VS Codex에 수동 전달하기 위한 보조 도구다.

이 도구는 아래까지만 자동화한다.

1. Chrome 열기 또는 기존 디버깅 세션에 붙기
2. 지정한 ChatGPT 링크 열기
3. 질문 보내기
4. 답변 텍스트 저장
5. 필요하면 Telegram으로 답변 전달

이 도구는 **VS Code 채팅에 자동 입력하지 않는다.**
산출물을 사람이 보고 VS Codex에 붙여넣는 반자동 브리지로 쓴다.
또는 `--notify-telegram`으로 답변을 텔레그램에 바로 보낼 수 있다.

## canonical

- 코드 정본: `C:\1POW\tools\auto_work\chatgpt_web_review_bridge.py`
- 실행 래퍼:
  - `C:\1POW\tools\auto_work\RUN_CHATGPT_WEB_REVIEW_BRIDGE.ps1`
  - `C:\1POW\tools\auto_work\RUN_CHATGPT_WEB_REVIEW_BRIDGE.cmd`

## 전제

- Windows Chrome 사용
- ChatGPT 로그인 필요
- 처음 한 번은 전용 Chrome 프로필에서 로그인해야 한다
- Playwright Python 패키지 설치 필요

전용 프로필 기본값:

- `C:\Users\<USERNAME>\AppData\Local\1POWChatGPTBridgeProfile`

## 기본 사용

Windows PowerShell 기준:

```powershell
cd C:\1POW
.\tools\auto_work\RUN_CHATGPT_WEB_REVIEW_BRIDGE.ps1 `
  --url "https://chatgpt.com/g/..." `
  --url "https://chatgpt.com/g/..." `
  --prompt-file "C:\path\to\review_prompt.txt" `
  --notify-telegram
```

이 도구는 기본적으로 **Windows PowerShell 실행 기준**으로 설계했다.  
다만 최신 버전은 WSL에서도 Windows Chrome의 remote-debugging host를 자동 추적해서 붙도록 보강했다.
그래도 첫 로그인이나 방화벽/로컬 포트 문제가 있으면 Windows 세션에서 한 번 로그인 준비를 먼저 하는 쪽이 가장 안정적이다.

## VS Code에서 시작하는 법

VS Code에 아래 task가 연결돼 있다.

- `ChatGPT Review Bridge: Login`
- `ChatGPT Review Bridge: Run Review`
- `ChatGPT Review Bridge: Quick Run`

사용 방법:

1. VS Code에서 `Ctrl+Shift+P`
2. `Tasks: Run Task`
3. 먼저 `ChatGPT Review Bridge: Login`
4. 전용 Chrome 프로필 창에서 ChatGPT 로그인
5. 다시 `Tasks: Run Task`
6. `ChatGPT Review Bridge: Run Review`
7. prompt 파일 경로를 넣고 실행

기본 prompt 파일 경로:

- `C:\1POW\runtime\review_prompt.txt`

더 간단한 방식:

- `Ctrl+Alt+Q`
- 고정 링크 2개 + 고정 prompt 파일로 바로 실행

Quick Run이 읽는 기본 prompt 파일:

- `C:\1POW\runtime\review_prompt.txt`

실행 후:

- 답변은 runtime 산출물에 저장된다
- `--notify-telegram`이 기본이라 텔레그램으로도 요약/답변이 온다

산출물:

- `C:\1POW\runtime\chatgpt_web_review_bridge\<timestamp>\`

주요 파일:

- `01_<slug>_prompt.txt`
- `01_<slug>_reply.txt`
- `01_<slug>_meta.json`
- `02_<slug>_prompt.txt`
- `02_<slug>_reply.txt`
- `02_<slug>_meta.json`
- `summary.json`

## 최초 로그인 준비

처음에는 로그인만 하도록 Chrome을 열 수 있다.

```powershell
cd C:\1POW
.\tools\auto_work\RUN_CHATGPT_WEB_REVIEW_BRIDGE.ps1 `
  --url "https://chatgpt.com/g/..." `
  --manual-login-only `
  --notify-telegram
```

그 후 전용 프로필 창에서 로그인한 뒤, 다시 일반 실행을 한다.

필요하면 remote-debugging host를 직접 줄 수 있다.

```powershell
cd C:\1POW
.\tools\auto_work\RUN_CHATGPT_WEB_REVIEW_BRIDGE.ps1 `
  --host "172.28.64.1" `
  --url "https://chatgpt.com/g/..." `
  --manual-login-only
```

## 권장 운영 흐름

1. VS Codex가 계획/패치 초안을 만든다.
2. 그 내용을 `review_prompt.txt`로 저장한다.
3. 이 브리지로 검수용 ChatGPT 링크 2곳에 같은 질문을 보낸다.
4. 답변 파일 2개를 보거나, Telegram으로 바로 받은 뒤 필요한 부분만 요약한다.
5. 요약본을 VS Codex에 붙여넣고 수정 지시를 한다.

## 한계

- ChatGPT 웹 UI 변경에 따라 selector가 깨질 수 있다.
- 로그인/보안확인/캡차가 뜨면 수동 개입이 필요하다.
- custom GPT의 응답 속도는 느릴 수 있다.
- VS 입력까지 완전 자동으로 밀어 넣지는 않는다.
- GPT 소개 화면으로 열리면 자동으로 “새 채팅/Use GPT” 진입을 시도한다.

## 보안

- 토큰, 비밀번호, 주민번호, 운영 시크릿은 그대로 넣지 않는다.
- 고객 개인정보는 필요한 최소한만 프롬프트에 넣는다.
- 원문이 민감하면 사전 마스킹 후 사용한다.
