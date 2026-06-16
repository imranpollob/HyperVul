import json
import re
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"

oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"
with open(oz_json_path) as f:
    oz_data = json.load(f)

dataset_files = set()
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    dataset_files.add(fp)

print(f"Dataset unique files count: {len(dataset_files)}")

import_graph = defaultdict(set)

def normalize_rel_path(p):
    p = str(p).replace("\\", "/")
    if "data/external/openzeppelin-contracts/contracts/" in p:
        return p.split("data/external/openzeppelin-contracts/contracts/")[-1]
    if "contracts/" in p:
        return p.split("contracts/")[-1]
    return p

all_sol_files = list(OZ_DIR.glob("**/*.sol"))
print(f"Total .sol files in OZ: {len(all_sol_files)}")

file_to_path = {}
for sf in all_sol_files:
    rel = normalize_rel_path(sf)
    file_to_path[rel] = sf

import_regex = re.compile(r'import\s+(?:(?:\{[^\}]*\}|\*)\s+from\s+)?["\']([^"\']+)["\'];')

for rel, path in file_to_path.items():
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()
        imports = import_regex.findall(content)
        for imp in imports:
            if imp.startswith("@openzeppelin/contracts/"):
                imp_rel = imp.replace("@openzeppelin/contracts/", "")
            else:
                current_dir = (OZ_DIR / rel).parent
                resolved = (current_dir / imp).resolve()
                try:
                    imp_rel = normalize_rel_path(resolved.relative_to(OZ_DIR))
                except ValueError:
                    imp_rel = normalize_rel_path(resolved)
            
            imp_rel = normalize_rel_path(imp_rel)
            import_graph[rel].add(imp_rel)
    except Exception as e:
        print(f"Error reading {rel}: {e}")

undirected_graph = defaultdict(set)
all_nodes = set(file_to_path.keys())

for u, neighbors in import_graph.items():
    for v in neighbors:
        if v in all_nodes:
            undirected_graph[u].add(v)
            undirected_graph[v].add(u)

visited = set()
components = []

for node in all_nodes:
    if node not in visited:
        comp = []
        queue = [node]
        visited.add(node)
        while queue:
            curr = queue.pop()
            comp.append(curr)
            for neighbor in undirected_graph[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(comp)

dataset_components = []
for comp in components:
    comp_dataset_files = [f for f in comp if f"data/external/openzeppelin-contracts/contracts/{f}" in dataset_files]
    if comp_dataset_files:
        dataset_components.append({
            "all_files": comp,
            "dataset_files": comp_dataset_files,
            "size_in_dataset": sum(sum(1 for item in oz_data if (item.get('file') or item.get('filePath')) == f"data/external/openzeppelin-contracts/contracts/{f}") for f in comp_dataset_files)
        })

dataset_components.sort(key=lambda x: x['size_in_dataset'], reverse=True)

print(f"\nTotal components containing dataset files: {len(dataset_components)}")
print(f"Total dataset items (from these components): {sum(c['size_in_dataset'] for c in dataset_components)}")

print("\nTop 15 Components by Number of Negatives:")
for idx, dc in enumerate(dataset_components[:15]):
    print(f"\nComponent {idx+1}:")
    print(f"  Total files in component: {len(dc['all_files'])}")
    print(f"  Dataset files in component: {len(dc['dataset_files'])}")
    print(f"  Number of negative hyperedges in dataset: {dc['size_in_dataset']}")
    print(f"  Sample dataset files:")
    for f in dc['dataset_files'][:8]:
        print(f"    - {f}")
    if len(dc['dataset_files']) > 8:
        print(f"    ... and {len(dc['dataset_files']) - 8} more")

# Print component size statistics (number of files)
sizes = [len(c['all_files']) for c in dataset_components]
print(f"\nComponent sizes (total files in OZ) stats: min={min(sizes)}, max={max(sizes)}, median={sorted(sizes)[len(sizes)//2]}")
neg_sizes = [c['size_in_dataset'] for c in dataset_components]
print(f"Component dataset hyperedges count stats: min={min(neg_sizes)}, max={max(neg_sizes)}, median={sorted(neg_sizes)[len(neg_sizes)//2]}")

# Let's count how many components are singletons, size 2-5, or large
size_ranges = Counter()
for dc in dataset_components:
    s = len(dc['all_files'])
    if s == 1:
        size_ranges['1 file (singleton)'] += 1
    elif s <= 5:
        size_ranges['2-5 files'] += 1
    elif s <= 20:
        size_ranges['6-20 files'] += 1
    else:
        size_ranges['>20 files'] += 1

print("\nComponent distribution by file size:")
for r, c in size_ranges.items():
    print(f"  {r}: {c} components")

# Let's check imports between these top components or if there is any other sharing
comp_by_file = {}
for idx, dc in enumerate(dataset_components):
    for f in dc['all_files']:
        comp_by_file[f] = idx

inter_comp_imports = defaultdict(set)
for rel, neighbors in import_graph.items():
    if rel in comp_by_file:
        c1 = comp_by_file[rel]
        for n in neighbors:
            if n in comp_by_file:
                c2 = comp_by_file[n]
                if c1 != c2:
                    inter_comp_imports[c1].add(c2)

if inter_comp_imports:
    print(f"Warning: Found {len(inter_comp_imports)} inter-component imports. List:")
    for c1, c2s in inter_comp_imports.items():
        print(f"  Component {c1+1} imports from: {sorted([c2+1 for c2 in c2s])}")
else:
    print("No inter-component imports found. All components are completely isolated from each other under the import graph.")

# Save component mapping to JSON so we can use it for split design
output_map = []
for idx, dc in enumerate(dataset_components):
    output_map.append({
        "component_id": idx + 1,
        "all_files": dc['all_files'],
        "dataset_files": dc['dataset_files'],
        "size_in_dataset": dc['size_in_dataset']
    })

with open(PROJECT_ROOT / "scratch" / "oz_components.json", "w") as fh:
    json.dump(output_map, fh, indent=2)

print("\nSaved component mapping to scratch/oz_components.json")

