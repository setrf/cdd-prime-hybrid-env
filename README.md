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

1. Validate toolchain and Prime OpenAPI contracts (`scripts/check_toolchain.py`, `scripts/check_prime_openapi_contract.py`).
2. Build a historical deal universe (`scripts/expand_deals_from_wikipedia.py`, `scripts/merge_deal_sources.py`).
3. Enrich with realized outcomes using market data (`scripts/build_outcomes.py`).
4. Ingest richer text evidence snippets (`scripts/enrich_text_evidence.py`).
5. Build pre-deal-only packets and prompts (`scripts/build_packets.py`).
6. Split and validate (`scripts/split_dataset.py`, `scripts/validate_dataset.py`).
7. Run baseline and evaluate (`scripts/run_heuristic_baseline.py`, `scripts/evaluate_predictions.py`, `scripts/evaluate_group_policy.py`).
8. Run memorization probes and judge scoring (`scripts/run_memorization_probe.py`, `scripts/run_model_judge.py`).
9. Use `environments/cdd_hybrid/` with `prime env install` + `prime eval run`.

## Quick Start (Local Smoke)

```bash
set -a; source .env.local; set +a
./scripts/smoke_pipeline.sh
```

## Full Pipeline (200+ Deals)

```bash
set -a; source .env.local; set +a
./scripts/full_pipeline.sh
```

This runs:
- Toolchain lock checks
- Prime OpenAPI contract checks
- Wikipedia expansion + source merge
- Outcome enrichment + rich text evidence ingestion + packetization
- Split + leakage validation + baseline metrics + group metrics + regression gate + tests

## Toolchain Lock

Pinned versions are in `toolchain.lock.toml`.

Validate:

```bash
python3 scripts/check_toolchain.py
```

## Prime Integration

- Environment source: `environments/cdd_hybrid/cdd_hybrid.py`
- Environment package metadata: `environments/cdd_hybrid/pyproject.toml`
- Eval config template: `configs/eval/cdd_hybrid.toml`
- Prime-RL config template: `configs/prime-rl/cdd_hybrid.toml`

### Live Eval (Current CLI Stack)

On the currently installed stack (`prime` 0.4.x + `verifiers` 0.1.5), local evaluation is run with `vf-eval`:

```bash
PRIME_API_KEY=... vf-eval cdd_hybrid \
  -m qwen/qwen3-235b-a22b-instruct-2507 \
  -b https://api.pinference.ai/api/v1 \
  -k PRIME_API_KEY \
  -n 2 -r 1 \
  -a '{"dataset_path":"data/processed/train.jsonl","eval_dataset_path":"data/processed/test.jsonl"}' \
  -s
```

## Baseline Matrix and Seed Experiments

Small-model matrix benchmark:

```bash
set -a; source .env.local; set +a
python3 scripts/run_model_matrix.py --dataset data/processed/test.jsonl --limit 24
```

Outputs:
- `data/interim/model_matrix/benchmark_report.md`
- `data/interim/model_matrix/benchmark_summary.json`
- Tracked copies: `reports/benchmark_report.md`, `reports/benchmark_summary.json`

Optional multi-sample pass@k run:

```bash
set -a; source .env.local; set +a
python3 scripts/run_model_matrix.py \
  --dataset data/processed/test.jsonl \
  --models qwen/qwen3-8b \
  --limit 12 \
  --samples-per-deal 3 \
  --temperature 0.1 \
  --out-dir data/interim/model_matrix_passk
```

Three-seed short optimization experiments:

```bash
set -a; source .env.local; set +a
python3 scripts/run_seed_optimization.py --dataset data/processed/train.jsonl --eval-dataset data/processed/test.jsonl
```

Outputs:
- `data/interim/seed_optimization/seed_results.json`
- `data/interim/seed_optimization/seed_summary.json`
- Tracked copy: `reports/seed_summary.json`

## Judge + Group Metrics

Blinded process-quality judge (dry-run heuristic or online model judge):

```bash
python3 scripts/run_model_judge.py \
  --dataset data/processed/test.jsonl \
  --predictions data/interim/model_matrix/qwen-qwen3-8b.jsonl \
  --dry-run \
  --output data/interim/model_judge_results.jsonl \
  --summary-output reports/model_judge_summary.json
```

Group metrics from multi-sample predictions:

```bash
python3 scripts/evaluate_group_policy.py \
  --dataset data/processed/test.jsonl \
  --predictions data/interim/heuristic_predictions_test.jsonl \
  --k-values 1 \
  --output data/interim/group_metrics.json
cp data/interim/group_metrics.json reports/group_metrics.json
```

## Comments

- The current dataset is expanded from public acquisition list pages plus a curated seed set.
- Time-split evaluation and leakage checks are enforced to reduce label contamination risk.
- Memorization probing is included and can be run in `--dry-run` or online mode.
- Judge rubric scoring is blinded to realized outcomes by design.

## Notes

- Public-source extraction quality depends on citation availability and page structure.
- For production, enrich evidence from issuer filings/transcripts and internal data room documents.
- Reward design is modular; adjust weights and thresholds for your IC loss function.
