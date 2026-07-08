#!/usr/bin/env python3
"""G-HAN propagation-depth ablation (0 / 1 / 2 layers) on the fixed pooled pipeline.

Same pooled representation, same sqrt weighting, same full-pool test (41p/732n), 3 seeds
each. 0 layers = pooled node representation only (no cross-node propagation) — the control
for whether propagation helps or hurts. Reports ROC-AUC + PR-AUC side by side.
"""
import json, sys
from pathlib import Path
import numpy as np, torch
from sklearn.metrics import average_precision_score, roc_auc_score
ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
from model.ghan import PooledContractGraphModel
from model.contract_graph_data import (load_graphs, node_embeddings, member_embeddings,
                                        graph_pooled_tensors, batch_pooled, option_a_pos_weight)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FUNC, MEMB = node_embeddings(), member_embeddings()
DATA = {s: [graph_pooled_tensors(g, FUNC, MEMB) for g in load_graphs(s)] for s in ["train", "val", "test"]}
print(f"precomputed: train={len(DATA['train'])} val={len(DATA['val'])} test={len(DATA['test'])}", flush=True)

def eval_split(model, data):
    model.eval(); probs, labs = [], []
    with torch.no_grad():
        for g in data:
            members, mmask, ei, et, imask, L = batch_pooled([g], device=device)
            probs.append(torch.sigmoid(model(members, mmask, ei, et, imask)).cpu()); labs.append(L.cpu())
    return torch.cat(probs).numpy(), torch.cat(labs).numpy()

def run(layers, seed, epochs=60, lr=1e-3, bs=64):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PooledContractGraphModel(dim=768, hidden=256, layers=layers, dropout=0.3).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    lossfn = torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor([option_a_pos_weight("sqrt")], device=device))
    best_ap, best_state = -1, None
    order = list(range(len(DATA["train"])))
    for ep in range(epochs):
        model.train(); np.random.shuffle(order)
        for i in range(0, len(order), bs):
            gs = [DATA["train"][j] for j in order[i:i+bs]]
            members, mmask, EI, ET, M, L = batch_pooled(gs, device=device)
            loss = lossfn(model(members, mmask, EI, ET, M), L)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        vp, vl = eval_split(model, DATA["val"]); ap = average_precision_score(vl, vp)
        if ap > best_ap: best_ap = ap; best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    tp, tl = eval_split(model, DATA["test"])
    return roc_auc_score(tl, tp), average_precision_score(tl, tp)

SEEDS = [42, 43, 44]
res = {}
for layers in [0, 1, 2]:
    rocs, prs = [], []
    for s in SEEDS:
        roc, pr = run(layers, s); rocs.append(roc); prs.append(pr)
        print(f"[layers={layers} seed={s}] ROC-AUC={roc:.3f} PR-AUC={pr:.3f}", flush=True)
    res[layers] = (np.mean(rocs), np.std(rocs), np.mean(prs), np.std(prs))

print("\n=== PROPAGATION-DEPTH ABLATION (pooled pipeline, sqrt weighting, full-pool test) ===")
print(f"{'layers':>7s} {'ROC-AUC':>16s} {'PR-AUC':>16s}")
for L in [0, 1, 2]:
    rm, rs, pm, ps = res[L]
    print(f"{L:7d} {rm:.3f} ± {rs:.3f}    {pm:.3f} ± {ps:.3f}")
print("\nreference: original isolated-hyperedge on full pool ROC-AUC 0.848 / PR-AUC 0.237")
json.dump({str(L): res[L] for L in res}, open(ROOT / "scratch" / "depth_ablation.json", "w"), indent=1)
