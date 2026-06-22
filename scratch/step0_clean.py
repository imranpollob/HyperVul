"""STEP 0 groundwork — produce cleaned splits (non-destructive; originals untouched).
 0a Box fix: move the 6 train Box negatives to test (all 14 vfp_00189 Box items -> test)
 0b scaffolding filter: drop items whose contract is a test/mock scaffold
 0c Task-8 exclusion: remove the named non-security FORGE positives entirely"""
import json
from pathlib import Path
SP = Path("/home/pollmix/Coding/HyperVul/data/splits")
OUT = Path("/home/pollmix/Coding/HyperVul/data/splits_clean"); OUT.mkdir(exist_ok=True)
SCRATCH = Path("/home/pollmix/Coding/HyperVul/scratch")

scaffold = set(c["contract"] for c in json.load(open(SCRATCH / "scaffold_candidates.json")))
TASK8_DROP = {("FlashLoans", "flashLoan"), ("OctoDistributor", "withdrawAllAgentTokens"),
              ("OctoDistributor", "transferHiringDistributions"), ("MainFeeDistributor", "swapLzToken")}

def fn(it): return it.get("function") or it.get("ast_function")
splits = {s: json.load(open(SP / f"{s}.json")) for s in ["train", "val", "test"]}

log = {"task8_dropped": [], "scaffold_dropped": [], "box_moved": []}

# 0c — drop Task-8 non-security positives (from wherever they are)
for s in splits:
    kept = []
    for it in splits[s]:
        if (it.get("contract"), fn(it)) in TASK8_DROP and it.get("label") == 1:
            log["task8_dropped"].append(f"{s}:{it.get('contract')}.{fn(it)} vfp={it.get('vfp_id')}")
        else:
            kept.append(it)
    splits[s] = kept

# 0b — scaffolding filter
for s in splits:
    kept = []
    for it in splits[s]:
        if it.get("contract") in scaffold:
            log["scaffold_dropped"].append(f"{s}:{it.get('contract')}.{fn(it)} label={it.get('label')}")
        else:
            kept.append(it)
    splits[s] = kept

# 0a — Box fix: move train Box items -> test
box_train = [it for it in splits["train"] if it.get("contract") == "Box"]
splits["train"] = [it for it in splits["train"] if it.get("contract") != "Box"]
for it in box_train:
    log["box_moved"].append(f"{it.get('contract')}.{fn(it)} label={it.get('label')} train->test")
splits["test"] = splits["test"] + box_train

# write
for s in splits:
    json.dump(splits[s], open(OUT / f"{s}.json", "w"), indent=1)

def counts(items):
    p = sum(1 for it in items if it.get("label") == 1); return p, len(items) - p

print("=== STEP 0 RESULTS ===")
base = {s: json.load(open(SP / f"{s}.json")) for s in ["train", "val", "test"]}
for s in ["train", "val", "test"]:
    bp, bn = counts(base[s]); cp, cn = counts(splits[s])
    print(f"  {s:5s}: base pos/neg = {bp}/{bn}  ->  clean pos/neg = {cp}/{cn}")

print(f"\n0c Task-8 dropped ({len(log['task8_dropped'])} rows):")
for x in log["task8_dropped"]: print("   -", x)
print(f"\n0b Scaffolding dropped from splits ({len(log['scaffold_dropped'])} items):")
for x in log["scaffold_dropped"]: print("   -", x)
print(f"\n0a Box moved train->test ({len(log['box_moved'])} items):")
for x in log["box_moved"]: print("   -", x)
box_test = [it for it in splits["test"] if it.get("contract") == "Box"]
print(f"   Box items now in test: {len(box_test)} (expect 14)")
json.dump(log, open(SCRATCH / "step0_log.json", "w"), indent=1)
