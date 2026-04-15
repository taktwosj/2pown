#!/usr/bin/env python3
"""Guardrail audit for Telegram menu 34 before broader folder cleanup."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


def _normalize_input_path(raw: str) -> Path:
    text = str(raw or "").strip()
    if not text:
        return Path.cwd()
    if os.name != "nt":
        match = re.match(r"^([A-Za-z]):\\(.*)$", text)
        if match:
            drive = match.group(1).lower()
            suffix = match.group(2).replace("\\", "/")
            return Path(f"/mnt/{drive}/{suffix}")
    return Path(text)


def _to_windows_like(path: Path) -> str:
    text = str(path)
    match = re.match(r"^/mnt/([a-zA-Z])/(.*)$", text)
    if match:
        drive = match.group(1).upper()
        suffix = match.group(2).replace("/", "\\")
        return f"{drive}:\\{suffix}"
    return text


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_event_time(value: str) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for pattern in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text, pattern)
        except ValueError:
            continue
    return None


def _age_minutes(event_time: dt.datetime | None) -> float | None:
    if event_time is None:
        return None
    return max(0.0, (dt.datetime.now() - event_time).total_seconds() / 60.0)


def _path_report(path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "path": str(path),
        "windows_path": _to_windows_like(path),
        "exists": path.exists(),
    }
    if path.exists():
        stat = path.stat()
        report["size"] = stat.st_size
        report["mtime"] = dt.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%S")
    return report


def _compare_pair(left: Path, right: Path) -> dict[str, Any]:
    result = {
        "left": _path_report(left),
        "right": _path_report(right),
        "same_hash": False,
    }
    if left.exists() and right.exists():
        left_hash = _sha256(left)
        right_hash = _sha256(right)
        result["left"]["sha256"] = left_hash
        result["right"]["sha256"] = right_hash
        result["same_hash"] = left_hash == right_hash
    return result


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _run_shadow_smoke(bot_base_dir: Path, menu34_base_dir: Path) -> dict[str, Any]:
    script_path = menu34_base_dir / "tools" / "ops" / "shadow_route_menu34.py"
    env = os.environ.copy()
    env["BOT_BASE_DIR"] = str(menu34_base_dir)
    env["SHADOW_HOME_MODULE_PATH"] = str(bot_base_dir / "03_telegram_py" / "bot_app" / "menus" / "home.py")
    env["SHADOW_HOME_BASE_DIR"] = str(bot_base_dir)
    env["SHADOW_MENU34_BASE_DIR"] = str(menu34_base_dir)
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(menu34_base_dir),
        capture_output=True,
        text=True,
        errors="replace",
        env=env,
    )
    return {
        "command": [sys.executable, str(script_path)],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bot-base-dir", default=r"C:\2POW")
    parser.add_argument("--menu34-base-dir", default="")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--heartbeat-warn-minutes", type=int, default=30)
    parser.add_argument("--heartbeat-fail-minutes", type=int, default=180)
    parser.add_argument("--last-sync-warn-hours", type=int, default=24)
    args = parser.parse_args()

    bot_base_dir = _normalize_input_path(args.bot_base_dir)
    menu34_base_dir = _normalize_input_path(args.menu34_base_dir or args.bot_base_dir)
    now = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    report: dict[str, Any] = {
        "checked_at": now,
        "bot_base_dir": {
            "local": str(bot_base_dir),
            "windows": _to_windows_like(bot_base_dir),
        },
        "menu34_base_dir": {
            "local": str(menu34_base_dir),
            "windows": _to_windows_like(menu34_base_dir),
        },
        "checks": {},
        "warnings": [],
        "failures": [],
    }
    warnings: list[str] = report["warnings"]
    failures: list[str] = report["failures"]

    required_paths = {
        "live_bot": bot_base_dir / "bot.py",
        "root_home": bot_base_dir / "bot_app" / "menus" / "home.py",
        "repo_home": bot_base_dir / "03_telegram_py" / "bot_app" / "menus" / "home.py",
        "root_ivwith_menu": menu34_base_dir / "bot_app" / "menus" / "ivwith_menu.py",
        "repo_ivwith_menu": bot_base_dir / "03_telegram_py" / "bot_app" / "menus" / "ivwith_menu.py",
        "daily_sync": menu34_base_dir / "ivwith" / "daily_sync.py",
        "lockfile": menu34_base_dir / "lockfile.py",
        "canonical_map": menu34_base_dir / "config" / "canonical_map.local.json",
        "runtime_last_sync": menu34_base_dir / "runtime" / "last_sync.json",
        "heartbeat": bot_base_dir / "runtime" / "root_bot" / "state" / "bot_heartbeat.json",
        "runtime_status": bot_base_dir / "runtime" / "root_bot" / "state" / "bot_runtime_status.json",
    }
    report["checks"]["required_paths"] = {
        name: _path_report(path) for name, path in required_paths.items()
    }
    for name, path in required_paths.items():
        if not path.exists():
            failures.append(f"missing required path: {name} -> {_to_windows_like(path)}")

    home_pair = _compare_pair(required_paths["root_home"], required_paths["repo_home"])
    report["checks"]["home_pair"] = home_pair
    if not home_pair["same_hash"]:
        failures.append("root home.py and 03_telegram_py home.py diverged; smoke no longer covers live routing safely")

    deprecated_repo_bot = bot_base_dir / "03_telegram_py" / "bot.py"
    report["checks"]["deprecated_repo_bot"] = _path_report(deprecated_repo_bot)
    if deprecated_repo_bot.exists():
        warnings.append("deprecated 03_telegram_py/bot.py still exists; root bot.py should be the only bot.py")

    ivwith_pair = _compare_pair(required_paths["root_ivwith_menu"], required_paths["repo_ivwith_menu"])
    report["checks"]["ivwith_menu_pair"] = ivwith_pair
    if ivwith_pair["left"]["exists"] and ivwith_pair["right"]["exists"] and not ivwith_pair["same_hash"]:
        warnings.append("root ivwith_menu.py and repo copy differ; menu34 admin mirror path must be watched closely")

    canonical_info: dict[str, Any] = {}
    canonical_map_path = required_paths["canonical_map"]
    if canonical_map_path.exists():
        try:
            canonical_map = _load_json(canonical_map_path)
            canon_xlsm_raw = str(canonical_map.get("CANON_XLSM", "")).strip()
            canon_xlsm_path = _normalize_input_path(canon_xlsm_raw) if canon_xlsm_raw else None
            canonical_info = {
                "canon_xlsm": canon_xlsm_raw,
                "canon_xlsm_exists": bool(canon_xlsm_path and canon_xlsm_path.exists()),
                "canon_xlsm_local": str(canon_xlsm_path) if canon_xlsm_path else "",
            }
            if not canon_xlsm_raw:
                failures.append("CANON_XLSM is missing from canonical_map.local.json")
            elif not canon_xlsm_path or not canon_xlsm_path.exists():
                failures.append(f"canonical workbook is missing: {canon_xlsm_raw}")
        except Exception as exc:
            canonical_info = {"error": str(exc)}
            failures.append(f"failed to parse canonical_map.local.json: {exc}")
    report["checks"]["canonical_map"] = canonical_info

    last_sync_payload: dict[str, Any] = {}
    last_sync_path = required_paths["runtime_last_sync"]
    if last_sync_path.exists():
        try:
            last_sync_payload = _load_json(last_sync_path)
            report["checks"]["runtime_last_sync"] = last_sync_payload
            sync_status = str(last_sync_payload.get("sync_status", "")).strip()
            if sync_status == "failed":
                failures.append(f"runtime last_sync is failed: {last_sync_payload.get('error') or 'unknown error'}")
            elif sync_status == "held":
                warnings.append("runtime last_sync is held; workbook lock prevented menu34 from writing H sheet")
            event_time = _parse_event_time(str(last_sync_payload.get("last_sync_time", "")))
            age_minutes = _age_minutes(event_time)
            if age_minutes is not None:
                report["checks"]["runtime_last_sync_age_minutes"] = round(age_minutes, 1)
                if age_minutes > args.last_sync_warn_hours * 60:
                    warnings.append(
                        f"runtime last_sync is older than {args.last_sync_warn_hours}h ({round(age_minutes / 60.0, 1)}h)"
                    )
        except Exception as exc:
            report["checks"]["runtime_last_sync"] = {"error": str(exc)}
            failures.append(f"failed to parse runtime last_sync.json: {exc}")

    heartbeat_payload: dict[str, Any] = {}
    heartbeat_path = required_paths["heartbeat"]
    if heartbeat_path.exists():
        try:
            heartbeat_payload = _load_json(heartbeat_path)
            report["checks"]["heartbeat"] = heartbeat_payload
            status = str(heartbeat_payload.get("status", "")).strip()
            if status != "polling_start":
                failures.append(f"office bot heartbeat is not polling_start: {status or 'missing'}")
            hb_time = _parse_event_time(str(heartbeat_payload.get("updated_at", "")))
            hb_age_minutes = _age_minutes(hb_time)
            if hb_age_minutes is not None:
                report["checks"]["heartbeat_age_minutes"] = round(hb_age_minutes, 1)
                if hb_age_minutes > args.heartbeat_fail_minutes:
                    failures.append(
                        f"office bot heartbeat is older than {args.heartbeat_fail_minutes} minutes ({round(hb_age_minutes, 1)}m)"
                    )
                elif hb_age_minutes > args.heartbeat_warn_minutes:
                    warnings.append(
                        f"office bot heartbeat is older than {args.heartbeat_warn_minutes} minutes ({round(hb_age_minutes, 1)}m)"
                    )
            expected_menu34_base = _to_windows_like(menu34_base_dir)
            actual_menu34_base = str(heartbeat_payload.get("ivwith_menu34_base_dir", "")).strip()
            report["checks"]["heartbeat_expected_menu34_base"] = expected_menu34_base
            if actual_menu34_base and actual_menu34_base != expected_menu34_base:
                failures.append(
                    f"heartbeat menu34 base mismatch: expected {expected_menu34_base}, got {actual_menu34_base}"
                )
        except Exception as exc:
            report["checks"]["heartbeat"] = {"error": str(exc)}
            failures.append(f"failed to parse bot_heartbeat.json: {exc}")

    admin_mirror = menu34_base_dir / "ivwith" / "admin_new_runtime" / "assets" / "last_sync.json"
    legacy_admin_mirror = menu34_base_dir / "admin" / "_admin_new_work" / "assets" / "last_sync.json"
    mirror_checks = {
        "active_admin_mirror": _path_report(admin_mirror),
        "legacy_admin_mirror": _path_report(legacy_admin_mirror),
    }
    if admin_mirror.exists() and last_sync_payload:
        try:
            admin_payload = _load_json(admin_mirror)
            mirror_checks["active_admin_mirror"]["payload"] = admin_payload
            if admin_payload.get("last_sync_run_id") != last_sync_payload.get("last_sync_run_id"):
                warnings.append("admin_new_runtime last_sync mirror is out of sync with runtime/last_sync.json")
        except Exception as exc:
            mirror_checks["active_admin_mirror"]["error"] = str(exc)
            warnings.append(f"failed to parse admin_new_runtime last_sync mirror: {exc}")
    elif not admin_mirror.exists():
        warnings.append("admin_new_runtime last_sync mirror is missing")
    if legacy_admin_mirror.exists():
        warnings.append("legacy admin/_admin_new_work mirror still exists; watch for stale menu34 writes")
    report["checks"]["admin_mirrors"] = mirror_checks

    if not args.skip_smoke and not failures:
        smoke_result = _run_shadow_smoke(bot_base_dir=bot_base_dir, menu34_base_dir=menu34_base_dir)
        report["checks"]["shadow_smoke"] = smoke_result
        if smoke_result["returncode"] != 0:
            failures.append("menu34 shadow smoke failed")
    else:
        report["checks"]["shadow_smoke"] = {
            "skipped": bool(args.skip_smoke),
            "reason": "precheck failures present" if failures and not args.skip_smoke else "",
        }

    verify_dir = menu34_base_dir / "runtime" / "verify" / "menu34_guard"
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_path = verify_dir / "menu34_guard_latest.json"
    timestamped_path = verify_dir / f"menu34_guard_{timestamp}.json"
    for output_path in (latest_path, timestamped_path):
        _ensure_parent(output_path)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[menu34-guard] checked_at={report['checked_at']}")
    print(f"[menu34-guard] report={_to_windows_like(latest_path)}")
    if warnings:
        print("[menu34-guard] warnings:")
        for item in warnings:
            print(f"  - {item}")
    if failures:
        print("[menu34-guard] failures:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("[menu34-guard] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
