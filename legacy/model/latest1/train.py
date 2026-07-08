import json
import sys
import os
import argparse
import random
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from collections import defaultdict
from sklearn.metrics import precision_recall_curve, auc, roc_auc_score, precision_recall_fscore_support

# Setup paths
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))

try:
    from model.model import HyperedgeClassifier
except ModuleNotFoundError:
    from model import HyperedgeClassifier

from src.models.ops import ProjectionHead, SupConLoss, build_node_types
from src.models.symbolic import SYM_DIM, sym_mask

# ---------------------------------------------------------------------------
# Stage 3 — Supervised Contrastive Calibration defaults
#   L = L_CE + lambda * L_SCL, with SCL applied to a normalized projection of the
#   pooled hyperedge embedding. Clean (label=0) interactions that contain external
#   calls are up-weighted as hard anchors to crush the OOD false-positive rate.
# ---------------------------------------------------------------------------
SCL_LAMBDA = 0.5            # weight of the contrastive term
SCL_TEMPERATURE = 0.1      # SupCon temperature
SCL_PROJ_DIM = 128         # projection head output dim
SCL_HARD_NEG_WEIGHT = 3.0  # per-anchor weight for clean-with-external-call items


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="HyperVul iteration-3 training with "
                                            "Supervised Contrastive Calibration (Stage 3).")
    p.add_argument("--no-scl", action="store_true",
                   help="Disable SCL and train CE-only (baseline ablation).")
    p.add_argument("--no-localize", action="store_true",
                   help="Disable the interaction-aware LocalizationHead and use the pure "
                        "set-pool MLP path (bypasses loc_gate fusion).")
    p.add_argument("--scl-lambda", type=float, default=SCL_LAMBDA,
                   help="Weight lambda of the SCL term in L = L_CE + lambda*L_SCL.")
    p.add_argument("--scl-temperature", type=float, default=SCL_TEMPERATURE)
    p.add_argument("--scl-hard-neg-weight", type=float, default=SCL_HARD_NEG_WEIGHT,
                   help="Per-anchor SCL weight for clean (label=0) items with external calls.")
    p.add_argument("--scl-proj-dim", type=int, default=SCL_PROJ_DIM)
    p.add_argument("--scl-pretrain-epochs", type=int, default=15,
                   help="Number of epochs for SCL pre-training (Stage 3 sequence).")
    p.add_argument("--no-asl", action="store_true",
                   help="Disable Asymmetric Loss (ASL) and use standard Binary Cross Entropy (BCE).")
    p.add_argument("--out-tag", type=str, default="",
                   help="Optional suffix for checkpoint/report filenames to avoid "
                        "clobbering across ablations (e.g. 'scl', 'baseline').")
    p.add_argument("--seed", type=int, default=42,
                   help="Single training seed for this run. Multi-seed = invoke once per "
                        "seed; experiments/aggregate_ablation.py pools the per-seed JSONs.")
    p.add_argument("--fix-k", type=int, default=None,
                   help="Train at this fixed K_app (Aave clean negatives) and SKIP the "
                        "K-sweep. De-confounds the ablation (use e.g. --fix-k 100 in all arms).")
    p.add_argument("--sym-mode", choices=["off", "none", "security", "full"], default="off",
                   help="Stage-2 symbolic node features concatenated onto embeddings: "
                        "off=768-d only; none=zeroed symbolic (arch-matched baseline); "
                        "security=safety slots only (target_kind/security_context/cross/nonReentrant); "
                        "full=all symbolic. Requires *_sym.json sidecars (build_security_features.py).")
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
        # x: logits, y: labels (0 or 1)
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


def has_external_calls(item) -> bool:
    """True if the hyperedge contains at least one callee/external call, across both the
    SmartBERT feature schema (node_features.external_calls) and the Stage-2 bottleneck
    schema (callee_nodes)."""
    nf = item.get("node_features") or {}
    if nf.get("external_calls"):
        return True
    if item.get("callee_nodes"):
        return True
    return False


def scl_anchor_weights(items, hard_weight: float, device) -> torch.Tensor:
    """Per-anchor SCL weight: hard_weight for clean (label=0) hyperedges that have
    external calls (our dominant false-positive trigger), 1.0 otherwise."""
    w = [hard_weight if (float(it.get("label", 0.0)) == 0.0 and has_external_calls(it)) else 1.0
         for it in items]
    return torch.tensor(w, dtype=torch.float32, device=device)

# Fix random seed
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

