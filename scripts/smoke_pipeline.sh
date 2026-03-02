#!/usr/bin/env bash
set -euo pipefail

python3 scripts/check_prime_openapi_contract.py
python3 scripts/build_outcomes.py
python3 scripts/enrich_text_evidence.py --input data/interim/deals_enriched.csv --output data/interim/text_evidence.jsonl --max-deals 12 --max-unique-urls 0
python3 scripts/build_packets.py
python3 scripts/split_dataset.py
python3 scripts/validate_dataset.py
python3 scripts/run_heuristic_baseline.py
python3 scripts/evaluate_predictions.py \
  --dataset data/processed/test.jsonl \
  --predictions data/interim/heuristic_predictions_test.jsonl
python3 scripts/check_regression_thresholds.py
python3 scripts/evaluate_group_policy.py --dataset data/processed/test.jsonl --predictions data/interim/heuristic_predictions_test.jsonl --k-values 1 --output data/interim/group_metrics.json
python3 scripts/run_memorization_probe.py --dataset data/processed/test.jsonl --dry-run
python3 -m unittest discover -s tests -p 'test_*.py'

echo "SMOKE PIPELINE COMPLETE"
