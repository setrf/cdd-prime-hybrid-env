#!/usr/bin/env python3
"""Evaluate prediction JSONL against packet labels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.metrics import accuracy, brier_score, calibration_bins, decision_utility, log_loss


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate predictions")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", default="data/interim/eval_metrics.json")
    parser.add_argument("--threshold", type=float, default=0.55)
    return parser.parse_args()


def load_dataset(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            answer = row.get("answer")
            if isinstance(answer, dict):
                out[row["deal_id"]] = int(answer["outcome_label"])
            elif isinstance(answer, str):
                parsed = json.loads(answer)
                if not isinstance(parsed, dict) or "outcome_label" not in parsed:
                    raise ValueError(f"invalid answer JSON for deal_id={row.get('deal_id')}")
                out[row["deal_id"]] = int(parsed["outcome_label"])
            else:
                raise ValueError(f"unsupported answer type for deal_id={row.get('deal_id')}")
    return out


def load_predictions(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[row["deal_id"]] = float(row["success_probability"])
    return out


def main() -> None:
    args = parse_args()
    y_map = load_dataset(Path(args.dataset))
    p_map = load_predictions(Path(args.predictions))

    common_ids = sorted(set(y_map) & set(p_map))
    if not common_ids:
        raise RuntimeError("no overlapping deal_id values found")

    probs = [p_map[d] for d in common_ids]
    labels = [y_map[d] for d in common_ids]
    preds = [1 if p >= args.threshold else 0 for p in probs]

    metrics = {
        "n": len(common_ids),
        "threshold": args.threshold,
        "brier_score": brier_score(probs, labels),
        "log_loss": log_loss(probs, labels),
        "accuracy": accuracy(preds, labels),
        "decision_utility": decision_utility(preds, labels),
        "calibration_bins": calibration_bins(probs, labels, bins=5),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2, sort_keys=True))

    print(f"wrote {out_path}")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
