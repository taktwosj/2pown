import atexit
import importlib
import logging
import os
import socket
import sys
import threading
import time
import urllib.error
from datetime import datetime

import requests


def _resolve_notification_chat_id(notification_chat_id_getter):
    if not callable(notification_chat_id_getter):
        return None
    try:
        chat_id = notification_chat_id_getter()
    except Exception:
        return None
    if chat_id in ("", None):
        return None
    return chat_id


def _ivwith_daily_sync_loop(bot, ivwith_runtime_base_dir, notification_chat_id_getter):
    """Run the legacy 08:00 ivwith sync without leaving the logic in bot.py."""
    sync_hour = 8
    last_run_date = None
    while True:
        try:
            now = datetime.now()
            today = now.date()
            if now.hour == sync_hour and last_run_date != today:
                last_run_date = today
                print(f"[ivwith_sync] {now} 자동 동기화 시작")
                try:
                    module_dir = os.path.join(ivwith_runtime_base_dir, "ivwith")
                    if module_dir not in sys.path:
                        sys.path.insert(0, module_dir)
                    import daily_sync

                    importlib.reload(daily_sync)
                    daily_sync.main()
                    print("[ivwith_sync] 완료")
                except Exception as exc:
                    print(f"[ivwith_sync] 에러: {exc}")
                    notify_chat_id = _resolve_notification_chat_id(notification_chat_id_getter)
                    if notify_chat_id is not None:
                        try:
                            bot.send_message(notify_chat_id, f"❌ ivwith 자동 동기화 에러: {exc}")
                        except Exception:
                            pass
            time.sleep(60)
        except Exception:
            time.sleep(60)


def start_bot_runtime(
    *,
    bot,
    base_dir_display,
    ensure_runtime_dirs,
    write_pid_file,
    cleanup_runtime_identity_files,
    write_runtime_status,
    acquire_single_instance_guard,
    runtime_heartbeat_loop,
    write_runtime_heartbeat,
    prime_menu_status_cache,
    due_customer_schedule_loop,
    ivwith_available,
    ivwith_runtime_base_dir,
    notification_chat_id_getter,
    bot_username,
    openclaw_handler_enabled,
    looks_like_telegram_conflict,
    bot_fatal_exit_conflict,
    polling_retry_sleep_sec,
):
    print(f"집 전용 비서가 맑은 정신으로 출근했습니다! ({base_dir_display})")
    print("텔레그램에서 봇에게 아무 메시지나 한 번 보내면 메뉴를 띄웁니다.")

    ensure_runtime_dirs()
    write_pid_file()
    atexit.register(cleanup_runtime_identity_files)
    write_runtime_status("booting", "프로세스 시작")

    try:
        acquire_single_instance_guard()
    except Exception as exc:
        print(f"[single-instance] {exc}")
        raise SystemExit(1)

    threading.Thread(target=runtime_heartbeat_loop, daemon=True).start()
    write_runtime_heartbeat()
    prime_menu_status_cache()

    threading.Thread(target=due_customer_schedule_loop, daemon=True).start()

    if ivwith_available:
        threading.Thread(
            target=_ivwith_daily_sync_loop,
            kwargs={
                "bot": bot,
                "ivwith_runtime_base_dir": ivwith_runtime_base_dir,
                "notification_chat_id_getter": notification_chat_id_getter,
            },
            daemon=True,
        ).start()
        print("[ivwith_sync] 매일 08:00 자동 동기화 스레드 시작")

    write_runtime_status(
        "polling_start",
        "텔레그램 polling 시작",
        bot_username=bot_username,
        openclaw_handler_enabled=openclaw_handler_enabled,
    )

    while True:
        try:
            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=20,
                logger_level=logging.CRITICAL,
            )
            write_runtime_status("polling_stopped", "polling 이 예외 없이 종료되었습니다.")
        except requests.exceptions.ReadTimeout as exc:
            detail = f"Telegram polling read timeout: {exc}"
            write_runtime_status("polling_timeout", detail)
            try:
                print(f"[polling-timeout] {detail}")
            except Exception:
                pass
            time.sleep(polling_retry_sleep_sec)
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
            urllib.error.URLError,
            socket.timeout,
            TimeoutError,
        ) as exc:
            detail = f"Telegram network retry: {exc}"
            write_runtime_status("polling_network_retry", detail)
            try:
                print(f"[polling-network-retry] {detail}")
            except Exception:
                pass
            time.sleep(polling_retry_sleep_sec)
        except Exception as exc:
            if looks_like_telegram_conflict(exc):
                conflict_detail = (
                    "Telegram 409 Conflict: 같은 토큰이 다른 PC 또는 다른 세션에서 동시에 실행 중입니다. "
                    "사무실 PC 1대만 실행되게 정리하세요."
                )
                print(f"[polling-conflict] {conflict_detail}")
                write_runtime_status(
                    "fatal_conflict",
                    conflict_detail,
                    exit_code=bot_fatal_exit_conflict,
                )
                raise SystemExit(bot_fatal_exit_conflict)
            write_runtime_status("polling_retry", str(exc))
            try:
                print(f"[polling-restart] {exc}")
            except Exception:
                pass
            time.sleep(polling_retry_sleep_sec)
