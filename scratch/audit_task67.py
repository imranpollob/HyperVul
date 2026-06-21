"""Tasks 6 & 7 — hyperedge overlap rate and size distribution, by split. Read-only."""
import json, statistics
from pathlib import Path
from itertools import combinations
SP = Path("/home/pollmix/Coding/HyperVul/data/splits")
RES = Path("/home/pollmix/Coding/HyperVul/experiments/results")

# ---- build group -> split membership from the splits ----
def group_key(it):
    if it.get("vfp_id"):
        return ("FORGE", it["vfp_id"], it["contract"])
    pr = it.get("project_root")
    if pr:
        return ("DAPP", pr, it["contract"])
    # old-format dappscan positives carry project_root; negatives carry source/file
    return None

split_of = {}
for s in ["train", "val", "test"]:
    for it in json.load(open(SP / f"{s}.json")):
        g = group_key(it)
        if g:
            split_of[g] = s

def detail_group(x, src):
    if src == "FORGE":
        return ("FORGE", x.get("vfp_id"), x.get("contract"))
    return ("DAPP", x.get("project_root"), x.get("contract"))

def callee_key(ec):
    return (ec.get("receiver") or "") + "." + (ec.get("method") or "")

def nodes_of(x):
    sv = set(x.get("state_vars_accessed") or [])
    cl = set(callee_key(e) for e in (x.get("external_calls") or []))
    return sv, cl

# ---- load constructable interactions, attach split ----
groups = {}   # group -> list of interactions
for f, src in [("forge_ast_hyperedge_detailed.json", "FORGE"), ("dappscan_ast_detailed.json", "DAPP")]:
    for x in json.load(open(RES / f)):
        if not x.get("constructable"):
            continue
        g = detail_group(x, src)
        groups.setdefault(g, []).append(x)

def split_for_group(g):
    return split_of.get(g, "unassigned")

# ============ TASK 6: OVERLAP ============
print("=" * 60); print("TASK 6 — HYPEREDGE OVERLAP (multi-interaction contracts)"); print("=" * 60)
by_split = {}
for g, items in groups.items():
    if len(items) < 2:
        continue
    sp = split_for_group(g)
    pairs = list(combinations(items, 2))
    overlap_pairs = 0
    for a, b in pairs:
        sva, cla = nodes_of(a); svb, clb = nodes_of(b)
        if (sva & svb) or (cla & clb):
            overlap_pairs += 1
    rec = by_split.setdefault(sp, {"multi_contracts": 0, "contracts_with_overlap": 0, "total_pairs": 0, "overlap_pairs": 0})
    rec["multi_contracts"] += 1
    rec["total_pairs"] += len(pairs)
    rec["overlap_pairs"] += overlap_pairs
    if overlap_pairs > 0:
        rec["contracts_with_overlap"] += 1

allrec = {"multi_contracts": 0, "contracts_with_overlap": 0, "total_pairs": 0, "overlap_pairs": 0}
for sp in ["train", "val", "test", "unassigned"]:
    if sp not in by_split: continue
    r = by_split[sp]
    for k in allrec: allrec[k] += r[k]
    co = 100*r["contracts_with_overlap"]/r["multi_contracts"] if r["multi_contracts"] else 0
    po = 100*r["overlap_pairs"]/r["total_pairs"] if r["total_pairs"] else 0
    print(f"\n[{sp}] multi-interaction contracts={r['multi_contracts']}")
    print(f"   contracts with >=1 overlapping pair: {r['contracts_with_overlap']} ({co:.1f}%)")
    print(f"   overlapping pairs: {r['overlap_pairs']}/{r['total_pairs']} ({po:.1f}%)")
co = 100*allrec["contracts_with_overlap"]/allrec["multi_contracts"]
po = 100*allrec["overlap_pairs"]/allrec["total_pairs"]
print(f"\n[ALL] multi-interaction contracts={allrec['multi_contracts']}")
print(f"   contracts with overlap: {allrec['contracts_with_overlap']} ({co:.1f}%)")
print(f"   overlapping pairs: {allrec['overlap_pairs']}/{allrec['total_pairs']} ({po:.1f}%)")

# ============ TASK 7: SIZE DISTRIBUTION ============
print("\n" + "=" * 60); print("TASK 7 — HYPEREDGE SIZE DISTRIBUTION"); print("=" * 60)
def dist(name, vals):
    vals = sorted(vals)
    print(f"  {name:18s} n={len(vals):3d} min={min(vals)} median={statistics.median(vals):.1f} mean={statistics.mean(vals):.2f} max={max(vals)} p90={vals[int(0.9*len(vals))-1] if vals else 0}")

size_by_split = {}
for g, items in groups.items():
    sp = split_for_group(g)
    for x in items:
        sv = len(set(x.get("state_vars_accessed") or []))
        cl = len(set(callee_key(e) for e in (x.get("external_calls") or [])))
        size_by_split.setdefault(sp, []).append((sv, cl))

allv = []
for sp in ["train", "val", "test", "unassigned"]:
    if sp not in size_by_split: continue
    v = size_by_split[sp]; allv += v
    print(f"\n[{sp}]  ({len(v)} interactions)")
    dist("state_vars", [a for a, _ in v])
    dist("ext_calls", [b for _, b in v])
    dist("combined", [a + b for a, b in v])
print(f"\n[ALL]  ({len(allv)} interactions)")
dist("state_vars", [a for a, _ in allv])
dist("ext_calls", [b for _, b in allv])
dist("combined", [a + b for a, b in allv])
