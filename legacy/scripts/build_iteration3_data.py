#!/usr/bin/env python3
import json
import sys
import torch
import re
import hashlib
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

try:
    from transformers import RobertaTokenizer, RobertaModel
except ModuleNotFoundError:
    print("Please ensure Hugging Face transformers is installed.")

CLONES_DIR = PROJECT_ROOT / "scratch" / "clones"
AAVE_MAPPING_PATH = PROJECT_ROOT / "scratch" / "aave_split_mapping.json"
AAVE_OUTPUT_FILE = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_aave_split.json"
LIQUITY_OUTPUT_FILE = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_liquity.json"

# Load tree-sitter parser
import tree_sitter as ts
import tree_sitter_solidity as tss
LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)

# Load SmartBERT-v3 tokenizer and model
print("Loading SmartBERT-v3 from Hugging Face...")
MODEL_NAME = "web3se/SmartBERT-v3"
tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
encoder = RobertaModel.from_pretrained(MODEL_NAME)
encoder.eval()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
encoder.to(device)
print(f"Loaded SmartBERT-v3. Device: {device}")

def batch_encode_texts(texts_list, max_length=256, batch_size=32):
    unique_texts = list(set(texts_list))
    embeddings_map = {}
    print(f"Batch encoding {len(unique_texts)} unique spans with max_length={max_length}...")
    
    for i in range(0, len(unique_texts), batch_size):
        batch = unique_texts[i:i+batch_size]
        inputs = tokenizer(
            batch,
            return_tensors="pt",
            max_length=max_length,
            truncation=True,
            padding="max_length",
        ).to(device)
        with torch.no_grad():
            outputs = encoder(**inputs)
        cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().tolist()
        for text, emb in zip(batch, cls_embeddings):
            embeddings_map[text] = emb
            
    return embeddings_map

