import json
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"
with open(oz_json_path) as f:
    oz_data = json.load(f)

dataset_files = set()
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    dataset_files.add(fp)

# Let's write a function to map a path to a domain
def get_domain(path):
    # Normalize path: remove prefix data/external/openzeppelin-contracts/contracts/ if present
    p = str(path).replace("\\", "/")
    if "data/external/openzeppelin-contracts/contracts/" in p:
        p = p.split("data/external/openzeppelin-contracts/contracts/")[-1]
    elif "contracts/" in p:
        p = p.split("contracts/")[-1]
        
    parts = p.split("/")
    
    # Check for governance
    if "governance" in p:
        return "Governance"
    
    # Check for tokens
    if "ERC20" in p:
        return "ERC20"
    if "ERC721" in p:
        return "ERC721"
    if "ERC1155" in p:
        return "ERC1155"
    
    # Check for account / ERC4337 / ERC7579
    if "account" in p or "ERC4337" in p or "ERC7579" in p or "ERC7739" in p or "ERC7821" in p:
        return "Account"
        
    # Check for access
    if "access" in p:
        return "Access"
        
    # Check for crosschain
    if "crosschain" in p or "bridge" in p or "ERC7786" in p or "ERC7802" in p:
        return "Crosschain"
        
    # Check for finance
    if "finance" in p or "vesting" in p:
        return "Finance"
        
    # Check for metatx
    if "metatx" in p:
        return "MetaTx"
        
    # Utilities
    if "utils" in p:
        return "Utils"
        
    # Mocks
    if "mocks" in p:
        return "Mocks"
        
    return "Other"

# Assign each dataset file to a domain
file_to_domain = {}
domain_files = defaultdict(list)
domain_counts = Counter()

for fp in dataset_files:
    dom = get_domain(fp)
    file_to_domain[fp] = dom
    domain_files[dom].append(fp)

for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    dom = file_to_domain[fp]
    domain_counts[dom] += 1

print("=== DOMAIN ASSIGNMENT SUMMARY ===")
print(f"Total files: {len(dataset_files)}, Total items: {len(oz_data)}")
for dom, count in domain_counts.most_common():
    files_in_dom = len(domain_files[dom])
    print(f"Domain: {dom:12} | Unique Files: {files_in_dom:3} | Items: {count:3}")

# Load the import graph we saved (or recreate it briefly)
# Let's inspect the imports crossing between domains
# We want to know: if file A in domain D1 imports file B in domain D2, what are D1 and D2?
import re
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"

all_sol_files = list(OZ_DIR.glob("**/*.sol"))
file_to_path = {}
for sf in all_sol_files:
    # normalize path relative to contracts/
    p = str(sf).replace("\\", "/")
    if "contracts/" in p:
        p = p.split("contracts/")[-1]
    file_to_path[p] = sf

import_regex = re.compile(r'import\s+(?:(?:\{[^\}]*\}|\*)\s+from\s+)?["\']([^"\']+)["\'];')
import_graph = defaultdict(set)

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
                    imp_rel = str(resolved.relative_to(OZ_DIR)).replace("\\", "/")
                except ValueError:
                    imp_rel = str(resolved).replace("\\", "/")
            if "contracts/" in imp_rel:
                imp_rel = imp_rel.split("contracts/")[-1]
            import_graph[rel].add(imp_rel)
    except Exception:
        pass

# Now check crossing imports between domains of dataset files
print("\n=== CROSSING IMPORTS BETWEEN DOMAINS (for dataset files) ===")
crossing_edges = Counter()

# Let's map dataset files to their domain in normalized form
norm_dataset_files = {}
for fp in dataset_files:
    norm_p = fp
    if "data/external/openzeppelin-contracts/contracts/" in fp:
        norm_p = fp.split("data/external/openzeppelin-contracts/contracts/")[-1]
    elif "contracts/" in fp:
        norm_p = fp.split("contracts/")[-1]
    norm_dataset_files[norm_p] = file_to_domain[fp]

for f_rel, dom_from in norm_dataset_files.items():
    imports = import_graph.get(f_rel, set())
    for imp in imports:
        # Check if the imported file is in the dataset or just a general OZ file
        if imp in norm_dataset_files:
            dom_to = norm_dataset_files[imp]
            if dom_from != dom_to:
                crossing_edges[(dom_from, dom_to)] += 1
        else:
            # Check what domain the imported file belongs to (even if not in dataset)
            dom_to = get_domain(imp)
            if dom_from != dom_to:
                crossing_edges[(dom_from, dom_to, "(non-dataset OZ file)")] += 1

print("\nDirect crossing imports:")
for edge, count in crossing_edges.most_common():
    if len(edge) == 2:
        print(f"  {edge[0]} -> {edge[1]}: {count} imports")
    else:
        print(f"  {edge[0]} -> {edge[1]} {edge[2]}: {count} imports")

