import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

CLONES_DIR = PROJECT_ROOT / "scratch" / "clones"
CLONES_DIR.mkdir(parents=True, exist_ok=True)

def clone_repo(url, folder_name):
    target = CLONES_DIR / folder_name
    if target.exists():
        print(f"{folder_name} already cloned.")
        return target
    print(f"Cloning {url} to {target}...")
    subprocess.run(["git", "clone", "--depth", "1", url, str(target)], check=True)
    return target

def extract_hyperedges(contracts_dir):
    print(f"Scanning {contracts_dir} for Solidity files...")
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
            
    print(f"Total parsed contracts: {len(all_contracts)}")
    
    hyperedges = []
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
                        hyperedges.append({
                            "file": sf,
                            "contract": contract_name,
                            "function": func_name,
                            "state_vars_accessed": accessed_vars,
                            "external_calls": ext_calls
                        })
            except Exception as e:
                pass
                
    return hyperedges

def main():
    candidates = [
        {"url": "https://github.com/Synthetixio/synthetix-v3.git", "folder": "synthetix-v3", "sub": "protocol"},
        {"url": "https://github.com/bancorprotocol/contracts-v3.git", "folder": "bancor-v3", "sub": "contracts"}
    ]
    
    for cand in candidates:
        print("\n" + "="*50)
        print(f"Candidate: {cand['folder']}")
        print("="*50)
        try:
            repo_path = clone_repo(cand['url'], cand['folder'])
            contracts_path = repo_path / cand['sub']
            hyperedges = extract_hyperedges(contracts_path)
            print(f"Successfully extracted {len(hyperedges)} hyperedges for {cand['folder']}!")
        except Exception as e:
            print(f"Failed to process {cand['folder']}: {e}")

if __name__ == "__main__":
    main()

