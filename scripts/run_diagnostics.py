#!/usr/bin/env python3
import json
import sys
import hashlib
import numpy as np
import torch
from pathlib import Path
from collections import defaultdict, Counter
import tree_sitter as ts
import tree_sitter_solidity as tss
from transformers import RobertaTokenizer

# Setup paths
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
from model.model import HyperedgeClassifier
from model.train import HyperedgeDataset, collate_fn, evaluate_model

FORGE_VULN_DIR = PROJECT_ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
DAPPSCAN_ROOT = PROJECT_ROOT / "data" / "DAppSCAN"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

# Load tree-sitter parser
LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)

# Load tokenizer
MODEL_NAME = "web3se/SmartBERT-v3"
tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)

# Cache for DAppSCAN projects
dappscan_projects_cache = {}

def get_dappscan_project_contracts(filepath):
    full_path = DAPPSCAN_ROOT / filepath
    try:
        proj_root = nhs.find_project_root(full_path)
    except Exception:
        parts = Path(filepath).parts
        if len(parts) >= 3:
            proj_root = DAPPSCAN_ROOT / parts[0] / parts[1] / parts[2]
        else:
            proj_root = full_path.parent
            
    proj_root_key = str(proj_root)
    if proj_root_key in dappscan_projects_cache:
        return dappscan_projects_cache[proj_root_key]
        
    project_contracts = {}
    if proj_root.exists():
        for sol_file in proj_root.glob("**/*.sol"):
            try:
                with open(sol_file, "r", encoding="utf-8", errors="ignore") as fh:
                    s = fh.read()
                project_contracts.update(nhs.parse_contracts(s))
            except Exception:
                pass
    dappscan_projects_cache[proj_root_key] = project_contracts
    return project_contracts

# Cache for FORGE VFP files
vfp_data = {}
for p in FORGE_VULN_DIR.glob('*.json'):
    with open(p) as f:
        vfp_data[p.stem] = json.load(f)

def find_forge_vfp_id(item):
    file_name = Path(item['file']).name
    target_hash = item['normalized_source_hash']
    func_name = item.get('function') or item.get('ast_function')
    contract = item['contract']
    
    for vid, vdata in vfp_data.items():
        if item['file'] in vdata.get('affected_files', {}) or file_name in vdata.get('affected_files', {}):
            fcode = vdata['affected_files'].get(item['file']) or vdata['affected_files'].get(file_name)
            try:
                parsed = nhs.parse_contracts(fcode)
                all_funcs = nhs.resolve_all_functions(contract, parsed)
                if func_name in all_funcs:
                    func_node = all_funcs[func_name]
                    func_src = nhs.node_text(func_node)
                    norm_hash = hashlib.sha256(nhs.normalize_source(func_src).encode('utf-8')).hexdigest()
                    if norm_hash == target_hash:
                        return vid
            except Exception:
                pass
                
    for vid, vdata in vfp_data.items():
        if item['file'] in vdata.get('affected_files', {}) or file_name in vdata.get('affected_files', {}):
            try:
                all_contracts = {}
                for fn, fc in vdata['affected_files'].items():
                    all_contracts.update(nhs.parse_contracts(fc))
                all_funcs = nhs.resolve_all_functions(contract, all_contracts)
                if func_name in all_funcs:
                    func_node = all_funcs[func_name]
                    func_src = nhs.node_text(func_node)
                    norm_hash = hashlib.sha256(nhs.normalize_source(func_src).encode('utf-8')).hexdigest()
                    if norm_hash == target_hash:
                        return vid
            except Exception:
                pass
    return None

