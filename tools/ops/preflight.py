import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_windows_path(value: str) -> bool:
    return len(value) >= 3 and value[1:3] == ":\\"


def _normalize_path(value: str) -> Path:
    if os.name != "nt" and _is_windows_path(value):
        drive = value[0].lower()
        rest = value[3:].replace("\\", "/")
        return Path(f"/mnt/{drive}/{rest}")
    return Path(value)


def load_cfg() -> dict:
    example = ROOT / "config" / "canonical_map.example.json"
    local = ROOT / "config" / "canonical_map.local.json"
    if not example.exists():
        raise RuntimeError(f"missing config: {example}")
    cfg = _read(example)
    if local.exists():
        cfg.update(_read(local))
    return cfg


def fail(message: str, code: int = 2) -> None:
    raise RuntimeError(f"[PREFLIGHT FAIL] {message}")


def preflight() -> tuple[dict, Path]:
    cfg = load_cfg()

    need_role = cfg.get("NODE_ROLE_REQUIRED", "office_runner")
    role = os.environ.get("NODE_ROLE", "")
    if role != need_role:
        fail(f"NODE_ROLE={role!r} (필요: {need_role})")

    cwd = Path.cwd().resolve()
    expected_cwd = _normalize_path(cfg["OFFICE_WORKDIR"]).resolve()
    if cwd != expected_cwd:
        fail(f"cwd mismatch: {cwd} != {expected_cwd}")

    argv0 = _normalize_path(str(sys.argv[0])).resolve()
    expected_bot = _normalize_path(cfg["OFFICE_BOT_PATH"]).resolve()
    if argv0 != expected_bot:
        fail(f"bot path mismatch: {argv0} != {expected_bot}")

    canon = _normalize_path(cfg["CANON_XLSM"])
    if "OneDrive" not in str(canon):
        fail(f"CANON not OneDrive: {canon}")
    if not canon.exists():
        fail(f"CANON missing: {canon}")

    for path in cfg.get("FORBIDDEN_COPIES", []):
        if _normalize_path(path).exists():
            fail(f"forbidden copy exists: {path}")

    runtime_dir = Path(cfg["RUNTIME_DIR"])
    runtime_dir.mkdir(parents=True, exist_ok=True)

    return cfg, canon
