"""Dependency-free graph baselines for generic call/pairwise graph views."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import validate_edge_index


class MeanGraphConv(nn.Module):
    """Simple GCN-style mean aggregation with self and neighbor transforms."""

    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.self_linear = nn.Linear(input_dim, output_dim)
        self.neigh_linear = nn.Linear(input_dim, output_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        validate_edge_index(edge_index)
        src, dst = edge_index
        agg = torch.zeros_like(x)
        deg = torch.zeros(x.shape[0], device=x.device, dtype=x.dtype)
        if edge_index.numel() > 0:
            agg.index_add_(0, dst, x[src])
            deg.index_add_(0, dst, torch.ones_like(dst, dtype=x.dtype))
        agg = agg / deg.clamp_min(1.0).unsqueeze(-1)
        return self.self_linear(x) + self.neigh_linear(agg)


class EdgeTypeGraphConv(nn.Module):
    """Mean aggregation with one neighbor transform per edge type."""

    def __init__(self, input_dim: int, output_dim: int, edge_types: int):
        super().__init__()
        self.self_linear = nn.Linear(input_dim, output_dim)
        self.edge_linears = nn.ModuleList(nn.Linear(input_dim, output_dim) for _ in range(edge_types))

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_type: torch.Tensor) -> torch.Tensor:
        validate_edge_index(edge_index)
        out = self.self_linear(x)
        if edge_index.numel() == 0:
            return out
        src, dst = edge_index
        for etype, linear in enumerate(self.edge_linears):
            mask = edge_type == etype
            if not mask.any():
                continue
            agg = torch.zeros(x.shape[0], x.shape[1], device=x.device, dtype=x.dtype)
            deg = torch.zeros(x.shape[0], device=x.device, dtype=x.dtype)
            agg.index_add_(0, dst[mask], x[src[mask]])
            deg.index_add_(0, dst[mask], torch.ones_like(dst[mask], dtype=x.dtype))
            out = out + linear(agg / deg.clamp_min(1.0).unsqueeze(-1))
        return out


class GraphAttentionLayer(nn.Module):
    """Small single-head GAT layer for node classification baselines."""

    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)
        self.attn_src = nn.Linear(output_dim, 1, bias=False)
        self.attn_dst = nn.Linear(output_dim, 1, bias=False)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        validate_edge_index(edge_index)
        h = self.linear(x)
        if edge_index.numel() == 0:
            return h
        src, dst = edge_index
        scores = self.leaky_relu(self.attn_src(h[src]).squeeze(-1) + self.attn_dst(h[dst]).squeeze(-1))
        out = torch.zeros_like(h)
        max_per_dst = torch.full((h.shape[0],), -torch.inf, device=h.device, dtype=h.dtype)
        max_per_dst.scatter_reduce_(0, dst, scores, reduce="amax", include_self=True)
        exp_scores = torch.exp(scores - max_per_dst[dst])
        denom = torch.zeros(h.shape[0], device=h.device, dtype=h.dtype)
        denom.index_add_(0, dst, exp_scores)
        weights = exp_scores / denom[dst].clamp_min(1e-12)
        out.index_add_(0, dst, h[src] * weights.unsqueeze(-1))
        no_incoming = torch.ones(h.shape[0], device=h.device, dtype=torch.bool)
        no_incoming[dst] = False
        out[no_incoming] = h[no_incoming]
        return out


class GraphNodeClassifier(nn.Module):
    """GCN/GAT node classifier for callgraph and pairwise graph baselines."""

    def __init__(
        self,
        input_dim: int = 768,
        scalar_dim: int = 0,
        hidden_dim: int = 256,
        layers: int = 2,
        dropout: float = 0.3,
        conv: str = "gcn",
        edge_types: int = 1,
    ):
        super().__init__()
        if conv not in {"gcn", "rgcn", "gat"}:
            raise ValueError(f"Unsupported conv={conv}")
        self.conv = conv
        self.input = nn.Linear(input_dim + scalar_dim, hidden_dim)
        convs = []
        for _ in range(layers):
            if conv == "gcn":
                convs.append(MeanGraphConv(hidden_dim, hidden_dim))
            elif conv == "rgcn":
                convs.append(EdgeTypeGraphConv(hidden_dim, hidden_dim, edge_types=edge_types))
            else:
                convs.append(GraphAttentionLayer(hidden_dim, hidden_dim))
        self.convs = nn.ModuleList(convs)
        self.norms = nn.ModuleList(nn.LayerNorm(hidden_dim) for _ in range(layers))
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        node_embeddings: torch.Tensor,
        edge_index: torch.Tensor,
        scalar_features: torch.Tensor | None = None,
        edge_type: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if scalar_features is not None:
            x = torch.cat([node_embeddings, scalar_features], dim=-1)
        else:
            x = node_embeddings
        h = torch.relu(self.input(x))
        for conv, norm in zip(self.convs, self.norms):
            if self.conv == "rgcn":
                if edge_type is None:
                    raise ValueError("edge_type is required for rgcn")
                msg = conv(h, edge_index, edge_type)
            else:
                msg = conv(h, edge_index)
            h = norm(h + self.drop(torch.relu(msg)))
        return self.head(h).squeeze(-1)
