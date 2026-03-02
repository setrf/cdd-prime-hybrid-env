#!/usr/bin/env python3
"""Run short 3-seed prompt-policy optimization experiments.

This is a lightweight RL-style bandit optimization over system-prompt variants,
used as a practical seed-stability check when full model finetuning infra is unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import time
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run 3-seed short optimization experiments")
    p.add_argument("--dataset", default="data/processed/train.jsonl")
    p.add_argument("--eval-dataset", default="data/processed/test.jsonl")
    p.add_argument("--api-base-url", default="https://api.pinference.ai/api/v1")
    p.add_argument("--api-key-var", default="PRIME_API_KEY")
    p.add_argument("--model", default="qwen/qwen3-8b")
    p.add_argument("--seeds", default="1,7,42")
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=1200)
    p.add_argument("--out-dir", default="data/interim/seed_optimization")
    return p.parse_args()


PROMPT_VARIANTS = [
    "Focus on downside protection and reject unsupported optimism.",
    "Prioritize regulatory and integration risk as first-class constraints.",
    "Use conservative probabilities unless evidence quality is high.",
    "Emphasize valuation discipline and premium justification.",
    "Reward clear contradiction handling and explicit uncertainty.",
    "Prefer NO_GO when critical evidence is missing or low-confidence.",
]


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _extract_json(text: str) -> dict[str, Any] | None:
    t = text.strip()
    if not t:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, flags=re.S)
    if fence:
        t = fence.group(1)
    if not t.startswith("{"):
        m = re.search(r"\{.*\}", t, flags=re.S)
        if not m:
            return None
        t = m.group(0)
    try:
        v = json.loads(t)
    except json.JSONDecodeError:
        return None
    return v if isinstance(v, dict) else None


def _true_label(answer: Any) -> int:
    obj = json.loads(answer) if isinstance(answer, str) else answer
    return int(obj["outcome_label"])


def _chat(base_url: str, api_key: str, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; cdd-prime-seed-opt/1.0)",
        },
    )
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except Exception:
            if k == 2:
                raise
            time.sleep(2 * (k + 1))
    raise RuntimeError("unreachable")


def _score_completion(parsed: dict[str, Any] | None, true_label: int) -> tuple[float, int, float]:
    # Returns reward, pred_label, prob
    if parsed is None:
        return 0.0, 0, 0.0

    needed = {"recommendation", "success_probability", "risk_flags", "workstream_findings", "evidence_citations", "thesis_summary"}
    if not needed.issubset(parsed.keys()):
        return 0.05, 0, 0.0

    try:
        p = float(parsed.get("success_probability"))
    except Exception:
        return 0.05, 0, 0.0
    if not (0.0 <= p <= 1.0):
        return 0.05, 0, 0.0

    rec = str(parsed.get("recommendation", "")).upper().strip()
    pred = 1 if rec == "GO" else 0 if rec == "NO_GO" else (1 if p >= 0.5 else 0)

    format_score = 1.0
    calibration = 1.0 - (p - true_label) ** 2
    decision = 1.0 if pred == true_label else 0.0

    reward = 0.4 * format_score + 0.3 * calibration + 0.3 * decision
    return reward, pred, p


def softmax(xs: list[float]) -> list[float]:
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps)
    return [e / s for e in exps]


def sample_index(probs: list[float], rng: random.Random) -> int:
    r = rng.random()
    c = 0.0
    for i, p in enumerate(probs):
        c += p
        if r <= c:
            return i
    return len(probs) - 1


def run_seed(
    seed: int,
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    base_url: str,
    api_key: str,
    model: str,
    steps: int,
    batch_size: int,
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    logits = [0.0 for _ in PROMPT_VARIANTS]
    lr = 0.8
    trace: list[dict[str, Any]] = []

    for step in range(1, steps + 1):
        probs = softmax(logits)
        idx = sample_index(probs, rng)
        variant = PROMPT_VARIANTS[idx]

        batch = rng.sample(train_rows, k=min(batch_size, len(train_rows)))
        rewards = []
        for row in batch:
            prompt = list(row["prompt"])
            prompt[0] = {
                "role": "system",
                "content": str(prompt[0]["content"]) + "\nAdditional policy: " + variant,
            }
            completion = _chat(base_url, api_key, model, prompt, temperature, max_tokens)
            parsed = _extract_json(completion)
            y = _true_label(row["answer"])
            reward, _, _ = _score_completion(parsed, y)
            rewards.append(reward)

        avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
        baseline = sum(trace_i["avg_reward"] for trace_i in trace) / len(trace) if trace else 0.5
        advantage = avg_reward - baseline
        logits[idx] += lr * advantage

        trace.append(
            {
                "step": step,
                "variant_index": idx,
                "variant": variant,
                "avg_reward": avg_reward,
                "advantage": advantage,
                "policy_probs": probs,
            }
        )

    best_idx = max(range(len(logits)), key=lambda i: logits[i])
    best_variant = PROMPT_VARIANTS[best_idx]

    # Final evaluation on holdout.
    eval_rewards = []
    eval_preds = []
    eval_probs = []
    eval_labels = []
    for row in eval_rows:
        prompt = list(row["prompt"])
        prompt[0] = {
            "role": "system",
            "content": str(prompt[0]["content"]) + "\nAdditional policy: " + best_variant,
        }
        completion = _chat(base_url, api_key, model, prompt, temperature, max_tokens)
        parsed = _extract_json(completion)
        y = _true_label(row["answer"])
        reward, pred, prob = _score_completion(parsed, y)
        eval_rewards.append(reward)
        eval_preds.append(pred)
        eval_probs.append(prob)
        eval_labels.append(y)

    utility = 0.0
    for p, y in zip(eval_preds, eval_labels):
        if p == 1 and y == 1:
            utility += 1.0
        elif p == 0 and y == 0:
            utility += 0.5
        elif p == 1 and y == 0:
            utility += -1.5
        else:
            utility += -1.0
    utility /= len(eval_labels) if eval_labels else 1.0

    result = {
        "seed": seed,
        "best_variant_index": best_idx,
        "best_variant": best_variant,
        "trace": trace,
        "eval_mean_reward": sum(eval_rewards) / len(eval_rewards) if eval_rewards else 0.0,
        "eval_accuracy": sum(1 for p, y in zip(eval_preds, eval_labels) if p == y) / len(eval_labels) if eval_labels else 0.0,
        "eval_utility": utility,
    }
    return result


def main() -> None:
    args = parse_args()
    api_key = os.getenv(args.api_key_var, "")
    if not api_key:
        raise RuntimeError(f"missing {args.api_key_var}")

    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    train_rows = load_rows(Path(args.dataset))
    eval_rows = load_rows(Path(args.eval_dataset))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for seed in seeds:
        print(f"running seed={seed}")
        res = run_seed(
            seed=seed,
            train_rows=train_rows,
            eval_rows=eval_rows,
            base_url=args.api_base_url,
            api_key=api_key,
            model=args.model,
            steps=args.steps,
            batch_size=args.batch_size,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        results.append(res)
        print(json.dumps({k: v for k, v in res.items() if k != "trace"}, indent=2, sort_keys=True))

    utils = [r["eval_utility"] for r in results]
    accs = [r["eval_accuracy"] for r in results]
    summary = {
        "model": args.model,
        "seeds": seeds,
        "mean_eval_utility": sum(utils) / len(utils) if utils else 0.0,
        "mean_eval_accuracy": sum(accs) / len(accs) if accs else 0.0,
        "min_eval_utility": min(utils) if utils else 0.0,
        "max_eval_utility": max(utils) if utils else 0.0,
        "stability_pass": (max(utils) - min(utils) <= 0.35) if utils else False,
        "scale_recommendation": "scale_up" if utils and (sum(utils) / len(utils) > 0.0 and max(utils) - min(utils) <= 0.35) else "tune_then_scale",
    }

    (out_dir / "seed_results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
    (out_dir / "seed_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
