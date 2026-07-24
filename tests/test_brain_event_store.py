"""Tests for the rotating brain event store."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path

from brain_event_store import BrainEventReader, BrainEventWriter


def record(
    number: int,
    *,
    day: str = "2026-07-14",
    source_event_id: str | None = None,
    direction: str = "WAIT",
) -> dict:
    """Return one compact test brain event."""

    return {
        "received_at": f"{day}T12:00:{number % 60:02d}+00:00",
        "source_event_id": source_event_id or f"evt-{number}",
        "event_type": "CRYPTO_ANALYSIS_FINISHED",
        "source": "test",
        "market_type": "crypto",
        "symbol": "BTCUSDT",
        "direction": direction,
        "probability": 55 + number,
        "source_timestamp": f"{day}T12:00:{number % 60:02d}+00:00",
        "payload": {"symbol": "BTCUSDT"},
    }


class BrainEventStoreTest(unittest.TestCase):
    def test_append_persists_one_event_with_manifest_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "brain_events"
            writer = BrainEventWriter(root, rotation_bytes=10_000, fsync_every=1)
            writer.append(record(1))

            files = list(root.glob("*/*.jsonl"))
            self.assertEqual(len(files), 1)
            self.assertEqual(len(files[0].read_text(encoding="utf-8").splitlines()), 1)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            index = json.loads((root / "2026-07-14" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["total_event_count"], 1)
            self.assertEqual(index["total_event_count"], 1)

    def test_rotation_uses_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "brain_events"
            writer = BrainEventWriter(root, rotation_bytes=450, fsync_every=1)
            for number in range(8):
                writer.append(record(number))

            files = sorted(root.glob("2026-07-14/events_*.jsonl"))
            self.assertGreater(len(files), 1)
            index = json.loads((root / "2026-07-14" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["total_event_count"], 8)

    def test_day_change_creates_new_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "brain_events"
            writer = BrainEventWriter(root, rotation_bytes=10_000)
            writer.append(record(1, day="2026-07-14"))
            writer.append(record(2, day="2026-07-15"))

            self.assertTrue((root / "2026-07-14").exists())
            self.assertTrue((root / "2026-07-15").exists())
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["known_days"], ["2026-07-14", "2026-07-15"])

    def test_incomplete_last_line_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            legacy = Path(temp) / "brain_events.jsonl"
            legacy.write_text(
                json.dumps(record(1), ensure_ascii=True) + "\n" + '{"broken":',
                encoding="utf-8",
            )
            reader = BrainEventReader(legacy_file=legacy, rotated_root=Path(temp) / "missing")

            rows = reader.recent(limit=10)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_event_id"], "evt-1")
            self.assertTrue(any(item["warning"] == "incomplete_last_line_skipped" for item in reader.warnings))

    def test_legacy_and_rotated_are_deduped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            legacy = temp_path / "brain_events.jsonl"
            duplicate = record(1, source_event_id="same-event")
            legacy.write_text(json.dumps(duplicate, ensure_ascii=True) + "\n", encoding="utf-8")
            root = temp_path / "brain_events"
            writer = BrainEventWriter(root)
            writer.append(duplicate)
            writer.append(record(2, source_event_id="new-event"))

            rows = BrainEventReader(legacy_file=legacy, rotated_root=root).recent(limit=10)

            self.assertEqual(len(rows), 2)
            self.assertEqual({item["source_event_id"] for item in rows}, {"same-event", "new-event"})

    def test_parallel_writes_keep_jsonl_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "brain_events"
            writer = BrainEventWriter(root, rotation_bytes=2_000, fsync_every=1)

            def write_range(start: int) -> None:
                for number in range(start, start + 10):
                    writer.append(record(number, source_event_id=f"parallel-{number}"))

            threads = [threading.Thread(target=write_range, args=(offset,)) for offset in (0, 10, 20, 30)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            rows = BrainEventReader(rotated_root=root).recent(limit=100)

            self.assertEqual(len(rows), 40)
            self.assertEqual(len({item["source_event_id"] for item in rows}), 40)


if __name__ == "__main__":
    unittest.main()
