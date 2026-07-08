"""Shared building blocks for the HyperVul representation model zoo."""
import torch
import torch.nn as nn
import torch.nn.functional as F
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


# ---------------------------------------------------------------------------
# Stage 4 — Fine-grained interaction localization
# ---------------------------------------------------------------------------
# Node-type convention inside a padded hyperedge tensor (B, N, dim):
#   0 = function hub, 1 = state node, 2 = callee node, -1 = padding.
# This matches the dataset node order [func] + state_vars + callees.
NODE_FUNC, NODE_STATE, NODE_CALLEE, NODE_PAD = 0, 1, 2, -1


def build_node_types(items, max_len: int, device=None):
    """Reconstruct (B, max_len) node-type ids from item metadata, aligned with the
    [func] + state_vars + callees node order and right-padding used by collate_fn.

    Supports both the SmartBERT feature schema (node_features.state_vars / external_calls)
    and the Stage-2 bottleneck schema (state_nodes / callee_nodes)."""
    rows = []
    for it in items:
        nf = it.get("node_features") or {}
        if nf:
            n_state = len(nf.get("state_vars", {}) or {})
            n_callee = len(nf.get("external_calls", []) or [])
        else:
            n_state = len(it.get("state_nodes", []) or [])
            n_callee = len(it.get("callee_nodes", []) or [])
        t = [NODE_FUNC] + [NODE_STATE] * n_state + [NODE_CALLEE] * n_callee
        t = t[:max_len] + [NODE_PAD] * (max_len - len(t))
        rows.append(t)
    return torch.tensor(rows, dtype=torch.long, device=device)


def split_nodes_by_type(x, node_types):
    """Scatter a flat padded node tensor into per-type tensors.

    Returns
    -------
    func        : (B, dim)            the function-hub embedding (NODE_FUNC).
    states      : (B, Smax, dim)      padded state-node embeddings.
    state_mask  : (B, Smax) bool      valid state nodes.
    callees     : (B, Cmax, dim)      padded callee-node embeddings.
    callee_mask : (B, Cmax) bool      valid callee nodes.
    """
    B, N, D = x.shape
    device = x.device
    is_state = node_types == NODE_STATE
    is_callee = node_types == NODE_CALLEE

    Smax = max(int(is_state.sum(dim=1).max().item()), 1) if B else 1
    Cmax = max(int(is_callee.sum(dim=1).max().item()), 1) if B else 1

    func = x.new_zeros(B, D)
    states = x.new_zeros(B, Smax, D)
    callees = x.new_zeros(B, Cmax, D)
    state_mask = torch.zeros(B, Smax, dtype=torch.bool, device=device)
    callee_mask = torch.zeros(B, Cmax, dtype=torch.bool, device=device)

    for b in range(B):
        f_idx = (node_types[b] == NODE_FUNC).nonzero(as_tuple=True)[0]
        if len(f_idx):
            func[b] = x[b, f_idx[0]]
        s_idx = is_state[b].nonzero(as_tuple=True)[0]
        if len(s_idx):
            states[b, :len(s_idx)] = x[b, s_idx]
            state_mask[b, :len(s_idx)] = True
        c_idx = is_callee[b].nonzero(as_tuple=True)[0]
        if len(c_idx):
            callees[b, :len(c_idx)] = x[b, c_idx]
            callee_mask[b, :len(c_idx)] = True

    return func, states, state_mask, callees, callee_mask


