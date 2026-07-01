"""Function-sequence baseline for RQ1."""

from __future__ import annotations

import torch
import torch.nn as nn


class FunctionSequenceModel(nn.Module):
    """Bidirectional GRU over functions in a contract.

    The model returns one logit per function token so it can be trained against
    interaction/function labels while using contract context.
    """

    def __init__(
        self,
        embedding_dim: int = 768,
        scalar_dim: int = 0,
        hidden_dim: int = 256,
        layers: int = 1,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.input_dim = embedding_dim + scalar_dim
        self.encoder = nn.GRU(
            input_size=self.input_dim,
            hidden_size=hidden_dim,
            num_layers=layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if layers > 1 else 0.0,
        )
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(hidden_dim * 2, 1)

    def forward(
        self,
        function_embeddings: torch.Tensor,
        mask: torch.Tensor,
        scalar_features: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if scalar_features is not None:
            x = torch.cat([function_embeddings, scalar_features], dim=-1)
        else:
            x = function_embeddings
        encoded, _ = self.encoder(x)
        logits = self.head(self.drop(encoded)).squeeze(-1)
        return logits.masked_fill(~mask, 0.0)

