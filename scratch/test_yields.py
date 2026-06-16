import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs

try:
    import tree_sitter as ts
    import tree_sitter_solidity as tss
    LANG = ts.Language(tss.language())
    PARSER = ts.Parser(LANG)
except Exception as e:
    print(f"Error loading tree-sitter: {e}")

CLONES_DIR = PROJECT_ROOT / "scratch" / "clones"

def count_hyperedges_in_dir(contracts_dir, source_name):
    sol_files = list(Path(contracts_dir).glob("**/*.sol"))
    print(f"\n[{source_name}] Scanning {contracts_dir}...")
    print(f"Found {len(sol_files)} Solidity files.")
    
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
    
    yield_count = 0
    cross_contract_count = 0
    
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
                        yield_count += 1
                        is_cross = any("call on contract-typed" in ec.get("reason", "") or 
                                       "call on interface/contract" in ec.get("reason", "")
                                       for ec in ext_calls)
                        if is_cross:
                            cross_contract_count += 1
            except Exception as e:
                pass
                
    print(f"Yield: {yield_count} hyperedges (Cross-contract: {cross_contract_count})")
    return yield_count

if __name__ == "__main__":
    count_hyperedges_in_dir(CLONES_DIR / "yearn-vaults" / "contracts", "Yearn Vaults")
    count_hyperedges_in_dir(CLONES_DIR / "synthetix-v3" / "protocol", "Synthetix V3 Protocol")
    count_hyperedges_in_dir(CLONES_DIR / "liquity" / "packages" / "contracts" / "contracts", "Liquity V1")
    count_hyperedges_in_dir(CLONES_DIR / "aave-v3" / "contracts", "Aave V3 Core")
