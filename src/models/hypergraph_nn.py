"""HypergraphNN (ours): two-stage hyperedge message passing.

Within a contract, hyperedges that touch the same state variable / callee share a
node. We propagate context across those shared nodes so a multi-step interaction
(funcA writes X; funcB reads X after an external call) is informed by its partners:

  for L layers:
    edge_h  = attn_pool(node_h over members)        # node  -> hyperedge
    node_msg = mean(edge_h over incident edges)      # hyperedge -> node
    node_h  = LayerNorm(node_h + W node_msg)         # residual update
  logit_e = MLP(edge_h_final)

This is the n-ary relation a pairwise (clique/star) expansion cannot represent
without fragmenting the joint co-occurrence into independent dyads.
"""
import torch
import torch.nn as nn
from torch_geometric.utils import scatter
from .ops import SegmentAttentionPool, MLPHead


class HypergraphNN(nn.Module):
    name = "hypergraph (ours)"

    def __init__(self, dim=768, hidden=256, dropout=0.3, layers=2, use_skip=True, alpha=0.1):
        super().__init__()
        self.layers = layers
        self.in_proj = nn.Linear(dim, hidden)
        
        # Specialized Attention-based Hyperedge Message Passing
        self.n2e = nn.ModuleList([SegmentAttentionPool(hidden, hidden=128) for _ in range(layers)])
        self.e2n = nn.ModuleList([nn.Linear(hidden, hidden) for _ in range(layers)])
        
        # Anti-oversmoothing Regularization
        self.norm = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(layers)])
        self.drop = nn.Dropout(dropout)
        
        # Specialized Attention Readout
        self.final_pool = SegmentAttentionPool(hidden, hidden=128)
        self.head = MLPHead(hidden, hidden, dropout)

    def forward(self, batch):
        inc_node, inc_edge = batch.inc_node, batch.inc_edge
        node_h = torch.relu(self.in_proj(batch.node_feats))
        
        for l in range(self.layers):
            edge_h = self.n2e[l](node_h[inc_node], inc_edge, batch.num_edges)   # node -> edge
            node_msg = scatter(edge_h[inc_edge], inc_node, dim=0, dim_size=batch.num_nodes, reduce="mean")
            
            # Residual connection with LayerNorm
            msg = self.drop(torch.relu(self.e2n[l](node_msg)))
            node_h = self.norm[l](node_h + msg)
            
        edge_ctx = self.final_pool(node_h[inc_node], inc_edge, batch.num_edges)
        return self.head(edge_ctx)
