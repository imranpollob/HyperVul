"""Shared building blocks for the HyperVul representation model zoo."""
import torch
import torch.nn as nn
from torch_geometric.utils import scatter, softmax


class SegmentAttentionPool(nn.Module):
    """Attention-pool a set of member embeddings into one vector per segment.

    Mirrors model/model.py AttentionPooling but works on a flat (membership) layout:
    `x` are member node features, `seg` assigns each member to a segment (hyperedge),
    output is (num_segments, dim). This is the node->hyperedge aggregation.
    """
    def __init__(self, dim=768, hidden=128):
        super().__init__()
        self.w_a = nn.Linear(dim, hidden)
        self.v = nn.Linear(hidden, 1, bias=False)

    def forward(self, x, seg, num_segments):
        scores = self.v(torch.tanh(self.w_a(x))).squeeze(-1)          # (M,)
        attn = softmax(scores, seg, num_nodes=num_segments)           # segment softmax
        pooled = scatter(attn.unsqueeze(-1) * x, seg, dim=0,
                         dim_size=num_segments, reduce="sum")         # (S, dim)
        return pooled


class MLPHead(nn.Module):
    def __init__(self, dim=768, hidden=256, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)
