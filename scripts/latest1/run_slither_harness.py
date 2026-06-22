import os
import re
import sys
import json
import subprocess
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))

# Target detectors in Slither
# Reentrancy: reentrancy-eth, reentrancy-no-eth, reentrancy-benign, reentrancy-events
# Unchecked call return: unchecked-lowlevel, unchecked-send, unchecked-transfer
DETECTORS_REENTRANCY = {"reentrancy-eth", "reentrancy-no-eth", "reentrancy-benign", "reentrancy-events"}
DETECTORS_UNCHECKED = {"unchecked-lowlevel", "unchecked-send", "unchecked-transfer"}

GLOBAL_FILE_MAP = defaultdict(list)

def build_global_file_map():
    global GLOBAL_FILE_MAP
    search_dirs = [PROJECT_ROOT / "data", PROJECT_ROOT / "data/external"]
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for root, _, files in os.walk(str(sdir)):
            if "scratch" in root:
                continue
            for f in files:
                if f.endswith(".sol"):
                    path = Path(root) / f
                    if path.resolve() not in GLOBAL_FILE_MAP[f]:
                        GLOBAL_FILE_MAP[f].append(path.resolve())

def find_sol_file(rel_path):
    prefixes = [
        PROJECT_ROOT,
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data/DAppSCAN",
        PROJECT_ROOT / "data/FORGE-Curated/dataset-curated/contracts"
    ]
    p = Path(rel_path)
    if p.exists():
        return p.resolve()
    for pref in prefixes:
        full_p = (Path(pref) / rel_path).resolve()
        if full_p.exists():
            return full_p
    # Walk and search
    name = Path(rel_path).name
    for root, dirs, files in os.walk(str(PROJECT_ROOT / "data")):
        for f in files:
            if f == name:
                full_p = Path(root) / f
                if str(full_p).endswith(rel_path):
                    return full_p.resolve()
    for root, dirs, files in os.walk(str(PROJECT_ROOT / "data")):
        for f in files:
            if f == name:
                return Path(root) / f
    return None

def get_project_root(file_path):
    parts = Path(file_path).parts
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] in ('contracts', 'dataset-curated'):
            return Path(*parts[:i+2])
    return Path(file_path).parent

def parse_imports(content):
    patterns = [
        r'import\s+["\']([^"\';]+)["\']\s*;',
        r'import\s+[^;]+\s+from\s+["\']([^"\']+)["\']\s*;'
    ]
    imports = []
    for pat in patterns:
        for match in re.finditer(pat, content):
            imports.append((match.group(0), match.group(1)))
    return imports

def score_path_match(candidate_path, import_path):
    import_parts = [p.lower() for p in import_path.replace("@", "").split("/") if p]
    candidate_str = str(candidate_path).lower()
    score = 0
    for ip in import_parts:
        if ip in candidate_str:
            score += 1
    return score

def resolve_import(import_path, current_dir, project_root):
    # 1. Try relative
    p = (current_dir / import_path).resolve()
    if p.exists():
        return p
    # 2. OpenZeppelin Mapping (non-upgradeable only)
    if import_path.startswith("@openzeppelin/contracts/"):
        rel = import_path.replace("@openzeppelin/contracts/", "")
        p = (PROJECT_ROOT / "data/external/openzeppelin-contracts/contracts" / rel).resolve()
        if p.exists():
            return p
    # 3. Recursive search in project root
    name = Path(import_path).name
    for root, dirs, files in os.walk(str(project_root)):
        if name in files:
            return (Path(root) / name).resolve()
    # 4. Global fallback with path scoring
    if name in GLOBAL_FILE_MAP:
        candidates = GLOBAL_FILE_MAP[name]
        best_candidate = max(candidates, key=lambda c: score_path_match(c, import_path))
        return best_candidate
    return None

