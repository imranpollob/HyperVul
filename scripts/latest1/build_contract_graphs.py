#!/usr/bin/env python3
"""Build shared contract-level graphs (Task 5 + Task 10).

One graph per (project, contract): all constructable interaction hyperedges (pos+neg)
+ 1-hop state-touching helper NODES + directed call edges + shared-data edges.

Structural emit only (no embeddings yet — encoded in a later training-prep pass).
Applies the Step-0 groundwork: scaffolding filter, Task-8 exclusions, project-level
split assignment (positives define split, so Box/vfp_00189 lands wholly in test).

Outputs: data/contract_graphs/{train,val,test}.json
"""
import json, sys, hashlib
from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations
sys.path.append(str(Path(__file__).resolve().parents[0]))
import negative_hyperedge_sampling as nhs
from negative_hyperedge_sampling import (
    parse_contracts, resolve_all_state_vars, resolve_all_state_var_types,
    resolve_all_functions, extract_local_vars, find_state_var_accesses,
    find_external_calls_ast, node_text, normalize_source, check_is_cross_contract,
    find_descendants_by_type, _unwrap_expression,
    DAPPSCAN_ROOT, SWC_SOURCE_DIR, FORGE_VULN_DIR,
)

ROOT = Path("/home/pollmix/Coding/HyperVul")
RES = ROOT / "experiments" / "results"
SCRATCH = ROOT / "scratch"
OUTDIR = ROOT / "data" / "contract_graphs"; OUTDIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- groundwork inputs
SCAFFOLD = set(c["contract"] for c in json.load(open(SCRATCH / "scaffold_candidates.json")))
TASK8_DROP = {("FlashLoans", "flashLoan"), ("OctoDistributor", "withdrawAllAgentTokens"),
              ("OctoDistributor", "transferHiringDistributions"), ("MainFeeDistributor", "swapLzToken")}

forge_pos = json.load(open(RES / "forge_ast_constructable_hyperedges.json"))
dapp_pos = json.load(open(RES / "dappscan_ast_constructable_hyperedges.json"))
pos_hashes = set(p["normalized_source_hash"] for p in (forge_pos + dapp_pos) if p.get("normalized_source_hash"))
def dfn(p): return p.get("function") or p.get("ast_function")
positive_key = set()
for p in forge_pos: positive_key.add((("FORGE", p["vfp_id"]), p["contract"], dfn(p)))
for p in dapp_pos: positive_key.add((("DAPP", p["project_root"]), p["contract"], dfn(p)))

# project -> split, from ORIGINAL splits' positives (label==1 carry vfp_id/project_root)
grp_split = {}
for s in ["train", "val", "test"]:
    for it in json.load(open(ROOT / "data" / "splits" / f"{s}.json")):
        if it.get("label") != 1: continue
        if it.get("vfp_id"): g = ("FORGE", it["vfp_id"])
        elif it.get("project_root"): g = ("DAPP", it["project_root"])
        else: continue
        # prefer test > val > train when a project spans splits (Box leakage -> test)
        prev = grp_split.get(g)
        rank = {"test": 3, "val": 2, "train": 1}
        if prev is None or rank[s] > rank[prev]: grp_split[g] = s

# exclusion sets (annotated vuln funcs that are not kept positives)
forge_excluded, dapp_excluded = set(), set()
for f in sorted(FORGE_VULN_DIR.glob("vfp_*.json")):
    v = json.load(open(f)); allc = {}
    for _, s in v.get("affected_files", {}).items():
        try: allc.update(parse_contracts(s))
        except Exception: pass
    for finding in v.get("findings", []):
        for loc in finding.get("location", []):
            if "::" in loc:
                parts = loc.split("::"); fb = Path(parts[0].strip()).name
                fnm = parts[1].strip().split("#")[0].strip()
                for cn, ci in allc.items():
                    if fnm in ci.functions: forge_excluded.add((f.stem, fb, cn, fnm)); break
for f in sorted(SWC_SOURCE_DIR.glob("**/*.json")):
    try:
        data = json.load(open(f)); fps = data.get("filePath", ""); fb = Path(fps).name
        ap = DAPPSCAN_ROOT / fps
        if not ap.exists(): continue
        fc = parse_contracts(ap.read_text(encoding="utf-8", errors="ignore"))
        for swc in data.get("SWCs", []):
            fn = swc.get("function", "")
            if fn and fn != "N/A":
                for cn in fc: dapp_excluded.add((fps, fb, cn, fn))
    except Exception: pass

