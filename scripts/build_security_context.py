#!/usr/bin/env python3
"""Per-interaction security_context vectors for the MoE router (regime conditioning).
Reuses the original SECURITY_FLAGS semantics (nonReentrant / safe_erc20 / low_level / cross)
plus access-control and payable, computed cheaply from each node's signature + callee methods
+ is_cross_contract. Adds node['sec'] (8-d) to interaction nodes. No GPU."""
import json, re, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))
from negative_hyperedge_sampling import LOW_LEVEL_CALLS, SAFE_TRANSFER_METHODS
GDIR = Path("/home/pollmix/Coding/HyperVul/data/contract_graphs")
BK = Path("/home/pollmix/Coding/HyperVul/scratch/contract_graphs_pre_sec"); BK.mkdir(parents=True, exist_ok=True)
SEC_DIM = 8
AC = re.compile(r"only[A-Z]\w*|onlyowner|authorized|hasrole|require\s*\(\s*msg\.sender", re.I)

def sec_vector(n):
    src = n["function_source"]; header = src.split("{", 1)[0]
    hl = header.lower()
    methods = [(e.get("method") or "").strip() for e in n.get("external_calls", [])]
    any_low = any(m in LOW_LEVEL_CALLS for m in methods)
    any_safe = any(m in SAFE_TRANSFER_METHODS for m in methods)
    return [
        1.0 if ("nonreentrant" in hl or "noreentrancy" in hl) else 0.0,   # reentrancy guard
        1.0 if AC.search(header) or AC.search(src[:400]) else 0.0,        # access control
        1.0 if re.search(r"\bpayable\b", header) else 0.0,                # payable
        1.0 if any_low else 0.0,                                          # low-level call
        1.0 if any_safe else 0.0,                                         # safe-erc20 call
        1.0 if n.get("is_cross_contract") else 0.0,                       # cross-contract
        min(len(methods), 10) / 10.0,                                     # #external calls
        min(len(n.get("state_vars_accessed", [])), 10) / 10.0,            # #state vars
    ]

for s in ["train", "val", "test"]:
    data = json.load(open(GDIR / f"{s}.json"))
    import shutil; shutil.copy(GDIR / f"{s}.json", BK / f"{s}.json")
    n_int = 0
    for g in data:
        for n in g["nodes"]:
            if n["kind"] == "interaction":
                n["sec"] = sec_vector(n); n_int += 1
    json.dump(data, open(GDIR / f"{s}.json", "w"))
    # quick distribution sanity
    import numpy as np
    secs = np.array([n["sec"] for g in data for n in g["nodes"] if n["kind"] == "interaction"])
    print(f"{s}: {n_int} interactions tagged; mean security_context = {np.round(secs.mean(0), 3).tolist()}")
print(f"SEC_DIM={SEC_DIM}; backup in scratch/contract_graphs_pre_sec/")
