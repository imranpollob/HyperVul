"""Task 8 — random audit of 15 positive labels vs original finding. Read-only.
Excludes the 4 previously-flagged DUBIOUS SWC-104 items."""
import json, random, sys
from pathlib import Path
PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT)); sys.path.append(str(PROJECT_ROOT / "scripts"))
import run_diagnostics as rd

DUBIOUS = {"balanceOfy3CRVinWant", "_getLatestRoundData"}

pos = []
for s in ["train", "val", "test"]:
    for it in json.load(open(PROJECT_ROOT / "data" / "splits" / f"{s}.json")):
        if it["label"] != 1:
            continue
        fn = it.get("function") or it.get("ast_function")
        if fn in DUBIOUS:
            continue
        it["_split"] = s
        pos.append(it)

random.seed(42)
sample = random.sample(pos, 15)

vfp_data = rd.vfp_data

def forge_finding(it):
    vid = it.get("vfp_id")
    if not vid or vid not in vfp_data:
        return None
    v = vfp_data[vid]
    out = {"vfp_id": vid, "findings": []}
    for f in v.get("findings", []) if isinstance(v.get("findings"), list) else []:
        out["findings"].append({"title": f.get("title"), "severity": f.get("severity")})
    # fallback: top-level fields
    for k in ("title", "vulnerability_type", "category", "cwe"):
        if k in v:
            out[k] = v[k]
    return out

def dappscan_annotation(it):
    fp = it.get("file") or it.get("filePath")
    full = rd.DAPPSCAN_ROOT / fp
    fn = it.get("function") or it.get("ast_function")
    if not full.exists():
        return "FILE NOT FOUND"
    text = full.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits = []
    for i, line in enumerate(text):
        if "SWC-" in line and ("//" in line or "/*" in line):
            hits.append(f"L{i+1}: {line.strip()[:140]}")
    return hits[:6] if hits else "no inline SWC comment found"

for i, it in enumerate(sample, 1):
    src = "FORGE" if it.get("vfp_id") else "DAppSCAN"
    fn = it.get("function") or it.get("ast_function")
    print(f"\n{'='*70}\n[{i}] {src}  split={it['_split']}  label={it['label']}")
    print(f"  contract={it.get('contract')}  function={fn}")
    print(f"  recorded vtype/swc = {it.get('vtype') or it.get('swc_code') or it.get('category')}")
    print(f"  file = {it.get('file') or it.get('filePath')}")
    if src == "FORGE":
        print(f"  FORGE finding: {json.dumps(forge_finding(it))[:400]}")
    else:
        ann = dappscan_annotation(it)
        print(f"  DAppSCAN inline SWC annotations in file:")
        if isinstance(ann, list):
            for h in ann:
                print(f"    {h}")
        else:
            print(f"    {ann}")