def inline_file(file_path, project_root, inlined_files):
    file_path = Path(file_path).resolve()
    file_key = (file_path.parts[-2], file_path.name) if len(file_path.parts) >= 2 else file_path.name
    if file_key in inlined_files:
        return ""
    inlined_files.add(file_key)
    if not file_path.exists():
        return f"// Warning: imported file {file_path.name} not found\n"
    content = file_path.read_text(errors='ignore')
    content = re.sub(r'pragma\s+solidity\s+[^;]+;', '', content)
    content = re.sub(r'//\s*SPDX-License-Identifier:\s*[^\r\n]*', '', content)
    
    imports = parse_imports(content)
    for import_line, import_path in imports:
        resolved = resolve_import(import_path, file_path.parent, project_root)
        if resolved:
            inlined = inline_file(resolved, project_root, inlined_files)
            content = content.replace(import_line, inlined)
        else:
            content = content.replace(import_line, f"// Failed to resolve import: {import_line}")
    return content

def deduplicate_declarations(content):
    pattern = re.compile(r'\b(contract|interface|library|abstract\s+contract)\s+([A-Za-z0-9_]+)\s*(?:is\s+[^{]+)?\{')
    seen_names = set()
    pos = 0
    while True:
        match = pattern.search(content, pos)
        if not match:
            break
        
        decl_type = match.group(1)
        name = match.group(2)
        start_idx = match.start()
        open_brace_idx = match.end() - 1
        
        if name in seen_names:
            depth = 1
            close_brace_idx = -1
            for i in range(open_brace_idx + 1, len(content)):
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        close_brace_idx = i
                        break
            if close_brace_idx != -1:
                decl_len = close_brace_idx + 1 - start_idx
                replacement = f"/* Duplicate {decl_type} {name} removed */"
                if len(replacement) < decl_len:
                    replacement += " " * (decl_len - len(replacement))
                else:
                    replacement = replacement[:decl_len]
                content = content[:start_idx] + replacement + content[close_brace_idx + 1:]
                pos = start_idx + len(replacement)
                continue
        else:
            seen_names.add(name)
            
        pos = open_brace_idx + 1
        
    return content

def flatten_solidity_file(src_path, dst_path, solc_ver):
    project_root = get_project_root(src_path)
    inlined_files = set()
    src_key = (src_path.parts[-2], src_path.name) if len(src_path.parts) >= 2 else src_path.name
    inlined_files.add(src_key)
    content = src_path.read_text(errors='ignore')
    
    # Extract SPDX & pragma to prepend
    spdx = re.findall(r'//\s*SPDX-License-Identifier:\s*[^\r\n]*', content)
    
    content = re.sub(r'pragma\s+solidity\s+[^;]+;', '', content)
    content = re.sub(r'//\s*SPDX-License-Identifier:\s*[^\r\n]*', '', content)
    
    imports = parse_imports(content)
    for import_line, import_path in imports:
        resolved = resolve_import(import_path, src_path.parent, project_root)
        if resolved:
            inlined = inline_file(resolved, project_root, inlined_files)
            content = content.replace(import_line, inlined)
        else:
            content = content.replace(import_line, f"// Failed to resolve import: {import_line}")
            
    # Downgrade syntax to compile on 0.8.11
    # 1. Strip memory-safe annotation
    content = re.sub(r'assembly\s*\(\s*["\']memory-safe["\']\s*\)', 'assembly', content)
    # 2. Strip parameter labels in mappings: mapping(type label => type) -> mapping(type => type)
    for _ in range(5):
        content = re.sub(r'mapping\s*\(\s*([a-zA-Z0-9_.]+(?:\[\])?)\s+[a-zA-Z0-9_]+\s*=>', r'mapping(\1 =>', content)
    # 3. Strip transient storage keyword
    content = re.sub(r'\btransient\b', ' ', content)
    # 4. Convert require(cond, CustomError(...)) to if (!(cond)) revert CustomError(...)
    content = re.sub(
        r'require\s*\(([^;]*?),\s*([a-zA-Z0-9_.]+\s*\([\s\S]*?\))\s*\)\s*;',
        lambda m: f"if (!({m.group(1).strip()})) revert {m.group(2).strip()};",
        content
    )
    # 5. Convert abi.encodeCall(Interface.func, (args)) to abi.encodeWithSelector(Interface.func.selector, args)
    content = re.sub(
        r'abi\.encodeCall\s*\(\s*([a-zA-Z0-9_.]+)\s*,\s*\(([^)]*?)\)\s*\)',
        r'abi.encodeWithSelector(\1.selector, \2)',
        content
    )
    
    content = deduplicate_declarations(content)
    prefix = ""
    if spdx:
        prefix += spdx[0] + "\n"
    prefix += f"pragma solidity {solc_ver};\n"
        
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(prefix + content)

