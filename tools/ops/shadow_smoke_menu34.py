#!/usr/bin/env python3
"""Run a non-live menu 34 shadow smoke against the 2POW workspace."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import types


ROOT = Path(os.environ.get("BOT_BASE_DIR", r"C:\2POW"))
if os.name != "nt" and str(ROOT).startswith("C:\\"):
    ROOT = Path("/mnt/c/2POW")

_PREFERRED_SCRIPT_DIR = Path(os.environ.get("BOT_SCRIPT_DIR", str(ROOT / "03_telegram_py")))
MODULE_PATH = _PREFERRED_SCRIPT_DIR / "bot_app" / "menus" / "ivwith_menu.py"
if not MODULE_PATH.exists():
    MODULE_PATH = ROOT / "bot_app" / "menus" / "ivwith_menu.py"


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


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, chat_id, text, **kwargs):
        parse_mode = kwargs.get("parse_mode")
        suffix = f" [parse_mode={parse_mode}]" if parse_mode else ""
        line = f"[chat:{chat_id}] {text}{suffix}"
        self.messages.append(line)
        _console_write(line)


def _load_shadow_module():
    module = types.ModuleType("shadow_ivwith_menu")
    module.__file__ = str(MODULE_PATH)
    code = compile(MODULE_PATH.read_text(encoding="utf-8"), str(MODULE_PATH), "exec")
    exec(code, module.__dict__)
    return module


def _path_stamp(path: Path):
    if not path.exists():
        return None
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def main() -> int:
    if not MODULE_PATH.exists():
        _console_write(f"missing shadow module: {MODULE_PATH}", stream=sys.stderr)
        return 2

    module = _load_shadow_module()
    bot = FakeBot()
    result_holder = {"ok": False}
    last_sync_path = ROOT / "runtime" / "last_sync.json"
    last_sync_before = _path_stamp(last_sync_path)

    def start_background_task(chat_id, label, target, *args, **kwargs):
        _console_write(f"[shadow-task] {label}")
        target(*args, **kwargs)
        result_holder["ok"] = True

    def show_list():
        return "shadow smoke complete"

    module.start_menu_34(
        bot,
        chat_id=999999,
        start_background_task=start_background_task,
        show_list=show_list,
        base_dir=str(ROOT),
    )
    last_sync_after = _path_stamp(last_sync_path)
    if last_sync_before == last_sync_after:
        _console_write(f"runtime last_sync.json did not change: {last_sync_path}", stream=sys.stderr)
        return 1
    return 0 if result_holder["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
