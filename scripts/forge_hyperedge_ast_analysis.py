#!/usr/bin/env python3
"""
HyperVul — AST-based Positive Hyperedge Analysis (tree-sitter-solidity)
=========================================================================

Re-runs the constructable-hyperedge analysis from forge_hyperedge_analysis.py
but replaces regex matching with a proper AST parse to:
  1. Build an inheritance map across all contracts in each VFP
  2. Detect external calls via AST call_expression / member_expression nodes
  3. Detect state variable access via the full inheritance chain
  4. Recount constructable positive hyperedges
  5. Compare against the previous regex-based count (61)
"""

import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import tree_sitter as ts
import tree_sitter_solidity as tss

# Suppress the deprecation warning from tree-sitter int argument
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

LANG = ts.Language(tss.language())
PARSER = ts.Parser(LANG)

VFP_VULN_DIR = Path(__file__).resolve().parent.parent / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "experiments" / "results"

# CWE + keyword filters (reused from the regex script)
INTERACTION_CWES = {
    "CWE-1265", "CWE-841", "CWE-691", "CWE-362", "CWE-435",
    "CWE-670", "CWE-696", "CWE-835", "CWE-674", "CWE-834",
    "CWE-364", "CWE-366", "CWE-367", "CWE-421",
    "CWE-436", "CWE-437", "CWE-439",
    "CWE-662", "CWE-663", "CWE-667", "CWE-764", "CWE-765",
    "CWE-820", "CWE-821", "CWE-1058", "CWE-1088",
}

