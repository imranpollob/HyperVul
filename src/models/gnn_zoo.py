"""Unified GNN skeleton: identical everywhere except the convolution operator.

This is the fair adjudicator for hyperedge-vs-pairwise. All variants share:
  in_proj -> L x [conv + residual + LayerNorm + dropout] -> attention-pool members -> MLP head
Only `conv` differs:
  - "gcn" / "gat": operate on the CLIQUE-expanded pairwise graph (batch.edge_index)
  - "hyper":       operate on the hypergraph incidence (PyG HypergraphConv over (node, hyperedge))
No skip to the raw set readout, so no representation gets a structure-free shortcut.
"""
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv, GATConv, HypergraphConv
from .ops import SegmentAttentionPool, MLPHead


class GNNClassifier(nn.Module):
    def __init__(self, dim=768, hidden=256, dropout=0.3, layers=2, conv="gcn", heads=4):
        super().__init__()
        self.conv_type = conv
        self.name = {"gcn": "pairwise-gcn (clique)", "gat": "pairwise-gat (clique)",
                     "hyper": "hypergraph (ours)"}[conv]
        self.in_proj = nn.Linear(dim, hidden)
        self.convs = nn.ModuleList()
        for _ in range(layers):
            if conv == "gcn":
                self.convs.append(GCNConv(hidden, hidden))
            elif conv == "gat":
                self.convs.append(GATConv(hidden, hidden // heads, heads=heads))
            elif conv == "hyper":
                self.convs.append(HypergraphConv(hidden, hidden))
            else:
                raise ValueError(conv)
        self.norm = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(layers)])
        self.drop = nn.Dropout(dropout)
        self.pool = SegmentAttentionPool(hidden, hidden=128)
        self.head = MLPHead(hidden, hidden, dropout)

    def _struct(self, batch):
        if self.conv_type == "hyper":
            return torch.stack([batch.inc_node, batch.inc_edge])  # hyperedge incidence
        return batch.edge_index                                    # clique pairwise graph

    def forward(self, batch):
        h = torch.relu(self.in_proj(batch.node_feats))
        struct = self._struct(batch)
        for conv, norm in zip(self.convs, self.norm):
            h = norm(h + self.drop(torch.relu(conv(h, struct))))
        edge_h = self.pool(h[batch.inc_node], batch.inc_edge, batch.num_edges)
        return self.head(edge_h)
