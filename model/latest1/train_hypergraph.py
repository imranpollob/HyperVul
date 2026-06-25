"""HyperVul Hypergraph Training Pipeline.

Replaces HyperedgeClassifier (pooling-only) with HypergraphNN (node->edge->node
message passing) to realize the theoretical advantage of hyperedge-based
vulnerability detection.

Architecture:
  1. Node->Hyperedge: attention pooling over member nodes
  2. Hyperedge->Node: mean aggregation + residual update
  3. Per-hyperedge binary classification head

This captures n-ary relational dependencies through hypergraph message passing,
which pairwise models (GCN/GAT) cannot represent without fragmenting joint
co-occurrence into independent dyads.
"""
import json
import sys
import os
import argparse
import random
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import defaultdict
from sklearn.metrics import precision_recall_curve, auc, roc_auc_score, precision_recall_fscore_support

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from torch_geometric.utils import scatter
from build_hypergraph import build_contract_graphs, ContractGraph
from src.models.hypergraph_nn import HypergraphNN
from src.models.ops import ProjectionHead, SupConLoss

SCL_LAMBDA = 0.5
SCL_TEMPERATURE = 0.1
SCL_PROJ_DIM = 128
SCL_HARD_NEG_WEIGHT = 3.0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="HyperVul Hypergraph Training with Message Passing.")
    p.add_argument("--no-scl", action="store_true")
    p.add_argument("--scl-lambda", type=float, default=SCL_LAMBDA)
    p.add_argument("--scl-temperature", type=float, default=SCL_TEMPERATURE)
    p.add_argument("--scl-hard-neg-weight", type=float, default=SCL_HARD_NEG_WEIGHT)
    p.add_argument("--scl-proj-dim", type=int, default=SCL_PROJ_DIM)
    p.add_argument("--scl-pretrain-epochs", type=int, default=15)
    p.add_argument("--no-asl", action="store_true")
    p.add_argument("--asl-gamma-neg", type=float, default=4.0)
    p.add_argument("--asl-gamma-pos", type=float, default=1.0)
    p.add_argument("--target-recall", type=float, default=0.95)
    p.add_argument("--out-tag", type=str, default="hypergraph")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--fix-k", type=int, default=100)
    p.add_argument("--hidden", type=int, default=256)
    p.add_argument("--dropout", type=float, default=0.3)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--epochs", type=int, default=200)
    p.add_argument("--patience", type=int, default=20)
    p.add_argument("--layers", type=int, default=2,
                   help="Number of message passing layers")
    p.add_argument("--use-skip", action="store_true", default=True,
                   help="Use skip connections in HypergraphNN")
    return p.parse_args(argv)


class AsymmetricLoss(nn.Module):
    def __init__(self, gamma_neg=4, gamma_pos=1, clip=0.05, eps=1e-8, pos_weight=None):
        super().__init__()
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip = clip
        self.eps = eps
        self.pos_weight = pos_weight

    def forward(self, x, y):
        xs_p = torch.sigmoid(x)
        xs_n = 1.0 - xs_p
        if self.clip is not None and self.clip > 0:
            xs_n = (xs_n + self.clip).clamp(max=1.0)
        loss_pos = y * torch.log(xs_p.clamp(min=self.eps)) * ((1.0 - xs_p) ** self.gamma_pos)
        loss_neg = (1.0 - y) * torch.log(xs_n.clamp(min=self.eps)) * ((1.0 - xs_n) ** self.gamma_neg)
        if self.pos_weight is not None:
            loss_pos = loss_pos * self.pos_weight
        loss = -loss_pos - loss_neg
        return loss.mean()


def has_external_calls(item):
    nf = item.get("node_features") or {}
    if nf.get("external_calls"):
        return True
    if item.get("callee_nodes"):
        return True
    return False


def scl_anchor_weights(items, hard_weight, device):
    w = [hard_weight if (float(it.get("label", 0.0)) == 0.0 and has_external_calls(it)) else 1.0
         for it in items]
    return torch.tensor(w, dtype=torch.float32, device=device)


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
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


def collate_graphs(graphs):
    """Collate ContractGraph objects into a single Batch."""
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


def iterate_batches(graphs, batch_size, shuffle=False, seed=0):
    """Iterate over graphs in batches."""
    idx = list(range(len(graphs)))
    if shuffle:
        random.Random(seed).shuffle(idx)
    for i in range(0, len(idx), batch_size):
        yield collate_graphs([graphs[j] for j in idx[i:i + batch_size]])


