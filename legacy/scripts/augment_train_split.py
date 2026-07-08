#!/usr/bin/env python3
import json
import re
import sys
import hashlib
import random
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
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def clean_comments_and_whitespace(src: str) -> str:
    # Transform 2: comment removal
    src = re.sub(r'//.*', '', src)
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
    
    # Whitespace normalization (preserves lines, cleans spacing)
    lines = [line.strip() for line in src.splitlines() if line.strip()]
    normalized_lines = []
    for line in lines:
        normalized_lines.append(" ".join(line.split()))
    return "\n".join(normalized_lines)


def literal_substitution(src: str) -> str:
    # Transform 3: equivalent literal substitutions
    # 0x0 ↔ address(0)
    has_0x0 = bool(re.search(r'\b0x0\b', src))
    has_addr0 = "address(0)" in src
    if has_0x0:
        src = re.sub(r'\b0x0\b', 'address(0)', src)
    elif has_addr0:
        src = src.replace('address(0)', '0x0')
        
    # uint ↔ uint256
    has_uint = bool(re.search(r'\buint\b', src))
    has_uint256 = bool(re.search(r'\buint256\b', src))
    if has_uint:
        src = re.sub(r'\buint\b', 'uint256', src)
    elif has_uint256:
        src = re.sub(r'\buint256\b', 'uint', src)
        
    return src


def inject_inert_statement(func_src: str, at_start: bool, seed_val: int) -> str:
    # Transform 4: inject inert calculations at the start or end of the function body
    tree = PARSER.parse(func_src.encode('utf-8'))
    root = tree.root_node
    
    func_def = None
    if root.type == "function_definition":
        func_def = root
    else:
        for child in root.children:
            if child.type == "function_definition":
                func_def = child
                break
    if not func_def:
        return func_src
        
    block_node = None
    for child in func_def.children:
        if child.type == "block":
            block_node = child
            break
    if not block_node:
        return func_src
        
    open_brace = None
    close_brace = None
    for child in block_node.children:
        if child.type == "{":
            open_brace = child
        elif child.type == "}":
            close_brace = child
            
    # Insert a semantically inert calculation
    inert_stmt = f"\n        uint256 _inert_val_{seed_val} = {seed_val} + {seed_val + 1};\n"
    
    func_bytes = func_src.encode('utf-8')
    if at_start and open_brace:
        idx = open_brace.end_byte
        new_bytes = func_bytes[:idx] + inert_stmt.encode('utf-8') + func_bytes[idx:]
        return new_bytes.decode('utf-8', errors='ignore')
    elif not at_start and close_brace:
        idx = close_brace.start_byte
        new_bytes = func_bytes[:idx] + inert_stmt.encode('utf-8') + func_bytes[idx:]
        return new_bytes.decode('utf-8', errors='ignore')
        
    return func_src


def get_renameable_vars(func_node, contract_state_vars, contract_funcs, ext_calls):
    local_vars = nhs.extract_local_vars(func_node)
    call_receivers = set()
    for ec in ext_calls:
        rec = ec.get('receiver')
        if rec:
            call_receivers.add(rec)
            
    renameable = set()
    for v in local_vars:
        if v in contract_state_vars:
            continue
        if v in nhs.BUILTIN_GLOBALS:
            continue
        if v in contract_funcs:
            continue
        if v in call_receivers:
            continue
        if len(v) > 0:
            renameable.add(v)
    return renameable


def rename_local_vars(func_src, renameable_vars, suffix):
    tree = PARSER.parse(func_src.encode('utf-8'))
    root = tree.root_node
    
    new_names_map = {v: f"{v}_{suffix}" for v in renameable_vars}
    replacements = []
    
    def traverse(node):
        if node.type == "identifier":
            name = node.text.decode('utf-8', errors='ignore')
            if name in renameable_vars:
                # Do not rename if it is a member access property (e.g. object.property)
                if node.parent and node.parent.type == "member_expression":
                    if node == node.parent.children[-1]:
                        return
                replacements.append((node.start_byte, node.end_byte, new_names_map[name]))
                return
        for child in node.children:
            traverse(child)
            
    traverse(root)
    
    # Apply replacements descending to preserve offsets
    replacements = sorted(replacements, key=lambda x: x[0], reverse=True)
    func_bytes = func_src.encode('utf-8')
    for start, end, new_text in replacements:
        func_bytes = func_bytes[:start] + new_text.encode('utf-8') + func_bytes[end:]
    return func_bytes.decode('utf-8', errors='ignore')


