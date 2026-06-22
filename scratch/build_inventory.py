"""Groundwork: enumerate the full constructable interaction set (pos+neg) per
(project,contract), save to scratch/inventory.json for reuse by both builds, and
emit scaffolding-filter CANDIDATES for human review. Read-only w.r.t. pipeline."""
import json, sys, hashlib, re
from pathlib import Path
from collections import defaultdict
sys.path.append(str(Path("/home/pollmix/Coding/HyperVul/scripts")))
import negative_hyperedge_sampling as nhs
from negative_hyperedge_sampling import (
    parse_contracts, resolve_all_state_vars, resolve_all_state_var_types,
    resolve_all_functions, extract_local_vars, find_state_var_accesses,
    find_external_calls_ast, node_text, normalize_source, check_is_cross_contract,
    DAPPSCAN_ROOT, SWC_SOURCE_DIR, FORGE_VULN_DIR,
)
RES = Path("/home/pollmix/Coding/HyperVul/experiments/results")
OUT = Path("/home/pollmix/Coding/HyperVul/scratch")

forge_pos = json.load(open(RES / "forge_ast_constructable_hyperedges.json"))
dapp_pos = json.load(open(RES / "dappscan_ast_constructable_hyperedges.json"))
pos_hashes = set(p["normalized_source_hash"] for p in (forge_pos + dapp_pos) if p.get("normalized_source_hash"))

def dfn(p): return p.get("function") or p.get("ast_function")
positive_key = set()
pos_meta = {}
for p in forge_pos:
    k = (("FORGE", p["vfp_id"]), p["contract"], dfn(p)); positive_key.add(k)
    pos_meta[k] = {"finding_title": p.get("finding_title")}
for p in dapp_pos:
    k = (("DAPP", p["project_root"]), p["contract"], dfn(p)); positive_key.add(k)
    pos_meta[k] = {"category": p.get("category")}

# exclusion sets (annotated vuln funcs)
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

records = []   # one per interaction node
def add(grp, contract, function, label, tier, av, ec, is_cross, h):
    records.append({"grp": list(grp), "contract": contract, "function": function,
                    "label": label, "tier": tier, "is_cross_contract": is_cross,
                    "state_vars_accessed": av,
                    "external_calls": [{"call_text": e["call_text"], "method": e["method"],
                                        "receiver": e["receiver"]} for e in ec],
                    "hash": h})

# FORGE projects
for vid in set(p["vfp_id"] for p in forge_pos):
    vf = FORGE_VULN_DIR / f"{vid}.json"
    if not vf.exists(): continue
    v = json.load(open(vf)); aff = v.get("affected_files", {})
    allc, filec = {}, {}
    for fn, s in aff.items():
        try: pp = parse_contracts(s); filec[fn] = pp; allc.update(pp)
        except Exception: pass
    vfp_pos_files = set(Path(p["file"]).name for p in forge_pos if p["vfp_id"] == vid)
    for fn, s in aff.items():
        fb = Path(fn).name
        for cn in filec.get(fn, {}):
            sv = resolve_all_state_vars(cn, allc); svt = resolve_all_state_var_types(cn, allc)
            for fnname, fnode in resolve_all_functions(cn, allc).items():
                lv = extract_local_vars(fnode)
                av = find_state_var_accesses(fnode, sv, lv)
                ec = find_external_calls_ast(fnode, svt, allc, allow_fallback=False)
                if not (av and ec): continue
                h = hashlib.sha256(normalize_source(node_text(fnode)).encode()).hexdigest()
                k = (("FORGE", vid), cn, fnname)
                if k in positive_key:
                    add(("FORGE", vid), cn, fnname, 1, "POS", av, ec,
                        check_is_cross_contract(ec, cn, svt, lv, allc), h)
                elif (vid, fb, cn, fnname) in forge_excluded:
                    continue  # annotated vuln but not a kept positive
                elif h in pos_hashes:
                    continue
                else:
                    add(("FORGE", vid), cn, fnname, 0, "A" if fb in vfp_pos_files else "B",
                        av, ec, check_is_cross_contract(ec, cn, svt, lv, allc), h)

