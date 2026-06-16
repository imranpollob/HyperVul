"""Set-pool classifier: the no-structure lower bound.

Each hyperedge is classified independently by attention-pooling its member nodes
(function + state vars + callees) and feeding the pooled vector to an MLP. This is
exactly the deployed model (model/model.py), re-expressed on the membership layout
so it shares the batch format with the structural models. NO message passing.
"""
import torch.nn as nn
from .ops import SegmentAttentionPool, MLPHead


class SetPoolClassifier(nn.Module):
    name = "set-pool (no edges)"

    def __init__(self, dim=768, hidden=256, dropout=0.3):
        super().__init__()
        self.pool = SegmentAttentionPool(dim, hidden=128)
        self.head = MLPHead(dim, hidden, dropout)

    def forward(self, batch):
        edge_h = self.pool(batch.node_feats[batch.inc_node], batch.inc_edge, batch.num_edges)
        return self.head(edge_h)
