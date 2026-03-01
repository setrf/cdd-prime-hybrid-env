"""Leakage and memorization guardrails for CDD dataset packets."""

from __future__ import annotations

from datetime import date
from typing import Any


OUTCOME_LEAK_TERMS = (
    "completed",
    "closed",
    "terminated",
    "blocked",
    "approved",
    "won arbitration",
    "post-close",
    "after closing",
)


def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


def check_timestamp_leakage(packet: dict[str, Any]) -> list[str]:
    """Return leakage issues where evidence dates are after decision date."""
    issues: list[str] = []
    decision = _parse_date(str(packet["decision_date"]))
    for item in packet.get("evidence_items", []):
        try:
            src_date = _parse_date(str(item.get("source_date")))
        except Exception:
            issues.append(f"invalid source_date for evidence_id={item.get('evidence_id')}")
            continue
        if src_date > decision:
            issues.append(
                f"evidence_id={item.get('evidence_id')} has source_date {src_date} after decision_date {decision}"
            )
    return issues


def check_prompt_for_outcome_leaks(packet: dict[str, Any]) -> list[str]:
    """Simple lexical scan for direct outcome leakage language in prompt text."""
    issues: list[str] = []
    text = "\n".join(str(m.get("content", "")) for m in packet.get("prompt", []))
    lower = text.lower()
    for term in OUTCOME_LEAK_TERMS:
        if term in lower:
            issues.append(f"prompt contains possible outcome leak term: {term}")
    return issues


def check_memorization_prompt(prompt_text: str, deal_name: str) -> dict[str, Any]:
    """Heuristic check for likely memorization-oriented prompts."""
    lower = prompt_text.lower()
    direct = any(
        phrase in lower
        for phrase in (
            "what happened",
            "did the deal close",
            "was the acquisition completed",
            "eventual outcome",
        )
    )
    mentions_deal = deal_name.lower() in lower
    risk = "high" if direct and mentions_deal else "medium" if direct else "low"
    return {
        "memorization_risk": risk,
        "direct_outcome_query": direct,
        "mentions_specific_deal": mentions_deal,
    }
