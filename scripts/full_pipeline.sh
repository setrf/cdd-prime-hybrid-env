#!/usr/bin/env bash
set -euo pipefail

python3 scripts/check_toolchain.py
python3 scripts/check_prime_openapi_contract.py
python3 scripts/expand_deals_from_wikipedia.py --output data/raw/deals_expanded.csv
python3 scripts/merge_deal_sources.py --output data/raw/deals_master.csv
python3 scripts/build_outcomes.py --input data/raw/deals_master.csv --output data/interim/deals_enriched.csv
python3 scripts/enrich_text_evidence.py --input data/interim/deals_enriched.csv --output data/interim/text_evidence.jsonl --max-deals 400 --max-unique-urls 150
python3 scripts/build_packets.py
python3 scripts/split_dataset.py
python3 scripts/validate_dataset.py
python3 scripts/run_heuristic_baseline.py --dataset data/processed/test.jsonl --output data/interim/heuristic_predictions_test.jsonl
python3 scripts/evaluate_predictions.py --dataset data/processed/test.jsonl --predictions data/interim/heuristic_predictions_test.jsonl
python3 scripts/check_regression_thresholds.py
python3 scripts/evaluate_group_policy.py --dataset data/processed/test.jsonl --predictions data/interim/heuristic_predictions_test.jsonl --k-values 1 --output data/interim/group_metrics.json
python3 -m unittest discover -s tests -p 'test_*.py'

echo "FULL PIPELINE COMPLETE"
