import datetime
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from contextlib import contextmanager


def send_ivwith_report(bot, chat_id, report):
    if len(report) > 4000:
        parts = report.split("\n🟢")
        if len(parts) == 2:
            bot.send_message(chat_id, parts[0], parse_mode="HTML")
            bot.send_message(chat_id, "🟢" + parts[1], parse_mode="HTML")
            return
        chunk = ""
        for line in report.split("\n"):
            if len(chunk) + len(line) + 1 > 3900:
                bot.send_message(chat_id, chunk, parse_mode="HTML")
                chunk = line
            else:
                chunk += "\n" + line if chunk else line
        if chunk:
            bot.send_message(chat_id, chunk, parse_mode="HTML")
        return
    bot.send_message(chat_id, report, parse_mode="HTML")


def start_menu_34(bot, chat_id, start_background_task, show_list, base_dir):
    bot.send_message(chat_id, "⏳ ivwith H시트 최신화를 백그라운드로 시작했습니다.")
    start_background_task(chat_id, "ivwith H시트 최신화", run_hsheet_sync, bot, chat_id, base_dir)
    bot.send_message(chat_id, show_list())


def _last_sync_path(base_dir):
    return Path(base_dir) / "runtime" / "last_sync.json"


def _admin_new_last_sync_path(base_dir):
    return Path(base_dir) / "ivwith" / "admin_new_runtime" / "assets" / "last_sync.json"


