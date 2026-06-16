import json
from pathlib import Path
from collections import defaultdict
import re

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"

with open(oz_json_path) as f:
    oz_data = json.load(f)

# Map file to items
file_items = defaultdict(list)
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
    file_items[rel].append(item)

all_files = list(file_items.keys())

# 1. Parse imports
import_regex = re.compile(r'import\s+(?:(?:\{[^\}]*\}|\*)\s+from\s+)?["\']([^"\']+)["\'];')
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"

import_graph = defaultdict(set)
for rel in all_files:
    path = OZ_DIR / rel
    if not path.exists():
        continue
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        imports = import_regex.findall(content)
        for imp in imports:
            if imp.startswith("@openzeppelin/contracts/"):
                imp_rel = imp.replace("@openzeppelin/contracts/", "")
            else:
                current_dir = path.parent
                resolved = (current_dir / imp).resolve()
                try:
                    imp_rel = str(resolved.relative_to(OZ_DIR)).replace("\\", "/")
                except ValueError:
                    imp_rel = str(resolved).replace("\\", "/")
            
            if imp_rel in file_items:
                import_graph[rel].add(imp_rel)
                import_graph[imp_rel].add(rel)
    except Exception as e:
        pass

# 2. Map function hashes
hash_to_files = defaultdict(set)
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
    h = item['normalized_source_hash']
    hash_to_files[h].add(rel)

# 3. Build adjacency list
adj = defaultdict(set)
for u, neighbors in import_graph.items():
    for v in neighbors:
        adj[u].add(v)
        adj[v].add(u)

for h, files in hash_to_files.items():
    f_list = list(files)
    for i in range(len(f_list) - 1):
        adj[f_list[i]].add(f_list[i+1])
        adj[f_list[i+1]].add(f_list[i])

# 4. Connected components
visited = set()
components = []

for node in all_files:
    if node not in visited:
        comp = []
        queue = [node]
        visited.add(node)
        while queue:
            curr = queue.pop(0)
            comp.append(curr)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(comp)

components.sort(key=len, reverse=True)

# Map component index (1-based) to split based on design:
# Component 1 -> train
# Components 2, 6, 8, 10 -> val
# Others -> holdout
file_split_map = {}
for idx, comp in enumerate(components):
    comp_id = idx + 1
    if comp_id == 1:
        split_name = "train"
    elif comp_id in (2, 6, 8, 10):
        split_name = "val"
    else:
        split_name = "holdout"
        
    for f in comp:
        file_split_map[f] = split_name

# Save split mapping to JSON
out_path = PROJECT_ROOT / "scratch" / "oz_split_mapping.json"
with open(out_path, "w") as fh:
    json.dump(file_split_map, fh, indent=2)

print(f"Saved split mapping for {len(file_split_map)} files to {out_path}")

