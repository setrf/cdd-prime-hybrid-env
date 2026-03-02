from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.group_metrics import majority_vote_labels, majority_vote_utility, pass_at_k


class GroupMetricsTests(unittest.TestCase):
    def test_pass_at_k(self) -> None:
        sample_preds = [
            [0, 1, 0],  # label 1 -> hit by k=2
            [0, 0, 0],  # label 0 -> hit
            [1, 1, 0],  # label 1 -> hit
            [1, 1, 1],  # label 0 -> miss
        ]
        labels = [1, 0, 1, 0]
        self.assertAlmostEqual(pass_at_k(sample_preds, labels, k=2), 0.75)

    def test_majority_vote_labels(self) -> None:
        sample_preds = [[1, 0], [0, 0], [1, 1], [1, 0]]
        self.assertEqual(majority_vote_labels(sample_preds, k=2, tie_breaker=0), [0, 0, 1, 0])
        self.assertEqual(majority_vote_labels(sample_preds, k=2, tie_breaker=1), [1, 0, 1, 1])

    def test_majority_vote_utility(self) -> None:
        sample_preds = [[1, 1], [0, 0], [1, 0], [1, 0]]
        labels = [1, 0, 1, 0]
        # tie_breaker=0 => voted labels [1,0,0,0]
        # tp=1, tn=2, fn=1 => utility=(1 + 2*0.5 - 1)/4 = 0.25
        self.assertAlmostEqual(majority_vote_utility(sample_preds, labels, k=2, tie_breaker=0), 0.25)


if __name__ == "__main__":
    unittest.main()
