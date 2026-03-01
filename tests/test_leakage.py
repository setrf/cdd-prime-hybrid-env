from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.leakage import check_prompt_for_outcome_leaks, check_timestamp_leakage


class LeakageTests(unittest.TestCase):
    def test_timestamp_leak_detected(self) -> None:
        row = {
            "decision_date": "2022-01-01",
            "evidence_items": [
                {"evidence_id": "E1", "source_date": "2022-01-02"},
            ],
            "prompt": [{"role": "user", "content": "hello"}],
        }
        issues = check_timestamp_leakage(row)
        self.assertTrue(issues)

    def test_prompt_outcome_leak_detected(self) -> None:
        row = {
            "decision_date": "2022-01-01",
            "evidence_items": [{"evidence_id": "E1", "source_date": "2022-01-01"}],
            "prompt": [{"role": "user", "content": "The deal eventually closed after review."}],
        }
        issues = check_prompt_for_outcome_leaks(row)
        self.assertTrue(issues)


if __name__ == "__main__":
    unittest.main()