# DAppSCAN projects
for pr in set(p["project_root"] for p in dapp_pos):
    proot = DAPPSCAN_ROOT / pr
    if not proot.exists(): continue
    proj_pos_files = set(Path(p["filePath"]).name for p in dapp_pos if p["project_root"] == pr)
    projc, filec = {}, {}
    for sol in proot.glob("**/*.sol"):
        try:
            rp = str(sol.relative_to(DAPPSCAN_ROOT)); s = sol.read_text(encoding="utf-8", errors="ignore")
            pp = parse_contracts(s); filec[rp] = pp; projc.update(pp)
        except Exception: pass
    for rp, contracts in filec.items():
        fb = Path(rp).name
        for cn in contracts:
            sv = resolve_all_state_vars(cn, projc); svt = resolve_all_state_var_types(cn, projc)
            for fnname, fnode in resolve_all_functions(cn, projc).items():
                lv = extract_local_vars(fnode)
                av = find_state_var_accesses(fnode, sv, lv)
                ec = find_external_calls_ast(fnode, svt, projc, allow_fallback=False)
                if not (av and ec): continue
                h = hashlib.sha256(normalize_source(node_text(fnode)).encode()).hexdigest()
                k = (("DAPP", pr), cn, fnname)
                if k in positive_key:
                    add(("DAPP", pr), cn, fnname, 1, "POS", av, ec,
                        check_is_cross_contract(ec, cn, svt, lv, projc), h)
                elif (rp, fb, cn, fnname) in dapp_excluded:
                    continue
                elif h in pos_hashes:
                    continue
                else:
                    add(("DAPP", pr), cn, fnname, 0, "A" if fb in proj_pos_files else "B",
                        av, ec, check_is_cross_contract(ec, cn, svt, lv, projc), h)

# dedup negatives by (contract, function, hash); keep all positives
seen, uniq = set(), []
for r in records:
    if r["label"] == 0:
        k = (r["contract"], r["function"], r["hash"])
        if k in seen: continue
        seen.add(k)
    uniq.append(r)

json.dump(uniq, open(OUT / "inventory.json", "w"))
npos = sum(1 for r in uniq if r["label"] == 1); nneg = len(uniq) - npos
print(f"saved inventory.json: {len(uniq)} interactions  pos={npos} neg={nneg}  ratio 1:{nneg/npos:.1f}")

# ---- scaffolding CANDIDATES ----
SCAFFOLD_RE = [
    (re.compile(r"Test$"), "endswith Test"), (re.compile(r"Tester$"), "endswith Tester"),
    (re.compile(r"Mock"), "contains Mock"), (re.compile(r"^Mock"), "startswith Mock"),
    (re.compile(r"Harness$"), "endswith Harness"), (re.compile(r"Fixture$"), "endswith Fixture"),
    (re.compile(r"Stub$"), "endswith Stub"), (re.compile(r"^console2?$"), "console"),
    (re.compile(r"Fake"), "contains Fake"), (re.compile(r"Example$"), "endswith Example"),
    (re.compile(r"^DSTest"), "DSTest"), (re.compile(r"^Vm$"), "Vm cheatcode"),
]
contract_counts = defaultdict(lambda: [0, 0])  # contract -> [interactions, positives]
for r in uniq:
    contract_counts[r["contract"]][0] += 1
    contract_counts[r["contract"]][1] += r["label"]
cands = []
for cn, (cnt, pcnt) in contract_counts.items():
    for rx, why in SCAFFOLD_RE:
        if rx.search(cn):
            cands.append((cn, cnt, pcnt, why)); break
cands.sort(key=lambda x: -x[1])
json.dump([{"contract": c, "interactions": n, "positives": p, "rule": w} for c, n, p, w in cands],
          open(OUT / "scaffold_candidates.json", "w"), indent=1)
print(f"\n=== SCAFFOLDING CANDIDATES ({len(cands)} contracts, {sum(c[1] for c in cands)} interactions) ===")
print(f"{'contract':36s} {'#int':>5s} {'#pos':>5s}  rule")
for c, n, p, w in cands:
    flag = "  <-- HAS POSITIVE!" if p > 0 else ""
    print(f"{c:36s} {n:5d} {p:5d}  {w}{flag}")