INTERACTION_KW_RE = re.compile(
    r"re-?entrancy|re-?entrant|flash[\s-]?loan|front[\s-]?run(?:ning)?|"
    r"sandwich|cross[\s-]?contract|callback|read[\s-]?only[\s-]?re-?entrancy|"
    r"reentrancy",
    re.IGNORECASE,
)

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
    return node.text.decode("utf-8") if node else ""


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
    tree = PARSER.parse(source_code.encode("utf-8"))
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
    up the inheritance chain (C3 linearization simplified as DFS).
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
    """
    Recursively unwrap 'expression' wrapper nodes to reach the actual
    underlying node (member_expression, identifier, struct_expression, etc.).
    tree-sitter-solidity wraps many things in 'expression' nodes.
    """
    while node is not None and node.type == "expression" and node.children:
        # An expression node with a single meaningful child: unwrap it
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
    Returns list of {call_text, method, receiver, reason}.

    An external call is:
      1. Low-level: x.call/delegatecall/staticcall/transfer/send(...)
      2. Interface/contract-typed state variable method call: token.transfer(...)
      3. Inline cast call: IERC20(addr).transfer(...)
      4. Known external method name on a non-primitive receiver
    """
    calls = []
    local_vars = extract_local_vars(func_node)

    # Collect all type names used in local variable declarations AND function
    # parameters (to know which locals are contract-typed)
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

        # The first child of call_expression is usually an 'expression' wrapper.
        # We need to unwrap it to get the actual callee node.
        raw_expr = None
        for child in call_node.children:
            if child.type in ("expression", "member_expression", "identifier", "struct_expression"):
                raw_expr = child
                break

        if raw_expr is None:
            continue

        # Unwrap expression wrapper
        actual_expr = _unwrap_expression(raw_expr)
        if actual_expr is None:
            continue

        # Handle struct_expression: .call{value: X}(...) wraps
        # the member_expression inside a struct_expression
        if actual_expr.type == "struct_expression":
            for child in actual_expr.children:
                unwrapped = _unwrap_expression(child)
                if unwrapped and unwrapped.type == "member_expression":
                    actual_expr = unwrapped
                    break

        if actual_expr.type == "member_expression":
            method_name = None
            receiver_node = None

            # member_expression children are either:
            #   [identifier, '.', identifier] — simple: token.transfer
            #   [expression, '.', identifier] — complex: IERC20(addr).transfer
            for child in actual_expr.children:
                if child.type == "identifier":
                    method_name = node_text(child)  # overwritten; last one wins
                elif child.type == "expression":
                    receiver_node = _unwrap_expression(child)

            if receiver_node is None:
                # Simple case: [identifier, '.', identifier]
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

            # Classify the call
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

        elif actual_expr.type == "identifier":
            # Direct function call (e.g., require, emit, or inherited function).
            # We don't count these as external unless very specific conditions.
            pass

    return calls


def _get_receiver_root_name(receiver_node) -> str | None:
    """Get the root identifier name from a receiver expression (already unwrapped)."""
    if receiver_node is None:
        return None
    if receiver_node.type == "identifier":
        return node_text(receiver_node)
    # For member_expression chains (a.b.c), get the root 'a'
    if receiver_node.type == "member_expression":
        for child in receiver_node.children:
            if child.type == "identifier":
                return node_text(child)
            elif child.type == "expression":
                inner = _unwrap_expression(child)
                return _get_receiver_root_name(inner)
    # For call_expression like IERC20(addr), get "IERC20"
    if receiver_node.type == "call_expression":
        for child in receiver_node.children:
            if child.type == "expression":
                inner = _unwrap_expression(child)
                return _get_receiver_root_name(inner)
            elif child.type == "identifier":
                return node_text(child)
    # For array_access (mappings/arrays), get the base array/mapping identifier (Change #3)
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
    
    # Strip mapping wrappers: mapping(keyType => valueType) -> valueType (Change #2)
    while "=>" in base:
        parts = base.split("=>")
        base = parts[-1].strip()
        # Strip trailing closing parenthesis from mapping definition
        if base.endswith(")"):
            base = base[:-1].strip()
            
    # Strip array brackets
    base = base.rstrip("[]").strip()
    
    # Check for Solidity primitive types
    if base in ("address", "bool", "string", "var", "int", "uint", "byte", "bytes", "fixed", "ufixed") or \
       base.startswith("uint") or base.startswith("int") or base.startswith("bytes") or \
       base.startswith("ufixed") or base.startswith("fixed"):
        return False
        
    # Interface naming convention: starts with 'I' + uppercase
    if len(base) >= 2 and base[0] == "I" and base[1].isupper():
        return True
        
    # Check if it's a known contract
    if base in all_contracts:
        return True
        
    # Common contract-typed identifiers / prefixes
    if any(base.startswith(prefix) for prefix in ("ERC20", "ERC721", "ERC1155", "IERC", "SafeERC")):
        return True
        
    # Principled check: in Solidity, custom types (contracts, interfaces)
    # start with an uppercase letter by standard convention.
    if base and base[0].isupper():
        return True
        
    return False


def _classify_call(method_name: str, receiver_name: str | None,
                   receiver_node, state_var_types: dict[str, str],
                   local_var_types: dict[str, str],
                   all_contracts: dict[str, ContractInfo],
                   allow_fallback: bool = False) -> str | None:
    """
    Determine if a member call is external. Returns a reason string or None.
    """
    if receiver_name in BUILTIN_GLOBALS and receiver_name != "this":
        # msg.sender, block.timestamp, abi.encode — NOT external calls
        # But msg.sender.call{...} IS — check method
        if receiver_name == "msg" or receiver_name == "tx":
            # These can lead to calls on addresses: the actual receiver is
            # deeper (e.g., msg.sender.call). But in the AST this is already
            # a member_expression chain. The method_name would be 'call' etc.
            if method_name in LOW_LEVEL_CALLS:
                return "low-level call on msg.sender/tx.origin"
            return None
        return None

    # Skip 'super' calls — these call parent implementations, not external
    if receiver_name == "super":
        return None

    # 1) Low-level calls
    if method_name in LOW_LEVEL_CALLS:
        return f"low-level .{method_name}()"

    # 2) SafeERC20 methods
    if method_name in SAFE_TRANSFER_METHODS:
        return f"SafeERC20 .{method_name}()"

    # 3) Check if receiver is a state variable with a contract/interface type
    if receiver_name and receiver_name in state_var_types:
        rtype = state_var_types[receiver_name]
        if _is_interface_or_contract_type(rtype, all_contracts):
            return f"call on contract-typed state var '{receiver_name}' (type: {rtype})"

    # 4) Check if receiver is a local variable with a contract/interface type
    if receiver_name and receiver_name in local_var_types:
        rtype = local_var_types[receiver_name]
        if _is_interface_or_contract_type(rtype, all_contracts):
            return f"call on contract-typed local var '{receiver_name}' (type: {rtype})"

    # 5) Inline cast: IERC20(addr).method() — receiver_name would be "IERC20"
    if receiver_name and _is_interface_or_contract_type(receiver_name, all_contracts):
        # Check if the receiver node is actually a call_expression (cast)
        if receiver_node and receiver_node.type == "call_expression":
            return f"inline cast call {receiver_name}(...).{method_name}()"
        # Or it's directly typed
        if receiver_name in all_contracts or (len(receiver_name) >= 2 and receiver_name[0] == "I" and receiver_name[1].isupper()):
            return f"call on interface/contract type '{receiver_name}'"

    # 6) Known external method name on a non-trivial receiver
    if method_name in EXTERNAL_CALL_METHODS and receiver_name and receiver_name not in BUILTIN_GLOBALS:
        if method_name in ("transfer", "transferFrom", "approve", "balanceOf", "allowance",
                           "mint", "burn", "burnFrom"):
            # These are common ERC20 methods — likely external
            return f"known ERC-like method .{method_name}() on '{receiver_name}'"
        elif method_name in ("deposit", "withdraw", "borrow", "repay", "liquidate",
                             "flashLoan", "execute", "unlock", "lock", "settle", "take",
                             "getSlot0", "accrueInterest", "flash", "claim"):
            # DeFi interaction methods
            return f"DeFi method .{method_name}() on '{receiver_name}'"
        elif method_name in ("getPrice", "latestAnswer", "latestRoundData"):
            return f"oracle method .{method_name}() on '{receiver_name}'"
        else:
            return f"known external method .{method_name}() on '{receiver_name}'"

    # 7) Check if this could be "address-typed variable .call/transfer"
    # via struct_expression wrapping
    if method_name in LOW_LEVEL_CALLS:
        return f"low-level .{method_name}()"

    # 8) Change #5 keyword fallback (dry-run evaluation only, not committed in dataset)
    if allow_fallback and receiver_name and not receiver_name[0].isupper():
        lower_name = receiver_name.lower()
        if any(kw in lower_name for kw in ("token", "vault", "pool", "oracle", "router", "manager", "registry", "factory", "strategy", "game", "governor", "bridge", "escrow", "wallet", "aggregator")):
            if receiver_name not in BUILTIN_GLOBALS and method_name not in BUILTIN_MEMBERS:
                return f"Change #5 fallback: '{receiver_name}.{method_name}()'"

    if allow_fallback and receiver_node and receiver_node.type == "member_expression":
        recv_text = node_text(receiver_node).lower()
        if any(kw in recv_text for kw in ("token", "vault", "pool", "oracle", "router", "manager", "registry", "factory", "strategy", "game", "governor", "bridge", "escrow", "wallet", "aggregator")):
            if method_name not in BUILTIN_MEMBERS:
                return f"Change #5 fallback member chain: '{node_text(receiver_node)}.{method_name}()'"

    return None


def find_state_var_accesses(func_node, all_state_vars: set[str],
                            local_vars: set[str]) -> list[str]:
    """
    Find all state variable accesses in a function AST node.
    An identifier references a state variable if:
      - It appears as an identifier in an expression context
      - It is NOT a local variable, parameter, or built-in
      - It IS in the resolved state variable set
    """
    accessed = set()

    for ident_node in find_descendants_by_type(func_node, "identifier"):
        name = node_text(ident_node)

        if name in local_vars:
            continue
        if name in BUILTIN_GLOBALS:
            continue
        if name in all_state_vars:
            # Verify it's in an expression context (not a type, declaration, etc.)
            parent = ident_node.parent
            if parent and parent.type in ("type_name", "user_defined_type", "pragma_directive",
                                          "import_directive", "inheritance_specifier",
                                          "emit_statement", "event_definition",
                                          "error_definition"):
                continue
            accessed.add(name)

    return sorted(accessed)


# ============================================================================
# VFP-LEVEL ANALYSIS (reused filter logic)
# ============================================================================

def is_interaction_finding(finding: dict) -> bool:
    cat = finding.get("category", {})
    for level, cwes in cat.items():
        for cwe in cwes:
            if cwe in INTERACTION_CWES:
                return True
    text = (finding.get("title", "") + " " + finding.get("description", ""))
    return bool(INTERACTION_KW_RE.search(text))


def extract_function_locations(finding: dict) -> list[dict]:
    locs = []
    for loc_str in finding.get("location", []):
        if "::" in loc_str:
            parts = loc_str.split("::")
            file_part = parts[0].strip()
            func_and_line = parts[1].strip() if len(parts) > 1 else ""
            func_name = func_and_line.split("#")[0].strip()
            locs.append({"file": file_part, "function": func_name, "raw": loc_str})
    return locs


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def load_all_vfps():
    vfps = []
    for f in sorted(VFP_VULN_DIR.glob("vfp_*.json")):
        with open(f) as fh:
            vfps.append(json.load(fh))
    return vfps


def find_contract_for_file(file_key: str, all_contracts: dict[str, ContractInfo],
                           func_name: str, contracts_in_file: dict[str, ContractInfo] | None = None) -> str | None:
    """
    Given a file name and function name, find the contract that defines this function.
    Strategy: prefer the contract that directly defines the function, then fall back
    to the last non-interface contract.
    """
    # 0) First check inside the current file's contracts to see if any directly defines this function (Change #1)
    if contracts_in_file:
        file_candidates = []
        for cname, cinfo in contracts_in_file.items():
            if func_name in cinfo.functions:
                file_candidates.append(cname)
        if len(file_candidates) == 1:
            return file_candidates[0]
        elif len(file_candidates) > 1:
            # Prefer non-interface, non-library
            for c in file_candidates:
                info = contracts_in_file[c]
                if not info.is_interface and not info.is_library:
                    return c
            return file_candidates[0]

        # Check if any contract in the file inherits this function
        for cname, cinfo in contracts_in_file.items():
            if cinfo.is_interface or cinfo.is_library:
                continue
            all_funcs = resolve_all_functions(cname, all_contracts)
            if func_name in all_funcs:
                return cname

    # First: find contracts that directly define this function in all contracts
    candidates = []
    for cname, cinfo in all_contracts.items():
        if func_name in cinfo.functions:
            candidates.append(cname)

    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        # Prefer non-interface, non-library
        for c in candidates:
            info = all_contracts[c]
            if not info.is_interface and not info.is_library:
                return c
        return candidates[0]

    # Fallback: find any contract that could inherit this function
    for cname, cinfo in all_contracts.items():
        if cinfo.is_interface or cinfo.is_library:
            continue
        all_funcs = resolve_all_functions(cname, all_contracts)
        if func_name in all_funcs:
            return cname

    # Last resort: just return the last non-interface contract
    if contracts_in_file:
        for cname, cinfo in reversed(list(contracts_in_file.items())):
            if not cinfo.is_interface and not cinfo.is_library:
                return cname

    for cname, cinfo in reversed(list(all_contracts.items())):
        if not cinfo.is_interface and not cinfo.is_library:
            return cname

    return None


def run():
    print("=" * 80)
    print("HyperVul — AST-based Positive Hyperedge Analysis (tree-sitter)")
    print("=" * 80)

    vfps = load_all_vfps()
    total_findings = sum(len(v.get("findings", [])) for v in vfps)
    print(f"\nLoaded {len(vfps)} VFPs with {total_findings} total findings.")

    # ── STEP 1: Same CWE + keyword filter ──────────────────────────────
    interaction_findings = []
    for vfp in vfps:
        for finding in vfp.get("findings", []):
            if is_interaction_finding(finding):
                interaction_findings.append((vfp, finding))

    print(f"\nStep 1: {len(interaction_findings)} interaction-type findings (unchanged).")

    # ── STEP 2: Extract function-level locations ────────────────────────
    findings_with_locs = []
    for vfp, finding in interaction_findings:
        locs = extract_function_locations(finding)
        if locs:
            findings_with_locs.append((vfp, finding, locs))

    print(f"Step 2: {len(findings_with_locs)} findings with function-level locations.")

    # ── STEP 3 + 4: AST analysis ──────────────────────────────────────
    print(f"\nStep 3: AST-based source code analysis...")

    # Cache parsed contracts per VFP
    vfp_contracts_cache: dict[str, dict[str, dict[str, ContractInfo]]] = {}

    analysis_results = []
    stats = Counter()
    # Track uplift sources
    inheritance_var_uplift = 0
    inheritance_call_uplift = 0

    for vfp, finding, func_locs in findings_with_locs:
        vfp_id = vfp["vfp_id"]
        affected_files = vfp.get("affected_files", {})

        # Parse all affected files for this VFP (cached)
        if vfp_id not in vfp_contracts_cache:
            file_contracts = {}
            all_contracts_in_vfp: dict[str, ContractInfo] = {}
            for fname, source in affected_files.items():
                try:
                    parsed = parse_contracts(source)
                    file_contracts[fname] = parsed
                    all_contracts_in_vfp.update(parsed)
                except Exception as e:
                    stats["parse_error"] += 1
            vfp_contracts_cache[vfp_id] = {
                "files": file_contracts,
                "all": all_contracts_in_vfp,
            }

        cached = vfp_contracts_cache[vfp_id]
        all_contracts = cached["all"]
        file_contracts = cached["files"]

        for loc in func_locs:
            file_key = loc["file"]
            func_name = loc["function"]

            # Find the source
            source_code = affected_files.get(file_key)
            if source_code is None:
                for af_key in affected_files:
                    if af_key.endswith(file_key) or file_key.endswith(af_key):
                        source_code = affected_files[af_key]
                        file_key = af_key
                        break

            if source_code is None:
                stats["source_not_found"] += 1
                analysis_results.append({
                    "vfp_id": vfp_id,
                    "finding_id": finding["id"],
                    "finding_title": finding.get("title", ""),
                    "severity": finding.get("severity", "Unknown"),
                    "file": loc["file"],
                    "function": func_name,
                    "source_found": False,
                    "constructable": False,
                    "constructable_fb": False,
                    "external_calls": [],
                    "external_calls_fb": [],
                    "state_vars_accessed": [],
                    "inherited_vars_used": False,
                    "inherited_calls_used": False,
                })
                continue

            stats["source_found"] += 1

            # Find the contract containing this function
            contracts_in_file = file_contracts.get(file_key, {})
            # Also try the original loc file key
            if not contracts_in_file:
                contracts_in_file = file_contracts.get(loc["file"], {})
            # Merge with all contracts for inheritance resolution
            merged_contracts = dict(all_contracts)
            merged_contracts.update(contracts_in_file)

            contract_name = find_contract_for_file(file_key, merged_contracts, func_name, contracts_in_file)

            if contract_name is None:
                stats["contract_not_found"] += 1
                analysis_results.append({
                    "vfp_id": vfp_id,
                    "finding_id": finding["id"],
                    "finding_title": finding.get("title", ""),
                    "severity": finding.get("severity", "Unknown"),
                    "file": loc["file"],
                    "function": func_name,
                    "source_found": True,
                    "constructable": False,
                    "constructable_fb": False,
                    "external_calls": [],
                    "external_calls_fb": [],
                    "state_vars_accessed": [],
                    "inherited_vars_used": False,
                    "inherited_calls_used": False,
                })
                continue

            contract_info = merged_contracts[contract_name]

            # Resolve full inheritance chain
            all_state_vars = resolve_all_state_vars(contract_name, merged_contracts)
            all_state_var_types = resolve_all_state_var_types(contract_name, merged_contracts)
            all_funcs = resolve_all_functions(contract_name, merged_contracts)

            # Get the function AST node
            func_node = all_funcs.get(func_name)
            if func_node is None:
                stats["func_not_found_in_ast"] += 1
                analysis_results.append({
                    "vfp_id": vfp_id,
                    "finding_id": finding["id"],
                    "finding_title": finding.get("title", ""),
                    "severity": finding.get("severity", "Unknown"),
                    "file": loc["file"],
                    "function": func_name,
                    "source_found": True,
                    "constructable": False,
                    "constructable_fb": False,
                    "external_calls": [],
                    "external_calls_fb": [],
                    "state_vars_accessed": [],
                    "inherited_vars_used": False,
                    "inherited_calls_used": False,
                })
                continue

            # ── State variable accesses ──
            local_vars = extract_local_vars(func_node)
            accessed_vars = find_state_var_accesses(func_node, all_state_vars, local_vars)

            # ── External calls (Official: changes 1-4) ──
            ext_calls = find_external_calls_ast(func_node, all_state_var_types, merged_contracts, allow_fallback=False)

            # ── External calls (Hypothetical: changes 1-5) ──
            ext_calls_fb = find_external_calls_ast(func_node, all_state_var_types, merged_contracts, allow_fallback=True)

            # Check if any external call comes from an inherited context
            # (receiver is an inherited state variable)
            own_vars = contract_info.state_vars
            inherited_call = False
            for ec in ext_calls:
                recv = ec.get("receiver", "")
                if recv in all_state_vars and recv not in own_vars:
                    inherited_call = True
                    break
                # Also check if the call method is inherited
                if "inherited" in ec.get("reason", "").lower():
                    inherited_call = True
                    break

            # Check if any accessed var is inherited (not in own contract)
            inherited_var = False
            for v in accessed_vars:
                if v in all_state_vars and v not in own_vars:
                    inherited_var = True
                    break

            has_ext = len(ext_calls) > 0
            has_sv = len(accessed_vars) > 0
            constructable = has_ext and has_sv

            has_ext_fb = len(ext_calls_fb) > 0
            constructable_fb = has_ext_fb and has_sv

            if has_ext:
                stats["has_external_call"] += 1
            if has_sv:
                stats["has_state_var"] += 1
            if constructable:
                stats["has_both"] += 1

            analysis_results.append({
                "vfp_id": vfp_id,
                "finding_id": finding["id"],
                "finding_title": finding.get("title", ""),
                "severity": finding.get("severity", "Unknown"),
                "file": loc["file"],
                "function": func_name,
                "contract": contract_name,
                "source_found": True,
                "constructable": constructable,
                "constructable_fb": constructable_fb,
                "external_calls": [{"call_text": c["call_text"], "method": c["method"],
                                     "receiver": c["receiver"], "reason": c["reason"]}
                                    for c in ext_calls],
                "external_calls_fb": [{"call_text": c["call_text"], "method": c["method"],
                                        "receiver": c["receiver"], "reason": c["reason"]}
                                       for c in ext_calls_fb],
                "state_vars_accessed": accessed_vars,
                "all_state_vars_in_chain": sorted(all_state_vars)[:30],
                "own_state_vars": sorted(own_vars),
                "inherited_vars_used": inherited_var,
                "inherited_calls_used": inherited_call,
                "function_source": node_text(func_node)[:500],
            })

    # ── STEP 4: Count constructable hyperedges ────────────────────────

    print(f"\n{'='*80}")
    print(f"Step 3 Statistics:")
    print(f"{'='*80}")
    total_analyzed = stats["source_found"]
    print(f"  Source found:           {stats['source_found']}")
    print(f"  Source NOT found:       {stats['source_not_found']}")
    print(f"  Parse errors:           {stats.get('parse_error', 0)}")
    print(f"  Contract not found:     {stats.get('contract_not_found', 0)}")
    print(f"  Function not in AST:    {stats.get('func_not_found_in_ast', 0)}")
    print(f"  Has external call:      {stats['has_external_call']}")
    print(f"  Has state var access:   {stats['has_state_var']}")
    print(f"  Has BOTH:               {stats['has_both']}")

    # Deduplicate Official (Changes 1-4)
    seen = set()
    unique_constructable = []
    for r in analysis_results:
        if r["constructable"]:
            key = (r["vfp_id"], r["finding_id"], r["function"])
            if key not in seen:
                seen.add(key)
                unique_constructable.append(r)

    # Deduplicate with Fallback (Changes 1-5) (dry-run evaluation only)
    seen_fb = set()
    unique_constructable_fb = []
    for r in analysis_results:
        if r["constructable_fb"]:
            key = (r["vfp_id"], r["finding_id"], r["function"])
            if key not in seen_fb:
                seen_fb.add(key)
                unique_constructable_fb.append(r)

    # Count inheritance-based uplifts
    inh_var_count = sum(1 for r in unique_constructable if r.get("inherited_vars_used"))
    inh_call_count = sum(1 for r in unique_constructable if r.get("inherited_calls_used"))

    finding_keys = set((r["vfp_id"], r["finding_id"]) for r in unique_constructable)
    vfp_keys = set(r["vfp_id"] for r in unique_constructable)

    sev_dist = Counter(r["severity"] for r in unique_constructable)

    print(f"\n{'='*80}")
    print(f"  DECISION GATE NUMBER (AST-based Changes #1-4)")
    print(f"  Constructable positive hyperedges: {len(unique_constructable)}")
    print(f"{'='*80}")
    print(f"  From {len(finding_keys)} unique findings")
    print(f"  Across {len(vfp_keys)} unique VFPs")
    print(f"\n  Severity distribution:")
    for sev, cnt in sev_dist.most_common():
        print(f"    {sev}: {cnt}")

    # Report fallback count contribution separately
    fallback_count = len(unique_constructable_fb)
    additional_fallback_count = fallback_count - len(unique_constructable)
    print(f"\n{'='*80}")
    print(f"  DRY-RUN EVALUATION: Change #5 (Keyword Fallback)")
    print(f"  Constructable hyperedges with Change #5 enabled: {fallback_count}")
    print(f"  ADDITIONAL hyperedges from Change #5 fallback:    {additional_fallback_count}")
    print(f"{'='*80}")

    # ── STEP 5: Comparison ───────────────────────────────────────────

    PREV_COUNT = 61
    delta = len(unique_constructable) - PREV_COUNT

    print(f"\n{'='*80}")
    print(f"Step 5 — Comparison with Regex-based Analysis")
    print(f"{'='*80}")
    print(f"  Previous (regex):  {PREV_COUNT}")
    print(f"  Current (AST):     {len(unique_constructable)}")
    print(f"  Delta:             {'+' if delta >= 0 else ''}{delta}")
    print(f"\n  Uplift breakdown:")
    print(f"    Hyperedges using inherited state vars:     {inh_var_count}")
    print(f"    Hyperedges using inherited/interface calls: {inh_call_count}")
    print(f"    (Some may use both)")

    # ── Examples ──────────────────────────────────────────────────────

    print(f"\n{'='*80}")
    print(f"Examples — New Constructable Hyperedges (AST-detected)")
    print(f"{'='*80}")

    # Load previous results to find which are new
    prev_file = RESULTS_DIR / "forge_constructable_hyperedges.json"
    prev_keys = set()
    if prev_file.exists():
        with open(prev_file) as f:
            prev_data = json.load(f)
            for d in prev_data:
                prev_keys.add((d["vfp_id"], d["finding_id"], d["function"]))

    new_hyperedges = [r for r in unique_constructable
                      if (r["vfp_id"], r["finding_id"], r["function"]) not in prev_keys]
    retained = [r for r in unique_constructable
                if (r["vfp_id"], r["finding_id"], r["function"]) in prev_keys]

    print(f"\n  Retained from regex analysis: {len(retained)}")
    print(f"  Newly detected by AST:        {len(new_hyperedges)}")

    # Show up to 5 new examples
    shown = 0
    for r in new_hyperedges:
        if shown >= 5:
            break
        print(f"\n  {'─'*50}")
        print(f"  VFP:      {r['vfp_id']}")
        print(f"  Finding:  {r['finding_title'][:80]}")
        print(f"  Severity: {r['severity']}")
        print(f"  Contract: {r.get('contract', '?')}")
        print(f"  Function: {r['function']}")
        print(f"  Inherited state vars used: {r.get('inherited_vars_used', False)}")
        print(f"  Inherited calls used:      {r.get('inherited_calls_used', False)}")
        print(f"  External calls ({len(r['external_calls'])}):")
        for ec in r["external_calls"][:3]:
            print(f"    → [{ec['reason']}] {ec['call_text'][:80]}")
        print(f"  State vars accessed ({len(r['state_vars_accessed'])}):")
        for sv in r["state_vars_accessed"][:5]:
            own = r.get("own_state_vars", [])
            marker = " (inherited)" if sv not in own else ""
            print(f"    → {sv}{marker}")
        shown += 1

    # Show examples of previously-missed hyperedges that used inheritance
    inh_examples = [r for r in new_hyperedges if r.get("inherited_vars_used") or r.get("inherited_calls_used")]
    if inh_examples:
        print(f"\n{'='*80}")
        print(f"Examples — Inheritance-enabled Hyperedges")
        print(f"{'='*80}")
        for r in inh_examples[:3]:
            print(f"\n  {'─'*50}")
            print(f"  VFP:      {r['vfp_id']}")
            print(f"  Finding:  {r['finding_title'][:80]}")
            print(f"  Contract: {r.get('contract', '?')} (bases: {r.get('all_state_vars_in_chain', [])[:5]}...)")
            print(f"  Function: {r['function']}")
            own = set(r.get("own_state_vars", []))
            for sv in r["state_vars_accessed"]:
                marker = " ← INHERITED" if sv not in own else ""
                print(f"    state var: {sv}{marker}")
            for ec in r["external_calls"][:2]:
                print(f"    ext call:  {ec['receiver']}.{ec['method']}() — {ec['reason']}")

    # ── Save results ──────────────────────────────────────────────────

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "method": "tree-sitter AST",
        "total_vfps": len(vfps),
        "total_findings": total_findings,
        "interaction_findings": len(interaction_findings),
        "findings_with_func_loc": len(findings_with_locs),
        "source_found": stats["source_found"],
        "source_not_found": stats["source_not_found"],
        "parse_errors": stats.get("parse_error", 0),
        "contract_not_found": stats.get("contract_not_found", 0),
        "func_not_found_in_ast": stats.get("func_not_found_in_ast", 0),
        "has_external_call": stats["has_external_call"],
        "has_state_var_access": stats["has_state_var"],
        "has_both": stats["has_both"],
        "constructable_hyperedges": len(unique_constructable),
        "from_unique_findings": len(finding_keys),
        "from_unique_vfps": len(vfp_keys),
        "severity_distribution": dict(sev_dist),
        "previous_regex_count": PREV_COUNT,
        "delta": delta,
        "inherited_state_var_uplift": inh_var_count,
        "inherited_call_uplift": inh_call_count,
        "retained_from_regex": len(retained),
        "newly_detected_by_ast": len(new_hyperedges),
        # Fallback dry-run evaluation fields
        "fallback_dryrun_total_constructable": fallback_count,
        "fallback_dryrun_additional_count": additional_fallback_count
    }

    with open(RESULTS_DIR / "forge_ast_hyperedge_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Save detailed results (without full source)
    detailed_out = []
    for r in analysis_results:
        d = dict(r)
        d.pop("function_source", None)
        d.pop("all_state_vars_in_chain", None)
        d.pop("own_state_vars", None)
        detailed_out.append(d)
    with open(RESULTS_DIR / "forge_ast_hyperedge_detailed.json", "w") as f:
        json.dump(detailed_out, f, indent=2)

    # Save constructable
    constr_out = []
    for r in unique_constructable:
        constr_out.append({
            "vfp_id": r["vfp_id"],
            "finding_id": r["finding_id"],
            "finding_title": r["finding_title"],
            "severity": r["severity"],
            "file": r["file"],
            "function": r["function"],
            "contract": r.get("contract"),
            "external_calls": r["external_calls"],
            "state_vars_accessed": r["state_vars_accessed"],
            "inherited_vars_used": r.get("inherited_vars_used", False),
            "inherited_calls_used": r.get("inherited_calls_used", False),
        })
    with open(RESULTS_DIR / "forge_ast_constructable_hyperedges.json", "w") as f:
        json.dump(constr_out, f, indent=2)

    print(f"\nResults saved to {RESULTS_DIR}/")
    print(f"  forge_ast_hyperedge_summary.json")
    print(f"  forge_ast_hyperedge_detailed.json")
    print(f"  forge_ast_constructable_hyperedges.json")

    return summary, unique_constructable


if __name__ == "__main__":
    summary, constructable = run()