# ---------------------------------------------------------------- helper detection
def one_hop_internal(fnode, funcs):
    out = set()
    for call in find_descendants_by_type(fnode, "call_expression"):
        callee = None
        for ch in call.children:
            if ch.type in ("expression", "identifier", "member_expression"):
                callee = _unwrap_expression(ch) if ch.type == "expression" else ch
                break
        if callee is not None and callee.type == "identifier":
            nm = node_text(callee)
            if nm in funcs: out.add(nm)
    return out

def callee_key(e): return (e.get("receiver") or "") + "." + (e.get("method") or "")

# ---------------------------------------------------------------- build per project
graphs = []   # one dict per (grp, contract)

def build_project(grp, project_contracts, file_of_contract, pos_files, excluded, is_forge):
    """project_contracts: {name: ContractInfo}; build graphs for each contract in it."""
    funcs_cache = {}
    def funcs_for(cn):
        if cn not in funcs_cache: funcs_cache[cn] = resolve_all_functions(cn, project_contracts)
        return funcs_cache[cn]
    for cn in project_contracts:
        if cn in SCAFFOLD: continue
        sv = resolve_all_state_vars(cn, project_contracts)
        svt = resolve_all_state_var_types(cn, project_contracts)
        funcs = funcs_for(cn)
        interactions, helper_meta = [], {}
        for fnm, fnode in funcs.items():
            lv = extract_local_vars(fnode)
            av = find_state_var_accesses(fnode, sv, lv)
            ec = find_external_calls_ast(fnode, svt, project_contracts, allow_fallback=False)
            if not (av and ec): continue
            k = (grp, cn, fnm)
            h = hashlib.sha256(normalize_source(node_text(fnode)).encode()).hexdigest()
            if k in positive_key:
                if (cn, fnm) in TASK8_DROP: continue   # Task-8 exclusion
                label, tier = 1, "POS"
            else:
                fb = file_of_contract.get(cn, "")
                if is_forge and (grp[1], fb, cn, fnm) in excluded: continue
                if (not is_forge) and any((rp, Path(rp).name, cn, fnm) in excluded for rp in [file_of_contract.get(cn, "")]):
                    continue
                if h in pos_hashes: continue
                label = 0
                tier = "A" if fb in pos_files else "B"
            interactions.append({
                "function": fnm, "label": label, "tier": tier,
                "is_cross_contract": check_is_cross_contract(ec, cn, svt, lv, project_contracts),
                "state_vars_accessed": av,
                "external_calls": [{"call_text": e["call_text"], "method": e["method"], "receiver": e["receiver"]} for e in ec],
                "function_source": node_text(fnode),
            })
        if not interactions: continue
        inter_fns = set(it["function"] for it in interactions)
        # nodes
        nodes, idx = [], {}
        for it in interactions:
            nid = f"i:{it['function']}"; idx[it["function"]] = nid
            nodes.append({"id": nid, "kind": "interaction", **it})
        # helpers + call edges
        edges = []
        for it in interactions:
            fnode = funcs[it["function"]]
            for h in one_hop_internal(fnode, funcs):
                if h == it["function"]: continue
                hnode = funcs[h]
                hlocals = extract_local_vars(hnode)
                hsv = find_state_var_accesses(hnode, sv, hlocals)
                if not hsv: continue                      # only state-touching callees
                if h in inter_fns:
                    dst = idx[h]                           # call edge between two interactions
                else:
                    if h not in helper_meta:
                        hid = f"h:{h}"; helper_meta[h] = hid
                        nodes.append({"id": hid, "kind": "helper", "function": h, "label": -1,
                                      "state_vars_accessed": hsv, "function_source": node_text(hnode)})
                    dst = helper_meta[h]
                edges.append({"src": idx[it["function"]], "dst": dst, "etype": "call", "direction": "forward"})
                edges.append({"src": dst, "dst": idx[it["function"]], "etype": "call", "direction": "reverse"})
        # shared-data edges among interactions
        for a, b in combinations(interactions, 2):
            sa, ca = set(a["state_vars_accessed"]), set(callee_key(e) for e in a["external_calls"])
            sb, cb = set(b["state_vars_accessed"]), set(callee_key(e) for e in b["external_calls"])
            if sa & sb:
                edges.append({"src": idx[a["function"]], "dst": idx[b["function"]], "etype": "shared_state", "direction": "undirected"})
            if ca & cb:
                edges.append({"src": idx[a["function"]], "dst": idx[b["function"]], "etype": "shared_callee", "direction": "undirected"})
        split = grp_split.get(grp)
        graphs.append({
            "graph_id": f"{grp[0]}::{grp[1]}::{cn}", "split": split,
            "source": grp[0], "project": grp[1], "contract": cn,
            "n_pos": sum(1 for it in interactions if it["label"] == 1),
            "n_neg": sum(1 for it in interactions if it["label"] == 0),
            "n_helper": len(helper_meta), "n_edges": len(edges),
            "nodes": nodes, "edges": edges,
        })

