#!/usr/bin/env python3
"""
Step 2 — build symbolic safety-aware node features as index-aligned SIDECARS.

For each SmartBERT feature file the trainer loads, emit `{stem}_sym.json`: a list with one
entry per item (same order/length as the feature file), holding the Stage-2 symbolic vectors
per node:

    {"function": [SYM_DIM], "state_vars": {name: [SYM_DIM]}, "external_calls": [[SYM_DIM], ...]}

(or null when the item's source cannot be resolved). model/train.py merges the sidecar by
index and concatenates each node's symbolic vector onto its 768-d embedding.

Symbolic features are derived per item with the Stage-2 resolver `build_bottleneck_item`
(reuses extract_bottleneck_schema), so alignment is exact regardless of the 7 unresolved
train rows or variant duplicates. Encodings come from src/models/symbolic.py.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))

import extract_bottleneck_schema as ebs   # build_bottleneck_item + node builders (loads SmartBERT)
import negative_hyperedge_sampling as nhs
from src.models import symbolic as S

# Clean-code OOD holdouts (source != OZ/Aave/DAppSCAN/FORGE) live in local clones; their
# source files are resolved by parsing the whole repo (mirrors build_external_clean.py /
# build_iteration3_data.py roots).
CLONES = PROJECT_ROOT / "scratch" / "clones"
REPO_DIRS = {
    "MakerDAO": CLONES / "makerdao-dss" / "src",
    "Bancor": CLONES / "bancor-v3" / "contracts",
    "Liquity": CLONES / "liquity" / "packages" / "contracts" / "contracts",
}
_repo_cache = {}


def repo_contracts(source):
    if source not in _repo_cache:
        merged = {}
        for sf in REPO_DIRS[source].glob("**/*.sol"):
            try:
                merged.update(nhs.parse_contracts(sf.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                pass
        _repo_cache[source] = merged
    return _repo_cache[source]


def _nodes_for_clone(item):
    """(function_hub, state_nodes, callee_nodes) for a clone-repo holdout item, or None."""
    contract = item["contract"]
    func = item.get("function") or item.get("ast_function")
    merged = repo_contracts(item["source"])
    fn = nhs.resolve_all_functions(contract, merged).get(func)
    if fn is None:
        return None
    svt = nhs.resolve_all_state_var_types(contract, merged)
    asv = nhs.resolve_all_state_vars(contract, merged)
    lv = nhs.extract_local_vars(fn)
    hub = ebs.build_function_hub(fn, merged)
    state_nodes = ebs.classify_state_accesses(fn, asv, lv, svt, merged)
    callee_nodes = ebs.build_callee_nodes(fn, svt, merged, contract, hub["modifiers"])
    return hub, state_nodes, callee_nodes


def _sym_from_nodes(hub, state_nodes, callee_nodes, feat_item):
    accesses = defaultdict(list)
    type_bucket = {}
    for sn in state_nodes:
        accesses[sn["name"]].append(sn["access"])
        type_bucket[sn["name"]] = sn.get("type_bucket", "other")

    nf = feat_item["node_features"]
    state_syms = {}
    for name in nf["state_vars"].keys():            # preserve feature node ordering
        state_syms[name] = S.encode_state({
            "type_bucket": type_bucket.get(name, "other"),
            "access": S.merge_state_access(accesses.get(name, ["read"])),
        })
    callee_syms = []
    for i in range(len(nf["external_calls"])):       # align by index (counts match)
        node = callee_nodes[i] if i < len(callee_nodes) else {}
        callee_syms.append(S.encode_callee(node))

    return {
        "function": S.encode_function(hub),
        "state_vars": state_syms,
        "external_calls": callee_syms,
    }


def symbolic_for_item(feat_item):
    """Return the per-node symbolic dict for one feature item, or None if unresolvable."""
    if feat_item.get("source") in REPO_DIRS:         # MakerDAO / Bancor / Liquity clones
        nodes = _nodes_for_clone(feat_item)
        return _sym_from_nodes(*nodes, feat_item) if nodes else None
    bott = ebs.build_bottleneck_item(feat_item)      # OZ / Aave / DAppSCAN / FORGE
    if bott is None:
        return None
    return _sym_from_nodes(bott["function_hub"], bott["state_nodes"], bott["callee_nodes"], feat_item)


def process(features_path: Path, out_path: Path):
    data = json.load(open(features_path))
    print(f"\n{features_path.name}: {len(data)} items")
    out, resolved, mism = [], 0, 0
    for it in data:
        try:
            sym = symbolic_for_item(it)
        except Exception:
            sym = None
        if sym is None:
            out.append(None)
            continue
        resolved += 1
        if len(sym["external_calls"]) != len(it["node_features"]["external_calls"]):
            mism += 1
        out.append(sym)
    json.dump(out, open(out_path, "w"))
    print(f"  resolved {resolved}/{len(data)} | callee-count mismatches: {mism} "
          f"| SYM_DIM={S.SYM_DIM} -> {out_path.name}")


if __name__ == "__main__":
    splits = PROJECT_ROOT / "data" / "splits"
    res = PROJECT_ROOT / "experiments" / "results"
    jobs = [
        (splits / "train_augmented.json", splits / "train_augmented_sym.json"),
        (splits / "val_features.json",    splits / "val_features_sym.json"),
        (splits / "test_features.json",   splits / "test_features_sym.json"),
        (res / "eval_clean_negatives_oz_features.json", res / "eval_clean_negatives_oz_features_sym.json"),
        (res / "eval_clean_negatives_external.json",    res / "eval_clean_negatives_external_sym.json"),
        (res / "eval_clean_negatives_aave_split.json",  res / "eval_clean_negatives_aave_split_sym.json"),
        (res / "eval_clean_negatives_liquity.json",     res / "eval_clean_negatives_liquity_sym.json"),
    ]
    if len(sys.argv) >= 3:
        process(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        for src, dst in jobs:
            if src.exists():
                process(src, dst)
            else:
                print(f"skip (missing): {src}")
        print("\nDone.")
