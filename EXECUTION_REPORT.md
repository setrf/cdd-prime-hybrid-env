# Execution Report: CDD Hybrid RL Environment (Full Build)

## Scope Executed

Implemented and validated end-to-end roadmap items:

- Toolchain locking + verification (`toolchain.lock.toml`, `scripts/check_toolchain.py`)
- Prime OpenAPI contract checks (`scripts/check_prime_openapi_contract.py`)
- 200+ deal expansion with citation-backed ingestion (`scripts/expand_deals_from_wikipedia.py`)
- Source merge with curated seed deals (`scripts/merge_deal_sources.py`)
- Multi-target outcome enrichment (`scripts/build_outcomes.py`)
- Rich text-evidence ingestion for filings/calls/decks/press snippets (`scripts/enrich_text_evidence.py`)
- Packet/evidence generation with quality metadata (`scripts/build_packets.py`)
- Time split + schema/leakage validation (`scripts/split_dataset.py`, `scripts/validate_dataset.py`)
- Stronger reward stack (risk-weighted calibration, citation validity, contradiction penalty)
- Small-model live matrix benchmark (`scripts/run_model_matrix.py`)
- 3-seed short optimization experiments (`scripts/run_seed_optimization.py`)
- Group metrics and pass@k evaluation (`scripts/evaluate_group_policy.py`, `src/cdd_prime/group_metrics.py`)
- Blinded model-judge rubric (`scripts/run_model_judge.py`)
- CI gates + threshold checks (`.github/workflows/ci.yml`, `scripts/check_regression_thresholds.py`)

## Data Build Results

- Expanded rows from Wikipedia acquisition lists: `841`
- Merged master rows (expanded + curated): `859`
- Labeled rows after outcome enrichment: `549`
- Split:
  - train: `487`
  - val: `50`
  - test: `12`

## Baseline Quality Gate (Heuristic)

- Accuracy: `0.7500`
- Brier: `0.2227`
- Log loss: `0.6381`
- Decision utility: `0.2083`
- Regression gate: passed
- Group metric (k=1) pass@k: `0.7500`

## Live Small-Model Matrix (Prime Inference)

Executed against 12 test deals. Summary is in:
- `reports/benchmark_report.md`
- `reports/benchmark_summary.json`

Top-by-utility from this run:
1. `qwen/qwen3-8b` (utility `0.2083`)
2. `meta-llama/Llama-3.2-1B-Instruct` (utility `0.0417`)
3. `meta-llama/Llama-3.2-3B-Instruct` (utility `-0.2917`)

## 3-Seed Short Optimization (RL-Style Prompt Policy)

Executed with seeds `1, 7, 42` using `qwen/qwen3-8b`.

Summary (`reports/seed_summary.json`):
- mean_eval_utility: `-0.2917`
- mean_eval_accuracy: `0.5000`
- stability_pass: `true`
- scale_recommendation: `tune_then_scale`

Interpretation:
- Stability across seeds is acceptable for this short run.
- Policy quality is not yet strong enough for scaling; next step is tuning reward weights and evidence richness.

## Blinded Judge Result

Dry-run judge summary (`reports/model_judge_summary.json`):
- n: `12`
- mean_process_score: `0.7250`

## Verification Status

- Toolchain check: passed
- OpenAPI contract check: passed
- Full pipeline: passed
- Unit tests: passed (`11/11`)
- Compile checks: passed
- Live API benchmark runs: completed

## Security Handling

- API key stored in local `.env.local` (ignored by git)
- `.env.example` tracked for template-only usage
