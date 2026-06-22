#!/usr/bin/env python3
"""Option B ratio sweep on the 0-layer pooled model. Targets 10:1 / 20:1 / 30:1 keep some
all-negative graphs in rotation (whole graphs only; a fresh rotating window each epoch for
coverage). 3 seeds each. Reports ROC-AUC + PR-AUC next to the two reference points."""
import json, sys
from pathlib import Path
import numpy as np, torch
from sklearn.metrics import average_precision_score, roc_auc_score
ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
from model.ghan import PooledContractGraphModel
from model.contract_graph_data import (load_graphs, node_embeddings, member_embeddings,
                                        graph_pooled_tensors, batch_pooled, option_a_pos_weight)

dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FUNC, MEMB = node_embeddings(), member_embeddings()
GR = {s: load_graphs(s) for s in ["train", "val", "test"]}
DATA = {s: [graph_pooled_tensors(g, FUNC, MEMB) for g in GR[s]] for s in ["train", "val", "test"]}
PW = torch.tensor([option_a_pos_weight("sqrt")], device=dev)
print(f"precomputed train={len(DATA['train'])} val={len(DATA['val'])} test={len(DATA['test'])}", flush=True)

with_pos = [i for i, g in enumerate(GR["train"]) if g["n_pos"] > 0]
all_neg = [i for i, g in enumerate(GR["train"]) if g["n_pos"] == 0]
nneg = [g["n_neg"] for g in GR["train"]]
pos_int = sum(GR["train"][i]["n_pos"] for i in with_pos)
base_neg = sum(GR["train"][i]["n_neg"] for i in with_pos)

def lossfn(lo, L): return torch.nn.functional.binary_cross_entropy_with_logits(lo, L, pos_weight=PW)
def eval_probs(model, data):
    model.eval(); ps, ls = [], []
    with torch.no_grad():
        for g in data:
            m, mm, ei, et, im, L = batch_pooled([g], device=dev)
            ps.append(torch.sigmoid(model(m, mm, ei, et, im)).cpu()); ls.append(L.cpu())
    return torch.cat(ps).numpy(), torch.cat(ls).numpy()

def epoch_indices(target, cursor):
    budget = max(0, target * pos_int - base_neg)
    chosen, acc, n = [], 0, len(all_neg)
    while acc < budget and len(chosen) < n:
        gi = all_neg[cursor[0] % n]; cursor[0] += 1; chosen.append(gi); acc += nneg[gi]
    return with_pos + chosen

def run(target, seed, epochs=60, lr=1e-3, bs=64):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PooledContractGraphModel(layers=0).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    best_ap, best_state, cursor = -1, None, [0]
    for ep in range(epochs):
        model.train()
        idxs = epoch_indices(target, cursor); np.random.shuffle(idxs)
        for i in range(0, len(idxs), bs):
            gs = [DATA["train"][j] for j in idxs[i:i+bs]]
            m, mm, EI, ET, M, L = batch_pooled(gs, device=dev)
            loss = lossfn(model(m, mm, EI, ET, M), L)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        vp, vl = eval_probs(model, DATA["val"]); ap = average_precision_score(vl, vp)
        if ap > best_ap: best_ap, best_state = ap, {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    tp, tl = eval_probs(model, DATA["test"])
    return roc_auc_score(tl, tp), average_precision_score(tl, tp)

res = {}
for target in [10, 20, 30]:
    b = max(0, target * pos_int - base_neg)
    rocs, prs = [], []
    for s in [42, 43, 44]:
        roc, pr = run(target, s); rocs.append(roc); prs.append(pr)
        print(f"[target={target}:1 seed={s}] ROC={roc:.3f} PR={pr:.3f}", flush=True)
    res[target] = (np.mean(rocs), np.std(rocs), np.mean(prs), np.std(prs))
    print(f"  -> target {target}:1 (extra-neg budget {b}): ROC {res[target][0]:.3f}±{res[target][1]:.3f} "
          f"PR {res[target][2]:.3f}±{res[target][3]:.3f}", flush=True)

print("\n=== OPTION B RATIO SWEEP (0-layer pooled, full-pool test) ===")
print(f"{'config':28s} {'ROC-AUC':>14s} {'PR-AUC':>14s}")
print(f"{'all data (no balancing)':28s} {'0.808':>14s} {'0.342':>14s}")
print(f"{'3:1 (positive-only graphs)':28s} {'0.835':>14s} {'0.229':>14s}")
for t in [10, 20, 30]:
    rm, rs, pm, ps = res[t]
    print(f"{(str(t)+':1'):28s} {rm:.3f}±{rs:.3f}   {pm:.3f}±{ps:.3f}")
json.dump({str(t): res[t] for t in res}, open(ROOT / "scratch" / "optionb_sweep.json", "w"), indent=1)
print("DONE", flush=True)
