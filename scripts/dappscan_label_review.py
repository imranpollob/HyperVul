#!/usr/bin/env python3
"""
HyperVul — DAppSCAN Label Quality Review
==========================================

Extracts evidence for human review of DAppSCAN positive hyperedges.
Produces experiments/results/dappscan_label_review.md with:
  1. SWC annotation metadata
  2. Actual function source code
  3. Constructed hyperedge components
  4. Pre-classification (CONFIRMED, MISLOCATED, COMMIT_DRIFT, DUBIOUS)

Scope priority:
  1. TEST split DAppSCAN cross-contract positives
  2. All DAppSCAN cross-contract positives (val + train)
  3. DAppSCAN intra-contract positives
"""

import json
import sys
import hashlib
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import tree_sitter as ts
import tree_sitter_solidity as tss

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))

import negative_hyperedge_sampling as nhs

DAPPSCAN_ROOT = PROJECT_ROOT / "data" / "DAppSCAN"
SWC_SOURCE_DIR = DAPPSCAN_ROOT / "DAppSCAN-source" / "SWCsource"
CONTRACTS_ROOT = DAPPSCAN_ROOT / "DAppSCAN-source" / "contracts"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)

INTERACTION_SWCS = {"SWC-107", "SWC-114", "SWC-104", "SWC-112"}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def is_dappscan(item):
    """Check if an item comes from DAppSCAN."""
    return (item.get('source') == 'DAppSCAN' or
            'dappscan' in str(item.get('file', '')).lower() or
            'dappscan' in str(item.get('filePath', '')).lower() or
            'project_root' in item)


def get_filepath(item):
    """Get the file path from an item (handles both 'file' and 'filePath' keys)."""
    return item.get('filePath') or item.get('file') or ''


def get_func_name(item):
    """Get the function name from an item."""
    return item.get('annotated_function') or item.get('ast_function') or item.get('function') or ''


def find_project_root_safe(filepath):
    """Find project root, returning None on failure."""
    full_path = DAPPSCAN_ROOT / filepath
    try:
        return nhs.find_project_root(full_path)
    except Exception:
        parts = Path(filepath).parts
        if len(parts) >= 3:
            candidate = DAPPSCAN_ROOT / parts[0] / parts[1] / parts[2]
            if candidate.is_dir():
                return candidate
        return None


def load_project_contracts(proj_root):
    """Load and parse all .sol files in a project root."""
    all_contracts = {}
    if proj_root and proj_root.exists():
        for sol_file in proj_root.glob("**/*.sol"):
            try:
                with open(sol_file, "r", encoding="utf-8", errors="ignore") as fh:
                    source = fh.read()
                all_contracts.update(nhs.parse_contracts(source))
            except Exception:
                pass
    return all_contracts


def get_function_source_and_node(item, all_contracts=None):
    """
    Retrieve the actual function source code and AST node for a DAppSCAN item.
    Returns (source_text, func_node, file_source) or (None, None, None).
    """
    filepath = get_filepath(item)
    contract = item['contract']
    func_name = get_func_name(item)

    full_path = DAPPSCAN_ROOT / filepath
    if not full_path.exists():
        return None, None, None

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            file_source = fh.read()
    except Exception:
        return None, None, None

    if all_contracts is None:
        proj_root = find_project_root_safe(filepath)
        all_contracts = load_project_contracts(proj_root)

    # Also parse the specific file
    file_contracts = nhs.parse_contracts(file_source)
    merged = dict(all_contracts)
    merged.update(file_contracts)

    try:
        all_funcs = nhs.resolve_all_functions(contract, merged)
        if func_name in all_funcs:
            func_node = all_funcs[func_name]
            return nhs.node_text(func_node), func_node, file_source
    except Exception:
        pass

    return None, None, file_source


