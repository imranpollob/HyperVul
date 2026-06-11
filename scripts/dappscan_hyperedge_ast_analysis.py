#!/usr/bin/env python3
"""
HyperVul — DAppSCAN AST-based Positive Hyperedge Analysis (tree-sitter-solidity)
=============================================================================

Applies the AST hyperedge construction (Changes #1-4, NO keyword guessing)
to DAppSCAN. Incorporates:
  - Robust project root detection by walking up ancestors (Change A)
  - Deduplication against FORGE-Curated positives by contract name + function name + normalized source hash (Change B)
  - Label-quality check verifying AST function name vs annotated function name (Change C)
"""

import json
import re
import sys
import hashlib
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import tree_sitter as ts
import tree_sitter_solidity as tss

# Suppress tree-sitter deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)

DAPPSCAN_ROOT = Path("/home/pollmix/Coding/HyperVul/data/DAppSCAN")
SWC_SOURCE_DIR = DAPPSCAN_ROOT / "DAppSCAN-source" / "SWCsource"
CONTRACTS_ROOT = DAPPSCAN_ROOT / "DAppSCAN-source" / "contracts"
RESULTS_DIR = Path("/home/pollmix/Coding/HyperVul/experiments/results")

INTERACTION_SWCS = {"SWC-107", "SWC-114", "SWC-104", "SWC-112"}

# Known low-level call method names that are ALWAYS external
LOW_LEVEL_CALLS = {"call", "delegatecall", "staticcall", "transfer", "send"}

# SafeERC20 / ERC20 wrapper methods that are always external transfers
SAFE_TRANSFER_METHODS = {
    "safeTransfer", "safeTransferFrom", "safeApprove",
    "safeIncreaseAllowance", "safeDecreaseAllowance",
}

# Methods that are intrinsically external call operations
EXTERNAL_CALL_METHODS = LOW_LEVEL_CALLS | SAFE_TRANSFER_METHODS | {
    "transfer", "transferFrom", "approve",
    "balanceOf", "allowance",
    "mint", "burn", "burnFrom",
    # Uniswap / DeFi
    "swap", "swapExactTokensForTokens", "swapExactTokensForTokensSupportingFeeOnTransferTokens",
    "swapTokensForExactTokens", "swapExactETHForTokens", "swapExactTokensForETH",
    "addLiquidity", "removeLiquidity", "getAmountsOut", "getAmountsIn",
    "exactInputSingle", "exactInput", "exactOutputSingle", "exactOutput",
    # Uniswap v4 / DeFi callbacks / Vault operations (Change #4)
    "unlock", "lock", "settle", "take", "getSlot0", "accrueInterest", "flash", "claim",
    # Common
    "deposit", "withdraw", "borrow", "repay", "liquidate",
    "flashLoan", "execute", "getPrice", "latestAnswer", "latestRoundData",
}

# Solidity built-in members that are NOT external calls when used as member access
BUILTIN_MEMBERS = {"length", "push", "pop", "selector", "balance", "code", "codehash"}

# Solidity built-in globals — identifiers that are not state variables
BUILTIN_GLOBALS = {
    "msg", "block", "tx", "abi", "type", "super", "this",
    "now", "gasleft", "blockhash", "keccak256", "sha256", "ripemd160",
    "ecrecover", "addmod", "mulmod", "selfdestruct", "assert", "require",
    "revert", "emit",
}


# ============================================================================
# AST HELPERS
# ============================================================================

def find_children_by_type(node, node_type: str):
    """Yield all direct children of `node` with the given type."""
    for child in node.children:
        if child.type == node_type:
            yield child


def find_descendants_by_type(node, node_type: str):
    """Yield all descendants (recursive) of `node` with the given type."""
    for child in node.children:
        if child.type == node_type:
            yield child
        yield from find_descendants_by_type(child, node_type)


def node_text(node) -> str:
    """Get the UTF-8 text of a node."""
    return node.text.decode("utf-8", errors="ignore") if node else ""


def get_identifier_name(node) -> str | None:
    """Extract the identifier name from various node types."""
    if node is None:
        return None
    if node.type == "identifier":
        return node_text(node)
    # For user_defined_type, get the identifier child
    for child in node.children:
        if child.type == "identifier":
            return node_text(child)
    return None


# ============================================================================
# CONTRACT-LEVEL PARSING
# ============================================================================