class LocalizationHead(nn.Module):
    """Interaction-aware readout that scores every (function-hub, state-node, callee-node)
    tuple for 'excitability' — how strongly that specific 3-way interaction drives the
    hyperedge's vulnerability.

    It produces (a) a per-tuple score grid used at inference to point at the responsible
    nodes, and (b) an attention-pooled interaction context that yields a vulnerability
    logit, so the head is trained jointly by the binary objective (no tuple-level labels
    needed — it is weakly supervised attribution).
    """

    def __init__(self, dim=768, hidden=128):
        super().__init__()
        self.wf = nn.Linear(dim, hidden)
        self.ws = nn.Linear(dim, hidden)
        self.wc = nn.Linear(dim, hidden)
        self.v = nn.Linear(hidden, 1, bias=False)     # tuple excitability score
        self.out = nn.Linear(hidden, 1)               # interaction-context -> logit

    def forward(self, func, states, callees, state_mask, callee_mask):
        B, S, _ = states.shape
        C = callees.shape[1]

        # factorized additive interaction: h_{b,j,k} = tanh(Wf f + Ws s_j + Wc c_k)
        h = torch.tanh(
            self.wf(func)[:, None, None, :]
            + self.ws(states)[:, :, None, :]
            + self.wc(callees)[:, None, :, :]
        )                                              # (B, S, C, H)
        scores = self.v(h).squeeze(-1)                 # (B, S, C)

        valid = state_mask[:, :, None] & callee_mask[:, None, :]   # (B, S, C)
        neg = torch.finfo(scores.dtype).min
        scores = scores.masked_fill(~valid, neg)

        flat = scores.view(B, -1)
        no_valid = ~valid.view(B, -1).any(dim=1)       # hyperedges with no func+state+callee triple
        flat = flat.masked_fill(no_valid[:, None], 0.0)            # avoid all -inf softmax row
        attn = torch.softmax(flat, dim=-1).view(B, S, C) * valid   # (B, S, C), zero on invalid

        ctx = (attn[..., None] * h).sum(dim=(1, 2))    # (B, H) attention-pooled interaction
        logit = self.out(ctx)                          # (B, 1)
        return scores, attn, logit


class ProjectionHead(nn.Module):
    """Project a pooled hyperedge embedding to the unit-sphere space where the
    Supervised Contrastive Loss lives (Khosla et al. 2020). The classification MLP
    keeps operating on the raw pooled embedding; SCL operates on this normalized
    projection, never on the logits."""

    def __init__(self, in_dim=768, hidden=256, out_dim=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x):
        return F.normalize(self.net(x), dim=-1)          # (B, out_dim), L2-normalized


class SupConLoss(nn.Module):
    """Supervised Contrastive Loss (Khosla et al. 2020), single view per sample.

    Pulls same-label hyperedge projections together and pushes different-label ones
    apart. `weights` apply a per-anchor multiplier so we can over-penalize the anchors
    we most need clustered correctly — here, clean (label=0) interactions that contain
    external calls, the dominant source of out-of-distribution false positives.

    Args
    ----
    features : (B, D) L2-normalized projections.
    labels   : (B,) binary/integer labels.
    weights  : (B,) optional per-anchor weights (defaults to all-ones).
    """

    def __init__(self, temperature: float = 0.1):
        super().__init__()
        self.temperature = temperature

    def forward(self, features, labels, weights=None):
        device = features.device
        B = features.shape[0]
        if B < 2:
            return features.sum() * 0.0                  # nothing to contrast

        labels = labels.contiguous().view(-1, 1)
        same = torch.eq(labels, labels.T).float().to(device)        # (B, B) same-class
        self_mask = torch.eye(B, device=device)
        pos_mask = same * (1.0 - self_mask)                          # positives, excl. self

        # cosine-similarity logits (features are unit norm) with stability shift
        logits = torch.matmul(features, features.T) / self.temperature
        logits = logits - logits.max(dim=1, keepdim=True)[0].detach()

        exp_logits = torch.exp(logits) * (1.0 - self_mask)           # exclude self from denom
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-12)

        pos_per_anchor = pos_mask.sum(dim=1)
        valid = pos_per_anchor > 0                                   # anchors with >=1 positive
        if valid.sum() == 0:
            return features.sum() * 0.0

        mean_log_prob_pos = (pos_mask * log_prob).sum(dim=1)[valid] / pos_per_anchor[valid]
        loss_per_anchor = -mean_log_prob_pos                        # (n_valid,)

        if weights is not None:
            w = weights.to(device)[valid]
            return (loss_per_anchor * w).sum() / (w.sum() + 1e-12)
        return loss_per_anchor.mean()