def find_swc_annotation(filepath, func_name):
    """
    Find the original SWC annotation JSON for a given file and function.
    Returns the SWC entry dict or None.
    """
    # The SWC annotation mirrors the contracts directory structure
    # filepath looks like: DAppSCAN-source/contracts/Org-Project/...file.sol
    # SWC annotation is at: DAppSCAN-source/SWCsource/Org-Project/...file.json
    rel = filepath
    if rel.startswith("DAppSCAN-source/contracts/"):
        swc_rel = rel.replace("DAppSCAN-source/contracts/", "DAppSCAN-source/SWCsource/", 1)
    else:
        swc_rel = rel

    # Change .sol to .json
    swc_path = DAPPSCAN_ROOT / swc_rel.replace(".sol", ".json")

    if not swc_path.exists():
        # Try searching more broadly
        parts = Path(filepath).parts
        if len(parts) >= 4:
            # Try: SWCsource / org-project / subdir... / file.json
            org_project = parts[2]  # e.g., "Coinbae-TapCoins_Token_Contract"
            search_dir = SWC_SOURCE_DIR / org_project
            if search_dir.exists():
                stem = Path(filepath).stem
                for candidate in search_dir.glob(f"**/{stem}.json"):
                    swc_path = candidate
                    break

    if not swc_path.exists():
        return None

    try:
        with open(swc_path) as f:
            data = json.load(f)
        for swc in data.get("SWCs", []):
            cat = swc.get("category", "")
            ann_func = swc.get("function", "")
            # Match by function name
            if ann_func == func_name:
                parts = cat.split("-")
                swc_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else cat
                if swc_code in INTERACTION_SWCS:
                    return swc
        # If no exact match, return any interaction SWC in range
        for swc in data.get("SWCs", []):
            cat = swc.get("category", "")
            parts = cat.split("-")
            swc_code = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else cat
            if swc_code in INTERACTION_SWCS:
                return swc
    except Exception:
        pass

    return None


def reconstruct_hyperedge(item, func_node, file_source, all_contracts):
    """
    Attempt to reconstruct the hyperedge from the function AST.
    Returns a dict with the hyperedge components and a consistency check.
    """
    contract = item['contract']
    func_name = get_func_name(item)
    original_state_vars = item.get('state_vars_accessed', [])
    original_ext_calls = item.get('external_calls', [])
    original_is_cc = item.get('is_cross_contract', False)

    result = {
        'func_name': func_name,
        'contract': contract,
        'original_state_vars': original_state_vars,
        'original_ext_calls': original_ext_calls,
        'original_is_cross_contract': original_is_cc,
        'reconstructed_state_vars': [],
        'reconstructed_ext_calls': [],
        'reconstructed_is_cross_contract': False,
        'state_vars_match': False,
        'ext_calls_match': False,
        'cc_match': False,
        'hyperedge_constructable': False,
    }

    if func_node is None:
        return result

    try:
        # Resolve state vars
        all_state_vars = nhs.resolve_all_state_vars(contract, all_contracts)
        local_vars = nhs.extract_local_vars(func_node)
        state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)

        # Find state var accesses
        accessed = nhs.find_state_var_accesses(func_node, all_state_vars, local_vars)
        result['reconstructed_state_vars'] = accessed

        # Find external calls
        ext_calls = nhs.find_external_calls_ast(func_node, state_var_types, all_contracts)
        result['reconstructed_ext_calls'] = ext_calls

        # Determine cross-contract
        is_cc = any(
            c.get('receiver') not in (contract, 'this', '(complex)')
            and c.get('receiver') not in all_contracts.get(contract, nhs.ContractInfo(contract, None)).base_names
            for c in ext_calls
        ) if ext_calls else False
        result['reconstructed_is_cross_contract'] = is_cc

        # Consistency checks
        result['state_vars_match'] = set(original_state_vars) == set(accessed)
        orig_methods = {c.get('method') for c in original_ext_calls}
        recon_methods = {c.get('method') for c in ext_calls}
        result['ext_calls_match'] = orig_methods == recon_methods
        result['cc_match'] = original_is_cc == is_cc
        result['hyperedge_constructable'] = len(accessed) > 0 and len(ext_calls) > 0

    except Exception as e:
        result['error'] = str(e)

    return result


