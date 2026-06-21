"""G-HAN — Gated Heterogeneous Attention Network for contract-level graphs (rebuild).

Edge-typed, direction-aware gated message passing over a contract graph whose nodes are
interaction hyperedges + state-mutating helper nodes. Edge types encode direction so the
gate LEARNS direction-weighting rather than hard-coding caller->helper:

    0 call_forward   (interaction -> callee)
    1 call_reverse   (callee -> interaction)      # down-weightable by the gate
    2 shared_state   (symmetric; materialized both ways)
    3 shared_callee  (symmetric; materialized both ways)

Each node carries a pre-pooled D-dim embedding (from the existing AttentionPooling over its
constituent function/state/callee node-features; helpers pool function+state only). G-HAN
refines those embeddings with neighbourhood context; the per-interaction binary head then
runs on the refined interaction-node embeddings.
"""
import torch
import torch.nn as nn

EDGE_TYPES = {"call_forward": 0, "call_reverse": 1, "shared_state": 2, "shared_callee": 3}
N_EDGE_TYPES = 4


class EdgeGatedLayer(nn.Module):
    """h_v <- LayerNorm(h_v + sum_{u->v} gate(etype_uv) * msg(h_u))."""
    def __init__(self, dim, n_edge_types=N_EDGE_TYPES):
        super().__init__()
        self.msg = nn.Linear(dim, dim)
        self.gate = nn.Embedding(n_edge_types, dim)   # per-edge-type (incl. direction) gate vector
        self.norm = nn.LayerNorm(dim)
        nn.init.zeros_(self.gate.weight)              # sigmoid(0)=0.5 -> edges start half-open

    def forward(self, x, edge_index, edge_type):
        if edge_index.numel() == 0:
            return self.norm(x)
        src, dst = edge_index[0], edge_index[1]
        g = torch.sigmoid(self.gate(edge_type))       # (E, dim)
        m = g * self.msg(x[src])                       # (E, dim) gated messages
        # out-of-place index_add keeps the gradient path to x[src] intact
        # (an in-place index_add_ on a fresh zeros tensor silently severs grad-to-leaf)
        agg = torch.zeros_like(x).index_add(0, dst, m)  # sum into destinations
        return self.norm(x + agg)


class GHAN(nn.Module):
    def __init__(self, dim=768, layers=2, n_edge_types=N_EDGE_TYPES):
        super().__init__()
        self.layers = nn.ModuleList([EdgeGatedLayer(dim, n_edge_types) for _ in range(layers)])

    def forward(self, x, edge_index, edge_type):
        for layer in self.layers:
            x = layer(x, edge_index, edge_type)
        return x


def materialize_edges(edges, node_id_to_idx, device="cpu"):
    """Convert emitted edge dicts -> (edge_index[2,E], edge_type[E]).
    call edges keep their forward/reverse type; shared_* are symmetric -> emitted both ways."""
    src, dst, et = [], [], []
    for e in edges:
        s, d = node_id_to_idx[e["src"]], node_id_to_idx[e["dst"]]
        if e["etype"] == "call":
            t = EDGE_TYPES["call_forward"] if e["direction"] == "forward" else EDGE_TYPES["call_reverse"]
            src.append(s); dst.append(d); et.append(t)
        else:  # shared_state / shared_callee — symmetric
            t = EDGE_TYPES[e["etype"]]
            src += [s, d]; dst += [d, s]; et += [t, t]
    if not src:
        return (torch.zeros(2, 0, dtype=torch.long, device=device),
                torch.zeros(0, dtype=torch.long, device=device))
    return (torch.tensor([src, dst], dtype=torch.long, device=device),
            torch.tensor(et, dtype=torch.long, device=device))


class ContractGraphModel(nn.Module):
    """G-HAN propagation + per-interaction binary head (additive over the proven pooled head)."""
    def __init__(self, dim=768, hidden=256, layers=2, dropout=0.3):
        super().__init__()
        self.ghan = GHAN(dim=dim, layers=layers)
        self.head = nn.Sequential(
            nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1))

    def forward(self, node_emb, edge_index, edge_type, interaction_mask):
        h = self.ghan(node_emb, edge_index, edge_type)      # refine all nodes
        logits = self.head(h).squeeze(-1)                   # (N,)
        return logits[interaction_mask]                     # score interaction nodes only
