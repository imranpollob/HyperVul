#!/usr/bin/env python3
"""Full metric table (precision/recall/F1/F2 + ROC/PR-AUC) for the headline config:
0-layer pooled + Option B 20:1. Reported at the val-F1-optimal threshold and the
project's >=95%-val-recall threshold. 3 seeds."""
import sys
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
TARGET = 20
with_pos = [i for i, g in enumerate(GR["train"]) if g["n_pos"] > 0]
all_neg = [i for i, g in enumerate(GR["train"]) if g["n_pos"] == 0]
nneg = [g["n_neg"] for g in GR["train"]]
pos_int = sum(GR["train"][i]["n_pos"] for i in with_pos); base_neg = sum(GR["train"][i]["n_neg"] for i in with_pos)

def lossfn(lo, L): return torch.nn.functional.binary_cross_entropy_with_logits(lo, L, pos_weight=PW)
def eval_probs(model, data):
    model.eval(); ps, ls = [], []
    with torch.no_grad():
        for g in data:
            m, mm, ei, et, im, L = batch_pooled([g], device=dev)
            ps.append(torch.sigmoid(model(m, mm, ei, et, im)).cpu()); ls.append(L.cpu())
    return torch.cat(ps).numpy(), torch.cat(ls).numpy()
def epoch_idx(cursor):
    budget = max(0, TARGET * pos_int - base_neg); chosen, acc, n = [], 0, len(all_neg)
    while acc < budget and len(chosen) < n:
        gi = all_neg[cursor[0] % n]; cursor[0] += 1; chosen.append(gi); acc += nneg[gi]
    return with_pos + chosen
def tbl(probs, labels, t):
    pred = (probs >= t).astype(int); y = labels.astype(int)
    tp = int(((pred==1)&(y==1)).sum()); fp=int(((pred==1)&(y==0)).sum()); fn=int(((pred==0)&(y==1)).sum())
    p = tp/(tp+fp) if tp+fp else 0.0; r = tp/(tp+fn) if tp+fn else 0.0
    f1 = 2*p*r/(p+r) if p+r else 0.0; f2 = 5*p*r/(4*p+r) if 4*p+r else 0.0
    return dict(precision=p, recall=r, f1=f1, f2=f2, tp=tp, fp=fp, fn=fn)
def thr_f1(probs, labels):
    best, bf = 0.5, -1
    for t in sorted(set(probs.tolist())):
        m = tbl(probs, labels, t)
        if m["f1"] > bf: bf, best = m["f1"], t
    return best
def thr_r95(probs, labels, tr=0.95):
    P = labels.sum(); best = 0.0
    for t in sorted(set(probs.tolist()), reverse=True):
        if ((probs>=t)&(labels==1)).sum()/P >= tr: best = t
    return best

def run(seed, epochs=60, lr=1e-3, bs=64):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PooledContractGraphModel(layers=0).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    best_ap, best_state, cursor = -1, None, [0]
    for ep in range(epochs):
        model.train(); idxs = epoch_idx(cursor); np.random.shuffle(idxs)
        for i in range(0, len(idxs), bs):
            m, mm, EI, ET, M, L = batch_pooled([DATA["train"][j] for j in idxs[i:i+bs]], device=dev)
            loss = lossfn(model(m, mm, EI, ET, M), L)
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        vp, vl = eval_probs(model, DATA["val"]); ap = average_precision_score(vl, vp)
        if ap > best_ap: best_ap, best_state = ap, {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    vp, vl = eval_probs(model, DATA["val"]); tf1 = thr_f1(vp, vl); t95 = thr_r95(vp, vl)
    tp, tl = eval_probs(model, DATA["test"])
    return (tbl(tp, tl, tf1), tf1, tbl(tp, tl, t95), t95,
            roc_auc_score(tl, tp), average_precision_score(tl, tp))

f1m, r95m, rocs, prs, tf1s, t95s = [], [], [], [], [], []
for s in [42, 43, 44]:
    mf1, tf1, m95, t95, roc, pr = run(s)
    f1m.append(mf1); r95m.append(m95); rocs.append(roc); prs.append(pr); tf1s.append(tf1); t95s.append(t95)
    print(f"[seed {s}] @F1thr={tf1:.3f}: P={mf1['precision']:.3f} R={mf1['recall']:.3f} F1={mf1['f1']:.3f} "
          f"(tp={mf1['tp']} fp={mf1['fp']} fn={mf1['fn']}) | ROC={roc:.3f} PR={pr:.3f}", flush=True)

def agg(rows, k): v=[r[k] for r in rows]; return np.mean(v), np.std(v)
print("\n=== HEADLINE: 0-layer pooled + Option B 20:1 (full-pool test 41p/732n, 3 seeds) ===")
print(f"  threshold-free:  ROC-AUC {np.mean(rocs):.3f}±{np.std(rocs):.3f}   PR-AUC {np.mean(prs):.3f}±{np.std(prs):.3f}")
print(f"\n  @ val-F1-optimal threshold ({np.mean(tf1s):.3f} avg):")
for k in ["precision","recall","f1","f2"]:
    mu,sd=agg(f1m,k); print(f"     {k:10s} {mu:.3f} ± {sd:.3f}")
print(f"\n  @ >=95%-val-recall threshold ({np.mean(t95s):.3f} avg):")
for k in ["precision","recall","f1","f2"]:
    mu,sd=agg(r95m,k); print(f"     {k:10s} {mu:.3f} ± {sd:.3f}")
print("DONE", flush=True)