def evaluate_model(model, graphs, device, batch_size=16):
    """Evaluate model on a list of ContractGraphs."""
    model.eval()
    all_probs = []
    all_labels = []
    with torch.no_grad():
        for batch in iterate_batches(graphs, batch_size, shuffle=False):
            batch = batch.to(device)
            logits = model(batch)
            probs = torch.sigmoid(logits).cpu().numpy()
            all_probs.append(probs)
            all_labels.append(batch.edge_label.cpu().numpy())
    return np.concatenate(all_probs), np.concatenate(all_labels)


def main(args=None):
    if args is None:
        args = parse_args([])
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device} | seed={args.seed}")
    print(f"Config: layers={args.layers}, hidden={args.hidden}, dropout={args.dropout}, lr={args.lr}")

    # 1. Load flat JSON data
    splits_dir = PROJECT_ROOT / "data" / "splits"
    results_dir = PROJECT_ROOT / "experiments" / "latest1"

    print("Loading datasets...")
    with open(splits_dir / "train_augmented.json") as f:
        train_data = json.load(f)
    with open(splits_dir / "val_features.json") as f:
        val_data = json.load(f)
    with open(splits_dir / "test_features.json") as f:
        test_data = json.load(f)

    # Load clean negatives
    with open(results_dir / "eval_clean_negatives_oz_features.json") as f:
        oz_data = json.load(f)
    with open(results_dir / "eval_clean_negatives_aave_split.json") as f:
        aave_data = json.load(f)
    mapping_path = PROJECT_ROOT / "scratch" / "latest1" / "oz_split_mapping.json"
    oz_mapping = json.load(open(mapping_path))

    # Split OZ data
    oz_train_items = []
    for item in oz_data:
        fp = item.get('file') or item.get('filePath')
        rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
        split = oz_mapping.get(rel, "holdout")
        if split == "train":
            oz_train_items.append(item)

    aave_train_items = [item for item in aave_data if item.get("split") == "train"]

    # Sample clean negatives
    set_seed(args.seed)
    sorted_oz = sorted(oz_train_items, key=lambda x: (x.get('file', ''), x.get('contract', ''), x.get('function', '')))
    sampled_oz = random.sample(sorted_oz, min(100, len(sorted_oz)))
    sorted_aave = sorted(aave_train_items, key=lambda x: (x.get('file', ''), x.get('contract', ''), x.get('function', '')))
    sampled_aave = random.sample(sorted_aave, min(args.fix_k, len(sorted_aave)))

    train_items = train_data + sampled_oz + sampled_aave
    print(f"Training items: {len(train_data)} base + {len(sampled_oz)} OZ + {len(sampled_aave)} Aave = {len(train_items)}")

    # 2. Build contract graphs
    print("Building contract graphs...")
    train_graphs = build_contract_graphs(train_items)
    val_graphs = build_contract_graphs(val_data)
    test_graphs = build_contract_graphs(test_data)

    train_edges = sum(g.num_edges for g in train_graphs)
    val_edges = sum(g.num_edges for g in val_graphs)
    test_edges = sum(g.num_edges for g in test_graphs)
    print(f"Train: {len(train_graphs)} graphs, {train_edges} hyperedges")
    print(f"Val: {len(val_graphs)} graphs, {val_edges} hyperedges")
    print(f"Test: {len(test_graphs)} graphs, {test_edges} hyperedges")

    # 3. Initialize model
    model = HypergraphNN(
        dim=768, hidden=args.hidden, dropout=args.dropout,
        layers=args.layers, use_skip=args.use_skip
    ).to(device)

    proj_head = ProjectionHead(in_dim=args.hidden, hidden=256, out_dim=args.scl_proj_dim).to(device)
    supcon = SupConLoss(temperature=args.scl_temperature)

    params = list(model.parameters()) + (list(proj_head.parameters()) if not args.no_scl else [])
    optimizer = optim.Adam(params, lr=args.lr, weight_decay=1e-5)

    # 4. Compute pos_weight
    total_pos = sum(g.edge_label.sum().item() for g in train_graphs)
    total_neg = sum((g.edge_label == 0).sum().item() for g in train_graphs)
    pos_upweight = total_neg / max(total_pos, 1)
    print(f"Class balance: pos={total_pos}, neg={total_neg}, ratio=1:{total_neg/max(total_pos,1):.1f}")

    if args.no_asl:
        criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_upweight], device=device))
    else:
        criterion = AsymmetricLoss(
            gamma_neg=args.asl_gamma_neg, gamma_pos=args.asl_gamma_pos,
            pos_weight=torch.tensor([pos_upweight], device=device)
        )

    # 5. SCL pre-training
    use_scl = not args.no_scl
    if use_scl and args.scl_pretrain_epochs > 0:
        print(f"\nSCL pre-training for {args.scl_pretrain_epochs} epochs...")
        for ep in range(1, args.scl_pretrain_epochs + 1):
            model.train()
            proj_head.train()
            epoch_scl_loss = 0.0
            n_samples = 0
            for batch in iterate_batches(train_graphs, 16, shuffle=True, seed=args.seed * 1000 + ep):
                batch = batch.to(device)
                optimizer.zero_grad()

                # Get node embeddings after message passing
                h = torch.relu(model.in_proj(batch.node_feats))
                for l in range(model.layers):
                    edge_h = model.n2e[l](h[batch.inc_node], batch.inc_edge, batch.num_edges)
                    node_msg = scatter(
                        edge_h[batch.inc_edge], batch.inc_node, dim=0,
                        dim_size=batch.num_nodes, reduce="mean"
                    )
                    msg = model.drop(torch.relu(model.e2n[l](node_msg)))
                    h = model.norm[l](h + msg)

                # Get edge embeddings
                edge_h = model.final_pool(h[batch.inc_node], batch.inc_edge, batch.num_edges)

                # SCL on edge embeddings
                z = proj_head(edge_h)

                # Create items for anchor weights
                items = [{"label": l.item(), "node_features": {"external_calls": []}}
                         for l in batch.edge_label]
                weights = scl_anchor_weights(items, args.scl_hard_neg_weight, device)
                scl_loss = supcon(z, batch.edge_label, weights=weights)
                scl_loss.backward()
                optimizer.step()
                epoch_scl_loss += scl_loss.item() * batch.num_edges
                n_samples += batch.num_edges
            if ep % 5 == 0 or ep == args.scl_pretrain_epochs:
                print(f"  SCL Epoch {ep}/{args.scl_pretrain_epochs} | Loss: {epoch_scl_loss/n_samples:.4f}")

    # 6. Main training loop
    print(f"\nStarting main training for {args.epochs} epochs...")
    best_val_loss = float('inf')
    epochs_no_improve = 0
    best_model_state = None

    for epoch in range(1, args.epochs + 1):
        model.train()
        proj_head.train()
        train_loss = 0.0
        n_samples = 0

        for batch in iterate_batches(train_graphs, 16, shuffle=True, seed=args.seed * 1000 + epoch):
            batch = batch.to(device)
            optimizer.zero_grad()

            logits = model(batch)
            ce_loss = criterion(logits, batch.edge_label)
            loss = ce_loss

            if use_scl and args.scl_lambda > 0:
                # Get pooled edge embeddings for SCL
                h = torch.relu(model.in_proj(batch.node_feats))
                for l in range(model.layers):
                    edge_h = model.n2e[l](h[batch.inc_node], batch.inc_edge, batch.num_edges)
                    node_msg = scatter(
                        edge_h[batch.inc_edge], batch.inc_node, dim=0,
                        dim_size=batch.num_nodes, reduce="mean"
                    )
                    msg = model.drop(torch.relu(model.e2n[l](node_msg)))
                    h = model.norm[l](h + msg)
                edge_h = model.final_pool(h[batch.inc_node], batch.inc_edge, batch.num_edges)
                z = proj_head(edge_h)
                items = [{"label": l.item(), "node_features": {"external_calls": []}}
                         for l in batch.edge_label]
                weights = scl_anchor_weights(items, args.scl_hard_neg_weight, device)
                scl_loss = supcon(z, batch.edge_label, weights=weights)
                loss = ce_loss + args.scl_lambda * scl_loss

            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch.num_edges
            n_samples += batch.num_edges

        train_loss /= n_samples

        # Validation
        model.eval()
        val_loss = 0.0
        val_n = 0
        with torch.no_grad():
            for batch in iterate_batches(val_graphs, 16, shuffle=False):
                batch = batch.to(device)
                logits = model(batch)
                loss = criterion(logits, batch.edge_label)
                val_loss += loss.item() * batch.num_edges
                val_n += batch.num_edges

        val_loss /= val_n

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:3d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            best_model_state = {k: v.cpu() for k, v in model.state_dict().items()}
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= args.patience:
                print(f"Early stopping at epoch {epoch}")
                break

    # Restore best model
    model.load_state_dict({k: v.to(device) for k, v in best_model_state.items()})

    # 7. Threshold selection on validation set
    print("\nTuning threshold on validation set...")
    val_probs, val_labels = evaluate_model(model, val_graphs, device)
    thresholds = np.linspace(0.000, 1.000, 10001)
    recall_above_target = []
    for t in thresholds:
        preds = (val_probs >= t).astype(int)
        tp = np.sum((preds == 1) & (val_labels == 1))
        fn = np.sum((preds == 0) & (val_labels == 1))
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        if recall >= args.target_recall:
            recall_above_target.append((t, recall))

    if recall_above_target:
        t_opt, r_opt = max(recall_above_target, key=lambda x: x[0])
    else:
        recalls = []
        for t in thresholds:
            preds = (val_probs >= t).astype(int)
            tp = np.sum((preds == 1) & (val_labels == 1))
            fn = np.sum((preds == 0) & (val_labels == 1))
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            recalls.append((t, recall))
        t_opt, r_opt = max(recalls, key=lambda x: x[1])

    print(f"Selected threshold: {t_opt:.4f} (val recall: {r_opt*100:.2f}%)")

    # 8. Test evaluation
    print("\nEvaluating on test set...")
    test_probs, test_labels = evaluate_model(model, test_graphs, device)
    test_preds = (test_probs >= t_opt).astype(int)

    p_opt, r_opt, f1_opt, _ = precision_recall_fscore_support(
        test_labels, test_preds, average='binary', zero_division=0
    )
    p_curve, r_curve, _ = precision_recall_curve(test_labels, test_probs)
    pr_auc = auc(r_curve, p_curve)
    roc_auc = roc_auc_score(test_labels, test_probs)
    f2_opt = (5 * p_opt * r_opt) / (4 * p_opt + r_opt) if (4 * p_opt + r_opt) > 0 else 0.0

    print(f"\n{'='*60}")
    print(f"Test Results (threshold={t_opt:.4f}):")
    print(f"  Precision: {p_opt*100:.2f}%")
    print(f"  Recall:    {r_opt*100:.2f}%")
    print(f"  F1-Score:  {f1_opt*100:.2f}%")
    print(f"  F2-Score:  {f2_opt*100:.2f}%")
    print(f"  PR-AUC:    {pr_auc*100:.2f}%")
    print(f"  ROC-AUC:   {roc_auc*100:.2f}%")
    print(f"{'='*60}")

    # 9. Save results
    os.makedirs(results_dir / "ablation", exist_ok=True)

    tag = f"_{args.out_tag}_seed{args.seed}"
    artifact = {
        "arm": args.out_tag, "seed": args.seed,
        "layers": args.layers, "hidden": args.hidden,
        "threshold": float(t_opt), "val_recall": float(r_opt),
        "test": {
            "n": len(test_labels), "precision": float(p_opt), "recall": float(r_opt),
            "f1": float(f1_opt), "f2": float(f2_opt), "pr_auc": float(pr_auc),
            "roc_auc": float(roc_auc),
            "probs": [float(p) for p in test_probs],
            "labels": [int(l) for l in test_labels],
        },
    }
    with open(results_dir / "ablation" / f"{args.out_tag}_seed{args.seed}.json", "w") as fh:
        json.dump(artifact, fh, indent=2)
    print(f"\nSaved results to ablation/{args.out_tag}_seed{args.seed}.json")

    # Save checkpoint
    checkpoint_dir = PROJECT_ROOT / "model" / "latest1"
    os.makedirs(checkpoint_dir, exist_ok=True)
    torch.save(best_model_state, checkpoint_dir / f"hypergraph_checkpoint{tag}.pt")
    print(f"Saved checkpoint to model/latest1/hypergraph_checkpoint{tag}.pt")


if __name__ == "__main__":
    main(parse_args())