# ---------------------------------------------------------------------------
# EVENT ORDER TRACING FOR CONSTRAINT C
# ---------------------------------------------------------------------------

def get_sequence_of_events(func_node, state_vars, state_var_types, all_contracts, ext_calls):
    sequence = []
    local_vars = nhs.extract_local_vars(func_node)
    
    def is_external_call_node(node):
        if node.type == "call_expression":
            call_text = nhs.node_text(node)[:120].strip()
            for ec in ext_calls:
                ec_text = ec['call_text'].strip()
                if ec_text in call_text or call_text in ec_text:
                    return True
        return False

    def is_write_context(node):
        current = node.parent
        while current and current != func_node:
            if current.type == "assignment_expression":
                left = current.child_by_field_name("left")
                temp = node
                while temp and temp != current:
                    if temp == left:
                        return True
                    temp = temp.parent
                return False
            if current.type == "update_expression":
                return True
            current = current.parent
        return False

    def visit(node):
        if is_external_call_node(node):
            sequence.append(("call", nhs.node_text(node)[:50]))
            for child in node.children:
                visit(child)
            return

        if node.type == "identifier":
            name = nhs.node_text(node)
            if name in state_vars and name not in local_vars and name not in nhs.BUILTIN_GLOBALS:
                parent = node.parent
                if parent and parent.type in ("type_name", "user_defined_type", "pragma_directive",
                                              "import_directive", "inheritance_specifier",
                                              "emit_statement", "event_definition",
                                              "error_definition"):
                    pass
                else:
                    if is_write_context(node):
                        sequence.append(("write", name))
                    else:
                        sequence.append(("read", name))
            return

        for child in node.children:
            visit(child)

    visit(func_node)
    return sequence

# ---------------------------------------------------------------------------
# LOADING SOURCE CODES FOR train.json ITEMS
# ---------------------------------------------------------------------------

def load_dappscan_project_contracts(file_path):
    full_path = DAPPSCAN_ROOT / file_path
    try:
        proj_root = nhs.find_project_root(full_path)
    except Exception:
        parts = Path(file_path).parts
        if len(parts) >= 3:
            proj_root = DAPPSCAN_ROOT / parts[0] / parts[1] / parts[2]
        else:
            proj_root = full_path.parent
            
    project_contracts = {}
    if proj_root.exists():
        for sol_file in proj_root.glob("**/*.sol"):
            try:
                with open(sol_file, "r", encoding="utf-8", errors="ignore") as fh:
                    s = fh.read()
                project_contracts.update(nhs.parse_contracts(s))
            except Exception:
                pass
    return project_contracts


def find_forge_vfp_id(item, vfp_data):
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
# MAIN AUGMENTATION PIPELINE
# ---------------------------------------------------------------------------

