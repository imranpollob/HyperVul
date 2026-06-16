import json
import re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
oz_json_path = PROJECT_ROOT / "experiments" / "results" / "eval_clean_negatives_oz.json"
with open(oz_json_path) as f:
    oz_data = json.load(f)

dataset_files = set()
for item in oz_data:
    fp = item.get('file') or item.get('filePath')
    dataset_files.add(fp)

# Domain mapping function
def get_domain(path):
    p = str(path).replace("\\", "/")
    if "data/external/openzeppelin-contracts/contracts/" in p:
        p = p.split("data/external/openzeppelin-contracts/contracts/")[-1]
    elif "contracts/" in p:
        p = p.split("contracts/")[-1]
    parts = p.split("/")
    if "governance" in p:
        return "Governance"
    if "ERC20" in p:
        return "ERC20"
    if "ERC721" in p:
        return "ERC721"
    if "ERC1155" in p:
        return "ERC1155"
    if "account" in p or "ERC4337" in p or "ERC7579" in p or "ERC7739" in p or "ERC7821" in p:
        return "Account"
    if "access" in p:
        return "Access"
    if "crosschain" in p or "bridge" in p or "ERC7786" in p or "ERC7802" in p:
        return "Crosschain"
    if "finance" in p or "vesting" in p:
        return "Finance"
    if "metatx" in p:
        return "MetaTx"
    if "utils" in p:
        return "Utils"
    if "mocks" in p:
        return "Mocks"
    return "Other"

file_to_domain = {}
for fp in dataset_files:
    norm_p = fp
    if "data/external/openzeppelin-contracts/contracts/" in fp:
        norm_p = fp.split("data/external/openzeppelin-contracts/contracts/")[-1]
    elif "contracts/" in fp:
        norm_p = fp.split("contracts/")[-1]
    file_to_domain[norm_p] = get_domain(fp)

# Load imports
OZ_DIR = PROJECT_ROOT / "data" / "external" / "openzeppelin-contracts" / "contracts"
all_sol_files = list(OZ_DIR.glob("**/*.sol"))
file_to_path = {str(sf).split("contracts/")[-1].replace("\\", "/"): sf for sf in all_sol_files if "contracts/" in str(sf)}

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

print("=== DETAILED CROSS-DOMAIN IMPORTS IN DATASET ===")
for f_rel, dom_from in file_to_domain.items():
    imports = import_graph.get(f_rel, set())
    for imp in imports:
        if imp in file_to_domain:
            dom_to = file_to_domain[imp]
            if dom_from != dom_to:
                print(f"[{dom_from}] {f_rel} -> [{dom_to}] {imp}")

