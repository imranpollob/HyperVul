#!/usr/bin/env python3
"""Propagation sanity check on the EXPANDED schema (Phase-3 bar, re-applied).

Tiny synthetic contract graph with a known CALL edge (helper->interaction) and a known
SHARED-DATA edge (interaction<->interaction), plus disconnected controls. Verifies via
GRADIENT + ACTIVATION that a signal at a source node reaches a CONNECTED interaction node's
*prediction logit* (the real per-interaction head), and does NOT reach disconnected controls.

Probe = the model's actual logit head (Linear). NB: do not probe sum(LayerNorm(.)) — that
is analytically 0 (LayerNorm output is mean-centred), which only measures float noise.
"""
import sys
from pathlib import Path
import torch
sys.path.append(str(Path(__file__).resolve().parents[1]))
from model.ghan import ContractGraphModel, materialize_edges

torch.manual_seed(0)
DIM = 32
# nodes: 0=I0(int) 1=H0(helper) 2=I1(int) 3=I2(ctrl int) 4=Hiso(ctrl helper)
idx = {"I0": 0, "H0": 1, "I1": 2, "I2": 3, "Hiso": 4}
interaction_mask = torch.tensor([True, False, True, True, False])
int_order = ["I0", "I1", "I2"]                      # nodes selected by the mask, in order
int_pos = {n: i for i, n in enumerate(int_order)}

edges = [   # call I0<->H0 (fwd I0->H0, rev H0->I0); shared_state I0<->I1; I2 & Hiso isolated
    {"src": "I0", "dst": "H0", "etype": "call", "direction": "forward"},
    {"src": "H0", "dst": "I0", "etype": "call", "direction": "reverse"},
    {"src": "I0", "dst": "I1", "etype": "shared_state", "direction": "undirected"},
]
edge_index, edge_type = materialize_edges(edges, idx)
model = ContractGraphModel(dim=DIM, hidden=16, layers=2, dropout=0.0).eval()

def grads_logit_wrt(int_name, sources):
    """grad-norm of the logit of interaction `int_name` w.r.t. each source node input."""
    x = torch.randn(5, DIM, requires_grad=True)
    logits = model(x, edge_index, edge_type, interaction_mask)   # (3,) for I0,I1,I2
    logits[int_pos[int_name]].backward()
    return [x.grad[idx[s]].norm().item() for s in sources]

print("=== PROPAGATION SANITY CHECK (expanded schema, probed at the logit head) ===\n")

# Test 1 — CALL edge: helper H0 must reach interaction I0's logit (via H0->I0 reverse edge)
g_self, g_call, g_ctrl = grads_logit_wrt("I0", ["I0", "H0", "Hiso"])
r1 = g_call / g_self if g_self else 0.0
print(f"[CALL  ] d(logit_I0)/d(H0)  = {g_call:.4e}    self d/d(I0) = {g_self:.4e}    ratio = {r1:.3f}")
print(f"[control] d(logit_I0)/d(Hiso) = {g_ctrl:.4e}    (disconnected -> exactly 0)")
t1 = g_call > 0 and g_ctrl == 0.0 and r1 > 0.01

# Test 2 — SHARED-DATA edge: interaction I0 must reach interaction I1's logit
g_self2, g_shared, g_ctrl2 = grads_logit_wrt("I1", ["I1", "I0", "I2"])
r2 = g_shared / g_self2 if g_self2 else 0.0
print(f"\n[SHARED] d(logit_I1)/d(I0)  = {g_shared:.4e}    self d/d(I1) = {g_self2:.4e}    ratio = {r2:.3f}")
print(f"[control] d(logit_I1)/d(I2)  = {g_ctrl2:.4e}    (disconnected -> exactly 0)")
t2 = g_shared > 0 and g_ctrl2 == 0.0 and r2 > 0.01

# Test 3 — ACTIVATION: perturbing H0 shifts I0's logit; perturbing isolated Hiso shifts I2's by 0
x = torch.randn(5, DIM)
base = model(x, edge_index, edge_type, interaction_mask)
x2 = x.clone(); x2[idx["H0"]] += 5.0
d_I0 = (model(x2, edge_index, edge_type, interaction_mask)[int_pos["I0"]] - base[int_pos["I0"]]).abs().item()
x3 = x.clone(); x3[idx["Hiso"]] += 5.0
d_I2 = (model(x3, edge_index, edge_type, interaction_mask)[int_pos["I2"]] - base[int_pos["I2"]]).abs().item()
print(f"\n[ACTIVATION] |logit_I0(H0+5) - logit_I0| = {d_I0:.4e}    (expect > 0)")
print(f"[control   ] |logit_I2(Hiso+5) - logit_I2| = {d_I2:.4e}    (expect 0)")
t3 = d_I0 > 1e-4 and d_I2 == 0.0

# Test 4 — direction gate distinct per direction
fwd, rev = model.ghan.layers[0].gate.weight[0], model.ghan.layers[0].gate.weight[1]
print(f"\n[GATE] call_forward vs call_reverse are separate learnable params: "
      f"{'YES' if fwd.data_ptr() != rev.data_ptr() else 'NO'}")

print("\n=== RESULT ===")
for name, ok in [("Test 1 call-edge -> logit", t1), ("Test 2 shared-data -> logit", t2),
                 ("Test 3 activation", t3)]:
    print(f"  {name:30s} {'PASS' if ok else 'FAIL'}")
print(f"  OVERALL: {'PASS' if (t1 and t2 and t3) else 'FAIL'}")
