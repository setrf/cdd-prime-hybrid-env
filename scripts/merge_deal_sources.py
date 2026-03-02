#!/usr/bin/env python3
"""Merge expanded wikipedia deals with curated seed deals."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge deal source CSV files")
    p.add_argument("--seed", default="data/raw/deals_seed.csv")
    p.add_argument("--expanded", default="data/raw/deals_expanded.csv")
    p.add_argument("--output", default="data/raw/deals_master.csv")
    return p.parse_args()


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("acquirer_ticker", "").upper(),
        row.get("target", "").strip().lower(),
        row.get("decision_date", ""),
    )


def main() -> None:
    args = parse_args()
    seed_rows = list(csv.DictReader(Path(args.seed).open()))
    exp_rows = list(csv.DictReader(Path(args.expanded).open()))

    out: dict[tuple[str, str, str], dict[str, str]] = {}

    for row in exp_rows:
        out[key(row)] = row

    # Prefer curated seed row on collision.
    for row in seed_rows:
        out[key(row)] = row

    rows = list(out.values())
    rows.sort(key=lambda r: (r.get("decision_date", ""), r.get("acquirer_ticker", ""), r.get("target", "").lower()))

    # superset fieldnames
    fieldnames: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"wrote {output}")
    print(f"seed_rows={len(seed_rows)} expanded_rows={len(exp_rows)} merged_rows={len(rows)}")


if __name__ == "__main__":
    main()
