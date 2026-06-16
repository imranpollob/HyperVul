"""
Headline experiment: does the HYPEREDGE representation beat PAIRWISE-edge
representations on the same data, features, and training regime?

Controlled like run_unit_comparison.py (identical data assembly, threshold rule,
config), but the unit of computation is now a contract-scoped hypergraph and we vary
ONLY the representation/model:
    set-pool (no edges) | pairwise-gcn (clique) | pairwise-gat (clique) | hypergraph (ours)

Runs multiple seeds, reports mean/std + bootstrap CIs, and a McNemar paired test of
the hypergraph model vs the pairwise-gcn baseline on the test set.
"""
import argparse
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import precision_recall_fscore_support, precision_recall_curve, auc, roc_auc_score

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build_hypergraph import build_contract_graphs  # noqa: E402
from src.models.set_pool import SetPoolClassifier  # noqa: E402
from src.models.gnn_zoo import GNNClassifier  # noqa: E402

K_OZ, K_AAVE = 100, 100
FIXED = {"lr": 1e-3, "dropout": 0.3, "hidden": 256, "layers": 2}
HG = {"layers": 2, "skip": True}  # hypergraph config, overridable via CLI


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@dataclass
class Batch:
    node_feats: torch.Tensor
    inc_node: torch.Tensor
    inc_edge: torch.Tensor
    edge_index: torch.Tensor
    edge_label: torch.Tensor
    edge_vtype: list
    edge_cross: np.ndarray
    num_nodes: int
    num_edges: int

    def to(self, device):
        self.node_feats = self.node_feats.to(device)
        self.inc_node = self.inc_node.to(device)
        self.inc_edge = self.inc_edge.to(device)
        self.edge_index = self.edge_index.to(device)
        self.edge_label = self.edge_label.to(device)
        return self


def _clique_edges(inc_node, inc_edge, num_edges):
    """All-pairs (directed) edges among members of each hyperedge."""
    rows, cols = [], []
    for e in range(num_edges):
        members = inc_node[inc_edge == e]
        if len(members) < 2:
            continue
        for a in range(len(members)):
            for b in range(len(members)):
                if a != b:
                    rows.append(members[a]); cols.append(members[b])
    if not rows:
        return np.zeros((2, 0), dtype=np.int64)
    return np.asarray([rows, cols], dtype=np.int64)


def collate(graphs):
    nf, inode, iedge, elabel, evtype, ecross = [], [], [], [], [], []
    ei_r, ei_c = [], []
    n_off, e_off = 0, 0
    for g in graphs:
        nf.append(g.node_feats)
        inode.append(g.inc_node + n_off)
        iedge.append(g.inc_edge + e_off)
        elabel.append(g.edge_label)
        evtype.extend(g.edge_vtype)
        ecross.append(g.edge_cross)
        ce = _clique_edges(g.inc_node, g.inc_edge, g.num_edges)
        if ce.shape[1]:
            ei_r.append(ce[0] + n_off); ei_c.append(ce[1] + n_off)
        n_off += g.num_nodes; e_off += g.num_edges
    edge_index = (np.stack([np.concatenate(ei_r), np.concatenate(ei_c)])
                  if ei_r else np.zeros((2, 0), dtype=np.int64))
    return Batch(
        node_feats=torch.tensor(np.concatenate(nf), dtype=torch.float32),
        inc_node=torch.tensor(np.concatenate(inode), dtype=torch.long),
        inc_edge=torch.tensor(np.concatenate(iedge), dtype=torch.long),
        edge_index=torch.tensor(edge_index, dtype=torch.long),
        edge_label=torch.tensor(np.concatenate(elabel), dtype=torch.float32),
        edge_vtype=evtype,
        edge_cross=np.concatenate(ecross),
        num_nodes=n_off, num_edges=e_off,
    )


def make_model(kind, device):
    if kind == "set":
        m = SetPoolClassifier(768, FIXED["hidden"], FIXED["dropout"])
    elif kind == "hypergraph":
        m = GNNClassifier(768, FIXED["hidden"], FIXED["dropout"], HG["layers"], conv="hyper")
    elif kind == "pairwise-gcn":
        m = GNNClassifier(768, FIXED["hidden"], FIXED["dropout"], FIXED["layers"], conv="gcn")
    elif kind == "pairwise-gat":
        m = GNNClassifier(768, FIXED["hidden"], FIXED["dropout"], FIXED["layers"], conv="gat")
    else:
        raise ValueError(kind)
    return m.to(device)


def iterate_batches(graphs, batch_graphs, shuffle, seed=0):
    idx = list(range(len(graphs)))
    if shuffle:
        random.Random(seed).shuffle(idx)
    for i in range(0, len(idx), batch_graphs):
        yield collate([graphs[j] for j in idx[i:i + batch_graphs]])


