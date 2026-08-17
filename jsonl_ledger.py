"""Append-only JSONL ledger helpers with safe size rotation."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock, RLock
from typing import Any


_PROCESS_LEDGER_LOCKS: set[str] = set()
_PROCESS_LEDGER_LOCKS_GUARD = Lock()


class LedgerLockUnavailableError(RuntimeError):
    """Raised when another adapter or process owns an exclusive ledger lock."""


class ExclusiveFileLock:
    """Hold a non-blocking process and OS lock for one ledger lifetime."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._key = os.path.normcase(str(self.path.resolve(strict=False)))
        self._handle: Any | None = None

    @property
    def acquired(self) -> bool:
        return self._handle is not None

    def acquire(self) -> None:
        if self._handle is not None:
            return
        with _PROCESS_LEDGER_LOCKS_GUARD:
            if self._key in _PROCESS_LEDGER_LOCKS:
                raise LedgerLockUnavailableError(f"ledger lock already held: {self.path}")
            _PROCESS_LEDGER_LOCKS.add(self._key)

        handle: Any | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.path.open("a+b")
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            _lock_file_handle(handle)
            self._handle = handle
        except BaseException:
            if handle is not None:
                handle.close()
            with _PROCESS_LEDGER_LOCKS_GUARD:
                _PROCESS_LEDGER_LOCKS.discard(self._key)
            raise

    def release(self) -> None:
        handle = self._handle
        if handle is None:
            return
        self._handle = None
        try:
            handle.seek(0)
            _unlock_file_handle(handle)
        finally:
            handle.close()
            with _PROCESS_LEDGER_LOCKS_GUARD:
                _PROCESS_LEDGER_LOCKS.discard(self._key)


def _lock_file_handle(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file_handle(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class RotatingJsonlLedger:
    """Append JSONL records and rotate the active file before it grows too large."""

    def __init__(
        self,
        path: Path,
        *,
        max_bytes: int = 128 * 1024 * 1024,
        max_archives: int | None = None,
    ) -> None:
        self.path = path
        self.max_bytes = max(int(max_bytes), 1024 * 1024)
        self.max_archives = None if max_archives is None else max(int(max_archives), 0)
        self._lock = RLock()

    def append(self, record: dict[str, Any]) -> Path:
        """Append one record and return the file that received it."""

        return self.append_many([record])

    def append_many(self, records: list[dict[str, Any]]) -> Path:
        """Append an ordered batch with one flush/fsync per active-file chunk."""

        lines = [json.dumps(record, ensure_ascii=True) + "\n" for record in records]
        if not lines:
            return self.path
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                current_size = self.path.stat().st_size
            except OSError:
                current_size = 0
            pending: list[str] = []
            for line in lines:
                incoming_bytes = len(line.encode("utf-8"))
                if current_size and current_size + incoming_bytes > self.max_bytes:
                    self._write_lines(pending)
                    pending = []
                    self._rotate_if_needed(incoming_bytes)
                    current_size = 0
                pending.append(line)
                current_size += incoming_bytes
            self._write_lines(pending)
        return self.path

    def _write_lines(self, lines: list[str]) -> None:
        """Write one already serialized chunk while the ledger lock is held."""

        if not lines:
            return
        with self.path.open("a", encoding="utf-8") as handle:
            handle.writelines(lines)
            handle.flush()
            os.fsync(handle.fileno())

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        """Move the active ledger to an archive file when it exceeds max_bytes."""

        if not self.path.exists():
            return
        try:
            current_size = self.path.stat().st_size
        except OSError:
            return
        if current_size + incoming_bytes <= self.max_bytes:
            return

        archive_dir = self.path.parent / "archive" / self.path.stem
        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        target = archive_dir / f"{self.path.stem}_{timestamp}{self.path.suffix}"
        counter = 1
        while target.exists():
            target = archive_dir / f"{self.path.stem}_{timestamp}_{counter:03d}{self.path.suffix}"
            counter += 1
        os.replace(self.path, target)
        self._prune_archives(archive_dir)

    def _prune_archives(self, archive_dir: Path) -> None:
        """Keep only the configured number of archives for bounded ledgers."""

        if self.max_archives is None:
            return
        archives = sorted(
            item
            for item in archive_dir.glob(f"{self.path.stem}_*{self.path.suffix}")
            if item.is_file()
        )
        for stale in archives[: max(len(archives) - self.max_archives, 0)]:
            stale.unlink()


def related_jsonl_files(path: Path) -> list[Path]:
    """Return archived ledgers plus the active file, ordered oldest to newest."""

    files: list[Path] = []
    archive_dir = path.parent / "archive" / path.stem
    if archive_dir.exists():
        files.extend(sorted(item for item in archive_dir.glob(f"{path.stem}_*{path.suffix}") if item.is_file()))
    if path.exists() and path.is_file():
        files.append(path)
    return files
