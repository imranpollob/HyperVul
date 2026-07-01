"""Loss functions and class-imbalance helpers."""

from __future__ import annotations

import torch
import torch.nn as nn


def positive_weight(labels: torch.Tensor) -> torch.Tensor:
    labels = labels.float()
    positives = (labels == 1).sum().clamp_min(1)
    negatives = (labels == 0).sum().clamp_min(1)
    return negatives.float() / positives.float()


def bce_with_logits_for_labels(labels: torch.Tensor, device: torch.device | None = None) -> nn.BCEWithLogitsLoss:
    weight = positive_weight(labels).to(device=device) if device is not None else positive_weight(labels)
    return nn.BCEWithLogitsLoss(pos_weight=weight.reshape(1))


class AsymmetricLoss(nn.Module):
    """Asymmetric binary loss for imbalanced vulnerability detection."""

    def __init__(
        self,
        gamma_neg: float = 4.0,
        gamma_pos: float = 1.0,
        clip: float = 0.05,
        eps: float = 1e-8,
        pos_weight: torch.Tensor | None = None,
    ):
        super().__init__()
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
        self.eps = eps
        self.register_buffer("pos_weight", pos_weight.reshape(1) if pos_weight is not None else None)

    def forward(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        labels = labels.float()
        pos_prob = torch.sigmoid(logits)
        neg_prob = 1.0 - pos_prob
        if self.clip is not None and self.clip > 0:
            neg_prob = (neg_prob + self.clip).clamp(max=1.0)

        pos_loss = labels * torch.log(pos_prob.clamp(min=self.eps)) * ((1.0 - pos_prob) ** self.gamma_pos)
        neg_loss = (1.0 - labels) * torch.log(neg_prob.clamp(min=self.eps)) * (pos_prob ** self.gamma_neg)
        if self.pos_weight is not None:
            pos_loss = pos_loss * self.pos_weight
        return (-pos_loss - neg_loss).mean()

