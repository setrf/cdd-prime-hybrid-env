#!/usr/bin/env python3
"""Time-based split for packet dataset."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split packets into train/val/test by decision date")
    parser.add_argument("--input", default="data/interim/deal_packets.jsonl")
    parser.add_argument("--train-end", default="2020-12-31")
    parser.add_argument("--val-end", default="2022-12-31")
    parser.add_argument("--output-dir", default="data/processed")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_end = date.fromisoformat(args.train_end)
    val_end = date.fromisoformat(args.val_end)
    if train_end > val_end:
        raise ValueError("train-end must be <= val-end")

    rows = load_jsonl(in_path)

    train, val, test = [], [], []
    for row in rows:
        d = date.fromisoformat(row["decision_date"])
        if d <= train_end:
            train.append(row)
        elif d <= val_end:
            val.append(row)
        else:
            test.append(row)

    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "val.jsonl", val)
    write_jsonl(out_dir / "test.jsonl", test)

    print(f"wrote {out_dir / 'train.jsonl'} ({len(train)} rows)")
    print(f"wrote {out_dir / 'val.jsonl'} ({len(val)} rows)")
    print(f"wrote {out_dir / 'test.jsonl'} ({len(test)} rows)")


if __name__ == "__main__":
    main()
