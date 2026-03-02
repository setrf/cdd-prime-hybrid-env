#!/usr/bin/env python3
"""Evaluate multi-sample policy metrics (pass@k, majority-vote utility)."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.group_metrics import majority_vote_utility, pass_at_k


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate grouped multi-sample predictions")
    p.add_argument("--dataset", default="data/processed/test.jsonl")
    p.add_argument("--predictions", required=True, help="JSONL with deal_id and predicted_label")
    p.add_argument("--k-values", default="1,2,3,5")
    p.add_argument("--output", default="data/interim/group_metrics.json")
    return p.parse_args()


def _true_label(answer: Any) -> int:
    if isinstance(answer, str):
        obj = json.loads(answer)
    elif isinstance(answer, dict):
        obj = answer
    else:
        raise ValueError("unsupported answer type")
    return int(obj["outcome_label"])


def load_labels(dataset_path: Path) -> dict[str, int]:
    labels: dict[str, int] = {}
    with dataset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            labels[str(row["deal_id"])] = _true_label(row["answer"])
    return labels


def load_group_preds(path: Path) -> dict[str, list[int]]:
    grouped: dict[str, list[tuple[int, int]]] = defaultdict(list)
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            deal_id = str(row["deal_id"])
            pred = int(row["predicted_label"])
            sample_idx = int(row.get("sample_idx", 0))
            grouped[deal_id].append((sample_idx, pred))
    out: dict[str, list[int]] = {}
    for deal_id, vals in grouped.items():
        vals.sort(key=lambda x: x[0])
        out[deal_id] = [pred for _, pred in vals]
    return out


def main() -> None:
    args = parse_args()
    labels_map = load_labels(Path(args.dataset))
    grouped_preds = load_group_preds(Path(args.predictions))
    common_deals = sorted(set(labels_map.keys()) & set(grouped_preds.keys()))
    if not common_deals:
        raise RuntimeError("no overlapping deal_id values between dataset and predictions")

    sample_preds = [grouped_preds[d] for d in common_deals]
    labels = [labels_map[d] for d in common_deals]

    ks = [int(x.strip()) for x in args.k_values.split(",") if x.strip()]
    metrics: list[dict[str, float]] = []
    for k in ks:
        metrics.append(
            {
                "k": float(k),
                "pass_at_k": pass_at_k(sample_preds, labels, k=k),
                "majority_vote_utility": majority_vote_utility(sample_preds, labels, k=k, tie_breaker=0),
            }
        )

    out = {
        "n_deals": len(common_deals),
        "k_metrics": metrics,
        "prediction_source": str(args.predictions),
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"wrote {out_path}")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
