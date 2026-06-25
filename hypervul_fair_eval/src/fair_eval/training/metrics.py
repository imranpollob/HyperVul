"""Binary classification metrics for vulnerability detection."""

from __future__ import annotations

from typing import Any

import numpy as np


def _safe_auc(labels: np.ndarray, probs: np.ndarray, kind: str) -> float | None:
    if len(np.unique(labels)) < 2:
        return None
    try:
        from sklearn.metrics import average_precision_score, roc_auc_score

        if kind == "pr":
            return float(average_precision_score(labels, probs))
        if kind == "roc":
            return float(roc_auc_score(labels, probs))
    except Exception:
        return None
    raise ValueError(kind)


def binary_metrics(probs: np.ndarray, labels: np.ndarray, threshold: float) -> dict[str, Any]:
    probs = np.asarray(probs, dtype=float)
    labels = np.asarray(labels, dtype=int)
    pred = probs >= threshold
    truth = labels.astype(bool)

    tp = int(np.sum(pred & truth))
    tn = int(np.sum(~pred & ~truth))
    fp = int(np.sum(pred & ~truth))
    fn = int(np.sum(~pred & truth))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if precision + recall else 0.0
    f2 = (5 * precision * recall) / (4 * precision + recall) if 4 * precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if len(labels) else 0.0

    return {
        "threshold": float(threshold),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "false_positive_rate": fpr,
        "f1": f1,
        "f2": f2,
        "accuracy": accuracy,
        "pr_auc": _safe_auc(labels, probs, "pr"),
        "roc_auc": _safe_auc(labels, probs, "roc"),
        "support": int(len(labels)),
        "positive_support": int(np.sum(labels == 1)),
        "negative_support": int(np.sum(labels == 0)),
    }


def clean_negative_metrics(probs: np.ndarray, threshold: float) -> dict[str, Any]:
    probs = np.asarray(probs, dtype=float)
    flagged = probs >= threshold
    return {
        "threshold": float(threshold),
        "support": int(len(probs)),
        "false_positives": int(np.sum(flagged)),
        "false_positive_rate": float(np.mean(flagged)) if len(probs) else 0.0,
        "mean_probability": float(np.mean(probs)) if len(probs) else 0.0,
    }