def extract_hyperedges_from_dir(contracts_dir, source_name):
    print(f"Scanning {contracts_dir} for {source_name} Solidity files...")
    sol_files = list(Path(contracts_dir).glob("**/*.sol"))
    print(f"Found {len(sol_files)} Solidity files.")
    
    # Parse all contracts first to build a global map
    all_contracts = {}
    file_contracts = {}
    for sf in sol_files:
        try:
            with open(sf, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            parsed = nhs.parse_contracts(content)
            if parsed:
                all_contracts.update(parsed)
                file_contracts[str(sf)] = parsed
        except Exception as e:
            pass
            
    print(f"Total parsed contracts for {source_name}: {len(all_contracts)}")
    
    raw_hyperedges = []
    for sf, contracts in file_contracts.items():
        rel_f = str(Path(sf).relative_to(contracts_dir))
        for contract_name, contract_info in contracts.items():
            try:
                state_vars = nhs.resolve_all_state_vars(contract_name, all_contracts)
                state_var_types = nhs.resolve_all_state_var_types(contract_name, all_contracts)
                all_funcs = nhs.resolve_all_functions(contract_name, all_contracts)
                
                for func_name, func_node in all_funcs.items():
                    local_vars = nhs.extract_local_vars(func_node)
                    accessed_vars = nhs.find_state_var_accesses(func_node, state_vars, local_vars)
                    ext_calls = nhs.find_external_calls_ast(func_node, state_var_types, all_contracts, allow_fallback=False)
                    
                    if len(accessed_vars) > 0 and len(ext_calls) > 0:
                        func_src = nhs.node_text(func_node)
                        # Identify if cross-contract: if any external call is not on a local or state var contract type
                        is_cross = any("call on contract-typed" in ec.get("reason", "") or 
                                       "call on interface/contract" in ec.get("reason", "")
                                       for ec in ext_calls)
                        
                        raw_hyperedges.append({
                            "file": rel_f,
                            "contract": contract_name,
                            "function": func_name,
                            "label": 0.0,
                            "source": source_name,
                            "is_cross_contract": is_cross,
                            "state_vars_accessed": accessed_vars,
                            "external_calls": ext_calls,
                            "func_src": func_src,
                            "state_var_types": state_var_types
                        })
            except Exception as e:
                pass
                
    return raw_hyperedges

def build_dataset_with_embeddings(raw_items, source_name):
    if not raw_items:
        return []
        
    # Collect texts
    function_texts = []
    state_var_texts = []
    call_texts = []
    for item in raw_items:
        function_texts.append(item["func_src"])
        for sv in item["state_vars_accessed"]:
            sv_type = item["state_var_types"].get(sv, "")
            state_var_texts.append(f"{sv_type} {sv}".strip())
        for ec in item["external_calls"]:
            call_texts.append(ec["call_text"])
            
    print(f"[{source_name}] Collected: {len(function_texts)} functions, {len(state_var_texts)} state vars, {len(call_texts)} calls")
    
    # Batch encode
    function_emb_map = batch_encode_texts(function_texts, max_length=256, batch_size=32)
    state_var_emb_map = batch_encode_texts(state_var_texts, max_length=256, batch_size=32)
    call_emb_map = batch_encode_texts(call_texts, max_length=64, batch_size=32)
    
    # Construct final items
    final_dataset = []
    for item in raw_items:
        func_emb = function_emb_map[item["func_src"]]
        
        sv_embs = {}
        for sv in item["state_vars_accessed"]:
            sv_type = item["state_var_types"].get(sv, "")
            text = f"{sv_type} {sv}".strip()
            sv_embs[sv] = state_var_emb_map[text]
            
        ec_embs = []
        for ec in item["external_calls"]:
            call_text = ec["call_text"]
            ec_embs.append({
                "call_text": call_text,
                "embedding": call_emb_map[call_text]
            })
            
        final_item = {
            "file": item["file"],
            "contract": item["contract"],
            "function": item["function"],
            "label": item["label"],
            "source": item["source"],
            "is_cross_contract": item["is_cross_contract"],
            "state_vars_accessed": item["state_vars_accessed"],
            "external_calls": [ec["call_text"] for ec in item["external_calls"]],
            "node_features": {
                "function": func_emb,
                "state_vars": sv_embs,
                "external_calls": ec_embs
            },
            "source_id": f"external_{item['source'].lower()}",
            "is_variant": False
        }
        final_dataset.append(final_item)
        
    return final_dataset

def main():
    # 1. Process Aave V3
    aave_dir = CLONES_DIR / "aave-v3" / "contracts"
    raw_aave = extract_hyperedges_from_dir(aave_dir, "AaveV3")
    print(f"Extracted {len(raw_aave)} raw Aave V3 hyperedges.")
    
    # Load mapping
    with open(AAVE_MAPPING_PATH) as f:
        aave_mapping = json.load(f)
        
    # Split raw Aave
    raw_aave_train = []
    raw_aave_val = []
    for item in raw_aave:
        split = aave_mapping.get(item["file"], "val")
        if split == "train":
            raw_aave_train.append(item)
        else:
            raw_aave_val.append(item)
            
    print(f"Aave Splits - Raw Train: {len(raw_aave_train)}, Raw Val: {len(raw_aave_val)}")
    
    # Encode Aave
    print("\nEncoding Aave Train...")
    aave_train_encoded = build_dataset_with_embeddings(raw_aave_train, "AaveV3-Train")
    print("\nEncoding Aave Val...")
    aave_val_encoded = build_dataset_with_embeddings(raw_aave_val, "AaveV3-Val")
    
    # Add split key to encoded items
    for item in aave_train_encoded:
        item["split"] = "train"
    for item in aave_val_encoded:
        item["split"] = "val"
        
    aave_encoded = aave_train_encoded + aave_val_encoded
    with open(AAVE_OUTPUT_FILE, "w") as f:
        json.dump(aave_encoded, f, indent=2)
    print(f"Saved {len(aave_encoded)} Aave V3 encoded hyperedges to {AAVE_OUTPUT_FILE}")
    
    # 2. Process Liquity V1
    liquity_dir = CLONES_DIR / "liquity" / "packages" / "contracts" / "contracts"
    raw_liquity = extract_hyperedges_from_dir(liquity_dir, "Liquity")
    print(f"Extracted {len(raw_liquity)} raw Liquity hyperedges.")
    
    # Encode Liquity
    print("\nEncoding Liquity...")
    liquity_encoded = build_dataset_with_embeddings(raw_liquity, "Liquity")
    
    with open(LIQUITY_OUTPUT_FILE, "w") as f:
        json.dump(liquity_encoded, f, indent=2)
    print(f"Saved {len(liquity_encoded)} Liquity encoded hyperedges to {LIQUITY_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
