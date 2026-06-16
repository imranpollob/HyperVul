import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"
mapping_path = PROJECT_ROOT / "scratch" / "oz_split_mapping.json"

with open(oz_json_path) as f:
    oz_data = json.load(f)

with open(mapping_path) as f:
    mapping = json.load(f)

split_counts = Counter()
split_files = {
    "train": set(),
    "val": set(),
    "holdout": set()
}

for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
    split = mapping[rel]
    split_counts[split] += 1
    split_files[split].add(rel)

print("Split counts of negative hyperedges:")
for sp, cnt in split_counts.items():
    print(f"  {sp}: {cnt} items ({len(split_files[sp])} unique files)")

# Verify disjointness
all_splits = ["train", "val", "holdout"]
for i in range(len(all_splits)):
    for j in range(i + 1, len(all_splits)):
        s1 = all_splits[i]
        s2 = all_splits[j]
        intersection = split_files[s1].intersection(split_files[s2])
        print(f"Overlap between {s1} and {s2}: {len(intersection)} files")