def get_installed_solc_versions():
    res = subprocess.run(["solc-select", "versions"], capture_output=True, text=True)
    versions = []
    for line in res.stdout.split("\n"):
        parts = line.strip().split()
        if parts:
            v = parts[0]
            # Strip suffix if any
            if v.endswith(" "):
                v = v[:-1]
            versions.append(v)
    return versions

def determine_solc_version(content, installed_versions):
    match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
    if not match:
        return "0.8.11"
    version_expr = match.group(1).strip()
    
    # Cap at 0.8.11 if it requires a newer version
    if any(x in version_expr for x in ["0.8.12", "0.8.13", "0.8.14", "0.8.15", "0.8.16", "0.8.17", "0.8.18", "0.8.19", "0.8.20", "0.8.21", "0.8.22", "0.8.23", "0.8.24", "0.8.25", "0.8.26"]):
        return "0.8.11"
        
    versions = re.findall(r'\d+\.\d+\.\d+', version_expr)
    if not versions:
        return "0.8.11"
    for v in installed_versions:
        if v in version_expr:
            return v
    first_v = versions[0]
    if first_v in installed_versions:
        return first_v
    parts = first_v.split('.')
    prefix = f"{parts[0]}.{parts[1]}."
    matches = [iv for iv in installed_versions if iv.startswith(prefix)]
    if matches:
        return matches[-1]
    return "0.8.11"

