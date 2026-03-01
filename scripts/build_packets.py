#!/usr/bin/env python3
"""Build pre-deal prompt packets from enriched deal rows."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "You are a buy-side commercial due diligence analyst. "
    "Assess this deal using only provided pre-deal information. "
    "Return strict JSON with keys: recommendation, success_probability, "
    "risk_flags, workstream_findings, evidence_citations, and thesis_summary."
)

WORKSTREAMS = [
    "market_growth",
    "customer_demand",
    "competitive_position",
    "pricing_power",
    "gtm_execution",
    "operational_feasibility",
    "regulatory_risk",
    "integration_risk",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build packet JSONL from enriched deals")
    parser.add_argument("--input", default="data/interim/deals_enriched.csv")
    parser.add_argument("--output", default="data/interim/deal_packets.jsonl")
    return parser.parse_args()


def _as_float(value: str) -> float | None:
    v = str(value).strip()
    if not v:
        return None
    return float(v)


def _as_int(value: str) -> int | None:
    v = str(value).strip()
    if not v:
        return None
    return int(v)


def _to_bool_flag(value: str) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "y"}


def build_user_prompt(row: dict[str, str]) -> str:
    lines = []
    lines.append(f"Deal ID: {row['deal_id']}")
    lines.append(f"Decision Date: {row['decision_date']}")
    lines.append(f"Acquirer: {row['acquirer']} ({row['acquirer_ticker']})")
    lines.append(f"Target: {row['target']}")
    lines.append(f"Sector: {row['sector']}")
    lines.append(f"Deal Type: {row['deal_type']}")
    lines.append(f"Payment Type: {row['payment_type']}")
    lines.append(f"Cross Border: {row['cross_border']}")
    lines.append(f"Deal Value (USD B): {row['deal_value_usd_b']}")
    lines.append(f"Premium (%): {row['premium_pct']}")
    lines.append(f"Regulatory Risk (management estimate): {row['regulatory_risk']}")
    lines.append(f"Analyst note: {row['notes']}")
    lines.append("Required CDD workstreams to cover:")
    for w in WORKSTREAMS:
        lines.append(f"- {w}")
    lines.append("Output requirements:")
    lines.append("- recommendation: GO or NO_GO")
    lines.append("- success_probability: float in [0,1]")
    lines.append("- risk_flags: list of concise red flags")
    lines.append("- workstream_findings: object keyed by workstream")
    lines.append("- evidence_citations: list of evidence_id strings")
    lines.append("- thesis_summary: short paragraph")
    return "\n".join(lines)


def build_evidence_items(row: dict[str, str]) -> list[dict[str, str]]:
    announce = date.fromisoformat(row["announce_date"])
    decision = date.fromisoformat(row["decision_date"])
    pre_macro = max(date(2000, 1, 1), decision - timedelta(days=30))

    return [
        {
            "evidence_id": "EV1_PRESS_RELEASE",
            "source_type": "company_press_release",
            "source_date": announce.isoformat(),
            "summary": f"Public announcement of {row['acquirer']} acquiring {row['target']} with headline value {row['deal_value_usd_b']}B.",
        },
        {
            "evidence_id": "EV2_DEAL_TERMS",
            "source_type": "deal_terms_snapshot",
            "source_date": decision.isoformat(),
            "summary": f"Terms include payment type {row['payment_type']}, premium {row['premium_pct']}%, and deal type {row['deal_type']}.",
        },
        {
            "evidence_id": "EV3_RISK_CONTEXT",
            "source_type": "analyst_context",
            "source_date": pre_macro.isoformat(),
            "summary": f"Pre-deal risk context: regulatory risk {row['regulatory_risk']}, cross_border={row['cross_border']}.",
        },
    ]


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(input_path.open()))
    if not rows:
        raise RuntimeError("input file has no rows")

    packets: list[dict[str, Any]] = []
    skipped = 0

    for row in rows:
        outcome_label = _as_int(row.get("outcome_label", ""))
        if outcome_label is None:
            skipped += 1
            continue

        abnormal = _as_float(row.get("abnormal_return_730d", ""))
        deal_completed = 1 if row["status"].strip().lower() == "completed" else 0

        packet: dict[str, Any] = {
            "deal_id": row["deal_id"],
            "decision_date": row["decision_date"],
            "prompt": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(row)},
            ],
            "answer": {
                "deal_completed": deal_completed,
                "outcome_label": outcome_label,
                "abnormal_return_730d": abnormal,
            },
            "info": {
                "acquirer": row["acquirer"],
                "target": row["target"],
                "sector": row["sector"],
                "deal_type": row["deal_type"],
                "payment_type": row["payment_type"],
                "cross_border": _to_bool_flag(row["cross_border"]),
                "premium_pct": float(row["premium_pct"]),
                "regulatory_risk": row["regulatory_risk"],
                "deal_value_usd_b": float(row["deal_value_usd_b"]),
                "primary_source": row.get("primary_source", ""),
            },
            "evidence_items": build_evidence_items(row),
        }

        packets.append(packet)

    with output_path.open("w") as f:
        for packet in packets:
            f.write(json.dumps(packet, sort_keys=True) + "\n")

    print(f"wrote {output_path}")
    print(f"packets={len(packets)} skipped_unlabeled={skipped}")


if __name__ == "__main__":
    main()
