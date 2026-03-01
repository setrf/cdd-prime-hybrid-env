#!/usr/bin/env python3
"""Validate dataset schema and leakage guards."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.leakage import check_prompt_for_outcome_leaks, check_timestamp_leakage
from cdd_prime.schema import validate_packet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one or more packet JSONL files")
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=["data/processed/train.jsonl", "data/processed/val.jsonl", "data/processed/test.jsonl"],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    total_rows = 0
    errors: list[str] = []

    for in_file in args.inputs:
        path = Path(in_file)
        if not path.exists():
            errors.append(f"missing input file: {path}")
            continue

        seen_ids: set[str] = set()
        with path.open() as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                total_rows += 1
                row = json.loads(line)
                packet_errors = validate_packet(row)
                if packet_errors:
                    for e in packet_errors:
                        errors.append(f"{path}:{idx}: {e}")

                ts_issues = check_timestamp_leakage(row)
                for issue in ts_issues:
                    errors.append(f"{path}:{idx}: timestamp_leak: {issue}")

                outcome_issues = check_prompt_for_outcome_leaks(row)
                for issue in outcome_issues:
                    errors.append(f"{path}:{idx}: prompt_leak: {issue}")

                deal_id = str(row.get("deal_id"))
                if deal_id in seen_ids:
                    errors.append(f"{path}:{idx}: duplicate deal_id within file: {deal_id}")
                seen_ids.add(deal_id)

    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print(f"VALIDATION PASSED: rows={total_rows} files={len(args.inputs)}")


if __name__ == "__main__":
    main()
