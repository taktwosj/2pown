import json
import random
import string
from datetime import datetime
from pathlib import Path


def new_run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    rnd = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{ts}-{rnd}"


def write_json(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
