#!/usr/bin/env python3
"""
Build SIGNATURE/skeleton node features: re-embed each function node from its
signature (declaration header WITHOUT the body), keeping the existing state-var and
callee embeddings untouched. This is the clean atomic feature (vs the hard
function-node drop): the function keeps its identity (name, params, modifiers,
returns) but loses the body text that redundantly contained the call/state info,
so the {function, state, callee} relation must be reassembled through structure.

Reuses extract_features.py resolvers (SmartBERT, OZ/DAppSCAN/FORGE source location).
Writes *_sig.json next to each input *_features.json (only node_features.function changes).
"""
import json
import sys
from pathlib import Path

import tree_sitter as ts
import tree_sitter_solidity as tss

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))

import extract_features as ef  # loads SmartBERT + OZ + FORGE vfp at import
import negative_hyperedge_sampling as nhs

LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)
AAVE_ROOT = PROJECT_ROOT / "scratch" / "clones" / "aave-v3" / "contracts"

_aave_contracts = None


def aave_contracts():
    global _aave_contracts
    if _aave_contracts is None:
        _aave_contracts = {}
        for sf in AAVE_ROOT.glob("**/*.sol"):
            try:
                _aave_contracts.update(nhs.parse_contracts(sf.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                pass
    return _aave_contracts


def to_signature(src):
    """Function text up to (but excluding) the body block; fallback to text before first '{'."""
    try:
        tree = PARSER.parse(src.encode("utf-8"))

        def find_fn(n):
            if n.type == "function_definition":
                return n
            for c in n.children:
                r = find_fn(c)
                if r:
                    return r
            return None

        fn = find_fn(tree.root_node)
        if fn is not None:
            body = fn.child_by_field_name("body")
            b = src.encode("utf-8")
            end = body.start_byte if body is not None else fn.end_byte
            return b[fn.start_byte:end].decode("utf-8", errors="ignore").strip()
    except Exception:
        pass
    return src.split("{", 1)[0].strip()


def locate_func_src(item):
    if item.get("function_source"):
        return item["function_source"]

    contract = item["contract"]
    func = item.get("function") or item.get("ast_function")
    fp = item.get("file") or item.get("filePath")
    src = item.get("source")
    if not src:
        if "openzeppelin" in str(fp).lower():
            src = "OpenZeppelin"
        elif "dappscan" in str(fp).lower() or "project_root" in item:
            src = "DAppSCAN"
        else:
            src = "FORGE"

    try:
        if src == "OpenZeppelin":
            code = (PROJECT_ROOT / fp).read_text(encoding="utf-8", errors="ignore")
            merged = dict(ef.oz_contracts); merged.update(nhs.parse_contracts(code))
        elif src == "AaveV3":
            code = (AAVE_ROOT / fp).read_text(encoding="utf-8", errors="ignore")
            merged = dict(aave_contracts()); merged.update(nhs.parse_contracts(code))
        elif src == "DAppSCAN":
            code = (ef.DAPPSCAN_ROOT / fp).read_text(encoding="utf-8", errors="ignore")
            merged = dict(ef.get_dappscan_project_contracts(fp)); merged.update(nhs.parse_contracts(code))
        else:  # FORGE / None
            vid = item.get("vfp_id") or ef.find_forge_vfp_id(item)
            if not vid:
                return None
            merged = {}
            for fn_, fc in ef.vfp_data[vid]["affected_files"].items():
                merged.update(nhs.parse_contracts(fc))
        funcs = nhs.resolve_all_functions(contract, merged)
        if func in funcs:
            return nhs.node_text(funcs[func])
    except Exception:
        return None
    return None


def process(features_path, out_path):
    data = json.load(open(features_path))
    print(f"\n{features_path.name}: {len(data)} items")
    sigs, idx_ok = [], []
    for i, it in enumerate(data):
        s = locate_func_src(it)
        if s:
            sig = to_signature(s)
            it["_sig_text"] = sig
            sigs.append(sig); idx_ok.append(i)
    print(f"  resolved {len(idx_ok)}/{len(data)} function sources")
    emb_map = ef.batch_encode_texts(sigs, max_length=128, batch_size=32)
    out = []
    for i, it in enumerate(data):
        if "_sig_text" not in it:
            continue  # drop unresolved (keeps dataset clean)
        it["node_features"]["function"] = emb_map[it.pop("_sig_text")]
        out.append(it)
    json.dump(out, open(out_path, "w"))
    print(f"  wrote {len(out)} -> {out_path.name}")


if __name__ == "__main__":
    splits = PROJECT_ROOT / "data" / "splits"
    res = PROJECT_ROOT / "experiments" / "results"
    jobs = [
        (splits / "train_augmented.json", splits / "train_augmented_sig.json"),
        (splits / "val_features.json", splits / "val_sig.json"),
        (splits / "test_features.json", splits / "test_sig.json"),
        (res / "eval_clean_negatives_oz_features.json", res / "eval_clean_negatives_oz_sig.json"),
        (res / "eval_clean_negatives_aave_split.json", res / "eval_clean_negatives_aave_sig.json"),
    ]
    for src, dst in jobs:
        process(src, dst)
    print("\nDone.")
