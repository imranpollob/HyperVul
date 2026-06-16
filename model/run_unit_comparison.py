"""
Controlled prediction-unit comparison.

Trains Function-only, {Function,State}, {Function,Callee}, and Full
{Function,State,Callee} variants under IDENTICAL conditions:
  - same training data (base + 100 OZ-train + 100 Aave-train, matching iteration3),
  - same fixed hyperparameters (hidden_dim=256, dropout=0.3, lr=1e-3, wd=1e-5),
  - same threshold procedure (highest threshold achieving >=95% recall on val positives),
  - same seed, epochs, patience, pos_weight.
The ONLY thing that varies between runs is which node types enter the hyperedge.

This replaces the invalid comparison in run_baselines.py, where "Ours" was a
stale/stitched row from older iterations and the ablations were trained on
different data with an 8-config grid search.
"""
import json
import random
from pathlib import Path
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import precision_recall_fscore_support, precision_recall_curve, auc, roc_auc_score

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")

MODES = ["function", "func_state", "func_callee", "full"]
MODE_LABELS = {
    "function": "Function-only",
    "func_state": "{Function, State}",
    "func_callee": "{Function, Callee}",
    "full": "Full {Function, State, Callee} (Ours)",
}

FIXED_CONFIG = {"lr": 1e-3, "dropout": 0.3, "hidden_dim": 256}
K_AAVE = 100      # matches iteration3 selected K_app
K_OZ = 100        # matches iteration3 / iteration2


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class AttentionPooling(nn.Module):
    def __init__(self, input_dim=768, hidden_dim=128):
        super().__init__()
        self.w_a = nn.Linear(input_dim, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, x, mask=None):
        scores = self.v(torch.tanh(self.w_a(x))).squeeze(-1)
        if mask is not None:
            scores = scores.masked_fill(~mask, -1e9)
        attn_weights = torch.softmax(scores, dim=-1)
        pooled = torch.sum(attn_weights.unsqueeze(-1) * x, dim=1)
        return pooled, attn_weights


class HyperedgeClassifier(nn.Module):
    def __init__(self, input_dim=768, hidden_dim=256, dropout=0.3):
        super().__init__()
        self.pool = AttentionPooling(input_dim=input_dim, hidden_dim=128)
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x, mask=None):
        pooled, attn = self.pool(x, mask)
        return self.mlp(pooled), attn


class UnitDataset(Dataset):
    def __init__(self, items, mode):
        self.items = items
        self.mode = mode

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        func_emb = item["node_features"]["function"]
        sv_embs = list(item["node_features"]["state_vars"].values())
        ec_embs = [ec["embedding"] for ec in item["node_features"]["external_calls"]]

        if self.mode == "function":
            nodes = [func_emb]
        elif self.mode == "func_state":
            nodes = [func_emb] + sv_embs
        elif self.mode == "func_callee":
            nodes = [func_emb] + ec_embs
        elif self.mode == "full":
            nodes = [func_emb] + sv_embs + ec_embs
        else:
            raise ValueError(self.mode)

        x = torch.tensor(nodes, dtype=torch.float32)
        return x, float(item.get("label", 0.0)), item


def collate_fn(batch):
    tensors, labels, items = zip(*batch)
    max_len = max(t.size(0) for t in tensors)
    padded, masks = [], []
    for t in tensors:
        n = t.size(0)
        pad = max_len - n
        if pad > 0:
            t = torch.cat([t, torch.zeros(pad, 768)], dim=0)
            m = torch.cat([torch.ones(n, dtype=torch.bool), torch.zeros(pad, dtype=torch.bool)])
        else:
            m = torch.ones(n, dtype=torch.bool)
        padded.append(t)
        masks.append(m)
    return torch.stack(padded), torch.stack(masks), torch.tensor(labels, dtype=torch.float32), items


def evaluate_model(model, loader, device):
    model.eval()
    probs, labels, items = [], [], []
    with torch.no_grad():
        for x, mask, y, batch_items in loader:
            x, mask = x.to(device), mask.to(device)
            logits, _ = model(x, mask)
            p = torch.sigmoid(logits).squeeze(-1).cpu().numpy()
            probs.extend(np.atleast_1d(p))
            labels.extend(y.numpy())
            items.extend(batch_items)
    return np.array(probs), np.array(labels), items


def f2_score(p, r):
    return (5 * p * r) / (4 * p + r) if (4 * p + r) > 0 else 0.0


def subset_f1(probs, labels, indices, threshold):
    if not indices:
        return 0.0
    sp, sl = probs[indices], labels[indices]
    pred = (sp >= threshold).astype(int)
    _, _, f1, _ = precision_recall_fscore_support(sl, pred, average="binary", zero_division=0)
    return f1


