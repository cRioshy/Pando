"""Append-only JSONL ledger helpers with safe size rotation."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any


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
