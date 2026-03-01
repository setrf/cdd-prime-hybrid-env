# CDD Hybrid RL Environment on Prime Intellect

This workspace implements a production-oriented starter for a **hybrid Commercial Due Diligence (CDD) RL environment** using Prime Intellect patterns:

- Environment package under `environments/cdd_hybrid/`
- Data pipeline under `scripts/`
- Core validation and metrics under `src/cdd_prime/`
- Reproducible configs under `configs/`
- Tests under `tests/`

## About

This project provides a practical foundation for training and evaluating LLM agents on CDD-style reasoning with strict anti-leakage controls and measurable decision quality. It is designed for Prime Intellect workflows (`verifiers`, `prime eval`, and `prime-rl`) while staying runnable locally.

## Objective

Train/evaluate models to perform CDD-like reasoning with two reward families:

1. **Process quality**: workstream coverage, evidence usage, internal consistency, output format quality.
2. **Outcome quality**: calibrated probability prediction and decision utility against realized outcomes.

## Implemented Hybrid Flow

1. Build a historical deal universe (`data/raw/deals_seed.csv`).
2. Enrich with realized outcomes using market data (`scripts/build_outcomes.py`).
3. Build pre-deal-only packets and prompts (`scripts/build_packets.py`).
4. Split and validate (`scripts/split_dataset.py`, `scripts/validate_dataset.py`).
5. Run baseline and evaluate (`scripts/run_heuristic_baseline.py`, `scripts/evaluate_predictions.py`).
6. Run memorization probes (`scripts/run_memorization_probe.py`).
7. Use `environments/cdd_hybrid/` with `prime env install` + `prime eval run`.

## Quick Start (Local Smoke)

```bash
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
```

## Prime Integration

- Environment source: `environments/cdd_hybrid/cdd_hybrid.py`
- Environment package metadata: `environments/cdd_hybrid/pyproject.toml`
- Eval config template: `configs/eval/cdd_hybrid.toml`
- Prime-RL config template: `configs/prime-rl/cdd_hybrid.toml`

## Comments

- The current dataset is a seed set intended for pipeline validation and should be expanded for real benchmarking.
- Time-split evaluation and leakage checks are enforced to reduce label contamination risk.
- Memorization probing is included and can be run in `--dry-run` or online mode.

## Notes

- Seed deal data is intentionally compact and should be expanded.
- Some deal dates/fields should be verified against primary filings before production use.
- Reward design is modular; adjust weights and thresholds for your IC loss function.
