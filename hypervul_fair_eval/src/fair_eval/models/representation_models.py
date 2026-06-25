"""Controlled representation-ablation models for RQ2."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import masked_mean
from .graph_models import GraphAttentionLayer, MeanGraphConv


class SetPoolClassifier(nn.Module):
    """No-structure baseline over hyperedge members."""

    def __init__(self, input_dim: int = 768, hidden_dim: int = 256, dropout: float = 0.3):
        super().__init__()
        self.input = nn.Linear(input_dim, hidden_dim)
        self.drop = nn.Dropout(dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, members: torch.Tensor, member_mask: torch.Tensor) -> torch.Tensor:
        h = self.drop(torch.relu(self.input(members)))
        pooled = masked_mean(h, member_mask, dim=1)
        return self.head(pooled).squeeze(-1)


class PairwiseMemberGNNClassifier(nn.Module):
    """Pairwise clique-reduction encoder for the same hyperedge candidates."""

    def __init__(
        self,
        input_dim: int = 768,
        hidden_dim: int = 256,
        layers: int = 2,
        dropout: float = 0.3,
        conv: str = "gcn",
    ):
        super().__init__()
        if conv not in {"gcn", "gat"}:
            raise ValueError(f"Unsupported conv={conv}")
        self.conv = conv
        self.input = nn.Linear(input_dim, hidden_dim)
        self.convs = nn.ModuleList(
            MeanGraphConv(hidden_dim, hidden_dim) if conv == "gcn" else GraphAttentionLayer(hidden_dim, hidden_dim)
            for _ in range(layers)
        )
        self.norms = nn.ModuleList(nn.LayerNorm(hidden_dim) for _ in range(layers))
        self.drop = nn.Dropout(dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, node_features: torch.Tensor, edge_index: torch.Tensor, segment_ids: torch.Tensor, num_segments: int) -> torch.Tensor:
        h = torch.relu(self.input(node_features))
        for conv, norm in zip(self.convs, self.norms):
            msg = conv(h, edge_index)
            h = norm(h + self.drop(torch.relu(msg)))

        pooled = torch.zeros(num_segments, h.shape[-1], device=h.device, dtype=h.dtype)
        counts = torch.zeros(num_segments, device=h.device, dtype=h.dtype)
        pooled.index_add_(0, segment_ids, h)
        counts.index_add_(0, segment_ids, torch.ones_like(segment_ids, dtype=h.dtype))
        pooled = pooled / counts.clamp_min(1.0).unsqueeze(-1)
        return self.head(pooled).squeeze(-1)