def run_slither(flat_file, solc_ver):
    solc_path = Path.home() / f".solc-select/artifacts/solc-{solc_ver}/solc-{solc_ver}"
    cmd = ["slither", str(flat_file)]
    if solc_path.exists():
        cmd += ["--solc", str(solc_path)]
    
    try_via_ir = False
    try:
        parts = [int(x) for x in solc_ver.split(".")]
        if len(parts) >= 3 and (parts[0] > 0 or parts[1] >= 8):
            try_via_ir = True
    except Exception:
        pass
        
    solc_args = ["--optimize"]
    if try_via_ir:
        solc_args.append("--experimental-via-ir")
        
    cmd_run = cmd + [f"--solc-args={' '.join(solc_args)}", "--json", "-"]
    res = subprocess.run(cmd_run, capture_output=True, text=True)
    
    data = None
    try:
        data = json.loads(res.stdout)
    except Exception:
        match = re.search(r'\{.*\}', res.stdout, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except Exception:
                pass
                
    # Fallback: if failed and we tried via-ir, try without via-ir
    if data is None and try_via_ir:
        solc_args = ["--optimize"]
        cmd_run = cmd + [f"--solc-args={' '.join(solc_args)}", "--json", "-"]
        res = subprocess.run(cmd_run, capture_output=True, text=True)
        try:
            data = json.loads(res.stdout)
        except Exception:
            match = re.search(r'\{.*\}', res.stdout, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    pass
                    
    return data

def main():
    print("Building global file map...")
    build_global_file_map()
    print("Starting Slither Comparison Harness...")
    test_json_path = PROJECT_ROOT / "data" / "splits" / "test_features.json"
    if not test_json_path.exists():
        print(f"Error: test split file not found at {test_json_path}")
        sys.exit(1)
        
    with open(test_json_path) as f:
        test_items = json.load(f)
        
    # Group by file path to run Slither once per contract
    items_by_file = defaultdict(list)
    for item in test_items:
        fp = item.get("file") or item.get("filePath")
        items_by_file[fp].append(item)
        
    installed_versions = get_installed_solc_versions()
    flat_dir = PROJECT_ROOT / "scratch" / "flat_test_contracts"
    
    slither_predictions = {}
    
    success_count = 0
    total_files = len(items_by_file)
    
    for idx, (rel_path, items) in enumerate(items_by_file.items(), 1):
        print(f"[{idx}/{total_files}] Processing: {rel_path}")
        full_path = find_sol_file(rel_path)
        if not full_path:
            print(f"  Warning: Could not locate file {rel_path} in workspace.")
            continue
            
        flat_content_temp = full_path.read_text(errors='ignore')
        solc_ver = determine_solc_version(flat_content_temp, installed_versions)
        print(f"  Solc version: {solc_ver}")
        
        flat_path = flat_dir / f"{full_path.stem}_flat.sol"
        try:
            flatten_solidity_file(full_path, flat_path, solc_ver)
        except Exception as e:
            print(f"  Warning: Flattening failed: {e}")
            continue
        
        slither_out = run_slither(flat_path, solc_ver)
        if not slither_out:
            print(f"  Warning: Slither failed to analyze contract.")
            continue
            
        success_count += 1
        
        # Analyze findings
        detectors = slither_out.get("results", {}).get("detectors", [])
        
        # Build mapping of flagged functions
        flagged_functions = defaultdict(set) # detector_category -> set of (contract, function)
        for det in detectors:
            det_name = det.get("check")
            category = None
            if det_name in DETECTORS_REENTRANCY:
                category = "reentrancy"
            elif det_name in DETECTORS_UNCHECKED:
                category = "unchecked"
                
            if category:
                for elem in det.get("elements", []):
                    if elem.get("type") == "function":
                        func_name = elem.get("name")
                        contract_name = elem.get("contract", {}).get("name")
                        if not contract_name:
                            contract_name = elem.get("type_specific_fields", {}).get("parent", {}).get("name")
                        flagged_functions[category].add((contract_name, func_name))
                        
        # Store predictions for the items
        for item in items:
            contract = item.get("contract")
            func = item.get("function") or item.get("ast_function")
            vtype = item.get("vtype") or "Unknown"
            
            # Predict based on vuln type
            pred = 0
            if "reentrancy" in vtype.lower() or "swc-107" in vtype.lower():
                if func is None:
                    if any(c == contract for (c, f) in flagged_functions["reentrancy"]):
                        pred = 1
                else:
                    if (contract, func) in flagged_functions["reentrancy"]:
                        pred = 1
            elif "unchecked" in vtype.lower() or "swc-104" in vtype.lower():
                if func is None:
                    if any(c == contract for (c, f) in flagged_functions["unchecked"]):
                        pred = 1
                else:
                    if (contract, func) in flagged_functions["unchecked"]:
                        pred = 1
            else:
                # Other types
                if func is None:
                    if any(c == contract for (c, f) in flagged_functions["reentrancy"]) or any(c == contract for (c, f) in flagged_functions["unchecked"]):
                        pred = 1
                else:
                    if (contract, func) in flagged_functions["reentrancy"] or (contract, func) in flagged_functions["unchecked"]:
                        pred = 1
            
            slither_predictions[f"{rel_path}::{contract}::{func}"] = pred
            
    print(f"\nSuccessfully compiled and analyzed {success_count}/{total_files} files with Slither.")
    
    # Calculate performance metrics
    y_true = []
    y_pred = []
    
    for item in test_items:
        fp = item.get("file") or item.get("filePath")
        contract = item.get("contract")
        func = item.get("function") or item.get("ast_function")
        label = int(item.get("label", 0))
        
        key = f"{fp}::{contract}::{func}"
        pred = slither_predictions.get(key, 0)
        
        y_true.append(label)
        y_pred.append(pred)
        
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    f2 = 5 * precision * recall / (4 * precision + recall) if (4 * precision + recall) > 0 else 0.0
    
    print(f"\n=== Slither Test Performance ===")
    print(f"TP: {tp}, FP: {fp}, FN: {fn}, TN: {tn}")
    print(f"Precision: {precision*100:.2f}%")
    print(f"Recall: {recall*100:.2f}%")
    print(f"F1-Score: {f1*100:.2f}%")
    print(f"F2-Score: {f2*100:.2f}%")
    
    # Save results to experiments/latest1/slither_comparison_results.json
    res_dict = {
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "precision": float(precision), "recall": float(recall), "f1": float(f1), "f2": float(f2),
        "probs": y_pred.tolist(),
        "labels": y_true.tolist(),
        "ids": [f"{item.get('contract')}::{item.get('function') or item.get('ast_function')}" for item in test_items]
    }
    with open(PROJECT_ROOT / "experiments/latest1/slither_comparison_results.json", "w") as fh:
        json.dump(res_dict, fh, indent=2)
    print("Saved Slither results to experiments/latest1/slither_comparison_results.json")

if __name__ == "__main__":
    import numpy as np
    main()
