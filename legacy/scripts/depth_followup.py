#!/usr/bin/env python3
"""Follow-up to the depth ablation:
 TASK 1  convergence check (0/1/2 layers, log val-loss curve, early-stop on val loss)
 TASK 2  gated-residual propagation sweep (global-1L, global-2L, per-type-1L; 5 seeds)
 TASK 3  Option B (graph-level balanced sampling) on the 0-layer pooled model (3 seeds)
Shared pooled-tensor precompute; same full-pool test (41p/732n)."""
import json, sys
from pathlib import Path
import numpy as np, torch
from sklearn.metrics import average_precision_score, roc_auc_score
ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
from model.ghan import PooledContractGraphModel, PooledGatedModel
from model.contract_graph_data import (load_graphs, node_embeddings, member_embeddings,
                                        graph_pooled_tensors, batch_pooled, option_a_pos_weight)

dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
FUNC, MEMB = node_embeddings(), member_embeddings()
GRAPHS = {s: load_graphs(s) for s in ["train", "val", "test"]}
DATA = {s: [graph_pooled_tensors(g, FUNC, MEMB) for g in GRAPHS[s]] for s in ["train", "val", "test"]}
PW = torch.tensor([option_a_pos_weight("sqrt")], device=dev)
print(f"precomputed train={len(DATA['train'])} val={len(DATA['val'])} test={len(DATA['test'])}", flush=True)

def lossfn(lo, L): return torch.nn.functional.binary_cross_entropy_with_logits(lo, L, pos_weight=PW)

def eval_probs(model, data):
    model.eval(); ps, ls = [], []
    with torch.no_grad():
        for g in data:
            m, mm, ei, et, im, L = batch_pooled([g], device=dev)
            ps.append(torch.sigmoid(model(m, mm, ei, et, im)).cpu()); ls.append(L.cpu())
    return torch.cat(ps).numpy(), torch.cat(ls).numpy()

def val_loss(model):
    model.eval(); tot, n = 0.0, 0
    with torch.no_grad():
        for g in DATA["val"]:
            m, mm, ei, et, im, L = batch_pooled([g], device=dev)
            tot += lossfn(model(m, mm, ei, et, im), L).item() * len(L); n += len(L)
    return tot / n

def train(make_model, train_data, seed, maxepochs=60, lr=1e-3, bs=64, es_patience=None):
    torch.manual_seed(seed); np.random.seed(seed)
    model = make_model().to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    best_ap, best_state, best_ap_ep = -1, None, 0
    best_vl, best_vl_ep, since = 1e9, 0, 0
    curve = []
    order = list(range(len(train_data)))
    ep = 0
    for ep in range(maxepochs):
        model.train(); np.random.shuffle(order)
        for i in range(0, len(order), bs):
            gs = [train_data[j] for j in order[i:i+bs]]
            m, mm, EI, ET, M, L = batch_pooled(gs, device=dev)
            loss = lossfn(model(m, mm, EI, ET, M), L)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
        vp, vl_lab = eval_probs(model, DATA["val"]); ap = average_precision_score(vl_lab, vp)
        vl = val_loss(model); curve.append((ep, round(vl, 4), round(ap, 4)))
        if ap > best_ap: best_ap, best_ap_ep, best_state = ap, ep, {k: v.cpu().clone() for k, v in model.state_dict().items()}
        if vl < best_vl - 1e-4: best_vl, best_vl_ep, since = vl, ep, 0
        else: since += 1
        if es_patience and since >= es_patience: break
    model.load_state_dict(best_state)
    tp, tl = eval_probs(model, DATA["test"])
    return dict(roc=roc_auc_score(tl, tp), pr=average_precision_score(tl, tp),
                epochs=ep + 1, best_ap_ep=best_ap_ep, best_vl_ep=best_vl_ep, curve=curve, model=model)

# ============================ TASK 1 — convergence ============================
print("\n############ TASK 1 — CONVERGENCE (early-stop on val loss, max 200) ############", flush=True)
t1 = {}
for layers in [0, 1, 2]:
    rocs, prs, info = [], [], []
    for s in [42, 43]:
        r = train(lambda L=layers: PooledContractGraphModel(layers=L), DATA["train"], s,
                  maxepochs=200, es_patience=30)
        rocs.append(r["roc"]); prs.append(r["pr"])
        c = r["curve"]; vl60 = next((v for e, v, a in c if e == 59), None)
        info.append((s, r["epochs"], r["best_vl_ep"], r["best_ap_ep"], vl60, c[-1][1], r["roc"]))
        print(f"[T1 layers={layers} seed={s}] epochs_used={r['epochs']} best_val_loss_ep={r['best_vl_ep']} "
              f"best_val_AP_ep={r['best_ap_ep']} val_loss@60={vl60} val_loss@end={c[-1][1]} ROC={r['roc']:.3f}", flush=True)
    t1[layers] = (np.mean(rocs), np.std(rocs), np.mean(prs), np.std(prs))
