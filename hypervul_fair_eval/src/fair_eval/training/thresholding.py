"""Validation-threshold selection policies."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ThresholdSelection:
    policy: str
    threshold: float
    precision: float
    recall: float
    f1: float
    f2: float


def _counts(probs: np.ndarray, labels: np.ndarray, threshold: float) -> tuple[int, int, int]:
    pred = probs >= threshold
    truth = labels.astype(bool)
    tp = int(np.sum(pred & truth))
    fp = int(np.sum(pred & ~truth))
    fn = int(np.sum(~pred & truth))
    return tp, fp, fn


def _scores(probs: np.ndarray, labels: np.ndarray, threshold: float) -> tuple[float, float, float, float]:
    tp, fp, fn = _counts(probs, labels, threshold)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if precision + recall else 0.0
    f2 = (5 * precision * recall) / (4 * precision + recall) if 4 * precision + recall else 0.0
    return precision, recall, f1, f2


def threshold_grid(steps: int = 1001) -> np.ndarray:
    return np.linspace(0.0, 1.0, steps)


def select_threshold(
    probs: np.ndarray,
    labels: np.ndarray,
    policy: str = "target_recall",
    target_recall: float = 0.90,
    target_precision: float = 0.70,
    steps: int = 1001,
) -> ThresholdSelection:
    probs = np.asarray(probs, dtype=float)
    labels = np.asarray(labels, dtype=int)
    best: tuple[float, float, float, float, float] | None = None

    for threshold in threshold_grid(steps):
        precision, recall, f1, f2 = _scores(probs, labels, float(threshold))
        if policy == "max_f1":
            key = f1
        elif policy == "max_f2":
            key = f2
        elif policy == "target_recall":
            key = precision if recall >= target_recall else -1.0
        elif policy == "target_precision":
            key = recall if precision >= target_precision else -1.0
        else:
            raise ValueError(f"Unknown threshold policy: {policy}")

        candidate = (key, float(threshold), precision, recall, f1, f2)
        if best is None or candidate > best:
            best = candidate

    if best is None or best[0] < 0:
        fallback = "max_f2" if policy in {"target_recall", "target_precision"} else policy
        if fallback != policy:
            return select_threshold(probs, labels, policy=fallback, steps=steps)
        raise RuntimeError("Unable to select threshold")

    _, threshold, precision, recall, f1, f2 = best
    return ThresholdSelection(
        policy=policy,
        threshold=threshold,
        precision=precision,
        recall=recall,
        f1=f1,
        f2=f2,
    )

