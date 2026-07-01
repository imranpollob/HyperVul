"""Hyperedge neural network for RQ2 representation ablation."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import segment_softmax


class SegmentAttentionPool(nn.Module):
    def __init__(self, dim: int, hidden_dim: int = 128):
        super().__init__()
        self.score = nn.Sequential(
            nn.Linear(dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1, bias=False),
        )

    def forward(self, values: torch.Tensor, segment_ids: torch.Tensor, num_segments: int) -> torch.Tensor:
        scores = self.score(values).squeeze(-1)
        weights = segment_softmax(scores, segment_ids, num_segments)
        out = torch.zeros(num_segments, values.shape[-1], device=values.device, dtype=values.dtype)
        out.index_add_(0, segment_ids, values * weights.unsqueeze(-1))
        return out


class HyperedgeNN(nn.Module):
    """Node-hyperedge message passing over incidence lists."""

    def __init__(self, input_dim: int = 768, hidden_dim: int = 256, layers: int = 2, dropout: float = 0.3):
        super().__init__()
        self.input = nn.Linear(input_dim, hidden_dim)
        self.node_to_edge = nn.ModuleList(SegmentAttentionPool(hidden_dim) for _ in range(layers))
        self.edge_to_node = nn.ModuleList(nn.Linear(hidden_dim, hidden_dim) for _ in range(layers))
        self.norms = nn.ModuleList(nn.LayerNorm(hidden_dim) for _ in range(layers))
        self.drop = nn.Dropout(dropout)
        self.final_pool = SegmentAttentionPool(hidden_dim)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        node_features: torch.Tensor,
        incidence_node: torch.Tensor,
        incidence_edge: torch.Tensor,
        num_edges: int,
    ) -> torch.Tensor:
        h = torch.relu(self.input(node_features))
        for pool, edge_to_node, norm in zip(self.node_to_edge, self.edge_to_node, self.norms):
            edge_h = pool(h[incidence_node], incidence_edge, num_edges)
            node_msg = torch.zeros_like(h)
            deg = torch.zeros(h.shape[0], device=h.device, dtype=h.dtype)
            node_msg.index_add_(0, incidence_node, edge_h[incidence_edge])
            deg.index_add_(0, incidence_node, torch.ones_like(incidence_node, dtype=h.dtype))
            node_msg = node_msg / deg.clamp_min(1.0).unsqueeze(-1)
            h = norm(h + self.drop(torch.relu(edge_to_node(node_msg))))
        edge_ctx = self.final_pool(h[incidence_node], incidence_edge, num_edges)
        return self.head(edge_ctx).squeeze(-1)

