"""Conflict-resistant atomic JSON persistence for small runtime state files."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Iterable


DEFAULT_RETRY_DELAYS = (0.01, 0.025, 0.05, 0.1, 0.2)
_RETRIABLE_WINDOWS_ERRORS = frozenset({5, 32, 33})
_PATH_LOCKS: dict[str, RLock] = {}
_PATH_LOCKS_GUARD = Lock()


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    retry_delays: Iterable[float] = DEFAULT_RETRY_DELAYS,
) -> None:
    """Validate and atomically replace one JSON file.

    Writes to the same resolved path are serialized inside the process. Every
    attempt uses its own same-directory temporary file, and transient Windows
    sharing violations during ``os.replace`` receive a small bounded retry.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=True)
    json.loads(text)
    delays = tuple(max(float(delay), 0.0) for delay in retry_delays)

    with _path_lock(path):
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())

            for attempt in range(len(delays) + 1):
                try:
                    os.replace(temporary_path, path)
                    temporary_path = None
                    return
                except OSError as exc:
                    if attempt >= len(delays) or not _is_retriable_replace_error(exc):
                        raise
                    time.sleep(delays[attempt])
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass


def _path_lock(path: Path) -> RLock:
    key = os.path.normcase(str(path.resolve(strict=False)))
    with _PATH_LOCKS_GUARD:
        return _PATH_LOCKS.setdefault(key, RLock())


def _is_retriable_replace_error(exc: OSError) -> bool:
    if isinstance(exc, PermissionError):
        return True
    return getattr(exc, "winerror", None) in _RETRIABLE_WINDOWS_ERRORS