def run_augmentation():
    print("=" * 80)
    print("HyperVul — Train Split Augmentation Pipeline")
    print("=" * 80)
    
    # 1. Load splits
    with open(SPLITS_DIR / "train.json") as f:
        train_data = json.load(f)
    with open(SPLITS_DIR / "val.json") as f:
        val_data = json.load(f)
    with open(SPLITS_DIR / "test.json") as f:
        test_data = json.load(f)
        
    print(f"Loaded train: {len(train_data)}, val: {len(val_data)}, test: {len(test_data)}.")
    
    # Collect val and test hashes for leakage checking
    val_hashes = set(item['normalized_source_hash'] for item in val_data)
    test_hashes = set(item['normalized_source_hash'] for item in test_data)
    eval_hashes = val_hashes | test_hashes
    print(f"Loaded {len(eval_hashes)} evaluation hashes for leakage prevention.")
    
    # Load FORGE VFP files
    vfp_data = {}
    for p in FORGE_VULN_DIR.glob('*.json'):
        with open(p) as f:
            vfp_data[p.stem] = json.load(f)
            
    # Discard counters
    discard_reasons = Counter()
    total_generated = 0
    total_accepted = 0
    
    pos_candidates = []
    neg_candidates = []
    
    # Let's loop and generate variants
    random.seed(42)
    
    for idx, item in enumerate(train_data):
        if idx % 100 == 0:
            print(f"Processing train item {idx}/{len(train_data)}...")
            
        contract = item['contract']
        func_name = item.get('function') or item.get('ast_function')
        label = item['label']
        source_type = "DAppSCAN" if (item.get('source') == 'DAppSCAN' or 'project_root' in item) else "FORGE"
        
        # Load file source and project contracts
        source_code = None
        all_contracts = {}
        
        if source_type == "DAppSCAN":
            filepath = item.get('file') or item.get('filePath')
            full_path = DAPPSCAN_ROOT / filepath
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    source_code = fh.read()
                all_contracts = load_dappscan_project_contracts(filepath)
            else:
                continue
        else:
            # FORGE
            vfp_id = item.get('vfp_id') or find_forge_vfp_id(item, vfp_data)
            if vfp_id:
                file_name = Path(item['file']).name
                source_code = vfp_data[vfp_id]['affected_files'].get(item['file']) or vfp_data[vfp_id]['affected_files'].get(file_name)
                # Load all files in VFP
                for fn, fc in vfp_data[vfp_id]['affected_files'].items():
                    all_contracts.update(nhs.parse_contracts(fc))
            else:
                continue
                
        if not source_code:
            continue
            
        # Parse contracts and resolve functions
        try:
            parsed = nhs.parse_contracts(source_code)
            # update with all contracts in the project for inheritance
            merged_contracts = dict(all_contracts)
            merged_contracts.update(parsed)
            
            all_funcs = nhs.resolve_all_functions(contract, merged_contracts)
            if func_name not in all_funcs:
                continue
                
            func_node = all_funcs[func_name]
            original_src = nhs.node_text(func_node)
            original_hash = item['normalized_source_hash']
            
            # Extract state vars and calls
            state_vars = nhs.resolve_all_state_vars(contract, merged_contracts)
            state_var_types = nhs.resolve_all_state_var_types(contract, merged_contracts)
            ext_calls = nhs.find_external_calls_ast(func_node, state_var_types, merged_contracts, allow_fallback=False)
            
            # Find renameable variables
            contract_funcs = set(all_funcs.keys())
            renameable_vars = get_renameable_vars(func_node, state_vars, contract_funcs, ext_calls)
            
            # Get original sequence of events for constraint c
            original_seq = get_sequence_of_events(func_node, state_vars, state_var_types, merged_contracts, ext_calls)
            
        except Exception as e:
            # print(f"Exception preparing {contract}.{func_name}: {e}")
            continue
            
        # Target number of variants
        num_variants = 5 if label == 1 else 2
        item_variants = []
        seen_hashes = {original_hash}
        
        for v_idx in range(1, num_variants + 1):
            total_generated += 1
            seed_val = idx * 100 + v_idx
            
            variant_src = original_src
            
            try:
                # Apply transform combinations
                if v_idx == 1:
                    if renameable_vars:
                        variant_src = rename_local_vars(variant_src, renameable_vars, f"aug{v_idx}")
                    variant_src = literal_substitution(variant_src)
                elif v_idx == 2:
                    variant_src = clean_comments_and_whitespace(variant_src)
                    variant_src = inject_inert_statement(variant_src, at_start=True, seed_val=seed_val)
                elif v_idx == 3:
                    variant_src = literal_substitution(variant_src)
                    variant_src = inject_inert_statement(variant_src, at_start=False, seed_val=seed_val)
                elif v_idx == 4:
                    if renameable_vars:
                        variant_src = rename_local_vars(variant_src, renameable_vars, f"aug{v_idx}")
                    variant_src = clean_comments_and_whitespace(variant_src)
                elif v_idx == 5:
                    if renameable_vars:
                        variant_src = rename_local_vars(variant_src, renameable_vars, f"aug{v_idx}")
                    variant_src = literal_substitution(variant_src)
                    variant_src = inject_inert_statement(variant_src, at_start=True, seed_val=seed_val)
                    variant_src = clean_comments_and_whitespace(variant_src)
                
                # Compute variant hash
                norm_variant = nhs.normalize_source(variant_src)
                var_hash = hashlib.sha256(norm_variant.encode('utf-8')).hexdigest()
                
                # Check for duplicates or empty
                if var_hash in seen_hashes:
                    discard_reasons["duplicate_variant"] += 1
                    continue
                if len(variant_src.strip()) == 0:
                    discard_reasons["empty_source"] += 1
                    continue
                    
                # Verification: AST parsing of the variant
                var_tree = PARSER.parse(variant_src.encode('utf-8'))
                var_root = var_tree.root_node
                
                # Find the function node in the variant AST
                var_func_node = None
                if var_root.type == "function_definition":
                    var_func_node = var_root
                else:
                    for child in var_root.children:
                        if child.type == "function_definition":
                            var_func_node = child
                            break
                            
                if not var_func_node:
                    discard_reasons["parse_failure"] += 1
                    continue
                    
                # Verify AST checks (a, b, c)
                var_local_vars = nhs.extract_local_vars(var_func_node)
                var_accessed_vars = nhs.find_state_var_accesses(var_func_node, state_vars, var_local_vars)
                var_ext_calls = nhs.find_external_calls_ast(var_func_node, state_var_types, merged_contracts, allow_fallback=False)
                
                # Check a: constructability
                if len(var_accessed_vars) == 0 or len(var_ext_calls) == 0:
                    discard_reasons["not_constructable"] += 1
                    continue
                    
                # Check b: hyperedge structure preservation
                if len(var_ext_calls) != len(ext_calls):
                    discard_reasons["call_count_mismatch"] += 1
                    continue
                if sorted(var_accessed_vars) != sorted(state_vars_accessed := item['state_vars_accessed']):
                    discard_reasons["state_vars_mismatch"] += 1
                    continue
                var_is_cross = nhs.check_is_cross_contract(var_ext_calls, contract, state_var_types, var_local_vars, merged_contracts)
                if var_is_cross != item['is_cross_contract']:
                    discard_reasons["cross_contract_mismatch"] += 1
                    continue
                    
                # Check c: order of read/call/write preserved
                var_seq = get_sequence_of_events(var_func_node, state_vars, state_var_types, merged_contracts, var_ext_calls)
                # Map names to original names to ignore renamed variables in sequence match
                name_mapping = {f"{v}_aug{v_idx}": v for v in renameable_vars}
                mapped_var_seq = []
                for event_type, event_name in var_seq:
                    mapped_name = name_mapping.get(event_name, event_name)
                    mapped_var_seq.append((event_type, mapped_name))
                    
                if mapped_var_seq != original_seq:
                    discard_reasons["sequence_order_changed"] += 1
                    continue
                    
                # Leakage check: check if variant's normalized hash collides with val/test
                if var_hash in eval_hashes:
                    discard_reasons["eval_leakage_collision"] += 1
                    continue
                    
                # Valid variant accepted!
                seen_hashes.add(var_hash)
                
                provenance_item = dict(item)
                provenance_item['normalized_source_hash'] = var_hash
                provenance_item['function_source'] = variant_src
                provenance_item['is_variant'] = True
                provenance_item['source_id'] = item.get('vfp_id') or item.get('project_root') or "train_" + str(idx)
                provenance_item['transforms_applied'] = [
                    f"transform_{v_idx}"
                ]
                
                item_variants.append(provenance_item)
                total_accepted += 1
                
            except Exception as e:
                discard_reasons[f"exception_{type(e).__name__}"] += 1
                
        # Also store original item with its source code so we can encode it uniformly
        item_copy = dict(item)
        item_copy['function_source'] = original_src
        item_copy['is_variant'] = False
        
        if label == 1:
            pos_candidates.append(item_copy)
            pos_candidates.extend(item_variants)
        else:
            neg_candidates.append(item_copy)
            neg_candidates.extend(item_variants)
            
    print(f"Generation completed. Total generated: {total_generated}, Accepted: {total_accepted}.")
    print("Discard reasons:")
    for r, c in discard_reasons.most_common():
        print(f"  {r}: {c}")
        
    print(f"Original positives: {len([x for x in train_data if x['label']==1])}, candidates with variants: {len(pos_candidates)}")
    print(f"Original negatives: {len([x for x in train_data if x['label']==0])}, candidates with variants: {len(neg_candidates)}")
    
    # ---------------------------------------------------------------------------
    # STEP 9: DETERMINISTIC RANDOM SAMPLING (SEED 42)
    # ---------------------------------------------------------------------------
    # Target 870 of each class
    TARGET_COUNT = 870
    random.seed(42)
    
    # Shuffle variants only (keep original train items always!)
    original_positives = [x for x in pos_candidates if not x.get('is_variant')]
    variant_positives = [x for x in pos_candidates if x.get('is_variant')]
    original_negatives = [x for x in neg_candidates if not x.get('is_variant')]
    variant_negatives = [x for x in neg_candidates if x.get('is_variant')]
    
    random.shuffle(variant_positives)
    random.shuffle(variant_negatives)
    
    needed_pos = TARGET_COUNT - len(original_positives)
    needed_neg = TARGET_COUNT - len(original_negatives)
    
    selected_pos_variants = variant_positives[:needed_pos]
    selected_neg_variants = variant_negatives[:needed_neg]
    
    final_positives = original_positives + selected_pos_variants
    final_negatives = original_negatives + selected_neg_variants
    
    final_augmented_train = final_positives + final_negatives
    print(f"Final sampled count: positives: {len(final_positives)}, negatives: {len(final_negatives)}.")
    
    # ---------------------------------------------------------------------------
    # FEATURE EXTRACTION ON SELECTED ITEMS
    # ---------------------------------------------------------------------------
    # Collect all unique text spans that need encoding
    function_texts = []
    state_var_texts = []
    call_texts = []
    
    for item in final_augmented_train:
        # Calling function
        function_texts.append(item['function_source'])
        
        # State variables
        # We need to resolve contract state variables for types
        source_type = "DAppSCAN" if (item.get('source') == 'DAppSCAN' or 'project_root' in item) else "FORGE"
        contract = item['contract']
        
        # Resolve types
        state_var_types = {}
        if source_type == "DAppSCAN":
            filepath = item.get('file') or item.get('filePath')
            all_contracts = load_dappscan_project_contracts(filepath)
            state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)
        else:
            vfp_id = item.get('vfp_id') or find_forge_vfp_id(item, vfp_data)
            if vfp_id:
                all_contracts = {}
                for fn, fc in vfp_data[vfp_id]['affected_files'].items():
                    all_contracts.update(nhs.parse_contracts(fc))
                state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)
                
        for sv in item['state_vars_accessed']:
            sv_type = state_var_types.get(sv, "")
            text = f"{sv_type} {sv}".strip()
            state_var_texts.append(text)
            
        # External calls
        for ec in item['external_calls']:
            call_texts.append(ec['call_text'])
            
    # Batch encode
    function_emb_map = batch_encode_texts(function_texts, max_length=256, batch_size=32)
    state_var_emb_map = batch_encode_texts(state_var_texts, max_length=256, batch_size=32)
    call_emb_map = batch_encode_texts(call_texts, max_length=64, batch_size=32)
    
    # Assign embeddings to final train items
    print("Assigning node features to items...")
    for item in final_augmented_train:
        source_type = "DAppSCAN" if (item.get('source') == 'DAppSCAN' or 'project_root' in item) else "FORGE"
        contract = item['contract']
        
        # Resolve types
        state_var_types = {}
        if source_type == "DAppSCAN":
            filepath = item.get('file') or item.get('filePath')
            all_contracts = load_dappscan_project_contracts(filepath)
            state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)
        else:
            vfp_id = item.get('vfp_id') or find_forge_vfp_id(item, vfp_data)
            if vfp_id:
                all_contracts = {}
                for fn, fc in vfp_data[vfp_id]['affected_files'].items():
                    all_contracts.update(nhs.parse_contracts(fc))
                state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)
                
        # Function embedding
        func_emb = function_emb_map[item['function_source']]
        
        # State variables embeddings
        sv_embs = {}
        for sv in item['state_vars_accessed']:
            sv_type = state_var_types.get(sv, "")
            text = f"{sv_type} {sv}".strip()
            sv_embs[sv] = state_var_emb_map[text]
            
        # External call embeddings
        ec_embs = []
        for ec in item['external_calls']:
            ec_embs.append({
                "call_text": ec['call_text'],
                "embedding": call_emb_map[ec['call_text']]
            })
            
        # Store in dict
        item['node_features'] = {
            "function": func_emb,
            "state_vars": sv_embs,
            "external_calls": ec_embs
        }
        
    # Remove function_source prior to saving to save space, but wait, provenance and report might want to inspect it.
    # We can keep it or clean it up. Let's keep it for verification and clean output.
    
    # ---------------------------------------------------------------------------
    # LEAKAGE VERIFICATION CHECK
    # ---------------------------------------------------------------------------
    leakage_violations = 0
    for item in final_augmented_train:
        if item.get('is_variant'):
            h = item['normalized_source_hash']
            if h in eval_hashes:
                leakage_violations += 1
                
    print(f"Final leakage check violations: {leakage_violations}")
    
    # ---------------------------------------------------------------------------
    # SAVE train_augmented.json
    # ---------------------------------------------------------------------------
    with open(SPLITS_DIR / "train_augmented.json", "w") as fh:
        json.dump(final_augmented_train, fh, indent=2)
    print(f"Saved train_augmented.json to {SPLITS_DIR}/")
    
    # ---------------------------------------------------------------------------
    # WRITE REPORT TO augmentation_report.md
    # ---------------------------------------------------------------------------
    p_orig = len(original_positives)
    n_orig = len(original_negatives)
    p_aug = len(selected_pos_variants)
    n_aug = len(selected_neg_variants)
    
    report_content = f"""# HyperVul — Train Split Augmentation Report

> **Date**: 2026-06-11  
> **Original Train Set**: {len(train_data)} ({p_orig} Positives / {n_orig} Negatives)  
> **Augmented Train Set**: {len(final_augmented_train)} ({len(final_positives)} Positives / {len(final_negatives)} Negatives)  
> **Ratio**: {len(final_positives)}:{len(final_negatives)} ({len(final_positives)/len(final_negatives):.2f}:1)

---

## Executive Summary
This report documents the training data expansion using semantic-preserving transforms on the `train.json` split. The validation (`val.json`) and test (`test.json`) splits were preserved as untouched evaluation data. Node features were re-extracted using the frozen `web3se/SmartBERT-v3` encoder for both original items and accepted variants.

---

## Gating, Verification, and Discard Metrics

We enforced strict tree-sitter AST validation checks to ensure semantic identity was preserved:
1. **Check a (Constructability)**: External call present AND state variable access present.
2. **Check b (Structural Preservation)**: Same number of external calls, same state variable accesses, and same cross-contract vs. intra-contract classification.
3. **Check c (Sequence Ordering)**: Relative order of `{{state read, external call, state write}}` within the function remains identical.
4. **Leakage check**: No variant's hash matches any hash in validation or test splits.

### Discard Statistics
* **Total Variants Generated**: {total_generated}
* **Accepted Variants**: {total_accepted}
* **Discarded Variants**: {total_generated - total_accepted}

### Discard Reasons
{"".join(f"- **{reason}**: {count} variants\\n" for reason, count in discard_reasons.most_common())}

---

## Leakage Check Result
* **Val/Test Leakage Violations**: **{leakage_violations}**

---

## Feature Scheme Specification (CHANGE 1 Choice)

To guarantee consistency and avoid mismatch errors during G-HAN downstream architectures, we applied the **768-d uniform feature scheme**:
1. **Function nodes**: CLS token embedding from SmartBERT-v3 ($d=768$).
2. **State variable nodes**: CLS token embedding of `f"{{var_type}} {{var_name}}"` ($d=768$).
3. **Call site nodes**: CLS token embedding of `call_text` ($d=768$). Opcode flags (6-d) are omitted here and deferred to the downstream graph classification layers to keep the node embedding space uniform.

---

## Dataset Files
* [train_augmented.json](file:///home/pollmix/Coding/HyperVul/data/splits/train_augmented.json) — Final augmented train set containing original items + variants with metadata, provenance, and node features.
"""
    # Fix newline formats in report content
    report_content = report_content.replace("\\n", "\n")
    
    with open(RESULTS_DIR / "augmentation_report.md", "w") as fh:
        fh.write(report_content)
    print(f"Saved augmentation_report.md to {RESULTS_DIR}/")

if __name__ == "__main__":
    run_augmentation()
