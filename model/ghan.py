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


class APPNPLayer(nn.Module):
    """
    APPNP propagation step blending gated message passing with the root feature x0:
      x^{(k+1)} = (1 - alpha) * Propagate(x^{(k)}) + alpha * x^{(0)}
    """
    def __init__(self, dim, alpha=0.1, n_edge_types=N_EDGE_TYPES):
        super().__init__()
        self.alpha = alpha
        self.msg = nn.Linear(dim, dim)
        self.gate = nn.Embedding(n_edge_types, dim)
        self.norm = nn.LayerNorm(dim)
        nn.init.zeros_(self.gate.weight)

    def forward(self, x, x0, edge_index, edge_type):
        if edge_index.numel() == 0:
            return (1.0 - self.alpha) * self.norm(x) + self.alpha * x0
        src, dst = edge_index[0], edge_index[1]
        g = torch.sigmoid(self.gate(edge_type))       # (E, dim)
        m = g * self.msg(x[src])                       # (E, dim) gated messages
        agg = torch.zeros_like(x).index_add(0, dst, m)  # sum into destinations
        prop = self.norm(x + agg)
        return (1.0 - self.alpha) * prop + self.alpha * x0


class APPNP(nn.Module):
    def __init__(self, dim=768, layers=2, alpha=0.1, n_edge_types=N_EDGE_TYPES):
        super().__init__()
        self.layers = nn.ModuleList([APPNPLayer(dim, alpha, n_edge_types) for _ in range(layers)])

    def forward(self, x, edge_index, edge_type):
        x0 = x
        for layer in self.layers:
            x = layer(x, x0, edge_index, edge_type)
        return x


class GatedResidualLayer(nn.Module):
    """Propagation blended into the node's own pooled feature by a LEARNABLE gate,
    initialized near zero so the model starts equivalent to the 0-layer (no-propagation)
    config and must *learn* to open the gate if propagation helps.

        x' = x + alpha * sum_{u->v} msg(x_u)        (no LayerNorm -> identity at init)

    per_type=False : single global scalar alpha.
    per_type=True  : separate alpha per {call, shared_state, shared_callee}
                     (call_forward/call_reverse share the 'call' gate)."""
    def __init__(self, dim, per_type=False, init_blend=-5.0):
        super().__init__()
        self.msg = nn.Linear(dim, dim)
        self.per_type = per_type
        if per_type:
            self.blend = nn.Parameter(torch.full((3,), init_blend))
            self.register_buffer("group", torch.tensor([0, 0, 1, 2]))  # type id -> gate group
        else:
            self.blend = nn.Parameter(torch.tensor(init_blend))

    def forward(self, x, edge_index, edge_type):
        if edge_index.numel() == 0:
            return x
        src, dst = edge_index[0], edge_index[1]
        m = self.msg(x[src])
        if self.per_type:
            alpha = torch.sigmoid(self.blend)[self.group[edge_type]].unsqueeze(-1)  # (E,1)
            agg = torch.zeros_like(x).index_add(0, dst, m * alpha)
            return x + agg
        agg = torch.zeros_like(x).index_add(0, dst, m)
        return x + torch.sigmoid(self.blend) * agg


class GatedResidualGHAN(nn.Module):
    def __init__(self, dim=768, layers=1, per_type=False):
        super().__init__()
        self.layers = nn.ModuleList([GatedResidualLayer(dim, per_type) for _ in range(layers)])

    def forward(self, x, edge_index, edge_type):
        for layer in self.layers:
            x = layer(x, edge_index, edge_type)
        return x


class PooledGatedModel(nn.Module):
    """Pooled node representation -> gated-residual propagation -> per-interaction head."""
    def __init__(self, dim=768, hidden=256, layers=1, dropout=0.3, per_type=False, pool_hidden=128):
        super().__init__()
        from model.model import AttentionPooling
        self.pool = AttentionPooling(input_dim=dim, hidden_dim=pool_hidden)
        self.ghan = GatedResidualGHAN(dim, layers, per_type)
        self.head = nn.Sequential(
            nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1))

    def forward(self, members, member_mask, edge_index, edge_type, interaction_mask):
        node_feat, _ = self.pool(members, member_mask)
        h = self.ghan(node_feat, edge_index, edge_type)
        return self.head(h).squeeze(-1)[interaction_mask]

    def gate_values(self):
        return [torch.sigmoid(l.blend).detach().cpu().tolist() for l in self.ghan.layers]