def tune_threshold(val_probs, val_labels):
    """Highest threshold achieving >=95% recall on val positives (matches train.py)."""
    thresholds = np.linspace(0.0, 1.0, 10001)
    above = []
    for t in thresholds:
        pred = (val_probs >= t).astype(int)
        tp = np.sum((pred == 1) & (val_labels == 1))
        fn = np.sum((pred == 0) & (val_labels == 1))
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if recall >= 0.95:
            above.append((t, recall))
    if above:
        return max(above, key=lambda x: x[0])
    # fallback: maximize recall
    best = (0.0, -1.0)
    for t in thresholds:
        pred = (val_probs >= t).astype(int)
        tp = np.sum((pred == 1) & (val_labels == 1))
        fn = np.sum((pred == 0) & (val_labels == 1))
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if recall > best[1]:
            best = (t, recall)
    return best


def train_one(mode, train_items, val_items, device):
    set_seed(42)
    train_loader = DataLoader(UnitDataset(train_items, mode), batch_size=32, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(UnitDataset(val_items, mode), batch_size=32, shuffle=False, collate_fn=collate_fn)

    pos = sum(1 for x in train_items if x.get("label", 0.0) == 1)
    neg = sum(1 for x in train_items if x.get("label", 0.0) == 0)
    pos_w = neg / pos if pos > 0 else 1.5

    model = HyperedgeClassifier(768, FIXED_CONFIG["hidden_dim"], FIXED_CONFIG["dropout"]).to(device)
    opt = optim.Adam(model.parameters(), lr=FIXED_CONFIG["lr"], weight_decay=1e-5)
    crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_w], device=device))

    patience, min_loss, no_improve, best_state = 20, float("inf"), 0, None
    for epoch in range(1, 201):
        model.train()
        for x, mask, y, _ in train_loader:
            x, mask, y = x.to(device), mask.to(device), y.to(device)
            opt.zero_grad()
            logits, _ = model(x, mask)
            loss = crit(logits.squeeze(-1), y)
            loss.backward()
            opt.step()
        model.eval()
        vloss = 0.0
        with torch.no_grad():
            for x, mask, y, _ in val_loader:
                x, mask, y = x.to(device), mask.to(device), y.to(device)
                logits, _ = model(x, mask)
                vloss += crit(logits.squeeze(-1), y).item() * x.size(0)
        vloss /= len(val_items)
        if vloss < min_loss:
            min_loss, no_improve = vloss, 0
            best_state = {k: v.cpu() for k, v in model.state_dict().items()}
        else:
            no_improve += 1
            if no_improve >= patience:
                break

    model.load_state_dict({k: v.to(device) for k, v in best_state.items()})
    return model, min_loss