def classify_item(item, func_source, func_node, file_source, all_contracts, hyperedge_info):
    """
    Pre-classify the label quality of a DAppSCAN positive.
    Returns one of: CONFIRMED, MISLOCATED, COMMIT_DRIFT, DUBIOUS, and a reason.
    """
    func_name = get_func_name(item)
    category = item.get('category', '')
    swc_code = item.get('swc_code', '')

    # If we can't even find the function source, it's COMMIT_DRIFT
    if func_source is None:
        return "COMMIT_DRIFT", "Function not found in current source file"

    # If the hyperedge is not constructable, mark as DUBIOUS
    if not hyperedge_info['hyperedge_constructable']:
        if not hyperedge_info['reconstructed_ext_calls']:
            return "DUBIOUS", "No external calls found in function AST — no interaction to be vulnerable"
        if not hyperedge_info['reconstructed_state_vars']:
            return "DUBIOUS", "No state variable accesses found — no state to exploit"

    # Check if the vulnerability type matches the code pattern
    # SWC-107 (Reentrancy): needs external call + state write AFTER the call
    # SWC-112 (Delegatecall to Untrusted Callee): needs delegatecall specifically
    # SWC-104 (Unchecked Call Return Value): any external call whose return isn't checked
    # SWC-114 (Transaction Order Dependence / Front-running): needs state-dependent external call

    if "107" in swc_code or "reentrancy" in category.lower():
        # Check for reentrancy pattern: external call + state modification
        has_ext_call = len(hyperedge_info['reconstructed_ext_calls']) > 0
        has_state_var = len(hyperedge_info['reconstructed_state_vars']) > 0

        if has_ext_call and has_state_var:
            # Check if there's a state write after an external call
            # (simplified check — just verify both exist in the function)
            if _has_state_write_after_ext_call(func_source, hyperedge_info):
                return "CONFIRMED", "Reentrancy pattern present: external call + state modification in function"
            else:
                # State reads but no writes after call — weaker evidence
                return "CONFIRMED", "External call + state access present; state-write-after-call ordering not verified from source alone"
        elif has_ext_call and not has_state_var:
            return "DUBIOUS", "External call found but no state variable access — no state to exploit via reentrancy"
        else:
            return "DUBIOUS", "No external call found — reentrancy not possible"

    elif "112" in swc_code or "delegatecall" in category.lower():
        # SWC-112: Delegatecall to Untrusted Callee
        has_delegatecall = any(
            'delegatecall' in c.get('method', '') or 'delegatecall' in c.get('call_text', '')
            for c in hyperedge_info['reconstructed_ext_calls']
        )
        if has_delegatecall:
            return "CONFIRMED", "delegatecall found in function"
        else:
            # Check source directly
            if 'delegatecall' in func_source:
                return "CONFIRMED", "delegatecall found in function source text"
            else:
                return "MISLOCATED", "No delegatecall in function — vulnerability may be in a different function"

    elif "104" in swc_code or "unchecked" in category.lower():
        # SWC-104: Unchecked Call Return Value — applies to external calls whose
        # boolean/bytes return is not checked. The canonical case is ERC20
        # transfer()/transferFrom()/approve() returning false silently.
        #
        # Key distinction: read-only queries (balanceOf, getPrice) in a view function
        # are NOT genuine SWC-104 — they can't cause state corruption.
        has_low_level = any(
            c.get('method') in ('call', 'send', 'delegatecall', 'staticcall')
            or 'low-level' in c.get('reason', '')
            for c in hyperedge_info['reconstructed_ext_calls']
        )
        # ERC20/value-transfer methods whose return value, if unchecked, causes real harm
        VALUE_TRANSFER_METHODS = {
            'transfer', 'transferFrom', 'approve',
            'safeTransfer', 'safeTransferFrom', 'safeApprove',
            'sendETH', 'returnData',
        }
        has_value_transfer = any(
            c.get('method') in VALUE_TRANSFER_METHODS
            for c in hyperedge_info['reconstructed_ext_calls']
        )
        # Read-only methods whose "unchecked return" is cosmetic, not exploitable
        READ_ONLY_METHODS = {
            'balanceOf', 'allowance', 'getPrice', 'latestAnswer', 'latestRoundData',
            'getPricePerFullShare', 'get_virtual_price',
            'getSharesByPooledEth', 'getPooledEthByShares',
            'getLUSDDebt', 'totalSupply', 'decimals', 'symbol', 'name',
            'slot0', 'positions', 'computeAddress',
        }
        only_reads = all(
            c.get('method') in READ_ONLY_METHODS or
            c.get('method') in ('mul', 'div', 'add', 'sub')  # SafeMath
            for c in hyperedge_info['reconstructed_ext_calls']
        )
        # Check if the function is a view/pure function
        is_view = func_source and ('view' in func_source.split('{')[0] or 'pure' in func_source.split('{')[0]) if func_source else False

        if has_low_level:
            return "CONFIRMED", "Low-level call found — unchecked return value vulnerability plausible"
        elif has_value_transfer:
            return "CONFIRMED", "Value-transfer call (transfer/transferFrom/approve) with potentially unchecked return (SWC-104)"
        elif is_view and only_reads:
            return "DUBIOUS", "View/pure function with only read-only external calls — unchecked return has no state impact"
        elif only_reads:
            return "DUBIOUS", "Only read-only external calls found — unchecked return unlikely to be exploitable"
        elif hyperedge_info['hyperedge_constructable']:
            return "CONFIRMED", "External call present — unchecked return value plausible"
        else:
            return "DUBIOUS", "No external call found for unchecked return value"

    elif "114" in swc_code or "front" in category.lower() or "transaction order" in category.lower():
        # SWC-114: Transaction Order Dependence (front-running)
        # Genuine front-running requires: reading state -> making decision ->
        # executing external call, where a miner/frontrunner can interleave
        has_ext_call = len(hyperedge_info['reconstructed_ext_calls']) > 0
        has_state_var = len(hyperedge_info['reconstructed_state_vars']) > 0
        if has_ext_call and has_state_var:
            return "CONFIRMED", "State-dependent external call present — front-running plausible"
        elif has_ext_call:
            return "CONFIRMED", "External call present — transaction ordering could be exploited"
        else:
            return "DUBIOUS", "No external call found — front-running not applicable"

    # Default: if hyperedge is constructable, lean towards CONFIRMED
    if hyperedge_info['hyperedge_constructable']:
        return "CONFIRMED", "Hyperedge constructable; vulnerability type not specifically verified"
    else:
        return "DUBIOUS", "Hyperedge not constructable"


