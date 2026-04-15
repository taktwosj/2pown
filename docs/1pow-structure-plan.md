# 1POW 폴더 운영구조 개편안

## 현재 문제
- 코드, 원본 데이터, 생성 결과물, 백업 파일이 같은 레벨에 섞여 있다.
- 어떤 파일이 원본이고 어떤 파일이 생성물인지 즉시 구분하기 어렵다.
- 같은 내용의 복제본이 여러 위치에 있어 기준 파일이 흔들릴 수 있다.
- 문서화와 자동화는 시작됐지만 변경 이력 추적은 약하다.

## 목표
- 작업 단위를 빠르게 식별할 수 있게 만든다.
- 원본 데이터와 생성 결과물을 분리한다.
- `myhome`, `admin`, `ivwith`를 서로 독립된 작업 영역으로 본다.
- 나중에 Git 도입과 자동화 확장이 쉬운 구조로 정리한다.

## 권장 구조
```text
1POW/
  AGENTS.md
  docs/
    codex-usage-checklist.md
    1pow-structure-plan.md
    change-log/

  myhome/
    src/
    app/
    data/
      raw/
      interim/
      out/
    reports/
    scripts/

  admin/
    src/
    data/
    docs/
    archive/

  ivwith/
    src/
    data/
      raw/
      out/
    reports/
    scripts/

  archive/
```

## 현재 기준 최소 개편 원칙
- 한 번에 전부 옮기지 않는다.
- 먼저 `docs/`와 운영 규칙부터 만든다.
- 그다음 생성물이 많은 영역부터 분리한다. 우선순위는 `myhome`이다.
- 복제본은 바로 삭제하지 말고 `archive/`로 옮긴 뒤 기준 파일을 정한다.

## myhome 우선 개편안
- 스크립트: `run_daily_pipeline.py`, `build_sales_ready_outputs.py`, `merge_private_rental_into_hwspr.py`는 장기적으로 `myhome/scripts/` 또는 `myhome/src/`로 이동
- 원본 데이터: 지자체/LH/민간임대 원본 CSV는 `myhome/data/raw/`
- 중간 생성물: 병합본과 보강본은 `myhome/data/interim/`
- 최종 산출물: 영업리스트와 임베드용 결과는 `myhome/data/out/`
- 리포트: 품질 보고서와 누락 보고서는 `myhome/reports/`

## 당장 실행할 5단계
1. `1POW`를 Git 저장소로 초기화한다.
2. `docs/`를 기준 문서 위치로 고정한다.
3. `myhome` 안에서 `raw / interim / out / reports`만 먼저 나눈다.
4. `03_telegram_py` 아래 복제본 중 기준 파일과 배포 파일을 구분한다.
5. 실행 명령을 하나로 줄이고, 그 명령이 끝나면 보고서까지 생성되게 맞춘다.

## 주의점
- 경로 개편은 파일명 변경보다 참조 경로 수정이 더 큰 일이다.
- 배치 파일, 텔레그램 연동, HTML 임베드 파일은 상대경로 의존성이 있을 수 있으니 한 번에 이동하지 않는다.
- 원본 데이터 파일은 먼저 이동하지 말고, 생성물부터 정리하는 편이 안전하다.
