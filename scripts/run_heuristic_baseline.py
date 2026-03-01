#!/usr/bin/env python3
"""Run a deterministic heuristic baseline for CDD predictions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.metrics import accuracy, brier_score, decision_utility, log_loss


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Heuristic baseline on packet JSONL")
    parser.add_argument("--dataset", default="data/processed/test.jsonl")
    parser.add_argument("--output", default="data/interim/heuristic_predictions_test.jsonl")
    parser.add_argument("--threshold", type=float, default=0.55)
    return parser.parse_args()


def clamp(v: float, low: float = 0.02, high: float = 0.98) -> float:
    return max(low, min(high, v))


def score_packet(info: dict) -> tuple[float, list[str]]:
    p = 0.55
    reasons: list[str] = []

    risk = str(info.get("regulatory_risk", "medium")).lower()
    if risk == "high":
        p -= 0.18
        reasons.append("high_reg_risk")
    elif risk == "medium":
        p -= 0.08
        reasons.append("medium_reg_risk")
    else:
        p += 0.05
        reasons.append("low_reg_risk")

    if bool(info.get("cross_border", False)):
        p -= 0.04
        reasons.append("cross_border")

    premium = float(info.get("premium_pct", 25.0))
    if premium > 25:
        p -= min(0.15, (premium - 25.0) * 0.003)
        reasons.append("high_premium")
    else:
        p += min(0.05, (25.0 - premium) * 0.0015)
        reasons.append("moderate_premium")

    deal_type = str(info.get("deal_type", "horizontal")).lower()
    if deal_type == "vertical":
        p += 0.03
        reasons.append("vertical_synergy")
    elif deal_type == "conglomerate":
        p -= 0.03
        reasons.append("conglomerate_complexity")

    payment = str(info.get("payment_type", "cash")).lower()
    if payment == "cash":
        p += 0.02
        reasons.append("cash_certainty")
    elif payment == "stock":
        p -= 0.02
        reasons.append("stock_execution_risk")
    elif payment == "cash_stock":
        p -= 0.01
        reasons.append("mixed_consideration")

    sector = str(info.get("sector", "")).lower()
    if "software" in sector:
        p += 0.02
        reasons.append("software_margin_profile")
    if "semiconductor" in sector:
        p -= 0.02
        reasons.append("semi_geopolitical_exposure")
    if "telecom" in sector:
        p -= 0.01
        reasons.append("telecom_regulatory_burden")

    return clamp(p), reasons


def true_label_from_answer(answer: object) -> int:
    if isinstance(answer, dict):
        return int(answer["outcome_label"])
    if isinstance(answer, str):
        parsed = json.loads(answer)
        if isinstance(parsed, dict) and "outcome_label" in parsed:
            return int(parsed["outcome_label"])
    raise ValueError("answer is not a valid dict or JSON string with outcome_label")


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    labels: list[int] = []
    probs: list[float] = []
    pred_labels: list[int] = []

    rows_out: list[dict] = []
    with dataset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            info = row["info"]
            prob, reasons = score_packet(info)
            pred = 1 if prob >= args.threshold else 0
            truth = true_label_from_answer(row["answer"])

            labels.append(truth)
            probs.append(prob)
            pred_labels.append(pred)

            rows_out.append(
                {
                    "deal_id": row["deal_id"],
                    "success_probability": round(prob, 6),
                    "recommendation": "GO" if pred == 1 else "NO_GO",
                    "predicted_label": pred,
                    "true_label": truth,
                    "features_used": reasons,
                }
            )

    with out_path.open("w") as f:
        for r in rows_out:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    print(f"wrote {out_path}")
    print(f"rows={len(rows_out)}")
    print(f"brier={brier_score(probs, labels):.6f}")
    print(f"log_loss={log_loss(probs, labels):.6f}")
    print(f"accuracy={accuracy(pred_labels, labels):.6f}")
    print(f"utility={decision_utility(pred_labels, labels):.6f}")


if __name__ == "__main__":
    main()