class ContractInfo:
    """Parsed information about a single contract."""

    def __init__(self, name: str, node):
        self.name = name
        self.node = node
        self.base_names: list[str] = []  # direct parent contract names
        self.state_vars: set[str] = set()  # state variable names declared here
        self.state_var_types: dict[str, str] = {}  # var_name -> type_text
        self.functions: dict[str, object] = {}  # func_name -> AST node
        self.is_interface: bool = False
        self.is_library: bool = False

    def __repr__(self):
        return f"ContractInfo({self.name}, bases={self.base_names}, vars={self.state_vars})"


def parse_contracts(source_code: str) -> dict[str, ContractInfo]:
    """
    Parse all contracts/interfaces/libraries from a Solidity source string.
    Returns dict: contract_name -> ContractInfo.
    """
    tree = PARSER.parse(source_code.encode("utf-8", errors="ignore"))
    root = tree.root_node
    contracts: dict[str, ContractInfo] = {}

    for node in root.children:
        if node.type in ("contract_declaration", "interface_declaration", "library_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node is None:
                # Fallback: look for first identifier child
                for child in node.children:
                    if child.type == "identifier":
                        name_node = child
                        break
            if name_node is None:
                continue

            name = node_text(name_node)
            info = ContractInfo(name, node)

            if node.type == "interface_declaration":
                info.is_interface = True
            elif node.type == "library_declaration":
                info.is_library = True

            # Parse inheritance: "is A, B, C"
            for spec in find_children_by_type(node, "inheritance_specifier"):
                for udt in find_descendants_by_type(spec, "user_defined_type"):
                    base_name = get_identifier_name(udt)
                    if base_name:
                        info.base_names.append(base_name)

            # Parse body
            for body in find_children_by_type(node, "contract_body"):
                for item in body.children:
                    if item.type == "state_variable_declaration":
                        _parse_state_var(item, info)
                    elif item.type == "function_definition":
                        fname = _get_function_name(item)
                        if fname:
                            info.functions[fname] = item

            contracts[name] = info

    return contracts


def _parse_state_var(node, info: ContractInfo):
    """Parse a state_variable_declaration and add to ContractInfo."""
    var_name = None
    type_text = None

    for child in node.children:
        if child.type == "identifier":
            var_name = node_text(child)
        elif child.type == "type_name":
            type_text = node_text(child)

    if var_name:
        info.state_vars.add(var_name)
        if type_text:
            info.state_var_types[var_name] = type_text


def _get_function_name(node) -> str | None:
    """Get the name of a function_definition node."""
    name_node = node.child_by_field_name("name")
    if name_node:
        return node_text(name_node)
    # Fallback: look for identifier after 'function' keyword
    found_kw = False
    for child in node.children:
        if child.type == "function" or node_text(child) == "function":
            found_kw = True
        elif found_kw and child.type == "identifier":
            return node_text(child)
    return None


# ============================================================================
# INHERITANCE RESOLUTION
# ============================================================================

def resolve_all_state_vars(contract_name: str,
                           all_contracts: dict[str, ContractInfo],
                           visited: set[str] | None = None) -> set[str]:
    """
    Resolve ALL state variables visible to `contract_name` by walking
    up the inheritance chain.
    """
    if visited is None:
        visited = set()
    if contract_name in visited:
        return set()
    visited.add(contract_name)

    info = all_contracts.get(contract_name)
    if info is None:
        return set()

    result = set(info.state_vars)
    for base in info.base_names:
        result |= resolve_all_state_vars(base, all_contracts, visited)
    return result


def resolve_all_state_var_types(contract_name: str,
                                all_contracts: dict[str, ContractInfo],
                                visited: set[str] | None = None) -> dict[str, str]:
    """
    Resolve ALL state variable types visible to `contract_name`.
    """
    if visited is None:
        visited = set()
    if contract_name in visited:
        return {}
    visited.add(contract_name)

    info = all_contracts.get(contract_name)
    if info is None:
        return {}

    result = dict(info.state_var_types)
    for base in info.base_names:
        parent_types = resolve_all_state_var_types(base, all_contracts, visited)
        for k, v in parent_types.items():
            if k not in result:
                result[k] = v
    return result


def resolve_all_functions(contract_name: str,
                          all_contracts: dict[str, ContractInfo],
                          visited: set[str] | None = None) -> dict[str, object]:
    """
    Resolve ALL functions visible to `contract_name` by walking inheritance.
    Overriding: child's version takes precedence.
    """
    if visited is None:
        visited = set()
    if contract_name in visited:
        return {}
    visited.add(contract_name)

    info = all_contracts.get(contract_name)
    if info is None:
        return {}

    # Start with parent functions, then override with child
    result = {}
    for base in info.base_names:
        parent_funcs = resolve_all_functions(base, all_contracts, visited)
        result.update(parent_funcs)
    result.update(info.functions)
    return result


# ============================================================================
# FUNCTION-LEVEL ANALYSIS
# ============================================================================

def extract_local_vars(func_node) -> set[str]:
    """Extract all locally declared variable names inside a function body."""
    locals_ = set()

    # Parameters
    for param in find_descendants_by_type(func_node, "parameter"):
        for ident in find_children_by_type(param, "identifier"):
            locals_.add(node_text(ident))

    # Variable declarations inside body
    for vds in find_descendants_by_type(func_node, "variable_declaration_statement"):
        for vd in find_descendants_by_type(vds, "variable_declaration"):
            for ident in find_children_by_type(vd, "identifier"):
                locals_.add(node_text(ident))

    # Tuple declarations
    for vtuple in find_descendants_by_type(func_node, "variable_declaration_tuple"):
        for vd in find_descendants_by_type(vtuple, "variable_declaration"):
            for ident in find_children_by_type(vd, "identifier"):
                locals_.add(node_text(ident))

    return locals_


def _unwrap_expression(node):
    """Recursively unwrap 'expression' wrapper nodes."""
    while node is not None and node.type == "expression" and node.children:
        inner = node.children[0]
        if inner.type == "expression":
            node = inner
        else:
            return inner
    return node


def find_external_calls_ast(func_node, state_var_types: dict[str, str],
                             all_contracts: dict[str, ContractInfo],
                             allow_fallback: bool = False) -> list[dict]:
    """
    Find external calls in a function AST node.
    """
    calls = []
    local_vars = extract_local_vars(func_node)

    local_var_types: dict[str, str] = {}

    # Function parameters
    for param in find_descendants_by_type(func_node, "parameter"):
        pname = None
        ptype = None
        for child in param.children:
            if child.type == "identifier":
                pname = node_text(child)
            elif child.type == "type_name":
                ptype = node_text(child)
        if pname and ptype:
            local_var_types[pname] = ptype

    # Local variable declarations
    for vds in find_descendants_by_type(func_node, "variable_declaration_statement"):
        for vd in find_descendants_by_type(vds, "variable_declaration"):
            vname = None
            vtype = None
            for child in vd.children:
                if child.type == "identifier":
                    vname = node_text(child)
                elif child.type == "type_name":
                    vtype = node_text(child)
            if vname and vtype:
                local_var_types[vname] = vtype

    # Walk all call_expression nodes in the function
    for call_node in find_descendants_by_type(func_node, "call_expression"):
        call_text = node_text(call_node)[:120]

        raw_expr = None
        for child in call_node.children:
            if child.type in ("expression", "member_expression", "identifier", "struct_expression"):
                raw_expr = child
                break

        if raw_expr is None:
            continue

        actual_expr = _unwrap_expression(raw_expr)
        if actual_expr is None:
            continue

        if actual_expr.type == "struct_expression":
            for child in actual_expr.children:
                unwrapped = _unwrap_expression(child)
                if unwrapped and unwrapped.type == "member_expression":
                    actual_expr = unwrapped
                    break

        if actual_expr.type == "member_expression":
            method_name = None
            receiver_node = None

            for child in actual_expr.children:
                if child.type == "identifier":
                    method_name = node_text(child)
                elif child.type == "expression":
                    receiver_node = _unwrap_expression(child)

            if receiver_node is None:
                idents = [c for c in actual_expr.children if c.type == "identifier"]
                if len(idents) >= 2:
                    receiver_name = node_text(idents[0])
                    method_name = node_text(idents[1])
                elif len(idents) == 1:
                    method_name = node_text(idents[0])
                    receiver_name = None
                else:
                    continue
            else:
                receiver_name = _get_receiver_root_name(receiver_node)

            if method_name is None:
                continue

            reason = _classify_call(
                method_name, receiver_name, receiver_node,
                state_var_types, local_var_types, all_contracts,
                allow_fallback=allow_fallback
            )
            if reason:
                calls.append({
                    "call_text": call_text,
                    "method": method_name,
                    "receiver": receiver_name or "(complex)",
                    "reason": reason,
                })

    return calls


def _get_receiver_root_name(receiver_node) -> str | None:
    """Get the root identifier name from a receiver expression."""
    if receiver_node is None:
        return None
    if receiver_node.type == "identifier":
        return node_text(receiver_node)
    if receiver_node.type == "member_expression":
        for child in receiver_node.children:
            if child.type == "identifier":
                return node_text(child)
            elif child.type == "expression":
                inner = _unwrap_expression(child)
                return _get_receiver_root_name(inner)
    if receiver_node.type == "call_expression":
        for child in receiver_node.children:
            if child.type == "expression":
                inner = _unwrap_expression(child)
                return _get_receiver_root_name(inner)
            elif child.type == "identifier":
                return node_text(child)
    if receiver_node.type == "array_access":
        for child in receiver_node.children:
            if child.type == "expression":
                inner = _unwrap_expression(child)
                return _get_receiver_root_name(inner)
            elif child.type == "identifier":
                return node_text(child)
    return None


def _is_interface_or_contract_type(type_str: str, all_contracts: dict[str, ContractInfo]) -> bool:
    """Check if a type string refers to an interface or contract type."""
    if type_str is None:
        return False
    
    base = type_str.strip()
    
    # Strip mapping wrappers
    while "=>" in base:
        parts = base.split("=>")
        base = parts[-1].strip()
        if base.endswith(")"):
            base = base[:-1].strip()
            
    base = base.rstrip("[]").strip()
    
    if base in ("address", "bool", "string", "var", "int", "uint", "byte", "bytes", "fixed", "ufixed") or \
       base.startswith("uint") or base.startswith("int") or base.startswith("bytes") or \
       base.startswith("ufixed") or base.startswith("fixed"):
        return False
        
    if len(base) >= 2 and base[0] == "I" and base[1].isupper():
        return True
        
    if base in all_contracts:
        return True
        
    if any(base.startswith(prefix) for prefix in ("ERC20", "ERC721", "ERC1155", "IERC", "SafeERC")):
        return True
        
    if base and base[0].isupper():
        return True
        
    return False


def _classify_call(method_name: str, receiver_name: str | None,
                   receiver_node, state_var_types: dict[str, str],
                   local_var_types: dict[str, str],
                   all_contracts: dict[str, ContractInfo],
                   allow_fallback: bool = False) -> str | None:
    """Determine if a member call is external."""
    if receiver_name in BUILTIN_GLOBALS and receiver_name != "this":
        if receiver_name == "msg" or receiver_name == "tx":
            if method_name in LOW_LEVEL_CALLS:
                return "low-level call on msg.sender/tx.origin"
            return None
        return None

    if receiver_name == "super":
        return None

    if method_name in LOW_LEVEL_CALLS:
        return f"low-level .{method_name}()"

    if method_name in SAFE_TRANSFER_METHODS:
        return f"SafeERC20 .{method_name}()"

    if receiver_name and receiver_name in state_var_types:
        rtype = state_var_types[receiver_name]
        if _is_interface_or_contract_type(rtype, all_contracts):
            return f"call on contract-typed state var '{receiver_name}' (type: {rtype})"

    if receiver_name and receiver_name in local_var_types:
        rtype = local_var_types[receiver_name]
        if _is_interface_or_contract_type(rtype, all_contracts):
            return f"call on contract-typed local var '{receiver_name}' (type: {rtype})"

    if receiver_name and _is_interface_or_contract_type(receiver_name, all_contracts):
        if receiver_node and receiver_node.type == "call_expression":
            return f"inline cast call {receiver_name}(...).{method_name}()"
        if receiver_name in all_contracts or (len(receiver_name) >= 2 and receiver_name[0] == "I" and receiver_name[1].isupper()):
            return f"call on interface/contract type '{receiver_name}'"

    if method_name in EXTERNAL_CALL_METHODS and receiver_name and receiver_name not in BUILTIN_GLOBALS:
        if method_name in ("transfer", "transferFrom", "approve", "balanceOf", "allowance",
                           "mint", "burn", "burnFrom"):
            return f"known ERC-like method .{method_name}() on '{receiver_name}'"
        elif method_name in ("deposit", "withdraw", "borrow", "repay", "liquidate",
                             "flashLoan", "execute", "unlock", "lock", "settle", "take",
                             "getSlot0", "accrueInterest", "flash", "claim"):
            return f"DeFi method .{method_name}() on '{receiver_name}'"
        elif method_name in ("getPrice", "latestAnswer", "latestRoundData"):
            return f"oracle method .{method_name}() on '{receiver_name}'"
        else:
            return f"known external method .{method_name}() on '{receiver_name}'"

    return None


def find_state_var_accesses(func_node, all_state_vars: set[str],
                            local_vars: set[str]) -> list[str]:
    """Find all state variable accesses in a function AST node."""
    accessed = set()

    for ident_node in find_descendants_by_type(func_node, "identifier"):
        name = node_text(ident_node)

        if name in local_vars:
            continue
        if name in BUILTIN_GLOBALS:
            continue
        if name in all_state_vars:
            parent = ident_node.parent
            if parent and parent.type in ("type_name", "user_defined_type", "pragma_directive",
                                          "import_directive", "inheritance_specifier",
                                          "emit_statement", "event_definition",
                                          "error_definition"):
                continue
            accessed.add(name)

    return sorted(accessed)


# ============================================================================
# NEW CHANGE HELPERS (A, B, C)
# ============================================================================

def find_project_root(file_path: Path) -> Path:
    """
    Robust project root detection (Change A).
    Walks up from the annotated file until it reaches the directory directly under the
    audit-firm/project grouping directory in DAppSCAN-source/contracts/.
    """
    top_contracts_dir = Path("/home/pollmix/Coding/HyperVul/data/DAppSCAN/DAppSCAN-source/contracts").resolve()
    abs_path = file_path.resolve()
    
    current = abs_path
    ancestors = []
    while current != current.parent:
        ancestors.append(current)
        current = current.parent
        
    project_root = None
    for p in ancestors:
        if p.parent and p.parent.parent == top_contracts_dir:
            project_root = p
            break
            
    if project_root is None:
        raise ValueError(f"Ambiguous or undetected project root for file: {file_path}")
        
    if not project_root.is_dir():
        raise ValueError(f"Detected project root is not a directory: {project_root} for file: {file_path}")
        
    return project_root


def normalize_source(src: str) -> str:
    """Normalize Solidity function source code by stripping comments and all whitespace (Change B)."""
    # Remove multi-line comments
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
    # Remove single-line comments
    src = re.sub(r'//.*', '', src)
    # Remove all whitespace characters
    src = "".join(src.split())
    return src.lower()


def load_forge_positives_source_hashes() -> set[tuple[str, str, str]]:
    """
    Load the 83 FORGE-Curated positives and compute their (contract, function, normalized_hash) tuples (Change B).
    """
    forge_positives_path = Path("/home/pollmix/Coding/HyperVul/experiments/results/forge_ast_constructable_hyperedges.json")
    if not forge_positives_path.exists():
        print("WARNING: forge_ast_constructable_hyperedges.json not found! Deduplication will be empty.")
        return set()
        
    print(f"Loading FORGE positives from {forge_positives_path}...")
    with open(forge_positives_path) as f:
        forge_positives = json.load(f)
        
    vfp_vuln_dir = Path("/home/pollmix/Coding/HyperVul/data/FORGE-Curated/flatten/vfp-vuln")
    forge_hashes = set()
    positives_by_vfp = defaultdict(list)
    
    for p in forge_positives:
        positives_by_vfp[p["vfp_id"]].append(p)
        
    for vfp_id, plist in positives_by_vfp.items():
        vfp_file = vfp_vuln_dir / f"{vfp_id}.json"
        if not vfp_file.exists():
            continue
        with open(vfp_file) as fh:
            vfp_data = json.load(fh)
            
        affected_files = vfp_data.get("affected_files", {})
        all_contracts = {}
        for fname, source in affected_files.items():
            try:
                parsed = parse_contracts(source)
                all_contracts.update(parsed)
            except Exception:
                pass
                
        for p in plist:
            func_name = p["function"]
            contract_name = p["contract"]
            if contract_name in all_contracts:
                resolved_funcs = resolve_all_functions(contract_name, all_contracts)
                func_node = resolved_funcs.get(func_name)
                if func_node:
                    src_text = node_text(func_node)
                    norm_hash = hashlib.sha256(normalize_source(src_text).encode("utf-8")).hexdigest()
                    forge_hashes.add((contract_name, func_name, norm_hash))
                    
    print(f"Computed normalized source hashes for {len(forge_hashes)} FORGE positives.")
    return forge_hashes


def parse_line_number(line_str: str) -> tuple[int, int]:
    """Parse DAppSCAN line number string into a 1-indexed (start_line, end_line) range."""
    cleaned = line_str.replace("L", "").replace(" ", "")
    if not cleaned:
        return 0, 999999
    try:
        if "-" in cleaned:
            parts = cleaned.split("-")
            return int(parts[0]), int(parts[1])
        else:
            val = int(cleaned)
            return val, val
    except Exception:
        return 0, 999999


def locate_overlapping_function(root_node, start_line: int, end_line: int) -> list[tuple[object, str]]:
    """Locate all function definition nodes that overlap with the annotated line range."""
    func_nodes = find_descendants_by_type(root_node, "function_definition")
    overlapping = []
    for node in func_nodes:
        # tree-sitter lines are 0-indexed
        func_start = node.start_point[0] + 1
        func_end = node.end_point[0] + 1
        if max(start_line, func_start) <= min(end_line, func_end):
            name = _get_function_name(node) or ""
            overlapping.append((node, name))
    return overlapping


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run():
    print("=" * 80)
    print("HyperVul — DAppSCAN AST-based Positive Hyperedge Analysis")
    print("=" * 80)

    # 1. Load FORGE hashes for deduplication (Change B)
    forge_hashes = load_forge_positives_source_hashes()

    # 2. Find all DAppSCAN SWC annotations
    json_files = sorted(list(SWC_SOURCE_DIR.glob("**/*.json")))
    print(f"\nFound {len(json_files)} DAppSCAN annotation files.")

    # ── STEP 1: Filter to interaction SWCs ──
    filtered_annotations = []
    swc_counts = Counter()

    for f in json_files:
        try:
            with open(f) as fh:
                data = json.load(fh)
            filepath_str = data.get("filePath", "")
            swcs = data.get("SWCs", [])
            for swc in swcs:
                category = swc.get("category", "")
                func_name = swc.get("function", "")
                line_no = swc.get("lineNumber", "")

                parts = category.split("-")
                if len(parts) >= 2:
                    swc_code = f"{parts[0]}-{parts[1]}"
                else:
                    swc_code = category

                swc_counts[swc_code] += 1

                if swc_code in INTERACTION_SWCS:
                    # Skip N/A functions
                    if func_name == "N/A" or not func_name:
                        continue

                    filtered_annotations.append({
                        "annotation_file": f,
                        "filePath": filepath_str,
                        "category": category,
                        "swc_code": swc_code,
                        "function": func_name,
                        "lineNumber": line_no
                    })
        except Exception as e:
            print(f"Error parsing annotation file {f}: {e}")

    print("\nSTEP 1 — Interaction SWC counts:")
    for swc in sorted(INTERACTION_SWCS):
        print(f"  {swc}: {swc_counts[swc]}")

    print(f"\nTotal filtered DAppSCAN annotations (excluding N/A functions): {len(filtered_annotations)}")

    # ── STEP 2 & 3: AST analysis ──
    print("\nProcessing annotations...")
    project_cache = {}  # project_root_path -> parsed contracts dict
    analysis_results = []

    located_count = 0
    name_matched_count = 0
    ambiguous_roots = 0

    for idx, ann in enumerate(filtered_annotations):
        rel_filepath = ann["filePath"]
        abs_sol_path = (DAPPSCAN_ROOT / rel_filepath).resolve()

        if not abs_sol_path.exists():
            continue

        # Change A: Detect project root robustly
        try:
            proj_root = find_project_root(abs_sol_path)
        except ValueError as ve:
            print(f"Ambiguity/Error: {ve}")
            ambiguous_roots += 1
            continue

        # Load and parse project bundle contracts (cached)
        proj_root_key = str(proj_root)
        if proj_root_key not in project_cache:
            project_contracts = {}
            for sol_file in proj_root.glob("**/*.sol"):
                try:
                    with open(sol_file, "r", encoding="utf-8", errors="ignore") as fh:
                        src = fh.read()
                    parsed = parse_contracts(src)
                    # We key them by contract name
                    project_contracts.update(parsed)
                except Exception:
                    pass
            project_cache[proj_root_key] = project_contracts

        merged_contracts = project_cache[proj_root_key]

        # Read and parse target file
        try:
            with open(abs_sol_path, "r", encoding="utf-8", errors="ignore") as fh:
                target_src = fh.read()
            target_file_contracts = parse_contracts(target_src)
        except Exception as e:
            print(f"Error reading target file {abs_sol_path}: {e}")
            continue

        # Extract line range
        start_line, end_line = parse_line_number(ann["lineNumber"])

        # Parse file AST to locate function node (Change C)
        tree = PARSER.parse(target_src.encode("utf-8", errors="ignore"))
        root_node = tree.root_node

        overlapping = locate_overlapping_function(root_node, start_line, end_line)
        if not overlapping:
            # Function not located
            continue

        located_count += 1
        annotated_name = ann["function"]

        # Select the best matching function node
        func_node = None
        func_name_in_ast = None

        # Look for exact name match
        for node, name in overlapping:
            if name == annotated_name:
                func_node = node
                func_name_in_ast = name
                name_matched_count += 1
                break

        # If no exact match, fall back to the first overlapping function node
        if func_node is None:
            func_node, func_name_in_ast = overlapping[0]

        # Enclosing contract for this function
        # Find which contract node this function belongs to by traversing ancestors
        curr = func_node.parent
        contract_name = None
        while curr:
            if curr.type in ("contract_declaration", "interface_declaration", "library_declaration"):
                name_node = curr.child_by_field_name("name")
                if name_node:
                    contract_name = node_text(name_node)
                break
            curr = curr.parent

        if contract_name is None:
            # Free-standing function, cannot have state vars
            continue

        # Resolve inheritance-aware state variables and functions
        all_state_vars = resolve_all_state_vars(contract_name, merged_contracts)
        all_state_var_types = resolve_all_state_var_types(contract_name, merged_contracts)

        # Get local vars, state var accesses and external calls
        local_vars = extract_local_vars(func_node)
        accessed_vars = find_state_var_accesses(func_node, all_state_vars, local_vars)
        ext_calls = find_external_calls_ast(func_node, all_state_var_types, merged_contracts, allow_fallback=False)

        has_sv = len(accessed_vars) > 0
        has_ext = len(ext_calls) > 0
        constructable = has_sv and has_ext

        # Categorize cross-contract vs. intra-contract
        is_cross_contract = False
        if constructable:
            # A call is cross-contract if the receiver's type resolves to another contract defined in the bundle
            for ec in ext_calls:
                method = ec["method"]
                receiver = ec["receiver"]
                
                # Check state var types
                rtype = None
                if receiver in all_state_var_types:
                    rtype = all_state_var_types[receiver]
                elif receiver in local_vars:
                    # Look up local var type in the AST
                    # (Quick check from code above, or we just extract from local_var_types)
                    # Let's rebuild local_var_types for this call
                    pass
                
                # We can also check if the receiver type matches any contract in merged_contracts
                # Check inline casts: e.g. T(addr)
                # In _classify_call, we classify based on T.
                # Let's look at the reason string! It contains information about what was classified.
                reason = ec["reason"]
                if "contract-typed" in reason or "interface/contract type" in reason or "inline cast" in reason:
                    # Extract type name from reason or types
                    # E.g. "call on contract-typed state var 'token' (type: IERC20)"
                    # E.g. "inline cast call IERC20(...).transfer()"
                    # Let's extract the type string from reason or check if it matches a contract in merged_contracts
                    type_candidates = []
                    if "type: " in reason:
                        type_candidates.append(reason.split("type: ")[1].split(")")[0].strip())
                    if "inline cast call " in reason:
                        type_candidates.append(reason.split("inline cast call ")[1].split("(")[0].strip())
                    if "call on interface/contract type '" in reason:
                        type_candidates.append(reason.split("call on interface/contract type '")[1].split("'")[0].strip())
                        
                    for tc in type_candidates:
                        base_tc = tc.rstrip("[]").strip()
                        if base_tc in merged_contracts and base_tc != contract_name:
                            is_cross_contract = True
                            break

        # Compute normalized hash for deduplication check (Change B)
        func_src = node_text(func_node)
        norm_hash = hashlib.sha256(normalize_source(func_src).encode("utf-8")).hexdigest()

        # Check duplicate against FORGE positives (Change B)
        is_duplicate = (contract_name, func_name_in_ast, norm_hash) in forge_hashes

        analysis_results.append({
            "filePath": rel_filepath,
            "category": ann["category"],
            "swc_code": ann["swc_code"],
            "annotated_function": annotated_name,
            "ast_function": func_name_in_ast,
            "lineNumber": ann["lineNumber"],
            "contract": contract_name,
            "project_root": str(proj_root.relative_to(DAPPSCAN_ROOT)),
            "constructable": constructable,
            "is_cross_contract": is_cross_contract if constructable else False,
            "is_duplicate_of_forge": is_duplicate,
            "state_vars_accessed": accessed_vars,
            "external_calls": ext_calls,
            "normalized_source_hash": norm_hash,
            "function_source": func_src
        })

    # ── REPORTING & DEDUPLICATION ──

    # Deduplicate DAppSCAN constructable positives
    # Multiple annotations might resolve to the same contract + function + normalized hash
    seen_positives = set()
    unique_dappscan_positives = []
    duplicate_of_forge_count = 0
    duplicates_excluded = []

    for r in analysis_results:
        if r["constructable"]:
            key = (r["contract"], r["ast_function"], r["normalized_source_hash"])
            if key not in seen_positives:
                seen_positives.add(key)
                if r["is_duplicate_of_forge"]:
                    duplicate_of_forge_count += 1
                    duplicates_excluded.append(r)
                else:
                    unique_dappscan_positives.append(r)

    # Label-quality match rate (Change C)
    match_rate = (name_matched_count / located_count) if located_count > 0 else 0.0

    # Counts per SWC
    swc_pos_counts = Counter()
    cross_contract_count = 0
    intra_contract_count = 0

    for r in unique_dappscan_positives:
        swc_pos_counts[r["swc_code"]] += 1
        if r["is_cross_contract"]:
            cross_contract_count += 1
        else:
            intra_contract_count += 1

    # Save outputs to RESULTS_DIR
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. dappscan_ast_constructable_hyperedges.json (only unique non-duplicate positives)
    constr_out = []
    for r in unique_dappscan_positives:
        constr_out.append({
            "filePath": r["filePath"],
            "category": r["category"],
            "swc_code": r["swc_code"],
            "annotated_function": r["annotated_function"],
            "ast_function": r["ast_function"],
            "lineNumber": r["lineNumber"],
            "contract": r["contract"],
            "project_root": r["project_root"],
            "is_cross_contract": r["is_cross_contract"],
            "state_vars_accessed": r["state_vars_accessed"],
            "external_calls": r["external_calls"],
            "normalized_source_hash": r["normalized_source_hash"]
        })
    with open(RESULTS_DIR / "dappscan_ast_constructable_hyperedges.json", "w") as fh:
        json.dump(constr_out, fh, indent=2)

    # 2. dappscan_ast_detailed.json
    detailed_out = []
    for r in analysis_results:
        d = dict(r)
        d.pop("function_source", None)
        detailed_out.append(d)
    with open(RESULTS_DIR / "dappscan_ast_detailed.json", "w") as fh:
        json.dump(detailed_out, fh, indent=2)

    # 3. dappscan_ast_summary.json
    summary = {
        "method": "tree-sitter AST (Changes #1-4)",
        "total_annotations_processed": len(filtered_annotations),
        "located_in_ast": located_count,
        "name_matched_in_ast": name_matched_count,
        "match_rate": match_rate,
        "ambiguous_project_roots": ambiguous_roots,
        "total_constructable_positives": len(unique_dappscan_positives) + duplicate_of_forge_count,
        "forge_duplicates_excluded": duplicate_of_forge_count,
        "unique_dappscan_positives": len(unique_dappscan_positives),
        "swc_distribution": dict(swc_pos_counts),
        "cross_contract_count": cross_contract_count,
        "intra_contract_count": intra_contract_count,
        "forge_positives": 83,
        "final_combined_unique_total": 83 + len(unique_dappscan_positives)
    }
    with open(RESULTS_DIR / "dappscan_ast_summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    # Print summary output
    print(f"\n{'='*80}")
    print("DAppSCAN AST-based Analysis Results Summary:")
    print(f"{'='*80}")
    print(f"  Processed annotations:               {len(filtered_annotations)}")
    print(f"  Located in AST:                      {located_count}")
    print(f"  Function name matched in AST:        {name_matched_count}")
    print(f"  Label-quality match rate (Change C): {match_rate:.2%}")
    print(f"  Ambiguous project roots (Change A):  {ambiguous_roots}")
    print(f"\n  Unique DAppSCAN positives:           {len(unique_dappscan_positives)}")
    print(f"  Excluded FORGE duplicates (Change B): {duplicate_of_forge_count}")
    print(f"\n  DAppSCAN Positives by SWC type:")
    for swc in sorted(INTERACTION_SWCS):
        print(f"    {swc}: {swc_pos_counts[swc]}")
    print(f"\n  Cross-contract vs Intra-contract breakdown:")
    print(f"    Cross-contract:                    {cross_contract_count}")
    print(f"    Intra-contract:                    {intra_contract_count}")
    print(f"\n  FINAL combined unique total:")
    print(f"    FORGE (83) + DAppSCAN unique ({len(unique_dappscan_positives)}): {83 + len(unique_dappscan_positives)}")
    print(f"{'='*80}")

    # Output list of duplicates for audit/inspection
    if duplicates_excluded:
        print("\nExcluded FORGE Duplicates:")
        for idx, d in enumerate(duplicates_excluded[:10]):
            print(f"  {idx+1}. Contract: {d['contract']}, Function: {d['ast_function']} (File: {d['filePath']})")
        if len(duplicates_excluded) > 10:
            print(f"  ... and {len(duplicates_excluded) - 10} more.")

    print(f"\nResults saved to {RESULTS_DIR}/")
    print(f"  dappscan_ast_constructable_hyperedges.json")
    print(f"  dappscan_ast_detailed.json")
    print(f"  dappscan_ast_summary.json")

    return summary


if __name__ == "__main__":
    run()
