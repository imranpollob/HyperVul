import json
import sys
import hashlib
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

FORGE_VULN_DIR = PROJECT_ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
DAPPSCAN_ROOT = PROJECT_ROOT / "data" / "DAppSCAN"

def main():
    # Cache VFP data
    vfp_data = {}
    for p in FORGE_VULN_DIR.glob('*.json'):
        with open(p) as f:
            vfp_data[p.stem] = json.load(f)
            
    # Load train split
    with open(PROJECT_ROOT / "data/splits/train.json") as f:
        train_data = json.load(f)
        
    print(f"Loaded {len(train_data)} train items.")
    
    missing_source = 0
    missing_func = 0
    hash_mismatches = 0
    
    for idx, item in enumerate(train_data):
        label = item['label']
        contract = item['contract']
        func_name = item.get('function') or item.get('ast_function')
        source_type = "DAppSCAN" if (item.get('source') == 'DAppSCAN' or 'project_root' in item) else "FORGE"
        
        # Load file source code
        source_code = None
        if source_type == "DAppSCAN":
            filepath = item.get('file') or item.get('filePath')
            full_path = DAPPSCAN_ROOT / filepath
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    source_code = fh.read()
            else:
                print(f"DAppSCAN file not found: {full_path}")
        else:
            # FORGE
            vfp_id = item.get('vfp_id')
            file_name = Path(item['file']).name
            if vfp_id:
                # Positive
                source_code = vfp_data[vfp_id]['affected_files'].get(item['file']) or vfp_data[vfp_id]['affected_files'].get(file_name)
            else:
                # Negative
                # Find which VFP contains this file and function
                target_hash = item['normalized_source_hash']
                found_vfp = None
                for vid, vdata in vfp_data.items():
                    if item['file'] in vdata.get('affected_files', {}) or file_name in vdata.get('affected_files', {}):
                        # Try to see if this file has the function with the matching hash
                        fcode = vdata['affected_files'].get(item['file']) or vdata['affected_files'].get(file_name)
                        try:
                            parsed = nhs.parse_contracts(fcode)
                            all_funcs = nhs.resolve_all_functions(contract, parsed)
                            if func_name in all_funcs:
                                func_node = all_funcs[func_name]
                                func_src = nhs.node_text(func_node)
                                norm_hash = hashlib.sha256(nhs.normalize_source(func_src).encode('utf-8')).hexdigest()
                                if norm_hash == target_hash:
                                    found_vfp = vid
                                    source_code = fcode
                                    break
                        except Exception:
                            pass
                if not found_vfp:
                    # fallback to any VFP containing the file
                    for vid, vdata in vfp_data.items():
                        if item['file'] in vdata.get('affected_files', {}) or file_name in vdata.get('affected_files', {}):
                            source_code = vdata['affected_files'].get(item['file']) or vdata['affected_files'].get(file_name)
                            break
                            
        if source_code is None:
            missing_source += 1
            print(f"[{idx}] Source not found for {source_type} {contract}.{func_name}")
            continue
            
        # Parse and resolve function
        try:
            parsed = nhs.parse_contracts(source_code)
            all_funcs = nhs.resolve_all_functions(contract, parsed)
            if func_name not in all_funcs:
                # try finding in all contracts of the project for inheritance
                if source_type == "FORGE":
                    # resolve across all files in the VFP
                    vfp_id = item.get('vfp_id')
                    if not vfp_id:
                        # find vfp_id from cached mapping
                        for vid, vdata in vfp_data.items():
                            if item['file'] in vdata.get('affected_files', {}) or file_name in vdata.get('affected_files', {}):
                                vfp_id = vid
                                break
                    if vfp_id:
                        all_contracts = {}
                        for fn, fc in vfp_data[vfp_id]['affected_files'].items():
                            all_contracts.update(nhs.parse_contracts(fc))
                        all_funcs = nhs.resolve_all_functions(contract, all_contracts)
                else:
                    # DAppSCAN: resolve across all files in the project
                    # Find project root
                    filepath = item.get('file') or item.get('filePath')
                    full_path = DAPPSCAN_ROOT / filepath
                    proj_root = nhs.find_project_root(full_path)
                    project_contracts = {}
                    for sol_file in proj_root.glob("**/*.sol"):
                        try:
                            with open(sol_file, "r", encoding="utf-8", errors="ignore") as fh:
                                s = fh.read()
                            project_contracts.update(nhs.parse_contracts(s))
                        except Exception:
                            pass
                    all_funcs = nhs.resolve_all_functions(contract, project_contracts)
                    
            if func_name not in all_funcs:
                missing_func += 1
                print(f"[{idx}] Function {func_name} not found in {contract} AST")
                continue
                
            func_node = all_funcs[func_name]
            func_src = nhs.node_text(func_node)
            norm_hash = hashlib.sha256(nhs.normalize_source(func_src).encode('utf-8')).hexdigest()
            if norm_hash != item['normalized_source_hash']:
                hash_mismatches += 1
                # print(f"[{idx}] Hash mismatch: expected {item['normalized_source_hash']}, got {norm_hash}")
        except Exception as e:
            print(f"[{idx}] Exception parsing {contract}.{func_name}: {e}")
            missing_func += 1
            
    print(f"Summary: missing source: {missing_source}, missing func: {missing_func}, hash mismatches: {hash_mismatches}")

if __name__ == "__main__":
    main()
