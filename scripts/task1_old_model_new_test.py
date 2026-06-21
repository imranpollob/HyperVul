#!/usr/bin/env python3
"""TASK 1 — original isolated-hyperedge model (iteration1_checkpoint) on the FULL
contract-graph test pool, in the model's NATIVE representation (function+state+callee
embeddings pooled by AttentionPooling, original 256/256/64 token settings). Read-only.

Isolates whether the 0.89->0.64 ROC-AUC drop is the test set getting harder vs the new
architecture being worse: same old model, new (full) test pool.
"""
import json, sys
from pathlib import Path
import numpy as np, torch
from transformers import RobertaTokenizer, RobertaModel
from sklearn.metrics import average_precision_score, roc_auc_score
ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(ROOT)); sys.path.append(str(ROOT / "scripts"))
import negative_hyperedge_sampling as nhs
from model.model import HyperedgeClassifier
from model.train import HyperedgeDataset, collate_fn, evaluate_model

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tok = RobertaTokenizer.from_pretrained("web3se/SmartBERT-v3")
enc = RobertaModel.from_pretrained("web3se/SmartBERT-v3").eval().to(device)
DAPP = ROOT / "data" / "DAppSCAN"
FVULN = ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"

def batch_encode(texts, max_length):
    uniq = list(set(texts)); out = {}
    with torch.no_grad():
        for i in range(0, len(uniq), 64):
            b = uniq[i:i+64]
            inp = tok(b, return_tensors="pt", max_length=max_length, truncation=True, padding="longest").to(device)
            cls = enc(**inp).last_hidden_state[:, 0, :].cpu().tolist()
            for t, e in zip(b, cls): out[t] = e
    return out

# parse each test project once -> state var types per contract
proj_types = {}
def types_for(source, project, contract):
    key = (source, project)
    if key not in proj_types:
        merged = {}
        if source == "FORGE":
            v = json.load(open(FVULN / f"{project}.json"))
            for _, s in v.get("affected_files", {}).items():
                try: merged.update(nhs.parse_contracts(s))
                except Exception: pass
        else:
            proot = DAPP / project
            for sol in proot.glob("**/*.sol"):
                try: merged.update(nhs.parse_contracts(sol.read_text(encoding="utf-8", errors="ignore")))
                except Exception: pass
        proj_types[key] = merged
    merged = proj_types[key]
    try: return nhs.resolve_all_state_var_types(contract, merged)
    except Exception: return {}

# build raw items from full contract-graph test interactions
raw, func_t, state_t, call_t = [], [], [], []
for g in json.load(open(ROOT / "data" / "contract_graphs" / "test.json")):
    svt = None
    for n in g["nodes"]:
        if n["kind"] != "interaction": continue
        if svt is None: svt = types_for(g["source"], g["project"], g["contract"])
        fsrc = n["function_source"]
        sv_texts = {sv: f"{svt.get(sv,'')} {sv}".strip() for sv in n.get("state_vars_accessed", [])}
        ec_texts = [e["call_text"] for e in n.get("external_calls", [])]
        func_t.append(fsrc); state_t += list(sv_texts.values()); call_t += ec_texts
        raw.append({"label": n["label"], "function": n["function"], "contract": g["contract"],
                    "fsrc": fsrc, "sv_texts": sv_texts, "ec_texts": ec_texts})

print(f"test interactions: {len(raw)}  (pos={sum(r['label'] for r in raw)})  encoding spans...")
fmap = batch_encode(func_t, 256); smap = batch_encode(state_t, 256) if state_t else {}; cmap = batch_encode(call_t, 64) if call_t else {}

items = []
for r in raw:
    items.append({"label": r["label"], "function": r["function"], "contract": r["contract"],
                  "node_features": {"function": fmap[r["fsrc"]],
                                    "state_vars": {sv: smap[t] for sv, t in r["sv_texts"].items()},
                                    "external_calls": [{"call_text": t, "embedding": cmap[t]} for t in r["ec_texts"]]}})

# run original model
model = HyperedgeClassifier(input_dim=768, hidden_dim=256, dropout=0.3, localize=False).to(device)
model.load_state_dict(torch.load(ROOT / "model" / "iteration1_checkpoint.pt", map_location=device))
model.eval()
loader = torch.utils.data.DataLoader(HyperedgeDataset(items), batch_size=64, shuffle=False, collate_fn=collate_fn)
probs, labels, _ = evaluate_model(model, loader, device)
thr = json.load(open(ROOT / "model" / "threshold_config.json"))["best_threshold"]

def table(probs, labels, t):
    pred = (probs >= t).astype(int); y = labels.astype(int)
    tp = int(((pred==1)&(y==1)).sum()); fp=int(((pred==1)&(y==0)).sum()); fn=int(((pred==0)&(y==1)).sum())
    p = tp/(tp+fp) if tp+fp else 0; r = tp/(tp+fn) if tp+fn else 0
    f1 = 2*p*r/(p+r) if p+r else 0; f2 = 5*p*r/(4*p+r) if 4*p+r else 0
    return p, r, f1, f2
p, r, f1, f2 = table(probs, labels, thr)
print("\n=== TASK 1: ORIGINAL model (iteration1) on FULL contract-graph test pool ===")
print(f"  test pool: {len(labels)} interactions, {int(labels.sum())} pos / {int((labels==0).sum())} neg  (base rate {labels.mean():.3f})")
print(f"  threshold (original config) = {thr:.4f}")
print(f"  precision={p:.3f}  recall={r:.3f}  F1={f1:.3f}  F2={f2:.3f}")
print(f"  PR-AUC={average_precision_score(labels, probs):.3f}")
print(f"  ROC-AUC={roc_auc_score(labels, probs):.3f}")
print("\n  --- comparison ---")
print(f"  original model on ORIGINAL test (44p/125n):     ROC-AUC ~0.89   PR-AUC ~0.72")
print(f"  original model on FULL pool (this run):          ROC-AUC {roc_auc_score(labels,probs):.3f}   PR-AUC {average_precision_score(labels,probs):.3f}")
print(f"  NEW G-HAN model on FULL pool (Option A sqrt):    ROC-AUC 0.637   PR-AUC 0.128")
