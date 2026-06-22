"""Task 5 measurement — scale of adding 1-hop state-touching helper nodes + call edges.
Read-only. For every constructable interaction in the splits, find direct internal/private
calls to state-reading/writing functions; classify each callee as an EXISTING interaction
(call edge only) or a NEW helper node. Dedup helper nodes per (project,contract)."""
import json, sys, statistics
from pathlib import Path
from collections import defaultdict
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
SPLITS_DIR = PROJECT_ROOT / (sys.argv[1] if len(sys.argv) > 1 else "data/splits")
sys.path.append(str(PROJECT_ROOT)); sys.path.append(str(PROJECT_ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
import run_diagnostics as rd

def project_key(it):
    if it.get("vfp_id"): return ("FORGE", it["vfp_id"])
    if it.get("project_root"): return ("DAPP", it["project_root"])
    fp = str(it.get("file") or it.get("filePath") or "")
    parts = Path(fp).parts
    if "DAppSCAN-source" in parts:
        i = parts.index("DAppSCAN-source")
        return ("DAPP", "/".join(parts[i:i+3]))
    return ("FORGE", Path(fp).name)

def load_ctx(it):
    contract = it["contract"]; fn = it.get("function") or it.get("ast_function")
    fp = it.get("file") or it.get("filePath"); st = it.get("source")
    if not st: st = "DAppSCAN" if ("dappscan" in str(fp).lower() or "project_root" in it) else "FORGE"
    src, allc = None, {}
    if st == "DAppSCAN":
        f = rd.DAPPSCAN_ROOT / fp
        if f.exists(): src = f.read_text(encoding="utf-8", errors="ignore"); allc = rd.get_dappscan_project_contracts(fp)
    else:
        vid = it.get("vfp_id") or rd.find_forge_vfp_id(it)
        if vid and vid in rd.vfp_data:
            nm = Path(it["file"]).name
            src = rd.vfp_data[vid]["affected_files"].get(it["file"]) or rd.vfp_data[vid]["affected_files"].get(nm)
            for _, fc in rd.vfp_data[vid]["affected_files"].items(): allc.update(nhs.parse_contracts(fc))
    if not src: return None
    parsed = nhs.parse_contracts(src); merged = dict(allc); merged.update(parsed)
    funcs = nhs.resolve_all_functions(contract, merged)
    if fn not in funcs: return None
    return merged, contract, fn, funcs

def one_hop_internal(fnode, contract, funcs):
    out = set()
    for call in nhs.find_descendants_by_type(fnode, "call_expression"):
        callee = None
        for ch in call.children:
            if ch.type in ("expression", "identifier", "member_expression"):
                callee = nhs._unwrap_expression(ch) if ch.type == "expression" else ch
                break
        if callee is not None and callee.type == "identifier":
            nm = nhs.node_text(callee)
            if nm in funcs: out.add(nm)
    return out

# build set of (project_key, contract, function) that ARE interactions in the splits
interaction_set = set()
items_by = []
for s in ["train", "val", "test"]:
    for it in json.load(open(SPLITS_DIR / f"{s}.json")):
        fn = it.get("function") or it.get("ast_function")
        interaction_set.add((project_key(it), it["contract"], fn))
        it["_split"] = s; items_by.append(it)

# per (project,contract) accumulation
helper_nodes = defaultdict(set)     # (pk,contract) -> set(helper_func)  NEW nodes only
call_edges = defaultdict(int)       # (pk,contract) -> count of caller->state-helper edges
edges_to_existing = defaultdict(int)
contract_split = {}
processed, noctx = 0, 0
for it in items_by:
    ctx = load_ctx(it)
    pk = project_key(it); contract = it["contract"]
    contract_split[(pk, contract)] = it["_split"]
    if ctx is None:
        noctx += 1; continue
    merged, contract, fn, funcs = ctx
    svars = nhs.resolve_all_state_vars(contract, merged)
    processed += 1
    for h in one_hop_internal(funcs[fn], contract, funcs):
        if h == fn: continue
        hnode = funcs[h]
        hlocals = nhs.extract_local_vars(hnode)
        if len(nhs.find_state_var_accesses(hnode, svars, hlocals)) == 0:
            continue  # only state-touching callees matter
        call_edges[(pk, contract)] += 1
        if (pk, contract, h) in interaction_set:
            edges_to_existing[(pk, contract)] += 1
        else:
            helper_nodes[(pk, contract)].add(h)

print(f"processed interactions={processed}  no-context={noctx}")
all_contracts = set(contract_split)
print(f"distinct (project,contract) graphs touched: {len(all_contracts)}\n")

def by_split(split):
    keys = [k for k in all_contracts if contract_split[k] == split]
    hn = [len(helper_nodes[k]) for k in keys]
    ce = [call_edges[k] for k in keys]
    tot_helpers = sum(hn); tot_edges = sum(ce)
    tot_existing = sum(edges_to_existing[k] for k in keys)
    print(f"[{split}] contracts={len(keys)}")
    print(f"   NEW helper nodes: total={tot_helpers}  per-contract median={statistics.median(hn) if hn else 0} mean={statistics.mean(hn) if hn else 0:.2f} max={max(hn) if hn else 0}")
    print(f"   call-graph edges (caller->state-helper): total={tot_edges}  ({tot_existing} to existing interactions, {tot_edges-tot_existing} to new helpers)")
    print(f"   contracts gaining >=1 helper node: {sum(1 for x in hn if x>0)} ({100*sum(1 for x in hn if x>0)/len(keys) if keys else 0:.0f}%)")
    return tot_helpers, tot_edges

th=te=0
for s in ["train","val","test"]:
    a,b=by_split(s); th+=a; te+=b
print(f"\n[ALL] total NEW helper nodes={th}  total call edges={te}")
