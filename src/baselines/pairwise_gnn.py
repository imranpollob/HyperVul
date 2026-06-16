"""Pairwise-edge baselines: what the thesis argues against.

Clique expansion replaces each hyperedge with pairwise edges among ALL its member
nodes, turning the hypergraph into an ordinary graph, then runs a standard GNN
(GCN or GAT). The n-ary interaction is thus fragmented into independent dyads and
spurious all-pairs connectivity. Per-hyperedge prediction = attention-pool of its
member node embeddings -> MLP (same head as the hypergraph model, for fairness).

`batch.edge_index` (the clique expansion) is precomputed by the harness collate.
"""
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv, GATConv
from src.models.ops import SegmentAttentionPool, MLPHead


class PairwiseGNN(nn.Module):
    def __init__(self, dim=768, hidden=256, dropout=0.3, layers=2, conv="gcn", heads=4):
        super().__init__()
        self.name = f"pairwise-{conv} (clique)"
        self.in_proj = nn.Linear(dim, hidden)
        self.convs = nn.ModuleList()
        for _ in range(layers):
            if conv == "gcn":
                self.convs.append(GCNConv(hidden, hidden))
            elif conv == "gat":
                self.convs.append(GATConv(hidden, hidden // heads, heads=heads))
            else:
                raise ValueError(conv)
        self.norm = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(layers)])
        self.drop = nn.Dropout(dropout)
        self.pool = SegmentAttentionPool(hidden, hidden=128)
        self.head = MLPHead(hidden, hidden, dropout)

    def forward(self, batch):
        h = torch.relu(self.in_proj(batch.node_feats))
        ei = batch.edge_index
        for conv, norm in zip(self.convs, self.norm):
            h = norm(h + self.drop(torch.relu(conv(h, ei))))
        edge_h = self.pool(h[batch.inc_node], batch.inc_edge, batch.num_edges)
        return self.head(edge_h)
