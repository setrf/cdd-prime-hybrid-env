# cdd-hybrid Environment

Prime-compatible Verifiers environment for hybrid CDD training/evaluation.

## Purpose

- Evaluate process quality across CDD workstreams.
- Evaluate outcome calibration against historical labels.

## Local Install

```bash
cd environments/cdd_hybrid
python3 -m pip install -e .
```

Prime CLI `env install` is for Hub IDs (`owner/name`), not local paths.

## Local Eval

```bash
prime eval run cdd-hybrid \
  -m gpt-4.1-mini \
  -n 8 \
  -a '{"dataset_path": "data/processed/train.jsonl", "eval_dataset_path": "data/processed/test.jsonl"}'
```

## Environment Arguments

- `dataset_path`: path to training JSONL packets
- `eval_dataset_path`: path to eval JSONL packets
- `num_examples`: optional train-subsample size for quick debugging
- `seed`: random seed for deterministic train subsampling

## Reward Components

- `format_reward`
- `coverage_reward`
- `evidence_citation_reward`
- `calibration_reward`
- `decision_alignment_reward`
- `consistency_reward`
