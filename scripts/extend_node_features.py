#!/usr/bin/env python3
"""TASK 2 — extend feature extraction to the FULL contract-graph dataset.

The encode pass only embedded function_source. Restore the original multi-component node
representation: per node, also embed each state-var ("type name" @256) and callee
(call_text @64), reusing the original encoding settings. Adds `state_texts`/`callee_texts`
to each node and saves member embeddings keyed by string. Prints unique-span counts FIRST
so the compute cost is confirmed before encoding.
"""
import json, sys, shutil
from pathlib import Path
import torch
from transformers import RobertaTokenizer, RobertaModel
ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
GDIR = ROOT / "data" / "contract_graphs"
DAPP = ROOT / "data" / "DAppSCAN"
FVULN = ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
BK = ROOT / "scratch" / "contract_graphs_pre_member"; BK.mkdir(parents=True, exist_ok=True)

# --- resolve state-var types per project (cached parse) ---
proj_cache = {}
def types_for(source, project, contract):
    key = (source, project)
    if key not in proj_cache:
        merged = {}
        if source == "FORGE":
            p = FVULN / f"{project}.json"
            if p.exists():
                for _, s in json.load(open(p)).get("affected_files", {}).items():
                    try: merged.update(nhs.parse_contracts(s))
                    except Exception: pass
        else:
            for sol in (DAPP / project).glob("**/*.sol"):
                try: merged.update(nhs.parse_contracts(sol.read_text(encoding="utf-8", errors="ignore")))
                except Exception: pass
        proj_cache[key] = merged
    try: return nhs.resolve_all_state_var_types(contract, proj_cache[key])
    except Exception: return {}

graphs = {s: json.load(open(GDIR / f"{s}.json")) for s in ["train", "val", "test"]}
state_set, callee_set = set(), set()
nnodes = 0
for s in graphs:
    for g in graphs[s]:
        svt = None
        for n in g["nodes"]:
            nnodes += 1
            if svt is None: svt = types_for(g["source"], g["project"], g["contract"])
            st = [f"{svt.get(sv,'')} {sv}".strip() for sv in n.get("state_vars_accessed", [])]
            ct = [e["call_text"] for e in n.get("external_calls", [])]  # helpers: no external_calls -> []
            n["state_texts"] = st; n["callee_texts"] = ct
            state_set.update(st); callee_set.update(ct)

print("=== TASK 2 — compute scale (CONFIRM before encoding) ===")
print(f"  total nodes: {nnodes}")
print(f"  unique state-var strings to encode @256: {len(state_set)}")
print(f"  unique callee call-texts to encode @64 : {len(callee_set)}")
print(f"  function embeddings: already computed (node_embeddings.pt) — reused, not recomputed")
print(f"  -> short strings; estimated < 1 min on GPU. Encoding now.\n")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tok = RobertaTokenizer.from_pretrained("web3se/SmartBERT-v3")
enc = RobertaModel.from_pretrained("web3se/SmartBERT-v3").eval().to(device)

def encode(texts, max_length):
    texts = [t for t in texts if t]; out = {}
    with torch.no_grad():
        for i in range(0, len(texts), 128):
            b = texts[i:i+128]
            inp = tok(b, return_tensors="pt", max_length=max_length, truncation=True, padding="longest").to(device)
            cls = enc(**inp).last_hidden_state[:, 0, :].cpu()
            for t, v in zip(b, cls): out[t] = v.clone()
    return out

state_emb = encode(list(state_set), 256)
callee_emb = encode(list(callee_set), 64)
torch.save({"state": state_emb, "callee": callee_emb}, GDIR / "member_embeddings.pt")
print(f"saved member_embeddings.pt: state={len(state_emb)} callee={len(callee_emb)} "
      f"({(GDIR/'member_embeddings.pt').stat().st_size/1e6:.1f} MB)")

# write augmented graphs (backup first)
for s in graphs:
    shutil.copy(GDIR / f"{s}.json", BK / f"{s}.json")
    json.dump(graphs[s], open(GDIR / f"{s}.json", "w"))
print("augmented graphs written (state_texts/callee_texts added; backup in scratch/contract_graphs_pre_member/)")
