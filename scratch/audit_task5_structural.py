"""Read-only structural check (Task 5 CORE): for each test reentrancy positive,
does the flagged function delegate to an internal helper, and can the current/planned
hyperedge construction structurally connect caller and helper? No model/label/split edits."""
import json, sys
from pathlib import Path
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT)); sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
import run_diagnostics as rd   # reuses vfp_data + dappscan loaders (main is guarded)


def load_context(item):
    """Return (merged_contracts, contract, func_node) or None."""
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
    return merged, contract, funcs[func_name]


def internal_helper_calls(func_node, contract, merged):
    """Bare-identifier calls inside func that resolve to a function in the same contract."""
    funcs = nhs.resolve_all_functions(contract, merged)
    helpers = set()
    for call in nhs.find_descendants_by_type(func_node, "call_expression"):
        # first child is the callee expression
        callee = None
        for ch in call.children:
            if ch.type in ("expression", "identifier", "member_expression"):
                callee = nhs._unwrap_expression(ch) if ch.type == "expression" else ch
                break
        if callee is not None and callee.type == "identifier":
            name = nhs.node_text(callee)
            if name in funcs and name != (nhs.node_text(func_node.child_by_field_name("name")) if func_node.child_by_field_name("name") else None):
                helpers.add(name)
    return helpers, funcs


def edge_of(func_node, contract, merged):
    svars = nhs.resolve_all_state_vars(contract, merged)
    svtypes = nhs.resolve_all_state_var_types(contract, merged)
    locals_ = nhs.extract_local_vars(func_node)
    accessed = set(nhs.find_state_var_accesses(func_node, svars, locals_))
    ext = nhs.find_external_calls_ast(func_node, svtypes, merged, allow_fallback=False)
    callees = set(e["method"] + "@" + (e["receiver"] or "") for e in ext)
    return accessed, callees, len(ext) > 0


with open(PROJECT_ROOT / "data" / "splits" / "test_features.json") as f:
    test = json.load(f)

def is_reent(it):
    s = (it.get("vtype") or it.get("category") or it.get("swc_code") or "").lower()
    return "reentran" in s or "107" in s

reent = [it for it in test if it["label"] == 1 and is_reent(it)]
print(f"Reentrancy positives: {len(reent)}\n")

indirect = []
for it in reent:
    ctx = load_context(it)
    fn = it.get("function") or it.get("ast_function")
    if ctx is None:
        print(f"[no-src] {it.get('contract')}.{fn}")
        continue
    merged, contract, fnode = ctx
    helpers, funcs = internal_helper_calls(fnode, contract, merged)
    if not helpers:
        continue
    caller_sv, caller_callees, caller_has_ext = edge_of(fnode, contract, merged)
    # examine each helper
    for h in helpers:
        h_sv, h_callees, h_has_ext = edge_of(funcs[h], contract, merged)
        h_writes_state = len(h_sv) > 0
        shares = (caller_sv & h_sv) or (caller_callees & h_callees)
        helper_constructable = (len(h_sv) > 0 and h_has_ext)
        if h_writes_state:  # only interesting if helper touches state
            indirect.append({
                "contract": contract, "func": fn, "helper": h,
                "vfp_id": it.get("vfp_id"), "project_root": it.get("project_root"),
                "file": it.get("file") or it.get("filePath"),
                "caller_sv": sorted(caller_sv), "helper_sv": sorted(h_sv),
                "caller_callees": sorted(caller_callees), "helper_callees": sorted(h_callees),
                "helper_has_ext_call": h_has_ext,
                "helper_constructable": helper_constructable,
                "share_node": bool(shares),
            })

print(f"=== Reentrancy positives that call a state-touching internal helper: {len(indirect)} ===")
for d in indirect:
    print(f"\n- {d['contract']}.{d['func']}  -->  helper {d['helper']}()")
    print(f"  vfp_id={d['vfp_id']} project_root={d['project_root']}")
    print(f"  caller state={d['caller_sv']}  caller callees={d['caller_callees']}")
    print(f"  helper state={d['helper_sv']}  helper callees={d['helper_callees']}")
    print(f"  helper has external call? {d['helper_has_ext_call']}   helper constructable (own hyperedge exists)? {d['helper_constructable']}")
    print(f"  caller & helper SHARE A NODE? {d['share_node']}")
