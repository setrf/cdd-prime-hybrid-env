"""Dataset schema and validation helpers."""

from __future__ import annotations

import json
from datetime import date
from typing import Any


REQUIRED_PACKET_KEYS = {"deal_id", "decision_date", "prompt", "answer", "info", "evidence_items"}
REQUIRED_ANSWER_KEYS = {
    "deal_completed",
    "close_label",
    "outcome_label",
    "thesis_hit_label",
    "abnormal_return_365d",
    "abnormal_return_730d",
    "max_drawdown_365d",
    "max_drawdown_730d",
}
REQUIRED_INFO_KEYS = {
    "acquirer",
    "target",
    "sector",
    "deal_type",
    "payment_type",
    "cross_border",
    "premium_pct",
    "regulatory_risk",
    "source_quality_score",
}


def parse_iso_date(s: str) -> date:
    return date.fromisoformat(s)


def validate_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = REQUIRED_PACKET_KEYS - set(packet.keys())
    if missing:
        errors.append(f"missing packet keys: {sorted(missing)}")

    if "deal_id" in packet and not isinstance(packet["deal_id"], str):
        errors.append("deal_id must be string")

    if "decision_date" in packet:
        try:
            parse_iso_date(str(packet["decision_date"]))
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"decision_date invalid: {exc}")

    prompt = packet.get("prompt")
    if not isinstance(prompt, list) or not prompt:
        errors.append("prompt must be a non-empty chat-message list")
    else:
        for i, msg in enumerate(prompt):
            if not isinstance(msg, dict):
                errors.append(f"prompt[{i}] must be dict")
                continue
            if "role" not in msg or "content" not in msg:
                errors.append(f"prompt[{i}] missing role/content")

    answer = packet.get("answer")
    answer_obj: dict[str, Any] | None = None
    if isinstance(answer, dict):
        answer_obj = answer
    elif isinstance(answer, str):
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict):
                answer_obj = parsed
            else:
                errors.append("answer string must decode to dict JSON")
        except json.JSONDecodeError:
            errors.append("answer string must be valid JSON")
    else:
        errors.append("answer must be dict or JSON string")

    if answer_obj is not None:
        missing_answer = REQUIRED_ANSWER_KEYS - set(answer_obj.keys())
        if missing_answer:
            errors.append(f"missing answer keys: {sorted(missing_answer)}")

    info = packet.get("info")
    if not isinstance(info, dict):
        errors.append("info must be dict")
    else:
        missing_info = REQUIRED_INFO_KEYS - set(info.keys())
        if missing_info:
            errors.append(f"missing info keys: {sorted(missing_info)}")

    evidence_items = packet.get("evidence_items")
    if not isinstance(evidence_items, list) or not evidence_items:
        errors.append("evidence_items must be non-empty list")
    else:
        for i, item in enumerate(evidence_items):
            if not isinstance(item, dict):
                errors.append(f"evidence_items[{i}] must be dict")
                continue
            for key in ("evidence_id", "source_type", "source_url", "source_date", "source_quality_score", "summary"):
                if key not in item:
                    errors.append(f"evidence_items[{i}] missing {key}")

    return errors
