"""Reusable neural training/evaluation loops.

The concrete experiment runners will provide model-specific `step_fn`
functions that turn a batch into `(logits, labels)`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn


StepFn = Callable[[nn.Module, Any, torch.device], tuple[torch.Tensor, torch.Tensor]]


@dataclass(frozen=True)
class EpochResult:
    loss: float
    examples: int


@dataclass(frozen=True)
class PredictionResult:
    logits: np.ndarray
    probs: np.ndarray
    labels: np.ndarray


def train_one_epoch(
    model: nn.Module,
    dataloader: Iterable[Any],
    optimizer: torch.optim.Optimizer,
    loss_fn: nn.Module,
    step_fn: StepFn,
    device: torch.device,
    grad_clip: float | None = None,
) -> EpochResult:
    model.train()
    total_loss = 0.0
    total_examples = 0
    for batch in dataloader:
        optimizer.zero_grad(set_to_none=True)
        logits, labels = step_fn(model, batch, device)
        labels = labels.float()
        loss = loss_fn(logits, labels)
        loss.backward()
        if grad_clip is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        n = int(labels.numel())
        total_loss += float(loss.item()) * n
        total_examples += n
    return EpochResult(loss=total_loss / max(total_examples, 1), examples=total_examples)


@torch.no_grad()
def predict(
    model: nn.Module,
    dataloader: Iterable[Any],
    step_fn: StepFn,
    device: torch.device,
) -> PredictionResult:
    model.eval()
    logits_list: list[np.ndarray] = []
    labels_list: list[np.ndarray] = []
    for batch in dataloader:
        logits, labels = step_fn(model, batch, device)
        logits_list.append(logits.detach().cpu().numpy())
        labels_list.append(labels.detach().cpu().numpy())
    logits_np = np.concatenate(logits_list) if logits_list else np.asarray([])
    labels_np = np.concatenate(labels_list).astype(int) if labels_list else np.asarray([], dtype=int)
    return PredictionResult(
        logits=logits_np,
        probs=1.0 / (1.0 + np.exp(-logits_np)),
        labels=labels_np,
    )