def main():
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    splits = PROJECT_ROOT / "data" / "splits"
    results = PROJECT_ROOT / "experiments" / "results"

    train_data = json.load(open(splits / "train_augmented.json"))
    val_data = json.load(open(splits / "val_features.json"))
    test_data = json.load(open(splits / "test_features.json"))
    oz_data = json.load(open(results / "eval_clean_negatives_oz_features.json"))
    aave_data = json.load(open(results / "eval_clean_negatives_aave_split.json"))
    oz_mapping = json.load(open(PROJECT_ROOT / "scratch" / "oz_split_mapping.json"))

    # OZ train/val split (matches train.py)
    oz_train, oz_val = [], []
    for item in oz_data:
        fp = item.get("file") or item.get("filePath")
        rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
        split = oz_mapping.get(rel, "holdout")
        if split == "train":
            oz_train.append(item)
        elif split == "val":
            oz_val.append(item)

    set_seed(42)
    oz_train_sorted = sorted(oz_train, key=lambda x: (x["file"], x["contract"], x["function"]))
    sampled_oz = random.sample(oz_train_sorted, K_OZ)

    aave_train = [i for i in aave_data if i.get("split") == "train"]
    aave_val = [i for i in aave_data if i.get("split") == "val"]
    set_seed(42)
    aave_train_sorted = sorted(aave_train, key=lambda x: (x["file"], x["contract"], x["function"]))
    sampled_aave = random.sample(aave_train_sorted, K_AAVE)

    train_items = train_data + sampled_oz + sampled_aave
    # validation for threshold tuning = codebase val (recall over its positives), matches train.py
    val_items = val_data

    print(f"Train items: {len(train_items)} (base {len(train_data)} + OZ {len(sampled_oz)} + Aave {len(sampled_aave)})")
    print(f"Val items (threshold): {len(val_items)} | Test items: {len(test_data)}")

    # cross/intra indices on test (shared)
    cross_idx = [i for i, it in enumerate(test_data) if it.get("is_cross_contract", False)]
    intra_idx = [i for i, it in enumerate(test_data) if not it.get("is_cross_contract", False)]

    store = {}
    for mode in MODES:
        print("\n" + "=" * 60)
        print(f"Training variant: {MODE_LABELS[mode]}")
        print("=" * 60)
        model, vloss = train_one(mode, train_items, val_items, device)

        val_probs, val_labels, _ = evaluate_model(
            model, DataLoader(UnitDataset(val_items, mode), batch_size=32, shuffle=False, collate_fn=collate_fn), device)
        thr, vrec = tune_threshold(val_probs, val_labels)

        test_probs, test_labels, test_items = evaluate_model(
            model, DataLoader(UnitDataset(test_data, mode), batch_size=32, shuffle=False, collate_fn=collate_fn), device)
        pred = (test_probs >= thr).astype(int)
        p, r, f1, _ = precision_recall_fscore_support(test_labels, pred, average="binary", zero_division=0)
        f2 = f2_score(p, r)
        pc, rc, _ = precision_recall_curve(test_labels, test_probs)
        pr_auc = auc(rc, pc)
        roc = roc_auc_score(test_labels, test_probs)
        cross_f1 = subset_f1(test_probs, test_labels, cross_idx, thr)
        intra_f1 = subset_f1(test_probs, test_labels, intra_idx, thr)

        per_class = {}
        vtypes = defaultdict(list)
        for i, it in enumerate(test_items):
            if it["label"] == 1:
                vtypes[it.get("vtype") or "Unknown"].append(i)
        for vt, idxs in vtypes.items():
            sp = test_probs[idxs]
            per_class[vt] = {"count": len(idxs), "recall": float(np.mean((sp >= thr).astype(int)))}

        store[mode] = dict(threshold=float(thr), val_loss=float(vloss), val_recall=float(vrec),
                           recall=r, precision=p, f1=f1, f2=f2, pr_auc=pr_auc, roc_auc=roc,
                           cross_f1=cross_f1, intra_f1=intra_f1, per_class=per_class)
        print(f"thr={thr:.4f} val_rec={vrec*100:.2f}% | TEST R={r*100:.2f} P={p*100:.2f} "
              f"F1={f1*100:.2f} F2={f2*100:.2f} PR-AUC={pr_auc*100:.2f} ROC={roc*100:.2f}")
        print(f"  per-class: " + " | ".join(f"{k}:{v['recall']*100:.2f}({v['count']})" for k, v in per_class.items()))

    # ---- write report ----
    def row(mode):
        m = store[mode]
        return (f"| **{MODE_LABELS[mode]}** | {m['recall']*100:.2f}% | {m['precision']*100:.2f}% | "
                f"{m['f1']*100:.2f}% | {m['f2']*100:.2f}% | {m['pr_auc']*100:.2f}% | {m['roc_auc']*100:.2f}% | "
                f"{m['cross_f1']*100:.2f}% | {m['intra_f1']*100:.2f}% |")

    all_vtypes = sorted({vt for mode in MODES for vt in store[mode]["per_class"]})

    def pc_row(mode):
        m = store[mode]["per_class"]
        cells = " | ".join(
            (f"{m[vt]['recall']*100:.2f}%" if vt in m else "—") for vt in all_vtypes)
        return f"| **{MODE_LABELS[mode]}** | {cells} |"

    report = f"""# HyperVul — Controlled Prediction-Unit Comparison

> **Controlled experiment.** All variants trained on identical data
> (base {len(train_data)} + {K_OZ} OZ-train + {K_AAVE} Aave-train negatives),
> identical fixed config (hidden_dim={FIXED_CONFIG['hidden_dim']}, dropout={FIXED_CONFIG['dropout']},
> lr={FIXED_CONFIG['lr']}), identical threshold rule (highest threshold with >=95% val recall),
> seed=42. The ONLY variable is which node types enter the hyperedge. "Ours" is
> re-trained and re-evaluated here, not copied from a previous iteration.

## 1. Interaction-Level Test Set ({len(test_data)} items: {int(sum(json.load(open(splits/'test_features.json'))[i]['label'] for i in range(len(test_data))))} pos)

| Model | Recall | Precision | F1 | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{row('function')}
{row('func_state')}
{row('func_callee')}
{row('full')}

## 2. Per-Vulnerability-Type Recall

| Model | {' | '.join(all_vtypes)} |
| :--- | {' | '.join([':---:'] * len(all_vtypes))} |
{pc_row('function')}
{pc_row('func_state')}
{pc_row('func_callee')}
{pc_row('full')}

## 3. Tuned thresholds / val recall
""" + "\n".join(
        f"- {MODE_LABELS[m]}: threshold={store[m]['threshold']:.4f}, val_recall={store[m]['val_recall']*100:.2f}%, val_loss={store[m]['val_loss']:.4f}"
        for m in MODES) + "\n"

    out = results / "unit_comparison_results.md"
    with open(out, "w") as fh:
        fh.write(report)
    json.dump(store, open(results / "unit_comparison_results.json", "w"), indent=2, default=float)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
