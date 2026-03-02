"""Group / multi-sample policy metrics for CDD evaluations."""

from __future__ import annotations

from typing import Sequence

from .metrics import decision_utility


def _validate(sample_preds: Sequence[Sequence[int]], labels: Sequence[int], k: int) -> None:
    if k <= 0:
        raise ValueError("k must be positive")
    if len(sample_preds) != len(labels) or not labels:
        raise ValueError("sample_preds and labels must be equal non-empty sequences")
    for preds in sample_preds:
        if not preds:
            raise ValueError("each sample_preds row must be non-empty")


def pass_at_k(sample_preds: Sequence[Sequence[int]], labels: Sequence[int], k: int) -> float:
    """Fraction of deals where at least one of top-k samples is correct."""
    _validate(sample_preds, labels, k)
    hits = 0
    for preds, y in zip(sample_preds, labels):
        if any(int(p) == int(y) for p in preds[:k]):
            hits += 1
    return hits / len(labels)


def majority_vote_labels(sample_preds: Sequence[Sequence[int]], k: int, tie_breaker: int = 0) -> list[int]:
    """Convert top-k samples into a single label via majority vote."""
    if k <= 0:
        raise ValueError("k must be positive")
    if tie_breaker not in (0, 1):
        raise ValueError("tie_breaker must be 0 or 1")
    out: list[int] = []
    for preds in sample_preds:
        top = [int(x) for x in preds[:k]]
        ones = sum(1 for x in top if x == 1)
        zeros = len(top) - ones
        if ones > zeros:
            out.append(1)
        elif zeros > ones:
            out.append(0)
        else:
            out.append(tie_breaker)
    return out


def majority_vote_utility(
    sample_preds: Sequence[Sequence[int]],
    labels: Sequence[int],
    k: int,
    tie_breaker: int = 0,
    tp_value: float = 1.0,
    tn_value: float = 0.5,
    fp_cost: float = -1.5,
    fn_cost: float = -1.0,
) -> float:
    """Decision utility for majority-vote policy over top-k samples."""
    _validate(sample_preds, labels, k)
    voted = majority_vote_labels(sample_preds, k, tie_breaker=tie_breaker)
    return decision_utility(
        voted,
        labels,
        tp_value=tp_value,
        tn_value=tn_value,
        fp_cost=fp_cost,
        fn_cost=fn_cost,
    )

