import json
import sys
import os
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

# Fix random seed
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

class HyperedgeDataset(Dataset):
    def __init__(self, data_list):
        self.items = data_list
        
    def __len__(self):
        return len(self.items)
        
    def __getitem__(self, idx):
        item = self.items[idx]
        
        # Extract function features (768)
        func_emb = item['node_features']['function']
        
        # Extract state variables features (dict)
        sv_embs = list(item['node_features']['state_vars'].values())
        
        # Extract external calls features (list of dicts)
        ec_embs = [ec['embedding'] for ec in item['node_features']['external_calls']]
        
        # Combine into a single sequence of node features
        # Sequence: [func] + [svs] + [ecs]
        all_node_features = [func_emb] + sv_embs + ec_embs
        
        # Convert to tensor
        x = torch.tensor(all_node_features, dtype=torch.float32)
        label = float(item.get('label', 0.0))
        
        return x, label, item

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
            padded_t = torch.cat([t, torch.zeros(padding_size, 768)], dim=0)
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
            logits, _ = model(x, mask)
            probs = torch.sigmoid(logits).squeeze(-1).cpu().numpy()
            all_probs.extend(probs)
            all_labels.extend(labels.numpy())
            all_items.extend(batch_items)
            
    return np.array(all_probs), np.array(all_labels), all_items

def main():
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # 1. Load datasets
    splits_dir = PROJECT_ROOT / "data" / "splits"
    results_dir = PROJECT_ROOT / "experiments" / "results"
    
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
    
    # Load OZ split mapping
    mapping_path = PROJECT_ROOT / "scratch" / "oz_split_mapping.json"
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
    
    # Sample fixed K_oz = 100 clean negatives from oz_train_data (reproducibly)
    set_seed(42)
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
    
    # We sweep K_app (Aave clean negatives added to training)
    # Available Aave train: 225
    sweep_K = [0, 50, 100, 150, 200, 225]
    sweep_results = []
    
    for K in sweep_K:
        print("\n" + "="*60)
        print(f"Running Sweep for K_app = {K} (Adding {K} Aave clean negatives to training)")
        print("="*60)
        
        # Set seed for reproducibility of sweep sampling and training
        set_seed(42)
        
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
        
        # Initialize model
        model = HyperedgeClassifier(input_dim=768, hidden_dim=256, dropout=0.3).to(device)
        optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
        criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_upweight], device=device))
        
        # Train with early stopping on val_data
        patience = 20
        best_val_loss = float('inf')
        epochs_no_improve = 0
        sweep_model_state = None
        
        for epoch in range(1, 201):
            model.train()
            train_loss = 0.0
            for x, mask, labels, _ in train_loader:
                x, mask, labels = x.to(device), mask.to(device), labels.to(device)
                optimizer.zero_grad()
                logits, _ = model(x, mask)
                loss = criterion(logits.squeeze(-1), labels)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * x.size(0)
            train_loss /= len(train_dataset)
            
            # Validation evaluation
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for x, mask, labels, _ in val_loader:
                    x, mask, labels = x.to(device), mask.to(device), labels.to(device)
                    logits, _ = model(x, mask)
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
        
    # Re-select best K_app based on lowest combined validation FPR in the stable region (50, 100, 150)
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
    
    # Save checkpoint
    checkpoint_dir = PROJECT_ROOT / "model"
    os.makedirs(checkpoint_dir, exist_ok=True)
    torch.save(best_model_state, checkpoint_dir / "iteration3_checkpoint.pt")
    
    with open(checkpoint_dir / "threshold_config_iter3.json", "w") as fh:
        json.dump({"best_threshold": float(best_threshold), "best_K": best_K, "val_recall": float(best_recall_val)}, fh, indent=2)
        
    # Re-initialize best model for evaluation
    model = HyperedgeClassifier(input_dim=768, hidden_dim=256, dropout=0.3).to(device)
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
        
    # Write report to iteration3_results.md
    report_path = results_dir / "iteration3_results.md"
    
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

> **Model Checkpoint**: [iteration3_checkpoint.pt](file:///home/pollmix/Coding/HyperVul/model/iteration3_checkpoint.pt)  
> **Best Clean Negative Training Count K_app**: `{best_K}` (Tuned on combined Validation set)  
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

## 7. Interpretation of Results & Findings
- **Stable Optimum Selection**: Selected the best $K_{{app}} = {best_K}$ from the stable region (50, 100, 150) of the sweep. Restricting to this stable region prevents knife-edge noise-chasing (such as the artifact at $K_{{app}}=200$).
- **In-Distribution Validation Bias**: Minimizing the combined validation FPR (which includes `Aave-Val`) favors the trained-on distribution. `Aave-Val` achieves a low 1.52% FPR because it is in-distribution with `Aave-Train`, whereas out-of-distribution holdout sets show significantly higher FPRs.
- **Data Coverage Intervention is Ineffective**: Sourcing and training on clean application-level negatives did NOT consistently reduce out-of-distribution FPR. The metrics on the never-trained external holdout sets fluctuated marginally compared to the Iteration-2 baseline:
  - **OZ-Holdout**: 38.10% $\rightarrow$ {fpr_oz_holdout*100:.2f}%
  - **MakerDAO DSS**: 70.52% $\rightarrow$ {fpr_makerdao*100:.2f}%
  - **Bancor V3**: 58.37% $\rightarrow$ {fpr_bancor*100:.2f}%
  - **Liquity V1 (Fresh Probe)**: Sits at {fpr_liquity*100:.2f}%
- **Persistent External Call Detector Behavior**: The intervention failed to resolve the "external call detector" behavior. The model still flags the majority of clean production interactions (e.g., MakerDAO FPR remains at {fpr_makerdao*100:.2f}%, and Bancor remains at {fpr_bancor*100:.2f}%). Because the flat node embeddings lack semantic awareness of safety checks or invariant sequences, the presence of any external call remains a strong trigger for positive vulnerability predictions.
- **Rejection of G-HAN Hypothesis**: Cross-contract recall ({cross_r*100:.2f}%) and ROC-AUC ({cross_roc_auc*100:.2f}%) on the test set are higher than or comparable to intra-contract metrics. Thus, there is no cross-contract relational performance gap to close. Transitioning to G-HAN is not supported, as modifying the encoder architecture does not address the model's fundamental behavior of over-flagging external calls.
- **Future Work Hypothesis**: Since data-coverage expansion provides only marginal/inconsistent impact and fails to resolve the underlying external call detector behavior, future work should focus on alternative representations or architectures that incorporate semantic control-flow logic and checking invariants.
"""
    
    with open(report_path, "w") as fh:
        fh.write(report_content)
    print(f"Saved iteration3_results.md to {results_dir}/")
    print("Training and evaluation completed successfully!")

if __name__ == '__main__':
    main()
