"""Shared neural-network utilities for fair-evaluation models."""

from __future__ import annotations

import torch
import torch.nn as nn


class MLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 256, output_dim: int = 1, dropout: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def masked_mean(x: torch.Tensor, mask: torch.Tensor, dim: int = 1) -> torch.Tensor:
    mask_f = mask.to(dtype=x.dtype).unsqueeze(-1)
    denom = mask_f.sum(dim=dim).clamp_min(1.0)
    return (x * mask_f).sum(dim=dim) / denom


def segment_softmax(scores: torch.Tensor, segment_ids: torch.Tensor, num_segments: int) -> torch.Tensor:
    """Small dependency-free segment softmax for 1D scores."""

    out = torch.zeros_like(scores)
    for idx in range(num_segments):
        mask = segment_ids == idx
        if mask.any():
            out[mask] = torch.softmax(scores[mask], dim=0)
    return out


def validate_edge_index(edge_index: torch.Tensor) -> None:
    if edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise ValueError(f"edge_index must have shape (2, E), got {tuple(edge_index.shape)}")

