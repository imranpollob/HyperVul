#!/usr/bin/env python3
"""
HyperVul — Label Correction Proposal: SWC-104 View/Pure Rule
==============================================================

Applies a general, model-blind correction rule to identify invalid SWC-104
annotations across the ENTIRE dataset (FORGE + DAppSCAN, all splits).

RULE: An SWC-104 (Unchecked Call Return Value) annotation is INVALID if:
  (a) The annotated function is declared `view` or `pure` (cannot modify state), AND
  (b) All of its external calls are read-only (getter/price queries returning a
      value used locally, not state-changing calls whose return is ignored).

This script does NOT reference the model's predictions when applying the rule.
Model predictions are cross-referenced separately for transparency only (Step 4).
"""

import json
import sys
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import tree_sitter as ts
import tree_sitter_solidity as tss
import torch
import numpy as np

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "scripts"))

import negative_hyperedge_sampling as nhs

DAPPSCAN_ROOT = PROJECT_ROOT / "data" / "DAppSCAN"
FORGE_VULN_DIR = PROJECT_ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"

LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)

# ---------------------------------------------------------------------------
# KNOWN READ-ONLY METHODS
# These are methods whose return value is consumed locally and which do not
# modify contract state. Missing a return check on these cannot cause
# state corruption — the value is simply used in a computation.
# ---------------------------------------------------------------------------
READ_ONLY_METHODS = {
    # ERC20 getters
    "balanceOf", "allowance", "totalSupply", "decimals", "symbol", "name",
    # Price oracles
    "getPrice", "latestAnswer", "latestRoundData", "latestRound",
    "getRoundData", "getLatestPrice",
    # DeFi read-only
    "getPricePerFullShare", "get_virtual_price", "virtualPrice",
    "getSharesByPooledEth", "getPooledEthByShares",
    "getReserves", "getAmountsOut", "getAmountsIn",
    "getLUSDDebt", "getEntireSystemDebt",
    "getCollateral", "getDebt",
    "slot0", "positions", "computeAddress",
    # SafeMath library methods (not external at all, but tree-sitter picks them up)
    "mul", "div", "add", "sub", "mod",
}

# ---------------------------------------------------------------------------
# STATE-CHANGING METHODS (whose unchecked return IS a real SWC-104)
# ---------------------------------------------------------------------------
STATE_CHANGING_METHODS = {
    # Token transfers
    "transfer", "transferFrom", "approve", "permit",
    "safeTransfer", "safeTransferFrom", "safeApprove",
    # Low-level
    "call", "send", "delegatecall", "staticcall",
    # State-changing DeFi operations
    "deposit", "withdraw", "borrow", "repay", "liquidate",
    "mint", "burn", "burnFrom",
    "swap", "flash", "flashLoan",
    "sendETH", "execute",
    "increaseAllowance", "decreaseAllowance",
    "safeIncreaseAllowance", "safeDecreaseAllowance",
}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def is_dappscan(item):
    return (item.get('source') == 'DAppSCAN' or
            'dappscan' in str(item.get('file', '')).lower() or
            'dappscan' in str(item.get('filePath', '')).lower() or
            'project_root' in item)


def get_filepath(item):
    return item.get('filePath') or item.get('file') or ''


def get_func_name(item):
    return (item.get('annotated_function') or item.get('ast_function') or
            item.get('function') or '')


def get_swc_code(item):
    """Extract SWC code from item, handling both FORGE and DAppSCAN formats."""
    swc = item.get('swc_code', '')
    if not swc:
        vtype = item.get('vtype', '') or item.get('category', '')
        if '104' in vtype:
            swc = 'SWC-104'
        elif '107' in vtype:
            swc = 'SWC-107'
        elif '114' in vtype:
            swc = 'SWC-114'
        elif '112' in vtype:
            swc = 'SWC-112'
    return swc


def get_source_type(item):
    if is_dappscan(item):
        return "DAppSCAN"
    return "FORGE"


# Project-level contract cache
project_cache = {}
vfp_data = {}

