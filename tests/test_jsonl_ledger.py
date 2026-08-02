from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonl_ledger import RotatingJsonlLedger


class RotatingJsonlLedgerTest(unittest.TestCase):
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
