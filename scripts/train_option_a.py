#!/usr/bin/env python3
"""Option A (weighted-loss) baseline training on the contract-graph rebuild.

Per-interaction binary head on G-HAN-refined node embeddings; class imbalance handled by
BCEWithLogitsLoss(pos_weight=neg/pos). Project threshold rule: highest threshold with
>=95% validation recall. Reports aggregate test metrics AND recall stratified by whether
each test positive's span fits within 512 tokens or still exceeds it.
"""
import json, sys, hashlib
from pathlib import Path
import numpy as np
import torch
from transformers import RobertaTokenizer
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
from model.ghan import PooledContractGraphModel
from model.contract_graph_data import (load_graphs, node_embeddings, member_embeddings,
                                        graph_pooled_tensors, batch_pooled, option_a_pos_weight)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FUNC = node_embeddings(); MEMB = member_embeddings()

# precompute per-graph POOLED tensors: (members, member_mask, ei, et, interaction_mask, labels)
DATA = {s: [graph_pooled_tensors(g, FUNC, MEMB) for g in load_graphs(s)] for s in ["train", "val", "test"]}

def batch(graphs):
    return batch_pooled(graphs, device=device)

# --- test-positive 512 stratification ---
tok = RobertaTokenizer.from_pretrained("web3se/SmartBERT-v3")
def exceeds512(src): return len(tok.tokenize(src)) + 2 > 512
test_pos_meta = []  # (global_interaction_index, exceeds_flag)
gi = 0
for g in load_graphs("test"):
    for n in g["nodes"]:
        if n["kind"] == "interaction":
            if n["label"] == 1:
                test_pos_meta.append((gi, exceeds512(n["function_source"])))
            gi += 1
exc_idx = set(i for i, e in test_pos_meta if e)
fit_idx = set(i for i, e in test_pos_meta if not e)

def eval_split(model, data):
    model.eval(); probs, labs = [], []
    with torch.no_grad():
        for g in data:
            members, mmask, ei, et, imask, L, sec = batch([g])
            lo = model(members, mmask, ei, et, imask, sec)
            probs.append(torch.sigmoid(lo).cpu()); labs.append(L.cpu())
    return torch.cat(probs).numpy(), torch.cat(labs).numpy()

def pick_threshold(probs, labels, target_recall=0.95):
    P = labels.sum()
    best = 0.0
    for t in sorted(set(probs.tolist()), reverse=True):
        rec = ((probs >= t) & (labels == 1)).sum() / P
        if rec >= target_recall:
            best = t
    return best

def f1_opt_threshold(probs, labels):
    best_t, best_f1 = 0.5, -1
    for t in sorted(set(probs.tolist())):
        pred = (probs >= t).astype(int)
        tp = ((pred == 1) & (labels == 1)).sum(); fp = ((pred == 1) & (labels == 0)).sum()
        fn = ((pred == 0) & (labels == 1)).sum()
        p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * p * r / (p + r) if p + r else 0
        if f1 > best_f1: best_f1, best_t = f1, t
    return best_t

