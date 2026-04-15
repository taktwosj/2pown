import telebot
import json
import logging
import os
import re
import subprocess
import sys
import socket
import shutil
import urllib.error
import urllib.request
import functools
import types
import requests
import importlib.util
from datetime import datetime, timedelta
import time
import threading
import xml.etree.ElementTree as ET
from zipfile import ZipFile
_PREFERRED_TELEGRAM_SCRIPT_DIR = (os.environ.get("BOT_SCRIPT_DIR") or "").strip()
if not _PREFERRED_TELEGRAM_SCRIPT_DIR:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(_HERE).lower() == "03_telegram_py":
        _PREFERRED_TELEGRAM_SCRIPT_DIR = _HERE
    else:
        _PREFERRED_TELEGRAM_SCRIPT_DIR = os.path.join(_HERE, "03_telegram_py")
if _PREFERRED_TELEGRAM_SCRIPT_DIR and os.path.isdir(_PREFERRED_TELEGRAM_SCRIPT_DIR):
    if _PREFERRED_TELEGRAM_SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _PREFERRED_TELEGRAM_SCRIPT_DIR)
_ROOT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_SCRIPT_DIR)
try:
    from 접수공통 import parse_customer_text as common_parse_customer_text
except Exception:
    common_parse_customer_text = None

from bot_app.menus import home as home_menu
from bot_app.menus import briefing as briefing_menu
from bot_app.menus import ivwith_menu
from bot_app.menus import ixio_excel as ixio_excel_menu
from bot_app.menus import rt_watch as rt_watch_menu
from bot_app.menus import sales_reports as sales_reports_menu
from bot_env_config import load_bot_env_config
from home_dispatch import dispatch_home_state_0
from bot_runtime_state import (
    build_runtime_heartbeat_payload,
    build_runtime_status_payload,
    cleanup_runtime_identity_files,
    ensure_runtime_dirs,
    load_runtime_status,
    write_json_payload,
    write_pid_file,
)
from bot_security_config import (
    first_nonempty_line,
    load_allowed_chat_ids,
    load_allowed_hostnames,
    load_bot_token,
    parse_name_list,
    read_text_file,
    read_secret_text,
    resolve_secret_file_path,
)
from bot_task_runner import run_powershell_command, start_background_task
from bot_chat_state import (
    build_default_chat_session,
    copy_session_value,
    get_chat_session,
    load_chat_session,
    run_in_chat_session,
    save_chat_session,
    with_chat_session_arg,
    with_message_chat_session,
)
from bot_state_wait_ixio import (
    handle_ixio_state_18,
    handle_ixio_state_19,
    handle_ixio_state_20,
    handle_ixio_state_21,
    handle_ixio_state_22,
    handle_processing_wait,
    handle_result_lookup_state,
)
from bot_state_ms_review import (
    handle_ms_review_state_13,
    handle_ms_review_state_14,
    handle_ms_review_state_15,
)
from bot_state_admin_followup import (
    handle_admin_followup_state_9,
    handle_admin_followup_state_10,
    handle_admin_followup_state_11,
    handle_admin_followup_state_12,
)
from bot_state_due_customers import (
    handle_due_customer_state_23,
    handle_due_customer_state_24,
    handle_due_customer_state_25,
)
from bot_state_sales_briefing_rt import (
    handle_briefing_state_35,
    handle_briefing_state_36,
    handle_rt_state_16,
    handle_rt_state_17,
    handle_sales_state_40,
    handle_sales_state_41,
)
from bot_script_runners import (
    run_capture_script,
    run_ms_consent_script,
    run_simple_text_script,
)
from bot_event_flow import (
    clear_openclaw_redirect,
    handle_urgent_reset_message,
    has_openclaw_redirect,
    mark_openclaw_redirect,
    process_new_messages_with_priority_reset,
)
from bot_instance_guard import acquire_single_instance_guard
from bot_message_preroute import handle_message_preroute
from bot_runtime_polling import start_bot_runtime

try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ivwith'))
    sys.path.insert(0, os.path.join(os.environ.get("BOT_BASE_DIR", r"C:\2POW"), 'projects', 'ivwith'))
    sys.path.insert(0, os.path.join(os.environ.get("BOT_BASE_DIR", r"C:\2POW"), 'ivwith'))
    from ivwith_report import (
        build_customer_report,
        format_sales_menu, format_weeks_menu,
        SALES_LIST, WEEK_OPTIONS,
    )
    IVWITH_AVAILABLE = True
except Exception:
    IVWITH_AVAILABLE = False

try:
    telebot.logger.setLevel(logging.CRITICAL)
except Exception:
    pass

_BOT_ENV = load_bot_env_config()
BASE_DIR = _BOT_ENV["BASE_DIR"]
IVWITH_MENU34_BASE_DIR = _BOT_ENV["IVWITH_MENU34_BASE_DIR"]
BOT_RUNTIME_DIR = _BOT_ENV["BOT_RUNTIME_DIR"]
BOT_STATE_DIR = _BOT_ENV["BOT_STATE_DIR"]
BOT_PROFILE = _BOT_ENV["BOT_PROFILE"]
BOT_SCRIPT_DIR = _BOT_ENV["BOT_SCRIPT_DIR"]
BOT_LOG_DIR = _BOT_ENV["BOT_LOG_DIR"]
BOT_LOCK_DIR = _BOT_ENV["BOT_LOCK_DIR"]
BOT_PID_FILE = _BOT_ENV["BOT_PID_FILE"]
BOT_LOCK_FILE = _BOT_ENV["BOT_LOCK_FILE"]
BOT_REQUIRE_RUNTIME_ALLOWED_CHAT_IDS = _BOT_ENV["BOT_REQUIRE_RUNTIME_ALLOWED_CHAT_IDS"]
BOT_AUTO_ALLOW_PRIVATE_CHAT = _BOT_ENV["BOT_AUTO_ALLOW_PRIVATE_CHAT"]


def _resolved_ivwith_base_dir(default_base_dir, menu_base_dir):
    candidate = str(menu_base_dir or "").strip()
    if not candidate:
        return default_base_dir

    required_paths = (
        os.path.join(candidate, "ivwith", "daily_sync.py"),
        os.path.join(candidate, "lockfile.py"),
        os.path.join(candidate, "runtime", "last_sync.json"),
        os.path.join(candidate, "config", "canonical_map.local.json"),
    )
    if all(os.path.exists(path) for path in required_paths):
        return candidate
    return default_base_dir


