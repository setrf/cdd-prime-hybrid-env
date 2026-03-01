from __future__ import annotations

import math
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.metrics import accuracy, brier_score, decision_utility, log_loss


class MetricsTests(unittest.TestCase):
    def test_brier(self) -> None:
        probs = [0.8, 0.2]
        labels = [1, 0]
        expected = ((0.8 - 1) ** 2 + (0.2 - 0) ** 2) / 2
        self.assertAlmostEqual(brier_score(probs, labels), expected)

    def test_log_loss(self) -> None:
        probs = [0.8, 0.2]
        labels = [1, 0]
        expected = (-(math.log(0.8) + math.log(0.8))) / 2
        self.assertAlmostEqual(log_loss(probs, labels), expected)

    def test_accuracy(self) -> None:
        pred = [1, 0, 1, 1]
        y = [1, 1, 1, 0]
        self.assertAlmostEqual(accuracy(pred, y), 0.5)

    def test_decision_utility(self) -> None:
        pred = [1, 1, 0, 0]
        y = [1, 0, 0, 1]
        # tp=1, fp=1, tn=1, fn=1
        expected = (1.0 + -1.5 + 0.5 + -1.0) / 4
        self.assertAlmostEqual(decision_utility(pred, y), expected)


if __name__ == "__main__":
    unittest.main()