class HyperedgeDataset(Dataset):
    # Class-level symbolic mask (length SYM_DIM) set once per run in main(); when not None,
    # each node's masked Stage-2 symbolic vector is concatenated onto its 768-d embedding.
    sym_mask = None

    def __init__(self, data_list):
        self.items = data_list

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        nf = item['node_features']
        sv_names = list(nf['state_vars'].keys())
        # Node sequence: [func] + [state vars] + [external calls]
        emb_nodes = ([nf['function']]
                     + [nf['state_vars'][n] for n in sv_names]
                     + [ec['embedding'] for ec in nf['external_calls']])

        mask = HyperedgeDataset.sym_mask
        if mask is not None:
            sym = item.get('_sym')
            ncall = len(nf['external_calls'])
            zero = [0.0] * SYM_DIM
            if sym is not None:
                csym = [(sym['external_calls'][i] if i < len(sym['external_calls']) else zero)
                        for i in range(ncall)]
                sym_nodes = ([sym['function']]
                             + [sym['state_vars'].get(n, zero) for n in sv_names]
                             + csym)
            else:                                  # source unresolved -> zero symbolic
                sym_nodes = [zero for _ in emb_nodes]
            node_feats = [e + [v * m for v, m in zip(s, mask)]
                          for e, s in zip(emb_nodes, sym_nodes)]
        else:
            node_feats = emb_nodes

        x = torch.tensor(node_feats, dtype=torch.float32)
        return x, float(item.get('label', 0.0)), item

def collate_fn(batch):
    tensors, labels, items = zip(*batch)
    lengths = [t.size(0) for t in tensors]
    max_len = max(lengths)
    
    padded_tensors = []
    masks = []
    for t in tensors:
        num_nodes = t.size(0)
        padding_size = max_len - num_nodes
        if padding_size > 0:
            padded_t = torch.cat([t, torch.zeros(padding_size, t.size(1))], dim=0)
            mask = torch.cat([torch.ones(num_nodes, dtype=torch.bool), torch.zeros(padding_size, dtype=torch.bool)], dim=0)
        else:
            padded_t = t
            mask = torch.ones(num_nodes, dtype=torch.bool)
        padded_tensors.append(padded_t)
        masks.append(mask)
        
    return torch.stack(padded_tensors), torch.stack(masks), torch.tensor(labels, dtype=torch.float32), items

def evaluate_model(model, dataloader, device):
    model.eval()
    all_probs = []
    all_labels = []
    all_items = []
    
    with torch.no_grad():
        for x, mask, labels, batch_items in dataloader:
            x, mask = x.to(device), mask.to(device)
            node_types = build_node_types(batch_items, x.shape[1], device=device)
            logits, _ = model(x, mask, node_types)
            probs = torch.sigmoid(logits).squeeze(-1).cpu().numpy()
            all_probs.extend(probs)
            all_labels.extend(labels.numpy())
            all_items.extend(batch_items)
            
    return np.array(all_probs), np.array(all_labels), all_items

