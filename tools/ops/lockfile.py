import json
import os
import subprocess
import time
from pathlib import Path


class LockError(RuntimeError):
    pass


def _pid_is_running(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return str(pid) in (result.stdout or "")
        except Exception:
            return False
    else:
        return True


def acquire_lock(lock_path: str, max_age_min: int = 180) -> dict:
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    now = time.time()
    max_age = max_age_min * 60

    if path.exists():
        age = now - path.stat().st_mtime
        if age < max_age:
            try:
                info = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                info = {"note": "unreadable_lock"}
            existing_pid = 0
            try:
                existing_pid = int(info.get("pid") or 0)
            except Exception:
                existing_pid = 0
            if existing_pid and not _pid_is_running(existing_pid):
                try:
                    path.unlink()
                except Exception as exc:
                    raise LockError(f"dead lock remove failed: {path} err={exc}") from exc
            else:
                raise LockError(f"lock exists: {path} info={info}")
        try:
            if path.exists():
                path.unlink()
        except Exception as exc:
            raise LockError(f"stale lock remove failed: {path} err={exc}") from exc

    info = {"pid": os.getpid(), "time": int(now)}
    path.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    return info


def release_lock(lock_path: str) -> None:
    path = Path(lock_path)
    if path.exists():
        try:
            path.unlink()
        except Exception:
            pass
