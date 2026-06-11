#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def validate():
    project_root = Path("/home/pollmix/Coding/HyperVul")
    splits_dir = project_root / "data" / "splits"
    
    train_aug_path = splits_dir / "train_augmented.json"
    val_path = splits_dir / "val.json"
    test_path = splits_dir / "test.json"
    
    if not train_aug_path.exists():
        print(f"Error: {train_aug_path} does not exist.")
        sys.exit(1)
        
    print(f"Loading {train_aug_path}...")
    with open(train_aug_path) as f:
        train_aug = json.load(f)
        
    print(f"Loading val and test splits for leakage checking...")
    with open(val_path) as f:
        val = json.load(f)
    with open(test_path) as f:
        test = json.load(f)
        
    val_hashes = set(item['normalized_source_hash'] for item in val)
    test_hashes = set(item['normalized_source_hash'] for item in test)
    eval_hashes = val_hashes | test_hashes
    
    print(f"Total items in train_augmented: {len(train_aug)}")
    positives = [item for item in train_aug if item['label'] == 1]
    negatives = [item for item in train_aug if item['label'] == 0]
    print(f"  Positives: {len(positives)}")
    print(f"  Negatives: {len(negatives)}")
    
    # Check 1: Feature dimensions must be exactly 768
    print("Verifying feature dimensions (uniform 768-d)...")
    dimension_errors = 0
    missing_features = 0
    
    for idx, item in enumerate(train_aug):
        if 'node_features' not in item:
            print(f"Error: Item at index {idx} ({item.get('contract')}.{item.get('function')}) has no node_features key.")
            missing_features += 1
            continue
            
        nf = item['node_features']
        
        # Check function embedding
        func_emb = nf.get('function')
        if not func_emb or not isinstance(func_emb, list) or len(func_emb) != 768:
            print(f"Error: Item {idx} function embedding has invalid shape/type: {type(func_emb)} (length: {len(func_emb) if func_emb else 0})")
            dimension_errors += 1
            
        # Check state variables embeddings
        sv_embs = nf.get('state_vars', {})
        for sv_name, sv_emb in sv_embs.items():
            if not sv_emb or not isinstance(sv_emb, list) or len(sv_emb) != 768:
                print(f"Error: Item {idx} state variable '{sv_name}' embedding has invalid shape/type: {type(sv_emb)} (length: {len(sv_emb) if sv_emb else 0})")
                dimension_errors += 1
                
        # Check external call embeddings
        ec_embs = nf.get('external_calls', [])
        for ec_idx, ec_emb_dict in enumerate(ec_embs):
            ec_emb = ec_emb_dict.get('embedding')
            if not ec_emb or not isinstance(ec_emb, list) or len(ec_emb) != 768:
                print(f"Error: Item {idx} external call {ec_idx} embedding has invalid shape/type: {type(ec_emb)} (length: {len(ec_emb) if ec_emb else 0})")
                dimension_errors += 1
                
    # Check 2: Leakage check
    print("Verifying leakage against val and test splits...")
    leakage_violations = 0
    for idx, item in enumerate(train_aug):
        if item.get('is_variant'):
            h = item['normalized_source_hash']
            if h in eval_hashes:
                print(f"Error: Variant at index {idx} ({item.get('contract')}.{item.get('function')}) matches val/test source hash: {h}")
                leakage_violations += 1
                
    # Check 3: Provenance tracking
    print("Verifying provenance tags...")
    provenance_errors = 0
    for idx, item in enumerate(train_aug):
        if 'is_variant' not in item:
            print(f"Error: Item {idx} has no 'is_variant' key.")
            provenance_errors += 1
        if item.get('is_variant') == True and 'source_id' not in item:
            print(f"Error: Variant at index {idx} has no 'source_id' key.")
            provenance_errors += 1
            
    print("=" * 40)
    print("VALIDATION SUMMARY:")
    print(f"Missing node_features: {missing_features}")
    print(f"Dimension errors (not 768-d): {dimension_errors}")
    print(f"Leakage violations: {leakage_violations}")
    print(f"Provenance errors: {provenance_errors}")
    print("=" * 40)
    
    if missing_features > 0 or dimension_errors > 0 or leakage_violations > 0 or provenance_errors > 0:
        print("Validation FAILED!")
        sys.exit(1)
    else:
        print("Validation PASSED successfully!")
        sys.exit(0)

if __name__ == '__main__':
    validate()
