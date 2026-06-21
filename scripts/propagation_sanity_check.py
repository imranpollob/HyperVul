#!/usr/bin/env python3
"""Propagation sanity check on the POOLED node-feature pipeline (regression check).

Now two composed stages: per-node AttentionPooling(member set) -> G-HAN propagation.
Verifies a signal injected at a node's MEMBER embeddings reaches a CONNECTED interaction
node's logit (gradient + activation) through both stages, and not through disconnected
controls. Confirms the node-feature fix didn't break the edge connectivity already verified.
"""
import sys
from pathlib import Path
import torch
sys.path.append(str(Path(__file__).resolve().parents[1]))
from model.ghan import PooledContractGraphModel, materialize_edges

torch.manual_seed(0)
DIM, M = 32, 3                                  # 3 members per node (func+state+callee-like)
idx = {"I0": 0, "H0": 1, "I1": 2, "I2": 3, "Hiso": 4}
interaction_mask = torch.tensor([True, False, True, True, False])
int_order = ["I0", "I1", "I2"]; int_pos = {n: i for i, n in enumerate(int_order)}
edges = [
    {"src": "I0", "dst": "H0", "etype": "call", "direction": "forward"},
    {"src": "H0", "dst": "I0", "etype": "call", "direction": "reverse"},
    {"src": "I0", "dst": "I1", "etype": "shared_state", "direction": "undirected"},
]
edge_index, edge_type = materialize_edges(edges, idx)
member_mask = torch.ones(5, M, dtype=torch.bool)
model = PooledContractGraphModel(dim=DIM, hidden=16, layers=2, dropout=0.0).eval()

def grads_logit_wrt(int_name, sources):
    members = torch.randn(5, M, DIM, requires_grad=True)
    logits = model(members, member_mask, edge_index, edge_type, interaction_mask)
    logits[int_pos[int_name]].backward()
    return [members.grad[idx[s]].norm().item() for s in sources]   # grad over the node's member block

print("=== PROPAGATION SANITY CHECK (POOLED pipeline: AttentionPooling -> G-HAN) ===\n")
g_self, g_call, g_ctrl = grads_logit_wrt("I0", ["I0", "H0", "Hiso"])
r1 = g_call / g_self if g_self else 0.0
print(f"[CALL  ] d(logit_I0)/d(H0 members)  = {g_call:.4e}   self = {g_self:.4e}   ratio = {r1:.3f}")
print(f"[control] d(logit_I0)/d(Hiso members) = {g_ctrl:.4e}   (disconnected -> exactly 0)")
t1 = g_call > 0 and g_ctrl == 0.0 and r1 > 0.01

g_self2, g_shared, g_ctrl2 = grads_logit_wrt("I1", ["I1", "I0", "I2"])
r2 = g_shared / g_self2 if g_self2 else 0.0
print(f"\n[SHARED] d(logit_I1)/d(I0 members)  = {g_shared:.4e}   self = {g_self2:.4e}   ratio = {r2:.3f}")
print(f"[control] d(logit_I1)/d(I2 members)  = {g_ctrl2:.4e}   (disconnected -> exactly 0)")
t2 = g_shared > 0 and g_ctrl2 == 0.0 and r2 > 0.01

members = torch.randn(5, M, DIM)
base = model(members, member_mask, edge_index, edge_type, interaction_mask)
m2 = members.clone(); m2[idx["H0"]] += 5.0
d_I0 = (model(m2, member_mask, edge_index, edge_type, interaction_mask)[int_pos["I0"]] - base[int_pos["I0"]]).abs().item()
m3 = members.clone(); m3[idx["Hiso"]] += 5.0
d_I2 = (model(m3, member_mask, edge_index, edge_type, interaction_mask)[int_pos["I2"]] - base[int_pos["I2"]]).abs().item()
print(f"\n[ACTIVATION] |logit_I0(H0 members+5) - logit_I0| = {d_I0:.4e}  (expect > 0)")
print(f"[control   ] |logit_I2(Hiso members+5) - logit_I2| = {d_I2:.4e}  (expect 0)")
t3 = d_I0 > 1e-4 and d_I2 == 0.0

fwd, rev = model.ghan.layers[0].gate.weight[0], model.ghan.layers[0].gate.weight[1]
print(f"\n[GATE] call_forward vs call_reverse separate params: {'YES' if fwd.data_ptr()!=rev.data_ptr() else 'NO'}")
print("\n=== RESULT ===")
for name, ok in [("Test 1 call-edge -> logit", t1), ("Test 2 shared-data -> logit", t2),
                 ("Test 3 activation", t3)]:
    print(f"  {name:30s} {'PASS' if ok else 'FAIL'}")
print(f"  OVERALL: {'PASS' if (t1 and t2 and t3) else 'FAIL'}")