def _load_ivwith_report_runtime(base_dir):
    module_path = os.path.join(base_dir, "ivwith", "ivwith_report.py")
    if not os.path.exists(module_path):
        raise FileNotFoundError(module_path)

    module_dir = os.path.dirname(module_path)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location("ivwith_report_runtime", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"ivwith_report spec load failed: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IVWITH_RUNTIME_BASE_DIR = _resolved_ivwith_base_dir(BASE_DIR, IVWITH_MENU34_BASE_DIR)
try:
    _ivwith_report_runtime = _load_ivwith_report_runtime(IVWITH_RUNTIME_BASE_DIR)
    build_customer_report = _ivwith_report_runtime.build_customer_report
    format_sales_menu = _ivwith_report_runtime.format_sales_menu
    format_weeks_menu = _ivwith_report_runtime.format_weeks_menu
    SALES_LIST = _ivwith_report_runtime.SALES_LIST
    WEEK_OPTIONS = _ivwith_report_runtime.WEEK_OPTIONS
    IVWITH_AVAILABLE = True
except Exception:
    IVWITH_RUNTIME_BASE_DIR = BASE_DIR

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
# 운영 토큰/허용채팅은 파일 또는 환경변수로만 읽는다.
TOKEN = ""
ALLOWED_CHAT_IDS = set()
AUTO_ALLOW_PRIVATE_CHAT = BOT_AUTO_ALLOW_PRIVATE_CHAT
bot = None
BOT_VERSION = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
POLLING_RETRY_SLEEP_SEC = 1
try:
    BOT_LOCK_PORT = int(os.environ.get("BOT_LOCK_PORT", "46359"))
except Exception:
    BOT_LOCK_PORT = 46359
BOT_ENFORCE_OFFICE_HOST = os.environ.get("BOT_ENFORCE_OFFICE_HOST", "0").strip() == "1"
BOT_INSTANCE_GUARD = None
try:
    EXCEL_DATE_YEAR = int(os.environ.get("EXCEL_DATE_YEAR", "2026"))
except ValueError:
    EXCEL_DATE_YEAR = 2026

# 0: 메뉴판, 1: admin 입력 대기, 2: 접수승인 대기, 3: 결과조회(MS/키움) 이름 대기, 4: 키움신규접수 입력 대기,
# 5: 키움신규접수 상품선택 대기, 6: ms신규접수 입력 대기, 7: 숫자2줄 금액확인 대기, 8: ms상품번호 선택 대기
# 9: admin 접수은행 확인, 10: admin 접수은행 선택, 11: admin후 ms신규접수 진행확인, 12: admin후 키움신규접수 진행확인
# 13: ms 입력값 확인(11/22/00), 14: ms 수정할 라벨 번호 선택, 15: ms 라벨 값 수정 입력(줄번호/직접입력)
# 16: 빌라 실거래 조회 개월수 선택, 17: 빌라 실거래 조회 유형 선택, 18: 익시오 상담요약 입력 대기
# 19: 익시오 후속 액션 선택, 20: 엑셀 중복 입력 확인, 21: 엑셀 고객입력 원문 대기, 22: 엑셀 입력값 확인
# 23: 오늘/지난 고객리스트 메뉴, 24: 오늘/지난 고객리스트 예약 시각 입력
# 35: AI 브리핑 간단분석 후 상세분석 여부 대기
# 40: ivwith 리포트 종류/영업자 선택 대기, 41: ivwith 주차 선택 대기
user_state = 0
file_list = []
target_script = ""
auto_script = ""
pending_new_text = ""
pending_new_script = ""
pending_amount_text = ""
pending_amount_script = ""
pending_amount_state = 0
pending_admin_text = ""
pending_admin_bank = ""
pending_admin_name = ""
pending_followup_text = ""
pending_followup_name = ""
pending_followup_kind = ""
pending_followup_option = ""
pending_ivwith_report_type = ""
pending_ivwith_sales_key = ""
pending_ivwith_sales_display = ""
pending_ms_script = ""
pending_ms_fields = {}
pending_ms_lines = []
pending_ms_edit_key = ""
pending_ms_mode = "ms"
pending_rt_months = 12
pending_rt_print_history = False
pending_ixio_data = {}
pending_ixio_duplicates = []
pending_excel_data = {}
pending_excel_resume = ""
_briefing_cached_rows = []
_briefing_classified = {}
AUTO_TIMER_REGISTRY = {}
AUTO_TIMER_TOKEN_REGISTRY = {}
PYTHON_EXE = sys.executable or "python"
NON_SELECTABLE_FILES = {"접수공통.py"}
HIDDEN_MENU_FILES = {"자동접수.py", "텔레자동접수.py", "접수공통.py"}
AUTO_PROGRESS_SECONDS = int(os.environ.get("BOT_AUTO_PROGRESS_SECONDS", "10"))
ADMIN_FLOW_RUNNING_STATE = 26
IXIO_SUMMARY_RUNNING_STATE = 27
AI_BRIEFING_RUNNING_STATE = 28
EXCEL_WRITE_RUNNING_STATE = 29
MENU_SCRIPT_MAP = {
    "1": "admin접수.py",
    "3": "ms신규접수.py",
    "4": "ms신용조회동의.py",
    "5": "키움신규접수.py",
    "6": "MS결과확인.py",
    "7": "키움결과확인.py",
}
SCRIPT_SEARCH_CACHE = {}
SCRIPT_SEARCH_MISS_CACHE = {}
SCRIPT_SEARCH_MISS_TTL_SECONDS = 300
MENU_RENDER_CACHE = {"message": "", "expires_at": 0.0}
RT_WATCH_SCRIPT = "molit_rt_watch.py"
RT_WATCH_TARGETS = "molit_targets_gwangjin_6apt_50_55.json"
RT_WATCH_LABEL = "광진구/40㎡이상"
IXIO_PROMPT_FILE = "익시오_파싱_지침서_v3.md"
IXIO_TRIGGER_PREFIXES = (
    "익시오에서 정상준님이 공유한 AI 통화 요약입니다.",
    "익시오에서 정상준님이 공유한 통화 내용입니다.",
)
IXIO_API_KEY_FILES = ("anthropic_api_key.txt", "claude_api_key.txt")
IXIO_MODEL_FILES = ("anthropic_model.txt", "claude_model.txt")
IXIO_DEFAULT_MODEL = "claude-sonnet-4-20250514"
IXIO_FALLBACK_SYSTEM_PROMPT = (
    "당신은 익시오 통화원문을 1POW 접수 포맷으로 정리하는 추출기다. 한국어만 사용한다.\n"
    "반드시 JSON 객체 하나만 출력한다. 설명, 문장, 마크다운, 코드펜스 금지.\n"
    "키는 정확히 다음만 사용한다:\n"
    "name, jumin, phone, address, deposit, loan, bank, kakao_kind, admin_kind, excel_kind, income, credit, note, consult_date, intake_date, stage, customer_status\n"
    "값 규칙:\n"
    "- bank: 키움 / 키움민간 / MS / 롯손 중 하나, 없으면 빈칸\n"
    "- kakao_kind: 외부업체 카톡접수에 넣을 종류 문구. 여러 개면 공백 구분 가능\n"
    "- admin_kind: 내부 admin 접수용 종류. 예: 공공임대선순위_N, 민간임대(선순위), 민간임대(신용관리), 민간임대(회파복), 임대아파트대출\n"
    "- excel_kind: 엑셀용 종류. 가계 / 대환 / 잔금 / 계잔금 중 하나\n"
    "- income: 직장인 / 프리랜서 / 자영/사업 / 주부 / 기타 중 하나\n"
    "- credit: 신용정상 / 개인회생 / 신용회복 / 파산면책 / 신용관리 / 회파복 중 하나\n"
    "- consult_date, intake_date: MM-DD 형식\n"
    "- note는 1차상담(B열)에 넣을 상담내용이며 핵심정보를 / 로 붙인 한 줄\n"
    "- customer_status는 고객상태(E열) 값이며 신규상담 기본값은 진행중(H)\n"
    "- stage, intake_date는 호환용 키다. 엑셀 붙여넣기 출력에서는 A열(2차상담)과 D열(2차접수)을 비우므로 빈 문자열로 두어도 된다\n"
    "- deposit, loan은 숫자만 남긴다\n"
    "- 모르는 값은 빈 문자열\n"
    "오늘 날짜 기준 기본값이 필요하면 " + datetime.now().strftime("%m-%d") + " 를 사용한다."
)
WOL_TARGET_MAC = os.environ.get("WOL_TARGET_MAC", "").strip()
WOL_BROADCAST_IP = os.environ.get("WOL_BROADCAST_IP", "255.255.255.255").strip()
try:
    WOL_PORT = int(os.environ.get("WOL_PORT", "9"))
except Exception:
    WOL_PORT = 9
MS_FIELD_ORDER = ["이름", "주민번호", "연락처", "주소", "보증금", "대출금", "접수", "종류", "신용", "기타"]
MS_REVIEW_FIELD_ORDER = ["이름", "주민번호", "연락처", "주소", "보증금", "대출금", "상품선택", "종류", "신용", "전송메모", "직업구분"]
KIWOOM_REVIEW_FIELD_ORDER = ["이름", "주민번호", "연락처", "주소", "보증금", "대출금", "접수", "종류", "신용", "기타", "직업구분"]
ADMIN_REVIEW_FIELD_ORDER = ["이름", "주민번호", "연락처", "주소", "보증금", "대출금", "접수", "종류", "신용", "직업구분", "상품선택", "기타"]
EXCEL_TARGET_BASENAME = os.environ.get("EXCEL_TARGET_BASENAME", "통합관리.xlsm").strip() or "통합관리.xlsm"
EXCEL_TARGET_PATH = (os.environ.get("EXCEL_TARGET_PATH") or "").strip()
REGION_PREFIXES = {
    "서울", "서울시", "서울특별시",
    "경기", "경기도",
    "인천", "인천시", "인천광역시",
    "부산", "부산시", "부산광역시",
    "대구", "대구시", "대구광역시",
    "대전", "대전시", "대전광역시",
    "광주", "광주시", "광주광역시",
    "울산", "울산시", "울산광역시",
    "세종", "세종시", "세종특별자치시",
    "강원", "강원도", "강원특별자치도",
    "충북", "충청북도",
    "충남", "충청남도",
    "전북", "전라북도", "전북특별자치도",
    "전남", "전라남도",
    "경북", "경상북도",
    "경남", "경상남도",
    "제주", "제주도", "제주특별자치도",
}
DUE_CUSTOMER_SCHEDULE_FILE = os.path.join(BASE_DIR, "due_customer_schedule.json")
BOT_RUNTIME_STATUS_FILE = os.environ.get(
    "BOT_RUNTIME_STATUS_FILE",
    os.path.join(BOT_STATE_DIR, "bot_runtime_status.json"),
)
BOT_HEARTBEAT_FILE = os.environ.get(
    "BOT_HEARTBEAT_FILE",
    os.path.join(BOT_STATE_DIR, "bot_heartbeat.json"),
)
BOT_HEARTBEAT_INTERVAL_SEC = 10
BOT_FATAL_EXIT_CONFLICT = 86
DUE_CUSTOMER_SCHEDULE_LOCK = threading.Lock()
RUNTIME_STATUS_LOCK = threading.Lock()
RUNTIME_STATUS_CACHE = {
    "status": "unknown",
    "detail": "",
    "extra": {},
}
if os.path.basename(PYTHON_EXE).lower() == "pythonw.exe":
    PYTHON_EXE = os.path.join(os.path.dirname(PYTHON_EXE), "python.exe")

def _excel_target_candidates():
    candidates = []
    if EXCEL_TARGET_PATH:
        candidates.append(EXCEL_TARGET_PATH)
    candidates.append(os.path.join(BASE_DIR, "고객관리", EXCEL_TARGET_BASENAME))
    user_profile = os.environ.get("USERPROFILE", "")
    one_drive = os.environ.get("OneDrive", "")
    one_drive_consumer = os.environ.get("OneDriveConsumer", "")
    # canonical workbook first (OneDrive fixed original)
    candidates.append(r"C:\ONEtaktwosj\OneDrive\11AI\1POW\고객관리\통합관리.xlsm")
    candidates.append(r"C:\Users\arajun\OneDrive\11AI\1POW\고객관리\통합관리.xlsm")
    # legacy / shared copies
    if one_drive:
        candidates.append(os.path.join(one_drive, "1myleaders", "통합문서", EXCEL_TARGET_BASENAME))
    if one_drive_consumer:
        candidates.append(os.path.join(one_drive_consumer, "1myleaders", "통합문서", EXCEL_TARGET_BASENAME))
    if user_profile:
        candidates.append(os.path.join(user_profile, "OneDrive", "1myleaders", "통합문서", EXCEL_TARGET_BASENAME))
    # 기존 환경에서 자주 쓰던 경로도 보조 후보로 포함
    candidates.append(r"C:\Users\arajun\OneDrive\1myleaders\통합문서\통합관리.xlsm")
    candidates.append(r"C:\Users\정상준\OneDrive\1myleaders\통합문서\통합관리.xlsm")
    uniq = []
    seen = set()
    for path in candidates:
        if not path:
            continue
        low = path.lower()
        if low in seen:
            continue
        seen.add(low)
        uniq.append(path)
    return uniq

def _resolve_excel_target_path():
    for path in _excel_target_candidates():
        if os.path.exists(path):
            return path
    return None

def _run_powershell(script, extra_env=None):
    return run_powershell_command(script, base_dir=BASE_DIR, extra_env=extra_env)

def open_managed_workbook():
    target = _resolve_excel_target_path()
    if not target:
        searched = "\n".join(_excel_target_candidates())
        return False, f"통합관리 파일 경로를 찾지 못했습니다.\n후보 경로:\n{searched}"
    ps_script = r"""
$ErrorActionPreference = 'Stop'
$target = $env:TG_EXCEL_TARGET
$baseName = $env:TG_EXCEL_BASENAME
$excel = $null
try {
  try { $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application') } catch {}
  if ($null -eq $excel) { $excel = New-Object -ComObject Excel.Application }
  $excel.Visible = $true
  $opened = $null
  foreach ($wb in @($excel.Workbooks)) {
    if ($wb.FullName -ieq $target) { $opened = $wb; break }
  }
  if ($null -eq $opened) {
    $sameName = @()
    foreach ($wb in @($excel.Workbooks)) {
      if ($wb.Name -ieq $baseName) { $sameName += $wb }
    }
    if ($sameName.Count -eq 1) { $opened = $sameName[0] }
  }
  if ($null -ne $opened) {
    Write-Output ('ALREADY_OPEN:' + $opened.FullName)
  } else {
    if (-not (Test-Path -LiteralPath $target)) { throw 'FILE_NOT_FOUND' }
    $newWb = $excel.Workbooks.Open($target)
    Write-Output ('OPENED:' + $newWb.FullName)
  }
}
catch {
  Write-Output ('ERROR:' + $_.Exception.Message)
  exit 1
}
"""
    result = _run_powershell(
        ps_script,
        extra_env={"TG_EXCEL_TARGET": target, "TG_EXCEL_BASENAME": EXCEL_TARGET_BASENAME},
    )
    out = decode_output(result.stdout).strip()
    err = decode_output(result.stderr).strip()
    if result.returncode != 0 or out.startswith("ERROR:"):
        return False, (out or err or "엑셀 열기 실패")
    if out.startswith("ALREADY_OPEN:"):
        return True, f"이미 열려 있습니다.\n{out.split(':', 1)[1].strip()}"
    if out.startswith("OPENED:"):
        return True, f"열었습니다.\n{out.split(':', 1)[1].strip()}"
    return True, out or "열기 완료"

def close_managed_workbook():
    ps_script = r"""
$ErrorActionPreference = 'Stop'
$baseName = $env:TG_EXCEL_BASENAME
$target = $env:TG_EXCEL_TARGET
$excel = $null
try { $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application') } catch {}
if ($null -eq $excel) {
  Write-Output 'NOT_RUNNING'
  exit 0
}
$closed = 0
foreach ($wb in @($excel.Workbooks)) {
  $isMatch = $false
  if ($target) { $isMatch = ($wb.FullName -ieq $target) }
  if (-not $isMatch -and ($excel.Workbooks.Count -eq 1)) { $isMatch = ($wb.Name -ieq $baseName) }
  if ($isMatch) {
    try { if (-not $wb.ReadOnly) { $wb.Save() } } catch {}
    $wb.Close($true)
    $closed += 1
  }
}
if ($closed -eq 0) {
  Write-Output 'NOT_OPEN'
} else {
  if ($excel.Workbooks.Count -eq 0) { try { $excel.Quit() } catch {} }
  Write-Output ('CLOSED:' + $closed)
}
"""
    target = _resolve_excel_target_path() or ""
    result = _run_powershell(
        ps_script,
        extra_env={"TG_EXCEL_TARGET": target, "TG_EXCEL_BASENAME": EXCEL_TARGET_BASENAME},
    )
    out = decode_output(result.stdout).strip()
    err = decode_output(result.stderr).strip()
    if result.returncode != 0:
        return False, (out or err or "엑셀 닫기 실패")
    if out == "NOT_RUNNING":
        return True, "엑셀이 실행 중이 아닙니다."
    if out == "NOT_OPEN":
        return True, f"{EXCEL_TARGET_BASENAME}이(가) 열려 있지 않습니다."
    if out.startswith("CLOSED:"):
        return True, f"{EXCEL_TARGET_BASENAME} 저장 후 닫기 완료"
    return True, out or "닫기 완료"


def _clear_pending_ixio():
    global pending_ixio_data, pending_ixio_duplicates
    pending_ixio_data = {}
    pending_ixio_duplicates = []


def _clear_pending_excel():
    global pending_excel_data, pending_excel_resume
    pending_excel_data = {}
    pending_excel_resume = ""


def _ixio_excel_row_values(data):
    normalized = _normalize_excel_write_payload(data)
    return [
        str(normalized.get("first_consult", "") or normalized.get("note", "") or "").strip(),
        str(normalized.get("consult_date", "") or "").strip(),
        str(normalized.get("second_date", "") or "").strip(),
        str(normalized.get("customer_status", "") or "").strip(),
        str(normalized.get("name", "") or "").strip(),
        str(normalized.get("jumin", "") or "").strip(),
        str(normalized.get("address", "") or "").strip(),
        str(normalized.get("phone", "") or "").strip(),
        str(normalized.get("deposit", "") or "").strip(),
        str(normalized.get("loan", "") or "").strip(),
        str(normalized.get("income", "") or "").strip(),
        str(normalized.get("excel_credit", "") or "").strip(),
        str(normalized.get("excel_kind", "") or "").strip(),
        str(normalized.get("display_bank", "") or "").strip(),
        "정",
    ]


def _parse_excel_month_day(value):
    raw = str(value or "").strip()
    if not raw:
        return None

    month = None
    day = None
    digits = re.sub(r"\D", "", raw)

    if re.fullmatch(r"\d{1,2}[-/.]\d{1,2}", raw):
        match = re.match(r"(\d{1,2})[-/.](\d{1,2})", raw)
        month = int(match.group(1))
        day = int(match.group(2))
    elif re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", raw):
        match = re.match(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", raw)
        month = int(match.group(2))
        day = int(match.group(3))
    elif re.fullmatch(r"\d{4}", digits):
        month = int(digits[:2])
        day = int(digits[2:4])
    elif re.fullmatch(r"\d{8}", digits):
        month = int(digits[4:6])
        day = int(digits[6:8])

    if month is None or day is None:
        return None

    try:
        datetime(EXCEL_DATE_YEAR, month, day)
    except ValueError:
        return None
    return month, day


def _normalize_excel_mmdd(value, fallback_today=False):
    parsed = _parse_excel_month_day(value)
    if parsed:
        month, day = parsed
        return f"{month:02d}-{day:02d}"
    if fallback_today:
        return datetime.now().strftime("%m-%d")
    return str(value or "").strip()


def _normalize_excel_write_payload(data):
    normalized = dict(data or {})
    normalized["consult_date"] = _normalize_excel_mmdd(normalized.get("consult_date", ""), fallback_today=True)
    normalized["second_date"] = _normalize_excel_mmdd(normalized.get("second_date", ""))
    normalized["deposit"] = _digits_only(normalized.get("deposit", ""))
    normalized["loan"] = _digits_only(normalized.get("loan", ""))
    for key in (
        "note",
        "first_consult",
        "second_consult",
        "customer_status",
        "name",
        "jumin",
        "address",
        "phone",
        "income",
        "excel_credit",
        "excel_kind",
        "display_bank",
    ):
        normalized[key] = str(normalized.get(key, "") or "").strip()
    return normalized


def _normalize_sheet_credit(value):
    raw = str(value or "").strip()
    if not raw:
        return "미확인"
    if raw == "회파복":
        return raw
    if any(token in raw for token in ("차주", "기존차주")):
        return "차주"
    if any(token in raw for token in ("정상", "신용정상")):
        return "정상"
    if any(token in raw for token in ("개인회생", "회생")):
        return "회생"
    if any(token in raw for token in ("신용회복", "회복")):
        return "회복"
    if any(token in raw for token in ("파산", "면책")):
        return "파산"
    if any(token in raw for token in ("신용관리", "신불", "연체", "채불", "채무불이행", "신용불량")):
        return "채불(신용이상)"
    return raw


def _build_excel_data_from_parsed(parsed):
    data = parsed or {}
    bank = _normalize_ixio_bank(str(data.get("접수", "") or "").strip())
    note = str(data.get("기타", "") or "").strip()
    income = str(data.get("직업", "") or "").strip() or "직장인"
    consult_date = _normalize_excel_mmdd(data.get("1차접수", ""), fallback_today=True)
    customer_status = str(data.get("고객상태", "") or "").strip() or "진행중(H)"
    return {
        "note": note,
        "first_consult": str(data.get("1차상담", "") or "").strip() or note,
        "second_consult": str(data.get("2차상담", "") or "").strip(),
        "consult_date": consult_date,
        "second_date": _normalize_excel_mmdd(data.get("2차접수", "")),
        "customer_status": customer_status,
        "name": str(data.get("이름", "") or "").strip(),
        "jumin": str(data.get("주민번호", "") or "").strip(),
        "address": str(data.get("주소", "") or "").strip(),
        "phone": str(data.get("연락처", "") or "").strip(),
        "deposit": _digits_only(data.get("보증금", "")),
        "loan": _digits_only(data.get("대출금", "")),
        "income": income,
        "excel_credit": _normalize_sheet_credit(data.get("신용", "")),
        "excel_kind": _normalize_ixio_excel_kind(data.get("종류", "")),
        "display_bank": _display_ixio_bank(bank),
    }


def _build_excel_data_from_text(raw_text):
    if common_parse_customer_text is None:
        return False, "공통 파서를 찾지 못했습니다."
    try:
        parsed = common_parse_customer_text(raw_text)
    except Exception as e:
        return False, f"고객 정보 파싱 실패: {e}"
    if not parsed:
        return False, "엑셀 입력용 고객 정보를 인식하지 못했습니다."
    return True, _build_excel_data_from_parsed(parsed)


def _build_excel_data_from_review_fields(fields, mode="ms"):
    current = dict(fields or {})
    bank = str(current.get("접수", "") or "").strip()
    if mode == "ms":
        bank = "MS저축은행"
    note = ""
    if mode == "ms":
        note = str(current.get("전송메모", "") or "").strip()
    else:
        note = str(current.get("기타", "") or "").strip()
    if not note:
        note = str(current.get("종류", "") or "").strip()
    return {
        "note": note,
        "first_consult": note,
        "second_consult": "",
        "consult_date": datetime.now().strftime("%m-%d"),
        "second_date": "",
        "customer_status": "진행중(H)",
        "name": str(current.get("이름", "") or "").strip(),
        "jumin": str(current.get("주민번호", "") or "").strip(),
        "address": str(current.get("주소", "") or "").strip(),
        "phone": str(current.get("연락처", "") or "").strip(),
        "deposit": _digits_only(current.get("보증금", "")),
        "loan": _digits_only(current.get("대출금", "")),
        "income": str(current.get("직업구분", "") or current.get("직업", "") or "").strip() or "직장인",
        "excel_credit": _normalize_sheet_credit(current.get("신용", "")),
        "excel_kind": _normalize_ixio_excel_kind(current.get("종류", "")),
        "display_bank": _display_ixio_bank(bank),
    }


def _parse_powershell_json_result(result):
    out = decode_output(result.stdout).strip()
    err = decode_output(result.stderr).strip()
    if not out:
        return False, err or "PowerShell 출력이 비어 있습니다."
    try:
        return True, json.loads(out)
    except Exception:
        return False, out or err or "JSON 파싱 실패"


def _inspect_excel_duplicates_by_jumin(jumin_text):
    target = _resolve_excel_target_path()
    if not target:
        searched = "\n".join(_excel_target_candidates())
        return False, f"통합관리 파일 경로를 찾지 못했습니다.\n후보 경로:\n{searched}"

    digits = re.sub(r"\D", "", str(jumin_text or ""))
    if not digits:
        return True, []

    ps_script = r"""
$ErrorActionPreference = 'Stop'
$target = $env:TG_EXCEL_TARGET
$baseName = $env:TG_EXCEL_BASENAME
$juminDigits = ($env:TG_EXCEL_JUMIN -replace '[^\d]', '')
$excel = $null
$wb = $null
$opened = $false
try {
  try { $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application') } catch {}
  if ($null -eq $excel) { $excel = New-Object -ComObject Excel.Application }
  foreach ($w in @($excel.Workbooks)) {
    if (($w.Name -ieq $baseName) -or ($w.FullName -ieq $target)) { $wb = $w; break }
  }
  if ($null -eq $wb) {
    if (-not (Test-Path -LiteralPath $target)) { throw 'FILE_NOT_FOUND' }
    $wb = $excel.Workbooks.Open($target)
    $opened = $true
  }
  $ws = $null
  try { $ws = $wb.Worksheets.Item('h') } catch {}
  if ($null -eq $ws) { try { $ws = $wb.Worksheets.Item('H') } catch {} }
  if ($null -eq $ws) { throw 'SHEET_NOT_FOUND:h' }

  $usedLast = $ws.UsedRange.Row + $ws.UsedRange.Rows.Count - 1
  if ($usedLast -lt 2) { $usedLast = 2 }
  $matches = @()
  for ($row = 2; $row -le $usedLast; $row++) {
    $cell = [string]$ws.Cells.Item($row, 7).Text
    $digits = ($cell -replace '[^\d]', '')
    if ($digits -and $digits -eq $juminDigits) {
      $matches += [pscustomobject]@{
        row = $row
        name = [string]$ws.Cells.Item($row, 6).Text
        customer_status = [string]$ws.Cells.Item($row, 5).Text
        first_consult = [string]$ws.Cells.Item($row, 2).Text
        bank = [string]$ws.Cells.Item($row, 15).Text
      }
    }
  }
  [pscustomobject]@{ ok = $true; read_only = [bool]$wb.ReadOnly; matches = $matches } | ConvertTo-Json -Depth 5 -Compress
}
catch {
  [pscustomobject]@{ ok = $false; error = $_.Exception.Message } | ConvertTo-Json -Compress
  exit 1
}
finally {
  if ($opened -and $null -ne $wb) { try { $wb.Close($false) } catch {} }
  if ($null -ne $excel) {
    try {
      if ($excel.Workbooks.Count -eq 0) { $excel.Quit() }
    } catch {}
  }
}
"""
    result = _run_powershell(
        ps_script,
        extra_env={
            "TG_EXCEL_TARGET": target,
            "TG_EXCEL_BASENAME": EXCEL_TARGET_BASENAME,
            "TG_EXCEL_JUMIN": digits,
        },
    )
    ok, payload = _parse_powershell_json_result(result)
    if not ok:
        return False, payload
    if not payload.get("ok"):
        return False, str(payload.get("error") or "중복 검사 실패")
    return True, {
        "read_only": bool(payload.get("read_only")),
        "matches": list(payload.get("matches") or []),
    }


def _append_ixio_row_to_excel(data):
    target = _resolve_excel_target_path()
    if not target:
        searched = "\n".join(_excel_target_candidates())
        return False, f"통합관리 파일 경로를 찾지 못했습니다.\n후보 경로:\n{searched}"

    row_values = _ixio_excel_row_values(data)
    ps_script = r"""
$ErrorActionPreference = 'Stop'
$target = $env:TG_EXCEL_TARGET
$baseName = $env:TG_EXCEL_BASENAME
$rowJson = $env:TG_EXCEL_ROW_JSON
$targetYear = [int]($env:TG_EXCEL_DATE_YEAR)
$values = ConvertFrom-Json $rowJson
$excel = $null
$wb = $null
$opened = $false

function Convert-ToTargetDate([string]$raw, [int]$year) {
  $text = [string]$raw
  if ([string]::IsNullOrWhiteSpace($text)) { return $null }
  $text = $text.Trim()
  $digits = ($text -replace '[^\d]', '')
  $month = $null
  $day = $null

  if ($text -match '^(\d{1,2})[-/.](\d{1,2})$') {
    $month = [int]$Matches[1]
    $day = [int]$Matches[2]
  } elseif ($text -match '^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$') {
    $month = [int]$Matches[2]
    $day = [int]$Matches[3]
  } elseif ($digits -match '^\d{4}$') {
    $month = [int]$digits.Substring(0, 2)
    $day = [int]$digits.Substring(2, 2)
  } elseif ($digits -match '^\d{8}$') {
    $month = [int]$digits.Substring(4, 2)
    $day = [int]$digits.Substring(6, 2)
  }

  if ($null -eq $month -or $null -eq $day) { return $null }
  try {
    return Get-Date -Year $year -Month $month -Day $day -Hour 0 -Minute 0 -Second 0
  } catch {
    return $null
  }
}

function Set-DateCellValue($cell, [string]$raw, [int]$year, [datetime]$today) {
  if ([string]::IsNullOrWhiteSpace([string]$raw)) {
    $cell.ClearContents()
    $cell.NumberFormat = 'mm-dd'
    $cell.Font.ColorIndex = -4105
    return
  }
  $dt = Convert-ToTargetDate $raw $year
  if ($null -eq $dt) {
    $cell.Value2 = $raw
    $cell.NumberFormat = '@'
    $cell.Font.ColorIndex = -4105
    return
  }
  $cell.Value2 = [double]$dt.ToOADate()
  $cell.NumberFormat = 'mm-dd'
  if ($dt.Date -le $today.Date) {
    $cell.Font.Color = 255
  } else {
    $cell.Font.ColorIndex = -4105
  }
}

try {
  try { $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application') } catch {}
  if ($null -eq $excel) { $excel = New-Object -ComObject Excel.Application }
  foreach ($w in @($excel.Workbooks)) {
    if (($w.Name -ieq $baseName) -or ($w.FullName -ieq $target)) { $wb = $w; break }
  }
  if ($null -eq $wb) {
    if (-not (Test-Path -LiteralPath $target)) { throw 'FILE_NOT_FOUND' }
    $wb = $excel.Workbooks.Open($target)
    $opened = $true
  }
  $ws = $null
  try { $ws = $wb.Worksheets.Item('h') } catch {}
  if ($null -eq $ws) { try { $ws = $wb.Worksheets.Item('H') } catch {} }
  if ($null -eq $ws) { throw 'SHEET_NOT_FOUND:h' }
  if ($wb.ReadOnly) { throw 'WORKBOOK_READ_ONLY' }

  $usedLast = $ws.UsedRange.Row + $ws.UsedRange.Rows.Count - 1
  if ($usedLast -lt 2) { $usedLast = 2 }
  $targetRow = $null
  for ($row = 2; $row -le ($usedLast + 1); $row++) {
    $nameText = [string]$ws.Cells.Item($row, 6).Text
    if ([string]::IsNullOrWhiteSpace($nameText)) {
      $targetRow = $row
      break
    }
  }
  if ($null -eq $targetRow) { $targetRow = $usedLast + 1 }
  $today = (Get-Date).Date

  for ($i = 0; $i -lt $values.Count; $i++) {
    $col = 2 + $i
    $raw = [string]$values[$i]
    $cell = $ws.Cells.Item($targetRow, $col)
    if ($col -in @(3, 4)) {
      Set-DateCellValue $cell $raw $targetYear $today
    } elseif ($col -in @(10, 11)) {
      $digits = ($raw -replace '[^\d]', '')
      if ($digits) {
        $cell.Value2 = [double]$digits
      } else {
        $cell.Value2 = $raw
      }
    } else {
      $cell.Value2 = $raw
    }
  }

  try { $wb.Save() } catch {}
  [pscustomobject]@{ ok = $true; row = $targetRow; path = $target } | ConvertTo-Json -Compress
}
catch {
  [pscustomobject]@{ ok = $false; error = $_.Exception.Message } | ConvertTo-Json -Compress
  exit 1
}
finally {
  if ($null -ne $excel) {
    try { $excel.Visible = $true } catch {}
  }
}
"""
    result = _run_powershell(
        ps_script,
        extra_env={
            "TG_EXCEL_TARGET": target,
            "TG_EXCEL_BASENAME": EXCEL_TARGET_BASENAME,
            "TG_EXCEL_DATE_YEAR": str(EXCEL_DATE_YEAR),
            "TG_EXCEL_ROW_JSON": json.dumps(row_values, ensure_ascii=False),
        },
    )
    ok, payload = _parse_powershell_json_result(result)
    if not ok:
        return False, payload
    if not payload.get("ok"):
        return False, str(payload.get("error") or "엑셀 입력 실패")
    row = payload.get("row")
    path = str(payload.get("path") or target)
    return True, f"h시트 {row}행에 입력했습니다.\n{path}"


def _format_ixio_duplicate_message(matches):
    lines = ["⚠️ h시트에 동일 주민번호 고객이 이미 있습니다."]
    for item in list(matches or [])[:5]:
        row = item.get("row")
        name = str(item.get("name") or "").strip() or "-"
        status = str(item.get("customer_status") or "").strip() or "-"
        bank = str(item.get("bank") or "").strip() or "-"
        consult = str(item.get("first_consult") or "").strip() or "-"
        lines.append(f"- {row}행 | {name} | {status} | {bank} | {consult}")
    if len(list(matches or [])) > 5:
        lines.append(f"- ... 외 {len(list(matches or [])) - 5}건")
    lines.append("")
    lines.append("그래도 새로 입력할까요?")
    lines.append("1. 예")
    lines.append("2. 아니오")
    lines.append("0. 초기화면")
    return "\n".join(lines)


def _build_ixio_admin_payload(data):
    fields = {
        "이름": str((data or {}).get("name", "") or "").strip(),
        "주민번호": str((data or {}).get("jumin", "") or "").strip(),
        "연락처": str((data or {}).get("phone", "") or "").strip(),
        "주소": str((data or {}).get("address", "") or "").strip(),
        "보증금": _normalize_ixio_amount((data or {}).get("deposit", "")),
        "대출금": _normalize_ixio_amount((data or {}).get("loan", "")),
        "접수": str((data or {}).get("bank", "") or (data or {}).get("display_bank", "") or "").strip(),
        "종류": str((data or {}).get("admin_kind", "") or "").strip(),
        "신용": str((data or {}).get("credit", "") or "").strip(),
        "직업구분": _normalize_ixio_income((data or {}).get("income", "")),
        "상품선택": "",
        "기타": str((data or {}).get("note", "") or "").strip(),
    }
    _recompute_admin_review_derived(fields)
    return _build_ms_payload_from_fields(fields, mode="admin")


def _send_ixio_action_menu(chat_id):
    global user_state
    user_state = 19
    bot.send_message(
        chat_id,
        (
            "원하는 작업을 선택하세요.\n"
            "1. 카톡접수용 복사하기\n"
            "2. admin접수하기\n"
            "3. 엑셀 통합관리 입력\n"
            "0. 초기화면"
        ),
    )


def _prompt_ixio_action_menu(chat_id, data):
    global user_state, pending_ixio_data, pending_ixio_duplicates
    pending_ixio_data = dict(data or {})
    pending_ixio_duplicates = []
    _send_ixio_action_menu(chat_id)


def _prompt_excel_customer_input(chat_id):
    global user_state
    user_state = 21
    bot.send_message(
        chat_id,
        (
            "📝 [엑셀 고객입력]\n"
            "통합관리 h시트에 넣을 고객 정보를 붙여넣어 주세요.\n"
            "지원 형식: 카톡 고객정보 / admin 라벨형 / 엑셀 한 줄\n"
            "입력 후 주민번호 중복 확인 뒤 바로 엑셀 입력을 진행합니다.\n"
            "0. 초기화면"
        ),
    )


def _prompt_pending_followup(chat_id):
    global user_state, pending_followup_option
    _cancel_auto_timer(chat_id)

    kind = pending_followup_kind
    name = pending_followup_name or _extract_name_from_text(pending_followup_text)
    option = pending_followup_option or "1"

    if kind == "ms":
        if option in {"1", "2", "3", "4"}:
            label = _ms_option_to_label(option)
            limit_kind = "복합한도" if _ms_option_limit_type(option) == "복합" else "일반한도"
        else:
            option, label, limit_kind = infer_ms_product_preview(pending_followup_text or "")
            pending_followup_option = option
        user_state = 11
        bot.send_message(
            chat_id,
            (
                "2. ms신규접수.py\n"
                f"고객명: {name}\n"
                f"대출유형: {label} ({limit_kind})\n"
                "진행할까요?\n"
                "1. 예\n"
                "2. 아니오\n"
                "3. 엑셀 통합관리 입력\n"
                "0. 초기화면\n"
                f"({AUTO_PROGRESS_SECONDS}초 무응답 시 자동 진행)"
            ),
        )
        _arm_auto_timer(chat_id, AUTO_PROGRESS_SECONDS, 11, lambda: _execute_ms_followup(chat_id, auto_trigger=True))
        return

    if kind == "kiwoom":
        if option not in {"1", "2", "3", "4"}:
            option = detect_loan_option(pending_followup_text or "") or "1"
            pending_followup_option = option
        label = _kiwoom_option_label(option)
        user_state = 12
        bot.send_message(
            chat_id,
            (
                "4. 키움신규접수.py\n"
                f"고객명: {name}\n"
                f"대출유형: {label}\n"
                "진행할까요?\n"
                "1. 예\n"
                "2. 아니오\n"
                "3. 엑셀 통합관리 입력\n"
                "0. 초기화면\n"
                f"({AUTO_PROGRESS_SECONDS}초 무응답 시 자동 진행)"
            ),
        )
        _arm_auto_timer(chat_id, AUTO_PROGRESS_SECONDS, 12, lambda: _execute_kiwoom_followup(chat_id, auto_trigger=True))
        return

    user_state = 0
    bot.send_message(chat_id, show_list())


def _format_excel_field_summary(data):
    values = {
        "1차상담": str((data or {}).get("first_consult", "") or (data or {}).get("note", "") or "").strip(),
        "1차접수": str((data or {}).get("consult_date", "") or "").strip(),
        "2차접수": str((data or {}).get("second_date", "") or "").strip(),
        "고객상태": str((data or {}).get("customer_status", "") or "").strip(),
        "이름": str((data or {}).get("name", "") or "").strip(),
        "주민": str((data or {}).get("jumin", "") or "").strip(),
        "주소": str((data or {}).get("address", "") or "").strip(),
        "연락처": str((data or {}).get("phone", "") or "").strip(),
        "보증금": str((data or {}).get("deposit", "") or "").strip(),
        "대출금": str((data or {}).get("loan", "") or "").strip(),
        "소득": str((data or {}).get("income", "") or "").strip(),
        "신용상태": str((data or {}).get("excel_credit", "") or "").strip(),
        "종류": str((data or {}).get("excel_kind", "") or "").strip(),
        "은행": str((data or {}).get("display_bank", "") or "").strip(),
        "영업자": "정",
    }
    lines = ["🧾 [엑셀 입력값 확인]"]
    for idx, key in enumerate(values.keys(), 1):
        value = values[key] or "(비어있음)"
        lines.append(f"{idx}. {key}: {value}")
    lines.extend(["", "그대로 할까요?", "1. 예", "2. 수정", "0. 초기화면"])
    return "\n".join(lines)


def _resume_after_excel(chat_id, notice=""):
    global user_state
    resume = pending_excel_resume
    _clear_pending_excel()
    if notice:
        bot.send_message(chat_id, notice)

    if resume == "ixio":
        _send_ixio_action_menu(chat_id)
        return
    if resume == "review":
        user_state = 13
        bot.send_message(chat_id, _format_ms_field_summary(pending_ms_fields, mode=(pending_ms_mode or "ms")))
        return
    if resume in {"followup_ms", "followup_kiwoom"}:
        _prompt_pending_followup(chat_id)
        return

    user_state = 0
    bot.send_message(chat_id, show_list())


def _start_excel_write_flow(chat_id, excel_data, resume="list"):
    global pending_excel_data, pending_excel_resume, user_state
    pending_excel_data = _normalize_excel_write_payload(excel_data)
    pending_excel_resume = resume
    user_state = 22
    bot.send_message(chat_id, _format_excel_field_summary(pending_excel_data))
    return


def _execute_excel_write_flow(chat_id, skip_duplicate_check=False):
    _start_excel_write_background(chat_id, skip_duplicate_check=skip_duplicate_check)


def _prepare_excel_write_background(chat_id, skip_duplicate_check=False):
    def _prepare():
        global user_state
        if not pending_excel_data:
            user_state = 0
            return None
        user_state = EXCEL_WRITE_RUNNING_STATE
        return {
            "data": dict(pending_excel_data or {}),
            "skip_duplicate_check": bool(skip_duplicate_check),
        }
    return _run_in_chat_session(chat_id, _prepare)


def _show_excel_duplicate_prompt_background(chat_id, matches):
    def _commit():
        global user_state
        if user_state != EXCEL_WRITE_RUNNING_STATE:
            return False
        user_state = 20
        bot.send_message(chat_id, _format_ixio_duplicate_message(matches))
        return True
    return _run_in_chat_session(chat_id, _commit)


def _resume_after_excel_background(chat_id, notice=""):
    def _commit():
        if user_state != EXCEL_WRITE_RUNNING_STATE:
            return False
        _resume_after_excel(chat_id, notice)
        return True
    return _run_in_chat_session(chat_id, _commit)


def _run_excel_write_flow_background(chat_id, excel_data, skip_duplicate_check=False):
    if not skip_duplicate_check:
        ok, payload = _inspect_excel_duplicates_by_jumin((excel_data or {}).get("jumin", ""))
        if not ok:
            _resume_after_excel_background(chat_id, f"❌ 엑셀 중복 확인 실패\n{payload}")
            return

        if bool((payload or {}).get("read_only")):
            _resume_after_excel_background(
                chat_id,
                (
                    "⚠️ 통합관리.xlsm 이 읽기 전용으로 열려 있습니다.\n"
                    "집이나 다른 PC에서 같은 파일을 열어 둔 상태일 수 있습니다.\n"
                    "사무실 PC에서 쓰기 가능한 상태인지 확인한 뒤 다시 시도해 주세요."
                ),
            )
            return

        matches = list((payload or {}).get("matches") or [])
        if matches:
            _show_excel_duplicate_prompt_background(chat_id, matches)
            return

    ok, msg = _append_ixio_row_to_excel(excel_data or {})
    _resume_after_excel_background(chat_id, f"{'✅' if ok else '❌'} {msg}")


def _start_excel_write_background(chat_id, skip_duplicate_check=False):
    snapshot = _prepare_excel_write_background(chat_id, skip_duplicate_check=skip_duplicate_check)
    if not snapshot:
        bot.send_message(chat_id, show_list())
        return
    bot.send_message(chat_id, "💾 엑셀 입력을 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    _start_background_task(
        chat_id,
        "엑셀 입력",
        _run_excel_write_flow_background,
        chat_id,
        snapshot.get("data") or {},
        bool(snapshot.get("skip_duplicate_check")),
    )

def script_path(filename):
    return os.path.join(BASE_DIR, filename)


def _dedupe_paths(paths):
    seen = set()
    ordered = []
    for path in paths:
        if not path:
            continue
        norm = os.path.normcase(os.path.abspath(path))
        if norm in seen:
            continue
        seen.add(norm)
        ordered.append(path)
    return ordered


def _script_search_roots():
    roots = [
        os.environ.get("BOT_SCRIPT_DIR", ""),
        os.path.join(BASE_DIR, "projects", "03_telegram_py"),
        os.path.join(BASE_DIR, "projects", "03_telegram_py", "admin"),
        os.path.join(BASE_DIR, "projects", "admin"),
        BASE_DIR,
        os.path.join(BASE_DIR, "03_telegram_py"),
        os.path.join(BASE_DIR, "admin"),
        os.path.join(BASE_DIR, "03_telegram_py", "admin"),
        SCRIPT_DIR,
        os.path.join(SCRIPT_DIR, "admin"),
    ]
    return [path for path in _dedupe_paths(roots) if os.path.isdir(path)]


def _script_candidate_paths(filename):
    if not filename:
        return []
    if os.path.isabs(filename):
        return [filename]
    return [os.path.join(root, filename) for root in _script_search_roots()]


def _walk_for_script(filename, max_depth=3):
    target = (filename or "").lower()
    if not target:
        return ""
    for root in _script_search_roots():
        base_depth = root.rstrip("\\/").count(os.sep)
        try:
            for current_root, dirnames, filenames in os.walk(root):
                depth = current_root.rstrip("\\/").count(os.sep) - base_depth
                if depth >= max_depth:
                    dirnames[:] = []
                for found in filenames:
                    if found.lower() == target:
                        return os.path.join(current_root, found)
        except Exception:
            continue
    return ""


def resolve_script_path(filename):
    cached = SCRIPT_SEARCH_CACHE.get(filename)
    if cached is not None:
        if cached and os.path.exists(cached):
            return cached
        if not cached:
            miss_until = SCRIPT_SEARCH_MISS_CACHE.get(filename, 0)
            if miss_until > time.monotonic():
                return ""
        SCRIPT_SEARCH_CACHE.pop(filename, None)
        SCRIPT_SEARCH_MISS_CACHE.pop(filename, None)

    for candidate in _script_candidate_paths(filename):
        if os.path.exists(candidate):
            SCRIPT_SEARCH_CACHE[filename] = candidate
            SCRIPT_SEARCH_MISS_CACHE.pop(filename, None)
            return candidate

    walked = _walk_for_script(filename)
    if walked and os.path.exists(walked):
        SCRIPT_SEARCH_CACHE[filename] = walked
        SCRIPT_SEARCH_MISS_CACHE.pop(filename, None)
        return walked

    # Missing files are common in menu/status checks, so cache misses briefly.
    SCRIPT_SEARCH_CACHE[filename] = ""
    SCRIPT_SEARCH_MISS_CACHE[filename] = time.monotonic() + SCRIPT_SEARCH_MISS_TTL_SECONDS
    return ""


def format_script_search_message(filename):
    lines = [f"❌ 파일을 찾지 못했습니다: {filename}", "검색 경로:"]
    for path in _script_search_roots():
        lines.append(f"- {path}")
    return "\n".join(lines)


def resolve_runtime_path(filename):
    return resolve_script_path(filename)


def _is_ms_consent_maintenance_mode():
    script_path = resolve_script_path("ms신용조회동의.py")
    if not script_path:
        return False
    try:
        with open(script_path, "r", encoding="utf-8") as handle:
            head = handle.read(256)
    except Exception:
        return False
    return "Temporary maintenance stub" in head


def _menu_status_suffix(required_files):
    for name in required_files:
        if not resolve_script_path(name):
            return " [파일없음]"
    return ""


def _ms_consent_menu_suffix():
    path = resolve_script_path("ms신용조회동의.py")
    if not path:
        return " [파일없음]"
    return " [점검중]" if _is_ms_consent_maintenance_mode() else ""


def _format_ms_consent_unavailable_message():
    return (
        "⚠️ MS신용조회동의는 현재 점검용 스텁 상태입니다.\n"
        "`ms신용조회동의.py` 파일은 있지만 실제 브라우저 자동화는 꺼져 있습니다.\n"
        "대체 경로:\n"
        "1) Gentry에서 신용조회동의를 수동 처리\n"
        "2) 처리 후 필요하면 6번(MS결과확인)으로 고객명 조회\n"
        "3) 자동화 복구가 필요하면 `ms신용조회동의.py` 신규 구현이 필요합니다."
    )




def _prime_menu_status_cache():
    for name in (
        "admin접수.py",
        "ms신규접수.py",
        "ms신용조회동의.py",
        "키움신규접수.py",
        "MS결과확인.py",
        "키움결과확인.py",
    ):
        resolve_script_path(name)


def _read_secret_file(filename):
    return read_secret_text(
        filename,
        base_dir=BASE_DIR,
        script_dir=BOT_SCRIPT_DIR,
        root_dir=BASE_DIR,
    )


def _read_text_file(path):
    return read_text_file(path)


def _read_runtime_file(filename):
    return _read_text_file(_runtime_state_path(filename))


def _load_ixio_system_prompt():
    return IXIO_FALLBACK_SYSTEM_PROMPT


def _first_nonempty_line(text):
    return first_nonempty_line(text)


def _runtime_state_path(filename):
    if not filename:
        return BASE_DIR
    if BOT_PROFILE == "office" and filename in {
        "bot_token.txt",
        "allowed_chat_ids.txt",
        "office_allowed_hosts.txt",
    }:
        return resolve_secret_file_path(
            filename,
            base_dir=BASE_DIR,
            script_dir=BOT_SCRIPT_DIR,
            root_dir=BASE_DIR,
        )
    return script_path(filename)


def _load_bot_token():
    return load_bot_token(
        env_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        runtime_text=_read_runtime_file("bot_token.txt"),
        secret_text=_read_secret_file("bot_token.txt"),
    )


def _parse_name_list(raw, *, default=None):
    return parse_name_list(raw, default=default)


def _get_current_hostname():
    for key in ("COMPUTERNAME", "HOSTNAME"):
        value = (os.environ.get(key) or "").strip()
        if value:
            return value
    try:
        return socket.gethostname().strip()
    except Exception:
        return ""


def _parse_allowed_chat_ids(raw):
    return parse_allowed_chat_ids(raw)


def _load_allowed_chat_ids():
    return load_allowed_chat_ids(
        env_chat_ids=os.environ.get("TELEGRAM_CHAT_IDS", ""),
        env_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
        runtime_raw=_read_runtime_file("allowed_chat_ids.txt"),
        secret_raw=_read_secret_file("allowed_chat_ids.txt"),
        require_runtime_allowed_chat_ids=BOT_REQUIRE_RUNTIME_ALLOWED_CHAT_IDS,
    )


def _load_allowed_hostnames():
    return load_allowed_hostnames(
        os.environ.get("BOT_ALLOWED_HOSTS", ""),
        os.environ.get("OFFICE_ALLOWED_HOSTS", ""),
        _read_runtime_file("office_allowed_hosts.txt"),
        _read_secret_file("office_allowed_hosts.txt"),
    )


def _write_json_payload(path, payload):
    write_json_payload(path, payload)


def _ensure_runtime_dirs():
    ensure_runtime_dirs(BASE_DIR, BOT_RUNTIME_DIR, BOT_STATE_DIR, BOT_LOG_DIR, BOT_LOCK_DIR)


def _write_pid_file():
    write_pid_file(
        BOT_PID_FILE,
        runtime_dirs=(BASE_DIR, BOT_RUNTIME_DIR, BOT_STATE_DIR, BOT_LOG_DIR, BOT_LOCK_DIR),
        pid=os.getpid(),
    )


def _cleanup_runtime_identity_files():
    cleanup_runtime_identity_files(BOT_PID_FILE, BOT_LOCK_FILE, pid=os.getpid())


def _write_runtime_status(status, detail="", **extra):
    status_extra = {"ivwith_menu34_base_dir": IVWITH_MENU34_BASE_DIR, **extra}
    payload = build_runtime_status_payload(
        status=status,
        detail=detail,
        base_dir=BASE_DIR,
        runtime_dir=BOT_RUNTIME_DIR,
        state_dir=BOT_STATE_DIR,
        bot_profile=BOT_PROFILE,
        python_exe=PYTHON_EXE,
        bot_version=BOT_VERSION,
        host=_get_current_hostname().upper() or "UNKNOWN",
        office_host_enforced=BOT_ENFORCE_OFFICE_HOST,
        allowed_chat_count=len(ALLOWED_CHAT_IDS or []),
        pid_file=BOT_PID_FILE,
        lock_dir=BOT_LOCK_DIR,
        lock_file=BOT_LOCK_FILE,
        pid=os.getpid(),
        extra=status_extra,
    )
    with RUNTIME_STATUS_LOCK:
        RUNTIME_STATUS_CACHE["status"] = payload["status"]
        RUNTIME_STATUS_CACHE["detail"] = payload["detail"]
        RUNTIME_STATUS_CACHE["extra"] = dict(status_extra)
    _write_json_payload(BOT_RUNTIME_STATUS_FILE, payload)
    return payload


def _load_runtime_status():
    return load_runtime_status(BOT_RUNTIME_STATUS_FILE)


def _write_runtime_heartbeat():
    with RUNTIME_STATUS_LOCK:
        status = str(RUNTIME_STATUS_CACHE.get("status") or "").strip() or "unknown"
        detail = str(RUNTIME_STATUS_CACHE.get("detail") or "").strip()

    payload = build_runtime_heartbeat_payload(
        status=status,
        detail=detail,
        lock_port=BOT_LOCK_PORT,
        base_dir=BASE_DIR,
        runtime_dir=BOT_RUNTIME_DIR,
        state_dir=BOT_STATE_DIR,
        bot_profile=BOT_PROFILE,
        pid_file=BOT_PID_FILE,
        lock_file=BOT_LOCK_FILE,
        python_exe=PYTHON_EXE,
        bot_version=BOT_VERSION,
        host=_get_current_hostname().upper() or "UNKNOWN",
        pid=os.getpid(),
        extra={"ivwith_menu34_base_dir": IVWITH_MENU34_BASE_DIR},
    )
    _write_json_payload(BOT_HEARTBEAT_FILE, payload)
    return payload


def _runtime_heartbeat_loop():
    while True:
        try:
            _write_runtime_heartbeat()
        except Exception:
            pass
        time.sleep(BOT_HEARTBEAT_INTERVAL_SEC)


def _save_allowed_chat_ids():
    path = _runtime_state_path("allowed_chat_ids.txt")
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    payload = "\n".join(str(chat_id) for chat_id in sorted(ALLOWED_CHAT_IDS))
    with open(path, "w", encoding="utf-8") as f:
        if payload:
            f.write(payload + "\n")
        else:
            f.write("")


def _remember_allowed_chat_id(chat_id):
    try:
        normalized = int(chat_id)
    except Exception:
        return False
    if normalized in ALLOWED_CHAT_IDS:
        return True
    ALLOWED_CHAT_IDS.add(normalized)
    _save_allowed_chat_ids()
    return True


def _enforce_office_host():
    if not BOT_ENFORCE_OFFICE_HOST:
        return
    current_host = _get_current_hostname().upper()
    allowed_hosts = _load_allowed_hostnames()
    if not allowed_hosts:
        _write_runtime_status(
            "fatal_office_host",
            "office_allowed_hosts.txt 또는 BOT_ALLOWED_HOSTS 설정이 없습니다.",
            exit_code=2,
            allowed_hosts=[],
        )
        raise SystemExit(
            "office_allowed_hosts.txt 또는 BOT_ALLOWED_HOSTS 설정이 없습니다. "
            "사무실 PC에서 office_recover_and_check.ps1 또는 START_TELEGRAM_BOT_NOW.bat 를 먼저 실행하세요."
        )
    if current_host not in allowed_hosts:
        allowed_text = ", ".join(allowed_hosts)
        _write_runtime_status(
            "fatal_office_host",
            f"허용되지 않은 호스트: {current_host}",
            exit_code=3,
            allowed_hosts=allowed_hosts,
        )
        raise SystemExit(
            f"이 PC({current_host or 'UNKNOWN'})는 텔레그램 봇 실행 허용 대상이 아닙니다. "
            f"허용 호스트: {allowed_text}"
        )


def _load_anthropic_api_key():
    for env_name in ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"):
        value = (os.environ.get(env_name) or "").strip()
        if value:
            return value
    for filename in IXIO_API_KEY_FILES:
        value = _read_runtime_file(filename) or _read_secret_file(filename)
        value = (value or "").strip()
        if value:
            return value.splitlines()[0].strip()
    return ""


def _load_anthropic_model():
    for env_name in ("ANTHROPIC_MODEL", "CLAUDE_MODEL"):
        value = (os.environ.get(env_name) or "").strip()
        if value:
            return value
    for filename in IXIO_MODEL_FILES:
        value = (_read_runtime_file(filename) or "").strip()
        if value:
            return value.splitlines()[0].strip()
    return IXIO_DEFAULT_MODEL


TOKEN = _load_bot_token()
if not TOKEN:
    _write_runtime_status("fatal_config", "TELEGRAM_BOT_TOKEN 또는 bot_token.txt 설정이 없습니다.", exit_code=4)
    raise SystemExit("TELEGRAM_BOT_TOKEN 또는 bot_token.txt 설정이 없습니다.")

_enforce_office_host()
ALLOWED_CHAT_IDS = _load_allowed_chat_ids()
if BOT_REQUIRE_RUNTIME_ALLOWED_CHAT_IDS and not ALLOWED_CHAT_IDS:
    _write_runtime_status(
        "fatal_config",
        "codex bot runtime allowed_chat_ids.txt 가 없거나 비어 있습니다.",
        exit_code=5,
        required_runtime_file=_runtime_state_path("allowed_chat_ids.txt"),
        bot_profile=BOT_PROFILE,
    )
    raise SystemExit("codex bot runtime allowed_chat_ids.txt 가 없거나 비어 있습니다.")
bot = telebot.TeleBot(TOKEN, skip_pending=True, threaded=True, num_threads=4)
def _detect_bot_username():
    override = (os.environ.get("BOT_USERNAME_OVERRIDE") or "").strip().lstrip("@").lower()
    actual = ""
    try:
        me = bot.get_me()
        actual = (getattr(me, "username", "") or "").strip().lstrip("@").lower()
    except Exception:
        actual = ""
    if override and actual and override != actual:
        _write_runtime_status(
            "fatal_config",
            "BOT_USERNAME_OVERRIDE와 실제 Telegram bot username이 일치하지 않습니다.",
            exit_code=6,
            bot_profile=BOT_PROFILE,
            requested_bot_username=override,
            actual_bot_username=actual,
        )
        raise SystemExit(
            f"bot username override mismatch: requested={override} actual={actual}"
        )
    if actual:
        return actual
    if override:
        return override
    return ""


BOT_USERNAME = _detect_bot_username()
OPENCLAW_HANDLER_BOT_USERNAMES = _parse_name_list(
    os.environ.get("OPENCLAW_HANDLER_BOT_USERNAMES", ""),
    default=("ofcgptcoder_bot",),
)
OPENCLAW_HANDLER_ENABLED = bool(BOT_USERNAME and BOT_USERNAME in OPENCLAW_HANDLER_BOT_USERNAMES)
_write_runtime_status(
    "startup_ready",
    "설정 로드 완료",
    allowed_chat_count=len(ALLOWED_CHAT_IDS),
    allowed_hosts=_load_allowed_hostnames(),
    bot_username=BOT_USERNAME,
    openclaw_handler_enabled=OPENCLAW_HANDLER_ENABLED,
)


CHAT_SESSION_FIELDS = (
    "user_state",
    "file_list",
    "target_script",
    "auto_script",
    "pending_new_text",
    "pending_new_script",
    "pending_amount_text",
    "pending_amount_script",
    "pending_amount_state",
    "pending_admin_text",
    "pending_admin_bank",
    "pending_admin_name",
    "pending_followup_text",
    "pending_followup_name",
    "pending_followup_kind",
    "pending_followup_option",
    "pending_ivwith_report_type",
    "pending_ms_script",
    "pending_ms_fields",
    "pending_ms_lines",
    "pending_ms_edit_key",
    "pending_ms_mode",
    "pending_rt_months",
    "pending_rt_print_history",
    "pending_ixio_data",
    "pending_ixio_duplicates",
    "pending_excel_data",
    "pending_excel_resume",
    "pending_ivwith_sales_key",
    "pending_ivwith_sales_display",
    "_briefing_cached_rows",
    "_briefing_classified",
)

CHAT_SESSIONS = {}
CHAT_STATE_LOCK = threading.RLock()
URGENT_RESET_TEXTS = {"0", "00", "취소"}
OPENCLAW_REDIRECT_LOCKS = {}
OPENCLAW_REDIRECT_TTL_SEC = 180


def _new_chat_session():
    return build_default_chat_session(resolve_script_path)


def _copy_session_value(value):
    return copy_session_value(value)


def _get_chat_session(chat_id):
    return get_chat_session(CHAT_SESSIONS, chat_id, _new_chat_session)


def _load_chat_session(chat_id):
    load_chat_session(CHAT_SESSIONS, chat_id, CHAT_SESSION_FIELDS, globals(), _new_chat_session)


def _save_chat_session(chat_id):
    save_chat_session(CHAT_SESSIONS, chat_id, CHAT_SESSION_FIELDS, globals(), _new_chat_session)


def _run_in_chat_session(chat_id, func, *args, **kwargs):
    return run_in_chat_session(
        CHAT_STATE_LOCK,
        CHAT_SESSIONS,
        chat_id,
        CHAT_SESSION_FIELDS,
        globals(),
        _new_chat_session,
        func,
        *args,
        **kwargs,
    )


def _mark_openclaw_redirect(chat_id):
    mark_openclaw_redirect(OPENCLAW_REDIRECT_LOCKS, chat_id, OPENCLAW_REDIRECT_TTL_SEC, now=time.time)


def _clear_openclaw_redirect(chat_id):
    clear_openclaw_redirect(OPENCLAW_REDIRECT_LOCKS, chat_id)


def _has_openclaw_redirect(chat_id):
    return has_openclaw_redirect(OPENCLAW_REDIRECT_LOCKS, chat_id, now=time.time)


def _with_chat_session_arg(index=0):
    return with_chat_session_arg(
        CHAT_STATE_LOCK,
        CHAT_SESSIONS,
        CHAT_SESSION_FIELDS,
        globals(),
        _new_chat_session,
        index=index,
    )


def _with_message_chat_session(func):
    return with_message_chat_session(
        CHAT_STATE_LOCK,
        CHAT_SESSIONS,
        CHAT_SESSION_FIELDS,
        globals(),
        _new_chat_session,
        func,
    )


def _acquire_single_instance_guard():
    global BOT_INSTANCE_GUARD
    BOT_INSTANCE_GUARD = acquire_single_instance_guard(
        BOT_INSTANCE_GUARD,
        socket_module=socket,
        port=BOT_LOCK_PORT,
        before_acquire=_ensure_runtime_dirs,
        on_acquired=lambda _sock: _write_json_payload(
            BOT_LOCK_FILE,
            {
                "pid": os.getpid(),
                "lock_port": BOT_LOCK_PORT,
                "base_dir": BASE_DIR,
                "bot_profile": BOT_PROFILE,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        ),
    )


def _is_ixio_text(text):
    source = (text or "").strip()
    return any(source.startswith(prefix) for prefix in IXIO_TRIGGER_PREFIXES)


def _strip_markdown_fence(text):
    lines = (text or "").strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
        return "\n".join(lines[1:-1]).strip()
    return (text or "").strip()


def _extract_anthropic_text(payload):
    parts = []
    for item in payload.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            chunk = (item.get("text") or "").strip()
            if chunk:
                parts.append(chunk)
    return "\n".join(parts).strip()


def _extract_json_object(text):
    source = _strip_markdown_fence(text)
    match = re.search(r"\{.*\}", source, re.S)
    if not match:
        raise ValueError("JSON 객체를 찾지 못했습니다.")
    return json.loads(match.group(0))


def _normalize_ixio_date(value):
    return _normalize_excel_mmdd(value, fallback_today=True)


def _normalize_ixio_amount(value):
    digits = re.sub(r"\D", "", str(value or ""))
    return digits or str(value or "").strip()


def _normalize_ixio_bank(value):
    raw = str(value or "").strip()
    if raw == "키움민간":
        return "키움(민간)"
    if raw == "MS":
        return "MS저축은행"
    normalized = _normalize_admin_bank(raw)
    return normalized or raw


def _display_ixio_bank(value):
    bank = _normalize_ixio_bank(value)
    if bank == "키움(민간)":
        return "키움민간"
    if bank == "MS저축은행":
        return "MS"
    return bank


def _normalize_ixio_income(value):
    raw = str(value or "").strip()
    if not raw:
        return "직장인"
    if any(token in raw for token in ("직장", "직장인", "건강보험")):
        return "직장인"
    if any(token in raw for token in ("프리랜서", "프리")):
        return "프리랜서"
    if any(token in raw for token in ("자영", "사업")):
        return "자영/사업"
    if "주부" in raw:
        return "주부"
    return raw


def _normalize_ixio_credit(value):
    raw = str(value or "").strip()
    if not raw:
        return "신용정상"
    if raw in {"회파복", "신용관리", "신용정상", "개인회생", "신용회복", "파산면책"}:
        return raw
    if any(token in raw for token in ("개인회생", "회생", "신용회복", "회복", "파산", "면책")):
        return "회파복"
    if any(token in raw for token in ("신용관리", "신불", "연체", "채불")):
        return "신용관리"
    return "신용정상"


def _normalize_ixio_excel_credit(value):
    credit = _normalize_ixio_credit(value)
    if credit == "신용정상":
        return "정상"
    if credit in {"개인회생", "신용회복", "파산면책", "회파복"}:
        return "회파복"
    if credit == "신용관리":
        return "신용관리"
    return credit or "정상"


def _normalize_ixio_excel_kind(value):
    raw = str(value or "").strip()
    if not raw:
        return "가계"
    if "계잔금" in raw or "계약잔금" in raw:
        return "계잔금"
    if "대환" in raw:
        return "대환"
    if "잔금" in raw or "입주" in raw:
        return "잔금"
    return "가계"


def _normalize_ixio_note(value):
    text = str(value or "").strip()
    text = re.sub(r"\s*[/|]+\s*", "/", text)
    return text.strip("/")


def _normalize_ixio_payload(payload):
    raw = dict(payload or {})
    bank = _normalize_ixio_bank(raw.get("bank", ""))
    display_bank = _display_ixio_bank(bank)
    credit = _normalize_ixio_credit(raw.get("credit", ""))
    income = _normalize_ixio_income(raw.get("income", ""))
    excel_kind = _normalize_ixio_excel_kind(raw.get("excel_kind") or raw.get("kakao_kind") or raw.get("admin_kind"))
    consult_date = _normalize_ixio_date(raw.get("consult_date", ""))
    intake_date = _normalize_ixio_date(raw.get("intake_date", consult_date))
    note = _normalize_ixio_note(raw.get("note", ""))
    stage = str(raw.get("stage", "") or "").strip() or "심사중"
    customer_status = str(raw.get("customer_status", "") or "").strip() or "진행중(H)"
    kakao_kind = str(raw.get("kakao_kind", "") or "").strip() or excel_kind

    admin_fields = {
        "접수": bank,
        "종류": str(raw.get("admin_kind", "") or raw.get("excel_kind", "") or raw.get("kakao_kind", "")).strip(),
        "신용": credit,
        "직업구분": income,
        "보증금": _normalize_ixio_amount(raw.get("deposit", "")),
        "대출금": _normalize_ixio_amount(raw.get("loan", "")),
    }
    _recompute_admin_review_derived(admin_fields)

    return {
        "name": str(raw.get("name", "") or "").strip(),
        "jumin": str(raw.get("jumin", "") or "").strip(),
        "phone": str(raw.get("phone", "") or "").strip(),
        "address": str(raw.get("address", "") or "").strip(),
        "deposit": _normalize_ixio_amount(raw.get("deposit", "")),
        "loan": _normalize_ixio_amount(raw.get("loan", "")),
        "bank": bank,
        "display_bank": display_bank,
        "kakao_kind": kakao_kind,
        "admin_kind": str(admin_fields.get("종류", "") or "").strip() or excel_kind,
        "income": income,
        "credit": str(admin_fields.get("신용", "") or credit).strip() or "신용정상",
        "excel_credit": _normalize_ixio_excel_credit(credit),
        "excel_kind": excel_kind,
        "note": note,
        "consult_date": consult_date,
        "intake_date": intake_date,
        "stage": stage,
        "customer_status": customer_status,
    }


def _format_ixio_kakao_message(data):
    lines = [
        f"1. 이름: {data['name']}",
        f"2. 주민번호: {data['jumin']}",
        f"3. 연락처: {data['phone']}",
        f"4. 주소: {data['address']}",
        f"5. 보증금: {data['deposit']}",
        f"6. 대출금: {data['loan']}",
        f"7. 접수: {data['display_bank']}",
        f"8. 종류: {data['kakao_kind']}",
        f"9. 신용: {data['credit']}",
        f"10. 기타: {data['note']}",
        "",
        f"접수은행: {data['display_bank']}",
    ]
    return "\n".join(lines).strip()


def _format_ixio_admin_message(data):
    lines = [
        f"1. 이름: {data['name']}",
        f"2. 주민번호: {data['jumin']}",
        f"3. 연락처: {data['phone']}",
        f"4. 주소: {data['address']}",
        f"5. 보증금: {data['deposit']}",
        f"6. 대출금: {data['loan']}",
        f"7. 접수: {data['display_bank']}",
        f"8. 종류: {data['admin_kind']}",
        f"9. 신용: {data['credit']}",
        f"10. 기타: {data['note']}",
        "",
        f"접수은행: {data['display_bank']}",
    ]
    return "\n".join(lines).strip()


def _format_ixio_excel_message(data):
    row = "\t".join(
        [
            "",
            data["note"],
            data["consult_date"],
            "",
            data["customer_status"],
            data["name"],
            data["jumin"],
            data["address"],
            data["phone"],
            data["deposit"],
            data["loan"],
            data["income"],
            data["excel_credit"],
            data["excel_kind"],
            data["display_bank"],
            "정",
        ]
    )
    return row


def _ixio_menu_status_suffix():
    if not _load_anthropic_api_key():
        return " [API키없음]"
    return ""


def summarize_ixio_with_claude(source_text):
    api_key = _load_anthropic_api_key()
    if not api_key:
        return False, (
            "Claude API 키가 없습니다.\n"
            "설정 방법: ANTHROPIC_API_KEY 환경변수 또는 anthropic_api_key.txt 파일"
        )

    payload = {
        "model": _load_anthropic_model(),
        "max_tokens": 2500,
        "temperature": 0.2,
        "system": _load_ixio_system_prompt(),
        "messages": [
            {
                "role": "user",
                "content": source_text,
            }
        ],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        parsed = json.loads(raw)
        text = _extract_anthropic_text(parsed)
        if not text:
            return False, "Claude 응답이 비어 있습니다."
        return True, _normalize_ixio_payload(_extract_json_object(text))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return False, f"Claude API 호출 실패 (HTTP {e.code})\n{body[:800]}".strip()
    except Exception as e:
        return False, f"Claude 호출 오류: {e}"


def _call_anthropic_messages(system_prompt, messages, max_tokens=1400, temperature=0.3):
    api_key = _load_anthropic_api_key()
    if not api_key:
        return False, (
            "Claude API 키가 없습니다.\n"
            "설정 방법: ANTHROPIC_API_KEY 환경변수 또는 anthropic_api_key.txt 파일"
        )

    payload = {
        "model": _load_anthropic_model(),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": messages,
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        parsed = json.loads(raw)
        text = _extract_anthropic_text(parsed)
        if not text:
            return False, "Claude 응답이 비어 있습니다."
        return True, text.strip()
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return False, f"Claude API 호출 실패 (HTTP {e.code})\n{body[:800]}".strip()
    except Exception as e:
        return False, f"Claude 호출 오류: {e}"


@_with_chat_session_arg(0)
def _commit_ixio_summary_success(chat_id, data):
    global user_state, pending_ixio_data, pending_ixio_duplicates
    if user_state != IXIO_SUMMARY_RUNNING_STATE:
        return False
    pending_ixio_data = dict(data or {})
    pending_ixio_duplicates = []
    user_state = 19
    return True


@_with_chat_session_arg(0)
def _commit_ixio_summary_failure(chat_id):
    global user_state
    if user_state != IXIO_SUMMARY_RUNNING_STATE:
        return False
    _clear_pending_ixio()
    user_state = 0
    return True


def _start_ixio_summary(chat_id, source_text):
    global user_state
    _clear_pending_ixio()
    user_state = IXIO_SUMMARY_RUNNING_STATE
    model_name = _load_anthropic_model()
    bot.send_message(
        chat_id,
        f"🧠 [익시오 상담요약] Claude 정리를 백그라운드로 시작했습니다. 모델: {model_name}",
    )
    _start_background_task(chat_id, "익시오 상담요약", _run_ixio_summary, chat_id, source_text)


def _run_ixio_summary(chat_id, source_text):
    ok, result = summarize_ixio_with_claude(source_text)
    if ok:
        if not _commit_ixio_summary_success(chat_id, result):
            return
        bot.send_message(chat_id, _format_ixio_kakao_message(result))
        bot.send_message(chat_id, _format_ixio_admin_message(result))
        bot.send_message(chat_id, _format_ixio_excel_message(result))
        bot.send_message(chat_id, _format_ixio_action_menu_text())
        return
    if not _commit_ixio_summary_failure(chat_id):
        return
    bot.send_message(chat_id, f"❌ [익시오 상담요약]\n{result}")
    bot.send_message(chat_id, show_list())

def _send_claude_channel_redirect(chat_id):
    bot.send_message(
        chat_id,
        "ℹ️ 이 봇은 사무실/고객관리 메뉴 전용입니다.\n"
        "OpenClaw 자동작업은 ofcgptcoder_bot 에서만 사용하세요.\n"
        "예: 현황, 코딩작업, 진행해, 다음단계 진행1\n"
        "사무실 메뉴 숫자 선택은 이 봇에서 계속 사용하시면 됩니다.",
    )


OPENCLAW_STATUS_TEXTS = {
    "/status",
    "/codex",
    "작업현황",
    "현황",
    "남은작업",
    "진행상황",
    "vs모드",
}

OPENCLAW_APPLY_TEXTS = {
    "코딩작업",
    "자동작업",
    "자동모드",
    "수동모드",
    "코딩모드하자 자동모드",
    "코딩모드 자동모드",
    "진행해",
    "vs모드 on",
    "vs모드 off",
    "vs 붙여",
    "vs 실행",
    "vs 실행하자",
}

OPENCLAW_PLAIN_NUMBER_PATTERN = r"^\s*[12]\s*$"

OPENCLAW_APPLY_PATTERNS = (
    r"^\s*(?:다음\s*단계\s*)?(?:진행|선택|번호|응답)\s*([1-9]\d*)\s*(?:번)?\s*$",
    r"^\s*([1-9]\d*)\s*(?:번)?\s*(?:으로\s*)?(?:진행|선택)\s*$",
    OPENCLAW_PLAIN_NUMBER_PATTERN,
)

OPENCLAW_PROGRESS_NEXT_ACTIONS = {
    "ask_codex_for_plan_bundle": "계획 초안을 생성할까요?",
    "send_plan_to_claude_reviewers": "계획 검수를 진행할까요?",
    "send_plan_to_codex_for_coding": "코딩을 진행할까요?",
    "send_approved_plan_to_codex": "코딩을 진행할까요?",
    "send_final_result_to_claude_reviewers": "최종 검수를 진행할까요?",
    "prepare_server_deploy_request": "서버반영 요청서를 만들까요?",
    "wait_for_user_plan_confirm_choice": "계획이 정리됐습니다. 다음을 골라주세요.\n1. 진행 - 승인된 계획으로 코딩 단계로 넘어갑니다.\n2. 중단 - 이번 작업을 여기서 멈추고 대기 상태로 둡니다.\n번호만 보내주세요.",
    "wait_for_final_outcome_choice": "최종 단계입니다. 무엇을 할까요?\n1. 다시 검토 - 최종 검수를 한 번 더 요청합니다.\n2. 이 작업 완료 - 서버 반영 없이 이번 작업을 여기서 마감합니다.\n3. 서버 반영 진행 - 서버 반영 요청 단계로 넘깁니다.\n번호만 보내주세요.",
    "wait_for_deploy_approval_choice": "서버반영을 진행할까요?\n1. 진행 - 서버 반영 요청서를 만들고 반영 단계를 이어갑니다.\n2. 보류 - 서버 반영은 멈추고 현재 상태를 유지합니다.\n번호만 보내주세요.",
}

OPENCLAW_STAGE_PROGRESS = {
    "IDLE": "0/5 단계 (대기)",
    "PREPARE": "1/5 단계 (작업 준비)",
    "PLAN_DRAFT": "2/5 단계 (계획 수립)",
    "PLAN_REVIEW": "2/5 단계 (계획 수립)",
    "PLAN_REVISION": "2/5 단계 (계획 수립)",
    "WAIT_USER_PLAN_CONFIRM": "2/5 단계 (계획 승인 대기)",
    "CODING": "3/5 단계 (코딩)",
    "FIXUP": "3/5 단계 (코딩)",
    "FINAL_REVIEW": "4/5 단계 (최종 검수)",
    "WAIT_USER_FINAL_CONFIRM": "5/5 단계 (최종 판단)",
    "WAIT_USER_APPROVAL": "5/5 단계 (배포 승인 대기)",
    "DONE": "5/5 단계 (완료)",
    "BLOCKED": "0/5 단계 (차단)",
}

OPENCLAW_ACTION_DESCRIPTIONS = {
    "ask_codex_for_plan_bundle": "코덱스용 계획 요청서를 만들고 계획 초안을 준비합니다.",
    "send_plan_to_claude_reviewers": "클로드 검토자 2명에게 계획 검수를 요청합니다.",
    "send_plan_to_claude_a": "클로드 검토자에게 계획 검수 요청서를 보냅니다.",
    "send_plan_to_claude_b": "클로드 검토자에게 계획 검수 요청서를 보냅니다.",
    "collect_plan_review": "계획 검수 결과를 모아 진행 여부를 정합니다.",
    "wait_for_user_plan_confirm_choice": "사용자에게 1 진행 / 2 중단 중 하나를 받습니다.",
    "send_plan_to_codex_for_coding": "승인된 계획으로 코딩을 시작합니다.",
    "send_approved_plan_to_codex": "승인된 계획으로 코딩을 시작합니다.",
    "send_final_result_to_claude_reviewers": "클로드 검토자 2명에게 최종 검수를 요청합니다.",
    "send_final_result_to_claude_a": "클로드 검토자에게 최종 검수 요청서를 보냅니다.",
    "send_final_result_to_claude_b": "클로드 검토자에게 최종 검수 요청서를 보냅니다.",
    "collect_final_review": "최종 검수 결과를 모아 다시 검토/완료/서버 반영 여부를 정합니다.",
    "wait_for_final_outcome_choice": "사용자에게 1 다시 검토 / 2 이 작업 완료 / 3 서버 반영 진행 중 하나를 받습니다.",
    "prepare_server_deploy_request": "서버 반영 요청서를 만들고 반영 판단 자료를 준비합니다.",
    "wait_for_deploy_approval_choice": "사용자에게 1 진행 / 2 보류 중 하나를 받습니다.",
}

OPENCLAW_ACTION_FOLLOWUP_HINTS = {
    "send_plan_to_claude_reviewers": ["collect_plan_review", "wait_for_user_plan_confirm_choice"],
    "wait_for_user_plan_confirm_choice": ["send_approved_plan_to_codex"],
    "send_final_result_to_claude_reviewers": ["collect_final_review", "wait_for_final_outcome_choice"],
    "prepare_server_deploy_request": ["wait_for_deploy_approval_choice"],
}


def _front_secretary_runtime():
    env_root = (os.environ.get("OPENCLAW_FRONT_SECRETARY_ROOT") or "").strip()
    base_parent = os.path.dirname(BASE_DIR.rstrip("\\/")) or os.path.dirname(BASE_DIR) or ""
    candidates = [
        env_root,
        os.path.join(base_parent, "1other", "openclaw-front-secretary"),
        r"C:\1other\openclaw-front-secretary",
        "/mnt/c/1other/openclaw-front-secretary",
    ]
    seen = set()
    for root in candidates:
        root = (root or "").strip()
        if not root or root in seen:
            continue
        seen.add(root)
        script = os.path.join(root, "tools", "auto_work", "front_secretary.py")
        state_file = os.path.join(root, "runtime", "front_secretary", "state.json")
        if os.path.exists(script):
            return {
                "ok": True,
                "root": root,
                "script": script,
                "state_file": state_file,
            }
    return {"ok": False, "reason": "front_secretary runtime not found"}


def _front_secretary_pending_prompt_text(payload):
    operator_view = payload.get("operator_view") or {}
    latest_question = str(operator_view.get("latest_question") or "").strip()
    if latest_question:
        return latest_question

    active_task = payload.get("active_task") or {}
    pending = dict(active_task.get("pending_user_prompt") or {})
    prompt_type = str(pending.get("type") or "").strip()
    question = str(pending.get("question") or "").strip()
    options = pending.get("options") or []
    if options:
        if not any(str(item.get("description") or "").strip() for item in options):
            next_action = str(payload.get("next_action") or "").strip()
            progress_question = OPENCLAW_PROGRESS_NEXT_ACTIONS.get(next_action, "")
            if progress_question:
                return progress_question.strip()
        lines = [question] if question else []
        for item in options:
            idx = str(item.get("id") or "").strip()
            label = str(item.get("label") or "").strip()
            description = str(item.get("description") or "").strip()
            if idx and label:
                if description:
                    lines.append(f"{idx}. {label} - {description}")
                else:
                    lines.append(f"{idx}. {label}")
        lines.append("번호만 보내주세요.")
        return "\n".join(lines).strip()
    if prompt_type == "extra_review_offer":
        lines = [
            question or "추가 검수 여부를 골라주세요.",
            "1. 추가 검수 진행 - 검수를 한 번 더 요청합니다.",
            "2. 수정 단계로 진행 - 수정 작업으로 되돌아갑니다.",
            "번호만 보내주세요.",
        ]
        return "\n".join(lines).strip()
    next_action = str(payload.get("next_action") or "").strip()
    progress_question = OPENCLAW_PROGRESS_NEXT_ACTIONS.get(next_action, "")
    if progress_question:
        if "\n" in progress_question:
            return progress_question.strip()
        return "\n".join([progress_question, "1. 진행", "2. 보류", "번호만 보내주세요."]).strip()
    return question


def _openclaw_progress_text(stage):
    stage = str(stage or "").strip()
    return OPENCLAW_STAGE_PROGRESS.get(stage, stage or "0/5 단계")


def _openclaw_action_description(action):
    action = str(action or "").strip()
    if not action:
        return ""
    return OPENCLAW_ACTION_DESCRIPTIONS.get(action, action.replace("_", " "))


def _openclaw_todo_lines(payload):
    next_action = str(payload.get("next_action") or "").strip()
    raw_actions = []
    if next_action and next_action not in {"", "await_user_request", "show_current_state"}:
        raw_actions.append(next_action)
    raw_actions.extend(OPENCLAW_ACTION_FOLLOWUP_HINTS.get(next_action, []))
    raw_actions.extend(str(item or "").strip() for item in (payload.get("recommended_actions") or []))

    labels = ["지금", "다음", "다다음"]
    seen_actions = set()
    seen_descriptions = set()
    lines = []
    for action in raw_actions:
        if not action or action in seen_actions:
            continue
        seen_actions.add(action)
        description = _openclaw_action_description(action)
        if not description or description in seen_descriptions:
            continue
        seen_descriptions.add(description)
        label = labels[len(lines)] if len(lines) < len(labels) else f"{len(lines) + 1}번째"
        lines.append(f"- {label}: {description}")
        if len(lines) >= 3:
            break
    return lines


def _format_front_secretary_reply(payload):
    operator_view = payload.get("operator_view") or {}
    active_task = payload.get("active_task") or {}
    mode = str(payload.get("conversation_mode") or "").strip()
    stage = str(payload.get("current_stage") or "").strip()
    summary = str(operator_view.get("openclaw_summary") or payload.get("summary") or "").strip()
    alert = str(operator_view.get("system_alert") or "").strip()
    if alert == "VS 모드를 해제했습니다." and stage not in {"IDLE", "PREPARE"}:
        alert = ""
    prompt_text = _front_secretary_pending_prompt_text(payload)
    lines = [f"[OpenClaw] {stage or 'IDLE'}"]
    if mode:
        lines.append(f"모드: {mode}")
    title = str(active_task.get("title") or "").strip()
    if title:
        lines.append(f"현재 계획: {title}")
    lines.append(f"진척: {_openclaw_progress_text(stage)}")
    if summary:
        lines.append(summary)
    if alert and alert not in summary:
        lines.append(f"알림: {alert}")
    next_action = str(payload.get("next_action") or "").strip()
    if next_action and next_action not in {"", "await_user_request", "show_current_state"}:
        lines.append(f"다음 남은 단계: {next_action}")
    todo_lines = _openclaw_todo_lines(payload)
    if todo_lines:
        lines.append("할 일:")
        lines.extend(todo_lines)
    if prompt_text:
        lines.append("")
        lines.append("지금 보낼 답:")
        lines.append(prompt_text)
    return "\n".join(line for line in lines if line).strip()


def _run_front_secretary(args, *, timeout_sec=None):
    runtime = _front_secretary_runtime()
    if not runtime.get("ok"):
        return False, str(runtime.get("reason") or "front_secretary runtime not found")
    command = [
        PYTHON_EXE,
        runtime["script"],
        *args,
        "--state-file",
        runtime["state_file"],
        "--json",
    ]
    try:
        cp = subprocess.run(
            command,
            cwd=runtime["root"],
            capture_output=True,
            text=True,
            timeout=timeout_sec or env_timeout_seconds("BOT_FRONT_SECRETARY_TIMEOUT", 30),
        )
    except Exception as exc:
        return False, f"front_secretary 실행 실패: {exc}"
    if cp.returncode != 0:
        detail = (cp.stderr or cp.stdout or "").strip()
        return False, detail or f"front_secretary exit {cp.returncode}"
    try:
        return True, json.loads((cp.stdout or "").strip())
    except Exception:
        return False, "front_secretary JSON 파싱 실패"


def _classify_front_secretary_request(text, *, allow_plain_number_choice=True):
    stripped = (text or "").strip()
    lowered = stripped.lower()
    if lowered in OPENCLAW_STATUS_TEXTS or stripped in OPENCLAW_STATUS_TEXTS:
        return "status"
    if lowered in OPENCLAW_APPLY_TEXTS or stripped in OPENCLAW_APPLY_TEXTS:
        return "apply"
    for pattern in OPENCLAW_APPLY_PATTERNS:
        if not allow_plain_number_choice and pattern == OPENCLAW_PLAIN_NUMBER_PATTERN:
            continue
        if re.match(pattern, stripped):
            return "apply"
    return ""


def _classify_front_secretary_message(text):
    if not OPENCLAW_HANDLER_ENABLED:
        return ""
    return _classify_front_secretary_request(text)


def _maybe_handle_front_secretary_message(message, text):
    # Hard stop: office bot must never emit OpenClaw replies even if another
    # handler path reaches this function unexpectedly.
    if not OPENCLAW_HANDLER_ENABLED:
        return False
    route = _classify_front_secretary_message(text)
    if not route:
        return False
    if route == "status":
        ok, payload = _run_front_secretary(["status"], timeout_sec=20)
    else:
        ok, payload = _run_front_secretary(["telegram-apply", "--text", text], timeout_sec=60)
    if not ok:
        bot.send_message(message.chat.id, f"⚠️ OpenClaw 처리 실패\n{payload}")
        return True
    reply = _format_front_secretary_reply(payload)
    if not reply:
        reply = "⚠️ OpenClaw 응답이 비어 있습니다."
    bot.send_message(message.chat.id, reply)
    return True


def _send_removed_legacy_menu_message(chat_id):
    bot.send_message(
        chat_id,
        "ℹ️ 61/62/63/94/000 레거시 메뉴는 현재 운영에서 제거되었습니다.\n"
        "해당 KR 후보발굴 기능은 외부 독립 저장소로 분리되어 현재 2POW 운영 메뉴에서는 다루지 않습니다.",
    )


def _detect_token_source():
    if (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip():
        return "env:TELEGRAM_BOT_TOKEN"
    if _first_nonempty_line(_read_runtime_file("bot_token.txt")):
        return "runtime:bot_token.txt"
    if _first_nonempty_line(_read_secret_file("bot_token.txt")):
        return "script:bot_token.txt"
    return "missing"


def _format_bot_runtime_status_message():
    payload = _load_runtime_status()
    current_host = _get_current_hostname().upper() or "UNKNOWN"
    allowed_hosts = _load_allowed_hostnames()
    last_status = (payload.get("status") or "unknown").strip()
    detail = (payload.get("detail") or "").strip()
    updated_at = (payload.get("updated_at") or "").strip() or "-"
    anthropic_ready = bool(_load_anthropic_api_key())

    # A later duplicate launch can leave a stale fatal_single_instance status
    # even while the current bot process is healthy and serving messages.
    if last_status == "fatal_single_instance" and BOT_INSTANCE_GUARD is not None:
        last_status = "running"
        detail = "현재 인스턴스는 정상 동작 중입니다. 이전 중복 실행 시도만 차단되었습니다."

    lines = ["🖥️ 사무실 봇상태"]
    lines.append(f"host: {current_host}")
    lines.append(f"base_dir: {BASE_DIR}")
    lines.append(f"bot_profile: {BOT_PROFILE}")
    lines.append(f"python: {PYTHON_EXE}")
    lines.append(f"bot_version: {BOT_VERSION}")
    lines.append(f"runtime_status: {last_status}")
    lines.append(f"updated_at: {updated_at}")
    lines.append(f"office_host_enforced: {BOT_ENFORCE_OFFICE_HOST}")
    lines.append(f"allowed_hosts: {', '.join(allowed_hosts) if allowed_hosts else '(none)'}")
    lines.append(f"allowed_chat_count: {len(ALLOWED_CHAT_IDS)}")
    lines.append(f"token_source: {_detect_token_source()}")
    lines.append(f"claude_api_ready: {'yes' if anthropic_ready else 'no'}")
    if detail:
        lines.append(f"detail: {detail}")
    lines.append("로그확인: /botlog 또는 봇로그")
    return "\n".join(lines)


def _format_bot_log_message():
    out_tail = read_tail(os.path.join(BOT_LOG_DIR, "bot_runtime.log"), max_lines=30)
    err_tail = read_tail(os.path.join(BOT_LOG_DIR, "bot_runtime.err.log"), max_lines=30)
    lines = ["📄 사무실 봇 로그 tail"]
    lines.append("[stdout]")
    lines.append(out_tail or "(empty)")
    lines.append("")
    lines.append("[stderr]")
    lines.append(err_tail or "(empty)")
    return "\n".join(lines)


def _looks_like_telegram_conflict(exc):
    text = str(exc or "")
    lowered = text.lower()
    return "409" in lowered and ("conflict" in lowered or "getupdates" in lowered)


def _load_due_customer_schedules():
    try:
        if os.path.exists(DUE_CUSTOMER_SCHEDULE_FILE):
            with open(DUE_CUSTOMER_SCHEDULE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            return payload if isinstance(payload, dict) else {}
    except Exception:
        pass
    return {}


def _save_due_customer_schedules(payload):
    with open(DUE_CUSTOMER_SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload or {}, f, ensure_ascii=False, indent=2)


def _get_due_customer_schedule(chat_id):
    with DUE_CUSTOMER_SCHEDULE_LOCK:
        payload = _load_due_customer_schedules()
        item = payload.get(str(chat_id)) or {}
    return item if isinstance(item, dict) else {}


def _set_due_customer_schedule(chat_id, time_text):
    with DUE_CUSTOMER_SCHEDULE_LOCK:
        payload = _load_due_customer_schedules()
        current = dict(payload.get(str(chat_id)) or {})
        current["time"] = time_text
        current["weekdays_only"] = True
        payload[str(chat_id)] = current
        _save_due_customer_schedules(payload)


def _clear_due_customer_schedule(chat_id):
    removed = False
    with DUE_CUSTOMER_SCHEDULE_LOCK:
        payload = _load_due_customer_schedules()
        if str(chat_id) in payload:
            payload.pop(str(chat_id), None)
            _save_due_customer_schedules(payload)
            removed = True
    return removed


def _mark_due_customer_schedule_sent(chat_id, sent_date):
    with DUE_CUSTOMER_SCHEDULE_LOCK:
        payload = _load_due_customer_schedules()
        current = dict(payload.get(str(chat_id)) or {})
        current["last_sent_date"] = sent_date
        payload[str(chat_id)] = current
        _save_due_customer_schedules(payload)


def _parse_due_schedule_time(text):
    source = str(text or "").strip()
    if not source:
        return ""
    match = re.fullmatch(r"(\d{1,2})(?::?(\d{2}))?", source)
    if not match:
        return ""
    hour = int(match.group(1))
    minute = int(match.group(2) or "00")
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return ""
    return f"{hour:02d}:{minute:02d}"


def _excel_serial_to_datetime(value):
    try:
        number = float(value)
    except Exception:
        return None
    if number >= 20000:
        return datetime(1899, 12, 30) + timedelta(days=number)
    if 101 <= number <= 1231:
        mmdd = f"{int(round(number)):04d}"
        parsed = _parse_excel_month_day(mmdd)
        if parsed:
            month, day = parsed
            return datetime(EXCEL_DATE_YEAR, month, day)
    return None


def _parse_display_date(value):
    parsed = _parse_excel_month_day(value)
    if not parsed:
        return None
    month, day = parsed
    return datetime(EXCEL_DATE_YEAR, month, day)


def _extract_shared_strings(zip_file):
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values = []
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return values
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    for si in root.findall("main:si", ns):
        text_node = si.find("main:t", ns)
        if text_node is not None:
            values.append(text_node.text or "")
            continue
        pieces = []
        for rt in si.findall(".//main:t", ns):
            pieces.append(rt.text or "")
        values.append("".join(pieces))
    return values


def _resolve_h_sheet_xml(zip_file):
    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    relmap = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("pkgrel:Relationship", ns)}
    for sheet in workbook.findall("main:sheets/main:sheet", ns):
        if str(sheet.attrib.get("name") or "").strip().lower() != "h":
            continue
        rid = sheet.attrib.get(f"{{{rel_ns}}}id")
        target = relmap.get(rid)
        if target:
            normalized_target = str(target).replace("\\", "/").lstrip("/")
            if normalized_target.lower().startswith("xl/"):
                return normalized_target
            return "xl/" + normalized_target
    return ""


def _sheet_snapshot_from_file(target):
    ns_uri = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ns = {"main": ns_uri}
    with ZipFile(target) as zip_file:
        sheet_xml = _resolve_h_sheet_xml(zip_file)
        if not sheet_xml:
            raise ValueError("H 시트를 찾지 못했습니다.")
        shared = _extract_shared_strings(zip_file)
        root = ET.fromstring(zip_file.read(sheet_xml))

    values_by_row = {}
    for cell in root.findall(".//main:c", ns):
        ref = str(cell.attrib.get("r") or "").strip()
        match = re.fullmatch(r"([A-Z]+)(\d+)", ref)
        if not match:
            continue
        col = match.group(1)
        row = int(match.group(2))
        cell_type = cell.attrib.get("t")
        raw_v = cell.findtext("main:v", default="", namespaces=ns)
        text_value = ""
        if cell_type == "s" and raw_v:
            try:
                idx = int(raw_v)
                text_value = shared[idx] if 0 <= idx < len(shared) else ""
            except Exception:
                text_value = ""
        elif cell_type == "inlineStr":
            text_value = cell.findtext("main:is/main:t", default="", namespaces=ns)
        elif cell_type == "str":
            text_value = raw_v
        elif raw_v:
            text_value = raw_v
        values_by_row.setdefault(row, {})[col] = {
            "type": cell_type or "n",
            "raw": raw_v,
            "text": str(text_value or "").strip(),
        }
    return values_by_row


def _cell_snapshot_text(row_map, col):
    cell = (row_map or {}).get(col) or {}
    return str(cell.get("text") or "").strip()


def _compact_multiline_value(value):
    return " ".join(str(value or "").replace("\r", "\n").split()).strip()


def _is_due_customer_excluded_status(value):
    return "기표완료" in _compact_multiline_value(value)


def _format_due_rate_value(value):
    raw = str(value or "").strip()
    if not raw or raw == "-":
        return ""
    if "%" in raw:
        return raw
    try:
        number = float(raw)
    except Exception:
        return raw
    if 0 <= number <= 1:
        number *= 100
    formatted = f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{formatted}%"


def _cell_snapshot_date(row_map, col):
    cell = (row_map or {}).get(col) or {}
    if not cell:
        return None
    dt = _excel_serial_to_datetime(cell.get("raw"))
    if dt:
        return dt
    return _parse_display_date(cell.get("text"))


def _fetch_due_customer_rows_from_file(target):
    try:
        values_by_row = _sheet_snapshot_from_file(target)
    except Exception as e:
        return False, f"파일 직접 조회 실패: {e}"

    last_name_row = 1
    for row, row_map in values_by_row.items():
        if _cell_snapshot_text(row_map, "F"):
            last_name_row = max(last_name_row, row)

    rows = []
    today = datetime.now().date()
    for row in range(2, last_name_row + 1):
        row_map = values_by_row.get(row) or {}
        name = _cell_snapshot_text(row_map, "F")
        if not name:
            continue
        customer_status = _cell_snapshot_text(row_map, "E")
        if _is_due_customer_excluded_status(customer_status):
            continue
        first_date = _cell_snapshot_date(row_map, "C")
        second_date = _cell_snapshot_date(row_map, "D")
        base_date = second_date or first_date
        if not base_date or base_date.date() > today:
            continue
        rows.append(
            {
                "row": row,
                "bucket": "today" if base_date.date() == today else "past",
                "base_date": base_date.strftime("%Y-%m-%d"),
                "first_date": first_date.strftime("%m-%d") if first_date else "",
                "second_date": second_date.strftime("%m-%d") if second_date else "",
                "second_consult": _cell_snapshot_text(row_map, "A"),
                "first_consult": _cell_snapshot_text(row_map, "B"),
                "customer_status": customer_status,
                "name": name,
                "jumin": _cell_snapshot_text(row_map, "G"),
                "address": _cell_snapshot_text(row_map, "H"),
                "phone": _cell_snapshot_text(row_map, "I"),
                "loan": _cell_snapshot_text(row_map, "K"),
                "income": _cell_snapshot_text(row_map, "L"),
                "credit": _cell_snapshot_text(row_map, "M"),
                "kind": _cell_snapshot_text(row_map, "N"),
                "bank": _cell_snapshot_text(row_map, "O"),
                "seller": _cell_snapshot_text(row_map, "P"),
                "rate": _cell_snapshot_text(row_map, "Q"),
            "commission_amount": _cell_snapshot_text(row_map, "T"),
            "ext_commission": _cell_snapshot_text(row_map, "U"),
            }
        )

    rows.sort(key=lambda item: (0 if str(item.get("bucket")) == "today" else 1, str(item.get("base_date") or ""), int(item.get("row") or 0)))
    return True, {"path": target, "rows": rows}


def _format_due_customer_menu(chat_id):
    schedule = _get_due_customer_schedule(chat_id)
    schedule_text = str(schedule.get("time") or "").strip() or "없음"
    return "\n".join(
        [
            "📅 [오늘/지난 고객리스트]",
            "기준: 2차접수 우선, 없으면 1차접수",
            "중간 공란 행이 있어도 마지막 이름행까지 조회합니다.",
            f"현재 예약: {schedule_text} (평일만)",
            "",
            "1. 지금 받기",
            "2. 평일 예약받기",
            "3. 예약확인",
            "4. 예약해제",
            "0. 초기화면",
        ]
    )


def _fetch_due_customer_rows():
    target = _resolve_excel_target_path()
    if not target:
        searched = "\n".join(_excel_target_candidates())
        return False, f"통합관리 파일 경로를 찾지 못했습니다.\n후보 경로:\n{searched}"

    ps_script = r"""
$ErrorActionPreference = 'Stop'
$target = $env:TG_EXCEL_TARGET
$targetYear = [int]($env:TG_EXCEL_DATE_YEAR)

function Convert-ToTargetDate([string]$raw, [int]$year) {
  $text = [string]$raw
  if ([string]::IsNullOrWhiteSpace($text)) { return $null }
  $text = $text.Trim()
  $digits = ($text -replace '[^\d]', '')
  $month = $null
  $day = $null
  if ($text -match '^(\d{1,2})[-/.](\d{1,2})$') {
    $month = [int]$Matches[1]
    $day = [int]$Matches[2]
  } elseif ($text -match '^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$') {
    $month = [int]$Matches[2]
    $day = [int]$Matches[3]
  } elseif ($digits -match '^\d{4}$') {
    $month = [int]$digits.Substring(0, 2)
    $day = [int]$digits.Substring(2, 2)
  } elseif ($digits -match '^\d{8}$') {
    $month = [int]$digits.Substring(4, 2)
    $day = [int]$digits.Substring(6, 2)
  }
  if ($null -eq $month -or $null -eq $day) { return $null }
  try {
    return Get-Date -Year $year -Month $month -Day $day -Hour 0 -Minute 0 -Second 0
  } catch {
    return $null
  }
}

function Resolve-CellDate($cell, [int]$year) {
  $value2 = $cell.Value2
  try {
    if ($null -ne $value2) {
      $number = [double]$value2
      if ($number -ge 20000) {
        return [datetime]::FromOADate($number)
      }
      if ($number -ge 101 -and $number -le 1231) {
        $mmdd = '{0:0000}' -f [int][math]::Round($number)
        return Convert-ToTargetDate $mmdd $year
      }
    }
  } catch {}
  $dt = Convert-ToTargetDate ([string]$cell.Text) $year
  if ($dt) { return $dt }
  return Convert-ToTargetDate ([string]$cell.Value2) $year
}

$excel = $null
$wb = $null
$opened = $false
try {
  try { $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application') } catch {}
  if ($null -eq $excel) { $excel = New-Object -ComObject Excel.Application }
  foreach ($w in @($excel.Workbooks)) {
    if ($w.FullName -ieq $target) { $wb = $w; break }
  }
  if ($null -eq $wb) {
    if (-not (Test-Path -LiteralPath $target)) { throw 'FILE_NOT_FOUND' }
    $wb = $excel.Workbooks.Open($target)
    $opened = $true
  }
  $ws = $null
  try { $ws = $wb.Worksheets.Item('h') } catch {}
  if ($null -eq $ws) { try { $ws = $wb.Worksheets.Item('H') } catch {} }
  if ($null -eq $ws) { throw 'SHEET_NOT_FOUND:h' }

  $lastNameCell = $ws.Columns.Item(6).Find('*', $ws.Cells.Item(1, 6), $null, $null, 1, 2, $false, $false, $false)
  $lastRow = if ($null -ne $lastNameCell) { [int]$lastNameCell.Row } else { 1 }
  $today = (Get-Date).Date
  $rows = @()

  for ($row = 2; $row -le $lastRow; $row++) {
    $name = [string]$ws.Cells.Item($row, 6).Text
    if ([string]::IsNullOrWhiteSpace($name)) { continue }
    $customerStatus = [string]$ws.Cells.Item($row, 5).Text
    if ($customerStatus -like '*기표완료*') { continue }

    $firstDate = Resolve-CellDate $ws.Cells.Item($row, 3) $targetYear
    $secondDate = Resolve-CellDate $ws.Cells.Item($row, 4) $targetYear
    $baseDate = if ($null -ne $secondDate) { $secondDate } elseif ($null -ne $firstDate) { $firstDate } else { $null }
    if ($null -eq $baseDate) { continue }
    if ($baseDate.Date -gt $today) { continue }

    $bucket = if ($baseDate.Date -eq $today) { 'today' } else { 'past' }
    $rows += [pscustomobject]@{
      row = $row
      bucket = $bucket
      base_date = $baseDate.ToString('yyyy-MM-dd')
      first_date = if ($null -ne $firstDate) { $firstDate.ToString('MM-dd') } else { '' }
      second_date = if ($null -ne $secondDate) { $secondDate.ToString('MM-dd') } else { '' }
      second_consult = [string]$ws.Cells.Item($row, 1).Text
      first_consult = [string]$ws.Cells.Item($row, 2).Text
      customer_status = $customerStatus
      name = $name
      jumin = [string]$ws.Cells.Item($row, 7).Text
      address = [string]$ws.Cells.Item($row, 8).Text
      phone = [string]$ws.Cells.Item($row, 9).Text
      loan = [string]$ws.Cells.Item($row, 11).Text
      income = [string]$ws.Cells.Item($row, 12).Text
      credit = [string]$ws.Cells.Item($row, 13).Text
      kind = [string]$ws.Cells.Item($row, 14).Text
      bank = [string]$ws.Cells.Item($row, 15).Text
      seller = [string]$ws.Cells.Item($row, 16).Text
      rate = [string]$ws.Cells.Item($row, 17).Text
    }
  }

  [pscustomobject]@{ ok = $true; path = $target; rows = $rows } | ConvertTo-Json -Depth 5 -Compress
}
catch {
  [pscustomobject]@{ ok = $false; error = $_.Exception.Message } | ConvertTo-Json -Compress
  exit 1
}
finally {
  if ($opened -and $null -ne $wb) { try { $wb.Close($false) } catch {} }
  if ($null -ne $excel) {
    try {
      if ($excel.Workbooks.Count -eq 0) { $excel.Quit() }
    } catch {}
  }
}
"""
    result = _run_powershell(
        ps_script,
        extra_env={
            "TG_EXCEL_TARGET": target,
            "TG_EXCEL_DATE_YEAR": str(EXCEL_DATE_YEAR),
        },
    )
    ok, payload = _parse_powershell_json_result(result)
    if ok and payload.get("ok"):
        rows = list(payload.get("rows") or [])
        rows.sort(key=lambda item: (0 if str(item.get("bucket")) == "today" else 1, str(item.get("base_date") or ""), int(item.get("row") or 0)))
        return True, {
            "path": str(payload.get("path") or target),
            "rows": rows,
        }
    return _fetch_due_customer_rows_from_file(target)


def _format_due_customer_report(payload):
    rows = list((payload or {}).get("rows") or [])
    today_rows = [item for item in rows if str(item.get("bucket") or "") == "today"]
    past_rows = [item for item in rows if str(item.get("bucket") or "") == "past"]

    lines = [
        "📅 오늘/지난 고객리스트",
        "기준: 2차접수 우선, 없으면 1차접수",
        "중간 공란 행이 있어도 마지막 이름행까지 조회",
    ]

    for label, items in (("오늘", today_rows), ("지난", past_rows)):
        lines.append("")
        lines.append(f"[{label}] {len(items)}건")
        if not items:
            lines.append("- 없음")
            continue
        for item in items:
            row = item.get("row")
            first_date = str(item.get("first_date") or "").strip() or "-"
            second_date = str(item.get("second_date") or "").strip() or "-"
            status = str(item.get("customer_status") or "").strip() or "-"
            name = str(item.get("name") or "").strip() or "-"
            jumin = str(item.get("jumin") or "").strip() or "-"
            address = str(item.get("address") or "").strip() or "-"
            phone = str(item.get("phone") or "").strip() or "-"
            loan = str(item.get("loan") or "").strip() or "-"
            income = str(item.get("income") or "").strip() or "-"
            credit = str(item.get("credit") or "").strip() or "-"
            kind = str(item.get("kind") or "").strip() or "-"
            bank = str(item.get("bank") or "").strip() or "-"
            seller = str(item.get("seller") or "").strip() or "-"
            rate = _format_due_rate_value(item.get("rate") or "")
            first_consult = _compact_multiline_value(item.get("first_consult") or "") or "-"
            second_consult = _compact_multiline_value(item.get("second_consult") or "") or "-"
            values = [
                first_consult,
                second_consult if second_consult not in {"", "-"} else "",
                " / ".join(part for part in (first_date, second_date, status) if part and part != "-"),
                name,
                jumin,
                phone,
                address,
                loan,
                income,
                credit,
                kind,
                bank,
                seller if seller not in {"", "-"} else "",
                rate if rate else "",
            ]
            lines.extend(value for value in values if value)
            lines.append("")
    return "\n".join(lines)


def _send_due_customer_report(chat_id, scheduled=False):
    ok, payload = _fetch_due_customer_rows()
    if not ok:
        bot.send_message(chat_id, f"❌ 오늘/지난 고객리스트 조회 실패\n{payload}")
        return False
    prefix = "⏰ [평일 예약]\n" if scheduled else ""
    send_long_message(chat_id, prefix + _format_due_customer_report(payload))
    return True


def _run_due_customer_schedule_tick():
    now = datetime.now()
    if now.weekday() >= 5:
        return
    today_text = now.strftime("%Y-%m-%d")
    current_hhmm = now.strftime("%H:%M")
    with DUE_CUSTOMER_SCHEDULE_LOCK:
        payload = _load_due_customer_schedules()
    for chat_id_text, item in payload.items():
        if not isinstance(item, dict):
            continue
        time_text = str(item.get("time") or "").strip()
        if not time_text or current_hhmm < time_text:
            continue
        if str(item.get("last_sent_date") or "").strip() == today_text:
            continue
        try:
            sent = _send_due_customer_report(int(chat_id_text), scheduled=True)
            if sent:
                _mark_due_customer_schedule_sent(chat_id_text, today_text)
        except Exception as e:
            try:
                print(f"[due-schedule] {chat_id_text} {e}")
            except Exception:
                pass


def _due_customer_schedule_loop():
    while True:
        try:
            _run_due_customer_schedule_tick()
        except Exception as e:
            try:
                print(f"[due-schedule-loop] {e}")
            except Exception:
                pass
        time.sleep(30)



# ──────────────────────────────────────────────
# 68번 AI 고객 브리핑
# ──────────────────────────────────────────────

# user_state 25: AI 브리핑 간단분석 표시 후 상세분석 여부 대기


def _fetch_all_h_rows():
    """H시트에서 기표완료 포함 전체 활성 고객을 가져온다."""
    target = _resolve_excel_target_path()
    if not target:
        searched = "\n".join(_excel_target_candidates())
        return False, f"통합관리 파일 경로를 찾지 못했습니다.\n후보 경로:\n{searched}"

    try:
        values_by_row = _sheet_snapshot_from_file(target)
    except Exception as e:
        return False, f"파일 직접 조회 실패: {e}"

    last_name_row = 1
    for row, row_map in values_by_row.items():
        if _cell_snapshot_text(row_map, "F"):
            last_name_row = max(last_name_row, row)

    rows = []
    for row in range(2, last_name_row + 1):
        row_map = values_by_row.get(row) or {}
        name = _cell_snapshot_text(row_map, "F")
        if not name:
            continue
        seller = _cell_snapshot_text(row_map, "P")
        if seller and seller not in ("정", ""):
            continue
        customer_status = _cell_snapshot_text(row_map, "E")
        if not customer_status:
            continue
        # D열에 "관리" 포함되면 별도관리 고객 → 패스
        d_val = _cell_snapshot_text(row_map, "D")
        if d_val and "관리" in d_val:
            continue
        rows.append({
            "row": row,
            "second_consult": _cell_snapshot_text(row_map, "A"),
            "first_consult": _cell_snapshot_text(row_map, "B"),
            "first_date": _cell_snapshot_text(row_map, "C"),
            "second_date": _cell_snapshot_text(row_map, "D"),
            "customer_status": customer_status,
            "name": name,
            "address": _cell_snapshot_text(row_map, "H"),
            "phone": _cell_snapshot_text(row_map, "I"),
            "deposit": _cell_snapshot_text(row_map, "J"),
            "loan": _cell_snapshot_text(row_map, "K"),
            "income": _cell_snapshot_text(row_map, "L"),
            "credit": _cell_snapshot_text(row_map, "M"),
            "kind": _cell_snapshot_text(row_map, "N"),
            "bank": _cell_snapshot_text(row_map, "O"),
            "rate": _cell_snapshot_text(row_map, "Q"),
        })
    return True, {"path": target, "rows": rows}


def _parse_memo_dates(memo):
    """A열 메모에서 날짜/시점을 추출한다."""
    if not memo:
        return []
    dates = []
    for m in re.finditer(r"(\d{2})[-/.]?(\d{2})", memo):
        mm, dd = m.group(1), m.group(2)
        try:
            mm_int, dd_int = int(mm), int(dd)
            if 1 <= mm_int <= 12 and 1 <= dd_int <= 31:
                dates.append((mm_int, dd_int))
        except Exception:
            pass
    for m in re.finditer(r"26[-년]?\s*(\d{1,2})\s*월?", memo):
        try:
            mm_int = int(m.group(1))
            if 1 <= mm_int <= 12:
                dates.append((mm_int, None))
        except Exception:
            pass
    for m in re.finditer(r"(\d{1,2})월", memo):
        try:
            mm_int = int(m.group(1))
            if 1 <= mm_int <= 12 and (mm_int, None) not in dates:
                dates.append((mm_int, None))
        except Exception:
            pass
    return dates


def _classify_briefing_rows(rows):
    """고객을 C열(접수일) 기준 3분류 + 기표완료 분리."""
    from datetime import timedelta
    now = datetime.now()
    today = now.date()
    week_end = today + timedelta(days=(6 - today.weekday()))

    past_due = []
    this_week = []
    future = []
    completed = []

    for r in rows:
        status = r.get("customer_status", "")
        if "기표완료" in status:
            completed.append(r)
            continue

        raw_date = r.get("first_date", "")
        target_date = None
        if raw_date:
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%y-%m-%d", "%m/%d", "%m-%d"):
                try:
                    parsed = datetime.strptime(str(raw_date).strip()[:10], fmt)
                    if parsed.year < 2000:
                        parsed = parsed.replace(year=today.year)
                    target_date = parsed.date()
                    break
                except Exception:
                    pass
            if not target_date:
                m = re.search(r"(\d{2})[-/.]?(\d{2})", str(raw_date))
                if m:
                    try:
                        mm, dd = int(m.group(1)), int(m.group(2))
                        if 1 <= mm <= 12 and 1 <= dd <= 31:
                            target_date = today.replace(month=mm, day=dd)
                    except Exception:
                        pass

        if not target_date:
            memo_a = r.get("second_consult", "")
            if memo_a:
                dates = _parse_memo_dates(memo_a)
                for md in dates:
                    mm, dd = md
                    if dd is not None:
                        try:
                            target_date = today.replace(month=mm, day=dd)
                            break
                        except Exception:
                            pass

        if target_date:
            if target_date < today:
                past_due.append(r)
            elif target_date <= week_end:
                this_week.append(r)
            else:
                future.append(r)
        else:
            if status in ("자서예정", "기표예정", "가승인"):
                this_week.append(r)
            else:
                future.append(r)

    return past_due, this_week, future, completed


INTERNAL_BANKS = {"키움", "키움민간", "ms", "MS", "롯데손해보험",
                  "키움특판", "키움특판6.9", "키움특판6.9/7.1"}


def _is_internal_bank(bank):
    if not bank:
        return False
    b = str(bank).strip()
    for ib in INTERNAL_BANKS:
        if ib in b:
            return True
    return b.startswith("키움") or b.startswith("MS") or b.startswith("ms")


def _format_customer_line(r, is_external=False):
    """고객 한 줄: 이름/연락처/보증금/대출금/은행 [상태] — 메모"""
    name = r.get("name", "?")
    phone = r.get("phone", "")
    deposit = r.get("deposit", "")
    loan = r.get("loan", "")
    bank = r.get("bank", "")
    status = r.get("customer_status", "")
    memo = r.get("second_consult", "")

    parts = [name, phone]
    if deposit:
        parts.append(f"{deposit}만")
    if loan:
        parts.append(f"{loan}만")
    parts.append(bank or "?")
    line = " / ".join(parts)
    if status:
        line += f" [{status}]"
    if memo:
        compact = memo.replace("\n", " ").strip()[:40]
        if compact:
            line += f" — {compact}"
    return line


def _format_completed_line(r, is_external=False):
    """기표완료 라인: 이름/연락처/보증금/대출금/은행/수수료"""
    name = r.get("name", "?")
    phone = r.get("phone", "")
    deposit = r.get("deposit", "")
    loan = r.get("loan", "")
    bank = r.get("bank", "")
    parts = [name, phone]
    if deposit:
        parts.append(f"{deposit}만")
    if loan:
        parts.append(f"{loan}만")
    parts.append(bank or "?")
    if is_external:
        comm = r.get("ext_commission", "")
    else:
        comm = r.get("commission_amount", "")
    if comm:
        parts.append(f"수수료:{comm}")
    return " / ".join(parts)


def _date_subsection(emoji, label, rows, is_external=False):
    if not rows:
        return ""
    lines = [f"{emoji} {label} ({len(rows)}건)"]
    for r in rows:
        lines.append(f"  {_format_customer_line(r, is_external)}")
    return "\n".join(lines)


def _safe_int(val):
    try:
        return int(float(str(val).replace(",", "").strip()))
    except Exception:
        return 0


def _format_simple_briefing(past_due, this_week, future, completed):
    """68번 간단 분석: 내부/외부 최상위 분리 → 날짜 3분류."""
    now = datetime.now()
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    total = len(past_due) + len(this_week) + len(future) + len(completed)
    header = f"\U0001f4cb {now.strftime('%m/%d')}({weekdays[now.weekday()]}) 고객 브리핑\n총 {total}명\n"

    def split_ie(rows):
        internal = [r for r in rows if _is_internal_bank(r.get("bank", ""))]
        external = [r for r in rows if not _is_internal_bank(r.get("bank", ""))]
        return internal, external

    pd_i, pd_e = split_ie(past_due)
    tw_i, tw_e = split_ie(this_week)
    fu_i, fu_e = split_ie(future)
    co_i, co_e = split_ie(completed)

    sections = []

    # 내부
    i_count = len(pd_i) + len(tw_i) + len(fu_i)
    if i_count > 0:
        i_parts = [f"\n\u3010내부\u3011 ({i_count}건)"]
        s = _date_subsection("\U0001f534", "날짜지남", pd_i)
        if s: i_parts.append(s)
        s = _date_subsection("\U0001f7e1", "이번주", tw_i)
        if s: i_parts.append(s)
        s = _date_subsection("\U0001f535", "예정", fu_i)
        if s: i_parts.append(s)
        sections.append("\n".join(i_parts))

    # 외부
    e_count = len(pd_e) + len(tw_e) + len(fu_e)
    if e_count > 0:
        e_parts = [f"\n\u3010외부\u3011 ({e_count}건)"]
        s = _date_subsection("\U0001f534", "날짜지남", pd_e, True)
        if s: e_parts.append(s)
        s = _date_subsection("\U0001f7e1", "이번주", tw_e, True)
        if s: e_parts.append(s)
        s = _date_subsection("\U0001f535", "예정", fu_e, True)
        if s: e_parts.append(s)
        sections.append("\n".join(e_parts))

    # 기표완료
    if completed:
        c_lines = [f"\n\u2b1c 기표완료 ({len(completed)}건)"]
        total_loan_i = 0
        total_comm_i = 0
        total_loan_e = 0
        total_comm_e = 0
        if co_i:
            c_lines.append("  \u3010내부\u3011")
            for r in co_i:
                c_lines.append(f"  {_format_completed_line(r)}")
                total_loan_i += _safe_int(r.get("loan", ""))
                total_comm_i += _safe_int(r.get("commission_amount", ""))
        if co_e:
            c_lines.append("  \u3010외부\u3011")
            for r in co_e:
                c_lines.append(f"  {_format_completed_line(r, is_external=True)}")
                total_loan_e += _safe_int(r.get("loan", ""))
                total_comm_e += _safe_int(r.get("ext_commission", ""))
        # 합계
        c_lines.append("")
        total_loan = total_loan_i + total_loan_e
        total_comm = total_comm_i + total_comm_e
        c_lines.append(f"  대출금합계: {total_loan:,}만")
        if total_comm_i:
            c_lines.append(f"  내부 수수료합계: {total_comm_i:,}원")
        if total_comm_e:
            c_lines.append(f"  외부 수수료합계: {total_comm_e:,}원")
        if total_comm:
            c_lines.append(f"  수수료 총합계: {total_comm:,}원")

        sections.append("\n".join(c_lines))

    if not sections:
        return header + "\n활성 고객이 없습니다."

    return header + "\n".join(sections)


def _build_briefing_ai_prompt(rows):
    """3단계: Claude API에 보낼 프롬프트 구성."""
    now = datetime.now()
    wd = ["월","화","수","목","금","토","일"][now.weekday()]
    lines = [f"오늘: {now.strftime('%Y-%m-%d')} ({wd}요일)\n"]
    lines.append("아래는 보증금담보대출 영업자 정상준의 고객 관리 엑셀(H시트)이다.")
    lines.append("각 고객의 상황을 분석하고 내일 확인해야 할 우선순위별 브리핑을 만들어라.\n")
    lines.append("컬럼: 2차상담(현재메모) | 1차상담(상세) | 접수일 | 고객상태 | 이름 | 주소 | 연락처 | 대출금(만원) | 소득 | 신용상태 | 종류 | 은행\n")

    for r in rows:
        parts = [
            _compact_multiline_value(r.get("second_consult", "")),
            _compact_multiline_value(r.get("first_consult", ""))[:80],
            r.get("second_date", "") or r.get("first_date", ""),
            r.get("customer_status", ""),
            r.get("name", ""),
            r.get("address", ""),
            r.get("phone", ""),
            r.get("loan", ""),
            r.get("income", ""),
            r.get("credit", ""),
            r.get("kind", ""),
            r.get("bank", ""),
        ]
        lines.append(" | ".join(parts))

    lines.append("\n\n출력 형식:")
    lines.append("\U0001f534 긴급 \u2014 이번주 계약/자서/만기 임박 (왜 긴급인지, 구체적 액션)")
    lines.append("\U0001f7e1 이번주 액션 \u2014 자서일정 잡기, 기표일 확정 등")
    lines.append("\U0001f7e2 대기 \u2014 재연락 시점과 사유")
    lines.append("\u2b1c 기표완료 \u2014 사후관리 포인트")
    lines.append("\n각 고객마다 1~2줄로 상황+액션을 써라. 주민번호는 절대 포함하지 마라.")
    lines.append("금리가 0%인 고객은 아직 승인 전이다.")
    return "\n".join(lines)


@_with_chat_session_arg(0)
def _commit_ai_briefing_step1(chat_id, rows, past_due, this_week, future, completed):
    global _briefing_cached_rows, _briefing_classified, user_state
    if user_state != AI_BRIEFING_RUNNING_STATE:
        return False
    _clear_pending_briefing()
    _briefing_cached_rows = [dict(item or {}) for item in list(rows or [])]
    _briefing_classified["past_due"] = [dict(item or {}) for item in list(past_due or [])]
    _briefing_classified["this_week"] = [dict(item or {}) for item in list(this_week or [])]
    _briefing_classified["future"] = [dict(item or {}) for item in list(future or [])]
    _briefing_classified["completed"] = [dict(item or {}) for item in list(completed or [])]
    user_state = 35
    return True


@_with_chat_session_arg(0)
def _reset_ai_briefing_step1(chat_id):
    global user_state
    if user_state != AI_BRIEFING_RUNNING_STATE:
        return False
    _clear_pending_briefing()
    user_state = 0
    return True


def _start_ai_briefing_step1(chat_id):
    global user_state
    _clear_pending_briefing()
    user_state = AI_BRIEFING_RUNNING_STATE
    bot.send_message(chat_id, "\U0001f4ca H시트 읽기를 백그라운드로 시작했습니다.")
    _start_background_task(chat_id, "H시트 브리핑", _send_ai_briefing_step1, chat_id)


def _send_ai_briefing_step1(chat_id):
    """68번: 1단계 H시트 읽기 + 2단계 간단분석."""
    ok, payload = _fetch_all_h_rows()
    if not ok:
        if not _reset_ai_briefing_step1(chat_id):
            return
        bot.send_message(chat_id, f"\u274c H시트 조회 실패\n{payload}")
        bot.send_message(chat_id, show_list())
        return

    rows = payload.get("rows", [])
    if not rows:
        if not _reset_ai_briefing_step1(chat_id):
            return
        bot.send_message(chat_id, "\u274c 활성 고객이 없습니다.")
        bot.send_message(chat_id, show_list())
        return

    past_due, this_week, future, completed = _classify_briefing_rows(rows)
    report = _format_simple_briefing(past_due, this_week, future, completed)

    report += "\n\n" + "\u2501" * 18 + "\n"
    report += "1. \U0001f534 날짜지남 AI분석\n"
    report += "2. \U0001f7e1 이번주 AI분석\n"
    report += "3. \U0001f535 예정 AI분석\n"
    report += "4. 전체 AI분석\n"
    report += "5. 내가 선택한 고객만 분석\n"
    report += "0. 메뉴로 돌아가기"

    if not _commit_ai_briefing_step1(chat_id, rows, past_due, this_week, future, completed):
        return
    send_long_message(chat_id, report)


@_with_chat_session_arg(0)
def _finish_ai_briefing_step2(chat_id):
    global user_state
    if user_state != AI_BRIEFING_RUNNING_STATE:
        return False
    _clear_pending_briefing()
    user_state = 0
    return True


def _start_ai_briefing_step2(chat_id, rows=None, raw_text=None):
    global _briefing_cached_rows, user_state

    selected_rows = rows
    if selected_rows is None:
        selected_rows = _briefing_cached_rows
    selected_rows = [dict(item or {}) for item in list(selected_rows or [])]

    if not raw_text and not selected_rows:
        bot.send_message(chat_id, "\u274c 캐시된 고객 데이터가 없습니다. 68번을 다시 실행해주세요.")
        user_state = 0
        return

    _clear_pending_briefing()
    user_state = AI_BRIEFING_RUNNING_STATE
    if raw_text:
        bot.send_message(chat_id, "\U0001f916 선택 고객 Claude API 분석을 백그라운드로 시작했습니다.")
    else:
        bot.send_message(chat_id, "\U0001f916 Claude API 분석을 백그라운드로 시작했습니다.")
    _start_background_task(chat_id, "AI 브리핑", _run_ai_briefing_step2, chat_id, selected_rows, raw_text)


def _run_ai_briefing_step2(chat_id, rows=None, raw_text=None):
    """68번: 3단계 Claude API 상세분석."""
    if raw_text:
        now = datetime.now()
        wd = ["월","화","수","목","금","토","일"][now.weekday()]
        prompt = (
            f"오늘: {now.strftime('%Y-%m-%d')} ({wd}요일)\n\n"
            "아래는 보증금담보대출 영업자 정상준의 고객 관리 데이터다.\n"
            "각 고객의 상황을 분석하고 우선순위별 브리핑을 만들어라.\n"
            "각 고객마다 1~2줄로 상황+액션을 써라. 주민번호는 절대 포함하지 마라.\n\n"
            f"{raw_text}"
        )
        ok, result = _call_anthropic_messages(
            system_prompt="당신은 보증금담보대출 영업 관리 어시스턴트입니다. 고객 데이터를 분석하고 실무적인 브리핑을 만듭니다. 한국어로 답변하세요.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        if not _finish_ai_briefing_step2(chat_id):
            return
        if ok:
            send_long_message(chat_id, f"\U0001f916 AI 선택 분석\n\n{result}")
        else:
            send_long_message(chat_id, f"\u274c AI 분석 실패\n{result}")
        bot.send_message(chat_id, show_list())
        return

    if not rows:
        if _finish_ai_briefing_step2(chat_id):
            bot.send_message(chat_id, "\u274c 캐시된 고객 데이터가 없습니다. 68번을 다시 실행해주세요.")
            bot.send_message(chat_id, show_list())
        return

    prompt = _build_briefing_ai_prompt(rows)
    ok, result = _call_anthropic_messages(
        system_prompt="당신은 보증금담보대출 영업 관리 어시스턴트입니다. 고객 데이터를 분석하고 실무적인 브리핑을 만듭니다. 한국어로 답변하세요.",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.3,
    )

    if not _finish_ai_briefing_step2(chat_id):
        return
    if ok:
        send_long_message(chat_id, f"\U0001f916 AI 상세 분석\n\n{result}")
    else:
        send_long_message(chat_id, f"\u274c AI 분석 실패\n{result}")
    bot.send_message(chat_id, show_list())


def _format_processing_wait_message(label):
    return (
        f"⏳ {label} 처리 중입니다.\n"
        "완료 메시지가 올 때까지 잠시 기다려 주세요.\n"
        "0. 초기화면"
    )

def display_script_name(filename):
    if not filename:
        return ""
    if filename.endswith(".py"):
        return filename[:-3] + " (py)"
    return filename

auto_script = resolve_script_path("admin접수.py")

def decode_output(data):
    if not data:
        return ""
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")

def read_tail(path, max_lines=40):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-max_lines:]).strip()
    except Exception:
        return ""

def send_long_message(chat_id, text, chunk_size=3500):
    message = (text or "").strip()
    if not message:
        return
    for i in range(0, len(message), chunk_size):
        bot.send_message(chat_id, message[i:i + chunk_size])

def send_capture_if_exists(chat_id, capture_path, caption):
    try:
        if os.path.exists(capture_path):
            with open(capture_path, "rb") as f:
                bot.send_photo(chat_id, f, caption=caption)
    except Exception:
        pass

def _looks_like_public(source):
    s = source.replace("\n", " ")
    return bool(re.search(r"(^|[,\s/])키움($|[,\s/])", s)) or "공공임대선순위" in s

def detect_loan_option(text):
    source = (text or "").strip()
    has_private = ("키움민간" in source) or ("민간" in source)
    has_public = _looks_like_public(source)
    has_credit = any(k in source for k in ("신용관리", "신용불량", "연체", "신불", "채불"))
    has_rehab = any(k in source for k in ("회파복", "개인회생", "회생", "파산면책", "파산", "신용회복", "회복"))
    has_normal = any(k in source for k in ("신용정상", "정상"))

    # 접수에 키움민간이 있으면 민간 우선
    if has_private:
        if has_rehab:
            return "4"
        if has_credit:
            return "3"
        if has_normal:
            return "2"
        return "2"

    if has_public:
        return "1"

    # 민간 언급 없으면 무조건 공공임대선순위 (대원칙)
    # 회파복/신용관리로 키움↔키움민간을 구분하지 않는다
    return "1"


def _kiwoom_option_from_kind(value):
    s = str(value or "").strip()
    if s in {"1", "2", "3", "4"}:
        return s
    if "공공임대선순위" in s:
        return "1"
    if "신용관리" in s:
        return "3"
    if ("회파복" in s) or ("개인회생" in s) or ("신용회복" in s) or ("파산" in s):
        return "4"
    if "민간임대" in s:
        return "2"
    if "키움민간" in s:
        return "2"
    return detect_loan_option(s)


def _kiwoom_kind_label(option):
    return {
        "1": "공공임대선순위_N",
        "2": "민간임대(선순위)",
        "3": "민간임대(신용관리)",
        "4": "민간임대(회파복)",
    }.get(str(option or "").strip(), "공공임대선순위_N")


def _kiwoom_credit_label(value):
    s = str(value or "").strip()
    if not s:
        return ""
    low = s.lower().replace(" ", "")
    if s in {"1", "신용정상"} or "정상" in s:
        return "신용정상"
    if s in {"2", "회파복"} or any(k in s for k in ("개인회생", "회생", "신용회복", "회복", "파산면책", "파산", "회파복")):
        return "회파복"
    if s in {"3", "신용관리", "신용관리(신불)"} or any(k in s for k in ("신용불량", "신불", "채불", "연체", "신용관리")):
        return "신용관리(신불)"
    if low in {"normal", "good"}:
        return "신용정상"
    return ""


def _kiwoom_option_from_credit(value):
    label = _kiwoom_credit_label(value)
    if label == "신용정상":
        return "2"
    if label == "신용관리(신불)":
        return "3"
    if label == "회파복":
        return "4"
    return ""

def has_deposit_input(text):
    source = (text or "").strip()
    if not source:
        return False

    if common_parse_customer_text is not None:
        try:
            parsed = common_parse_customer_text(source)
            if parsed:
                has_core = any(str(parsed.get(k, "") or "").strip() for k in ("이름", "주민번호", "연락처", "주소"))
                has_amount = any(_digits_only(parsed.get(k, "")) for k in ("보증금", "대출금"))
                if has_core and has_amount:
                    return True
        except Exception:
            pass

    # 1) 라벨형: 보증금: 1200
    if re.search(r"보증금\s*[>:：]?\s*\d", source):
        return True

    # 2) 줄형: 숫자 2줄(보증금, 대출금)
    lines = [ln.strip() for ln in source.splitlines() if ln.strip()]
    numeric_lines = [ln for ln in lines if re.fullmatch(r"[0-9,\s]{3,8}", ln)]
    return len(numeric_lines) >= 2

def detect_implicit_amount_pair(text):
    source = (text or "").strip()
    if not source:
        return None

    has_dep_label = bool(re.search(r"보증금\s*[>:：]?\s*\d", source))
    has_loan_label = bool(re.search(r"대출금\s*[>:：]?\s*\d", source))
    if has_dep_label or has_loan_label:
        return None

    lines = [ln.strip() for ln in source.splitlines() if ln.strip()]
    numeric_lines = [ln for ln in lines if re.fullmatch(r"[0-9,\s]{3,8}", ln)]
    if len(numeric_lines) < 2:
        return None

    dep = re.sub(r"\D", "", numeric_lines[0])
    loan = re.sub(r"\D", "", numeric_lines[1])
    if not dep or not loan:
        return None
    return dep, loan

def _extract_amount_by_label(source, label):
    m = re.search(rf"{label}\s*[>:：]?\s*([0-9,\s]{{2,8}})", source)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    if not digits:
        return None
    try:
        return int(digits)
    except Exception:
        return None

def _extract_ms_amounts(text):
    source = (text or "").strip()
    dep = _extract_amount_by_label(source, "보증금")
    loan = _extract_amount_by_label(source, "대출금")

    if dep is None or loan is None:
        lines = [ln.strip() for ln in source.splitlines() if ln.strip()]
        numeric_lines = [ln for ln in lines if re.fullmatch(r"[0-9,\s]{3,8}", ln)]
        if dep is None and len(numeric_lines) >= 1:
            try:
                dep = int(re.sub(r"\D", "", numeric_lines[0]))
            except Exception:
                dep = None
        if loan is None and len(numeric_lines) >= 2:
            try:
                loan = int(re.sub(r"\D", "", numeric_lines[1]))
            except Exception:
                loan = None
    return dep, loan

def _ms_general_ltv_rate(deposit_manwon):
    d = deposit_manwon
    if d is None:
        return None
    if 800 <= d < 1000:
        return 0.60
    if 1000 <= d < 1500:
        return 0.70
    if 1500 <= d < 2000:
        return 0.75
    if 2000 <= d < 2500:
        return 0.80
    if 2500 <= d < 6000:
        return 0.90
    if d >= 6000:
        return 0.95
    return None

def infer_ms_product_preview(text):
    dep, loan = _extract_ms_amounts(text)
    source = (text or "")
    is_refinance = ("대환" in source)

    rate = _ms_general_ltv_rate(dep)
    limit_kind = "일반한도"
    if dep is not None and loan is not None and rate is not None:
        normal_limit = int(dep * rate)
        if dep >= 1000 and loan > normal_limit and loan <= dep:
            limit_kind = "복합한도"

    if is_refinance:
        if limit_kind == "복합한도":
            return "3", "임대아파트대출(대환복합)", limit_kind
        return "2", "임대아파트대출(대환)", limit_kind

    if limit_kind == "복합한도":
        return "4", "임대아파트대출(복합)", limit_kind
    return "1", "임대아파트대출", limit_kind

def _clear_pending_followup():
    global pending_followup_text, pending_followup_name, pending_followup_kind, pending_followup_option
    pending_followup_text = ""
    pending_followup_name = ""
    pending_followup_kind = ""
    pending_followup_option = ""

def _cancel_auto_timer(chat_id):
    key = str(chat_id)
    timer = AUTO_TIMER_REGISTRY.pop(key, None)
    if timer is not None:
        try:
            timer.cancel()
        except Exception:
            pass
    AUTO_TIMER_TOKEN_REGISTRY[key] = int(AUTO_TIMER_TOKEN_REGISTRY.get(key) or 0) + 1

def _arm_auto_timer(chat_id, seconds, expected_state, action):
    key = str(chat_id)
    _cancel_auto_timer(chat_id)
    token = int(AUTO_TIMER_TOKEN_REGISTRY.get(key) or 0) + 1
    AUTO_TIMER_TOKEN_REGISTRY[key] = token

    def _runner():
        try:
            with CHAT_STATE_LOCK:
                current = _get_chat_session(chat_id)
                if token != AUTO_TIMER_TOKEN_REGISTRY.get(key):
                    return
                if current.get("user_state") != expected_state:
                    return
                AUTO_TIMER_REGISTRY.pop(key, None)
            action()
        except Exception as e:
            try:
                bot.send_message(chat_id, f"자동 진행 오류: {e}")
            except Exception:
                pass

    t = threading.Timer(seconds, _runner)
    t.daemon = True
    AUTO_TIMER_REGISTRY[key] = t
    t.start()


def _ensure_message_chat_allowed(message):
    if message.chat.id in ALLOWED_CHAT_IDS:
        return True

    if AUTO_ALLOW_PRIVATE_CHAT and message.chat.type == "private":
        _remember_allowed_chat_id(message.chat.id)
        print(f"✅ 개인 대화방 자동 등록: {message.chat.id}")
        bot.send_message(
            message.chat.id,
            f"✅ 이 대화방({message.chat.id})을 자동 등록했습니다. 이제 명령을 사용할 수 있습니다."
        )
        bot.send_message(message.chat.id, show_list())
        return True

    print(f"⚠️ 등록되지 않은 대화방입니다. (현재 방 번호: {message.chat.id})")
    print("만약 이 방에서 봇을 쓰고 싶다면, 코드의 ALLOWED_CHAT_IDS에 위 숫자를 추가해 주세요.")
    try:
        bot.send_message(
            message.chat.id,
            f"⛔ 등록되지 않은 대화방입니다.\n현재 방 번호: {message.chat.id}\n관리자에게 허용 목록 등록을 요청해 주세요."
        )
    except Exception:
        pass
    return False


def _reset_chat_session_fast(chat_id):
    key = str(chat_id)
    replacement = _new_chat_session()
    _cancel_auto_timer(chat_id)

    if CHAT_STATE_LOCK.acquire(blocking=False):
        try:
            CHAT_SESSIONS[key] = replacement
            _load_chat_session(chat_id)
            globals()["pending_ivwith_sales_key"] = ""
            globals()["pending_ivwith_sales_display"] = ""
            globals()["_briefing_cached_rows"] = []
            globals()["_briefing_classified"] = {}
            return True
        finally:
            CHAT_STATE_LOCK.release()

    CHAT_SESSIONS[key] = replacement
    return False

def _extract_name_from_text(text):
    if common_parse_customer_text is not None:
        try:
            parsed = common_parse_customer_text(text)
            if parsed and (parsed.get("이름") or "").strip():
                return parsed.get("이름").strip()
        except Exception:
            pass

    source = (text or "").strip()
    m = re.search(r"이름\s*[>:：]?\s*([가-힣A-Za-z]{2,12})", source)
    if m:
        return m.group(1)
    for line in source.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("이건패스>"):
            continue
        if ":" in s or ">" in s:
            continue
        if any(ch.isdigit() for ch in s):
            continue
        if any(k in s for k in ("시", "도", "구", "군", "동", "읍", "면", "로", "길")):
            continue
        if 1 < len(s) <= 12:
            return s
    return "고객"

def _digits_only(value):
    return re.sub(r"\D", "", str(value or ""))


def _normalize_mac(mac_text):
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", str(mac_text or ""))
    if len(cleaned) != 12:
        return ""
    return cleaned.upper()


def _parse_wol_mac_from_text(text):
    raw = str(text or "").strip()
    if not raw:
        return ""
    low = raw.lower()

    if low.startswith("/wol"):
        parts = raw.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""

    if low.startswith("켜기"):
        return raw[2:].strip()

    if low.startswith("wake"):
        parts = raw.split(maxsplit=1)
        return parts[1].strip() if len(parts) > 1 else ""

    return ""


def _send_wol_magic_packet(mac_text, broadcast_ip=None, port=None):
    mac = _normalize_mac(mac_text)
    if not mac:
        return False, "MAC 주소 형식이 올바르지 않습니다."

    host = (broadcast_ip or WOL_BROADCAST_IP or "255.255.255.255").strip()
    p = int(port or WOL_PORT or 9)
    mac_bytes = bytes.fromhex(mac)
    packet = b"\xff" * 6 + mac_bytes * 16

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(packet, (host, p))
        return True, f"WOL 패킷 전송 완료 (MAC={mac}, {host}:{p})"
    except Exception as e:
        return False, f"WOL 패킷 전송 실패: {e}"


def _normalize_payload_for_followup(raw_text):
    if common_parse_customer_text is None:
        return raw_text
    try:
        parsed = common_parse_customer_text(raw_text)
    except Exception:
        return raw_text
    if not parsed:
        return raw_text

    lines = []
    for key in ("이름", "주민번호", "연락처", "주소"):
        val = (parsed.get(key) or "").strip()
        if key == "주소":
            val = _normalize_address_text(val)
        if val:
            lines.append(f"{key}: {val}")

    dep = _digits_only(parsed.get("보증금", ""))
    loan = _digits_only(parsed.get("대출금", ""))
    if dep:
        lines.append(f"보증금: {dep}")
    if loan:
        lines.append(f"대출금: {loan}")

    for key in ("종류", "접수", "신용", "기타"):
        val = (parsed.get(key) or "").strip()
        if val:
            lines.append(f"{key}: {val}")

    # admin 검토 화면에서 넣은 라벨값(상품번호/직업/전송메모 등)은 파서가 버릴 수 있어 원문 라인을 보존한다.
    keep_keys = {"상품번호", "상품선택", "직업", "직업구분", "전송메모"}
    src_lines = _split_nonempty_lines(raw_text)
    exist = set(lines)
    for src in src_lines:
        m = re.match(r"^\s*([^:：>\-]+)\s*[:：>\-]\s*(.+?)\s*$", src)
        if not m:
            continue
        key = m.group(1).strip()
        val = m.group(2).strip()
        if key in keep_keys and val:
            line = f"{key}: {val}"
            if line not in exist:
                lines.append(line)
                exist.add(line)

    return "\n".join(lines) if lines else raw_text


def _split_nonempty_lines(raw_text):
    source = str(raw_text or "").replace("\r\n", "\n").replace("\r", "\n")
    return [ln.strip() for ln in source.split("\n") if ln.strip()]


def _ms_option_to_label(option):
    return {
        "1": "임대아파트대출",
        "2": "임대아파트대출(대환)",
        "3": "임대아파트대출(대환복합)",
        "4": "임대아파트대출(복합)",
    }.get(str(option or "").strip(), "")


def _ms_option_limit_type(option):
    return "복합" if str(option or "").strip() in {"3", "4"} else "일반"


def _ms_kind_short(kind_text):
    s = str(kind_text or "").strip()
    if "대환" in s:
        return "대환"
    if ("입주" in s) or ("잔금" in s):
        return "입주"
    return "가계"


def _recompute_ms_review_derived(fields):
    dep = _digits_only(fields.get("보증금", ""))
    kind = _ms_kind_short(fields.get("종류", ""))
    opt = str(fields.get("상품선택", "") or "").strip()
    if opt not in {"1", "2", "3", "4"}:
        payload = _build_ms_payload_from_fields(fields, mode="ms")
        opt, _, _ = infer_ms_product_preview(payload)
        fields["상품선택"] = opt
    fields["신용"] = ""
    fields["직업구분"] = fields.get("직업구분") or "직장인"
    limit_text = _ms_option_limit_type(fields.get("상품선택"))
    fields["전송메모"] = f"보증금{dep}만/{kind}/{limit_text}" if dep else f"보증금/{kind}/{limit_text}"
    return fields


def _detect_credit_from_text(text):
    """텍스트에서 신용 상태 키워드 감지. 회복/회생/파산/면책 → 전부 회파복"""
    s = str(text or "").strip()
    if not s:
        return ""
    if any(k in s for k in ("신용회복", "회복", "개인회생", "회생", "파산면책", "파산", "면책", "회파복")):
        return "회파복"
    if any(k in s for k in ("신용관리", "신불", "채불", "연체")):
        return "신용관리"
    return ""

def _recompute_kiwoom_review_derived(fields):
    bank = str(fields.get("접수", "") or "").strip()
    credit = _kiwoom_credit_label(fields.get("신용", ""))
    # 기타 필드에 신용 키워드가 있으면 신용 판정에 반영 (세분화)
    if not credit or credit == "신용정상":
        etc_credit = _detect_credit_from_text(fields.get("기타", ""))
        if etc_credit:
            credit = etc_credit
    if credit:
        fields["신용"] = credit

    # 대원칙: 접수에 키움(민간)이 명시적으로 있을 때만 민간 종류 결정
    # 회파복/신용관리로 키움↔키움민간을 구분하지 않는다
    if bank == "키움(민간)":
        if credit == "회파복":
            fields["종류"] = "민간임대(회파복)"
        elif credit == "신용관리(신불)":
            fields["종류"] = "민간임대(신용관리)"
        else:
            fields["종류"] = "민간임대(선순위)"
    else:
        fields["종류"] = "공공임대선순위_N"
        if not bank or bank == "키움":
            fields["접수"] = "키움"
    job = str(fields.get("직업구분", "") or "").strip()
    if job not in {"직장인", "프리랜서", "자영/사업"}:
        fields["직업구분"] = "직장인"
    return fields

def _ms_option_from_kind_text(kind_text):
    s = str(kind_text or "").strip()
    if not s:
        return ""
    compact = s.replace(" ", "")
    if compact in {"1", "01"}:
        return "1"
    if compact in {"2", "02"}:
        return "2"
    if compact in {"3", "03"}:
        return "3"
    if compact in {"4", "04"}:
        return "4"
    if "대환복합" in s:
        return "3"
    if "대환" in s:
        return "2"
    if "복합" in s:
        return "4"
    if "임대아파트대출" in s:
        return "1"
    return ""


def _recompute_admin_review_derived(fields):
    bank = _normalize_admin_bank(str(fields.get("접수", "") or ""))
    if bank:
        fields["접수"] = bank
    else:
        bank = str(fields.get("접수", "") or "").strip()

    job = str(fields.get("직업구분", "") or "").strip()
    if job not in {"직장인", "프리랜서", "자영/사업"}:
        fields["직업구분"] = "직장인"

    kind = str(fields.get("종류", "") or "").strip()
    credit = str(fields.get("신용", "") or "").strip()

    if bank == "MS저축은행":
        compact_kind = kind.replace(" ", "")
        explicit_ms_kind = (
            compact_kind in {"1", "01", "2", "02", "3", "03", "4", "04"}
            or "임대아파트대출" in kind
            or "대환복합" in kind
            or compact_kind == "복합"
        )
        option = _ms_option_from_kind_text(kind)
        if option not in {"1", "2", "3", "4"} or not explicit_ms_kind:
            payload_guess = "\n".join(
                line for line in (
                    f"보증금: {fields.get('보증금', '')}",
                    f"대출금: {fields.get('대출금', '')}",
                    f"종류: {kind}",
                )
                if str(line or "").strip()
            )
            option, _, _ = infer_ms_product_preview(payload_guess)
        fields["상품선택"] = option
        fields["종류"] = _ms_option_to_label(option) or "임대아파트대출"

        if credit in {"1", "정상", "신용정상"}:
            fields["신용"] = "신용정상"
        elif credit in {"2", "개인회생"} or "회생" in credit:
            fields["신용"] = "개인회생"
        elif credit in {"3", "신용회복"} or "회복" in credit:
            fields["신용"] = "신용회복"
        elif credit in {"4", "파산면책"} or "파산" in credit:
            fields["신용"] = "파산면책"
        elif not credit:
            fields["신용"] = "신용정상"
        fields["접수"] = "MS저축은행"
        return fields

    fields["상품선택"] = ""

    # 신용 정규화 (접수/종류 변경 전에 먼저 확정)
    # 기타 필드에 신용 키워드가 있으면 세분화 반영
    if credit in {"1", "정상", "신용정상"} or not credit:
        etc_credit = _detect_credit_from_text(fields.get("기타", ""))
        if etc_credit:
            credit = etc_credit
        elif not credit:
            credit = "신용정상"
        else:
            credit = "신용정상"
    elif credit in {"2", "회파복"} or any(k in credit for k in ("개인회생", "회생", "신용회복", "회복", "파산")):
        credit = "회파복"
    elif credit in {"3", "신용관리"} or any(k in credit for k in ("신용관리", "신용불량", "신불", "채불", "연체")):
        credit = "신용관리"

    # 접수는 사용자 입력값 유지 (키움/키움(민간) 자동전환 안 함)
    # 키움(민간)은 입력에 "민간"이 명시적으로 있을 때만
    if bank == "키움(민간)":
        # 민간 계열 종류 결정
        kiwoom_mingan_kinds = {"민간임대(선순위)", "민간임대(신용관리)", "민간임대(회파복)"}
        if kind not in kiwoom_mingan_kinds:
            if credit == "회파복":
                kind = "민간임대(회파복)"
            elif credit == "신용관리":
                kind = "민간임대(신용관리)"
            else:
                kind = "민간임대(선순위)"
    else:
        # 키움(공공) 또는 기타
        kind = "공공임대선순위_N"
        if not bank or bank == "키움":
            fields["접수"] = "키움"

    fields["종류"] = kind
    fields["신용"] = credit
    return fields


def _parse_ms_fields(raw_text, mode="ms"):
    if mode == "ms":
        target_order = MS_REVIEW_FIELD_ORDER
    elif mode == "kiwoom":
        target_order = KIWOOM_REVIEW_FIELD_ORDER
    elif mode == "admin":
        target_order = ADMIN_REVIEW_FIELD_ORDER
    else:
        target_order = MS_FIELD_ORDER
    fields = {k: "" for k in target_order}
    parsed = None
    if common_parse_customer_text is not None:
        try:
            parsed = common_parse_customer_text(raw_text)
        except Exception:
            parsed = None

    if mode == "ms":
        if parsed:
            fields["이름"] = str(parsed.get("이름", "") or "").strip()
            fields["주민번호"] = str(parsed.get("주민번호", "") or "").strip()
            fields["연락처"] = str(parsed.get("연락처", "") or "").strip()
            fields["주소"] = _normalize_address_text(str(parsed.get("주소", "") or "").strip())
            fields["보증금"] = _digits_only(parsed.get("보증금", ""))
            fields["대출금"] = _digits_only(parsed.get("대출금", ""))
            fields["종류"] = str(parsed.get("종류", "") or "").strip()
            src_job = str(parsed.get("직업", "") or parsed.get("기타", "") or "").strip()
            fields["직업구분"] = "자영/사업" if any(k in src_job for k in ("사업", "자영")) else "직장인"
        if not fields["이름"]:
            fields["이름"] = _extract_name_from_text(raw_text)
        fields["주소"] = _normalize_address_text(fields.get("주소", ""))
        if not fields["종류"]:
            raw = str(raw_text or "")
            if "대환" in raw:
                fields["종류"] = "대환"
            elif any(k in raw for k in ("입주", "잔금")):
                fields["종류"] = "입주"
            else:
                fields["종류"] = "가계"
        payload_guess = _normalize_payload_for_followup(raw_text)
        option, _, _ = infer_ms_product_preview(payload_guess)
        fields["상품선택"] = option
        fields = _recompute_ms_review_derived(fields)
        return fields

    if mode == "kiwoom":
        if parsed:
            for key in KIWOOM_REVIEW_FIELD_ORDER:
                if key == "직업구분":
                    continue
                fields[key] = str(parsed.get(key, "") or "").strip()
            src_job = str(parsed.get("직업", "") or parsed.get("기타", "") or "").strip()
            if any(k in src_job for k in ("자영", "사업")):
                fields["직업구분"] = "자영/사업"
            elif "프리" in src_job:
                fields["직업구분"] = "프리랜서"
            else:
                fields["직업구분"] = "직장인"
        if not fields["이름"]:
            fields["이름"] = _extract_name_from_text(raw_text)
        fields["주소"] = _normalize_address_text(fields.get("주소", ""))
        for key in ("보증금", "대출금"):
            fields[key] = _digits_only(fields.get(key))
        fields = _recompute_kiwoom_review_derived(fields)
        return fields

    # admin 검토용
    if parsed:
        for key in ("이름", "주민번호", "연락처", "주소", "보증금", "대출금", "접수", "종류", "신용", "기타"):
            fields[key] = str(parsed.get(key, "") or "").strip()
        src_job = str(parsed.get("직업", "") or parsed.get("기타", "") or "").strip()
        if any(k in src_job for k in ("자영", "사업")):
            fields["직업구분"] = "자영/사업"
        elif "프리" in src_job:
            fields["직업구분"] = "프리랜서"
        else:
            fields["직업구분"] = "직장인"

    if not fields["이름"]:
        fields["이름"] = _extract_name_from_text(raw_text)
    fields["주소"] = _normalize_address_text(fields.get("주소", ""))
    # 키움(민간)은 원문에 "민간" 텍스트가 있을 때만 허용; GPT 오추론 방지
    if fields.get("접수") in {"키움민간", "키움(민간)"} and "민간" not in str(raw_text or ""):
        fields["접수"] = "키움"
    if not fields["접수"]:
        fields["접수"] = detect_admin_bank(raw_text)
    for key in ("보증금", "대출금"):
        fields[key] = _digits_only(fields.get(key))

    if not str(fields.get("종류", "")).strip():
        raw = str(raw_text or "")
        if "대환" in raw:
            fields["종류"] = "대환"
        elif any(k in raw for k in ("입주", "잔금", "계잔")):
            fields["종류"] = "입주"
        else:
            fields["종류"] = "가계"

    fields = _recompute_admin_review_derived(fields)
    return fields


def _build_ms_payload_from_fields(fields, mode="ms"):
    lines = []
    if mode == "ms":
        name = str((fields or {}).get("이름", "") or "").strip()
        jumin = str((fields or {}).get("주민번호", "") or "").strip()
        phone = str((fields or {}).get("연락처", "") or "").strip()
        addr = str((fields or {}).get("주소", "") or "").strip()
        dep = _digits_only((fields or {}).get("보증금", ""))
        loan = _digits_only((fields or {}).get("대출금", ""))
        kind = str((fields or {}).get("종류", "") or "").strip()
        job = str((fields or {}).get("직업구분", "") or "").strip() or "직장인"
        memo = str((fields or {}).get("전송메모", "") or "").strip()
        option = str((fields or {}).get("상품선택", "") or "").strip()

        if name:
            lines.append(f"이름: {name}")
        if jumin:
            lines.append(f"주민번호: {jumin}")
        if phone:
            lines.append(f"연락처: {phone}")
        if addr:
            lines.append(f"주소: {addr}")
        if dep:
            lines.append(f"보증금: {dep}")
        if loan:
            lines.append(f"대출금: {loan}")
        lines.append("접수: MS저축은행")
        if kind:
            lines.append(f"종류: {kind}")
        if job:
            lines.append(f"직업: {job}")
        if memo:
            lines.append(f"전송메모: {memo}")
        if option in {"1", "2", "3", "4"}:
            lines.append(f"상품번호: {option}")
        return "\n".join(lines)

    if mode == "admin":
        name = str((fields or {}).get("이름", "") or "").strip()
        jumin = str((fields or {}).get("주민번호", "") or "").strip()
        phone = str((fields or {}).get("연락처", "") or "").strip()
        addr = str((fields or {}).get("주소", "") or "").strip()
        dep = _digits_only((fields or {}).get("보증금", ""))
        loan = _digits_only((fields or {}).get("대출금", ""))
        bank = str((fields or {}).get("접수", "") or "").strip()
        kind = str((fields or {}).get("종류", "") or "").strip()
        credit = str((fields or {}).get("신용", "") or "").strip()
        job = str((fields or {}).get("직업구분", "") or "").strip()
        option = str((fields or {}).get("상품선택", "") or "").strip()
        etc = str((fields or {}).get("기타", "") or "").strip()

        if name:
            lines.append(f"이름: {name}")
        if jumin:
            lines.append(f"주민번호: {jumin}")
        if phone:
            lines.append(f"연락처: {phone}")
        if addr:
            lines.append(f"주소: {addr}")
        if dep:
            lines.append(f"보증금: {dep}")
        if loan:
            lines.append(f"대출금: {loan}")
        if bank:
            lines.append(f"접수: {bank}")
        if kind:
            lines.append(f"종류: {kind}")
        if credit:
            lines.append(f"신용: {credit}")
        if job:
            lines.append(f"직업: {job}")
        if option in {"1", "2", "3", "4"}:
            lines.append(f"상품번호: {option}")
        if etc:
            lines.append(f"기타: {etc}")
        return "\n".join(lines)

    if mode == "kiwoom":
        name = str((fields or {}).get("이름", "") or "").strip()
        jumin = str((fields or {}).get("주민번호", "") or "").strip()
        phone = str((fields or {}).get("연락처", "") or "").strip()
        addr = str((fields or {}).get("주소", "") or "").strip()
        dep = _digits_only((fields or {}).get("보증금", ""))
        loan = _digits_only((fields or {}).get("대출금", ""))
        bank = str((fields or {}).get("접수", "") or "").strip()
        kind = str((fields or {}).get("종류", "") or "").strip()
        credit = str((fields or {}).get("신용", "") or "").strip()
        etc = str((fields or {}).get("기타", "") or "").strip()
        job = str((fields or {}).get("직업구분", "") or "").strip() or "직장인"

        if name:
            lines.append(f"이름: {name}")
        if jumin:
            lines.append(f"주민번호: {jumin}")
        if phone:
            lines.append(f"연락처: {phone}")
        if addr:
            lines.append(f"주소: {addr}")
        if dep:
            lines.append(f"보증금: {dep}")
        if loan:
            lines.append(f"대출금: {loan}")
        if bank:
            lines.append(f"접수: {bank}")
        if kind:
            lines.append(f"종류: {kind}")
        if credit:
            lines.append(f"신용: {credit}")
        if etc:
            lines.append(f"기타: {etc}")
        if job:
            lines.append(f"직업: {job}")
        return "\n".join(lines)

    for key in MS_FIELD_ORDER:
        value = str((fields or {}).get(key, "") or "").strip()
        if not value:
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _format_ms_field_summary(fields, mode="ms"):
    payload = _build_ms_payload_from_fields(fields, mode=mode)
    title_map = {
        "ms": "ms신규접수",
        "admin": "admin접수",
        "kiwoom": "키움신규접수",
    }
    out = [f"🧾 [{title_map.get(mode, '입력')} 입력 확인]"]
    if mode == "ms":
        order = MS_REVIEW_FIELD_ORDER
    elif mode == "kiwoom":
        order = KIWOOM_REVIEW_FIELD_ORDER
    elif mode == "admin":
        order = MS_FIELD_ORDER
    else:
        order = MS_FIELD_ORDER
    for idx, key in enumerate(order, 1):
        raw_value = str((fields or {}).get(key, "") or "").strip()
        value = raw_value or "(비어있음)"
        if mode == "ms" and key == "상품선택":
            label = _ms_option_to_label(value)
            value = f"{value}. {label}" if (value and label) else (value or "(비어있음)")
        if mode == "ms" and key == "신용":
            value = "(공란 고정)"
        if mode == "admin" and key == "상품선택":
            label = _ms_option_to_label(raw_value)
            value = f"{raw_value}. {label}" if (raw_value and label) else (raw_value or "(비어있음)")
        out.append(f"{idx}. {key}: {value}")

    if mode == "ms":
        selected = str((fields or {}).get("상품선택", "") or "").strip()
        if selected in {"1", "2", "3", "4"}:
            product_no = selected
            product_label = _ms_option_to_label(selected)
            limit_kind = "복합한도" if _ms_option_limit_type(selected) == "복합" else "일반한도"
        else:
            product_no, product_label, limit_kind = infer_ms_product_preview(payload)
        out.extend(
            [
                "",
                f"자동판정 상품: {product_no}번 {product_label} ({limit_kind})",
            ]
        )
    elif mode == "kiwoom":
        option = _kiwoom_option_from_kind((fields or {}).get("종류", ""))
        label = _kiwoom_kind_label(option)
        out.extend(["", f"자동판정 대출유형: {label}"])
    elif mode == "admin":
        bank = _normalize_admin_bank(str((fields or {}).get("접수", "") or ""))
        out.extend(["", f"접수은행: {bank or '인식 실패(수정 필요)'}"])
        if bank == "MS저축은행":
            opt = str((fields or {}).get("상품선택", "") or "").strip()
            label = _ms_option_to_label(opt)
            if opt and label:
                out.append(f"MS 상품: {opt}. {label}")

    out.extend(
        [
            "",
            "1. 그대로 진행",
            "2. 수정",
            "3. 엑셀 통합관리 입력",
            "0. 초기화면",
        ]
    )
    return "\n".join(out)


def _format_ms_original_lines(lines, mode="ms"):
    src = lines or []
    title_map = {
        "ms": "ms신규접수",
        "admin": "admin접수",
        "kiwoom": "키움신규접수",
    }
    out = [f"📝 [{title_map.get(mode, '입력')}] 처음 입력한 텍스트(줄번호)"]
    if not src:
        out.append("(원문 줄 없음)")
        return "\n".join(out)
    for i, line in enumerate(src, 1):
        out.append(f"{i}. {line}")
    return "\n".join(out)

def _is_region_prefix(token):
    t = str(token or "").strip().strip(",")
    if not t:
        return False
    if t in REGION_PREFIXES:
        return True
    if t.startswith("서울") or t.startswith("경기") or t.startswith("인천") or t.startswith("부산") or t.startswith("대구") or t.startswith("대전") or t.startswith("광주") or t.startswith("울산") or t.startswith("세종"):
        return True
    return False

def _normalize_address_text(value):
    s = re.sub(r"\s+", " ", str(value or "").strip())
    if not s:
        return ""
    parts = [p for p in s.split(" ") if p]
    if len(parts) < 2:
        return s
    if _is_region_prefix(parts[0]):
        return s
    region_idx = -1
    for i, p in enumerate(parts):
        if _is_region_prefix(p):
            region_idx = i
            break
    if region_idx <= 0:
        return s
    reordered = parts[region_idx:] + parts[:region_idx]
    return " ".join(reordered)


def _normalize_ms_field_value(field_key, raw_value):
    value = str(raw_value or "").strip()
    if not value:
        return ""

    if field_key in {"보증금", "대출금"}:
        digits = _digits_only(value)
        return digits

    if field_key == "주민번호":
        digits = _digits_only(value)
        if len(digits) >= 13:
            return f"{digits[:6]}-{digits[6:13]}"
        return value

    if field_key == "연락처":
        digits = _digits_only(value)
        if len(digits) >= 11:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:11]}"
        return value

    if field_key == "접수":
        normalized = _normalize_admin_bank(value)
        return normalized or value

    if field_key == "주소":
        return _normalize_address_text(value)

    if field_key == "종류":
        compact = value.replace(" ", "")
        if compact in {"1", "01"}:
            return "가계"
        if compact in {"2", "02"}:
            return "입주"
        if compact in {"3", "03"}:
            return "대환"
        if any(k in value for k in ("가계", "가계자금")):
            return "가계"
        if any(k in value for k in ("입주", "잔금", "입주자금")):
            return "입주"
        if any(k in value for k in ("대환", "대환자금")):
            return "대환"
        if compact.isdigit():
            return ""
        return value

    return value


def _normalize_ms_field_value_by_mode(field_key, raw_value, mode="ms"):
    value = str(raw_value or "").strip()
    if mode == "admin":
        if field_key == "접수":
            if value in {"1", "MS", "ms", "엠에스", "MS저축은행"}:
                return "MS저축은행"
            if value in {"2", "키움"}:
                return "키움"
            if value in {"3", "키움(민간)", "키움민간"}:
                return "키움(민간)"
            if value in {"4", "뒤로가기"}:
                return "__BACK__"
            normalized = _normalize_admin_bank(value)
            return normalized or value
        if field_key == "종류":
            bank = _normalize_admin_bank(str((pending_ms_fields or {}).get("접수", "") or ""))
            if bank == "MS저축은행":
                if value in {"5", "뒤로가기"}:
                    return "__BACK__"
                if value in {"1"}:
                    return "임대아파트대출"
                if value in {"2"}:
                    return "임대아파트대출(대환)"
                if value in {"3"}:
                    return "임대아파트대출(대환복합)"
                if value in {"4"}:
                    return "임대아파트대출(복합)"
                option = _ms_option_from_kind_text(value)
                if option in {"1", "2", "3", "4"}:
                    return _ms_option_to_label(option)
                return value
            if bank == "키움(민간)":
                if value in {"4", "뒤로가기"}:
                    return "__BACK__"
                if value in {"1", "민간", "민간임대(선순위)"}:
                    return "민간임대(선순위)"
                if value in {"2", "신용관리", "민간임대(신용관리)"}:
                    return "민간임대(신용관리)"
                if value in {"3", "회파복", "민간임대(회파복)"}:
                    return "민간임대(회파복)"
                return "민간임대(선순위)"
            if bank == "키움":
                if value in {"2", "뒤로가기"}:
                    return "__BACK__"
                if value in {"1", "공공", "공공임대선순위_N"}:
                    return "공공임대선순위_N"
                return "공공임대선순위_N"
            return value
        if field_key == "신용":
            bank = _normalize_admin_bank(str((pending_ms_fields or {}).get("접수", "") or ""))
            if bank == "MS저축은행":
                if value in {"5", "뒤로가기"}:
                    return "__BACK__"
                if value in {"1", "정상", "신용정상"}:
                    return "신용정상"
                if value in {"2", "개인회생"} or "회생" in value:
                    return "개인회생"
                if value in {"3", "신용회복"} or "회복" in value:
                    return "신용회복"
                if value in {"4", "파산면책"} or "파산" in value:
                    return "파산면책"
                return value
            if value in {"4", "뒤로가기"}:
                return "__BACK__"
            if value in {"1", "정상", "신용정상"}:
                return "신용정상"
            if value in {"2", "회파복"} or any(k in value for k in ("회파복", "개인회생", "회생", "신용회복", "회복", "파산")):
                return "회파복"
            if value in {"3", "신용관리"} or any(k in value for k in ("신용관리", "신용불량", "신불", "채불", "연체")):
                return "신용관리"
            return value
        if field_key == "직업구분":
            if value in {"4", "뒤로가기"}:
                return "__BACK__"
            if value in {"1", "직장인"}:
                return "직장인"
            if value in {"2", "프리랜서", "프리"}:
                return "프리랜서"
            if value in {"3", "자영/사업", "자영", "사업"}:
                return "자영/사업"
            return "직장인"
        if field_key == "상품선택":
            if value in {"5", "뒤로가기"}:
                return "__BACK__"
            if value in {"1", "2", "3", "4"}:
                return value
            if "대환복합" in value:
                return "3"
            if "대환" in value:
                return "2"
            if "복합" in value:
                return "4"
            if "임대아파트대출" in value:
                return "1"
            return ""
        return _normalize_ms_field_value(field_key, raw_value)

    if mode == "kiwoom":
        if field_key == "종류":
            bank = str((pending_ms_fields or {}).get("접수", "") or "").strip()
            if bank == "키움(민간)":
                if value in {"4", "뒤로가기"}:
                    return pending_ms_fields.get("종류", "민간임대(선순위)")
                if value in {"1", "민간", "민간임대(선순위)"}:
                    return "민간임대(선순위)"
                if value in {"2", "신용관리", "민간임대(신용관리)"}:
                    return "민간임대(신용관리)"
                if value in {"3", "회파복", "민간임대(회파복)"}:
                    return "민간임대(회파복)"
                return "민간임대(선순위)"
            else:
                if value in {"2", "뒤로가기"}:
                    return pending_ms_fields.get("종류", "공공임대선순위_N")
                return "공공임대선순위_N"
        if field_key == "신용":
            return _kiwoom_credit_label(value)
        if field_key == "접수":
            if value in {"1", "키움"}:
                return "키움"
            if value in {"2", "키움(민간)", "키움민간"}:
                return "키움(민간)"
            normalized = _normalize_admin_bank(value)
            return normalized or "키움"
        if field_key == "직업구분":
            if value in {"1", "직장인"}:
                return "직장인"
            if value in {"2", "프리랜서", "프리"}:
                return "프리랜서"
            if value in {"3", "자영/사업", "자영", "사업"}:
                return "자영/사업"
            return "직장인"
        return _normalize_ms_field_value(field_key, raw_value)

    if mode != "ms":
        return _normalize_ms_field_value(field_key, raw_value)

    if field_key == "신용":
        return ""

    if field_key == "상품선택":
        if value in {"1", "2", "3", "4"}:
            return value
        if "대환복합" in value:
            return "3"
        if "대환" in value:
            return "2"
        if "복합" in value:
            return "4"
        if "임대아파트대출" in value:
            return "1"
        return ""

    if field_key == "직업구분":
        if value in {"1", "직장인"}:
            return "직장인"
        if value in {"2", "자영/사업", "자영", "사업"}:
            return "자영/사업"
        return "직장인"

    if field_key == "전송메모":
        return value

    return _normalize_ms_field_value(field_key, raw_value)


def _clear_pending_ms_edit():
    global pending_ms_script, pending_ms_fields, pending_ms_lines, pending_ms_edit_key, pending_ms_mode
    pending_ms_script = ""
    pending_ms_fields = {}
    pending_ms_lines = []
    pending_ms_edit_key = ""
    pending_ms_mode = "ms"




def _clear_pending_ivwith_sales():
    global pending_ivwith_report_type, pending_ivwith_sales_key, pending_ivwith_sales_display
    pending_ivwith_report_type = ""
    pending_ivwith_sales_key = ""
    pending_ivwith_sales_display = ""


def _clear_pending_briefing():
    global _briefing_cached_rows, _briefing_classified
    _briefing_cached_rows = []
    _briefing_classified = {}


def _review_order_by_mode(mode):
    if mode == "ms":
        return MS_REVIEW_FIELD_ORDER
    if mode == "kiwoom":
        return KIWOOM_REVIEW_FIELD_ORDER
    if mode == "admin":
        return ADMIN_REVIEW_FIELD_ORDER
    return MS_FIELD_ORDER


def _start_ms_edit_prompt(chat_id, idx, mode=None):
    global user_state, pending_ms_edit_key
    current_mode = mode or pending_ms_mode or "ms"
    order = _review_order_by_mode(current_mode)
    if not (1 <= idx <= len(order)):
        bot.send_message(chat_id, f"1~{len(order)} 중에서 선택해 주세요.")
        return

    pending_ms_edit_key = order[idx - 1]
    user_state = 15

    if current_mode == "ms" and pending_ms_edit_key == "상품선택":
        bot.send_message(
            chat_id,
            (
                "상품선택 번호를 입력하세요.\n"
                "1. 임대아파트대출\n"
                "2. 임대아파트대출(대환)\n"
                "3. 임대아파트대출(대환복합)\n"
                "4. 임대아파트대출(복합)"
            ),
        )
        return
    if current_mode == "ms" and pending_ms_edit_key == "직업구분":
        bot.send_message(
            chat_id,
            (
                "직업구분을 선택하세요.\n"
                "1. 직장인\n"
                "2. 자영/사업"
            ),
        )
        return
    if current_mode == "ms" and pending_ms_edit_key == "신용":
        pending_ms_fields["신용"] = ""
        pending_ms_edit_key = ""
        user_state = 13
        bot.send_message(chat_id, "신용은 공란 고정 항목입니다.\n\n" + _format_ms_field_summary(pending_ms_fields, mode=current_mode))
        return
    if current_mode == "admin" and pending_ms_edit_key == "접수":
        bot.send_message(
            chat_id,
            (
                "접수은행을 선택하세요.\n"
                "1. MS저축은행\n"
                "2. 키움\n"
                "3. 키움(민간)\n"
                "4. 뒤로가기"
            ),
        )
        return
    if current_mode == "admin" and pending_ms_edit_key == "종류":
        bank = _normalize_admin_bank(str((pending_ms_fields or {}).get("접수", "") or ""))
        if bank == "MS저축은행":
            bot.send_message(
                chat_id,
                (
                    "종류(MS 상품유형)를 선택하세요.\n"
                    "1. 임대아파트대출\n"
                    "2. 임대아파트대출(대환)\n"
                    "3. 임대아파트대출(대환복합)\n"
                    "4. 임대아파트대출(복합)\n"
                    "5. 뒤로가기"
                ),
            )
        elif bank == "키움(민간)":
            bot.send_message(
                chat_id,
                (
                    "종류(키움 민간)를 선택하세요.\n"
                    "1. 민간임대(선순위)\n"
                    "2. 민간임대(신용관리)\n"
                    "3. 민간임대(회파복)\n"
                    "4. 뒤로가기"
                ),
            )
        else:
            bot.send_message(
                chat_id,
                (
                    "종류(키움)를 선택하세요.\n"
                    "1. 공공임대선순위_N\n"
                    "2. 뒤로가기"
                ),
            )
        return
    if current_mode == "admin" and pending_ms_edit_key == "신용":
        bank = _normalize_admin_bank(str((pending_ms_fields or {}).get("접수", "") or ""))
        if bank == "MS저축은행":
            bot.send_message(
                chat_id,
                (
                    "신용 라벨(MS)을 선택하세요.\n"
                    "1. 신용정상\n"
                    "2. 개인회생\n"
                    "3. 신용회복\n"
                    "4. 파산면책\n"
                    "5. 뒤로가기"
                ),
            )
            return
        bot.send_message(
            chat_id,
            (
                "신용 라벨을 선택하세요.\n"
                "1. 신용정상\n"
                "2. 회파복\n"
                "3. 신용관리\n"
                "4. 뒤로가기"
            ),
        )
        return
    if current_mode == "admin" and pending_ms_edit_key == "직업구분":
        bot.send_message(
            chat_id,
            (
                "직업구분을 선택하세요.\n"
                "1. 직장인\n"
                "2. 프리랜서\n"
                "3. 자영/사업\n"
                "4. 뒤로가기"
            ),
        )
        return
    if current_mode == "admin" and pending_ms_edit_key == "상품선택":
        bot.send_message(
            chat_id,
            (
                "MS 상품번호를 선택하세요.\n"
                "1. 임대아파트대출\n"
                "2. 임대아파트대출(대환)\n"
                "3. 임대아파트대출(대환복합)\n"
                "4. 임대아파트대출(복합)\n"
                "5. 뒤로가기"
            ),
        )
        return
    if current_mode == "kiwoom" and pending_ms_edit_key == "종류":
        bank = str((pending_ms_fields or {}).get("접수", "") or "").strip()
        if bank == "키움(민간)":
            bot.send_message(
                chat_id,
                (
                    "종류(키움 민간)를 선택하세요.\n"
                    "1. 민간임대(선순위)\n"
                    "2. 민간임대(신용관리)\n"
                    "3. 민간임대(회파복)\n"
                    "4. 뒤로가기"
                ),
            )
        else:
            bot.send_message(
                chat_id,
                (
                    "종류(키움)를 선택하세요.\n"
                    "1. 공공임대선순위_N\n"
                    "2. 뒤로가기"
                ),
            )
        return
    if current_mode == "kiwoom" and pending_ms_edit_key == "신용":
        bot.send_message(
            chat_id,
            (
                "신용 라벨을 선택하세요.\n"
                "1. 신용정상\n"
                "2. 회파복\n"
                "3. 신용관리(신불)"
            ),
        )
        return
    if current_mode == "kiwoom" and pending_ms_edit_key == "직업구분":
        bot.send_message(
            chat_id,
            (
                "직업구분을 선택하세요.\n"
                "1. 직장인\n"
                "2. 프리랜서\n"
                "3. 자영/사업"
            ),
        )
        return
    bot.send_message(
        chat_id,
        (
            f"{pending_ms_edit_key} 값을 수정합니다.\n"
            f"{_format_ms_original_lines(pending_ms_lines, mode=current_mode)}\n\n"
            "원문 줄번호를 입력하면 해당 줄 내용으로 반영됩니다.\n"
            "또는 새 값을 직접 입력해도 됩니다.\n"
            "예) 6  또는  010-1234-5678"
        ),
    )


def _start_ms_review(chat_id, script_path_value, raw_text, mode="ms"):
    global user_state, pending_ms_script, pending_ms_fields, pending_ms_lines, pending_ms_edit_key, pending_ms_mode
    pending_ms_script = script_path_value
    pending_ms_fields = _parse_ms_fields(raw_text, mode=mode)
    if mode == "kiwoom" and not pending_ms_fields.get("접수"):
        pending_ms_fields["접수"] = "키움"
    pending_ms_lines = _split_nonempty_lines(raw_text)
    pending_ms_edit_key = ""
    pending_ms_mode = mode
    user_state = 13
    bot.send_message(chat_id, _format_ms_field_summary(pending_ms_fields, mode=mode))

def _normalize_admin_bank(raw):
    text = (raw or "").strip()
    if not text:
        return ""
    low = text.lower().replace(" ", "")
    if "키움민간" in text or ("키움" in text and "민간" in text):
        return "키움(민간)"
    if ("ms2.31" in low) or ("ms저축" in low) or ("엠에스" in text) or re.search(r"(^|[^a-z])ms([^a-z]|$)", low):
        return "MS저축은행"
    if "키움" in text:
        return "키움"
    return ""

def detect_admin_bank(text):
    source = (text or "").strip()
    for line in source.splitlines():
        s = line.strip()
        if not s:
            continue
        for key in ("접수", "은행", "은행접수"):
            if not s.startswith(key):
                continue
            val = s[len(key):].strip()
            val = re.sub(r"^[>:：\-\s]+", "", val).strip()
            bank = _normalize_admin_bank(val)
            if bank:
                return bank
            return ""
    return _normalize_admin_bank(source)

def _kiwoom_option_label(option):
    return {
        "1": "공공임대선순위_N",
        "2": "민간임대(선순위)",
        "3": "민간임대(신용관리)",
        "4": "민간임대(회파복)",
    }.get(option, "공공임대선순위_N")

def _extract_forced_ms_option(text):
    source = str(text or "").strip()
    if not source:
        return ""
    for line in source.splitlines():
        s = line.strip()
        if not s:
            continue
        for key in ("상품번호", "상품선택"):
            if not s.startswith(key):
                continue
            val = s[len(key):].strip()
            val = re.sub(r"^[>:：\-\s]+", "", val).strip()
            m = re.search(r"[1-4]", val)
            if m:
                return m.group(0)
        if s.startswith("종류"):
            val = s[len("종류"):].strip()
            val = re.sub(r"^[>:：\-\s]+", "", val).strip()
            opt = _ms_option_from_kind_text(val)
            if opt in {"1", "2", "3", "4"}:
                return opt
    return ""

def _run_admin_script(chat_id, script_path_value, raw_text):
    if not script_path_value:
        raise RuntimeError("admin접수.py 경로를 찾지 못했습니다.")
    bot.send_message(chat_id, "⏳ admin접수 진행 중...")
    env = os.environ.copy()
    env["BOT_BROWSER_HEADLESS"] = "1"
    result = subprocess.run(
        [PYTHON_EXE, script_path_value, raw_text],
        capture_output=True,
        cwd=BASE_DIR,
        env=env,
    )
    stdout_text = decode_output(result.stdout).strip()
    error_text = decode_output(result.stderr).strip()
    if result.returncode != 0:
        detail = error_text or stdout_text or "오류 출력 없음"
        bot.send_message(
            chat_id,
            f"❌ admin접수 실패 (returncode={result.returncode})\n{detail[:500]}",
        )
        return
    capture_path = script_path("bot_capture.png")
    if os.path.exists(capture_path):
        with open(capture_path, "rb") as f:
            bot.send_photo(chat_id, f, caption="✅ admin접수 완료")
    else:
        suffix = f"\n{stdout_text[:300]}" if stdout_text else ""
        bot.send_message(chat_id, "✅ admin접수 완료 (캡처 이미지 없음)" + suffix)


def _start_background_task(chat_id, label, target, *args, **kwargs):
    return start_background_task(bot, chat_id, label, target, *args, **kwargs)


def _run_result_check(chat_id, script_path_value, customer_name):
    script_name = os.path.basename(script_path_value or "")
    is_ms_result = script_name.lower().startswith("ms")
    log_name = "ms_result.log" if is_ms_result else "kiwoom_result.log"
    env_key = "MS_RESULT_LOG_PATH" if is_ms_result else "KIWOOM_LOG_PATH"
    prefix = "MS결과확인" if is_ms_result else "키움결과확인"

    result_log_path = os.path.join(BOT_LOG_DIR, log_name)
    env = os.environ.copy()
    env[env_key] = result_log_path
    env["BOT_BROWSER_HEADLESS"] = "1"
    result = subprocess.run(
        [PYTHON_EXE, script_path_value, customer_name],
        capture_output=True,
        cwd=BASE_DIR,
        env=env,
    )
    output_text = decode_output(result.stdout).strip()
    error_text = decode_output(result.stderr).strip()

    if output_text:
        send_long_message(chat_id, f"📄 [{prefix} 조회 완료]\n{output_text}")
        return
    if error_text:
        send_long_message(chat_id, f"❌ {prefix} 실행 오류\n{error_text[:3000]}")
        return

    debug_tail = read_tail(result_log_path, max_lines=50)
    bot.send_message(
        chat_id,
        (
            "❌ 조회 결과가 화면에 나오지 않았습니다.\n"
            f"returncode={result.returncode}, script={os.path.basename(script_path_value)}\n"
            f"python={PYTHON_EXE}\n"
            f"stdout_len={len(result.stdout or '')}, stderr_len={len(result.stderr or '')}"
        ),
    )
    if debug_tail:
        send_long_message(chat_id, f"[{log_name} 마지막 내용]\n{debug_tail[-3000:]}")


@_with_chat_session_arg(0)
def _snapshot_admin_followup(chat_id):
    global user_state, auto_script, pending_admin_text, pending_admin_bank, pending_admin_name
    _cancel_auto_timer(chat_id)
    raw_text = pending_admin_text
    bank = pending_admin_bank
    name = pending_admin_name or _extract_name_from_text(raw_text)
    script_path_value = auto_script or resolve_script_path("admin접수.py")
    pending_admin_text = ""
    pending_admin_bank = ""
    pending_admin_name = ""
    user_state = ADMIN_FLOW_RUNNING_STATE if raw_text else 0
    return {
        "script_path": script_path_value,
        "raw_text": raw_text,
        "bank": bank,
        "name": name,
    }


@_with_chat_session_arg(0)
def _finish_admin_then_followup(chat_id, raw_text, bank, name):
    global user_state
    if user_state != ADMIN_FLOW_RUNNING_STATE:
        return False
    _start_followup_flow(chat_id, raw_text, bank, name)
    return True


@_with_chat_session_arg(0)
def _reset_admin_followup_state(chat_id):
    global user_state
    if user_state == ADMIN_FLOW_RUNNING_STATE:
        user_state = 0


def _run_admin_then_followup(chat_id, script_path_value, raw_text, bank, name):
    _run_admin_script(chat_id, script_path_value, raw_text)
    _finish_admin_then_followup(chat_id, raw_text, bank, name)

@_with_chat_session_arg(0)
def _execute_ms_followup(chat_id, auto_trigger=False):
    global user_state
    _cancel_auto_timer(chat_id)
    if auto_trigger:
        bot.send_message(chat_id, "⏱️ 응답이 없어 자동으로 ms신규접수를 진행합니다.")
    payload = pending_followup_text
    choice = pending_followup_option or "1"
    _clear_pending_followup()
    ms_script = resolve_script_path("ms신규접수.py")
    if not ms_script:
        bot.send_message(chat_id, format_script_search_message("ms신규접수.py"))
        user_state = 0
        bot.send_message(chat_id, show_list())
        return
    bot.send_message(chat_id, "🆕 ms신규접수.py를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    _start_background_task(chat_id, "ms신규접수", run_ms_new, chat_id, ms_script, payload, forced_option=choice)
    user_state = 0
    bot.send_message(chat_id, show_list())

@_with_chat_session_arg(0)
def _execute_kiwoom_followup(chat_id, auto_trigger=False):
    global user_state
    _cancel_auto_timer(chat_id)
    if auto_trigger:
        bot.send_message(chat_id, "⏱️ 응답이 없어 자동으로 키움신규접수를 진행합니다.")
    payload = pending_followup_text
    choice = pending_followup_option or "1"
    _clear_pending_followup()
    kiwoom_script = resolve_script_path("키움신규접수.py")
    if not kiwoom_script:
        bot.send_message(chat_id, format_script_search_message("키움신규접수.py"))
        user_state = 0
        bot.send_message(chat_id, show_list())
        return
    bot.send_message(chat_id, "🆕 키움신규접수.py를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    _start_background_task(chat_id, "키움신규접수", run_kiwoom_new, chat_id, kiwoom_script, payload, choice)
    user_state = 0
    bot.send_message(chat_id, show_list())

def _start_followup_flow(chat_id, raw_text, bank, name):
    global user_state, pending_followup_text, pending_followup_name, pending_followup_kind, pending_followup_option
    normalized_text = _normalize_payload_for_followup(raw_text)

    if bank == "MS저축은행":
        forced = _extract_forced_ms_option(normalized_text)
        if forced in {"1", "2", "3", "4"}:
            option = forced
            label = _ms_option_to_label(option)
            limit_kind = "복합한도" if _ms_option_limit_type(option) == "복합" else "일반한도"
        else:
            option, label, limit_kind = infer_ms_product_preview(normalized_text)
        pending_followup_text = normalized_text
        pending_followup_name = name
        pending_followup_kind = "ms"
        pending_followup_option = option
        _prompt_pending_followup(chat_id)
        return

    if bank in {"키움", "키움(민간)"}:
        option = detect_loan_option(normalized_text) or "1"
        label = _kiwoom_option_label(option)
        pending_followup_text = normalized_text
        pending_followup_name = name
        pending_followup_kind = "kiwoom"
        pending_followup_option = option
        _prompt_pending_followup(chat_id)
        return

    bot.send_message(chat_id, f"ℹ️ 후속 자동연동 생략: 접수은행 인식값='{bank or '없음'}'")
    user_state = 0
    bot.send_message(chat_id, show_list())


def _prepare_admin_flow(chat_id, raw_text):
    global user_state, pending_admin_text, pending_admin_bank, pending_admin_name
    pending_admin_text = raw_text
    pending_admin_name = _extract_name_from_text(raw_text)
    detected_bank = detect_admin_bank(raw_text)
    pending_admin_bank = detected_bank

    if not detected_bank:
        user_state = 10
        bot.send_message(
            chat_id,
            (
                f"고객명: {pending_admin_name}\n"
                "접수은행 인식 실패(키예/세람/미래 등은 직접 선택 필요)\n"
                "접수은행을 선택하세요.\n"
                "1. MS저축은행\n"
                "2. 키움\n"
                "3. 키움(민간)\n"
                "0. 초기화면"
            ),
        )
        return

    user_state = 9
    bot.send_message(
        chat_id,
        (
            f"고객명: {pending_admin_name}\n"
            f"접수은행: {detected_bank}\n"
            "이대로 접수할까요?\n"
            "1. 그대로 진행\n"
            "2. 접수은행 수정\n"
            "0. 초기화면\n"
            f"({AUTO_PROGRESS_SECONDS}초 무응답 시 1번 자동 진행)"
        ),
    )
    _arm_auto_timer(
        chat_id,
        AUTO_PROGRESS_SECONDS,
        9,
        lambda: _execute_admin_then_followup(chat_id, auto_trigger=True),
    )


def _build_admin_execution_payload(raw_text, fields, bank_override=""):
    payload_fields = dict(fields or {})
    if not payload_fields:
        return raw_text

    if bank_override:
        payload_fields["접수"] = bank_override
    payload_fields = _recompute_admin_review_derived(payload_fields)
    return _build_ms_payload_from_fields(payload_fields, mode="admin")


def _process_kiwoom_input(chat_id, script_path_value, raw_text):
    global user_state, pending_new_text, pending_new_script
    global pending_amount_text, pending_amount_script, pending_amount_state
    amount_pair = detect_implicit_amount_pair(raw_text)
    if amount_pair is not None:
        dep, loan = amount_pair
        pending_amount_text = raw_text
        pending_amount_script = script_path_value
        pending_amount_state = 4
        user_state = 7
        bot.send_message(
            chat_id,
            (
                f"보증금 {dep}만 / 대출금 {loan}만 으로 접수할까요?\n"
                "1. 맞음 (이대로 진행)\n"
                "2. 수정 (다시 입력)"
            ),
        )
        return

    option = detect_loan_option(raw_text)
    if option is None:
        pending_new_text = raw_text
        pending_new_script = script_path_value
        user_state = 5
        bot.send_message(
            chat_id,
            (
                "상품 구분이 모호해서 선택이 필요합니다.\n"
                "1. 공공임대선순위_N\n"
                "2. 민간임대(선순위)\n"
                "3. 민간임대(신용관리)\n"
                "4. 민간임대(회파복)\n"
                "번호(1~4)를 입력하세요."
            ),
        )
        return

    bot.send_message(chat_id, "🆕 키움 신규접수를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    _start_background_task(chat_id, "키움신규접수", run_kiwoom_new, chat_id, script_path_value, raw_text, option)

    user_state = 0
    bot.send_message(chat_id, show_list())


def _process_ms_input(chat_id, script_path_value, raw_text):
    global user_state, pending_amount_text, pending_amount_script, pending_amount_state
    amount_pair = detect_implicit_amount_pair(raw_text)
    if amount_pair is not None:
        dep, loan = amount_pair
        product_no, product_label, limit_kind = infer_ms_product_preview(raw_text)
        pending_amount_text = raw_text
        pending_amount_script = script_path_value
        pending_amount_state = 6
        user_state = 7
        bot.send_message(
            chat_id,
            (
                f"보증금 {dep}만 / 대출금 {loan}만 으로 접수할까요?\n"
                f"자동판정 상품: {product_no}번 {product_label} ({limit_kind})\n"
                "1. 그대로 진행\n"
                "2. 보증금/대출금 수정\n"
                "3. 상품번호 수정\n"
                "4. 초기화면"
            ),
        )
        return

    normalized = _normalize_payload_for_followup(raw_text)
    bot.send_message(chat_id, "🆕 ms신규접수를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    _start_background_task(chat_id, "ms신규접수", run_ms_new, chat_id, script_path_value, normalized)
    user_state = 0
    bot.send_message(chat_id, show_list())

def _execute_admin_then_followup(chat_id, auto_trigger=False):
    if auto_trigger:
        bot.send_message(chat_id, "⏱️ 응답이 없어 1번(그대로 진행)으로 자동 접수합니다.")
    snapshot = _snapshot_admin_followup(chat_id)
    raw = snapshot.get("raw_text", "")
    if not raw:
        bot.send_message(chat_id, show_list())
        return
    script_path_value = snapshot.get("script_path", "")
    if not script_path_value:
        _reset_admin_followup_state(chat_id)
        bot.send_message(chat_id, format_script_search_message("admin접수.py"))
        bot.send_message(chat_id, show_list())
        return
    bot.send_message(chat_id, "⏳ admin접수를 백그라운드로 시작했습니다. 완료 후 후속 접수 여부를 다시 물어봅니다.")
    _start_background_task(
        chat_id,
        "admin접수",
        _run_admin_then_followup,
        chat_id,
        script_path_value,
        raw,
        snapshot.get("bank", ""),
        snapshot.get("name", ""),
    )

def run_kiwoom_new(chat_id, script_path_value, raw_text, loan_option):
    capture_path = script_path("kiwoom_new_capture.png")
    return run_capture_script(
        chat_id=chat_id,
        script_path_value=script_path_value,
        command_args=[raw_text, loan_option],
        python_exe=PYTHON_EXE,
        base_dir=BASE_DIR,
        capture_path=capture_path,
        capture_env_var="KIWOOM_NEW_CAPTURE_PATH",
        decode_output=decode_output,
        send_long_message=send_long_message,
        send_capture_if_exists=send_capture_if_exists,
        bot=bot,
        empty_result_label="신규접수",
        success_capture_label="✅ 키움신규접수 완료 캡처",
        env_overrides={"BOT_BROWSER_HEADLESS": "1"},
    )

def run_text_script(chat_id, script_path_value, raw_text):
    return run_simple_text_script(
        chat_id=chat_id,
        script_path_value=script_path_value,
        raw_text=raw_text,
        python_exe=PYTHON_EXE,
        base_dir=BASE_DIR,
        decode_output=decode_output,
        send_long_message=send_long_message,
        bot=bot,
    )

def run_ms_new(chat_id, script_path_value, raw_text, forced_option=None):
    capture_path = script_path("ms_new_capture.png")
    cmd = [raw_text]
    if forced_option in {"1", "2", "3", "4"}:
        cmd.append(forced_option)
    return run_capture_script(
        chat_id=chat_id,
        script_path_value=script_path_value,
        command_args=cmd,
        python_exe=PYTHON_EXE,
        base_dir=BASE_DIR,
        capture_path=capture_path,
        capture_env_var="MS_NEW_CAPTURE_PATH",
        decode_output=decode_output,
        send_long_message=send_long_message,
        send_capture_if_exists=send_capture_if_exists,
        bot=bot,
        empty_result_label="실행",
        success_capture_label="✅ ms신규접수 완료 캡처",
        env_overrides={"BOT_BROWSER_HEADLESS": "1"},
    )


def run_ms_consent(chat_id, script_path_value, raw_text):
    """MS신용조회동의 — Playwright 브라우저 자동입력 (주민뒷자리 수동입력 대기 가능)"""
    capture_path = script_path("ms_consent_capture.png")
    return run_ms_consent_script(
        chat_id=chat_id,
        script_path_value=script_path_value,
        raw_text=raw_text,
        python_exe=PYTHON_EXE,
        base_dir=BASE_DIR,
        capture_path=capture_path,
        send_long_message=send_long_message,
        send_capture_if_exists=send_capture_if_exists,
        bot=bot,
    )


def _format_rt_watch_menu():
    return (
        "🏠 [빌라 실거래 조회]\n"
        f"대상: {RT_WATCH_LABEL}\n"
        f"설정파일: {RT_WATCH_TARGETS}\n\n"
        "1. 과거 24개월 조회 (전체 출력)\n"
        "2. 과거 12개월 조회 (전체 출력)\n"
        "3. 신규 체크 (최근 2개월)\n"
        "4. 빠른 체크 (최근 1개월)\n"
        "0. 초기화면"
    )

def _format_rt_mode_menu(months, print_history):
    mode_name = "과거+신규 전체" if print_history else "신규 중심"
    return (
        "🏷️ [실거래 유형 선택]\n"
        f"조회개월: {months}개월 / 방식: {mode_name}\n\n"
        "1. 전체\n"
        "2. 매매만\n"
        "3. 전월세만\n"
        "0. 초기화면"
    )

def _run_rt_watch(chat_id, months=12, print_history=False, deal_filter="all"):
    script = resolve_script_path(RT_WATCH_SCRIPT)
    targets = resolve_script_path(RT_WATCH_TARGETS)
    service_key = (os.environ.get("MOLIT_SERVICE_KEY", "") or "").strip() or _read_secret_file("molit_service_key.txt")
    if not script or not os.path.exists(script):
        bot.send_message(chat_id, format_script_search_message(RT_WATCH_SCRIPT))
        return
    if not targets or not os.path.exists(targets):
        bot.send_message(chat_id, format_script_search_message(RT_WATCH_TARGETS))
        return
    if not service_key:
        bot.send_message(
            chat_id,
            (
                "⚠️ MOLIT 서비스키를 찾지 못했습니다.\n"
                "MOLIT_SERVICE_KEY 환경변수 또는 molit_service_key.txt 파일을 확인해 주세요."
            ),
        )
        return

    cmd = [
        PYTHON_EXE,
        script,
        "--targets", targets,
        "--service-key", service_key,
        "--months", str(max(1, int(months))),
    ]
    if deal_filter in {"trade", "rent", "lease", "monthly"}:
        cmd += ["--deal-filter", deal_filter]
    if print_history:
        cmd.append("--print-history")

    mode_ko = {
        "all": "전체",
        "trade": "매매",
        "rent": "전월세",
        "lease": "전세",
        "monthly": "월세",
    }.get(str(deal_filter or "all"), "전체")

    bot.send_message(chat_id, f"🔎 실거래 조회 중... (최근 {months}개월 / {mode_ko})")
    result = subprocess.run(cmd, capture_output=True, cwd=BASE_DIR)
    out = decode_output(result.stdout).strip()
    err = decode_output(result.stderr).strip()

    if out:
        def _has_deal_lines(text):
            for ln in (text or "").splitlines():
                if ln.startswith("NEW "):
                    return True
                if re.match(r"^\d{4}-\d{2}-\d{2}\s+", ln):
                    return True
            return False

        # 신규 중심 모드에서 신규가 없더라도 최근 이력 일부는 보여준다.
        if (not print_history) and (not _has_deal_lines(out)):
            hist_cmd = cmd + ["--print-history"]
            hist_result = subprocess.run(hist_cmd, capture_output=True, cwd=BASE_DIR)
            hist_out = decode_output(hist_result.stdout).strip()
            if hist_out:
                hist_lines = [
                    ln for ln in hist_out.splitlines()
                    if re.match(r"^\d{4}-\d{2}-\d{2}\s+", ln)
                ]
                if hist_lines:
                    preview = "\n".join(hist_lines[:30])
                    out = out + "\n[최근 이력]\n" + preview

        lines = out.splitlines()
        # 과거 전체 출력 시 텔레 메시지 과다 방지
        if print_history and len(lines) > 260:
            head = lines[:220]
            tail = lines[-30:]
            out = "\n".join(head + [f"... (중간 {len(lines)-250}줄 생략) ..."] + tail)
        send_long_message(chat_id, f"📄 [실거래 조회 결과]\n{out}")
    elif err:
        send_long_message(chat_id, f"❌ 실거래 조회 오류\n{err[:3000]}")
    else:
        bot.send_message(
            chat_id,
            f"❌ 조회 결과가 비어있습니다. (returncode={result.returncode}, script={RT_WATCH_SCRIPT})",
        )


def _run_rt_watch_background(chat_id, months=12, print_history=False, deal_filter="all"):
    _run_rt_watch(chat_id, months=months, print_history=print_history, deal_filter=deal_filter)


def _run_excel_open(chat_id):
    ok, msg = open_managed_workbook()
    bot.send_message(chat_id, f"{'✅' if ok else '❌'} {msg}")


def _run_excel_close(chat_id):
    ok, msg = close_managed_workbook()
    bot.send_message(chat_id, f"{'✅' if ok else '❌'} {msg}")


def _resolve_wp_notice_post_script():
    candidates = [
        r"C:\ONEtaktwosj\OneDrive\22blog\wordpress\publish_notice_posts.py",
        "/mnt/c/ONEtaktwosj/OneDrive/22blog/wordpress/publish_notice_posts.py",
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return candidates[0]


def _run_wp_notice_post(chat_id):
    script = _resolve_wp_notice_post_script()
    try:
        result = subprocess.run(
            [PYTHON_EXE, script],
            capture_output=True,
            cwd=os.path.dirname(script),
            timeout=300,
        )
        out = decode_output(result.stdout).strip()
        err = decode_output(result.stderr).strip()
        msg = out if out else "결과 없음"
        if err:
            msg += f"\n[stderr] {err[:200]}"
    except subprocess.TimeoutExpired:
        msg = "⏱ 시간 초과 (5분)"
    except Exception as e:
        msg = f"❌ 실행 오류: {e}"
    bot.send_message(chat_id, msg)




def show_list():
    cached_message = MENU_RENDER_CACHE.get("message", "")
    cached_expiry = float(MENU_RENDER_CACHE.get("expires_at") or 0.0)
    now = time.monotonic()
    if cached_message and cached_expiry > now:
        return cached_message

    msg = f"📋 (bot {BOT_VERSION})\n"
    msg += "\n━━ 대출 접수/심사 ━━\n"
    msg += f"1. admin접수{_menu_status_suffix(['admin접수.py'])}\n"
    msg += f"2. 익시오 상담요약(Claude){_ixio_menu_status_suffix()}\n"
    msg += f"3. MS신규접수{_menu_status_suffix(['ms신규접수.py'])}\n"
    msg += f"4. MS신용조회동의{_ms_consent_menu_suffix()}\n"
    msg += f"5. 키움신규접수{_menu_status_suffix(['키움신규접수.py'])}\n"
    msg += f"6. MS결과확인{_menu_status_suffix(['MS결과확인.py'])}\n"
    msg += f"7. 키움결과확인{_menu_status_suffix(['키움결과확인.py'])}\n"
    msg += "\n━━ 고객관리 ━━\n"
    msg += "31. 엑셀 고객입력\n"
    msg += "32. H시트고객 브리핑\n"
    msg += "33. 오늘/지난 고객리스트\n"
    if IVWITH_AVAILABLE:
        msg += "34. ivwith H시트 최신화\n"
        msg += "35. ivwith 운영리포트\n"
        msg += "38. 단절고객/고객흐름 갱신\n"
    msg += "36. 엑셀 열기\n"
    msg += "37. 엑셀 닫기\n"
    msg += "\n━━ 기타 ━━\n"
    msg += "71. 공고문 자동 게시\n"
    msg += f"81. 빌라실거래 조회({RT_WATCH_LABEL})\n"
    msg += "91. PC재부팅\n"
    msg += "92. PC켜기(WOL)\n"
    msg += "93. PC끄기\n"
    msg += "\n/office 봇상태"
    MENU_RENDER_CACHE["message"] = msg
    MENU_RENDER_CACHE["expires_at"] = now + 15.0
    return msg

def _send_home_menu(chat_id, prefix=""):
    message = show_list()
    prefix_text = str(prefix or "").strip()
    if prefix_text:
        message = prefix_text + "\n\n" + message
    bot.send_message(chat_id, message)


def _trace_urgent_reset(message, stage, extra=""):
    try:
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_id = getattr(getattr(message, "chat", None), "id", "")
        suffix = f" {extra}".rstrip() if extra else ""
        print(f"[urgent-reset] {now_text} stage={stage} chat_id={chat_id}{suffix}")
    except Exception:
        pass


def _handle_urgent_reset_message(message):
    return handle_urgent_reset_message(
        message,
        perf_counter=time.perf_counter,
        trace_urgent_reset=_trace_urgent_reset,
        ensure_message_chat_allowed=_ensure_message_chat_allowed,
        reset_chat_session_fast=_reset_chat_session_fast,
        send_home_menu=_send_home_menu,
    )


@bot.message_handler(func=lambda m: ((m.text or "").strip() in URGENT_RESET_TEXTS))
def handle_quick_reset(message):
    _handle_urgent_reset_message(message)


_ORIGINAL_PROCESS_NEW_MESSAGES = bot.process_new_messages


def _process_new_messages_with_priority_reset(self, new_messages):
    return process_new_messages_with_priority_reset(
        self,
        new_messages,
        urgent_reset_texts=URGENT_RESET_TEXTS,
        handle_urgent_reset_message=_handle_urgent_reset_message,
        original_process_new_messages=_ORIGINAL_PROCESS_NEW_MESSAGES,
    )


bot.process_new_messages = types.MethodType(_process_new_messages_with_priority_reset, bot)


def _handle_state_0(message, text):
    global user_state, target_script, auto_script

    handled, home_state = dispatch_home_state_0(
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        target_script=target_script,
        auto_script=auto_script,
        home_menu=home_menu,
        ivwith_available=IVWITH_AVAILABLE,
        ivwith_menu=ivwith_menu,
        menu_script_map=MENU_SCRIPT_MAP,
        show_list=show_list,
        start_background_task=_start_background_task,
        base_dir=BASE_DIR,
        python_exe=PYTHON_EXE,
        resolve_runtime_path=resolve_runtime_path,
        send_long_message=send_long_message,
        format_script_search_message=format_script_search_message,
        format_sales_menu=format_sales_menu,
        resolve_script_path=resolve_script_path,
        display_script_name=display_script_name,
        format_ms_consent_unavailable_message=_format_ms_consent_unavailable_message,
        prompt_excel_customer_input=_prompt_excel_customer_input,
        format_due_customer_menu=_format_due_customer_menu,
        format_rt_watch_menu=_format_rt_watch_menu,
        start_ai_briefing_step1=_start_ai_briefing_step1,
        send_claude_channel_redirect=_send_claude_channel_redirect,
        run_wp_notice_post=_run_wp_notice_post,
        menu34_base_dir=IVWITH_MENU34_BASE_DIR,
    )
    user_state = home_state["user_state"]
    target_script = home_state["target_script"]
    auto_script = home_state["auto_script"]
    return handled


def _handle_state_40(message, text):
    global user_state, pending_ivwith_report_type, pending_ivwith_sales_key, pending_ivwith_sales_display
    result = handle_sales_state_40(
        sales_reports_menu,
        bot=bot,
        message=message,
        text=text,
        ivwith_available=IVWITH_AVAILABLE,
        user_state=user_state,
        pending_ivwith_report_type=pending_ivwith_report_type,
        pending_ivwith_sales_key=pending_ivwith_sales_key,
        pending_ivwith_sales_display=pending_ivwith_sales_display,
        sales_list=SALES_LIST,
        show_list=show_list,
    )
    handled = result["handled"]
    if not handled:
        return False
    sales_state = result["state"]
    user_state = sales_state["user_state"]
    pending_ivwith_report_type = sales_state["pending_ivwith_report_type"]
    pending_ivwith_sales_key = sales_state["pending_ivwith_sales_key"]
    pending_ivwith_sales_display = sales_state["pending_ivwith_sales_display"]
    return handled


def _handle_state_41(message, text):
    global user_state, pending_ivwith_report_type, pending_ivwith_sales_key, pending_ivwith_sales_display
    result = handle_sales_state_41(
        sales_reports_menu,
        bot=bot,
        message=message,
        text=text,
        ivwith_available=IVWITH_AVAILABLE,
        user_state=user_state,
        pending_ivwith_report_type=pending_ivwith_report_type,
        pending_ivwith_sales_key=pending_ivwith_sales_key,
        pending_ivwith_sales_display=pending_ivwith_sales_display,
        week_options=WEEK_OPTIONS,
        start_background_task=_start_background_task,
        show_list=show_list,
        build_customer_report=build_customer_report,
        base_dir=IVWITH_RUNTIME_BASE_DIR,
    )
    handled = result["handled"]
    if not handled:
        return False
    sales_state = result["state"]
    user_state = sales_state["user_state"]
    pending_ivwith_report_type = sales_state["pending_ivwith_report_type"]
    pending_ivwith_sales_key = sales_state["pending_ivwith_sales_key"]
    pending_ivwith_sales_display = sales_state["pending_ivwith_sales_display"]
    return handled


def _handle_state_wait_admin(message, text):
    return handle_processing_wait(bot, message, "admin접수", _format_processing_wait_message)


def _handle_state_wait_ixio(message, text):
    return handle_processing_wait(bot, message, "익시오 상담요약", _format_processing_wait_message)


def _handle_state_wait_briefing(message, text):
    return handle_processing_wait(bot, message, "AI 브리핑", _format_processing_wait_message)


def _handle_state_wait_excel(message, text):
    return handle_processing_wait(bot, message, "엑셀 입력", _format_processing_wait_message)


def _handle_state_3(message, text):
    global user_state
    result = handle_result_lookup_state(
        bot,
        message,
        text,
        target_script=target_script,
        start_background_task=_start_background_task,
        run_result_check=_run_result_check,
        show_list=show_list,
    )
    user_state = result["user_state"]
    return result["handled"]


def _handle_state_18(message, text):
    return handle_ixio_state_18(
        ixio_excel_menu,
        message=message,
        text=text,
        start_ixio_summary=_start_ixio_summary,
    )


def _handle_state_19(message, text):
    global user_state, auto_script, pending_ixio_data, pending_ixio_duplicates
    result = handle_ixio_state_19(
        ixio_excel_menu,
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        auto_script=auto_script,
        pending_ixio_data=pending_ixio_data,
        pending_ixio_duplicates=pending_ixio_duplicates,
        resolve_script_path=resolve_script_path,
        format_script_search_message=format_script_search_message,
        show_list=show_list,
        format_ixio_kakao_message=_format_ixio_kakao_message,
        build_ixio_admin_payload=_build_ixio_admin_payload,
        prepare_admin_flow=_prepare_admin_flow,
        send_ixio_action_menu=_send_ixio_action_menu,
        start_excel_write_flow=_start_excel_write_flow,
    )
    handled = result["handled"]
    ixio_state = result["state"]
    user_state = ixio_state["user_state"]
    auto_script = ixio_state["auto_script"]
    pending_ixio_data = ixio_state["pending_ixio_data"]
    pending_ixio_duplicates = ixio_state["pending_ixio_duplicates"]
    return handled


def _handle_state_20(message, text):
    return handle_ixio_state_20(
        ixio_excel_menu,
        bot=bot,
        message=message,
        text=text,
        resume_after_excel=_resume_after_excel,
        execute_excel_write_flow=_execute_excel_write_flow,
    )


def _handle_state_21(message, text):
    return handle_ixio_state_21(
        ixio_excel_menu,
        bot=bot,
        message=message,
        text=text,
        build_excel_data_from_text=_build_excel_data_from_text,
        start_excel_write_flow=_start_excel_write_flow,
    )


def _handle_state_22(message, text):
    global user_state, pending_excel_data, pending_excel_resume
    result = handle_ixio_state_22(
        ixio_excel_menu,
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        pending_excel_data=pending_excel_data,
        pending_excel_resume=pending_excel_resume,
        show_list=show_list,
        execute_excel_write_flow=_execute_excel_write_flow,
        resume_after_excel=_resume_after_excel,
    )
    handled = result["handled"]
    excel_state = result["state"]
    user_state = excel_state["user_state"]
    pending_excel_data = excel_state["pending_excel_data"]
    pending_excel_resume = excel_state["pending_excel_resume"]
    return handled


def _handle_state_13(message, text):
    global user_state
    result = handle_ms_review_state_13(
        bot,
        message,
        text,
        pending_ms_mode=pending_ms_mode,
        pending_ms_fields=pending_ms_fields,
        pending_ms_script=pending_ms_script,
        target_script=target_script,
        clear_pending_ms_edit=_clear_pending_ms_edit,
        build_ms_payload_from_fields=_build_ms_payload_from_fields,
        prepare_admin_flow=_prepare_admin_flow,
        process_kiwoom_input=_process_kiwoom_input,
        start_background_task=_start_background_task,
        run_ms_new=run_ms_new,
        show_list=show_list,
        build_excel_data_from_review_fields=_build_excel_data_from_review_fields,
        start_excel_write_flow=_start_excel_write_flow,
        review_order_by_mode=_review_order_by_mode,
        ms_option_to_label=_ms_option_to_label,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_14(message, text):
    result = handle_ms_review_state_14(
        bot,
        message,
        text,
        pending_ms_mode=pending_ms_mode,
        start_ms_edit_prompt=_start_ms_edit_prompt,
    )
    return result["handled"]


def _handle_state_15(message, text):
    global user_state, pending_ms_edit_key
    result = handle_ms_review_state_15(
        bot,
        message,
        text,
        pending_ms_mode=pending_ms_mode,
        pending_ms_edit_key=pending_ms_edit_key,
        pending_ms_fields=pending_ms_fields,
        pending_ms_lines=pending_ms_lines,
        normalize_ms_field_value_by_mode=_normalize_ms_field_value_by_mode,
        format_ms_field_summary=_format_ms_field_summary,
        recompute_ms_review_derived=_recompute_ms_review_derived,
        recompute_admin_review_derived=_recompute_admin_review_derived,
        recompute_kiwoom_review_derived=_recompute_kiwoom_review_derived,
        review_order_by_mode=_review_order_by_mode,
        start_ms_edit_prompt=_start_ms_edit_prompt,
    )
    user_state = result.get("user_state", user_state)
    pending_ms_edit_key = result.get("pending_ms_edit_key", pending_ms_edit_key)
    return result["handled"]


def _handle_state_9(message, text):
    global user_state
    result = handle_admin_followup_state_9(
        bot,
        message,
        text,
        execute_admin_then_followup=_execute_admin_then_followup,
        cancel_auto_timer=_cancel_auto_timer,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_10(message, text):
    global pending_admin_bank
    result = handle_admin_followup_state_10(
        bot,
        message,
        text,
        execute_admin_then_followup=_execute_admin_then_followup,
    )
    pending_admin_bank = result.get("pending_admin_bank", pending_admin_bank)
    return result["handled"]


def _handle_state_11(message, text):
    global user_state
    result = handle_admin_followup_state_11(
        bot,
        message,
        text,
        pending_followup_text=pending_followup_text,
        execute_ms_followup=_execute_ms_followup,
        cancel_auto_timer=_cancel_auto_timer,
        clear_pending_followup=_clear_pending_followup,
        show_list=show_list,
        build_excel_data_from_text=_build_excel_data_from_text,
        prompt_pending_followup=_prompt_pending_followup,
        start_excel_write_flow=_start_excel_write_flow,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_12(message, text):
    global user_state
    result = handle_admin_followup_state_12(
        bot,
        message,
        text,
        pending_followup_text=pending_followup_text,
        execute_kiwoom_followup=_execute_kiwoom_followup,
        cancel_auto_timer=_cancel_auto_timer,
        clear_pending_followup=_clear_pending_followup,
        show_list=show_list,
        build_excel_data_from_text=_build_excel_data_from_text,
        prompt_pending_followup=_prompt_pending_followup,
        start_excel_write_flow=_start_excel_write_flow,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_23(message, text):
    global user_state
    result = handle_due_customer_state_23(
        bot,
        message,
        text,
        send_due_customer_report=_send_due_customer_report,
        format_due_customer_menu=_format_due_customer_menu,
        get_due_customer_schedule=_get_due_customer_schedule,
        clear_due_customer_schedule=_clear_due_customer_schedule,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_24(message, text):
    global user_state
    result = handle_due_customer_state_24(
        bot,
        message,
        text,
        parse_due_schedule_time=_parse_due_schedule_time,
        set_due_customer_schedule=_set_due_customer_schedule,
        format_due_customer_menu=_format_due_customer_menu,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_25(message, text):
    global user_state
    result = handle_due_customer_state_25(
        bot,
        message,
        send_claude_channel_redirect=_send_claude_channel_redirect,
        show_list=show_list,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


def _handle_state_35(message, text):
    global user_state
    result = handle_briefing_state_35(
        briefing_menu,
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        briefing_classified=_briefing_classified,
        start_ai_briefing_step2=_start_ai_briefing_step2,
        clear_pending_briefing=_clear_pending_briefing,
        show_list=show_list,
    )
    handled = result["handled"]
    briefing_state = result["state"]
    user_state = briefing_state["user_state"]
    return handled


def _handle_state_36(message, text):
    global user_state
    result = handle_briefing_state_36(
        briefing_menu,
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        start_ai_briefing_step2=_start_ai_briefing_step2,
        clear_pending_briefing=_clear_pending_briefing,
        show_list=show_list,
    )
    handled = result["handled"]
    briefing_state = result["state"]
    user_state = briefing_state["user_state"]
    return handled


def _handle_state_16(message, text):
    global user_state, pending_rt_months, pending_rt_print_history
    result = handle_rt_state_16(
        rt_watch_menu,
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        pending_rt_months=pending_rt_months,
        pending_rt_print_history=pending_rt_print_history,
        format_rt_mode_menu=_format_rt_mode_menu,
        show_list=show_list,
    )
    handled = result["handled"]
    rt_state = result["state"]
    user_state = rt_state["user_state"]
    pending_rt_months = rt_state["pending_rt_months"]
    pending_rt_print_history = rt_state["pending_rt_print_history"]
    return handled


def _handle_state_17(message, text):
    global user_state, pending_rt_months, pending_rt_print_history
    result = handle_rt_state_17(
        rt_watch_menu,
        bot=bot,
        message=message,
        text=text,
        user_state=user_state,
        pending_rt_months=pending_rt_months,
        pending_rt_print_history=pending_rt_print_history,
        start_background_task=_start_background_task,
        run_rt_watch_background=_run_rt_watch_background,
        show_list=show_list,
    )
    handled = result["handled"]
    rt_state = result["state"]
    user_state = rt_state["user_state"]
    pending_rt_months = rt_state["pending_rt_months"]
    pending_rt_print_history = rt_state["pending_rt_print_history"]
    return handled


def _handle_state_1(message, text):
    global user_state
    if has_deposit_input(text):
        admin_script = auto_script or resolve_script_path("admin접수.py")
        if not admin_script:
            bot.send_message(message.chat.id, format_script_search_message("admin접수.py"))
            user_state = 0
            bot.send_message(message.chat.id, show_list())
            return True
        _start_ms_review(message.chat.id, admin_script, text, mode="admin")
        return True
    bot.send_message(message.chat.id, "양식에 맞춰 정보를 주세요. (보증금 라벨 / 숫자 2줄 / 엑셀 한 줄 형식)")
    return True


def _handle_state_2(message, text):
    global user_state
    if text == "1":
        bot.send_message(message.chat.id, "🎉 최종 확인 버튼 클릭!")
        subprocess.run([PYTHON_EXE, auto_script, "confirm"], cwd=BASE_DIR)
        user_state = 0
        bot.send_message(message.chat.id, show_list())
    return True


def _handle_state_4(message, text):
    _start_ms_review(message.chat.id, target_script, text, mode="kiwoom")
    return True


def _handle_state_5(message, text):
    global user_state, pending_new_text, pending_new_script
    choice = text.strip()
    if choice not in {"1", "2", "3", "4"}:
        bot.send_message(message.chat.id, "1~4 중 번호를 입력해 주세요.")
        return True

    bot.send_message(message.chat.id, "🆕 선택한 상품으로 키움 신규접수를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    _start_background_task(message.chat.id, "키움신규접수", run_kiwoom_new, message.chat.id, pending_new_script, pending_new_text, choice)

    pending_new_text = ""
    pending_new_script = ""
    user_state = 0
    bot.send_message(message.chat.id, show_list())
    return True


def _handle_state_30(message, text):
    global user_state
    if text == "0":
        user_state = 0
        bot.send_message(message.chat.id, show_list())
        return True
    consent_script = target_script or resolve_script_path("ms신용조회동의.py")
    if not consent_script:
        bot.send_message(message.chat.id, _format_ms_consent_unavailable_message())
        user_state = 0
        bot.send_message(message.chat.id, show_list())
        return True
    if _is_ms_consent_maintenance_mode():
        bot.send_message(message.chat.id, "⚠️ MS신용조회동의는 현재 점검중입니다. 안내 메시지만 전송합니다.")
    else:
        bot.send_message(message.chat.id, "⏳ MS신용조회동의 자동입력 시작...")
    run_ms_consent(message.chat.id, consent_script, text)
    user_state = 0
    return True


def _handle_state_6(message, text):
    _start_ms_review(message.chat.id, target_script, text)
    return True


def _handle_state_7(message, text):
    global user_state, pending_amount_text, pending_amount_script, pending_amount_state
    global pending_new_text, pending_new_script
    choice = text.strip()
    back_state = pending_amount_state
    is_ms_flow = back_state == 6

    if is_ms_flow and choice not in {"1", "2", "3", "4"}:
        looks_like_payload = (
            ("\n" in text)
            or bool(re.search(r"\d{6}\D*\d{7}", text))
            or bool(re.search(r"(01[016789])\D*(\d{3,4})\D*(\d{4})", text))
            or has_deposit_input(text)
        )
        if looks_like_payload:
            bot.send_message(message.chat.id, "📝 수정 입력으로 인식했습니다. 다시 판정합니다.")
            _process_ms_input(message.chat.id, pending_amount_script or target_script, text)
            return True

    if is_ms_flow and choice == "4":
        pending_amount_text = ""
        pending_amount_script = ""
        pending_amount_state = 0
        user_state = 0
        bot.send_message(message.chat.id, show_list())
        return True

    if choice == "2":
        pending_amount_text = ""
        pending_amount_script = ""
        pending_amount_state = 0
        if back_state in {4, 6}:
            user_state = back_state
            bot.send_message(message.chat.id, "수정할 내용을 다시 붙여넣어 주세요.")
        else:
            user_state = 0
            bot.send_message(message.chat.id, show_list())
        return True

    if is_ms_flow and choice == "3":
        user_state = 8
        bot.send_message(
            message.chat.id,
            (
                "상품번호를 선택하세요.\n"
                "1. 임대아파트대출\n"
                "2. 임대아파트대출(대환)\n"
                "3. 임대아파트대출(대환복합)\n"
                "4. 임대아파트대출(복합)\n"
                "5. 초기화면"
            )
        )
        return True

    if choice != "1":
        if is_ms_flow:
            bot.send_message(message.chat.id, "1/2/3/4 중 번호를 입력해 주세요.")
        else:
            bot.send_message(message.chat.id, "1 또는 2를 입력해 주세요.")
        return True

    saved_text = pending_amount_text
    saved_script = pending_amount_script
    pending_amount_text = ""
    pending_amount_script = ""
    pending_amount_state = 0

    if back_state == 4:
        option = detect_loan_option(saved_text)
        if option is None:
            pending_new_text = saved_text
            pending_new_script = saved_script
            user_state = 5
            bot.send_message(
                message.chat.id,
                (
                    "상품 구분이 모호해서 선택이 필요합니다.\n"
                    "1. 공공임대선순위_N\n"
                    "2. 민간임대(선순위)\n"
                    "3. 민간임대(신용관리)\n"
                    "4. 민간임대(회파복)\n"
                    "번호(1~4)를 입력하세요."
                )
            )
            return True

        bot.send_message(message.chat.id, "🆕 키움 신규접수를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
        _start_background_task(message.chat.id, "키움신규접수", run_kiwoom_new, message.chat.id, saved_script, saved_text, option)
        user_state = 0
        bot.send_message(message.chat.id, show_list())
        return True

    if back_state == 6:
        normalized = _normalize_payload_for_followup(saved_text)
        bot.send_message(message.chat.id, "🆕 ms신규접수를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
        _start_background_task(message.chat.id, "ms신규접수", run_ms_new, message.chat.id, saved_script, normalized)
        user_state = 0
        bot.send_message(message.chat.id, show_list())
        return True

    user_state = 0
    bot.send_message(message.chat.id, show_list())
    return True


def _handle_state_8(message, text):
    global user_state, pending_amount_text, pending_amount_script, pending_amount_state
    choice = text.strip()
    if choice == "5":
        pending_amount_text = ""
        pending_amount_script = ""
        pending_amount_state = 0
        user_state = 0
        bot.send_message(message.chat.id, show_list())
        return True

    if choice not in {"1", "2", "3", "4"}:
        bot.send_message(message.chat.id, "1~4 중 번호를 입력해 주세요. (5: 초기화면)")
        return True

    saved_text = pending_amount_text
    saved_script = pending_amount_script
    pending_amount_text = ""
    pending_amount_script = ""
    pending_amount_state = 0

    bot.send_message(message.chat.id, "🆕 선택한 상품번호로 ms신규접수를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
    normalized = _normalize_payload_for_followup(saved_text)
    _start_background_task(message.chat.id, "ms신규접수", run_ms_new, message.chat.id, saved_script, normalized, forced_option=choice)

    user_state = 0
    bot.send_message(message.chat.id, show_list())
    return True


STATE_HANDLERS = {
    0: _handle_state_0,
    1: _handle_state_1,
    2: _handle_state_2,
    3: _handle_state_3,
    4: _handle_state_4,
    5: _handle_state_5,
    6: _handle_state_6,
    7: _handle_state_7,
    8: _handle_state_8,
    9: _handle_state_9,
    10: _handle_state_10,
    11: _handle_state_11,
    12: _handle_state_12,
    13: _handle_state_13,
    14: _handle_state_14,
    15: _handle_state_15,
    16: _handle_state_16,
    17: _handle_state_17,
    18: _handle_state_18,
    19: _handle_state_19,
    20: _handle_state_20,
    21: _handle_state_21,
    22: _handle_state_22,
    23: _handle_state_23,
    24: _handle_state_24,
    25: _handle_state_25,
    30: _handle_state_30,
    35: _handle_state_35,
    36: _handle_state_36,
    40: _handle_state_40,
    41: _handle_state_41,
    ADMIN_FLOW_RUNNING_STATE: _handle_state_wait_admin,
    IXIO_SUMMARY_RUNNING_STATE: _handle_state_wait_ixio,
    AI_BRIEFING_RUNNING_STATE: _handle_state_wait_briefing,
    EXCEL_WRITE_RUNNING_STATE: _handle_state_wait_excel,
}

def _handle_message_impl(message):
    global user_state, file_list, target_script, auto_script, pending_new_text, pending_new_script
    global pending_amount_text, pending_amount_script, pending_amount_state
    global pending_admin_text, pending_admin_bank, pending_admin_name
    global pending_followup_text, pending_followup_name, pending_followup_kind, pending_followup_option
    global pending_ivwith_report_type
    global pending_ms_script, pending_ms_fields, pending_ms_lines, pending_ms_edit_key, pending_ms_mode
    global pending_rt_months, pending_rt_print_history, pending_ixio_data, pending_ixio_duplicates

    if not _ensure_message_chat_allowed(message):
        return True

    text = (message.text or "").strip()
    text_lower = text.lower()
    result = handle_message_preroute(
        bot,
        message,
        text,
        text_lower=text_lower,
        user_state=user_state,
        python_exe=PYTHON_EXE,
        bot_version=BOT_VERSION,
        openclaw_handler_enabled=OPENCLAW_HANDLER_ENABLED,
        classify_front_secretary_request=_classify_front_secretary_request,
        maybe_handle_front_secretary_message=_maybe_handle_front_secretary_message,
        send_claude_channel_redirect=_send_claude_channel_redirect,
        send_long_message=send_long_message,
        format_bot_runtime_status_message=_format_bot_runtime_status_message,
        format_bot_log_message=_format_bot_log_message,
        format_rt_watch_menu=_format_rt_watch_menu,
    )
    user_state = result.get("user_state", user_state)
    return result["handled"]


if OPENCLAW_HANDLER_ENABLED:
    @bot.message_handler(func=lambda m: bool(_classify_front_secretary_message((m.text or "").strip())))
    @_with_message_chat_session
    def handle_front_secretary_message(message):
        _handle_message_impl(message)


@bot.message_handler(func=lambda m: True) # 모든 메시지를 일단 받아서 ID를 검사합니다
@_with_message_chat_session
def handle_message(message):
    global user_state
    global pending_new_text, pending_new_script
    global pending_amount_text, pending_amount_script, pending_amount_state
    global pending_admin_text, pending_admin_bank, pending_admin_name
    global pending_rt_months, pending_rt_print_history

    text = (message.text or "").strip()
    text_lower = text.lower()

    if _handle_message_impl(message):
        return

    if text_lower in {"/excel_input", "/excelcustomer", "엑셀고객입력", "엑셀 고객입력"}:
        _prompt_excel_customer_input(message.chat.id)
        return

    if text_lower in {"/due_list", "/duelist", "/todaylist", "고객리스트", "오늘고객", "지난고객", "오늘지난고객"}:
        user_state = 23
        bot.send_message(message.chat.id, _format_due_customer_menu(message.chat.id))
        return

    wol_mac_input = _parse_wol_mac_from_text(text)
    if text in {"88", "92", "/wol", "켜기", "wake"} or wol_mac_input:
        mac = _normalize_mac(wol_mac_input) if wol_mac_input else _normalize_mac(WOL_TARGET_MAC)
        if not mac:
            bot.send_message(
                message.chat.id,
                (
                    "⚠️ WOL 대상 MAC이 없습니다.\n"
                    "사용법: /wol AA:BB:CC:DD:EE:FF  또는  켜기 AA:BB:CC:DD:EE:FF\n"
                    "기본값 사용 시 환경변수 WOL_TARGET_MAC 설정 필요"
                ),
            )
            return
        ok, msg = _send_wol_magic_packet(mac)
        bot.send_message(message.chat.id, f"{'✅' if ok else '❌'} {msg}")
        return

    if text in {"/shutdown", "shutdown", "끄기", "99", "93"}:
        bot.send_message(message.chat.id, "🛑 PC를 5초 후 종료합니다.")
        try:
            subprocess.run(["shutdown", "/s", "/t", "5", "/f"], cwd=BASE_DIR)
        except Exception as e:
            bot.send_message(message.chat.id, f"종료 명령 실패: {e}")
        return

    if text in {"66", "36", "/excel_open", "/excelopen", "엑셀열기", "통합열기"}:
        bot.send_message(message.chat.id, "📂 엑셀 열기를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
        _start_background_task(message.chat.id, "엑셀 열기", _run_excel_open, message.chat.id)
        bot.send_message(message.chat.id, show_list())
        return

    if text in {"67", "37", "/excel_close", "/excelclose", "엑셀닫기", "통합닫기"}:
        bot.send_message(message.chat.id, "📁 엑셀 닫기를 백그라운드로 시작했습니다. 완료되면 결과를 다시 보냅니다.")
        _start_background_task(message.chat.id, "엑셀 닫기", _run_excel_close, message.chat.id)
        bot.send_message(message.chat.id, show_list())
        return

    if text in {"61", "62", "63", "82", "94", "000", "claude재시작", "채널봇재시작", "junofccld재시작", "junofcld재시작"}:
        _send_removed_legacy_menu_message(message.chat.id)
        bot.send_message(message.chat.id, show_list())
        return

    if text in {"/reboot", "재부팅", "77", "91"}:
        bot.send_message(message.chat.id, "♻️ PC를 5초 후 재부팅합니다.")
        try:
            subprocess.run(["shutdown", "/r", "/t", "5", "/f"], cwd=BASE_DIR)
        except Exception as e:
            bot.send_message(message.chat.id, f"재부팅 명령 실패: {e}")
        return

    if text in {"0", "00", "취소"}:
        _cancel_auto_timer(message.chat.id)
        pending_admin_text = ""
        pending_admin_bank = ""
        pending_admin_name = ""
        _clear_pending_followup()
        _clear_pending_ms_edit()
        _clear_pending_ixio()
        _clear_pending_excel()
        _clear_pending_ivwith_sales()
        _clear_pending_briefing()
        pending_rt_months = 12
        pending_rt_print_history = False
        user_state = 0
        _send_home_menu(message.chat.id, "↩️ 취소하고 처음으로 돌아갑니다.")
        return

    if user_state == 0 and _is_ixio_text(text):
        _start_ixio_summary(message.chat.id, text)
        return

    state_handler = STATE_HANDLERS.get(user_state)
    if state_handler:
        handled = state_handler(message, text)
        if handled:
            return

def _primary_allowed_chat_id():
    if not ALLOWED_CHAT_IDS:
        return None
    try:
        return sorted(ALLOWED_CHAT_IDS)[0]
    except Exception:
        return next(iter(ALLOWED_CHAT_IDS), None)


start_bot_runtime(
    bot=bot,
    base_dir_display=BASE_DIR,
    ensure_runtime_dirs=_ensure_runtime_dirs,
    write_pid_file=_write_pid_file,
    cleanup_runtime_identity_files=_cleanup_runtime_identity_files,
    write_runtime_status=_write_runtime_status,
    acquire_single_instance_guard=_acquire_single_instance_guard,
    runtime_heartbeat_loop=_runtime_heartbeat_loop,
    write_runtime_heartbeat=_write_runtime_heartbeat,
    prime_menu_status_cache=_prime_menu_status_cache,
    due_customer_schedule_loop=_due_customer_schedule_loop,
    ivwith_available=IVWITH_AVAILABLE,
    ivwith_runtime_base_dir=IVWITH_RUNTIME_BASE_DIR,
    notification_chat_id_getter=_primary_allowed_chat_id,
    bot_username=BOT_USERNAME,
    openclaw_handler_enabled=OPENCLAW_HANDLER_ENABLED,
    looks_like_telegram_conflict=_looks_like_telegram_conflict,
    bot_fatal_exit_conflict=BOT_FATAL_EXIT_CONFLICT,
    polling_retry_sleep_sec=POLLING_RETRY_SLEEP_SEC,
)