print("\n[TASK 1 SUMMARY]  layers : ROC-AUC | PR-AUC | (prior fixed-60 ROC)")
prior = {0: 0.808, 1: 0.720, 2: 0.706}
for L in [0, 1, 2]:
    rm, rs, pm, ps = t1[L]
    print(f"  {L} : {rm:.3f}±{rs:.3f} | {pm:.3f}±{ps:.3f} | prior {prior[L]:.3f}", flush=True)

# ============================ TASK 2 — gated residual =========================
print("\n############ TASK 2 — GATED-RESIDUAL SWEEP (5 seeds) ############", flush=True)
variants = {"global-1L": dict(layers=1, per_type=False),
            "global-2L": dict(layers=2, per_type=False),
            "pertype-1L": dict(layers=1, per_type=True)}
t2 = {}
for name, cfg in variants.items():
    rocs, prs, gates = [], [], []
    for s in [42, 43, 44, 45, 46]:
        r = train(lambda c=cfg: PooledGatedModel(layers=c["layers"], per_type=c["per_type"]),
                  DATA["train"], s, maxepochs=60)
        rocs.append(r["roc"]); prs.append(r["pr"]); gates.append(r["model"].gate_values())
        print(f"[T2 {name} seed={s}] ROC={r['roc']:.3f} PR={r['pr']:.3f} gates={r['model'].gate_values()}", flush=True)
    t2[name] = (np.mean(rocs), np.std(rocs), np.mean(prs), np.std(prs))
print("\n[TASK 2 SUMMARY]  variant : ROC-AUC | PR-AUC")
for name in variants:
    rm, rs, pm, ps = t2[name]
    print(f"  {name:11s} : {rm:.3f}±{rs:.3f} | {pm:.3f}±{ps:.3f}", flush=True)

# ============================ TASK 3 — Option B ===============================
print("\n############ TASK 3 — OPTION B (graph-level balanced sampling), 0-layer ############", flush=True)
with_pos = [i for i, g in enumerate(GRAPHS["train"]) if g["n_pos"] > 0]
all_neg = [i for i, g in enumerate(GRAPHS["train"]) if g["n_pos"] == 0]
pos_int = sum(g["n_pos"] for g in GRAPHS["train"] if g["n_pos"] > 0)
base_neg = sum(g["n_neg"] for g in GRAPHS["train"] if g["n_pos"] > 0)
budget = max(0, 3 * pos_int - base_neg)
print(f"with-positive graphs={len(with_pos)} (pos={pos_int} neg={base_neg}, already 1:{base_neg/pos_int:.1f}); "
      f"target 3:1 budget for extra all-neg graphs = {budget}", flush=True)
balanced = [DATA["train"][i] for i in with_pos]  # 3:1 target -> with-positive graphs only (whole graphs)
rocs, prs = [], []
for s in [42, 43, 44]:
    r = train(lambda: PooledContractGraphModel(layers=0), balanced, s, maxepochs=60)
    rocs.append(r["roc"]); prs.append(r["pr"])
    print(f"[T3 OptionB-0layer seed={s}] ROC={r['roc']:.3f} PR={r['pr']:.3f}", flush=True)
print(f"\n[TASK 3 SUMMARY] Option B (0-layer, balanced) ROC-AUC {np.mean(rocs):.3f}±{np.std(rocs):.3f} "
      f"PR-AUC {np.mean(prs):.3f}±{np.std(prs):.3f}  (vs 0-layer all-data 0.808/0.342)", flush=True)

json.dump({"task1": {str(k): t1[k] for k in t1}, "task2": t2,
           "task3": (float(np.mean(rocs)), float(np.std(rocs)), float(np.mean(prs)), float(np.std(prs)))},
          open(ROOT / "scratch" / "depth_followup.json", "w"), indent=1)
print("\nDONE", flush=True)
