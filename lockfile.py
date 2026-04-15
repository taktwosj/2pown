"""Compatibility shim for legacy root imports.

Operational scripts still import ``lockfile`` from the repo root.
The implementation lives in ``tools.ops.lockfile`` after root cleanup.
"""

from tools.ops.lockfile import LockError, acquire_lock, release_lock

__all__ = ["LockError", "acquire_lock", "release_lock"]