# FORGE
for vid in set(p["vfp_id"] for p in forge_pos):
    vf = FORGE_VULN_DIR / f"{vid}.json"
    if not vf.exists(): continue
    v = json.load(open(vf)); aff = v.get("affected_files", {})
    allc, file_of_contract = {}, {}
    for fn, s in aff.items():
        try:
            pp = parse_contracts(s)
            for cn in pp: file_of_contract[cn] = Path(fn).name
            allc.update(pp)
        except Exception: pass
    pos_files = set(Path(p["file"]).name for p in forge_pos if p["vfp_id"] == vid)
    build_project(("FORGE", vid), allc, file_of_contract, pos_files, forge_excluded, True)

# DAppSCAN
for pr in set(p["project_root"] for p in dapp_pos):
    proot = DAPPSCAN_ROOT / pr
    if not proot.exists(): continue
    projc, file_of_contract = {}, {}
    for sol in proot.glob("**/*.sol"):
        try:
            rp = str(sol.relative_to(DAPPSCAN_ROOT))
            pp = parse_contracts(sol.read_text(encoding="utf-8", errors="ignore"))
            for cn in pp: file_of_contract[cn] = rp
            projc.update(pp)
        except Exception: pass
    pos_files = set(Path(p["filePath"]).name for p in dapp_pos if p["project_root"] == pr)
    build_project(("DAPP", pr), projc, file_of_contract, pos_files, dapp_excluded, False)

# ---------------------------------------------------------------- emit + stats
by_split = defaultdict(list)
for g in graphs:
    by_split[g["split"] or "unassigned"].append(g)
for s, gl in by_split.items():
    json.dump(gl, open(OUTDIR / f"{s}.json", "w"))

tot_pos = sum(g["n_pos"] for g in graphs); tot_neg = sum(g["n_neg"] for g in graphs)
tot_help = sum(g["n_helper"] for g in graphs); tot_edge = sum(g["n_edges"] for g in graphs)
print(f"graphs={len(graphs)}  pos={tot_pos} neg={tot_neg} helpers={tot_help} edges={tot_edge}")
print(f"interaction class balance 1:{tot_neg/tot_pos:.1f}\n")
for s in ["train", "val", "test", "unassigned"]:
    gl = by_split.get(s, [])
    if not gl: continue
    p = sum(g["n_pos"] for g in gl); n = sum(g["n_neg"] for g in gl)
    print(f"[{s}] graphs={len(gl)} pos={p} neg={n} helpers={sum(g['n_helper'] for g in gl)} edges={sum(g['n_edges'] for g in gl)}")

withpos = [g for g in graphs if g["n_pos"] > 0]
allneg = [g for g in graphs if g["n_pos"] == 0]
def size(g): return g["n_pos"] + g["n_neg"]   # interaction count (helpers excluded)
an_single = [g for g in allneg if size(g) == 1]
an_multi = [g for g in allneg if size(g) >= 2]
wp_single = [g for g in withpos if size(g) == 1]
wp_multi = [g for g in withpos if size(g) >= 2]
print("\n=== SINGLETON vs MULTI breakdown ===")
print(f"all-negative graphs: {len(allneg)}  singleton(1 interaction)={len(an_single)} ({100*len(an_single)/len(allneg):.0f}%)  multi(>=2)={len(an_multi)}")
print(f"with-positive graphs: {len(withpos)}  singleton={len(wp_single)}  multi(>=2)={len(wp_multi)}")
print(f"  -> singleton all-negative graphs have NO shared-data edges to propagate over.")
json.dump({"graphs": len(graphs), "pos": tot_pos, "neg": tot_neg, "helpers": tot_help, "edges": tot_edge,
           "allneg": len(allneg), "allneg_singleton": len(an_single), "allneg_multi": len(an_multi),
           "withpos": len(withpos)}, open(SCRATCH / "graph_build_stats.json", "w"), indent=1)
