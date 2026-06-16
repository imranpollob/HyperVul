import json
from pathlib import Path
from collections import defaultdict
import hashlib
import difflib

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"

with open(oz_json_path) as f:
    oz_data = json.load(f)

def assign_group(rel):
    rel_lower = rel.lower()
    if "governance" in rel_lower:
        return "TOK_GOV"
    if "crosschain" in rel_lower:
        return "ACC_CROSS"
    if any(k in rel_lower for k in ("token", "votes", "comp", "erc20", "erc721", "erc1155")):
        return "TOK_GOV"
    if any(k in rel_lower for k in ("access", "bridge")):
        return "ACC_CROSS"
    return "OTHER"

file_to_group = {}
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
    file_to_group[rel] = assign_group(rel)

# Load file contents and calculate hashes
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"
file_contents = {}
file_hashes = {}

for rel in file_to_group:
    path = OZ_DIR / rel
    if path.exists():
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        file_contents[rel] = content
        file_hashes[rel] = hashlib.sha256(content.encode('utf-8')).hexdigest()

# Check for hash collisions across different splits
hash_to_files = defaultdict(list)
for rel, h in file_hashes.items():
    hash_to_files[h].append(rel)

cross_split_collisions = []
for h, files in hash_to_files.items():
    if len(files) > 1:
        splits = set(file_to_group[f] for f in files)
        if len(splits) > 1:
            cross_split_collisions.append((files, splits))

print(f"Identical files across different splits: {len(cross_split_collisions)}")
for files, splits in cross_split_collisions:
    print(f"  Files: {files} | Splits: {splits}")

# Let's also verify that no function source text is identical across different splits
func_to_splits = defaultdict(set)
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
    grp = file_to_group[rel]
    h = item['normalized_source_hash']
    func_to_splits[h].add(grp)

cross_split_funcs = []
for h, grps in func_to_splits.items():
    if len(grps) > 1:
        # Find item details
        items_with_hash = [it for it in oz_data if it['normalized_source_hash'] == h]
        cross_split_funcs.append((items_with_hash, grps))

print(f"\nIdentical functions across different splits: {len(cross_split_funcs)}")
for items, grps in cross_split_funcs[:10]:
    first = items[0]
    print(f"  Function '{first['function']}' in contract '{first['contract']}' | Splits: {grps}")
    for it in items:
        fp = it.get('file') or it.get('filePath')
        rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
        print(f"    - File: {rel}")

