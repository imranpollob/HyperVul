"""Task 9 — systemic is_cross_contract reliability. Recompute via the same AST method
(nhs.check_is_cross_contract) used for the ChainlinkPriceFeed case, compare to recorded.
Read-only."""
import json, sys
from pathlib import Path
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT)); sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
import run_diagnostics as rd

def reconstruct(item):
    contract = item["contract"]
    func_name = item.get("function") or item.get("ast_function")
    filepath = item.get("file") or item.get("filePath")
    source_type = item.get("source")
    if not source_type:
        source_type = "DAppSCAN" if ("dappscan" in str(filepath).lower() or "project_root" in item) else "FORGE"
    source_code, all_contracts = None, {}
    if source_type == "DAppSCAN":
        fp = rd.DAPPSCAN_ROOT / filepath
        if fp.exists():
            source_code = fp.read_text(encoding="utf-8", errors="ignore")
            all_contracts = rd.get_dappscan_project_contracts(filepath)
    else:
        vfp_id = item.get("vfp_id") or rd.find_forge_vfp_id(item)
        if vfp_id:
            fname = Path(item["file"]).name
            source_code = rd.vfp_data[vfp_id]["affected_files"].get(item["file"]) or rd.vfp_data[vfp_id]["affected_files"].get(fname)
            for fn, fc in rd.vfp_data[vfp_id]["affected_files"].items():
                all_contracts.update(nhs.parse_contracts(fc))
    if not source_code:
        return None
    parsed = nhs.parse_contracts(source_code)
    merged = dict(all_contracts); merged.update(parsed)
    funcs = nhs.resolve_all_functions(contract, merged)
    if func_name not in funcs:
        return None
    fnode = funcs[func_name]
    svtypes = nhs.resolve_all_state_var_types(contract, merged)
    locals_ = nhs.extract_local_vars(fnode)
    ext = nhs.find_external_calls_ast(fnode, svtypes, merged, allow_fallback=False)
    return nhs.check_is_cross_contract(ext, contract, svtypes, locals_, merged)

mismatches, checked, unresolved = [], 0, 0
for s in ["train", "val", "test"]:
    for item in json.load(open(PROJECT_ROOT / "data" / "splits" / f"{s}.json")):
        recorded = item.get("is_cross_contract")
        recon = reconstruct(item)
        if recon is None:
            unresolved += 1
            continue
        checked += 1
        if bool(recon) != bool(recorded):
            mismatches.append((s, item.get("contract"),
                               item.get("function") or item.get("ast_function"),
                               item.get("vfp_id") or item.get("project_root"),
                               recorded, recon, item.get("label")))

print(f"checked={checked}  unresolved(no src/func)={unresolved}  mismatches={len(mismatches)}")
print(f"disagreement rate (of checked) = {100*len(mismatches)/checked:.2f}%\n")
from collections import Counter
c = Counter((m[4], m[5]) for m in mismatches)
print("recorded -> reconstructed counts:", dict(c))
print("\n=== ALL MISMATCHES ===")
for s, ct, fn, src, rec, recon, lab in mismatches:
    print(f"[{s}] {ct}.{fn}  recorded={rec} recon={recon} label={lab}  src={src}")
