# CDD Hybrid Execution TODO

## Phase 1: Foundation
- [x] Define objective and target labels.
- [x] Define leakage policy and anti-memorization checks.
- [x] Define reward architecture (process + outcome).
- [x] Create repository structure aligned with Prime patterns.

## Phase 2: Data
- [x] Create seed historical-deal universe schema.
- [x] Implement automated outcome enrichment from public market data.
- [x] Implement abnormal return outcome labeling logic.
- [x] Build pre-deal prompt packets.
- [x] Implement train/val/test split by decision time.
- [x] Implement dataset schema and timestamp validation.

## Phase 3: Environment + Evaluation
- [x] Implement Prime-compatible environment module with `load_environment()`.
- [x] Implement core reward functions: format, coverage, evidence, calibration, decision utility.
- [x] Add contradiction penalty and parser utilities.
- [x] Implement heuristic baseline runner.
- [x] Implement prediction evaluator (Brier, log loss, accuracy, utility).
- [x] Implement memorization probe generator and optional online probe executor.

## Phase 4: Ops and Quality
- [x] Create eval/training config templates.
- [x] Create smoke pipeline script.
- [x] Add unit tests for metrics and leakage checks.
- [x] Run smoke pipeline end-to-end.
- [x] Run unit tests and fix failures.

## Phase 5: Scale-Up Backlog
- [x] Expand deal universe (200-1,000+ deals) with primary-source links.
- [x] Add richer textual evidence ingestion (SEC filings, calls, deck snippets).
- [x] Add model-based judge rubric with blinded outcome labels.
- [x] Add group reward functions and pass@k-style policy metrics.
- [x] Add CI contract tests against Prime API/OpenAPI updates.
