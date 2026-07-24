"""Rotating JSONL storage for Pandorick brain events.

This module is intentionally technical infrastructure only. It does not change
trading decisions, learning scores, or market analysis results.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, date, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Iterable


FORMAT_VERSION = 1
DEFAULT_ROTATION_BYTES = 200 * 1024 * 1024
DEFAULT_DAY_WARNING_BYTES = int(1.5 * 1024 * 1024 * 1024)
DEFAULT_MAX_TAIL_BYTES = 12_000_000


def utc_now_iso() -> str:
    """Return a UTC timestamp in ISO format."""

    return datetime.now(UTC).isoformat()


def stable_event_id(record: dict[str, Any]) -> str:
    """Return a deterministic technical ID for dedupe-only purposes."""

    existing = (
        record.get("event_id")
        or record.get("source_event_id")
        or record.get("id")
        or _payload_value(record, "event_id")
        or _payload_value(record, "source_event_id")
    )
    if existing:
        return str(existing)

    safe_record = {
        "event_type": record.get("event_type"),
        "source": record.get("source"),
        "market_type": record.get("market_type"),
        "symbol": record.get("symbol"),
        "direction": record.get("direction"),
        "probability": record.get("probability"),
        "source_timestamp": record.get("source_timestamp"),
        "received_at": record.get("received_at"),
    }
    encoded = json.dumps(safe_record, sort_keys=True, ensure_ascii=True, default=str)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"derived:{digest}"


def _payload_value(record: dict[str, Any], key: str) -> Any:
    payload = record.get("payload")
    if isinstance(payload, dict):
        return payload.get(key)
    return None


class BrainEventWriter:
    """Append brain events into a per-day rotating JSONL structure."""

    def __init__(
        self,
        root_dir: Path,
        *,
        rotation_bytes: int = DEFAULT_ROTATION_BYTES,
        day_warning_bytes: int = DEFAULT_DAY_WARNING_BYTES,
        fsync_every: int = 25,
    ) -> None:
        self.root_dir = root_dir
        self.rotation_bytes = max(1024, int(rotation_bytes))
        self.day_warning_bytes = max(self.rotation_bytes, int(day_warning_bytes))
        self.fsync_every = max(1, int(fsync_every))
        self._lock = RLock()
        self._writes_since_fsync = 0

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        """Append one record and update day index plus manifest atomically."""

        with self._lock:
            stored = dict(record)
            stored.setdefault("received_at", utc_now_iso())
            stored["event_id"] = stable_event_id(stored)
            event_day = _event_day(stored)
            day_dir = self.root_dir / event_day.isoformat()
            day_dir.mkdir(parents=True, exist_ok=True)

            index = self._load_index(day_dir, event_day)
            line = json.dumps(stored, ensure_ascii=True, separators=(",", ":"), default=str).encode("utf-8") + b"\n"
            file_entry = self._active_file_entry(day_dir, index, len(line))
            file_path = day_dir / file_entry["name"]

            with file_path.open("ab") as handle:
                handle.write(line)
                handle.flush()
                self._writes_since_fsync += 1
                if self._writes_since_fsync >= self.fsync_every:
                    os.fsync(handle.fileno())
                    self._writes_since_fsync = 0

            self._update_file_entry(file_entry, stored, len(line))
            self._refresh_index_totals(index)
            index["last_successful_write_at"] = utc_now_iso()
            self._write_json_atomic(day_dir / "index.json", index)

            manifest = self._load_manifest()
            self._update_manifest(manifest, event_day, index)
            self._write_json_atomic(self.root_dir / "manifest.json", manifest)
            return stored

    def _active_file_entry(self, day_dir: Path, index: dict[str, Any], next_line_bytes: int) -> dict[str, Any]:
        files = index.setdefault("files", [])
        if not files:
            entry = self._new_file_entry(1)
            files.append(entry)
            return entry

        entry = files[-1]
        file_path = day_dir / str(entry["name"])
        current_size = file_path.stat().st_size if file_path.exists() else int(entry.get("size_bytes", 0))
        if current_size + next_line_bytes <= self.rotation_bytes:
            entry["size_bytes"] = current_size
            return entry

        entry = self._new_file_entry(len(files) + 1)
        files.append(entry)
        return entry

    def _new_file_entry(self, sequence: int) -> dict[str, Any]:
        return {
            "name": f"events_{sequence:04d}.jsonl",
            "size_bytes": 0,
            "event_count": 0,
            "first_event_at": None,
            "last_event_at": None,
            "event_types": {},
        }

    def _update_file_entry(self, entry: dict[str, Any], record: dict[str, Any], written_bytes: int) -> None:
        timestamp = str(record.get("received_at") or record.get("source_timestamp") or utc_now_iso())
        event_type = str(record.get("event_type") or "UNKNOWN")
        entry["size_bytes"] = int(entry.get("size_bytes", 0)) + written_bytes
        entry["event_count"] = int(entry.get("event_count", 0)) + 1
        entry["first_event_at"] = entry.get("first_event_at") or timestamp
        entry["last_event_at"] = timestamp
        event_types = entry.setdefault("event_types", {})
        event_types[event_type] = int(event_types.get(event_type, 0)) + 1

    def _refresh_index_totals(self, index: dict[str, Any]) -> None:
        files = [item for item in index.get("files", []) if isinstance(item, dict)]
        index["total_size_bytes"] = sum(int(item.get("size_bytes", 0)) for item in files)
        index["total_event_count"] = sum(int(item.get("event_count", 0)) for item in files)
        warnings: list[str] = []
        if index["total_size_bytes"] >= self.day_warning_bytes:
            warnings.append("day_size_warning")
        index["warnings"] = warnings

    def _load_index(self, day_dir: Path, event_day: date) -> dict[str, Any]:
        path = day_dir / "index.json"
        data = _read_json(path)
        if isinstance(data, dict):
            data.setdefault("date", event_day.isoformat())
            data.setdefault("files", [])
            data.setdefault("warnings", [])
            return data
        return {
            "date": event_day.isoformat(),
            "files": [],
            "total_size_bytes": 0,
            "total_event_count": 0,
            "last_successful_write_at": None,
            "warnings": [],
        }

    def _load_manifest(self) -> dict[str, Any]:
        data = _read_json(self.root_dir / "manifest.json")
        if isinstance(data, dict):
            data.setdefault("format_version", FORMAT_VERSION)
            data.setdefault("known_days", [])
            return data
        return {
            "format_version": FORMAT_VERSION,
            "active_day": None,
            "active_file": None,
            "known_days": [],
            "total_event_count": 0,
            "total_size_bytes": 0,
            "oldest_event_at": None,
            "newest_event_at": None,
            "rotation_bytes": self.rotation_bytes,
            "day_warning_bytes": self.day_warning_bytes,
            "updated_at": None,
        }

    def _update_manifest(self, manifest: dict[str, Any], event_day: date, index: dict[str, Any]) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        day_name = event_day.isoformat()
        known_days = set(str(day) for day in manifest.get("known_days", []))
        known_days.add(day_name)
        manifest["known_days"] = sorted(known_days)
        manifest["active_day"] = day_name
        files = [item for item in index.get("files", []) if isinstance(item, dict)]
        if files:
            manifest["active_file"] = f"{day_name}/{files[-1].get('name')}"
        manifest["total_event_count"] = self._sum_index_field("total_event_count")
        manifest["total_size_bytes"] = self._sum_index_field("total_size_bytes")
        manifest["oldest_event_at"] = self._oldest_event_at()
        manifest["newest_event_at"] = self._newest_event_at()
        manifest["rotation_bytes"] = self.rotation_bytes
        manifest["day_warning_bytes"] = self.day_warning_bytes
        manifest["updated_at"] = utc_now_iso()

    def _sum_index_field(self, field: str) -> int:
        total = 0
        for index_path in self.root_dir.glob("*/index.json"):
            data = _read_json(index_path)
            if isinstance(data, dict):
                total += int(data.get(field, 0))
        return total

    def _oldest_event_at(self) -> str | None:
        values: list[str] = []
        for index_path in self.root_dir.glob("*/index.json"):
            data = _read_json(index_path)
            if not isinstance(data, dict):
                continue
            for item in data.get("files", []):
                if isinstance(item, dict) and item.get("first_event_at"):
                    values.append(str(item["first_event_at"]))
        return min(values) if values else None

    def _newest_event_at(self) -> str | None:
        values: list[str] = []
        for index_path in self.root_dir.glob("*/index.json"):
            data = _read_json(index_path)
            if not isinstance(data, dict):
                continue
            for item in data.get("files", []):
                if isinstance(item, dict) and item.get("last_event_at"):
                    values.append(str(item["last_event_at"]))
        return max(values) if values else None

    def _write_json_atomic(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
        os.replace(tmp_path, path)


class BrainEventReader:
    """Read legacy and rotated brain events through one compatibility layer."""

    def __init__(
        self,
        *,
        legacy_file: Path | None = None,
        rotated_root: Path | None = None,
        max_tail_bytes: int = DEFAULT_MAX_TAIL_BYTES,
    ) -> None:
        self.legacy_file = legacy_file
        self.rotated_root = rotated_root
        self.max_tail_bytes = max(1024, int(max_tail_bytes))
        self.warnings: list[dict[str, Any]] = []

    def recent(self, *, limit: int) -> list[dict[str, Any]]:
        """Return recent records from both sources without duplicate events."""

        effective_limit = max(0, int(limit))
        if effective_limit == 0:
            return []
        records: list[dict[str, Any]] = []
        records.extend(self._recent_legacy(effective_limit))
        records.extend(self._recent_rotated(effective_limit))
        return self._dedupe(records)[-effective_limit:]

    def all(self) -> Iterable[dict[str, Any]]:
        """Yield all readable events from legacy and rotated storage."""

        yielded: set[str] = set()
        for record in self._iter_file(self.legacy_file):
            event_id = stable_event_id(record)
            if event_id in yielded:
                continue
            yielded.add(event_id)
            yield record
        for path in self._rotated_files():
            for record in self._iter_file(path):
                event_id = stable_event_id(record)
                if event_id in yielded:
                    continue
                yielded.add(event_id)
                yield record

    def _recent_legacy(self, limit: int) -> list[dict[str, Any]]:
        return list(self._iter_recent_file(self.legacy_file, limit))

    def _recent_rotated(self, limit: int) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in reversed(self._rotated_files()):
            records[:0] = list(self._iter_recent_file(path, limit))
            if len(records) >= limit:
                break
        return records[-limit:]

    def _rotated_files(self) -> list[Path]:
        if self.rotated_root is None or not self.rotated_root.exists():
            return []
        files = [
            path
            for path in self.rotated_root.glob("*/*.jsonl")
            if path.is_file() and path.name.startswith("events_")
        ]
        return sorted(files, key=lambda path: (path.parent.name, path.name))

    def _iter_recent_file(self, path: Path | None, limit: int) -> Iterable[dict[str, Any]]:
        if path is None or not path.exists() or not path.is_file():
            return []
        try:
            size = path.stat().st_size
            start = max(0, size - self.max_tail_bytes)
            with path.open("rb") as handle:
                handle.seek(start)
                data = handle.read(self.max_tail_bytes)
        except OSError as exc:
            self.warnings.append({"path": str(path), "warning": str(exc)})
            return []
        lines = data.decode("utf-8", errors="replace").splitlines()
        if start > 0 and lines:
            lines = lines[1:]
        return self._parse_lines(path, lines[-limit:], allow_incomplete_last=True)

    def _iter_file(self, path: Path | None) -> Iterable[dict[str, Any]]:
        if path is None or not path.exists() or not path.is_file():
            return []
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                previous = ""
                for line in handle:
                    if previous:
                        for item in self._parse_lines(
                            path,
                            [previous],
                            allow_incomplete_last=False,
                        ):
                            yield item
                    previous = line
                if previous:
                    for item in self._parse_lines(path, [previous], allow_incomplete_last=True):
                        yield item
        except OSError as exc:
            self.warnings.append({"path": str(path), "warning": str(exc)})
            return []

    def _parse_lines(
        self,
        path: Path,
        lines: Iterable[str],
        *,
        allow_incomplete_last: bool,
    ) -> list[dict[str, Any]]:
        parsed: list[dict[str, Any]] = []
        line_list = list(lines)
        for index, line in enumerate(line_list, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                if allow_incomplete_last and index == len(line_list):
                    self.warnings.append(
                        {"path": str(path), "warning": "incomplete_last_line_skipped"}
                    )
                    continue
                self.warnings.append({"path": str(path), "warning": f"invalid_json_line:{exc.msg}"})
                continue
            if isinstance(item, dict):
                parsed.append(item)
        return parsed

    def _dedupe(self, records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for record in records:
            event_id = stable_event_id(record)
            if event_id in seen:
                continue
            seen.add(event_id)
            unique.append(record)
        return unique


def _read_json(path: Path) -> Any:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _event_day(record: dict[str, Any]) -> date:
    value = str(record.get("received_at") or record.get("source_timestamp") or "")
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            pass
    return datetime.now(UTC).date()
