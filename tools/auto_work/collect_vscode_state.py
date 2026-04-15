"""Compatibility wrapper for the extracted 1other collect_vscode_state canonical.

This 1POW path is no longer the canonical implementation. It forwards execution
to `C:\\1other\\openclaw-front-secretary\\tools\\auto_work\\collect_vscode_state.py`
so VS Code observation logic stays in one place.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def canonical_script() -> Path:
    root_1pow = Path(__file__).resolve().parents[2]
    root_other = root_1pow.parent / "1other" / "openclaw-front-secretary"
    return root_other / "tools" / "auto_work" / "collect_vscode_state.py"


def main() -> int:
    target = canonical_script()
    if not target.exists():
        print(
            "collect_vscode_state canonical not found.\n"
            f"expected: {target}\n"
            "Run from C:\\1other\\openclaw-front-secretary or restore the extracted canonical first.",
            file=sys.stderr,
        )
        return 2

    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
