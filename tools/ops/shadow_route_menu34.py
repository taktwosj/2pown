#!/usr/bin/env python3
"""Exercise the menu 34 route through shadow home.py without touching live bot."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import types


ROOT = Path(os.environ.get("BOT_BASE_DIR", r"C:\2POW"))
if os.name != "nt" and str(ROOT).startswith("C:\\"):
    ROOT = Path("/mnt/c/2POW")

HOME_MODULE_PATH = Path(os.environ.get("SHADOW_HOME_MODULE_PATH", str(ROOT / "bot_app" / "menus" / "home.py")))
_DEFAULT_IVWITH_MENU_PATH = HOME_MODULE_PATH.with_name("ivwith_menu.py")
IVWITH_MENU_PATH = Path(
    os.environ.get(
        "SHADOW_IVWITH_MODULE_PATH",
        str(_DEFAULT_IVWITH_MENU_PATH if _DEFAULT_IVWITH_MENU_PATH.exists() else ROOT / "bot_app" / "menus" / "ivwith_menu.py"),
    )
)
HOME_BASE_DIR = os.environ.get("SHADOW_HOME_BASE_DIR", str(ROOT))
MENU34_BASE_DIR = os.environ.get("SHADOW_MENU34_BASE_DIR", "").strip()


def _console_write(text: str, *, stream=None) -> None:
    target = stream or sys.stdout
    text = str(text)
    encoding = getattr(target, "encoding", None) or "utf-8"
    try:
        target.write(text + "\n")
    except UnicodeEncodeError:
        data = (text + "\n").encode(encoding, errors="replace")
        buffer = getattr(target, "buffer", None)
        if buffer is not None:
            buffer.write(data)
        else:
            target.write(data.decode(encoding, errors="replace"))
    target.flush()


def _load_module(module_name: str, path: Path):
    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, module.__dict__)
    return module


def _path_stamp(path: Path):
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


class FakeChat:
    def __init__(self, chat_id: int) -> None:
        self.id = chat_id


class FakeMessage:
    def __init__(self, chat_id: int) -> None:
        self.chat = FakeChat(chat_id)


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, chat_id, text, **kwargs):
        parse_mode = kwargs.get("parse_mode")
        suffix = f" [parse_mode={parse_mode}]" if parse_mode else ""
        line = f"[chat:{chat_id}] {text}{suffix}"
        self.messages.append(line)
        _console_write(line)


def main() -> int:
    if not HOME_MODULE_PATH.exists():
        _console_write(f"missing shadow home module: {HOME_MODULE_PATH}", stream=sys.stderr)
        return 2
    if not IVWITH_MENU_PATH.exists():
        _console_write(f"missing shadow ivwith menu module: {IVWITH_MENU_PATH}", stream=sys.stderr)
        return 2

    home_module = _load_module("shadow_home_menu", HOME_MODULE_PATH)
    ivwith_menu_module = _load_module("shadow_ivwith_menu", IVWITH_MENU_PATH)

    bot = FakeBot()
    message = FakeMessage(chat_id=999999)
    state = {"user_state": 0}
    result_holder = {"ok": False}
    last_sync_path = ROOT / "runtime" / "last_sync.json"
    last_sync_before = _path_stamp(last_sync_path)

    def start_background_task(chat_id, label, target, *args, **kwargs):
        _console_write(f"[shadow-route-task] {label}")
        target(*args, **kwargs)
        result_holder["ok"] = True

    def show_list():
        return "shadow route complete"

    def _noop(*args, **kwargs):
        return None

    handled = home_module.handle_state_0(
        bot=bot,
        message=message,
        text="34",
        state=state,
        ivwith_available=True,
        ivwith_menu=ivwith_menu_module,
        menu_script_map={},
        show_list=show_list,
        start_background_task=start_background_task,
        base_dir=HOME_BASE_DIR,
        python_exe="python3",
        resolve_runtime_path=lambda *_args, **_kwargs: "",
        send_long_message=_noop,
        format_script_search_message=lambda *_args, **_kwargs: "",
        format_sales_menu=lambda *_args, **_kwargs: "",
        resolve_script_path=lambda *_args, **_kwargs: "",
        display_script_name=lambda *_args, **_kwargs: "",
        format_ms_consent_unavailable_message=lambda *_args, **_kwargs: "",
        prompt_excel_customer_input=_noop,
        format_due_customer_menu=lambda *_args, **_kwargs: "",
        format_rt_watch_menu=lambda *_args, **_kwargs: "",
        start_ai_briefing_step1=_noop,
        send_claude_channel_redirect=_noop,
        run_wp_notice_post=_noop,
        menu34_base_dir=MENU34_BASE_DIR,
    )
    last_sync_after = _path_stamp(last_sync_path)
    if last_sync_before == last_sync_after:
        _console_write(
            f"[shadow-route] runtime last_sync.json did not change: {last_sync_path}",
            stream=sys.stderr,
        )
        return 1
    _console_write(f"[shadow-route] handled={handled}")
    return 0 if handled and result_holder["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