def predict(model, graphs, device):
    model.eval()
    probs, labels, vtypes, cross = [], [], [], []
    with torch.no_grad():
        for b in iterate_batches(graphs, 16, shuffle=False):
            b = b.to(device)
            p = torch.sigmoid(model(b)).cpu().numpy()
            probs.append(p); labels.append(b.edge_label.cpu().numpy())
            vtypes.extend(b.edge_vtype); cross.append(b.edge_cross)
    return np.concatenate(probs), np.concatenate(labels), vtypes, np.concatenate(cross)


def tune_threshold(probs, labels):
    ts = np.linspace(0, 1, 10001)
    above = []
    for t in ts:
        pred = (probs >= t).astype(int)
        tp = np.sum((pred == 1) & (labels == 1)); fn = np.sum((pred == 0) & (labels == 1))
        r = tp / (tp + fn) if (tp + fn) else 0.0
        if r >= 0.95:
            above.append((t, r))
    if above:
        return max(above, key=lambda x: x[0])[0]
    best_t, best_r = 0.0, -1
    for t in ts:
        pred = (probs >= t).astype(int)
        tp = np.sum((pred == 1) & (labels == 1)); fn = np.sum((pred == 0) & (labels == 1))
        r = tp / (tp + fn) if (tp + fn) else 0.0
        if r > best_r:
            best_t, best_r = t, r
    return best_t


def metrics(probs, labels, thr, vtypes, cross):
    pred = (probs >= thr).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(labels, pred, average="binary", zero_division=0)
    f2 = (5 * p * r) / (4 * p + r) if (4 * p + r) else 0.0
    pc, rc, _ = precision_recall_curve(labels, probs)
    out = dict(recall=r, precision=p, f1=f1, f2=f2, pr_auc=auc(rc, pc), roc_auc=roc_auc_score(labels, probs))
    for sub, mask in [("cross", cross), ("intra", ~cross)]:
        if mask.sum() and len(np.unique(labels[mask])) > 1:
            _, _, sf1, _ = precision_recall_fscore_support(labels[mask], pred[mask], average="binary", zero_division=0)
        else:
            sf1 = 0.0
        out[f"{sub}_f1"] = sf1
    return out, pred


def train_eval(kind, train_g, val_g, test_g, device, seed):
    set_seed(seed)
    model = make_model(kind, device)
    opt = optim.Adam(model.parameters(), lr=FIXED["lr"], weight_decay=1e-5)
    tl = np.concatenate([g.edge_label for g in train_g])
    pos, neg = (tl == 1).sum(), (tl == 0).sum()
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([neg / max(pos, 1)], device=device))

    best_loss, no_imp, best_state, patience = float("inf"), 0, None, 20
    for epoch in range(1, 201):
        model.train()
        for b in iterate_batches(train_g, 16, shuffle=True, seed=seed * 1000 + epoch):
            b = b.to(device)
            opt.zero_grad()
            loss = crit(model(b), b.edge_label)
            loss.backward(); opt.step()
        model.eval()
        vloss, vn = 0.0, 0
        with torch.no_grad():
            for b in iterate_batches(val_g, 16, shuffle=False):
                b = b.to(device)
                vloss += crit(model(b), b.edge_label).item() * b.num_edges; vn += b.num_edges
        vloss /= vn
        if vloss < best_loss:
            best_loss, no_imp = vloss, 0
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
        else:
            no_imp += 1
            if no_imp >= patience:
                break
    model.load_state_dict({k: v.to(device) for k, v in best_state.items()})

    vp, vl, vv, vc = predict(model, val_g, device)
    thr = tune_threshold(vp, vl)
    val_m, _ = metrics(vp, vl, thr, vv, vc)
    tp, tl_, tv, tc = predict(model, test_g, device)
    m, pred = metrics(tp, tl_, thr, tv, tc)
    m["threshold"] = float(thr)
    m["val_f1"] = val_m["f1"]
    return m, pred, tl_, tv


def bootstrap_ci(vals):
    a = np.array(vals)
    return a.mean(), a.std(), np.percentile(a, 2.5), np.percentile(a, 97.5)


