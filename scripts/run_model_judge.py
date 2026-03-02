#!/usr/bin/env python3
"""Score model completions with a blinded process-quality judge rubric."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "recommendation",
    "success_probability",
    "risk_flags",
    "workstream_findings",
    "evidence_citations",
    "thesis_summary",
}

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
    p = argparse.ArgumentParser(description="Run blinded model judge on prediction JSONL")
    p.add_argument("--dataset", default="data/processed/test.jsonl")
    p.add_argument("--predictions", required=True)
    p.add_argument("--output", default="data/interim/model_judge_results.jsonl")
    p.add_argument("--summary-output", default="data/interim/model_judge_summary.json")
    p.add_argument("--dry-run", action="store_true", help="Use local heuristic judge")
    p.add_argument("--max-rows", type=int, default=0)
    p.add_argument("--judge-model", default="qwen/qwen3-8b")
    p.add_argument("--api-base-url", default="https://api.pinference.ai/api/v1")
    p.add_argument("--api-key-var", default="PRIME_API_KEY")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=900)
    return p.parse_args()


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
        parsed = json.loads(t)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _chat(base_url: str, api_key: str, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; cdd-prime-judge/1.0)",
        },
    )
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
        except Exception:
            if i == 2:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError("unreachable")


def _heuristic_judge(parsed: dict[str, Any] | None, evidence_ids: set[str]) -> dict[str, Any]:
    if parsed is None:
        return {
            "process_score": 0.0,
            "format_score": 0.0,
            "coverage_score": 0.0,
            "citation_score": 0.0,
            "consistency_score": 0.0,
            "rationale": "Could not parse completion JSON.",
        }

    format_score = 1.0 if REQUIRED_KEYS.issubset(parsed.keys()) else 0.0

    findings = parsed.get("workstream_findings", {})
    coverage_score = 0.0
    if isinstance(findings, dict):
        coverage_score = len(set(findings.keys()) & WORKSTREAMS) / len(WORKSTREAMS)

    citations = parsed.get("evidence_citations", [])
    citation_score = 0.0
    if isinstance(citations, list) and citations:
        cited = {str(c) for c in citations}
        citation_score = len(cited & evidence_ids) / max(1, len(cited))

    consistency_score = 0.0
    try:
        p = float(parsed.get("success_probability"))
        rec = str(parsed.get("recommendation", "")).upper().strip()
        if rec == "GO" and p >= 0.5:
            consistency_score = 1.0
        elif rec == "NO_GO" and p < 0.5:
            consistency_score = 1.0
    except Exception:
        consistency_score = 0.0

    process_score = (
        0.30 * format_score
        + 0.30 * coverage_score
        + 0.25 * citation_score
        + 0.15 * consistency_score
    )
    return {
        "process_score": process_score,
        "format_score": format_score,
        "coverage_score": coverage_score,
        "citation_score": citation_score,
        "consistency_score": consistency_score,
        "rationale": "Heuristic blinded judge.",
    }


def _judge_prompt(packet: dict[str, Any], raw_completion: str) -> list[dict[str, str]]:
    evidence_ids = [str(e.get("evidence_id", "")) for e in packet.get("evidence_items", [])]
    user_prompt = {
        "instructions": (
            "Score the analyst answer only on process quality. "
            "Do not infer or use post-deal outcomes. Return strict JSON with keys: "
            "process_score, format_score, coverage_score, citation_score, consistency_score, rationale. "
            "All scores must be floats in [0,1]."
        ),
        "required_workstreams": sorted(WORKSTREAMS),
        "allowed_evidence_ids": evidence_ids,
        "analyst_response": raw_completion,
    }
    return [
        {
            "role": "system",
            "content": "You are a strict CDD process-quality judge.",
        },
        {
            "role": "user",
            "content": json.dumps(user_prompt, ensure_ascii=True),
        },
    ]


def load_dataset(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out[str(row["deal_id"])] = row
    return out


def main() -> None:
    args = parse_args()
    dataset = load_dataset(Path(args.dataset))

    api_key = ""
    if not args.dry_run:
        api_key = os.getenv(args.api_key_var, "")
        if not api_key:
            raise RuntimeError(f"missing {args.api_key_var}")

    results: list[dict[str, Any]] = []
    with Path(args.predictions).open() as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            if args.max_rows > 0 and len(results) >= args.max_rows:
                break

            pred = json.loads(line)
            deal_id = str(pred.get("deal_id", ""))
            packet = dataset.get(deal_id)
            if packet is None:
                continue

            raw_completion = str(pred.get("raw_completion", ""))
            parsed = pred.get("parsed")
            if not isinstance(parsed, dict):
                parsed = _extract_json(raw_completion)

            evidence_ids = {str(e.get("evidence_id", "")) for e in packet.get("evidence_items", [])}

            if args.dry_run:
                judge = _heuristic_judge(parsed, evidence_ids)
            else:
                judge_messages = _judge_prompt(packet, raw_completion)
                judge_raw = _chat(
                    base_url=args.api_base_url,
                    api_key=api_key,
                    model=args.judge_model,
                    messages=judge_messages,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                )
                judge = _extract_json(judge_raw) or _heuristic_judge(parsed, evidence_ids)
                judge["judge_raw"] = judge_raw

            out_row = {
                "deal_id": deal_id,
                "sample_idx": int(pred.get("sample_idx", 0)),
                "error_type": str(pred.get("error_type", "")),
                "judge": judge,
            }
            results.append(out_row)
            if i % 25 == 0:
                print(f"processed={i}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for row in results:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    process_scores = [float(r["judge"].get("process_score", 0.0)) for r in results]
    summary = {
        "n": len(results),
        "mean_process_score": (sum(process_scores) / len(process_scores)) if process_scores else 0.0,
        "predictions": str(args.predictions),
        "dataset": str(args.dataset),
        "dry_run": bool(args.dry_run),
    }
    Path(args.summary_output).write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {out_path}")
    print(f"wrote {args.summary_output}")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
