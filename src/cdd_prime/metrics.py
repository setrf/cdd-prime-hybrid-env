"""Evaluation metrics for probabilistic CDD predictions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence


EPS = 1e-12


@dataclass(frozen=True)
class Confusion:
    tp: int
    fp: int
    tn: int
    fn: int


def _clamp_probability(p: float) -> float:
    return min(1.0 - EPS, max(EPS, float(p)))


def brier_score(probs: Sequence[float], labels: Sequence[int]) -> float:
    if len(probs) != len(labels) or not probs:
        raise ValueError("brier_score requires equal non-empty sequences")
    total = 0.0
    for p, y in zip(probs, labels):
        total += (_clamp_probability(p) - int(y)) ** 2
    return total / len(probs)


def log_loss(probs: Sequence[float], labels: Sequence[int]) -> float:
    if len(probs) != len(labels) or not probs:
        raise ValueError("log_loss requires equal non-empty sequences")
    total = 0.0
    for p, y in zip(probs, labels):
        pc = _clamp_probability(p)
        yi = int(y)
        total += -(yi * math.log(pc) + (1 - yi) * math.log(1 - pc))
    return total / len(probs)


def accuracy(pred_labels: Sequence[int], labels: Sequence[int]) -> float:
    if len(pred_labels) != len(labels) or not labels:
        raise ValueError("accuracy requires equal non-empty sequences")
    correct = sum(1 for p, y in zip(pred_labels, labels) if int(p) == int(y))
    return correct / len(labels)


def confusion(pred_labels: Sequence[int], labels: Sequence[int]) -> Confusion:
    if len(pred_labels) != len(labels):
        raise ValueError("confusion requires equal-length sequences")
    tp = fp = tn = fn = 0
    for p, y in zip(pred_labels, labels):
        pi, yi = int(p), int(y)
        if pi == 1 and yi == 1:
            tp += 1
        elif pi == 1 and yi == 0:
            fp += 1
        elif pi == 0 and yi == 0:
            tn += 1
        elif pi == 0 and yi == 1:
            fn += 1
    return Confusion(tp=tp, fp=fp, tn=tn, fn=fn)


def decision_utility(
    pred_labels: Sequence[int],
    labels: Sequence[int],
    tp_value: float = 1.0,
    tn_value: float = 0.5,
    fp_cost: float = -1.5,
    fn_cost: float = -1.0,
) -> float:
    """Average decision utility for a binary go/no-go decision policy."""
    c = confusion(pred_labels, labels)
    total = (
        c.tp * tp_value
        + c.tn * tn_value
        + c.fp * fp_cost
        + c.fn * fn_cost
    )
    n = len(labels)
    if n == 0:
        raise ValueError("decision_utility requires non-empty labels")
    return total / n


def calibration_bins(
    probs: Sequence[float],
    labels: Sequence[int],
    bins: int = 10,
) -> list[dict[str, float]]:
    if len(probs) != len(labels) or not probs:
        raise ValueError("calibration_bins requires equal non-empty sequences")
    if bins <= 0:
        raise ValueError("bins must be positive")

    groups: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for p, y in zip(probs, labels):
        pc = _clamp_probability(p)
        idx = min(bins - 1, int(pc * bins))
        groups[idx].append((pc, int(y)))

    out: list[dict[str, float]] = []
    for idx, g in enumerate(groups):
        if not g:
            continue
        pred_mean = sum(p for p, _ in g) / len(g)
        obs_rate = sum(y for _, y in g) / len(g)
        out.append(
            {
                "bin": float(idx),
                "count": float(len(g)),
                "pred_mean": pred_mean,
                "obs_rate": obs_rate,
            }
        )
    return out