def mcnemar(pred_a, pred_b, labels):
    """Paired test on correctness; returns (b, c, p) with continuity-corrected chi-sq -> p."""
    from scipy.stats import chi2
    ca = (pred_a == labels); cb = (pred_b == labels)
    b = int(np.sum(ca & ~cb)); c = int(np.sum(~ca & cb))
    if b + c == 0:
        return b, c, 1.0
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    return b, c, float(chi2.sf(stat, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--models", nargs="+", default=["set", "pairwise-gcn", "pairwise-gat", "hypergraph"])
    ap.add_argument("--hg-layers", type=int, default=HG["layers"])
    ap.add_argument("--hg-noskip", action="store_true")
    ap.add_argument("--drop-func", action="store_true",
                    help="atomic probe: drop the (redundant) full-function node, keep only state/callee nodes")
    ap.add_argument("--sig", action="store_true",
                    help="use signature/skeleton function embeddings (atomic, function identity kept)")
    args = ap.parse_args()
    HG["layers"] = args.hg_layers
    HG["skip"] = not args.hg_noskip

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} | seeds={args.seeds} | features={'SIGNATURE' if args.sig else 'FULL'}")
    splits = PROJECT_ROOT / "data" / "splits"
    results = PROJECT_ROOT / "experiments" / "results"

    if args.sig:
        train_data = json.load(open(splits / "train_augmented_sig.json"))
        val_data = json.load(open(splits / "val_sig.json"))
        test_data = json.load(open(splits / "test_sig.json"))
        oz = json.load(open(results / "eval_clean_negatives_oz_sig.json"))
        aave = json.load(open(results / "eval_clean_negatives_aave_sig.json"))
    else:
        train_data = json.load(open(splits / "train_augmented.json"))
        val_data = json.load(open(splits / "val_features.json"))
        test_data = json.load(open(splits / "test_features.json"))
        oz = json.load(open(results / "eval_clean_negatives_oz_features.json"))
        aave = json.load(open(results / "eval_clean_negatives_aave_split.json"))
    oz_map = json.load(open(PROJECT_ROOT / "scratch" / "oz_split_mapping.json"))

    oz_train = [i for i in oz if oz_map.get((i.get("file") or i.get("filePath")).replace(
        "data/external/openzeppelin-contracts/contracts/", ""), "holdout") == "train"]
    random.seed(42)
    oz_train = sorted(oz_train, key=lambda x: (x["file"], x["contract"], x["function"]))
    sampled_oz = random.sample(oz_train, K_OZ)
    aave_train = sorted([i for i in aave if i.get("split") == "train"],
                        key=lambda x: (x["file"], x["contract"], x["function"]))
    random.seed(42)
    sampled_aave = random.sample(aave_train, K_AAVE)

    train_items = train_data + sampled_oz + sampled_aave
    df = args.drop_func
    if df:
        print("ATOMIC PROBE: function nodes dropped (state/callee nodes only)")
    train_g = build_contract_graphs(train_items, drop_func=df)
    val_g = build_contract_graphs(val_data, drop_func=df)
    test_g = build_contract_graphs(test_data, drop_func=df)
    print(f"Train graphs={len(train_g)} hyperedges={sum(g.num_edges for g in train_g)} | "
          f"val graphs={len(val_g)} | test graphs={len(test_g)} hyperedges={sum(g.num_edges for g in test_g)}")

    store = {k: [] for k in args.models}
    preds_seed42 = {}
    test_labels_ref = None
    for seed in args.seeds:
        print(f"\n##### SEED {seed} #####")
        for kind in args.models:
            m, pred, tlab, tv = train_eval(kind, train_g, val_g, test_g, device, seed)
            store[kind].append(m)
            if seed == args.seeds[0]:
                preds_seed42[kind] = pred; test_labels_ref = tlab
            print(f"  {kind:14s} thr={m['threshold']:.4f} valF1={m['val_f1']*100:.2f} | "
                  f"R={m['recall']*100:.2f} P={m['precision']*100:.2f} "
                  f"F1={m['f1']*100:.2f} F2={m['f2']*100:.2f} PR={m['pr_auc']*100:.2f} ROC={m['roc_auc']*100:.2f}")

    # ---- report ----
    def agg(kind, key):
        return bootstrap_ci([r[key] * 100 for r in store[kind]])

    lines = ["# HyperVul — Representation Comparison (Hyperedge vs Pairwise)\n",
             f"Seeds: {args.seeds}. Identical data (base + {K_OZ} OZ + {K_AAVE} Aave), config "
             f"(hidden={FIXED['hidden']}, dropout={FIXED['dropout']}, lr={FIXED['lr']}, layers={FIXED['layers']}), "
             "threshold rule (highest thr with >=95% val recall). Only the representation varies.\n",
             "| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |",
             "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"]
    for kind in args.models:
        cells = []
        for key in ["f1", "precision", "recall", "f2", "pr_auc", "roc_auc", "cross_f1", "intra_f1"]:
            mean, std, lo, hi = agg(kind, key)
            cells.append(f"{mean:.2f}±{std:.2f}" if len(args.seeds) > 1 else f"{mean:.2f}")
        lines.append(f"| **{kind}** | " + " | ".join(cells) + " |")

    if "hypergraph" in preds_seed42 and "pairwise-gcn" in preds_seed42:
        b, c, p = mcnemar(preds_seed42["hypergraph"], preds_seed42["pairwise-gcn"], test_labels_ref)
        lines += ["", f"**McNemar (hypergraph vs pairwise-gcn, seed {args.seeds[0]})**: "
                      f"hypergraph-only-correct={b}, pairwise-only-correct={c}, p={p:.4f}"]

    out = results / "representation_comparison.md"
    out.write_text("\n".join(lines) + "\n")
    json.dump({k: store[k] for k in store}, open(results / "representation_comparison.json", "w"),
              indent=2, default=float)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
