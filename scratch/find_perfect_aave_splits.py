import json
import sys
import re
import hashlib
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

AAVE_DIR = PROJECT_ROOT / "scratch" / "clones" / "aave-v3" / "contracts"

def get_normalized_hash(src):
    # Remove single line comments
    src = re.sub(r'//.*', '', src)
    # Remove multi-line comments
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
    # Remove all whitespace
    src = re.sub(r'\s+', '', src)
    return hashlib.sha256(src.encode('utf-8')).hexdigest()

def main():
    sol_files = list(AAVE_DIR.glob("**/*.sol"))
    print(f"Found {len(sol_files)} Solidity files in Aave V3 Core.")
    
    # 1. Parse all contracts first
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
            
    print(f"Parsed {len(all_contracts)} contracts.")
    
    # 2. Extract hyperedges and function hashes
    raw_hyperedges = []
    file_to_funcs = defaultdict(list)
    hash_to_files = defaultdict(set)
    
    for sf, contracts in file_contracts.items():
        rel_f = str(Path(sf).relative_to(AAVE_DIR))
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
                        h = get_normalized_hash(func_src)
                        
                        raw_hyperedges.append({
                            "file": rel_f,
                            "contract": contract_name,
                            "function": func_name,
                            "func_src": func_src,
                            "hash": h
                        })
                        file_to_funcs[rel_f].append(h)
                        hash_to_files[h].add(rel_f)
            except Exception as e:
                pass
                
    print(f"Extracted {len(raw_hyperedges)} raw hyperedges from Aave V3.")
    
    # 3. Parse imports to build adjacency
    import_regex = re.compile(r'import\s+(?:(?:\{[^\}]*\}|\*)\s+from\s+)?["\']([^"\']+)["\'];')
    import_graph = defaultdict(set)
    
    for sf in sol_files:
        rel_f = str(sf.relative_to(AAVE_DIR))
        try:
            with open(sf, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
            imports = import_regex.findall(content)
            for imp in imports:
                # Resolve relative imports
                if imp.startswith(".") or "/" in imp:
                    current_dir = sf.parent
                    resolved = (current_dir / imp).resolve()
                    try:
                        imp_rel = str(resolved.relative_to(AAVE_DIR)).replace("\\", "/")
                        if (AAVE_DIR / imp_rel).exists():
                            import_graph[rel_f].add(imp_rel)
                            import_graph[imp_rel].add(rel_f)
                    except ValueError:
                        pass
        except Exception as e:
            pass
            
    # 4. Build adjacency list of files
    all_active_files = set(file_to_funcs.keys())
    adj = defaultdict(set)
    
    # Add import edges
    for u, neighbors in import_graph.items():
        if u in all_active_files:
            for v in neighbors:
                if v in all_active_files:
                    adj[u].add(v)
                    adj[v].add(u)
                    
    # Add identical function hash edges
    for h, files in hash_to_files.items():
        f_list = list(files)
        for i in range(len(f_list) - 1):
            f1, f2 = f_list[i], f_list[i+1]
            adj[f1].add(f2)
            adj[f2].add(f1)
            
    # 5. Connected components
    visited = set()
    components = []
    
    for node in all_active_files:
        if node not in visited:
            comp = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)
            
    components.sort(key=lambda x: sum(len(file_to_funcs[f]) for f in x), reverse=True)
    
    print(f"\nFound {len(components)} connected components in active Aave files:")
    for idx, comp in enumerate(components):
        total_edges = sum(len(file_to_funcs[f]) for f in comp)
        print(f"  Component {idx+1}: {len(comp)} files, {total_edges} hyperedges")
        
    # Let's perform split assignment (aiming for ~80/20 train/val hyperedges)
    train_files = set()
    val_files = set()
    train_edges = 0
    val_edges = 0
    
    # We assign greedily: since Aave V3 Core has a big giant component (like OZ did),
    # let's look at the actual distribution of components.
    total_hyperedges = len(raw_hyperedges)
    target_val = int(total_hyperedges * 0.20)
    
    # Let's assign components to val until we are close to target_val, and the rest to train.
    # Note: Component 1 is probably very large.
    # Let's see how they split.
    for idx, comp in enumerate(components):
        comp_edges = sum(len(file_to_funcs[f]) for f in comp)
        # Greedily assign smaller components to val to get close to 20%
        if val_edges + comp_edges <= target_val or (idx > 0 and val_edges < target_val):
            val_files.update(comp)
            val_edges += comp_edges
        else:
            train_files.update(comp)
            train_edges += comp_edges
            
    print(f"\nProposed Split:")
    print(f"  Train: {len(train_files)} files, {train_edges} hyperedges ({train_edges/total_hyperedges*100:.2f}%)")
    print(f"  Val: {len(val_files)} files, {val_edges} hyperedges ({val_edges/total_hyperedges*100:.2f}%)")
    
    # Save the mapping
    mapping = {}
    for f in train_files:
        mapping[f] = "train"
    for f in val_files:
        mapping[f] = "val"
        
    mapping_path = PROJECT_ROOT / "scratch" / "aave_split_mapping.json"
    with open(mapping_path, "w") as fh:
        json.dump(mapping, fh, indent=2)
    print(f"Saved Aave split mapping to {mapping_path}")

if __name__ == "__main__":
    main()