def load_vfp_data():
    """Load all FORGE VFP files."""
    global vfp_data
    for p in FORGE_VULN_DIR.glob('*.json'):
        with open(p) as f:
            vfp_data[p.stem] = json.load(f)


def find_project_root_safe(filepath):
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


def get_function_source_for_item(item):
    """
    Retrieve the function source code for any item (DAppSCAN or FORGE).
    Returns (func_source_text, external_calls_list) or (None, []).
    """
    filepath = get_filepath(item)
    contract = item.get('contract', '')
    func_name = get_func_name(item)
    source_type = get_source_type(item)

    if source_type == "DAppSCAN":
        full_path = DAPPSCAN_ROOT / filepath
        if not full_path.exists():
            return None, []

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                file_source = fh.read()
        except Exception:
            return None, []

        # Get project-level contracts
        proj_root = find_project_root_safe(filepath)
        proj_key = str(proj_root) if proj_root else filepath
        if proj_key not in project_cache:
            project_cache[proj_key] = load_project_contracts(proj_root)

        all_contracts = dict(project_cache[proj_key])
        all_contracts.update(nhs.parse_contracts(file_source))

        try:
            all_funcs = nhs.resolve_all_functions(contract, all_contracts)
            if func_name in all_funcs:
                func_node = all_funcs[func_name]
                func_src = nhs.node_text(func_node)

                # Get external calls
                state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)
                ext_calls = nhs.find_external_calls_ast(func_node, state_var_types, all_contracts)
                return func_src, ext_calls
        except Exception:
            pass
        return None, []

    else:
        # FORGE
        vfp_id = item.get('vfp_id')
        if not vfp_id or vfp_id not in vfp_data:
            return None, []

        all_contracts = {}
        for fn, fc in vfp_data[vfp_id].get('affected_files', {}).items():
            try:
                all_contracts.update(nhs.parse_contracts(fc))
            except Exception:
                pass

        try:
            all_funcs = nhs.resolve_all_functions(contract, all_contracts)
            if func_name in all_funcs:
                func_node = all_funcs[func_name]
                func_src = nhs.node_text(func_node)

                state_var_types = nhs.resolve_all_state_var_types(contract, all_contracts)
                ext_calls = nhs.find_external_calls_ast(func_node, state_var_types, all_contracts)
                return func_src, ext_calls
        except Exception:
            pass
        return None, []


def is_view_or_pure(func_source):
    """
    Check if a function is declared as `view` or `pure`.
    We look at the function signature (everything before the first `{`).
    """
    if not func_source:
        return False
    # Split at first opening brace to get the signature
    parts = func_source.split('{', 1)
    if not parts:
        return False
    signature = parts[0].lower()
    # Check for view or pure keywords (as whole words)
    return bool(re.search(r'\bview\b', signature) or re.search(r'\bpure\b', signature))


def all_calls_read_only(ext_calls):
    """
    Check if ALL external calls in the function are read-only.
    Returns (is_all_read_only, details_list).
    """
    if not ext_calls:
        return True, []  # No external calls = trivially read-only

    details = []
    all_ro = True
    for c in ext_calls:
        method = c.get('method', '')
        if method in READ_ONLY_METHODS:
            details.append((method, "read-only"))
        elif method in STATE_CHANGING_METHODS:
            details.append((method, "state-changing"))
            all_ro = False
        else:
            # Unknown method — be conservative, assume NOT read-only
            details.append((method, "unknown (treated as non-read-only)"))
            all_ro = False

    return all_ro, details


