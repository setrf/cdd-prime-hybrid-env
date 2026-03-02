.PHONY: toolchain openapi data smoke test matrix group judge ci

toolchain:
	python3 scripts/check_toolchain.py

openapi:
	python3 scripts/check_prime_openapi_contract.py

data:
	python3 scripts/expand_deals_from_wikipedia.py
	python3 scripts/merge_deal_sources.py
	python3 scripts/build_outcomes.py --input data/raw/deals_master.csv --output data/interim/deals_enriched.csv
	python3 scripts/enrich_text_evidence.py --input data/interim/deals_enriched.csv --output data/interim/text_evidence.jsonl --max-deals 400 --max-unique-urls 150
	python3 scripts/build_packets.py
	python3 scripts/split_dataset.py
	python3 scripts/validate_dataset.py

smoke:
	./scripts/smoke_pipeline.sh

test:
	python3 -m unittest discover -s tests -p 'test_*.py'

matrix:
	python3 scripts/run_model_matrix.py --dataset data/processed/test.jsonl --limit 24

group:
	python3 scripts/evaluate_group_policy.py --dataset data/processed/test.jsonl --predictions data/interim/heuristic_predictions_test.jsonl --k-values 1 --output data/interim/group_metrics.json

judge:
	python3 scripts/run_model_judge.py --dataset data/processed/test.jsonl --predictions data/interim/model_matrix/qwen-qwen3-8b.jsonl --dry-run --output data/interim/model_judge_results.jsonl --summary-output data/interim/model_judge_summary.json

ci: toolchain openapi smoke test
