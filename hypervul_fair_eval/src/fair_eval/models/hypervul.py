"""HyperVul model variants for RQ3 component ablation."""

from __future__ import annotations

import torch
import torch.nn as nn

from .common import masked_mean


class TupleLocalizationHead(nn.Module):
    """Scores function-state-callee tuples for localizable evidence."""

    def __init__(self, dim: int, hidden_dim: int = 128):
        super().__init__()
        self.func = nn.Linear(dim, hidden_dim)
        self.state = nn.Linear(dim, hidden_dim)
        self.callee = nn.Linear(dim, hidden_dim)
        self.score = nn.Linear(hidden_dim, 1)

    def forward(
        self,
        function_embedding: torch.Tensor,
        state_embeddings: torch.Tensor,
        callee_embeddings: torch.Tensor,
        state_mask: torch.Tensor,
        callee_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        f = self.func(function_embedding).unsqueeze(1).unsqueeze(2)
        s = self.state(state_embeddings).unsqueeze(2)
        c = self.callee(callee_embeddings).unsqueeze(1)
        raw = self.score(torch.tanh(f + s + c)).squeeze(-1)
        valid = state_mask.unsqueeze(2) & callee_mask.unsqueeze(1)
        raw = raw.masked_fill(~valid, -1e9)
        attn = torch.softmax(raw.reshape(raw.shape[0], -1), dim=-1).reshape_as(raw)
        attn = attn.masked_fill(~valid, 0.0)
        loc_logit = (attn * raw.masked_fill(~valid, 0.0)).sum(dim=(1, 2))
        return loc_logit, attn


class HyperVulModel(nn.Module):
    """HyperVul interaction classifier with ablation flags.

    Expected input shape is `(B, M, D)` where member order is function first,
    followed by state members and callee members. Runners will construct masks
    from the isolated hyperedge view.
    """

    def __init__(
        self,
        embedding_dim: int = 768,
        symbolic_dim: int = 8,
        hidden_dim: int = 256,
        dropout: float = 0.3,
        use_symbolic: bool = True,
        use_localization: bool = True,
        use_sequence_pool: bool = True,
    ):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.symbolic_dim = symbolic_dim if use_symbolic else 0
        self.input_dim = embedding_dim + self.symbolic_dim
        self.use_symbolic = use_symbolic
        self.use_localization = use_localization
        self.use_sequence_pool = use_sequence_pool

        if use_sequence_pool:
            self.sequence = nn.GRU(
                input_size=self.input_dim,
                hidden_size=self.input_dim // 2,
                batch_first=True,
                bidirectional=True,
            )
        else:
            self.sequence = None

        self.attn = nn.Sequential(
            nn.Linear(self.input_dim, 128),
            nn.Tanh(),
            nn.Linear(128, 1, bias=False),
        )
        self.head = nn.Sequential(
            nn.Linear(self.input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        self.localizer = TupleLocalizationHead(self.input_dim) if use_localization else None
        self.loc_gate = nn.Parameter(torch.tensor(1.0)) if use_localization else None

    def _combine_inputs(self, member_embeddings: torch.Tensor, symbolic_features: torch.Tensor | None) -> torch.Tensor:
        if self.use_symbolic:
            if symbolic_features is None:
                symbolic_features = torch.zeros(
                    *member_embeddings.shape[:-1],
                    self.symbolic_dim,
                    device=member_embeddings.device,
                    dtype=member_embeddings.dtype,
                )
            return torch.cat([member_embeddings, symbolic_features], dim=-1)
        return member_embeddings

    def forward(
        self,
        member_embeddings: torch.Tensor,
        member_mask: torch.Tensor,
        symbolic_features: torch.Tensor | None = None,
        state_mask: torch.Tensor | None = None,
        callee_mask: torch.Tensor | None = None,
        state_embeddings: torch.Tensor | None = None,
        callee_embeddings: torch.Tensor | None = None,
        state_symbolic: torch.Tensor | None = None,
        callee_symbolic: torch.Tensor | None = None,
        return_localization: bool = False,
    ) -> torch.Tensor | tuple[torch.Tensor, dict[str, torch.Tensor] | None]:
        x = self._combine_inputs(member_embeddings, symbolic_features)
        if self.sequence is not None:
            x, _ = self.sequence(x)

        scores = self.attn(x).squeeze(-1).masked_fill(~member_mask, -1e9)
        weights = torch.softmax(scores, dim=1).masked_fill(~member_mask, 0.0)
        pooled = (x * weights.unsqueeze(-1)).sum(dim=1)
        logits = self.head(pooled).squeeze(-1)

        localization = None
        if self.localizer is not None and state_mask is not None and callee_mask is not None:
            function_embedding = x[:, 0, :]
            if state_embeddings is None or callee_embeddings is None:
                # Fall back to slicing members when explicit state/callee tensors are not supplied.
                state_count = state_mask.shape[1]
                callee_count = callee_mask.shape[1]
                state_x = x[:, 1 : 1 + state_count, :]
                callee_x = x[:, 1 + state_count : 1 + state_count + callee_count, :]
            else:
                state_x = self._combine_inputs(state_embeddings, state_symbolic)
                callee_x = self._combine_inputs(callee_embeddings, callee_symbolic)
            loc_logit, tuple_attention = self.localizer(function_embedding, state_x, callee_x, state_mask, callee_mask)
            logits = logits + self.loc_gate * loc_logit
            localization = {"tuple_attention": tuple_attention, "loc_logit": loc_logit}

        if return_localization:
            return logits, localization
        return logits


class HyperVulEmbOnly(HyperVulModel):
    def __init__(self, **kwargs):
        super().__init__(use_symbolic=False, **kwargs)


class HyperVulFull(HyperVulModel):
    def __init__(self, **kwargs):
        super().__init__(use_symbolic=True, use_localization=True, **kwargs)