def apply_rule(item, func_source, ext_calls):
    """
    Apply the correction rule to a single item.
    Returns (is_invalid, reason_detail) tuple.
    """
    swc = get_swc_code(item)
    if '104' not in swc:
        return False, "Not SWC-104"

    # Condition (a): is the function view/pure?
    if not is_view_or_pure(func_source):
        return False, "Function is not view/pure — rule does not apply"

    # Condition (b): are ALL external calls read-only?
    all_ro, call_details = all_calls_read_only(ext_calls)
    if not all_ro:
        state_changing = [m for m, t in call_details if t == "state-changing" or "unknown" in t]
        return False, f"Function is view/pure but has state-changing/unknown calls: {state_changing}"

    # Both conditions met — annotation is INVALID
    ro_methods = [m for m, t in call_details if t == "read-only"]
    return True, f"view/pure function with only read-only calls: {ro_methods}"


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("HyperVul — Label Correction Proposal: SWC-104 View/Pure Rule")
    print("=" * 80)

    # Load VFP data for FORGE source resolution
    load_vfp_data()
    print(f"Loaded {len(vfp_data)} FORGE VFP files")

    # Load all splits
    splits = {}
    for split_name in ['train', 'val', 'test']:
        with open(SPLITS_DIR / f"{split_name}.json") as f:
            splits[split_name] = json.load(f)
        print(f"Loaded {split_name}: {len(splits[split_name])} items")

    # =========================================================================
    # STEP 2: Apply the rule to EVERY positive, blind to model predictions
    # =========================================================================
    print("\n" + "=" * 60)
    print("STEP 2: Applying correction rule to all positives...")
    print("=" * 60)

    all_invalidated = []
    stats = defaultdict(lambda: defaultdict(int))  # stats[split][(source, cc)] = count

    for split_name, split_data in splits.items():
        positives = [i for i in split_data if i.get('label') == 1]
        print(f"\n--- {split_name.upper()} split: {len(positives)} positives ---")

        swc104_count = 0
        for idx, item in enumerate(positives):
            swc = get_swc_code(item)
            source = get_source_type(item)
            cc = "cross" if item.get('is_cross_contract') else "intra"

            if '104' not in swc:
                continue
            swc104_count += 1

            func_name = get_func_name(item)
            contract = item.get('contract', '')
            print(f"  Checking SWC-104: {contract}.{func_name} ({source}, {cc})")

            # Get function source and calls
            func_source, ext_calls = get_function_source_for_item(item)

            # If we can't find source, use the recorded external_calls from the item
            if func_source is None:
                # Can't verify — skip (conservative)
                print(f"    → SKIP: source not found")
                continue

            # Also check external calls from the item itself if AST didn't find any
            if not ext_calls:
                ext_calls_from_item = item.get('external_calls', [])
                if ext_calls_from_item:
                    ext_calls = ext_calls_from_item

            is_invalid, reason = apply_rule(item, func_source, ext_calls)

            if is_invalid:
                print(f"    → INVALID: {reason}")
                all_invalidated.append({
                    'split': split_name,
                    'source': source,
                    'is_cross_contract': item.get('is_cross_contract', False),
                    'contract': contract,
                    'function': func_name,
                    'swc_code': swc,
                    'category': item.get('category', '') or item.get('vtype', ''),
                    'filepath': get_filepath(item),
                    'func_source': func_source,
                    'ext_calls': ext_calls,
                    'reason': reason,
                    'item': item,  # keep reference for Step 4
                })
                stats[split_name][(source, cc)] += 1
            else:
                print(f"    → VALID: {reason}")

        print(f"  SWC-104 items checked: {swc104_count}")

    # =========================================================================
    # STEP 4: Cross-reference with model predictions (transparency only)
    # =========================================================================
    print("\n" + "=" * 60)
    print("STEP 4: Cross-referencing with model predictions...")
    print("=" * 60)

    # Load model and run predictions on test set only
    from model.model import HyperedgeClassifier
    from model.train import HyperedgeDataset, collate_fn, evaluate_model

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = HyperedgeClassifier(input_dim=768, hidden_dim=256, dropout=0.3).to(device)
    checkpoint_path = PROJECT_ROOT / "model" / "iteration1_checkpoint.pt"
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    with open(PROJECT_ROOT / "model" / "threshold_config.json") as f:
        threshold_config = json.load(f)
    best_threshold = threshold_config["best_threshold"]

    with open(SPLITS_DIR / "test_features.json") as f:
        test_features = json.load(f)

    test_dataset = HyperedgeDataset(test_features)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    test_probs, test_labels, test_items = evaluate_model(model, test_loader, device)
    test_preds = (test_probs >= best_threshold).astype(int)

    # Build a lookup from (contract, function, normalized_source_hash) -> prediction
    test_pred_lookup = {}
    for idx, item in enumerate(test_items):
        key = (
            item.get('contract', ''),
            get_func_name(item),
            item.get('normalized_source_hash', '')
        )
        test_pred_lookup[key] = {
            'pred': int(test_preds[idx]),
            'prob': float(test_probs[idx]),
            'label': int(test_labels[idx]),
        }

    # Annotate each invalidated item with model prediction (test split only)
    for inv_item in all_invalidated:
        if inv_item['split'] == 'test':
            key = (
                inv_item['contract'],
                inv_item['function'],
                inv_item['item'].get('normalized_source_hash', '')
            )
            pred_info = test_pred_lookup.get(key)
            if pred_info:
                inv_item['model_caught'] = pred_info['pred'] == 1
                inv_item['model_prob'] = pred_info['prob']
            else:
                inv_item['model_caught'] = None
                inv_item['model_prob'] = None
        else:
            inv_item['model_caught'] = None  # no model predictions for train/val
            inv_item['model_prob'] = None

    # =========================================================================
    # Generate report
    # =========================================================================
    generate_report(all_invalidated, stats, splits, best_threshold)


