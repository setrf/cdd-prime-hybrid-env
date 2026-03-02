#!/usr/bin/env python3
"""Run small-model baseline matrix on CDD packets."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.metrics import accuracy, brier_score, decision_utility, log_loss
from cdd_prime.group_metrics import majority_vote_utility, pass_at_k


DEFAULT_MODELS = [
    "meta-llama/Llama-3.2-1B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "qwen/qwen3-8b",
    "google/gemma-3-27b-it",
    "openai/gpt-4.1-mini",
]

WORKSTREAMS = {
    "market_growth",
    "customer_demand",
    "competitive_position",
    "pricing_power",
    "gtm_execution",
    "operational_feasibility",
    "regulatory_risk",
    "integration_risk",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run model matrix benchmark")
    p.add_argument("--dataset", default="data/processed/test.jsonl")
    p.add_argument("--api-base-url", default="https://api.pinference.ai/api/v1")
    p.add_argument("--api-key-var", default="PRIME_API_KEY")
    p.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    p.add_argument("--limit", type=int, default=24)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=1400)
    p.add_argument("--samples-per-deal", type=int, default=1)
    p.add_argument("--out-dir", default="data/interim/model_matrix")
    return p.parse_args()


def load_rows(path: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    rows.sort(key=lambda r: r["deal_id"])
    if limit > 0:
        rows = rows[:limit]
    return rows


def _slug(x: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", x).strip("-").lower()


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


def _answer_label(answer: Any) -> int:
    if isinstance(answer, str):
        obj = json.loads(answer)
    elif isinstance(answer, dict):
        obj = answer
    else:
        raise ValueError("unsupported answer type")
    return int(obj["outcome_label"])


def _chat(base_url: str, api_key: str, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        url=base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; cdd-prime-matrix/1.0)",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="ignore")[:400]
            if attempt == 2:
                raise RuntimeError(f"HTTPError {e.code}: {text}") from e
            time.sleep(2 * (attempt + 1))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable")


def classify_error(parsed: dict[str, Any] | None, true_label: int) -> tuple[str, int | None, float | None, float]:
    if parsed is None:
        return "parse_error", None, None, 0.0

    required = {"recommendation", "success_probability", "risk_flags", "workstream_findings", "evidence_citations", "thesis_summary"}
    if not required.issubset(parsed.keys()):
        return "missing_fields", None, None, 0.0

    try:
        p = float(parsed.get("success_probability"))
    except Exception:
        return "prob_parse_error", None, None, 0.0
    if not (0.0 <= p <= 1.0):
        return "prob_out_of_range", None, p, 0.0

    rec = str(parsed.get("recommendation", "")).upper().strip()
    if rec == "GO":
        pred = 1
    elif rec == "NO_GO":
        pred = 0
    else:
        return "invalid_recommendation", None, p, 0.0

    findings = parsed.get("workstream_findings", {})
    coverage = 0.0
    if isinstance(findings, dict):
        coverage = len(set(findings.keys()) & WORKSTREAMS) / len(WORKSTREAMS)

    if pred != (1 if p >= 0.5 else 0):
        return "recommendation_probability_conflict", pred, p, coverage

    if pred == 1 and true_label == 0:
        return "false_positive", pred, p, coverage
    if pred == 0 and true_label == 1:
        return "false_negative", pred, p, coverage
    return "correct", pred, p, coverage


def evaluate_model(
    model: str,
    rows: list[dict[str, Any]],
    base_url: str,
    api_key: str,
    temperature: float,
    max_tokens: int,
    samples_per_deal: int,
    out_dir: Path,
) -> dict[str, Any]:
    preds: list[dict[str, Any]] = []
    probs: list[float] = []
    labels: list[int] = []
    pred_labels: list[int] = []
    coverage_values: list[float] = []
    errors = Counter()

    for i, row in enumerate(rows, start=1):
        true_label = _answer_label(row["answer"])
        for sample_idx in range(samples_per_deal):
            completion = _chat(base_url, api_key, model, row["prompt"], temperature, max_tokens)
            parsed = _extract_json(completion)
            error_type, pred_label, prob, coverage = classify_error(parsed, true_label)

            errors[error_type] += 1
            coverage_values.append(coverage)

            if pred_label is None or prob is None:
                # Penalize invalid outputs strongly in metrics.
                pred_label = 0
                prob = 0.0

            preds.append(
                {
                    "deal_id": row["deal_id"],
                    "sample_idx": sample_idx,
                    "true_label": true_label,
                    "predicted_label": pred_label,
                    "success_probability": prob,
                    "error_type": error_type,
                    "coverage": coverage,
                    "parsed": parsed,
                    "raw_completion": completion,
                }
            )

            probs.append(prob)
            labels.append(true_label)
            pred_labels.append(pred_label)

        if i % 10 == 0:
            print(f"model={model} progress={i}/{len(rows)}")

    out_path = out_dir / f"{_slug(model)}.jsonl"
    with out_path.open("w") as f:
        for p in preds:
            f.write(json.dumps(p, sort_keys=True) + "\n")

    # Group metrics over per-deal top-k samples.
    by_deal: dict[str, list[tuple[int, int]]] = {}
    label_by_deal: dict[str, int] = {}
    for p in preds:
        deal_id = str(p["deal_id"])
        by_deal.setdefault(deal_id, []).append((int(p["sample_idx"]), int(p["predicted_label"])))
        label_by_deal[deal_id] = int(p["true_label"])
    grouped = []
    grouped_labels = []
    for deal_id in sorted(by_deal.keys()):
        sorted_preds = [v for _, v in sorted(by_deal[deal_id], key=lambda x: x[0])]
        grouped.append(sorted_preds)
        grouped_labels.append(label_by_deal[deal_id])

    group_metrics: list[dict[str, float]] = []
    for k in range(1, samples_per_deal + 1):
        group_metrics.append(
            {
                "k": float(k),
                "pass_at_k": pass_at_k(grouped, grouped_labels, k=k),
                "majority_vote_utility": majority_vote_utility(grouped, grouped_labels, k=k, tie_breaker=0),
            }
        )

    summary = {
        "model": model,
        "n_deals": len(rows),
        "n_predictions": len(preds),
        "samples_per_deal": samples_per_deal,
        "brier_score": brier_score(probs, labels),
        "log_loss": log_loss(probs, labels),
        "accuracy": accuracy(pred_labels, labels),
        "decision_utility": decision_utility(pred_labels, labels),
        "mean_workstream_coverage": sum(coverage_values) / len(coverage_values) if coverage_values else 0.0,
        "error_taxonomy": dict(errors),
        "group_metrics": group_metrics,
        "predictions_path": str(out_path),
    }
    return summary


def write_report(summaries: list[dict[str, Any]], out_dir: Path) -> None:
    summaries_sorted = sorted(summaries, key=lambda s: (s["decision_utility"], -s["brier_score"]), reverse=True)

    md_lines = [
        "# Model Matrix Benchmark",
        "",
        "| Model | Deals | Preds | Brier | LogLoss | Accuracy | Utility | Coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries_sorted:
        md_lines.append(
            f"| {s['model']} | {s['n_deals']} | {s['n_predictions']} | {s['brier_score']:.4f} | {s['log_loss']:.4f} | "
            f"{s['accuracy']:.4f} | {s['decision_utility']:.4f} | {s['mean_workstream_coverage']:.4f} |"
        )

    md_lines.append("\n## Error Taxonomy\n")
    for s in summaries_sorted:
        md_lines.append(f"### {s['model']}")
        for k, v in sorted(s["error_taxonomy"].items(), key=lambda kv: kv[1], reverse=True):
            md_lines.append(f"- {k}: {v}")

    md_lines.append("\n## Group Metrics\n")
    for s in summaries_sorted:
        md_lines.append(f"### {s['model']}")
        for gm in s.get("group_metrics", []):
            md_lines.append(
                f"- k={int(gm['k'])}: pass@k={gm['pass_at_k']:.4f}, majority_vote_utility={gm['majority_vote_utility']:.4f}"
            )

    (out_dir / "benchmark_report.md").write_text("\n".join(md_lines))
    (out_dir / "benchmark_summary.json").write_text(json.dumps(summaries_sorted, indent=2, sort_keys=True))


def main() -> None:
    args = parse_args()
    api_key = os.getenv(args.api_key_var, "")
    if not api_key:
        raise RuntimeError(f"missing {args.api_key_var}")

    rows = load_rows(Path(args.dataset), args.limit)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []
    for model in args.models:
        print(f"running model={model} n={len(rows)}")
        summary = evaluate_model(
            model=model,
            rows=rows,
            base_url=args.api_base_url,
            api_key=api_key,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            samples_per_deal=args.samples_per_deal,
            out_dir=out_dir,
        )
        summaries.append(summary)
        print(json.dumps(summary, indent=2, sort_keys=True))

    write_report(summaries, out_dir)
    print(f"wrote {out_dir / 'benchmark_report.md'}")
    print(f"wrote {out_dir / 'benchmark_summary.json'}")


if __name__ == "__main__":
    main()
