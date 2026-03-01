"""CDD hybrid environment for Prime verifiers.

This environment combines process-quality and outcome-quality rewards.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any


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


def _require_dependencies() -> tuple[Any, Any]:
    try:
        import verifiers as vf  # type: ignore
        from datasets import Dataset  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Missing dependencies. Install with: pip install verifiers datasets"
        ) from exc
    return vf, Dataset


def _resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.exists():
        return path
    root = Path(__file__).resolve().parents[2]
    candidate = root / path_value
    if candidate.exists():
        return candidate
    return path


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _completion_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list):
        parts: list[str] = []
        for msg in completion:
            if isinstance(msg, dict):
                parts.append(str(msg.get("content", "")))
            else:
                parts.append(str(msg))
        return "\n".join(parts)
    return str(completion)


def _extract_json(text: str) -> dict[str, Any] | None:
    t = text.strip()
    if not t:
        return None

    # Handle fenced JSON blocks first.
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, flags=re.S)
    if fence:
        t = fence.group(1)

    # Fallback: grab largest brace block.
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


def _safe_probability(parsed: dict[str, Any]) -> float | None:
    p = parsed.get("success_probability")
    try:
        value = float(p)
    except Exception:
        return None
    if value < 0.0 or value > 1.0:
        return None
    return value


def _answer_obj(answer: Any) -> dict[str, Any] | None:
    if isinstance(answer, dict):
        return answer
    if isinstance(answer, str):
        try:
            parsed = json.loads(answer)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
    return None


def _recommended_label(parsed: dict[str, Any]) -> int | None:
    rec = str(parsed.get("recommendation", "")).strip().upper()
    if rec == "GO":
        return 1
    if rec == "NO_GO":
        return 0
    return None


async def format_reward(completion: Any) -> float:
    parsed = _extract_json(_completion_text(completion))
    if parsed is None:
        return 0.0
    required = {
        "recommendation",
        "success_probability",
        "risk_flags",
        "workstream_findings",
        "evidence_citations",
        "thesis_summary",
    }
    if not required.issubset(parsed.keys()):
        return 0.0
    if not isinstance(parsed["risk_flags"], list):
        return 0.0
    if not isinstance(parsed["workstream_findings"], dict):
        return 0.0
    if not isinstance(parsed["evidence_citations"], list):
        return 0.0
    if _safe_probability(parsed) is None:
        return 0.0
    return 1.0


async def coverage_reward(completion: Any) -> float:
    parsed = _extract_json(_completion_text(completion))
    if parsed is None:
        return 0.0
    findings = parsed.get("workstream_findings")
    if not isinstance(findings, dict):
        return 0.0
    covered = len(set(findings.keys()) & WORKSTREAMS)
    return covered / len(WORKSTREAMS)


async def evidence_citation_reward(
    completion: Any,
    evidence_items: list[dict[str, Any]] | None = None,
) -> float:
    parsed = _extract_json(_completion_text(completion))
    if parsed is None:
        return 0.0
    citations = parsed.get("evidence_citations", [])
    if not isinstance(citations, list) or not citations:
        return 0.0

    # Fallback when runtime does not inject evidence_items into reward args.
    if not evidence_items:
        return min(1.0, len({str(x) for x in citations}) / 3.0)

    valid_ids = {str(e.get("evidence_id", "")) for e in evidence_items}
    cited = {str(x) for x in citations}
    hits = len(valid_ids & cited)

    # Full credit at 3 unique valid citations.
    return min(1.0, hits / 3.0)


async def calibration_reward(completion: Any, answer: Any) -> float:
    parsed = _extract_json(_completion_text(completion))
    if parsed is None:
        return 0.0
    prob = _safe_probability(parsed)
    if prob is None:
        return 0.0
    answer_dict = _answer_obj(answer)
    if answer_dict is None:
        return 0.0
    y = float(answer_dict.get("outcome_label", 0))
    return 1.0 - (prob - y) ** 2


async def decision_alignment_reward(completion: Any, answer: Any) -> float:
    parsed = _extract_json(_completion_text(completion))
    if parsed is None:
        return 0.0
    pred = _recommended_label(parsed)
    if pred is None:
        return 0.0
    answer_dict = _answer_obj(answer)
    if answer_dict is None:
        return 0.0
    y = int(answer_dict.get("outcome_label", 0))
    return 1.0 if pred == y else 0.0


async def consistency_reward(completion: Any) -> float:
    parsed = _extract_json(_completion_text(completion))
    if parsed is None:
        return 0.0
    p = _safe_probability(parsed)
    rec = _recommended_label(parsed)
    if p is None or rec is None:
        return 0.0
    if rec == 1 and p < 0.5:
        return 0.0
    if rec == 0 and p >= 0.5:
        return 0.0
    return 1.0


def load_environment(
    dataset_path: str = "data/processed/train.jsonl",
    eval_dataset_path: str = "data/processed/val.jsonl",
    num_examples: int = -1,
    seed: int = 42,
):
    vf, Dataset = _require_dependencies()

    ds_path = _resolve_path(dataset_path)
    ev_path = _resolve_path(eval_dataset_path)

    train_rows = _load_jsonl(ds_path)
    eval_rows = _load_jsonl(ev_path)

    if num_examples > 0:
        random.seed(seed)
        random.shuffle(train_rows)
        train_rows = train_rows[:num_examples]

    dataset = Dataset.from_list(train_rows)
    eval_dataset = Dataset.from_list(eval_rows)

    rubric = vf.Rubric(
        funcs=[
            format_reward,
            coverage_reward,
            evidence_citation_reward,
            calibration_reward,
            decision_alignment_reward,
            consistency_reward,
        ],
        weights=[0.15, 0.20, 0.15, 0.25, 0.20, 0.05],
    )

    return vf.SingleTurnEnv(dataset=dataset, eval_dataset=eval_dataset, rubric=rubric)