def _has_state_write_after_ext_call(func_source, hyperedge_info):
    """
    Heuristic check: does the function source contain a state variable
    assignment after an external call? Very simplified — checks if any
    state var appears on the left side of an assignment.
    """
    # This is a rough heuristic for the review sheet
    ext_calls = hyperedge_info['reconstructed_ext_calls']
    state_vars = hyperedge_info['reconstructed_state_vars']

    if not ext_calls or not state_vars:
        return False

    # Look for any state var followed by '=' (assignment) in the source
    for sv in state_vars:
        # Pattern: state_var = or state_var[...] = or state_var +=, etc.
        pattern = rf'\b{re.escape(sv)}\b\s*[\[.]?[^\n]*\s*[+\-*\/]?='
        if re.search(pattern, func_source):
            return True

    return False


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("HyperVul — DAppSCAN Label Quality Review")
    print("=" * 80)

    # Load all splits
    with open(SPLITS_DIR / "test.json") as f:
        test_data = json.load(f)
    with open(SPLITS_DIR / "val.json") as f:
        val_data = json.load(f)
    with open(SPLITS_DIR / "train.json") as f:
        train_data = json.load(f)

    # Collect DAppSCAN positives by priority group
    groups = []

    # Group 1: TEST cross-contract DAppSCAN positives
    test_cc = [i for i in test_data if is_dappscan(i) and i.get('label') == 1 and i.get('is_cross_contract')]
    groups.append(("TEST Cross-Contract", test_cc))

    # Group 2: VAL cross-contract DAppSCAN positives
    val_cc = [i for i in val_data if is_dappscan(i) and i.get('label') == 1 and i.get('is_cross_contract')]
    groups.append(("VAL Cross-Contract", val_cc))

    # Group 3: TRAIN cross-contract DAppSCAN positives
    train_cc = [i for i in train_data if is_dappscan(i) and i.get('label') == 1 and i.get('is_cross_contract')]
    groups.append(("TRAIN Cross-Contract", train_cc))

    # Group 4: TEST intra-contract DAppSCAN positives
    test_ic = [i for i in test_data if is_dappscan(i) and i.get('label') == 1 and not i.get('is_cross_contract')]
    groups.append(("TEST Intra-Contract", test_ic))

    # Group 5: VAL intra-contract DAppSCAN positives
    val_ic = [i for i in val_data if is_dappscan(i) and i.get('label') == 1 and not i.get('is_cross_contract')]
    groups.append(("VAL Intra-Contract", val_ic))

    # Group 6: TRAIN intra-contract DAppSCAN positives
    train_ic = [i for i in train_data if is_dappscan(i) and i.get('label') == 1 and not i.get('is_cross_contract')]
    groups.append(("TRAIN Intra-Contract", train_ic))

    for gname, items in groups:
        print(f"  {gname}: {len(items)} items")

    # Process all items and collect review entries
    all_reviews = []
    project_cache = {}  # project_root -> contracts dict

    for group_name, items in groups:
        print(f"\n{'='*60}")
        print(f"Processing: {group_name} ({len(items)} items)")
        print(f"{'='*60}")

        for idx, item in enumerate(items):
            filepath = get_filepath(item)
            contract = item['contract']
            func_name = get_func_name(item)

            print(f"  [{idx+1}/{len(items)}] {contract}.{func_name} in {Path(filepath).name}")

            # Get project contracts (cached)
            proj_root = find_project_root_safe(filepath)
            proj_key = str(proj_root) if proj_root else filepath
            if proj_key not in project_cache:
                project_cache[proj_key] = load_project_contracts(proj_root)
            all_contracts = project_cache[proj_key]

            # Get function source
            func_source, func_node, file_source = get_function_source_and_node(item, all_contracts)

            # Find SWC annotation
            swc_ann = find_swc_annotation(filepath, func_name)

            # Reconstruct hyperedge
            # Merge file-level contracts
            if file_source:
                file_contracts = nhs.parse_contracts(file_source)
                merged = dict(all_contracts)
                merged.update(file_contracts)
            else:
                merged = all_contracts

            hyperedge_info = reconstruct_hyperedge(item, func_node, file_source, merged)

            # Classify
            classification, reason = classify_item(
                item, func_source, func_node, file_source, merged, hyperedge_info
            )

            review_entry = {
                'group': group_name,
                'index': idx,
                'filepath': filepath,
                'contract': contract,
                'function': func_name,
                'swc_code': item.get('swc_code', ''),
                'category': item.get('category', ''),
                'lineNumber': item.get('lineNumber', ''),
                'is_cross_contract': item.get('is_cross_contract', False),
                'swc_annotation': swc_ann,
                'func_source': func_source,
                'func_source_lines': len(func_source.split('\n')) if func_source else 0,
                'hyperedge': hyperedge_info,
                'classification': classification,
                'classification_reason': reason,
                'state_vars_accessed': item.get('state_vars_accessed', []),
                'external_calls': item.get('external_calls', []),
                'normalized_source_hash': item.get('normalized_source_hash', ''),
            }
            all_reviews.append(review_entry)

            print(f"    → {classification}: {reason}")

    # Save raw JSON for programmatic use
    raw_path = RESULTS_DIR / "dappscan_label_review_raw.json"
    with open(raw_path, "w") as f:
        json.dump(all_reviews, f, indent=2, default=str)
    print(f"\nSaved raw review data to {raw_path}")

    # Generate markdown report
    generate_report(all_reviews, groups)

    print(f"\nLabel review complete!")


