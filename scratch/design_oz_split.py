import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"

with open(oz_json_path) as f:
    oz_data = json.load(f)

file_items = defaultdict(list)
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    rel = fp.replace("data/external/openzeppelin-contracts/contracts/", "")
    file_items[rel].append(item)

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

group_items = defaultdict(list)
group_files = defaultdict(list)

for rel, items in file_items.items():
    grp = assign_group(rel)
    group_items[grp].extend(items)
    group_files[grp].append(rel)

print("Refined Group Statistics:")
for grp, items in group_items.items():
    print(f"  {grp}: {len(items)} items ({len(group_files[grp])} files)")

# map file to group
file_to_group = {}
for grp, files in group_files.items():
    for f in files:
        file_to_group[f] = grp

# crossings:
import re
import_regex = re.compile(r'import\s+(?:(?:\{[^\}]*\}|\*)\s+from\s+)?["\']([^"\']+)["\'];')
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"

import_graph = defaultdict(set)
for rel in file_items.keys():
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
            import_graph[rel].add(imp_rel)
    except Exception as e:
        pass

crossings = []
for f, imps in import_graph.items():
    g1 = file_to_group[f]
    for imp in imps:
        if imp in file_to_group:
            g2 = file_to_group[imp]
            if g1 != g2:
                crossings.append((f"[{g1}] {f}", f"[{g2}] {imp}"))

print(f"\nCrossings: {len(crossings)}")
for src, dst in crossings:
    print(f"  {src} -> {dst}")