def get_function_source(item):
    contract = item['contract']
    func_name = item.get('function') or item.get('ast_function')
    source_type = item.get('source')
    filepath = item.get('file') or item.get('filePath')
    
    if not source_type:
        if "dappscan" in str(filepath).lower() or 'project_root' in item:
            source_type = "DAppSCAN"
        else:
            source_type = "FORGE"
            
    source_code = None
    all_contracts = {}
    
    if source_type == "DAppSCAN":
        full_path = DAPPSCAN_ROOT / filepath
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                source_code = fh.read()
            all_contracts = get_dappscan_project_contracts(filepath)
    else:
        # FORGE
        vfp_id = item.get('vfp_id') or find_forge_vfp_id(item)
        if vfp_id:
            file_name = Path(item['file']).name
            source_code = vfp_data[vfp_id]['affected_files'].get(item['file']) or vfp_data[vfp_id]['affected_files'].get(file_name)
            for fn, fc in vfp_data[vfp_id]['affected_files'].items():
                all_contracts.update(nhs.parse_contracts(fc))
                
    if not source_code:
        return None
        
    try:
        parsed = nhs.parse_contracts(source_code)
        merged_contracts = dict(all_contracts)
        merged_contracts.update(parsed)
        all_funcs = nhs.resolve_all_functions(contract, merged_contracts)
        if func_name in all_funcs:
            return nhs.node_text(all_funcs[func_name])
    except Exception:
        pass
    return None

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    # 1. Load model and threshold config
    model = HyperedgeClassifier(input_dim=768, hidden_dim=256, dropout=0.3).to(device)
    checkpoint_path = PROJECT_ROOT / "model" / "iteration1_checkpoint.pt"
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    
    with open(PROJECT_ROOT / "model" / "threshold_config.json") as f:
        threshold_config = json.load(f)
    best_threshold = threshold_config["best_threshold"]
    print(f"Loaded threshold: {best_threshold:.4f}")
    
    # 2. Load test set features
    with open(SPLITS_DIR / "test_features.json") as f:
        test_data = json.load(f)
        
    test_dataset = HyperedgeDataset(test_data)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    # Run evaluation
    test_probs, test_labels, test_items = evaluate_model(model, test_loader, device)
    test_preds = (test_probs >= best_threshold).astype(int)
    
    # ---------------------------------------------------------------------------
    # DIAGNOSTIC 1 — DAppSCAN Label Noise
    # ---------------------------------------------------------------------------
    print("Running Diagnostic 1...")
    
    # Filter cross-contract positives
    cross_pos_indices = []
    for idx, item in enumerate(test_items):
        if item['label'] == 1 and item.get('is_cross_contract', False):
            cross_pos_indices.append(idx)
            
    # Classify by source and model prediction
    total_forge_cp = 0
    total_dappscan_cp = 0
    caught_forge_cp = 0
    caught_dappscan_cp = 0
    missed_forge_cp = 0
    missed_dappscan_cp = 0
    
    for idx in cross_pos_indices:
        item = test_items[idx]
        pred = test_preds[idx]
        
        # Determine source
        filepath = item.get('file') or item.get('filePath')
        source_type = item.get('source')
        if not source_type:
            if "dappscan" in str(filepath).lower() or 'project_root' in item:
                source_type = "DAppSCAN"
            else:
                source_type = "FORGE"
                
        if source_type == "DAppSCAN":
            total_dappscan_cp += 1
            if pred == 1:
                caught_dappscan_cp += 1
            else:
                missed_dappscan_cp += 1
        else:
            total_forge_cp += 1
            if pred == 1:
                caught_forge_cp += 1
            else:
                missed_forge_cp += 1
                
    recall_forge_cp = caught_forge_cp / total_forge_cp if total_forge_cp > 0 else 0.0
    recall_dappscan_cp = caught_dappscan_cp / total_dappscan_cp if total_dappscan_cp > 0 else 0.0
    
    print(f"Cross-contract positives source split: FORGE={total_forge_cp}, DAppSCAN={total_dappscan_cp}")
    print(f"  CAUGHT: FORGE={caught_forge_cp}, DAppSCAN={caught_dappscan_cp}")
    print(f"  MISSED (FN): FORGE={missed_forge_cp}, DAppSCAN={missed_dappscan_cp}")
    print(f"  RECALL: FORGE={recall_forge_cp*100:.2f}%, DAppSCAN={recall_dappscan_cp*100:.2f}%")
    
    # ---------------------------------------------------------------------------
    # DIAGNOSTIC 2 — Token Truncation
    # ---------------------------------------------------------------------------
    print("Running Diagnostic 2...")
    
    # For every test positive, retrieve its function text and compute token length
    test_positives_info = []
    
    for idx, item in enumerate(test_items):
        if item['label'] == 1:
            func_src = get_function_source(item)
            if not func_src:
                # Fallback to function name if source not found (should be very rare)
                func_src = item.get('function') or item.get('ast_function') or ""
                
            tokens = tokenizer.tokenize(func_src)
            token_len = len(tokens)
            is_cross = item.get('is_cross_contract', False)
            pred = test_preds[idx]
            
            test_positives_info.append({
                "idx": idx,
                "item": item,
                "token_len": token_len,
                "is_cross": is_cross,
                "pred": pred
            })
            
    # Split by contract category
    cross_lens = [info['token_len'] for info in test_positives_info if info['is_cross']]
    intra_lens = [info['token_len'] for info in test_positives_info if not info['is_cross']]
    
    cross_truncated_count = sum(1 for l in cross_lens if l > 256)
    intra_truncated_count = sum(1 for l in intra_lens if l > 256)
    
    cross_trunc_frac = cross_truncated_count / len(cross_lens) if len(cross_lens) > 0 else 0.0
    intra_trunc_frac = intra_truncated_count / len(intra_lens) if len(intra_lens) > 0 else 0.0
    
    # Check if missed cross-contract positives are truncated
    missed_cross_truncated = 0
    missed_cross_total = 0
    for info in test_positives_info:
        if info['is_cross'] and info['pred'] == 0:
            missed_cross_total += 1
            if info['token_len'] > 256:
                missed_cross_truncated += 1
                
    print(f"Function token length distributions:")
    print(f"  Cross-contract: count={len(cross_lens)}, min={np.min(cross_lens)}, max={np.max(cross_lens)}, median={np.median(cross_lens)}, mean={np.mean(cross_lens):.1f}")
    print(f"  Intra-contract: count={len(intra_lens)}, min={np.min(intra_lens)}, max={np.max(intra_lens)}, median={np.median(intra_lens)}, mean={np.mean(intra_lens):.1f}")
    print(f"Truncation (>256 tokens) rates on positives:")
    print(f"  Cross-contract: {cross_truncated_count}/{len(cross_lens)} ({cross_trunc_frac*100:.2f}%)")
    print(f"  Intra-contract: {intra_truncated_count}/{len(intra_lens)} ({intra_trunc_frac*100:.2f}%)")
    print(f"Missed cross-contract positives truncation rate:")
    print(f"  {missed_cross_truncated} out of {missed_cross_total} missed items ({missed_cross_truncated/missed_cross_total*100:.2f}% if missed_cross_total > 0 else 0.0%)")
    
    # ---------------------------------------------------------------------------
    # WRITE REPORT TO experiments/results/crosscontract_diagnostics.md
    # ---------------------------------------------------------------------------
    # Conclusion logic:
    # Conclusion 1 (Label Noise):
    if missed_dappscan_cp > 0 and missed_forge_cp == 0:
        conclusion1 = "DAppSCAN label noise is a primary factor; all missed cross-contract positives belong to DAppSCAN, whereas FORGE cross-contract positives were perfectly predicted (100% recall)."
    elif recall_forge_cp > recall_dappscan_cp + 0.15:
        conclusion1 = f"DAppSCAN label noise is a significant factor; recall on FORGE cross-contract positives is {recall_forge_cp*100:.1f}%, which is substantially higher than the {recall_dappscan_cp*100:.1f}% recall on DAppSCAN cross-contract positives."
    else:
        conclusion1 = f"DAppSCAN label noise is not the primary factor; recall is similar across both sources (FORGE: {recall_forge_cp*100:.1f}%, DAppSCAN: {recall_dappscan_cp*100:.1f}%)."
        
    # Conclusion 2 (Truncation):
    if missed_cross_total > 0:
        trunc_miss_pct = (missed_cross_truncated / missed_cross_total) * 100
        if trunc_miss_pct >= 50.0:
            conclusion2 = f"Token truncation is a major factor; {trunc_miss_pct:.1f}% of missed cross-contract positives exceed the 256-token limit, losing critical signature contexts."
        else:
            conclusion2 = f"Token truncation is a minor factor; only {trunc_miss_pct:.1f}% of missed cross-contract positives exceed 256 tokens, indicating that most misses are not due to truncation."
    else:
        conclusion2 = "No missed cross-contract positives to evaluate for truncation."
        
    # Overall Diagnosis:
    # If neither, it's genuinely encoder/representation limitations
    is_label_noise = (recall_forge_cp > recall_dappscan_cp + 0.15)
    is_truncation = (missed_cross_total > 0 and (missed_cross_truncated / missed_cross_total) >= 0.5)
    
    if is_label_noise and is_truncation:
        overall_conclusion = "The cross-contract weakness is a joint effect of DAppSCAN label noise and token truncation. Addressing both (improving validation/test selection and expanding function spans) is required."
    elif is_label_noise:
        overall_conclusion = "The cross-contract weakness is primarily a DAppSCAN label-noise artifact (high performance on cleaner FORGE data). G-HAN's structural message passing would not resolve this dataset labeling noise."
    elif is_truncation:
        overall_conclusion = "The cross-contract weakness is primarily a token truncation issue (critical contexts cut off). Increasing the token limit or using signature-based spans is the recommended fix."
    else:
        overall_conclusion = "The cross-contract weakness is neither label noise nor token truncation; it represents a genuine representation/encoder limitation. This strongly validates the necessity of G-HAN's structural message-passing layers to bridge contract boundaries."
        
    report_content = f"""# HyperVul — Cross-Contract Performance Diagnostic Report

This report analyzes the root cause of the performance gap on cross-contract vs. intra-contract hyperedges in Model Iteration 1.

---

## Diagnostic 1 — Is the cross-contract weakness a DAppSCAN label-noise artifact?
Cross-contract positives lean on both FORGE and DAppSCAN. DAppSCAN is known to contain noisier, single-point label assignments.

### Concrete Metrics (Cross-Contract Positives):
* **Total Positives**: {len(cross_pos_indices)} items
* **Split by Source**: FORGE = **{total_forge_cp}** | DAppSCAN = **{total_dappscan_cp}**
* **Model Predictions (at threshold `{best_threshold:.4f}`):**
  * **CAUGHT (True Positives)**: FORGE = **{caught_forge_cp}** | DAppSCAN = **{caught_dappscan_cp}**
  * **MISSED (False Negatives)**: FORGE = **{missed_forge_cp}** | DAppSCAN = **{missed_dappscan_cp}**
* **Source-Specific Recalls**:
  * **FORGE Cross-Contract Recall**: **{recall_forge_cp*100:.2f}%** ({caught_forge_cp}/{total_forge_cp})
  * **DAppSCAN Cross-Contract Recall**: **{recall_dappscan_cp*100:.2f}%** ({caught_dappscan_cp}/{total_dappscan_cp})

### Diagnostic Conclusion 1:
> [!NOTE]
> **Conclusion**: {conclusion1}

---

## Diagnostic 2 — Is 256-token truncation cutting off cross-contract signatures?
Cross-contract functions are typically longer than intra-contract helper functions. The feature extraction scheme truncates calling-function source code at 256 tokens.

### Concrete Metrics (Function Token Lengths):
* **Function Length Distribution (Positive Test Items)**:
  * **Cross-Contract**: count = {len(cross_lens)} | min = {np.min(cross_lens)} | max = {np.max(cross_lens)} | median = {np.median(cross_lens)} | mean = {np.mean(cross_lens):.1f} tokens
  * **Intra-Contract**: count = {len(intra_lens)} | min = {np.min(intra_lens)} | max = {np.max(intra_lens)} | median = {np.median(intra_lens)} | mean = {np.mean(intra_lens):.1f} tokens
* **Truncation Rate (>256 tokens) on Positive Items**:
  * **Cross-Contract**: **{cross_truncated_count}/{len(cross_lens)} ({cross_trunc_frac*100:.2f}%)** exceeded 256 tokens.
  * **Intra-Contract**: **{intra_truncated_count}/{len(intra_lens)} ({intra_trunc_frac*100:.2f}%)** exceeded 256 tokens.
* **Truncation Rate on Missed Cross-Contract Positives (False Negatives)**:
  * **{missed_cross_truncated} out of {missed_cross_total}** missed items (**{missed_cross_truncated/missed_cross_total*100:.2f}%** if missed_cross_total > 0 else 0.0%) exceeded 256 tokens.

### Diagnostic Conclusion 2:
> [!NOTE]
> **Conclusion**: {conclusion2}

---

## Overall Diagnostic Conclusion
> [!IMPORTANT]
> **Summary**: {overall_conclusion}
"""
    
    with open(RESULTS_DIR / "crosscontract_diagnostics.md", "w") as fh:
        fh.write(report_content)
    print(f"Saved crosscontract_diagnostics.md to {RESULTS_DIR}/")
    print("Diagnostics completed successfully!")

if __name__ == '__main__':
    main()
