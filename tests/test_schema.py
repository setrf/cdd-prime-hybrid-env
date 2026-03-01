from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.schema import validate_packet


class SchemaTests(unittest.TestCase):
    def test_validate_packet_ok(self) -> None:
        packet = {
            "deal_id": "x",
            "decision_date": "2020-01-01",
            "prompt": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
            "answer": {"deal_completed": 1, "outcome_label": 1, "abnormal_return_730d": 0.1},
            "info": {
                "acquirer": "A",
                "target": "B",
                "sector": "Software",
                "deal_type": "horizontal",
                "payment_type": "cash",
                "cross_border": False,
                "premium_pct": 30.0,
                "regulatory_risk": "medium",
            },
            "evidence_items": [
                {
                    "evidence_id": "E1",
                    "source_type": "press",
                    "source_date": "2020-01-01",
                    "summary": "pre-deal",
                }
            ],
        }
        self.assertEqual(validate_packet(packet), [])

    def test_validate_packet_missing(self) -> None:
        packet = {"deal_id": "x"}
        errors = validate_packet(packet)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