def metrics(probs, labels, thr):
    pred = (probs >= thr).astype(int)
    tp = int(((pred == 1) & (labels == 1)).sum()); fp = int(((pred == 1) & (labels == 0)).sum())
    fn = int(((pred == 0) & (labels == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    f2 = 5 * prec * rec / (4 * prec + rec) if 4 * prec + rec else 0.0
    return dict(precision=prec, recall=rec, f1=f1, f2=f2,
                pr_auc=average_precision_score(labels, probs),
                roc_auc=roc_auc_score(labels, probs))

def run_seed(seed, epochs=60, lr=1e-3, bs=64):
    torch.manual_seed(seed); np.random.seed(seed)
    model = PooledContractGraphModel(dim=768, hidden=256, layers=2, dropout=0.3).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    pw = torch.tensor([option_a_pos_weight("sqrt")], device=device)  # full weight collapses->all-positive
    lossfn = torch.nn.BCEWithLogitsLoss(pos_weight=pw)
    best_ap, best_state = -1, None
    order = list(range(len(DATA["train"])))
    for ep in range(epochs):
        model.train(); np.random.shuffle(order)
        for i in range(0, len(order), bs):
            gs = [DATA["train"][j] for j in order[i:i+bs]]
            members, mmask, EI, ET, M, L, sec = batch(gs)
            lo = model(members, mmask, EI, ET, M, sec)
            loss = lossfn(lo, L)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        vp, vl = eval_split(model, DATA["val"])
        ap = average_precision_score(vl, vp)
        if ap > best_ap:
            best_ap = ap; best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    vp, vl = eval_split(model, DATA["val"])
    thr95 = pick_threshold(vp, vl); thrf1 = f1_opt_threshold(vp, vl)
    tp, tl = eval_split(model, DATA["test"])
    m = metrics(tp, tl, thrf1)
    def grp_recall(idxset, thr):
        pred = (tp >= thr).astype(int)
        hit = sum(1 for i in idxset if pred[i] == 1); return hit / len(idxset)
    def grp_meanprob(idxset):
        return float(np.mean([tp[i] for i in idxset]))
    strat = dict(
        fit_r95=grp_recall(fit_idx, thr95), exc_r95=grp_recall(exc_idx, thr95),
        fit_rf1=grp_recall(fit_idx, thrf1), exc_rf1=grp_recall(exc_idx, thrf1),
        fit_mp=grp_meanprob(fit_idx), exc_mp=grp_meanprob(exc_idx))
    return m, thrf1, thr95, best_ap, strat

SEEDS = [42, 43, 44]
results = []
print(f"train graphs={len(DATA['train'])} val={len(DATA['val'])} test={len(DATA['test'])}")
print(f"pos_weight(sqrt)={option_a_pos_weight('sqrt'):.1f}  test positives: fit512={len(fit_idx)} exceed512={len(exc_idx)}\n")
for s in SEEDS:
    m, thrf1, thr95, vap, strat = run_seed(s)
    results.append((m, strat))
    print(f"[seed {s}] thrF1={thrf1:.3f} thr95={thr95:.3f} valPR-AUC={vap:.3f} | TEST(@F1thr) "
          f"P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} PR-AUC={m['pr_auc']:.3f} ROC-AUC={m['roc_auc']:.3f}")
    print(f"          recall@F1thr  fit512={strat['fit_rf1']:.3f}  exceed512={strat['exc_rf1']:.3f}")
    print(f"          recall@95thr  fit512={strat['fit_r95']:.3f}  exceed512={strat['exc_r95']:.3f}")
    print(f"          mean prob     fit512={strat['fit_mp']:.3f}  exceed512={strat['exc_mp']:.3f}")

def agg(key): v = [r[0][key] for r in results]; return float(np.mean(v)), float(np.std(v))
def saggr(key): v = [r[1][key] for r in results]; return float(np.mean(v)), float(np.std(v))
print("\n=== AGGREGATE test metrics @F1-thr (mean±std) ===")
for k in ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"]:
    mu, sd = agg(k); print(f"  {k:10s} {mu:.3f} ± {sd:.3f}")
print(f"\n=== STRATIFIED EVIDENCE: fits<=512 (n={len(fit_idx)}) vs exceeds-512 (n={len(exc_idx)}) ===")
for label, kf, ke in [("recall @ F1-opt threshold", "fit_rf1", "exc_rf1"),
                      ("recall @ 95%-recall threshold", "fit_r95", "exc_r95"),
                      ("mean predicted probability", "fit_mp", "exc_mp")]:
    fm, fs = saggr(kf); em, es = saggr(ke)
    print(f"  {label:32s} fit={fm:.3f}±{fs:.3f}   exceed={em:.3f}±{es:.3f}")
json.dump({"seeds": SEEDS, "agg": {k: agg(k) for k in ['precision','recall','f1','f2','pr_auc','roc_auc']},
           "strat": {k: saggr(k) for k in ['fit_rf1','exc_rf1','fit_r95','exc_r95','fit_mp','exc_mp']},
           "n_fit": len(fit_idx), "n_exc": len(exc_idx)},
          open(ROOT / "scratch" / "option_a_results.json", "w"), indent=1)
