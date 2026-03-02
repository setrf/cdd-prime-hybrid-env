#!/usr/bin/env python3
"""Check evaluation metrics against minimum quality thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Regression threshold gate")
    p.add_argument("--metrics", default="data/interim/eval_metrics.json")
    p.add_argument("--min-accuracy", type=float, default=0.60)
    p.add_argument("--max-brier", type=float, default=0.30)
    p.add_argument("--min-utility", type=float, default=0.00)
    p.add_argument("--max-log-loss", type=float, default=0.80)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    metrics = json.loads(Path(args.metrics).read_text())

    checks = [
        (metrics.get("accuracy", 0.0) >= args.min_accuracy, f"accuracy {metrics.get('accuracy')} < {args.min_accuracy}"),
        (metrics.get("brier_score", 1.0) <= args.max_brier, f"brier_score {metrics.get('brier_score')} > {args.max_brier}"),
        (metrics.get("decision_utility", -999.0) >= args.min_utility, f"decision_utility {metrics.get('decision_utility')} < {args.min_utility}"),
        (metrics.get("log_loss", 999.0) <= args.max_log_loss, f"log_loss {metrics.get('log_loss')} > {args.max_log_loss}"),
    ]

    failures = [msg for ok, msg in checks if not ok]
    if failures:
        print("REGRESSION GATE FAILED")
        for msg in failures:
            print(f"- {msg}")
        raise SystemExit(1)

    print("REGRESSION GATE PASSED")


if __name__ == "__main__":
    main()