class MoEHead(nn.Module):
    """Regime-aware mixture-of-experts head: a soft router conditioned on the per-interaction
    security_context vector mixes N expert MLPs over the pooled node embedding. Load-balancing
    regularizer (importance^2, minimized at uniform usage) prevents expert collapse."""
    def __init__(self, dim=768, sec_dim=8, n_experts=4, hidden=256, dropout=0.3):
        super().__init__()
        self.router = nn.Linear(sec_dim, n_experts)
        self.experts = nn.ModuleList([
            nn.Sequential(nn.Linear(dim, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1))
            for _ in range(n_experts)])
        self.n_experts = n_experts

    def forward(self, x, sec):
        gate = torch.softmax(self.router(sec), dim=-1)        # (N, E)
        ex = torch.cat([e(x) for e in self.experts], dim=-1)  # (N, E)
        logit = (gate * ex).sum(dim=-1)                       # (N,)
        importance = gate.mean(dim=0)                         # (E,)  mean routing mass per expert
        aux = self.n_experts * (importance ** 2).sum()        # min = 1.0 at uniform usage
        return logit, aux, importance.detach()


class PooledMoEModel(nn.Module):
    """0-layer pooled representation (propagation closed) + regime-aware MoE head."""
    def __init__(self, dim=768, sec_dim=8, n_experts=4, hidden=256, dropout=0.3, pool_hidden=128):
        super().__init__()
        from model.model import AttentionPooling
        self.pool = AttentionPooling(input_dim=dim, hidden_dim=pool_hidden)
        self.moe = MoEHead(dim, sec_dim, n_experts, hidden, dropout)

    def forward(self, members, member_mask, sec, interaction_mask):
        node_feat, _ = self.pool(members, member_mask)        # (N, dim)
        return self.moe(node_feat[interaction_mask], sec)     # (logit, aux, importance)


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


class PooledContractGraphModel(nn.Module):
    """Two composed stages: (1) per-node Sequence-aware / Attention pooling over the node's member set
    {function, state-vars, callees} -> one node vector; (2) G-HAN / APPNP cross-node propagation
    on top of those pooled vectors -> head."""
    def __init__(self, dim=768, hidden=256, layers=2, dropout=0.3, pool_hidden=128,
                 pool_type="sequence", propagation="appnp", appnp_alpha=0.1, sec_dim=32):
        super().__init__()
        from model.model import AttentionPooling, SequenceAwarePooling
        self.pool_type = pool_type.lower()
        if self.pool_type == "sequence":
            self.pool = SequenceAwarePooling(input_dim=dim, hidden_dim=pool_hidden)
        else:
            self.pool = AttentionPooling(input_dim=dim, hidden_dim=pool_hidden)
            
        self.sec_dim = sec_dim
        if sec_dim > 0:
            self.sec_proj = nn.Linear(8, sec_dim)
            gnn_dim = dim + sec_dim
        else:
            gnn_dim = dim
            
        self.propagation = propagation.lower()
        if self.propagation == "appnp":
            self.ghan = APPNP(dim=gnn_dim, layers=layers, alpha=appnp_alpha)
        else:
            self.ghan = GHAN(dim=gnn_dim, layers=layers)
            
        self.head = nn.Sequential(
            nn.Linear(gnn_dim, hidden), nn.ReLU(), nn.Dropout(dropout), nn.Linear(hidden, 1))

    def forward(self, members, member_mask, edge_index, edge_type, interaction_mask, sec=None):
        # members: (N, Mmax, dim)  member_mask: (N, Mmax) bool
        node_feat, _ = self.pool(members, member_mask)      # (N, dim)
        if self.sec_dim > 0 and sec is not None:
            s_proj = self.sec_proj(sec)                     # (N, sec_dim)
            node_feat = torch.cat([node_feat, s_proj], dim=-1) # (N, dim + sec_dim)
        h = self.ghan(node_feat, edge_index, edge_type)     # (N, gnn_dim)
        logits = self.head(h).squeeze(-1)
        return logits[interaction_mask]
