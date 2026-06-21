#!/usr/bin/env python3
"""Cross-split duplicate-source dedup for contract graphs (priority test>val>train).

Each unique normalized interaction-source is OWNED by its highest-priority split; its
instances in lower-priority splits are removed (with their edges). Positives are never
removed (guard). Orphaned helper nodes are pruned. The 6 unassigned graphs default to train.
Backs up the pre-dedup graphs to scratch/contract_graphs_prededup/.
"""
import json, sys, hashlib, shutil
from pathlib import Path
from collections import defaultdict
sys.path.append(str(Path(__file__).resolve().parents[0]))
import negative_hyperedge_sampling as nhs

GDIR = Path("/home/pollmix/Coding/HyperVul/data/contract_graphs")
BK = Path("/home/pollmix/Coding/HyperVul/scratch/contract_graphs_prededup"); BK.mkdir(parents=True, exist_ok=True)
PRIO = {"test": 3, "val": 2, "train": 1}

def nhash(src): return hashlib.sha256(nhs.normalize_source(src).encode()).hexdigest()

# load (fold unassigned -> train)
graphs = {"train": [], "val": [], "test": []}
for f in GDIR.glob("*.json"):
    shutil.copy(f, BK / f.name)
    data = json.load(open(f))
    s = f.stem if f.stem in graphs else "train"
    for g in data:
        g["split"] = s if g.get("split") in (None, "unassigned") else g["split"]
        graphs[g["split"]].append(g)

# 1) owner split per interaction source-hash
hash_splits = defaultdict(set)       # hash -> set(splits)
hash_split_count = defaultdict(lambda: defaultdict(int))  # hash -> split -> #instances
for s in graphs:
    for g in graphs[s]:
        for n in g["nodes"]:
            if n["kind"] == "interaction":
                h = nhash(n["function_source"])
                hash_splits[h].add(s); hash_split_count[h][s] += 1
cross = {h: ss for h, ss in hash_splits.items() if len(ss) > 1}
owner = {h: max(ss, key=lambda x: PRIO[x]) for h, ss in cross.items()}

# 2) remove non-owner instances (negatives only); prune edges + orphan helpers
removed = defaultdict(int)
for s in graphs:
    for g in graphs[s]:
        keep_ids, drop_ids = set(), set()
        new_nodes = []
        for n in g["nodes"]:
            if n["kind"] == "interaction":
                h = nhash(n["function_source"])
                if h in owner and owner[h] != s and n["label"] == 0:
                    drop_ids.add(n["id"]); removed[s] += 1; continue
            new_nodes.append(n); keep_ids.add(n["id"])
        # prune edges touching dropped nodes
        new_edges = [e for e in g["edges"] if e["src"] in keep_ids and e["dst"] in keep_ids]
        # prune orphan helpers (no remaining edge)
        deg = defaultdict(int)
        for e in new_edges: deg[e["src"]] += 1; deg[e["dst"]] += 1
        final_nodes = [n for n in new_nodes if not (n["kind"] == "helper" and deg[n["id"]] == 0)]
        fids = set(n["id"] for n in final_nodes)
        final_edges = [e for e in new_edges if e["src"] in fids and e["dst"] in fids]
        g["nodes"] = final_nodes; g["edges"] = final_edges
        g["n_pos"] = sum(1 for n in final_nodes if n.get("kind") == "interaction" and n["label"] == 1)
        g["n_neg"] = sum(1 for n in final_nodes if n.get("kind") == "interaction" and n["label"] == 0)
        g["n_helper"] = sum(1 for n in final_nodes if n["kind"] == "helper")
        g["n_edges"] = len(final_edges)

# 3) drop graphs with no interactions left
for s in graphs:
    graphs[s] = [g for g in graphs[s] if (g["n_pos"] + g["n_neg"]) > 0]
    json.dump(graphs[s], open(GDIR / f"{s}.json", "w"))
# remove stale unassigned file
(GDIR / "unassigned.json").unlink(missing_ok=True)

# ---- report ----
def negs(s): return sum(g["n_neg"] for g in graphs[s])
def poss(s): return sum(g["n_pos"] for g in graphs[s])
print("=== POST-DEDUP per-split counts ===")
for s in ["train", "val", "test"]:
    print(f"  {s:5s}: pos={poss(s)} neg={negs(s)} graphs={len(graphs[s])}  (removed {removed[s]} dup-neg nodes)")
print(f"  TOTAL neg removed: {sum(removed.values())}")
# informational: of the cross-split sources, how many ALSO duplicated within a single split
also_intra = sum(1 for h in cross if any(hash_split_count[h][s] >= 2 for s in hash_split_count[h]))
print(f"\ncross-split duplicate sources: {len(cross)}")
print(f"  ...of which ALSO duplicated within a single split (informational): {also_intra}")