def generate_report(all_reviews, groups):
    """Generate the markdown review report."""
    lines = []
    lines.append("# DAppSCAN Label Quality Review")
    lines.append("")
    lines.append("This document presents evidence for human review of DAppSCAN positive hyperedges.")
    lines.append("Each entry includes the SWC annotation, function source, hyperedge components,")
    lines.append("and a pre-classification. **Human reviewers should verify each classification.**")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")

    # Overall stats
    class_counts = Counter(r['classification'] for r in all_reviews)
    lines.append(f"**Total items reviewed**: {len(all_reviews)}")
    lines.append("")
    lines.append("| Classification | Count | % |")
    lines.append("|---|---|---|")
    for cls in ["CONFIRMED", "MISLOCATED", "COMMIT_DRIFT", "DUBIOUS"]:
        count = class_counts.get(cls, 0)
        pct = count / len(all_reviews) * 100 if all_reviews else 0
        lines.append(f"| {cls} | {count} | {pct:.1f}% |")
    lines.append("")

    # Per-group stats
    lines.append("### By Group")
    lines.append("")
    lines.append("| Group | Total | CONFIRMED | MISLOCATED | COMMIT_DRIFT | DUBIOUS |")
    lines.append("|---|---|---|---|---|---|")
    for group_name, _ in groups:
        group_items = [r for r in all_reviews if r['group'] == group_name]
        if not group_items:
            continue
        gc = Counter(r['classification'] for r in group_items)
        lines.append(f"| {group_name} | {len(group_items)} | {gc.get('CONFIRMED',0)} | {gc.get('MISLOCATED',0)} | {gc.get('COMMIT_DRIFT',0)} | {gc.get('DUBIOUS',0)} |")
    lines.append("")

    # Detailed entries — prioritize TEST cross-contract
    for group_name, _ in groups:
        group_items = [r for r in all_reviews if r['group'] == group_name]
        if not group_items:
            continue

        lines.append(f"---")
        lines.append(f"## {group_name} ({len(group_items)} items)")
        lines.append("")

        for entry in group_items:
            lines.append(f"### {entry['contract']}.{entry['function']}")
            lines.append("")

            # Classification badge
            cls = entry['classification']
            if cls == "CONFIRMED":
                badge = "✅ CONFIRMED"
            elif cls == "MISLOCATED":
                badge = "⚠️ MISLOCATED"
            elif cls == "COMMIT_DRIFT":
                badge = "🔄 COMMIT_DRIFT"
            else:
                badge = "❌ DUBIOUS"
            lines.append(f"**Pre-classification**: {badge}")
            lines.append(f"**Reason**: {entry['classification_reason']}")
            lines.append("")

            # SWC Annotation
            lines.append("#### 1. SWC Annotation")
            lines.append(f"- **Category**: {entry['category']}")
            lines.append(f"- **SWC Code**: {entry['swc_code']}")
            lines.append(f"- **Annotated Function**: {entry['function']}")
            lines.append(f"- **Line Range**: {entry['lineNumber']}")
            lines.append(f"- **File**: `{entry['filepath']}`")
            if entry['swc_annotation']:
                ann = entry['swc_annotation']
                lines.append(f"- **Original SWC entry**: category=`{ann.get('category')}`, function=`{ann.get('function')}`, lines=`{ann.get('lineNumber')}`")
            else:
                lines.append("- **Original SWC entry**: ⚠️ Not found in SWC annotation files")
            lines.append("")

            # Function Source
            lines.append("#### 2. Function Source Code")
            if entry['func_source']:
                # Truncate very long functions for readability
                src = entry['func_source']
                src_lines = src.split('\n')
                if len(src_lines) > 60:
                    shown = '\n'.join(src_lines[:30] + ['    // ... truncated ...'] + src_lines[-15:])
                    lines.append(f"({entry['func_source_lines']} lines, showing first 30 + last 15)")
                else:
                    shown = src
                lines.append("```solidity")
                lines.append(shown)
                lines.append("```")
            else:
                lines.append("> ⚠️ **Function source not found** — possible commit drift or file restructuring")
            lines.append("")

            # Hyperedge Components
            lines.append("#### 3. Hyperedge Components")
            lines.append("")
            lines.append("**Recorded in dataset:**")
            lines.append(f"- **State variables**: {entry['state_vars_accessed']}")
            ext_calls_str = []
            for c in entry['external_calls']:
                ext_calls_str.append(f"`{c.get('call_text', '?')}` (method: {c.get('method', '?')}, receiver: {c.get('receiver', '?')})")
            lines.append(f"- **External calls**: {', '.join(ext_calls_str) if ext_calls_str else 'None'}")
            lines.append(f"- **Cross-contract**: {entry['is_cross_contract']}")
            lines.append("")

            he = entry['hyperedge']
            lines.append("**Reconstructed from current AST:**")
            lines.append(f"- **State variables**: {he['reconstructed_state_vars']}")
            recon_calls_str = []
            for c in he['reconstructed_ext_calls']:
                recon_calls_str.append(f"`{c.get('call_text', '?')}` ({c.get('reason', '?')})")
            lines.append(f"- **External calls**: {', '.join(recon_calls_str) if recon_calls_str else 'None'}")
            lines.append(f"- **Cross-contract**: {he['reconstructed_is_cross_contract']}")
            lines.append(f"- **Hyperedge constructable**: {he['hyperedge_constructable']}")
            lines.append("")

            # Consistency
            lines.append("**Consistency checks:**")
            sv_match = "✅" if he['state_vars_match'] else "❌"
            ec_match = "✅" if he['ext_calls_match'] else "❌"
            cc_match = "✅" if he['cc_match'] else "❌"
            lines.append(f"- State vars match: {sv_match}")
            lines.append(f"- External calls match: {ec_match}")
            lines.append(f"- Cross-contract match: {cc_match}")
            lines.append("")

    report_content = "\n".join(lines)
    report_path = RESULTS_DIR / "dappscan_label_review.md"
    with open(report_path, "w") as f:
        f.write(report_content)
    print(f"Saved review report to {report_path}")


if __name__ == '__main__':
    main()