def generate_report(invalidated, stats, splits, threshold):
    """Generate the label correction proposal markdown report."""
    lines = []

    # ---- Header ----
    lines.append("# Label Correction Proposal: SWC-104 View/Pure Rule")
    lines.append("")
    lines.append("This document proposes a label correction based on a general, model-blind rule.")
    lines.append("**No labels have been modified.** The full list of affected items is presented")
    lines.append("for human confirmation before any changes are applied.")
    lines.append("")

    # ---- STEP 1: The Rule ----
    lines.append("## Step 1 — Formal Correction Rule")
    lines.append("")
    lines.append("> **RULE**: An SWC-104 (Unchecked Call Return Value) positive label is **INVALID** if and only if:")
    lines.append(">")
    lines.append("> **(a)** The annotated function is declared `view` or `pure` (i.e., the Solidity compiler")
    lines.append(">     enforces that it cannot modify contract state), **AND**")
    lines.append(">")
    lines.append("> **(b)** Every external call within the function is a **read-only query** — a getter,")
    lines.append(">     price oracle, or computational helper (e.g., `balanceOf`, `getPricePerFullShare`,")
    lines.append(">     `get_virtual_price`, `latestRoundData`, SafeMath `mul`/`div`) — meaning")
    lines.append(">     there is no state-changing call (e.g., `transfer`, `transferFrom`, `approve`,")
    lines.append(">     `call`, `send`) whose ignored return value could cause state corruption or loss of funds.")
    lines.append("")
    lines.append("> **Rationale**: SWC-104 concerns arise when an external call's return value is")
    lines.append("> not checked, allowing silent failure (e.g., `transfer()` returning `false`).")
    lines.append("> In a `view`/`pure` function that only calls read-only methods, there is no")
    lines.append("> state modification to fail silently — the return values are consumed in a")
    lines.append("> local computation. The annotation is therefore a false positive.")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> This rule makes **no reference** to the model's predictions. It is applied")
    lines.append("> uniformly to every positive in the dataset regardless of whether the model")
    lines.append("> predicted it correctly or not.")
    lines.append("")

    # ---- STEP 2: Impact ----
    lines.append("---")
    lines.append("## Step 2 — Per-Split / Per-Source Impact")
    lines.append("")

    # Count totals
    total_invalidated = len(invalidated)
    total_positives = sum(
        sum(1 for i in split_data if i.get('label') == 1)
        for split_data in splits.values()
    )
    lines.append(f"**Total positives across all splits**: {total_positives}")
    lines.append(f"**Total invalidated by the rule**: {total_invalidated}")
    lines.append("")

    lines.append("| Split | Source | Contract Type | Invalidated | SWC-104 Total | % of SWC-104 |")
    lines.append("|---|---|---|---|---|---|")

    for split_name in ['train', 'val', 'test']:
        split_data = splits[split_name]
        for source in ['FORGE', 'DAppSCAN']:
            for cc_label, cc_bool in [('Cross-contract', True), ('Intra-contract', False)]:
                # Count total SWC-104 in this group
                total_swc104 = sum(
                    1 for i in split_data
                    if i.get('label') == 1
                    and ('104' in get_swc_code(i))
                    and (get_source_type(i) == source)
                    and (i.get('is_cross_contract', False) == cc_bool)
                )
                inv_count = stats[split_name].get((source, "cross" if cc_bool else "intra"), 0)
                if total_swc104 > 0 or inv_count > 0:
                    pct = inv_count / total_swc104 * 100 if total_swc104 > 0 else 0
                    lines.append(f"| {split_name.upper()} | {source} | {cc_label} | **{inv_count}** | {total_swc104} | {pct:.1f}% |")

    lines.append("")

    # Summary by split
    lines.append("### Summary by Split")
    lines.append("")
    for split_name in ['train', 'val', 'test']:
        split_inv = [i for i in invalidated if i['split'] == split_name]
        total_pos = sum(1 for i in splits[split_name] if i.get('label') == 1)
        if split_inv:
            lines.append(f"- **{split_name.upper()}**: {len(split_inv)} items invalidated out of {total_pos} positives ({len(split_inv)/total_pos*100:.1f}%)")
        else:
            lines.append(f"- **{split_name.upper()}**: 0 items invalidated out of {total_pos} positives")
    lines.append("")

    # Note about FORGE
    forge_invalidated = [i for i in invalidated if i['source'] == 'FORGE']
    if not forge_invalidated:
        lines.append("> [!NOTE]")
        lines.append("> **FORGE has zero SWC-104 positives** in the entire dataset (FORGE only contains")
        lines.append("> SWC-107 Reentrancy and SWC-114 Front-running). The rule therefore affects only DAppSCAN items,")
        lines.append("> but this is a property of the data, not a bias in the rule.")
        lines.append("")

    # ---- STEP 3: Full list ----
    lines.append("---")
    lines.append("## Step 3 — Full List of Invalidated Items (for Human Confirmation)")
    lines.append("")
    lines.append(f"The following {total_invalidated} items satisfy both conditions of the rule.")
    lines.append("**Please review each function source to confirm it is genuinely a view/pure")
    lines.append("function with only read-only external calls.**")
    lines.append("")

    for idx, inv in enumerate(invalidated):
        lines.append(f"### Item {idx+1}: {inv['contract']}.{inv['function']}")
        lines.append("")
        lines.append(f"- **Split**: {inv['split'].upper()}")
        lines.append(f"- **Source**: {inv['source']}")
        lines.append(f"- **Cross-contract**: {inv['is_cross_contract']}")
        lines.append(f"- **SWC Code**: {inv['swc_code']}")
        lines.append(f"- **Category**: {inv['category']}")
        lines.append(f"- **File**: `{inv['filepath']}`")
        lines.append(f"- **Rule match**: {inv['reason']}")
        lines.append("")

        # Function source
        lines.append("**Function Source:**")
        src = inv['func_source']
        src_lines = src.split('\n')
        if len(src_lines) > 40:
            shown = '\n'.join(src_lines[:20] + ['    // ... truncated ...'] + src_lines[-10:])
            lines.append(f"({len(src_lines)} lines, truncated)")
        else:
            shown = src
        lines.append("```solidity")
        lines.append(shown)
        lines.append("```")
        lines.append("")

        # External calls
        lines.append("**External calls in this function:**")
        if inv['ext_calls']:
            for c in inv['ext_calls']:
                method = c.get('method', '?')
                call_text = c.get('call_text', '?')[:80]
                reason = c.get('reason', '')
                ro_status = "✅ read-only" if method in READ_ONLY_METHODS else "⚠️ unknown"
                lines.append(f"- `{method}()` — `{call_text}` — {ro_status}")
        else:
            lines.append("- (no external calls detected)")
        lines.append("")

        # View/pure confirmation
        signature = src.split('{', 1)[0] if '{' in src else src[:200]
        is_view = 'view' in signature.lower()
        is_pure = 'pure' in signature.lower()
        lines.append(f"**Function modifier**: {'`view`' if is_view else ''}{' `pure`' if is_pure else ''}")
        lines.append(f"**Signature**: `{signature.strip()[:120]}...`")
        lines.append("")

    # ---- STEP 4: Caught vs Missed ----
    lines.append("---")
    lines.append("## Step 4 — Caught vs. Missed Breakdown (Transparency)")
    lines.append("")
    lines.append(f"Model: Iteration 1 (threshold = {threshold:.4f})")
    lines.append("")
    lines.append("> [!IMPORTANT]")
    lines.append("> This section is for **transparency only**. The correction rule was defined and")
    lines.append("> applied without any reference to the model's predictions. This cross-reference")
    lines.append("> is provided so that reviewers can verify the rule is not disproportionately")
    lines.append("> removing items the model missed.")
    lines.append("")

    test_invalidated = [i for i in invalidated if i['split'] == 'test']
    if test_invalidated:
        caught = [i for i in test_invalidated if i.get('model_caught') is True]
        missed = [i for i in test_invalidated if i.get('model_caught') is False]
        unknown = [i for i in test_invalidated if i.get('model_caught') is None]

        lines.append(f"**Test split invalidated items**: {len(test_invalidated)}")
        lines.append(f"- **Model CAUGHT (TP at threshold)**: {len(caught)}")
        lines.append(f"- **Model MISSED (FN at threshold)**: {len(missed)}")
        if unknown:
            lines.append(f"- **Unknown (no prediction available)**: {len(unknown)}")
        lines.append("")

        lines.append("| Item | Contract.Function | Model Prediction | P(vuln) |")
        lines.append("|---|---|---|---|")
        for inv in test_invalidated:
            contract_func = f"{inv['contract']}.{inv['function']}"
            if inv.get('model_caught') is True:
                pred_str = "✅ CAUGHT"
            elif inv.get('model_caught') is False:
                pred_str = "❌ MISSED"
            else:
                pred_str = "? UNKNOWN"
            prob = inv.get('model_prob')
            prob_str = f"{prob:.4f}" if prob is not None else "N/A"
            lines.append(f"| {inv['source']} | {contract_func} | {pred_str} | {prob_str} |")
        lines.append("")

        # Assessment
        if len(caught) > 0 and len(missed) > 0:
            lines.append(f"> The rule removes **{len(caught)} items the model caught** and **{len(missed)} items it missed**.")
            lines.append(f"> This is {'approximately balanced' if abs(len(caught) - len(missed)) <= 1 else 'not perfectly balanced, but'}.")
        elif len(caught) > 0 and len(missed) == 0:
            lines.append(f"> ✅ The rule **only removes items the model CAUGHT**. This is the opposite of cherry-picking —")
            lines.append(f"> removing caught items actually hurts the model's reported performance, not helps it.")
        elif len(caught) == 0 and len(missed) > 0:
            lines.append("> ⚠️ **WARNING**: The rule only removes items the model missed. While the rule is")
            lines.append("> defined independently of the model, this pattern warrants extra scrutiny.")
            lines.append("> Please verify each item above is genuinely a view/pure + read-only case.")
        lines.append("")
    else:
        lines.append("No invalidated items in the test split — no cross-reference to report.")
        lines.append("")

    # Train/Val
    for split_name in ['train', 'val']:
        split_inv = [i for i in invalidated if i['split'] == split_name]
        if split_inv:
            lines.append(f"**{split_name.upper()} split**: {len(split_inv)} invalidated items")
            lines.append(f"(No model predictions available for {split_name} — model was only evaluated on test.)")
            lines.append("")

    # ---- Final instructions ----
    lines.append("---")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. **Human review**: Confirm each item in Step 3 is genuinely `view`/`pure` with only read-only calls.")
    lines.append("2. **If confirmed**: Remove the invalidated items from all splits and re-run evaluation.")
    lines.append("3. **If any item is NOT genuinely invalid**: Remove it from the invalidation list before applying.")
    lines.append("")

    report_content = "\n".join(lines)
    report_path = RESULTS_DIR / "label_correction_proposal.md"
    with open(report_path, "w") as f:
        f.write(report_content)
    print(f"\nSaved report to {report_path}")


if __name__ == '__main__':
    main()
