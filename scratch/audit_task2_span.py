"""Task 2 — print the literal strings fed to SmartBERT for one real test item. Read-only."""
import json, sys
from pathlib import Path
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT)); sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
import run_diagnostics as rd

test = json.load(open(PROJECT_ROOT / "data" / "splits" / "test.json"))
# pick a compact reentrancy positive
item = next(it for it in test if (it.get("function") or it.get("ast_function")) == "deposit"
            and it.get("contract") == "LendingPool")
src = rd.get_function_source(item)
contract = item["contract"]; fn = item.get("function") or item.get("ast_function")
print(f"ITEM: {contract}.{fn}  (label={item['label']}, vtype={item.get('vtype') or item.get('swc_code') or item.get('category')})")
print("\n--- FUNCTION NODE span fed to encoder (max_length=256, truncation=True) ---")
print(repr(src[:1200]))
print(f"\n[function span char length = {len(src)}; tokenizer tokens follow]")
from transformers import RobertaTokenizer
tok = rd.tokenizer
print(f"function span token count = {len(tok.tokenize(src))}  (>256 => TRUNCATED)")
print("\n--- STATE VAR node spans (each encoded separately, format 'type name') ---")
# reconstruct merged contracts to get types
parsed = nhs.parse_contracts(open(rd.DAPPSCAN_ROOT / (item.get('file') or item.get('filePath'))).read())
# simpler: pull from detailed json record
det = json.load(open(PROJECT_ROOT / "experiments/results/dappscan_ast_detailed.json"))
rec = next((x for x in det if x.get("contract") == contract and x.get("ast_function") == fn), None)
print("state_vars_accessed:", item.get("state_vars_accessed"))
print("\n--- CALLEE node spans (each encoded separately, max_length=64) ---")
for ec in (item.get("external_calls") or []):
    print("  ", repr(ec.get("call_text")))
