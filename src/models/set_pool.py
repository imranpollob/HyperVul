"""Set-pool classifier: the no-structure lower bound.

Each hyperedge is classified independently by attention-pooling its member nodes
(function + state vars + callees) and feeding the pooled vector to an MLP. This is
exactly the deployed model (model/model.py), re-expressed on the membership layout
so it shares the batch format with the structural models. NO message passing.
"""
import torch
import torch.nn as nn
from torch_geometric.utils import scatter
from .ops import MLPHead

class SetPoolClassifier(nn.Module):
    name = "set-pool (no edges)"

    def __init__(self, dim=768, hidden=256, dropout=0.3):
        super().__init__()
        self.in_proj = nn.Linear(dim, hidden)
        self.drop = nn.Dropout(dropout)
        self.head = MLPHead(hidden, hidden, dropout)

    def forward(self, batch):
        h = self.drop(torch.relu(self.in_proj(batch.node_feats)))
        # Naive bag-of-nodes pooling: mean over all members in the hyperedge
        edge_h = scatter(h[batch.inc_node], batch.inc_edge, dim=0, dim_size=batch.num_edges, reduce="mean")
        return self.head(edge_h)
