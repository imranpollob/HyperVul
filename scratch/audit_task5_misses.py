"""Read-only: identify the missed SWC-107 reentrancy positives at the §3.7 base model
(iteration1_checkpoint + threshold_config). No training, no file modification."""
import json, sys
from pathlib import Path
import torch
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))
from model.model import HyperedgeClassifier
from model.train import HyperedgeDataset, collate_fn, evaluate_model

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = HyperedgeClassifier(input_dim=768, hidden_dim=256, dropout=0.3, localize=False).to(device)
model.load_state_dict(torch.load(PROJECT_ROOT / "model" / "iteration1_checkpoint.pt", map_location=device))
model.eval()
with open(PROJECT_ROOT / "model" / "threshold_config.json") as f:
    thr = json.load(f)["best_threshold"]

with open(PROJECT_ROOT / "data" / "splits" / "test_features.json") as f:
    test_data = json.load(f)

loader = torch.utils.data.DataLoader(HyperedgeDataset(test_data), batch_size=32, shuffle=False, collate_fn=collate_fn)
probs, labels, items = evaluate_model(model, loader, device)
preds = (probs >= thr).astype(int)

def vtype_of(it):
    return (it.get("vtype") or it.get("category") or it.get("swc_code") or "").strip()

def is_reentrancy(it):
    s = vtype_of(it).lower()
    return "reentran" in s or "swc-107" in s or "swc107" in s

reent = [(i, it) for i, it in enumerate(items) if it["label"] == 1 and is_reentrancy(it)]
print(f"threshold={thr:.4f}")
print(f"SWC-107 reentrancy positives in test_features: {len(reent)}")
caught = sum(1 for i, it in reent if preds[i] == 1)
print(f"caught={caught}, missed={len(reent)-caught}, recall={caught/len(reent)*100:.2f}%")
print("\n=== MISSED REENTRANCY POSITIVES (FN) ===")
for i, it in reent:
    if preds[i] == 0:
        fn = it.get("function") or it.get("ast_function")
        print(f"\n- contract={it.get('contract')}  func={fn}")
        print(f"  vfp_id={it.get('vfp_id')}  project_root={it.get('project_root')}")
        print(f"  file={it.get('file') or it.get('filePath')}")
        print(f"  is_cross_contract={it.get('is_cross_contract')}  prob={probs[i]:.4f}")
        print(f"  state_vars_accessed={it.get('state_vars_accessed')}")
        ec = it.get('external_calls', [])
        print(f"  external_calls={[e.get('call_text') for e in ec]}")
