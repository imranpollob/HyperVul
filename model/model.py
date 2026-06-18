import sys
from pathlib import Path

import torch
import torch.nn as nn

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.models.ops import (
    LocalizationHead, build_node_types, split_nodes_by_type,
    NODE_STATE, NODE_CALLEE,
)


class AttentionPooling(nn.Module):
    """
    Computes learned attention weights over hyperedge member nodes and
    pools them into a single hyperedge vector.
    """
    def __init__(self, input_dim=768, hidden_dim=128):
        super().__init__()
        self.w_a = nn.Linear(input_dim, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, x, mask=None):
        # x shape: (B, N, input_dim)
        # mask shape: (B, N) where True/1 indicates active nodes, False/0 represents padding
        scores = self.v(torch.tanh(self.w_a(x)))  # (B, N, 1)
        scores = scores.squeeze(-1)  # (B, N)

        if mask is not None:
            # Mask out padded positions using negative infinity to make softmax 0
            scores = scores.masked_fill(~mask, -1e9)

        attn_weights = torch.softmax(scores, dim=-1)  # (B, N)
        attn_weights_unsqueezed = attn_weights.unsqueeze(-1)  # (B, N, 1)

        pooled = torch.sum(attn_weights_unsqueezed * x, dim=1)  # (B, input_dim)
        return pooled, attn_weights

class HyperedgeClassifier(nn.Module):
    """
    Pools node embeddings and feeds the pooled hyperedge embedding into a 2-layer MLP
    head for binary classification. When node-type ids are supplied, an interaction-aware
    LocalizationHead (Stage 4) adds a per-tuple excitability readout: it contributes a
    vulnerability logit (so it trains jointly with the binary loss) and, at inference,
    points at the specific (function, state, callee) tuple responsible for the flag.
    """
    def __init__(self, input_dim=768, hidden_dim=256, dropout=0.3, localize=True):
        super().__init__()
        self.pool = AttentionPooling(input_dim=input_dim, hidden_dim=128)
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )
        self.localizer = LocalizationHead(dim=input_dim, hidden=128) if localize else None
        # Learnable residual gate; the interaction logit is fused on top of the set-pool
        # logit so the proven classifier is preserved and the head is additive.
        self.loc_gate = nn.Parameter(torch.tensor(1.0)) if localize else None

    def encode(self, x, mask=None, node_types=None):
        """Returns (logits, pooled, attn_weights, localization).

        `localization` is None unless `node_types` is given, in which case it is a dict
        with the per-tuple score/attention grids and their masks.
        """
        pooled, attn_weights = self.pool(x, mask)
        logits = self.mlp(pooled)  # (B, 1)

        localization = None
        if self.localizer is not None and node_types is not None:
            func, states, state_mask, callees, callee_mask = split_nodes_by_type(x, node_types)
            scores, tuple_attn, loc_logit = self.localizer(
                func, states, callees, state_mask, callee_mask)
            logits = logits + self.loc_gate * loc_logit
            localization = {
                "scores": scores,            # (B, S, C) excitability (masked)
                "attn": tuple_attn,          # (B, S, C) normalized excitability
                "state_mask": state_mask,    # (B, S)
                "callee_mask": callee_mask,  # (B, C)
            }
        return logits, pooled, attn_weights, localization

    def forward(self, x, mask=None, node_types=None, return_localization=False):
        logits, _, attn_weights, localization = self.encode(x, mask, node_types)
        if return_localization:
            return logits, attn_weights, localization
        return logits, attn_weights


def _state_names(item):
    nf = item.get("node_features") or {}
    if nf.get("state_vars"):
        return list(nf["state_vars"].keys())
    return [s.get("name", f"state_{i}") for i, s in enumerate(item.get("state_nodes", []))]


def _callee_names(item):
    nf = item.get("node_features") or {}
    if nf.get("external_calls"):
        return [ec.get("call_text", f"callee_{i}") for i, ec in enumerate(nf["external_calls"])]
    out = []
    for i, c in enumerate(item.get("callee_nodes", [])):
        tgt = c.get("target") or c.get("target_type") or "?"
        out.append(f"{tgt}.{c.get('method', 'call')}()" if c.get("method") else f"callee_{i}")
    return out


@torch.no_grad()
def flag_tuples(model, x, mask, items, threshold=0.5, top_k=1, device=None):
    """Inference-time localization output (Stage 4 requirement 2).

    For each hyperedge predicted vulnerable (prob >= threshold), explicitly list the
    top-`k` responsible (function, state, callee) tuples ranked by excitability.

    Returns a list (one entry per item) of dicts:
        {function, vulnerable, prob, flagged_tuples: [{state, callee, excitability, score}, ...]}
    """
    model.eval()
    device = device or next(model.parameters()).device
    x = x.to(device)
    mask = mask.to(device)
    node_types = build_node_types(items, x.shape[1], device=device)

    logits, _, _, loc = model.encode(x, mask, node_types)
    probs = torch.sigmoid(logits.squeeze(-1)).cpu()

    results = []
    for b, item in enumerate(items):
        prob = float(probs[b])
        entry = {
            "function": item.get("function") or item.get("ast_function"),
            "contract": item.get("contract"),
            "vulnerable": prob >= threshold,
            "prob": prob,
            "flagged_tuples": [],
        }
        if entry["vulnerable"] and loc is not None:
            s_n = int(loc["state_mask"][b].sum().item())
            c_n = int(loc["callee_mask"][b].sum().item())
            if s_n > 0 and c_n > 0:
                grid = loc["attn"][b, :s_n, :c_n]              # (s_n, c_n) excitability
                raw = loc["scores"][b, :s_n, :c_n]
                state_names = _state_names(item)
                callee_names = _callee_names(item)
                k = min(top_k, s_n * c_n)
                flat_idx = torch.topk(grid.reshape(-1), k).indices
                for fi in flat_idx.tolist():
                    j, kk = divmod(fi, c_n)
                    entry["flagged_tuples"].append({
                        "function": entry["function"],
                        "state": state_names[j] if j < len(state_names) else f"state_{j}",
                        "callee": callee_names[kk] if kk < len(callee_names) else f"callee_{kk}",
                        "excitability": float(grid[j, kk]),
                        "score": float(raw[j, kk]),
                    })
        results.append(entry)
    return results
