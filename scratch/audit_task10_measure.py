"""Task 10 measurement — regenerate the FULL constructable interaction set per contract
(all positives + all ~12k codebase negatives incl. zero-positive contracts) to measure
real class balance and contract-graph size distribution. Read-only; writes nothing to the
pipeline. Validates against known totals (12,098 / Tier-A 1,389 / Tier-B 10,709)."""
import json, sys, hashlib, statistics
from pathlib import Path
from collections import defaultdict, Counter
sys.path.append(str(Path("/home/pollmix/Coding/HyperVul/scripts")))
import negative_hyperedge_sampling as nhs
from negative_hyperedge_sampling import (
    parse_contracts, resolve_all_state_vars, resolve_all_state_var_types,
    resolve_all_functions, extract_local_vars, find_state_var_accesses,
    find_external_calls_ast, node_text, normalize_source, check_is_cross_contract,
    DAPPSCAN_ROOT, SWC_SOURCE_DIR, FORGE_VULN_DIR,
)

RES = Path("/home/pollmix/Coding/HyperVul/experiments/results")
forge_pos = json.load(open(RES / "forge_ast_constructable_hyperedges.json"))
dapp_pos = json.load(open(RES / "dappscan_ast_constructable_hyperedges.json"))
pos_hashes = set(p["normalized_source_hash"] for p in (forge_pos + dapp_pos) if p.get("normalized_source_hash"))

# ---- build exclusion sets (annotated vulnerable funcs) ----
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
                fnname = parts[1].strip().split("#")[0].strip()
                for cn, ci in allc.items():
                    if fnname in ci.functions:
                        forge_excluded.add((f.stem, fb, cn, fnname)); break
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

# ---- enumerate codebase negatives (faithful to nhs.run, minus near-dup) ----
negs = []
pos_vfps = set(p["vfp_id"] for p in forge_pos)
for vid in pos_vfps:
    vf = FORGE_VULN_DIR / f"{vid}.json"
    if not vf.exists(): continue
    v = json.load(open(vf)); aff = v.get("affected_files", {})
    allc, filec = {}, {}
    for fn, s in aff.items():
        try: p = parse_contracts(s); filec[fn] = p; allc.update(p)
        except Exception: pass
    vfp_pos_files = set(Path(p["file"]).name for p in forge_pos if p["vfp_id"] == vid)
    for fn, s in aff.items():
        fb = Path(fn).name
        for cn, ci in filec.get(fn, {}).items():
            sv = resolve_all_state_vars(cn, allc); svt = resolve_all_state_var_types(cn, allc)
            for fnname, fnode in resolve_all_functions(cn, allc).items():
                if (vid, fb, cn, fnname) in forge_excluded: continue
                lv = extract_local_vars(fnode)
                av = find_state_var_accesses(fnode, sv, lv)
                ec = find_external_calls_ast(fnode, svt, allc, allow_fallback=False)
                if av and ec:
                    h = hashlib.sha256(normalize_source(node_text(fnode)).encode()).hexdigest()
                    if h in pos_hashes: continue
                    negs.append({"grp": ("FORGE", vid), "contract": cn, "function": fnname,
                                 "tier": "A" if fb in vfp_pos_files else "B", "hash": h})

pos_dapp_roots = set(p["project_root"] for p in dapp_pos)
for pr in pos_dapp_roots:
    proot = DAPPSCAN_ROOT / pr
    if not proot.exists(): continue
    proj_pos_files = set(Path(p["filePath"]).name for p in dapp_pos if p["project_root"] == pr)
    projc, filec = {}, {}
    for sol in proot.glob("**/*.sol"):
        try:
            rp = str(sol.relative_to(DAPPSCAN_ROOT)); s = sol.read_text(encoding="utf-8", errors="ignore")
            p = parse_contracts(s); filec[rp] = p; projc.update(p)
        except Exception: pass
    for rp, contracts in filec.items():
        fb = Path(rp).name
        for cn, ci in contracts.items():
            sv = resolve_all_state_vars(cn, projc); svt = resolve_all_state_var_types(cn, projc)
            for fnname, fnode in resolve_all_functions(cn, projc).items():
                if (rp, fb, cn, fnname) in dapp_excluded: continue
                lv = extract_local_vars(fnode)
                av = find_state_var_accesses(fnode, sv, lv)
                ec = find_external_calls_ast(fnode, svt, projc, allow_fallback=False)
                if av and ec:
                    h = hashlib.sha256(normalize_source(node_text(fnode)).encode()).hexdigest()
                    if h in pos_hashes: continue
                    negs.append({"grp": ("DAPP", pr), "contract": cn, "function": fnname,
                                 "tier": "A" if fb in proj_pos_files else "B", "hash": h})

# dedup negatives
seen, uneg = set(), []
for n in negs:
    k = (n["contract"], n["function"], n["hash"])
    if k not in seen: seen.add(k); uneg.append(n)

ta = sum(1 for n in uneg if n["tier"] == "A"); tb = sum(1 for n in uneg if n["tier"] == "B")
print("=== VALIDATION (target 12,098 / A 1,389 / B 10,709; near-dup not applied here) ===")
print(f"  unique codebase negatives = {len(uneg)}  Tier A={ta}  Tier B={tb}\n")

# ---- group ALL interactions per (group, contract) ----
graph = defaultdict(lambda: {"pos": 0, "neg": 0})
for p in forge_pos: graph[(("FORGE", p["vfp_id"]), p["contract"])]["pos"] += 1
for p in dapp_pos: graph[(("DAPP", p["project_root"]), p["contract"])]["pos"] += 1
for n in uneg: graph[(n["grp"], n["contract"])]["neg"] += 1

tot_pos = sum(g["pos"] for g in graph.values()); tot_neg = sum(g["neg"] for g in graph.values())
sizes = [g["pos"] + g["neg"] for g in graph.values()]
allneg = [k for k, g in graph.items() if g["pos"] == 0]
withpos = [k for k, g in graph.items() if g["pos"] > 0]

print("=== TASK 10 — FULL CONTRACT-GRAPH MEASUREMENT ===")
print(f"  total constructable interactions: pos={tot_pos}  neg={tot_neg}  ratio = 1:{tot_neg/tot_pos:.1f}")
print(f"  (current sampled training uses ~930 neg @ 3:1; full pool is {tot_neg})")
print(f"\n  contract-graphs total: {len(graph)}")
print(f"    with >=1 positive: {len(withpos)}")
print(f"    ALL-negative (zero positive): {len(allneg)}  ({100*len(allneg)/len(graph):.0f}%)")
print(f"\n  interactions per contract-graph: min={min(sizes)} median={statistics.median(sizes)} mean={statistics.mean(sizes):.1f} max={max(sizes)} p90={sorted(sizes)[int(0.9*len(sizes))-1]}")
wp_sizes = [graph[k]["pos"] + graph[k]["neg"] for k in withpos]
an_sizes = [graph[k]["neg"] for k in allneg]
print(f"    among with-positive graphs:  median={statistics.median(wp_sizes)} mean={statistics.mean(wp_sizes):.1f} max={max(wp_sizes)}")
print(f"    among all-negative graphs:   median={statistics.median(an_sizes)} mean={statistics.mean(an_sizes):.1f} max={max(an_sizes)}")
big = sorted(graph.items(), key=lambda kv: kv[1]["pos"]+kv[1]["neg"], reverse=True)[:8]
print("\n  largest contract-graphs:")
for k, g in big:
    print(f"    {k[1]:32s} pos={g['pos']:3d} neg={g['neg']:3d}  ({k[0][0]})")
