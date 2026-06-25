"""Function-level MLP baselines for RQ1."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import MLP


class FunctionMLP(nn.Module):
    """Semantic function baseline using only function embeddings."""

    def __init__(self, embedding_dim: int = 768, hidden_dim: int = 256, dropout: float = 0.3):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.head = MLP(embedding_dim, hidden_dim=hidden_dim, dropout=dropout)

    def forward(self, function_embeddings: torch.Tensor) -> torch.Tensor:
        return self.head(function_embeddings).squeeze(-1)


class FunctionFeaturesMLP(nn.Module):
    """Function embedding plus generic scalar metadata baseline."""

    def __init__(
        self,
        embedding_dim: int = 768,
        scalar_dim: int = 9,
        hidden_dim: int = 256,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.scalar_dim = scalar_dim
        self.head = MLP(embedding_dim + scalar_dim, hidden_dim=hidden_dim, dropout=dropout)

    def forward(self, function_embeddings: torch.Tensor, scalar_features: torch.Tensor) -> torch.Tensor:
        x = torch.cat([function_embeddings, scalar_features], dim=-1)
        return self.head(x).squeeze(-1)