def main(args=None):
    if args is None:
        args = parse_args([])
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device} | seed={args.seed} | fix_k={args.fix_k}")
    use_scl = not args.no_scl
    use_localize = not args.no_localize
    use_sym = args.sym_mode != "off"
    HyperedgeDataset.sym_mask = sym_mask(args.sym_mode) if use_sym else None
    input_dim = 768 + (SYM_DIM if use_sym else 0)
    print(f"Supervised Contrastive Calibration: {'ON' if use_scl else 'OFF'} "
          f"(lambda={args.scl_lambda}, temp={args.scl_temperature}, "
          f"hard_neg_weight={args.scl_hard_neg_weight}, proj_dim={args.scl_proj_dim})")
    print(f"Interaction-Aware Localization Head: {'ON' if use_localize else 'OFF'}")
    print(f"Symbolic node features: mode={args.sym_mode} | input_dim={input_dim}")
    
    # 1. Load datasets
    splits_dir = PROJECT_ROOT / "data" / "splits"
    results_dir = PROJECT_ROOT / "experiments" / "latest1"
    
    print("Loading datasets...")
    with open(splits_dir / "train_augmented.json") as f:
        train_data = json.load(f)
    with open(splits_dir / "val_features.json") as f:
        val_data = json.load(f)
    with open(splits_dir / "test_features.json") as f:
        test_data = json.load(f)
    with open(results_dir / "eval_clean_negatives_oz_features.json") as f:
        oz_data = json.load(f)
    with open(results_dir / "eval_clean_negatives_external.json") as f:
        external_data = json.load(f)
    with open(results_dir / "eval_clean_negatives_aave_split.json") as f:
        aave_data = json.load(f)
    with open(results_dir / "eval_clean_negatives_liquity.json") as f:
        liquity_data = json.load(f)
        
    print(f"Loaded train: {len(train_data)}, val: {len(val_data)}, test: {len(test_data)}, OZ: {len(oz_data)}, External (Maker/Bancor): {len(external_data)}, Aave: {len(aave_data)}, Liquity: {len(liquity_data)}.")

    # Attach Stage-2 symbolic sidecars (index-aligned *_sym.json) when sym features are on.
    def attach_sym(data, features_path):
        if not use_sym:
            return
        sp = features_path.with_name(features_path.stem + "_sym.json")
        if not sp.exists():
            raise FileNotFoundError(
                f"--sym-mode {args.sym_mode} needs sidecar {sp.name}; "
                f"run: python scripts/build_security_features.py")
        syms = json.load(open(sp))
        assert len(syms) == len(data), f"sidecar length {len(syms)} != data {len(data)} ({sp.name})"
        for it, s in zip(data, syms):
            it['_sym'] = s

    attach_sym(train_data, splits_dir / "train_augmented.json")
    attach_sym(val_data, splits_dir / "val_features.json")
    attach_sym(test_data, splits_dir / "test_features.json")
    attach_sym(oz_data, results_dir / "eval_clean_negatives_oz_features.json")
    attach_sym(external_data, results_dir / "eval_clean_negatives_external.json")
    attach_sym(aave_data, results_dir / "eval_clean_negatives_aave_split.json")
    attach_sym(liquity_data, results_dir / "eval_clean_negatives_liquity.json")

    # Load OZ split mapping
    mapping_path = PROJECT_ROOT / "scratch" / "latest1" / "oz_split_mapping.json"
    with open(mapping_path) as f:
        oz_mapping = json.load(f)
        
    # Split OZ data
    oz_train_data = []
    oz_val_data = []
    oz_holdout_data = []
    for item in oz_data:
        fp = item.get('file') or item.get('filePath')
        rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
        split = oz_mapping.get(rel, "holdout")
        if split == "train":
            oz_train_data.append(item)
        elif split == "val":
            oz_val_data.append(item)
        else:
            oz_holdout_data.append(item)
            
    print(f"OZ Splits - Train: {len(oz_train_data)}, Val: {len(oz_val_data)}, Holdout: {len(oz_holdout_data)}")
    
    # Split Aave data
    aave_train_data = [item for item in aave_data if item.get("split") == "train"]
    aave_val_data = [item for item in aave_data if item.get("split") == "val"]
    print(f"Aave Splits - Train: {len(aave_train_data)}, Val: {len(aave_val_data)}")
    
    # Split External data
    makerdao_data = [item for item in external_data if item.get("source") == "MakerDAO"]
    bancor_data = [item for item in external_data if item.get("source") == "Bancor"]
    print(f"External Splits - MakerDAO: {len(makerdao_data)}, Bancor: {len(bancor_data)}")
    
    # Sample fixed K_oz = 100 clean negatives from oz_train_data (reproducibly, per seed)
    set_seed(args.seed)
    sorted_oz_train = sorted(oz_train_data, key=lambda x: (x['file'], x['contract'], x['function']))
    sampled_oz_train = random.sample(sorted_oz_train, 100)
    
    # Prepare val loaders
    val_dataset = HyperedgeDataset(val_data)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    oz_val_dataset = HyperedgeDataset(oz_val_data)
    oz_val_loader = DataLoader(oz_val_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    aave_val_dataset = HyperedgeDataset(aave_val_data)
    aave_val_loader = DataLoader(aave_val_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    test_dataset = HyperedgeDataset(test_data)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    # We sweep K_app (Aave clean negatives added to training); --fix-k pins it (de-confound).
    # Available Aave train: 225
    sweep_K = [args.fix_k] if args.fix_k is not None else [0, 50, 100, 150, 200, 225]
    sweep_results = []

    for K in sweep_K:
        print("\n" + "="*60)
        print(f"Running Sweep for K_app = {K} (Adding {K} Aave clean negatives to training)")
        print("="*60)

        # Set seed for reproducibility of sweep sampling and training
        set_seed(args.seed)
        
        # Deterministically sample K items from aave_train_data
        sorted_aave_train = sorted(aave_train_data, key=lambda x: (x['file'], x['contract'], x['function']))
        if K > 0:
            sampled_aave_train = random.sample(sorted_aave_train, K)
        else:
            sampled_aave_train = []
            
        # Combine train dataset: codebase + 100 OZ clean negatives + K Aave clean negatives
        sweep_train_data = train_data + sampled_oz_train + sampled_aave_train
        
        train_dataset = HyperedgeDataset(sweep_train_data)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
        
        # Calculate pos_weight
        pos_count = sum(1 for x in sweep_train_data if x.get('label', 0.0) == 1)
        neg_count = sum(1 for x in sweep_train_data if x.get('label', 0.0) == 0)
        pos_upweight = neg_count / pos_count if pos_count > 0 else 1.5
        
        # Initialize model (+ projection head for contrastive calibration)
        model = HyperedgeClassifier(input_dim=input_dim, hidden_dim=256, dropout=0.3,
                                    localize=use_localize).to(device)
        proj_head = ProjectionHead(in_dim=input_dim, hidden=256, out_dim=args.scl_proj_dim).to(device)
        supcon = SupConLoss(temperature=args.scl_temperature)
        params = list(model.parameters()) + (list(proj_head.parameters()) if use_scl else [])
        optimizer = optim.Adam(params, lr=1e-3, weight_decay=1e-5)
        
        if args.no_asl:
            criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_upweight], device=device))
        else:
            criterion = AsymmetricLoss(pos_weight=torch.tensor([pos_upweight], device=device))
        
        # SCL pre-training phase (if use_scl and args.scl_pretrain_epochs > 0)
        if use_scl and args.scl_pretrain_epochs > 0:
            print(f"SCL pre-training phase for {args.scl_pretrain_epochs} epochs...")
            for ep in range(1, args.scl_pretrain_epochs + 1):
                model.train()
                proj_head.train()
                epoch_scl_loss = 0.0
                for x, mask, labels, batch_items in train_loader:
                    x, mask, labels = x.to(device), mask.to(device), labels.to(device)
                    optimizer.zero_grad()
                    node_types = build_node_types(batch_items, x.shape[1], device=device)
                    _, pooled, _, _ = model.encode(x, mask, node_types)
                    z = proj_head(pooled)
                    weights = scl_anchor_weights(batch_items, args.scl_hard_neg_weight, device)
                    scl_loss = supcon(z, labels, weights=weights)
                    scl_loss.backward()
                    optimizer.step()
                    epoch_scl_loss += scl_loss.item() * x.size(0)
                epoch_scl_loss /= len(train_dataset)
                if ep % 5 == 0 or ep == args.scl_pretrain_epochs:
                    print(f"  SCL Pre-train Epoch {ep}/{args.scl_pretrain_epochs} | SCL Loss: {epoch_scl_loss:.4f}")

        # Train with early stopping on val_data
        patience = 20
        best_val_loss = float('inf')
        epochs_no_improve = 0
        sweep_model_state = None
        
        for epoch in range(1, 201):
            model.train()
            proj_head.train()
            train_loss = 0.0
            for x, mask, labels, batch_items in train_loader:
                x, mask, labels = x.to(device), mask.to(device), labels.to(device)
                optimizer.zero_grad()
                # Encode once: logits fuse the set-pool head with the interaction-aware
                # localization logit (Stage 4); pooled feeds the SCL projection (Stage 3).
                node_types = build_node_types(batch_items, x.shape[1], device=device)
                logits, pooled, _, _ = model.encode(x, mask, node_types)
                ce_loss = criterion(logits.squeeze(-1), labels)
                loss = ce_loss
                if use_scl and args.scl_lambda > 0:
                    z = proj_head(pooled)
                    weights = scl_anchor_weights(batch_items, args.scl_hard_neg_weight, device)
                    scl_loss = supcon(z, labels, weights=weights)
                    loss = ce_loss + args.scl_lambda * scl_loss
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * x.size(0)
            train_loss /= len(train_dataset)
            
            # Validation evaluation
            model.eval()
            proj_head.eval()
            val_loss = 0.0
            with torch.no_grad():
                for x, mask, labels, val_items in val_loader:
                    x, mask, labels = x.to(device), mask.to(device), labels.to(device)
                    node_types = build_node_types(val_items, x.shape[1], device=device)
                    logits, _ = model(x, mask, node_types)
                    # Early stopping on CE/ASL only (SCL is a training-time regularizer).
                    loss = criterion(logits.squeeze(-1), labels)
                    val_loss += loss.item() * x.size(0)
            val_loss /= len(val_dataset)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                epochs_no_improve = 0
                sweep_model_state = {k: v.cpu() for k, v in model.state_dict().items()}
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= patience:
                    break
                    
        # Restore best weights for this sweep
        model.load_state_dict({k: v.to(device) for k, v in sweep_model_state.items()})
        
        # Tune threshold on val_loader to achieve >= 95% recall
        val_probs, val_labels, _ = evaluate_model(model, val_loader, device)
        thresholds = np.linspace(0.000, 1.000, 10001)
        recall_above_95 = []
        for t in thresholds:
            preds = (val_probs >= t).astype(int)
            tp = np.sum((preds == 1) & (val_labels == 1))
            fn = np.sum((preds == 0) & (val_labels == 1))
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            if recall >= 0.95:
                recall_above_95.append((t, recall))
                
        if recall_above_95:
            t_opt, r_opt = max(recall_above_95, key=lambda x: x[0])
        else:
            recalls = []
            for t in thresholds:
                preds = (val_probs >= t).astype(int)
                tp = np.sum((preds == 1) & (val_labels == 1))
                fn = np.sum((preds == 0) & (val_labels == 1))
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                recalls.append((t, recall))
            t_opt, r_opt = max(recalls, key=lambda x: x[1])
            
        # Evaluate FPR on OZ-Val and Aave-Val
        oz_val_probs, _, _ = evaluate_model(model, oz_val_loader, device)
        oz_val_preds = (oz_val_probs >= t_opt).astype(int)
        fp_oz_val = np.sum(oz_val_preds == 1)
        fpr_oz_val = fp_oz_val / len(oz_val_data)
        
        aave_val_probs, _, _ = evaluate_model(model, aave_val_loader, device)
        aave_val_preds = (aave_val_probs >= t_opt).astype(int)
        fp_aave_val = np.sum(aave_val_preds == 1)
        fpr_aave_val = fp_aave_val / len(aave_val_data)
        
        combined_val_fpr = (fp_oz_val + fp_aave_val) / (len(oz_val_data) + len(aave_val_data))
        
        print(f"K_app={K} | Best Val Loss: {best_val_loss:.4f} | Threshold: {t_opt:.4f} | Val Recall: {r_opt*100:.2f}% | Combined Val FPR: {combined_val_fpr*100:.2f}% (OZ: {fpr_oz_val*100:.2f}%, Aave: {fpr_aave_val*100:.2f}%)")
        
        sweep_results.append({
            "K": K,
            "val_loss": best_val_loss,
            "threshold": t_opt,
            "val_recall": r_opt,
            "combined_val_fpr": combined_val_fpr,
            "oz_val_fpr": fpr_oz_val,
            "aave_val_fpr": fpr_aave_val,
            "model_state": sweep_model_state,
            "total_pos": pos_count,
            "total_neg": neg_count
        })
        
    # Select best K_app. With --fix-k there is a single trained model; otherwise pick the
    # lowest combined validation FPR in the stable region (50, 100, 150).
    if args.fix_k is not None:
        best_sweep = sweep_results[0]
    else:
        stable_results = [r for r in sweep_results if r["K"] in (50, 100, 150)]
        best_sweep = min(stable_results, key=lambda x: (x["combined_val_fpr"], x["val_loss"]))
    best_K = best_sweep["K"]
    best_model_state = best_sweep["model_state"]
    best_threshold = best_sweep["threshold"]
    best_recall_val = best_sweep["val_recall"]
    final_pos_in_train = best_sweep["total_pos"]
    final_neg_in_train = best_sweep["total_neg"]
    
    print("\n" + "="*60)
    print(f"Sweep completed. Selected Best K_app: {best_K} with Combined Val FPR: {best_sweep['combined_val_fpr']*100:.2f}%")
    print("="*60)
    
    # Save checkpoint (tag + seed suffixed to keep ablation runs from clobbering each other)
    arm = args.out_tag or "run"
    tag = f"_{arm}_seed{args.seed}"
    checkpoint_dir = PROJECT_ROOT / "model/latest1"
    os.makedirs(checkpoint_dir, exist_ok=True)
    torch.save(best_model_state, checkpoint_dir / f"iteration3_checkpoint{tag}.pt")

    with open(checkpoint_dir / f"threshold_config_iter3{tag}.json", "w") as fh:
        json.dump({"best_threshold": float(best_threshold), "best_K": best_K, "val_recall": float(best_recall_val)}, fh, indent=2)
        
    # Re-initialize best model for evaluation (same localize/input_dim -> matching state_dict keys)
    model = HyperedgeClassifier(input_dim=input_dim, hidden_dim=256, dropout=0.3,
                                localize=use_localize).to(device)
    model.load_state_dict({k: v.to(device) for k, v in best_model_state.items()})
    model.eval()
    
    # ---------------------------------------------------------------------------
    # EVALUATION EXACTLY ONCE ON HOLDOUT SETS
    # ---------------------------------------------------------------------------
    print("\nEvaluating on holdout sets...")
    
    # (a) OZ-Holdout
    oz_holdout_dataset = HyperedgeDataset(oz_holdout_data)
    oz_holdout_loader = DataLoader(oz_holdout_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    oz_holdout_probs, _, _ = evaluate_model(model, oz_holdout_loader, device)
    oz_holdout_preds = (oz_holdout_probs >= best_threshold).astype(int)
    fp_oz_holdout = np.sum(oz_holdout_preds == 1)
    fpr_oz_holdout = fp_oz_holdout / len(oz_holdout_data)
    
    # (b) MakerDAO DSS (External)
    makerdao_dataset = HyperedgeDataset(makerdao_data)
    makerdao_loader = DataLoader(makerdao_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    makerdao_probs, _, _ = evaluate_model(model, makerdao_loader, device)
    makerdao_preds = (makerdao_probs >= best_threshold).astype(int)
    fp_makerdao = np.sum(makerdao_preds == 1)
    fpr_makerdao = fp_makerdao / len(makerdao_data)
    
    # (c) Bancor V3 (External)
    bancor_dataset = HyperedgeDataset(bancor_data)
    bancor_loader = DataLoader(bancor_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    bancor_probs, _, _ = evaluate_model(model, bancor_loader, device)
    bancor_preds = (bancor_probs >= best_threshold).astype(int)
    fp_bancor = np.sum(bancor_preds == 1)
    fpr_bancor = fp_bancor / len(bancor_data)
    
    # (d) Liquity V1 (Fresh External Holdout Probe)
    liquity_dataset = HyperedgeDataset(liquity_data)
    liquity_loader = DataLoader(liquity_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    liquity_probs, _, _ = evaluate_model(model, liquity_loader, device)
    liquity_preds = (liquity_probs >= best_threshold).astype(int)
    fp_liquity = np.sum(liquity_preds == 1)
    fpr_liquity = fp_liquity / len(liquity_data)
    
    # Calculate Wilson confidence intervals
    def wilson_interval(successes, total):
        if total == 0:
            return 0.0, 0.0
        p_hat = successes / total
        z = 1.96
        denom = 1 + z**2 / total
        center = (p_hat + z**2 / (2 * total)) / denom
        spread = z * np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * total)) / total) / denom
        return max(0.0, center - spread), min(1.0, center + spread)
        
    oz_ci_lower, oz_ci_upper = wilson_interval(fp_oz_holdout, len(oz_holdout_data))
    maker_ci_lower, maker_ci_upper = wilson_interval(fp_makerdao, len(makerdao_data))
    bancor_ci_lower, bancor_ci_upper = wilson_interval(fp_bancor, len(bancor_data))
    liquity_ci_lower, liquity_ci_upper = wilson_interval(fp_liquity, len(liquity_data))
    
    # Evaluate on standard test set
    test_probs, test_labels, test_items = evaluate_model(model, test_loader, device)
    test_preds = (test_probs >= best_threshold).astype(int)
    
    p_opt, r_opt, f1_opt, _ = precision_recall_fscore_support(test_labels, test_preds, average='binary', zero_division=0)
    p_curve, r_curve, _ = precision_recall_curve(test_labels, test_probs)
    pr_auc = auc(r_curve, p_curve)
    roc_auc = roc_auc_score(test_labels, test_probs)
    f2_opt = (5 * p_opt * r_opt) / (4 * p_opt + r_opt) if (4 * p_opt + r_opt) > 0 else 0.0
    
    # Cross vs Intra contract on test
    cross_indices = [idx for idx, item in enumerate(test_items) if item.get('is_cross_contract', False)]
    intra_indices = [idx for idx, item in enumerate(test_items) if not item.get('is_cross_contract', False)]
    
    def evaluate_subset(probs, labels, indices, threshold):
        if len(indices) == 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        sub_probs = probs[indices]
        sub_labels = labels[indices]
        sub_preds = (sub_probs >= threshold).astype(int)
        p, r, f1, _ = precision_recall_fscore_support(sub_labels, sub_preds, average='binary', zero_division=0)
        f2 = (5 * p * r) / (4 * p + r) if (4 * p + r) > 0 else 0.0
        if len(np.unique(sub_labels)) > 1:
            p_c, r_c, _ = precision_recall_curve(sub_labels, sub_probs)
            sub_pr_auc = auc(r_c, p_c)
            sub_roc_auc = roc_auc_score(sub_labels, sub_probs)
        else:
            sub_pr_auc = 0.0
            sub_roc_auc = 0.0
        return p, r, f1, f2, sub_pr_auc, sub_roc_auc
        
    cross_p, cross_r, cross_f1, cross_f2, cross_pr_auc, cross_roc_auc = evaluate_subset(test_probs, test_labels, cross_indices, best_threshold)
    intra_p, intra_r, intra_f1, intra_f2, intra_pr_auc, intra_roc_auc = evaluate_subset(test_probs, test_labels, intra_indices, best_threshold)
    
    # Per vulnerability type recalls
    vuln_types = defaultdict(list)
    for idx, item in enumerate(test_items):
        if item['label'] == 1:
            vtype = item.get('vtype') or "Unknown"
            vuln_types[vtype].append(idx)
            
    vuln_recalls = {}
    print("\nPer-vulnerability-type recall on test set:")
    for vtype, indices in vuln_types.items():
        sub_probs = test_probs[indices]
        sub_preds = (sub_probs >= best_threshold).astype(int)
        tp = np.sum(sub_preds == 1)
        rec = tp / len(indices)
        vuln_recalls[vtype] = {"count": len(indices), "recall": rec}
        print(f"  {vtype}: count={len(indices)}, recall={rec*100:.2f}%")
        
    delegatecall_key = next((k for k in vuln_recalls if "delegate" in k.lower()), None)
    if delegatecall_key:
        if vuln_recalls[delegatecall_key]["count"] == 0:
            vuln_recalls[delegatecall_key]["recall"] = "Unevaluated"
    else:
        vuln_recalls["Delegatecall (SWC-112)"] = {"count": 0, "recall": "Unevaluated"}
        
    # ---------------------------------------------------------------------------
    # Persist machine-readable per-seed/per-arm artifact for cross-run aggregation
    # (experiments/aggregate_ablation.py pools these into the multi-seed table).
    # ---------------------------------------------------------------------------
    def _ids(data_list):
        return [f"{it.get('contract')}::{it.get('function') or it.get('ast_function')}"
                for it in data_list]

    def _holdout_record(probs, data_list, threshold):
        probs = [float(p) for p in probs]
        preds = [int(p >= threshold) for p in probs]
        return {"n": len(data_list), "fp": int(sum(preds)),
                "fpr": (sum(preds) / len(data_list)) if data_list else 0.0,
                "threshold": float(threshold), "probs": probs, "ids": _ids(data_list)}

    ablation_dir = results_dir / "ablation"
    os.makedirs(ablation_dir, exist_ok=True)
    artifact = {
        "arm": arm, "seed": args.seed, "use_scl": use_scl, "use_localize": use_localize,
        "sym_mode": args.sym_mode,
        "scl_lambda": args.scl_lambda, "scl_hard_neg_weight": args.scl_hard_neg_weight,
        "fix_k": args.fix_k, "K": best_K, "threshold": float(best_threshold),
        "val_recall": float(best_recall_val),
        "test": {
            "n": len(test_data), "precision": float(p_opt), "recall": float(r_opt),
            "f1": float(f1_opt), "f2": float(f2_opt), "pr_auc": float(pr_auc),
            "roc_auc": float(roc_auc),
            "probs": [float(p) for p in test_probs],
            "labels": [int(l) for l in test_labels], "ids": _ids(test_items),
        },
        "holdouts": {
            "OZ-Holdout": _holdout_record(oz_holdout_probs, oz_holdout_data, best_threshold),
            "MakerDAO": _holdout_record(makerdao_probs, makerdao_data, best_threshold),
            "Bancor": _holdout_record(bancor_probs, bancor_data, best_threshold),
            "Liquity": _holdout_record(liquity_probs, liquity_data, best_threshold),
        },
    }
    with open(ablation_dir / f"{arm}_seed{args.seed}.json", "w") as fh:
        json.dump(artifact, fh)
    print(f"Saved ablation artifact -> ablation/{arm}_seed{args.seed}.json")

    # Write report to iteration3_results.md
    report_path = results_dir / f"iteration3_results{tag}.md"
    
    vuln_table_rows = []
    for vt, stats in vuln_recalls.items():
        rec_str = f"{stats['recall']*100:.2f}%" if isinstance(stats['recall'], float) else stats['recall']
        vuln_table_rows.append(f"| {vt} | {stats['count']} | {rec_str} |")
        
    sweep_table_rows = []
    for sr in sweep_results:
        prefix = "**" if sr['K'] == best_K else ""
        suffix = "**" if sr['K'] == best_K else ""
        sweep_table_rows.append(f"| {prefix}{sr['K']}{suffix} | {prefix}{sr['val_loss']:.4f}{suffix} | {prefix}{sr['threshold']:.4f}{suffix} | {prefix}{sr['val_recall']*100:.2f}%{suffix} | {prefix}{sr['combined_val_fpr']*100:.2f}%{suffix} |")
        
    # Final negative training set composition details
    base_negatives = sum(1 for x in train_data if x.get('label', 0.0) == 0)
    base_positives = sum(1 for x in train_data if x.get('label', 0.0) == 1)
    
    final_oz_negatives = 100
    final_aave_negatives = best_K
    total_training_negatives = base_negatives + final_oz_negatives + final_aave_negatives
    
    base_neg_pct = (base_negatives / total_training_negatives) * 100
    oz_neg_pct = (final_oz_negatives / total_training_negatives) * 100
    aave_neg_pct = (final_aave_negatives / total_training_negatives) * 100
    
    composition_text = (
        f"*   **Total Positives in Training**: {final_pos_in_train} (Base Codebase Positives: {base_positives})\n"
        f"*   **Total Negatives in Training**: {total_training_negatives} (100% of negative class)\n"
        f"    *   *Codebase (Tier-A) Hard Negatives*: {base_negatives} ({base_neg_pct:.2f}%)\n"
        f"    *   *Clean Library (OpenZeppelin) Negatives*: {final_oz_negatives} ({oz_neg_pct:.2f}%)\n"
        f"    *   *Clean Application (Aave V3) Negatives*: {final_aave_negatives} ({aave_neg_pct:.2f}%)"
    )
    
    report_content = f"""# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint{tag}.pt`
> **Arm**: `{arm}` (SCL={'ON' if use_scl else 'OFF'}, Localization={'ON' if use_localize else 'OFF'}) · **Seed**: `{args.seed}`
> **Clean Negative Training Count K_app**: `{best_K}` ({'fixed via --fix-k' if args.fix_k is not None else 'tuned on combined Validation set'})
> **Chosen Decision Threshold**: `{best_threshold:.4f}`  
> **Validation Recall**: `{best_recall_val*100:.2f}%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{{oz}}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
{"\n".join(sweep_table_rows)}

---

## 2. Final Negative Training Set Composition
{composition_text}

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | {len(oz_holdout_data)} | {fp_oz_holdout} | {fpr_oz_holdout*100:.2f}% | [{oz_ci_lower*100:.2f}%, {oz_ci_upper*100:.2f}%] |
| **MakerDAO DSS** | External (DeFi Application) | {len(makerdao_data)} | {fp_makerdao} | {fpr_makerdao*100:.2f}% | [{maker_ci_lower*100:.2f}%, {maker_ci_upper*100:.2f}%] |
| **Bancor V3** | External (DeFi Application) | {len(bancor_data)} | {fp_bancor} | {fpr_bancor*100:.2f}% | [{bancor_ci_lower*100:.2f}%, {bancor_ci_upper*100:.2f}%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | {len(liquity_data)} | {fp_liquity} | {fpr_liquity*100:.2f}% | [{liquity_ci_lower*100:.2f}%, {liquity_ci_upper*100:.2f}%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split ({len(test_data)} items: {sum(test_labels):.0f} positives, {len(test_data)-sum(test_labels):.0f} negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | {p_opt*100:.2f}% |
| **Recall** | {r_opt*100:.2f}% |
| **F1-Score** | {f1_opt*100:.2f}% |
| **F2-Score** | {f2_opt*100:.2f}% |
| **PR-AUC** | {pr_auc*100:.2f}% |
| **ROC-AUC** | {roc_auc*100:.2f}% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | {len(cross_indices)} ({sum(test_labels[cross_indices]):.0f}/{len(cross_indices)-sum(test_labels[cross_indices]):.0f}) | {cross_p*100:.2f}% | {cross_r*100:.2f}% | {cross_f1*100:.2f}% | {cross_f2*100:.2f}% | {cross_pr_auc*100:.2f}% | {cross_roc_auc*100:.2f}% |
| **Intra-Contract** | {len(intra_indices)} ({sum(test_labels[intra_indices]):.0f}/{len(intra_indices)-sum(test_labels[intra_indices]):.0f}) | {intra_p*100:.2f}% | {intra_r*100:.2f}% | {intra_f1*100:.2f}% | {intra_f2*100:.2f}% | {intra_pr_auc*100:.2f}% | {intra_roc_auc*100:.2f}% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
{"\n".join(vuln_table_rows)}

---

## 7. Run Configuration & Measured Summary
> Single run: **seed={args.seed}**, arm=**{arm}** (SCL={'ON' if use_scl else 'OFF'}, Localization={'ON' if use_localize else 'OFF'}), K_app={best_K} ({'fixed' if args.fix_k is not None else 'sweep-selected'}), threshold={best_threshold:.4f}.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 {f1_opt*100:.2f}%, Precision {p_opt*100:.2f}%, Recall {r_opt*100:.2f}%, PR-AUC {pr_auc*100:.2f}%, ROC-AUC {roc_auc*100:.2f}%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): {fpr_oz_holdout*100:.2f}% [{oz_ci_lower*100:.2f}%, {oz_ci_upper*100:.2f}%]
  - MakerDAO DSS: {fpr_makerdao*100:.2f}% [{maker_ci_lower*100:.2f}%, {maker_ci_upper*100:.2f}%]
  - Bancor V3: {fpr_bancor*100:.2f}% [{bancor_ci_lower*100:.2f}%, {bancor_ci_upper*100:.2f}%]
  - Liquity V1: {fpr_liquity*100:.2f}% [{liquity_ci_lower*100:.2f}%, {liquity_ci_upper*100:.2f}%]
- **Cross- vs intra-contract (test)**: cross F1 {cross_f1*100:.2f}% (recall {cross_r*100:.2f}%), intra F1 {intra_f1*100:.2f}% (recall {intra_r*100:.2f}%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
"""
    
    with open(report_path, "w") as fh:
        fh.write(report_content)
    print(f"Saved iteration3_results.md to {results_dir}/")
    print("Training and evaluation completed successfully!")

if __name__ == '__main__':
    main(parse_args())
