# Model Matrix Benchmark

| Model | N | Brier | LogLoss | Accuracy | Utility | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| qwen/qwen3-8b | 12 | 0.2527 | 0.7030 | 0.7500 | 0.2083 | 1.0000 |
| meta-llama/Llama-3.2-1B-Instruct | 12 | 0.3367 | 9.2289 | 0.6667 | 0.0417 | 0.0833 |
| meta-llama/Llama-3.2-3B-Instruct | 12 | 0.2923 | 0.8142 | 0.5000 | -0.2917 | 1.0000 |
| openai/gpt-4.1-mini | 12 | 0.3659 | 0.9613 | 0.4167 | -0.4583 | 1.0000 |
| google/gemma-3-27b-it | 12 | 0.4277 | 1.0955 | 0.2500 | -0.7917 | 1.0000 |

## Error Taxonomy

### qwen/qwen3-8b
- correct: 7
- false_positive: 3
- recommendation_probability_conflict: 2
### meta-llama/Llama-3.2-1B-Instruct
- parse_error: 7
- missing_fields: 4
- correct: 1
### meta-llama/Llama-3.2-3B-Instruct
- correct: 5
- recommendation_probability_conflict: 3
- false_negative: 2
- false_positive: 2
### openai/gpt-4.1-mini
- false_positive: 7
- correct: 5
### google/gemma-3-27b-it
- false_negative: 5
- false_positive: 4
- correct: 3