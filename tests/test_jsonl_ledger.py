from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonl_ledger import ExclusiveFileLock, LedgerLockUnavailableError, RotatingJsonlLedger


class RotatingJsonlLedgerTest(unittest.TestCase):
    def test_exclusive_file_lock_is_process_wide_and_releasable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.jsonl.lock"
            first = ExclusiveFileLock(path)
            second = ExclusiveFileLock(path)

            first.acquire()
            self.assertTrue(first.acquired)
            with self.assertRaises(LedgerLockUnavailableError):
                second.acquire()
            first.release()

            second.acquire()
            self.assertTrue(second.acquired)
            second.release()

    def test_append_many_writes_ordered_batch_with_one_fsync(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            ledger = RotatingJsonlLedger(path)
            records = [{"sequence": index} for index in range(5)]

            with patch("jsonl_ledger.os.fsync") as fsync:
                ledger.append_many(records)

            persisted = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(persisted, records)
            fsync.assert_called_once()


if __name__ == "__main__":
    unittest.main()
