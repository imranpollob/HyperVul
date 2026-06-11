#!/usr/bin/env python3
import json
import sys
import hashlib
import torch
from pathlib import Path
from collections import defaultdict, Counter
import tree_sitter as ts
import tree_sitter_solidity as tss
from transformers import RobertaTokenizer, RobertaModel

# Setup paths
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

FORGE_VULN_DIR = PROJECT_ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
DAPPSCAN_ROOT = PROJECT_ROOT / "data" / "DAppSCAN"
OZ_CONTRACTS_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

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

# ---------------------------------------------------------------------------
# CONTRACT CACHING & LOOKUPS
# ---------------------------------------------------------------------------

# Cache for DAppSCAN projects
dappscan_projects_cache = {}

def get_dappscan_project_contracts(filepath):
    # Find project root for this file to parse all files in project for inheritance
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
                
    for vid, vdata in vfp_data.items():
        if item['file'] in vdata.get('affected_files', {}) or file_name in vdata.get('affected_files', {}):
            return vid
    return None

# Load OpenZeppelin contracts globally
print("Parsing OpenZeppelin contracts...")
oz_contracts = {}
for sol_file in OZ_CONTRACTS_DIR.glob("**/*.sol"):
    try:
        with open(sol_file, "r", encoding="utf-8", errors="ignore") as fh:
            s = fh.read()
        oz_contracts.update(nhs.parse_contracts(s))
    except Exception:
        pass
print(f"Loaded {len(oz_contracts)} OpenZeppelin contracts.")

# ---------------------------------------------------------------------------
# BATCH ENCODING USING SmartBERT-v3
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# FEATURE EXTRACTION PROCESSOR
# ---------------------------------------------------------------------------

def extract_features_for_dataset(input_file_path, output_file_path):
    print("=" * 80)
    print(f"Extracting features for {input_file_path.name}")
    print("=" * 80)
    
    with open(input_file_path) as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} items.")
    
    processed_items = []
    
    # Text collection for batch encoding
    function_texts = []
    state_var_texts = []
    call_texts = []
    
    # Store temporary info for reconstruction
    temp_info = []
    
    for idx, item in enumerate(dataset):
        if idx % 100 == 0:
            print(f"Locating sources for item {idx}/{len(dataset)}...")
            
        contract = item['contract']
        func_name = item.get('function') or item.get('ast_function')
        source_type = item.get('source')
        
        # Override source type from path if needed
        filepath = item.get('file') or item.get('filePath')
        if not source_type:
            if "openzeppelin" in str(filepath).lower():
                source_type = "OpenZeppelin"
            elif "dappscan" in str(filepath).lower() or 'project_root' in item:
                source_type = "DAppSCAN"
            else:
                source_type = "FORGE"
                
        # Resolve source code and project contracts
        source_code = None
        all_contracts = {}
        
        if source_type == "OpenZeppelin":
            full_path = PROJECT_ROOT / filepath
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    source_code = fh.read()
                all_contracts = oz_contracts
            else:
                print(f"Warning: OpenZeppelin file {full_path} not found.")
                continue
        elif source_type == "DAppSCAN":
            full_path = DAPPSCAN_ROOT / filepath
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    source_code = fh.read()
                all_contracts = get_dappscan_project_contracts(filepath)
            else:
                print(f"Warning: DAppSCAN file {full_path} not found.")
                continue
        else:
            # FORGE
            vfp_id = item.get('vfp_id') or find_forge_vfp_id(item)
            if vfp_id:
                file_name = Path(item['file']).name
                source_code = vfp_data[vfp_id]['affected_files'].get(item['file']) or vfp_data[vfp_id]['affected_files'].get(file_name)
                # Load all files in VFP
                for fn, fc in vfp_data[vfp_id]['affected_files'].items():
                    all_contracts.update(nhs.parse_contracts(fc))
            else:
                print(f"Warning: FORGE vfp_id not found for item {idx}.")
                continue
                
        if not source_code:
            print(f"Warning: Source code empty for item {idx}.")
            continue
            
        try:
            parsed = nhs.parse_contracts(source_code)
            merged_contracts = dict(all_contracts)
            merged_contracts.update(parsed)
            
            all_funcs = nhs.resolve_all_functions(contract, merged_contracts)
            if func_name not in all_funcs:
                print(f"Warning: Function {func_name} not found in {contract} for item {idx}.")
                continue
                
            func_node = all_funcs[func_name]
            func_src = nhs.node_text(func_node)
            
            state_var_types = nhs.resolve_all_state_var_types(contract, merged_contracts)
            
            # Record texts to be encoded
            function_texts.append(func_src)
            
            item_sv_texts = {}
            for sv in item['state_vars_accessed']:
                sv_type = state_var_types.get(sv, "")
                text = f"{sv_type} {sv}".strip()
                state_var_texts.append(text)
                item_sv_texts[sv] = text
                
            item_ec_texts = []
            for ec in item['external_calls']:
                call_texts.append(ec['call_text'])
                item_ec_texts.append(ec['call_text'])
                
            # Store metadata for features assignment
            temp_info.append({
                "item": item,
                "func_src": func_src,
                "sv_texts": item_sv_texts,
                "ec_texts": item_ec_texts
            })
            
        except Exception as e:
            print(f"Exception parsing item {idx} ({contract}.{func_name}): {e}")
            continue
            
    print(f"Located sources for {len(temp_info)} items. Encoding...")
    
    # Batch encode texts
    function_emb_map = batch_encode_texts(function_texts, max_length=256, batch_size=32)
    state_var_emb_map = batch_encode_texts(state_var_texts, max_length=256, batch_size=32)
    call_emb_map = batch_encode_texts(call_texts, max_length=64, batch_size=32)
    
    # Construct final dataset
    final_dataset = []
    for info in temp_info:
        item = info['item']
        func_emb = function_emb_map[info['func_src']]
        
        sv_embs = {}
        for sv, text in info['sv_texts'].items():
            sv_embs[sv] = state_var_emb_map[text]
            
        ec_embs = []
        for call_text in info['ec_texts']:
            ec_embs.append({
                "call_text": call_text,
                "embedding": call_emb_map[call_text]
            })
            
        item['node_features'] = {
            "function": func_emb,
            "state_vars": sv_embs,
            "external_calls": ec_embs
        }
        # Add source_id if not present for provenance tracking
        if 'source_id' not in item:
            item['source_id'] = item.get('vfp_id') or item.get('project_root') or "eval_item"
        if 'is_variant' not in item:
            item['is_variant'] = False
            
        final_dataset.append(item)
        
    # Save the output file
    with open(output_file_path, "w") as fh:
        json.dump(final_dataset, fh, indent=2)
    print(f"Successfully saved {len(final_dataset)} items with features to {output_file_path}")
    print("=" * 80)

if __name__ == '__main__':
    # Extract features for all three sets
    extract_features_for_dataset(SPLITS_DIR / "val.json", SPLITS_DIR / "val_features.json")
    extract_features_for_dataset(SPLITS_DIR / "test.json", SPLITS_DIR / "test_features.json")
    extract_features_for_dataset(RESULTS_DIR / "eval_clean_negatives_oz.json", RESULTS_DIR / "eval_clean_negatives_oz_features.json")
