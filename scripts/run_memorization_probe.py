#!/usr/bin/env python3
"""Generate or execute memorization probes for deal-outcome recall."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cdd_prime.leakage import check_memorization_prompt


OUTCOME_PATTERN = re.compile(r"\b(completed|closed|terminated|blocked|approved|failed)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memorization probes for deal datasets")
    parser.add_argument("--dataset", default="data/processed/test.jsonl")
    parser.add_argument("--output", default="data/interim/memorization_probe_results.jsonl")
    parser.add_argument("--model", default="openai/gpt-4.1-mini")
    parser.add_argument("--api-base-url", default="https://api.pinference.ai/api/v1")
    parser.add_argument("--api-key-var", default="PRIME_API_KEY")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _chat_completion(base_url: str, api_key: str, model: str, messages: list[dict]) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 300,
    }
    req = request.Request(
        url=base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def build_prompts(row: dict) -> list[tuple[str, str]]:
    acquirer = row["info"]["acquirer"]
    target = row["info"]["target"]
    deal_name = f"{acquirer}-{target}"
    prompts = [
        (
            "direct",
            f"What happened to the {acquirer} acquisition of {target}? Give the outcome directly.",
        ),
        (
            "masked",
            "Given this hypothetical pre-deal context, estimate probability the deal closes successfully and explain uncertainty.",
        ),
    ]
    return [(deal_name, p_type + "::" + text) for p_type, text in prompts]


def main() -> None:
    args = parse_args()
    rows = []
    with Path(args.dataset).open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv(args.api_key_var, "")
    online = not args.dry_run
    if online and not api_key:
        raise RuntimeError(f"{args.api_key_var} is required unless --dry-run is used")

    results = []
    for row in rows:
        for deal_name, raw_prompt in build_prompts(row):
            probe_type, prompt_text = raw_prompt.split("::", 1)
            risk_meta = check_memorization_prompt(prompt_text, deal_name)
            response_text = ""
            if online:
                messages = [{"role": "user", "content": prompt_text}]
                response_text = _chat_completion(args.api_base_url, api_key, args.model, messages)

            results.append(
                {
                    "deal_id": row["deal_id"],
                    "deal_name": deal_name,
                    "probe_type": probe_type,
                    "prompt": prompt_text,
                    "memorization_meta": risk_meta,
                    "response": response_text,
                    "response_outcome_claim_detected": bool(OUTCOME_PATTERN.search(response_text)) if response_text else None,
                }
            )

    with out_path.open("w") as f:
        for r in results:
            f.write(json.dumps(r, sort_keys=True) + "\n")

    mode = "dry-run" if args.dry_run else "online"
    print(f"wrote {out_path} ({len(results)} probes, mode={mode})")


if __name__ == "__main__":
    main()