def _load_last_sync_payload(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_last_sync_payload(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _write_last_sync_targets(base_dir, payload):
    _write_last_sync_payload(_last_sync_path(base_dir), payload)
    admin_last_sync = _admin_new_last_sync_path(base_dir)
    if admin_last_sync.parent.exists():
        _write_last_sync_payload(admin_last_sync, payload)


@contextmanager
def _temporary_menu34_base_dir(base_dir):
    module_dir = os.path.join(str(base_dir), "ivwith")
    previous_base_dir = os.environ.get("BOT_BASE_DIR")
    inserted_module_dir = False

    if module_dir and module_dir not in sys.path:
        sys.path.insert(0, module_dir)
        inserted_module_dir = True

    os.environ["BOT_BASE_DIR"] = str(base_dir)
    try:
        yield
    finally:
        if inserted_module_dir:
            try:
                sys.path.remove(module_dir)
            except ValueError:
                pass
        if previous_base_dir is None:
            os.environ.pop("BOT_BASE_DIR", None)
        else:
            os.environ["BOT_BASE_DIR"] = previous_base_dir


def _extract_change_count(messages):
    patterns = (
        re.compile(r"변경\s+(\d+)건"),
        re.compile(r"엑셀 자동 업데이트\s*\((\d+)건\)"),
    )
    for message in reversed(messages):
        text = str(message)
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                try:
                    return int(match.group(1))
                except Exception:
                    continue
    return 0


def _record_hsheet_sync_result(
    base_dir,
    messages,
    ok,
    error_text="",
    error_stage="",
    run_id="",
    canon_xlsm="",
    canon_reason="",
):
    joined = "\n".join(str(message) for message in messages)
    payload = _load_last_sync_payload(_last_sync_path(base_dir))
    event_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    error_message = error_text or ("hsheet_sync_failed" if not ok else "")

    if error_text or not ok:
        sync_status = "failed"
        excel_mode = "오류"
        changes_applied = 0
        failed = [error_message]
        skipped = []
    elif "보류" in joined:
        sync_status = "held"
        excel_mode = "보류"
        changes_applied = 0
        failed = []
        skipped = ["excel_locked"]
    elif "변경 대상 없음" in joined:
        sync_status = "ok_no_change"
        excel_mode = "원본"
        changes_applied = 0
        failed = []
        skipped = []
    else:
        sync_status = "ok"
        excel_mode = "원본"
        changes_applied = _extract_change_count(messages)
        failed = []
        skipped = []

    payload.update(
        {
            "last_sync_run_id": run_id or payload.get("last_sync_run_id", ""),
            "last_sync_time": event_timestamp,
            "canon_xlsm": canon_xlsm or payload.get("canon_xlsm", ""),
            "canon_reason": canon_reason or payload.get("canon_reason", ""),
            "sync_mode": "hsheet",
            "sync_status": sync_status,
            "excel_mode": excel_mode,
            "changes_found": changes_applied,
            "changes_applied": changes_applied,
            "db_sync_ok": None,
            "customer_flow_refresh_ok": None,
            "customer_flow_refresh_requested": False,
            "uploaded": [],
            "failed": failed,
            "skipped": skipped,
            "summary_text": str(messages[-1]) if messages else "",
            "error": error_message,
            "error_stage": error_stage if error_message else "",
            "error_timestamp": event_timestamp if error_message else "",
        }
    )
    _write_last_sync_targets(base_dir, payload)


def run_hsheet_sync(bot, chat_id, base_dir):
    messages = []
    run_id = f"hsheet-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def _safe_send(text, parse_mode=None):
        try:
            kwargs = {}
            if parse_mode:
                kwargs["parse_mode"] = parse_mode
            bot.send_message(chat_id, text, **kwargs)
        except Exception as exc:
            print(f"[ivwith_hsheet notify failed] {exc}: {str(text)[:120]}")

    _safe_send("⏳ ivwith H시트 최신화 중... (덤프 → 변경분 탐색 → H시트 반영)")
    try:
        # menu 34/menu 10 may run against a shadow workspace, so reload daily_sync
        # with BOT_BASE_DIR temporarily pinned to the requested base_dir.
        with _temporary_menu34_base_dir(base_dir):
            import daily_sync
            importlib.reload(daily_sync)

            # menu 34/menu 10 canonical workbook resolution happens here exactly once.
            preflight_info = daily_sync.preflight()
            canon_xlsm = preflight_info.get("canon_xlsm", "")
            canon_reason = preflight_info.get("canon_reason", "")

            if not preflight_info.get("ok"):
                error_text = f"canon_xlsm preflight failed: {canon_reason}"
                messages.append(f"❌ 동기화 실패: {error_text}")
                _record_hsheet_sync_result(
                    base_dir,
                    messages,
                    False,
                    error_text=error_text,
                    error_stage="preflight",
                    run_id=run_id,
                    canon_reason=canon_reason,
                )
                _safe_send(f"❌ 동기화 실패: {error_text}")
                return

            def _relay(text):
                messages.append(str(text))
                _safe_send(text, parse_mode="HTML")

            ok = bool(daily_sync.run_hsheet_sync(status_callback=_relay, canon_xlsm=canon_xlsm))
            _record_hsheet_sync_result(
                base_dir,
                messages,
                ok,
                error_stage="" if ok else "sync_exec",
                run_id=run_id,
                canon_xlsm=canon_xlsm,
                canon_reason=canon_reason,
            )
    except Exception as exc:
        messages.append(f"❌ 동기화 실패: {exc}")
        _record_hsheet_sync_result(
            base_dir,
            messages,
            False,
            error_text=str(exc),
            error_stage="sync_exec",
            run_id=run_id,
        )
        _safe_send(f"❌ 동기화 실패: {exc}")


def start_menu_38(
    bot,
    chat_id,
    start_background_task,
    show_list,
    base_dir,
    python_exe,
    resolve_runtime_path,
    send_long_message,
    format_script_search_message,
):
    bot.send_message(chat_id, "⏳ 단절고객/고객흐름 갱신을 백그라운드로 시작했습니다.")
    start_background_task(
        chat_id,
        "단절고객/고객흐름 갱신",
        run_customer_flow_refresh,
        bot,
        chat_id,
        base_dir,
        python_exe,
        resolve_runtime_path,
        send_long_message,
        format_script_search_message,
    )
    bot.send_message(chat_id, show_list())


def _collect_customer_flow_summary(output_text):
    summary = []
    warnings = []
    seen_summary = set()
    seen_warnings = set()

    def _push(bucket, seen, text):
        normalized = str(text).strip()
        if not normalized:
            return
        key = normalized.casefold()
        if key in seen:
            return
        seen.add(key)
        bucket.append(normalized)

    lines = [line.strip() for line in str(output_text or "").splitlines() if line.strip()]
    for line in lines:
        lower = line.lower()
        if "customer_portal_api ok" in lower:
            _push(summary, seen_summary, "portal API ok")
            continue
        if "customer_flow_api ok" in lower:
            _push(summary, seen_summary, "flow API ok")
            continue

        sync_match = re.search(r"synced\s+(\d+)\s+files", line, re.IGNORECASE)
        if sync_match:
            _push(summary, seen_summary, f"synced {sync_match.group(1)} files")
            continue

        if "skip admin-new sync" in lower:
            _push(warnings, seen_warnings, "admin-new sync skipped")
            continue
        if "skip verify_customer_portal_api.py" in lower:
            _push(warnings, seen_warnings, "portal API verify skipped")
            continue
        if "skip verify_customer_flow_api.py" in lower:
            _push(warnings, seen_warnings, "flow API verify skipped")
            continue

    if not summary:
        for line in lines[-3:]:
            if line.startswith("["):
                continue
            _push(summary, seen_summary, line[:120])

    return summary, warnings


def _format_customer_flow_success_message(output_text):
    summary, warnings = _collect_customer_flow_summary(output_text)
    lines = ["✅ 단절고객/고객흐름 갱신 완료"]
    for item in summary:
        lines.append(f"- {item}")
    for item in warnings:
        lines.append(f"⚠️ {item}")
    return "\n".join(lines)


def run_customer_flow_refresh(
    bot,
    chat_id,
    base_dir,
    python_exe,
    resolve_runtime_path,
    send_long_message,
    format_script_search_message,
):
    bot.send_message(chat_id, "⏳ 단절고객/고객흐름 갱신 중...")
    try:
        candidates = (
            os.path.join(base_dir, "ivwith", "refresh_customer_flow_assets.py"),
            os.path.join(base_dir, "refresh_customer_flow_assets.py"),
            os.path.join(base_dir, "03_telegram_py", "refresh_customer_flow_assets.py"),
            os.path.join(base_dir, "admin", "refresh_customer_flow_assets.py"),
        )
        refresh_script = next((path for path in candidates if os.path.exists(path)), "")
        if not refresh_script:
            refresh_script = resolve_runtime_path("refresh_customer_flow_assets.py")
        if not refresh_script or not os.path.exists(refresh_script):
            bot.send_message(chat_id, format_script_search_message("refresh_customer_flow_assets.py"))
            return

        result = subprocess.run(
            [python_exe, refresh_script],
            capture_output=True,
            cwd=os.path.dirname(refresh_script),
        )
        output_text = _decode_output(result.stdout).strip()
        error_text = _decode_output(result.stderr).strip()

        if result.returncode != 0:
            send_long_message(chat_id, f"❌ 단절고객/고객흐름 갱신 실패\n{(error_text or output_text)[:3000]}")
            return

        send_long_message(chat_id, _format_customer_flow_success_message(output_text))
    except Exception as exc:
        bot.send_message(chat_id, f"❌ 단절고객/고객흐름 갱신 실패: {exc}")


def start_menu_35(bot, chat_id, format_sales_menu):
    from bot_app.menus import sales_reports as sales_reports_menu

    bot.send_message(chat_id, sales_reports_menu.format_report_type_menu(), parse_mode="HTML")


def parse_sales_selection(text, sales_list):
    try:
        idx = int(text.strip()) - 1
        if 0 <= idx < len(sales_list):
            return sales_list[idx]
    except Exception:
        pass
    return None


def parse_weeks_selection(text, week_options):
    return week_options.get(text.strip())


def start_sales_report(
    bot,
    chat_id,
    start_background_task,
    show_list,
    sales_key,
    sales_display,
    weeks,
    build_customer_report,
):
    bot.send_message(chat_id, f"⏳ {sales_display} 최근 {weeks // 7}주 조회를 백그라운드로 시작했습니다.")
    start_background_task(
        chat_id,
        "ivwith 고객리스트",
        run_ivwith_sales_report,
        bot,
        chat_id,
        sales_key,
        sales_display,
        weeks,
        build_customer_report,
    )
    bot.send_message(chat_id, show_list())


def run_ivwith_sales_report(bot, chat_id, sales_key, sales_display, weeks, build_customer_report):
    bot.send_message(chat_id, f"⏳ {sales_display} 최근 {weeks // 7}주 조회 중...")
    try:
        report = build_customer_report(sales_key, sales_display, weeks)
        send_ivwith_report(bot, chat_id, report)
    except Exception as exc:
        bot.send_message(chat_id, f"❌ 리포트 생성 실패: {exc}")


def _decode_output(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return value.decode(encoding)
        except Exception:
            continue
    return value.decode("utf-8", errors="replace")
