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
    p = argparse.ArgumentParser(description="Build packet JSONL from enriched deals")
    p.add_argument("--input", default="data/interim/deals_enriched.csv")
    p.add_argument("--output", default="data/interim/deal_packets.jsonl")
    p.add_argument("--text-evidence", default="data/interim/text_evidence.jsonl")
    p.add_argument("--max-text-evidence", type=int, default=1)
    return p.parse_args()


def _as_float(value: str, default: float | None = None) -> float | None:
    v = str(value).strip()
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def _as_int(value: str) -> int | None:
    v = str(value).strip()
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def _to_bool_flag(value: str) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "y"}


def load_text_evidence(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            deal_id = str(row.get("deal_id", "")).strip()
            if not deal_id:
                continue
            items = row.get("text_evidence", [])
            if isinstance(items, list):
                out[deal_id] = [i for i in items if isinstance(i, dict)]
    return out


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
    lines.append(f"Deal Value (USD B): {row.get('deal_value_usd_b', '')}")
    lines.append(f"Premium (%): {row['premium_pct']}")
    lines.append(f"Regulatory Risk (pre-deal estimate): {row['regulatory_risk']}")
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


def build_evidence_items(row: dict[str, str]) -> list[dict[str, Any]]:
    announce = date.fromisoformat(row["announce_date"])
    decision = date.fromisoformat(row["decision_date"])
    pre_macro = max(date(2000, 1, 1), decision - timedelta(days=30))
    source_url = row.get("primary_source", "")
    source_quality = _as_float(row.get("source_quality_score", ""), 0.65) or 0.65

    ev1_id = f"EV1_PRIMARY_{row['deal_id']}"
    ev2_id = f"EV2_TERMS_{row['deal_id']}"
    ev3_id = f"EV3_CONTEXT_{row['deal_id']}"

    return [
        {
            "evidence_id": ev1_id,
            "source_type": "primary_or_cited_source",
            "source_url": source_url,
            "source_date": announce.isoformat(),
            "source_quality_score": source_quality,
            "summary": (
                f"Primary/cited source for {row['acquirer']} acquiring {row['target']} "
                f"near announcement date."
            ),
        },
        {
            "evidence_id": ev2_id,
            "source_type": "deal_terms_snapshot",
            "source_url": row.get("source_page", ""),
            "source_date": decision.isoformat(),
            "source_quality_score": 0.60,
            "summary": (
                f"Terms snapshot: payment={row['payment_type']}, premium={row['premium_pct']}%, "
                f"cross_border={row['cross_border']}, value_usd_b={row.get('deal_value_usd_b', '')}."
            ),
        },
        {
            "evidence_id": ev3_id,
            "source_type": "risk_context",
            "source_url": row.get("source_page", ""),
            "source_date": pre_macro.isoformat(),
            "source_quality_score": 0.55,
            "summary": (
                f"Pre-deal context: regulatory_risk={row['regulatory_risk']}, sector={row['sector']}, "
                f"deal_type={row['deal_type']}."
            ),
        },
    ]


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(in_path.open()))
    if not rows:
        raise RuntimeError("input file has no rows")
    text_evidence_map = load_text_evidence(Path(args.text_evidence))

    packets: list[dict[str, Any]] = []
    skipped = 0

    for row in rows:
        outcome_label = _as_int(row.get("outcome_label", ""))
        if outcome_label is None:
            skipped += 1
            continue

        deal_completed = _as_int(row.get("close_label", ""))
        if deal_completed is None:
            deal_completed = 1 if row.get("status", "").strip().lower() == "completed" else 0

        answer_payload = {
            "deal_completed": deal_completed,
            "close_label": deal_completed,
            "outcome_label": outcome_label,
            "thesis_hit_label": _as_int(row.get("thesis_hit_label", "")),
            "abnormal_return_365d": _as_float(row.get("abnormal_return_365d", "")),
            "abnormal_return_730d": _as_float(row.get("abnormal_return_730d", "")),
            "max_drawdown_365d": _as_float(row.get("max_drawdown_365d", "")),
            "max_drawdown_730d": _as_float(row.get("max_drawdown_730d", "")),
        }

        evidence_items = build_evidence_items(row)
        extra_evidence = text_evidence_map.get(row["deal_id"], [])
        if args.max_text_evidence > 0:
            extra_evidence = extra_evidence[: args.max_text_evidence]
        evidence_items.extend(extra_evidence)

        packet: dict[str, Any] = {
            "deal_id": row["deal_id"],
            "decision_date": row["decision_date"],
            "prompt": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(row)},
            ],
            # verifiers 0.1.5 expects answer string in eval outputs.
            "answer": json.dumps(answer_payload, sort_keys=True),
            "info": {
                "acquirer": row["acquirer"],
                "target": row["target"],
                "sector": row["sector"],
                "deal_type": row["deal_type"],
                "payment_type": row["payment_type"],
                "cross_border": _to_bool_flag(row["cross_border"]),
                "premium_pct": _as_float(row.get("premium_pct", ""), 25.0),
                "regulatory_risk": row["regulatory_risk"],
                "deal_value_usd_b": _as_float(row.get("deal_value_usd_b", ""), 0.0),
                "primary_source": row.get("primary_source", ""),
                "source_page": row.get("source_page", ""),
                "source_quality_score": _as_float(row.get("source_quality_score", ""), 0.65),
                "true_outcome_label": outcome_label,
                "true_close_label": deal_completed,
                "true_thesis_hit_label": _as_int(row.get("thesis_hit_label", "")),
                "true_abnormal_return_730d": _as_float(row.get("abnormal_return_730d", "")),
            },
            "evidence_items": evidence_items,
        }

        packets.append(packet)

    with out_path.open("w") as f:
        for packet in packets:
            f.write(json.dumps(packet, sort_keys=True) + "\n")

    print(f"wrote {out_path}")
    print(f"packets={len(packets)} skipped_unlabeled={skipped}")


if __name__ == "__main__":
    main()
