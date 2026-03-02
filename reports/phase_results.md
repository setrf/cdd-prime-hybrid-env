# Phase Results

## Data Build
- deals_master_rows: 859
- labeled_packets: 549

## Baseline (Heuristic)
- n: 12
- accuracy: 0.75
- brier_score: 0.22274835416666672
- log_loss: 0.6380678146297439
- decision_utility: 0.20833333333333334
- pass_at_k@1: 0.75
- majority_vote_utility@1: 0.20833333333333334

## Small Model Matrix (Top by utility)
1. qwen/qwen3-8b | utility=0.2083 | brier=0.2527 | acc=0.7500
2. meta-llama/Llama-3.2-1B-Instruct | utility=0.0417 | brier=0.3367 | acc=0.6667
3. meta-llama/Llama-3.2-3B-Instruct | utility=-0.2917 | brier=0.2923 | acc=0.5000

## 3-Seed Optimization Summary
- max_eval_utility: -0.125
- mean_eval_accuracy: 0.5
- mean_eval_utility: -0.2916666666666667
- min_eval_utility: -0.4583333333333333
- model: qwen/qwen3-8b
- scale_recommendation: tune_then_scale
- seeds: [1, 7, 42]
- stability_pass: True

## Blinded Judge Summary
- n: 12
- mean_process_score: 0.725
- dry_run: True
