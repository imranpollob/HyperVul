#!/usr/bin/env python3
import json
import sys
import hashlib
import torch
from pathlib import Path
from collections import defaultdict
import tree_sitter as ts
import tree_sitter_solidity as tss
from transformers import RobertaTokenizer, RobertaModel

# Setup paths
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

CLONES_DIR = PROJECT_ROOT / "scratch" / "clones"
OUTPUT_FILE = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_external.json"

# Load tree-sitter parser
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
                        
                        # Store in standardized format
                        raw_hyperedges.append({
                            "file": str(Path(sf).relative_to(PROJECT_ROOT)),
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

def main():
    # 1. Extract raw hyperedges
    makerdao_dir = CLONES_DIR / "makerdao-dss" / "src"
    bancor_dir = CLONES_DIR / "bancor-v3" / "contracts"
    
    raw_maker = extract_hyperedges_from_dir(makerdao_dir, "MakerDAO")
    raw_bancor = extract_hyperedges_from_dir(bancor_dir, "Bancor")
    
    all_raw = raw_maker + raw_bancor
    print(f"\nExtracted total raw hyperedges: {len(all_raw)} (MakerDAO: {len(raw_maker)}, Bancor: {len(raw_bancor)})")
    
    if not all_raw:
        print("Error: No hyperedges extracted!")
        sys.exit(1)
        
    # 2. Collect texts to encode
    function_texts = []
    state_var_texts = []
    call_texts = []
    
    for item in all_raw:
        function_texts.append(item["func_src"])
        for sv in item["state_vars_accessed"]:
            sv_type = item["state_var_types"].get(sv, "")
            state_var_texts.append(f"{sv_type} {sv}".strip())
        for ec in item["external_calls"]:
            call_texts.append(ec["call_text"])
            
    print(f"Collected for encoding: {len(function_texts)} functions, {len(state_var_texts)} state vars, {len(call_texts)} calls")
    
    # 3. Batch encode
    function_emb_map = batch_encode_texts(function_texts, max_length=256, batch_size=32)
    state_var_emb_map = batch_encode_texts(state_var_texts, max_length=256, batch_size=32)
    call_emb_map = batch_encode_texts(call_texts, max_length=64, batch_size=32)
    
    # 4. Construct final dataset with embeddings
    final_dataset = []
    for item in all_raw:
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
            
        # Standardized dataset item
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
        
    # 5. Save output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_dataset, f, indent=2)
        
    print(f"\nSuccessfully saved {len(final_dataset)} items with features to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

