#!/usr/bin/env bash
set -euo pipefail

python3 scripts/build_outcomes.py
python3 scripts/build_packets.py
python3 scripts/split_dataset.py
python3 scripts/validate_dataset.py
python3 scripts/run_heuristic_baseline.py
python3 scripts/evaluate_predictions.py \
  --dataset data/processed/test.jsonl \
  --predictions data/interim/heuristic_predictions_test.jsonl
python3 scripts/run_memorization_probe.py --dataset data/processed/test.jsonl --dry-run
python3 -m unittest discover -s tests -p 'test_*.py'

echo "SMOKE PIPELINE COMPLETE"
