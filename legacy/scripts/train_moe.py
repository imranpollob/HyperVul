#!/usr/bin/env python3
"""Regime-aware MoE head on the 0-layer pooled base + chosen Option B config. 5 seeds.
Usage: train_moe.py <optionb_target>   (e.g. 20 ; 0 = all-data no balancing)"""
import json, sys
from pathlib import Path
import numpy as np, torch
from sklearn.metrics import average_precision_score, roc_auc_score
ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
from model.ghan import PooledMoEModel
from model.contract_graph_data import (load_graphs, node_embeddings, member_embeddings,
                                        graph_pooled_tensors, option_a_pos_weight)

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 20
N_EXPERTS = 4
LB = 0.01
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FUNC, MEMB = node_embeddings(), member_embeddings()
GR = {s: load_graphs(s) for s in ["train", "val", "test"]}

def graph_moe(g):
    members, mmask, ei, et, imask, labels = graph_pooled_tensors(g, FUNC, MEMB)
    sec = torch.tensor([n["sec"] for n in g["nodes"] if n["kind"] == "interaction"], dtype=torch.float32)
    return members, mmask, sec, imask, labels

DATA = {s: [graph_moe(g) for g in GR[s]] for s in ["train", "val", "test"]}
PW = torch.tensor([option_a_pos_weight("sqrt")], device=dev)
print(f"MoE: target={TARGET}:1  experts={N_EXPERTS}  LB={LB}  "
      f"train={len(DATA['train'])} val={len(DATA['val'])} test={len(DATA['test'])}", flush=True)

with_pos = [i for i, g in enumerate(GR["train"]) if g["n_pos"] > 0]
all_neg = [i for i, g in enumerate(GR["train"]) if g["n_pos"] == 0]
nneg = [g["n_neg"] for g in GR["train"]]
pos_int = sum(GR["train"][i]["n_pos"] for i in with_pos)
base_neg = sum(GR["train"][i]["n_neg"] for i in with_pos)

def epoch_indices(cursor):
    if TARGET == 0:
        return list(range(len(DATA["train"])))
    budget = max(0, TARGET * pos_int - base_neg)
    chosen, acc, n = [], 0, len(all_neg)
    while acc < budget and len(chosen) < n:
        gi = all_neg[cursor[0] % n]; cursor[0] += 1; chosen.append(gi); acc += nneg[gi]
    return with_pos + chosen

def batch(gs):
    Mmax = max(m.shape[1] for m, *_ in gs); D = gs[0][0].shape[2]
    mem, mm, sec, im, lab = [], [], [], [], []
    for members, mmask, s_, imask, labels in gs:
        N, Mg, _ = members.shape
        if Mg < Mmax:
            members = torch.cat([members, torch.zeros(N, Mmax - Mg, D)], 1)
            mmask = torch.cat([mmask, torch.zeros(N, Mmax - Mg, dtype=torch.bool)], 1)
        mem.append(members); mm.append(mmask); sec.append(s_); im.append(imask); lab.append(labels)
    return (torch.cat(mem).to(dev), torch.cat(mm).to(dev), torch.cat(sec).to(dev),
            torch.cat(im).to(dev), torch.cat(lab).to(dev))

def eval_probs(model, data):
    model.eval(); ps, ls = [], []
    with torch.no_grad():
        for g in data:
            members, mmask, sec, imask, L = batch([g])
            lo, _, _ = model(members, mmask, sec, imask)
            ps.append(torch.sigmoid(lo).cpu()); ls.append(L.cpu())
    return torch.cat(ps).numpy(), torch.cat(ls).numpy()

def run(seed, epochs=60, lr=1e-3, bs=64):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PooledMoEModel(sec_dim=8, n_experts=N_EXPERTS).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    best_ap, best_state, cursor = -1, None, [0]
    for ep in range(epochs):
        model.train(); idxs = epoch_indices(cursor); np.random.shuffle(idxs)
        for i in range(0, len(idxs), bs):
            members, mmask, sec, imask, L = batch([DATA["train"][j] for j in idxs[i:i+bs]])
            lo, aux, _ = model(members, mmask, sec, imask)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(lo, L, pos_weight=PW) + LB * aux
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        vp, vl = eval_probs(model, DATA["val"]); ap = average_precision_score(vl, vp)
        if ap > best_ap: best_ap, best_state = ap, {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    # expert usage on test
    model.eval()
    with torch.no_grad():
        imp = []
        for g in DATA["test"]:
            members, mmask, sec, imask, L = batch([g])
            _, _, importance = model(members, mmask, sec, imask); imp.append(importance.cpu().numpy())
    tp, tl = eval_probs(model, DATA["test"])
    return roc_auc_score(tl, tp), average_precision_score(tl, tp), np.mean(imp, 0)

rocs, prs, imps = [], [], []
for s in [42, 43, 44, 45, 46]:
    roc, pr, imp = run(s); rocs.append(roc); prs.append(pr); imps.append(imp)
    print(f"[MoE seed={s}] ROC={roc:.3f} PR={pr:.3f} expert_usage={np.round(imp,3).tolist()}", flush=True)
print(f"\n=== MoE HEAD (0-layer pooled, Option B {TARGET}:1, {N_EXPERTS} experts, 5 seeds) ===")
print(f"  ROC-AUC {np.mean(rocs):.3f} ± {np.std(rocs):.3f}")
print(f"  PR-AUC  {np.mean(prs):.3f} ± {np.std(prs):.3f}")
print(f"  mean expert usage {np.round(np.mean(imps,0),3).tolist()}  (uniform=={round(1/N_EXPERTS,3)})")
json.dump({"target": TARGET, "roc": [float(np.mean(rocs)), float(np.std(rocs))],
           "pr": [float(np.mean(prs)), float(np.std(prs))],
           "expert_usage": np.mean(imps, 0).tolist()}, open(ROOT / "scratch" / "moe_results.json", "w"), indent=1)
print("DONE", flush=True)
