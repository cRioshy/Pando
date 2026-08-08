"""Tests for conflict-resistant atomic JSON persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch


class AtomicJsonTest(unittest.TestCase):
    def test_transient_permission_error_is_retried(self) -> None:
        from atomic_json import atomic_write_json

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "state.json"
            real_replace = __import__("os").replace
            attempts = 0

            def flaky_replace(source: Path, destination: Path) -> None:
                nonlocal attempts
                attempts += 1
                if attempts < 3:
                    raise PermissionError(13, "temporary sharing violation", str(destination))
                real_replace(source, destination)

            with patch("atomic_json.os.replace", side_effect=flaky_replace):
                atomic_write_json(target, {"status": "ok"}, retry_delays=(0.0, 0.0, 0.0))

            self.assertEqual(attempts, 3)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"status": "ok"})
            self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])

    def test_parallel_writes_use_independent_temporary_files(self) -> None:
        from atomic_json import atomic_write_json

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "state.json"

            with ThreadPoolExecutor(max_workers=8) as pool:
                futures = [
                    pool.submit(atomic_write_json, target, {"writer": index, "values": list(range(100))})
                    for index in range(24)
                ]
                for future in futures:
                    future.result()

            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertIn(payload["writer"], range(24))
            self.assertEqual(payload["values"], list(range(100)))
            self.assertEqual(list(target.parent.glob(f".{target.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
