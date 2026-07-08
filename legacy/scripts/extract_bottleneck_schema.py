#!/usr/bin/env python3
"""
HyperVul — Stage 2: Semantic Bottleneck Schema Extractor
========================================================

Materializes the "Semantic Bottleneck Extraction Schema" designed in Stage 1:
for each function-hyperedge item, emit a structured, mostly-symbolic record with

  (1) function_hub  — signature ONLY (name, args, visibility, mutability, modifiers)
                      plus a body-stripped `signature_text` (the only LM input).
  (2) state_nodes   — split read/write: one node per (state var, access) pair.
  (3) callee_nodes  — external target + method + security_context
                      (nonReentrant / safe_erc20 / low_level / return_checked).

This is the "atomic, text-free" representation: the function keeps its identity
(signature), but the {function, state, callee} relation must be reassembled through
structure rather than read off from body text.

Reuse
-----
- `negative_hyperedge_sampling` (nhs): AST parsing, inheritance resolution, external-call
  classification, local-var extraction, expression unwrapping  — heavy reuse.
- `build_signature_features` (bsf): `to_signature` (body stripping) + Aave/PROJECT_ROOT
  resolvers; transitively imports `extract_features` (ef) for OZ/DAppSCAN/FORGE source
  location (same proven resolution path used by the sibling scripts).

The two genuinely new pieces (Stage 1 plan) live here:
  * `type_bucket()`            — symbolic type classifier.
  * `classify_state_accesses()`— read/write splitter over tree-sitter-solidity nodes.
A thin structured wrapper around `nhs.find_external_calls_ast` adds target_kind /
target_type / security_context (Step 3) without discarding the existing classification.

NOTE: no embedding happens here. `function_hub.signature_text` is produced for a later
stage to feed to `extract_features.batch_encode_texts` (SmartBERT, 768-d).
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/pollmix/Coding/HyperVul")
sys.path.append(str(PROJECT_ROOT / "scripts"))

import extract_features as ef          # OZ/DAppSCAN/FORGE resolvers (loads SmartBERT at import)
import negative_hyperedge_sampling as nhs
import build_signature_features as bsf  # to_signature + Aave/PROJECT_ROOT resolvers


# Parents under which a state-var identifier is NOT a real data access
# (mirrors nhs.find_state_var_accesses exclusions).
_EXCLUDED_IDENT_PARENTS = {
    "type_name", "user_defined_type", "pragma_directive", "import_directive",
    "inheritance_specifier", "emit_statement", "event_definition", "error_definition",
}


# ============================================================================
# NEW HELPER 1 — symbolic type bucket
# ============================================================================

def type_bucket(type_str: str | None, all_contracts: dict | None = None) -> str:
    """Collapse a Solidity type string into one symbolic bucket.

    Buckets: address|uint|int|bool|bytes|string|mapping|array|struct|contract|enum|other.
    Best-effort: user-defined uppercase types resolve to contract (interface/struct/enum
    are indistinguishable from a bare type string without a symbol table; `all_contracts`
    is consulted when available to recover library/contract names).
    """
    if not type_str:
        return "other"
    t = type_str.strip()
    if t.startswith("mapping"):
        return "mapping"
    if t.endswith("]"):                      # T[] or T[N]
        return "array"
    # strip data-location / payable qualifiers
    base = t
    for kw in ("memory", "storage", "calldata", "payable"):
        base = base.replace(kw, "")
    base = base.strip()
    if not base:
        return "other"
    if base == "address" or base.startswith("address"):
        return "address"
    if base == "bool":
        return "bool"
    if base == "string" or base.startswith("string"):
        return "string"
    if base.startswith("uint"):
        return "uint"
    if base.startswith("int"):
        return "int"
    if base == "byte" or base.startswith("bytes"):
        return "bytes"
    if base.startswith("ufixed") or base.startswith("fixed"):
        return "other"
    # user-defined type → contract (best effort)
    if all_contracts and base in all_contracts:
        return "contract"
    if base[0].isupper():
        return "contract"
    return "other"


# ============================================================================
# NEW HELPER 2 — read/write classification of state-variable accesses
# ============================================================================

def _root_identifier_node(node):
    """Resolve the leftmost (root) identifier node of an l-value expression.

    e.g. `balances[msg.sender]` -> `balances`; `a.b.c` -> `a`; `holders.push` -> `holders`.
    """
    node = nhs._unwrap_expression(node) if node is not None else None
    if node is None:
        return None
    if node.type == "identifier":
        return node
    if node.type in ("member_expression", "array_access", "call_expression"):
        if node.children:
            return _root_identifier_node(node.children[0])
    return None


def _collect_write_targets(func_node) -> dict[tuple[int, int], set[str]]:
    """Map (start_byte, end_byte) of an l-value root identifier -> access modes.

    A byte-span key (not id()) is required: tree-sitter-python returns fresh Node
    wrappers on every traversal, so object identity is not stable across walks.

    plain `=`            -> write
    augmented `+=`,`-=`… -> read + write
    `++` / `--`          -> read + write
    `delete x`           -> write
    `x.push(...)`/`.pop()`-> write (receiver mutated)
    """
    targets: dict[tuple[int, int], set[str]] = {}

    def mark(node, *modes):
        if node is None:
            return
        targets.setdefault((node.start_byte, node.end_byte), set()).update(modes)

    for a in nhs.find_descendants_by_type(func_node, "assignment_expression"):
        mark(_root_identifier_node(a.child_by_field_name("left")), "write")

    for a in nhs.find_descendants_by_type(func_node, "augmented_assignment_expression"):
        mark(_root_identifier_node(a.child_by_field_name("left")), "read", "write")

    for u in nhs.find_descendants_by_type(func_node, "update_expression"):
        mark(_root_identifier_node(u.child_by_field_name("argument")), "read", "write")

    for un in nhs.find_descendants_by_type(func_node, "unary_expression"):
        first = un.children[0] if un.children else None
        if first is not None and (first.type == "delete" or nhs.node_text(first) == "delete"):
            mark(_root_identifier_node(un.child_by_field_name("argument")), "write")

    for call in nhs.find_descendants_by_type(func_node, "call_expression"):
        callee = nhs._unwrap_expression(call.children[0]) if call.children else None
        if callee is not None and callee.type == "member_expression":
            idents = [c for c in callee.children if c.type == "identifier"]
            method = nhs.node_text(idents[-1]) if idents else None
            if method in ("push", "pop"):
                mark(_root_identifier_node(callee.children[0]), "write")

    return targets


def classify_state_accesses(func_node, all_state_vars: set[str], local_vars: set[str],
                            state_var_types: dict[str, str],
                            all_contracts: dict) -> list[dict]:
    """Split state-variable accesses into read/write nodes (Stage 1 Step 2).

    Returns one node per (variable, access-mode) pair, so a read-and-written variable
    yields two nodes. Filtering mirrors nhs.find_state_var_accesses.
    """
    write_targets = _collect_write_targets(func_node)
    var_modes: dict[str, set[str]] = {}

    for ident in nhs.find_descendants_by_type(func_node, "identifier"):
        name = nhs.node_text(ident)
        if name in local_vars or name in nhs.BUILTIN_GLOBALS:
            continue
        if name not in all_state_vars:
            continue
        parent = ident.parent
        if parent is not None and parent.type in _EXCLUDED_IDENT_PARENTS:
            continue
        modes = write_targets.get((ident.start_byte, ident.end_byte))
        if modes:
            var_modes.setdefault(name, set()).update(modes)
        else:
            var_modes.setdefault(name, set()).add("read")

    nodes = []
    for name in sorted(var_modes):
        raw_type = state_var_types.get(name, "")
        bucket = type_bucket(raw_type, all_contracts)
        for access in ("read", "write"):          # deterministic order
            if access in var_modes[name]:
                nodes.append({
                    "name": name,
                    "type": raw_type,
                    "type_bucket": bucket,
                    "access": access,
                })
    return nodes


# ============================================================================
# NEW HELPER 3 — structured callee + security context
# ============================================================================

def _local_var_types(func_node) -> dict[str, str]:
    """Parameter + local declaration name->type map (mirrors find_external_calls_ast)."""
    lvt: dict[str, str] = {}
    for param in nhs.find_descendants_by_type(func_node, "parameter"):
        pn = pt = None
        for ch in param.children:
            if ch.type == "identifier":
                pn = nhs.node_text(ch)
            elif ch.type == "type_name":
                pt = nhs.node_text(ch)
        if pn and pt:
            lvt[pn] = pt
    for vds in nhs.find_descendants_by_type(func_node, "variable_declaration_statement"):
        for vd in nhs.find_descendants_by_type(vds, "variable_declaration"):
            vn = vt = None
            for ch in vd.children:
                if ch.type == "identifier":
                    vn = nhs.node_text(ch)
                elif ch.type == "type_name":
                    vt = nhs.node_text(ch)
            if vn and vt:
                lvt[vn] = vt
    return lvt


def _resolve_target_type(receiver, reason, state_var_types, local_var_types, merged):
    """Best-effort resolved type of the call receiver (interface/contract name or address)."""
    if receiver and receiver in state_var_types and \
            nhs._is_interface_or_contract_type(state_var_types[receiver], merged):
        return state_var_types[receiver]
    if receiver and receiver in local_var_types and \
            nhs._is_interface_or_contract_type(local_var_types[receiver], merged):
        return local_var_types[receiver]
    if "inline cast call " in reason:
        return reason.split("inline cast call ")[1].split("(")[0].strip()
    if "call on interface/contract type '" in reason:
        return reason.split("call on interface/contract type '")[1].split("'")[0].strip()
    if "(type: " in reason:
        return reason.split("(type: ")[1].split(")")[0].strip()
    if receiver and nhs._is_interface_or_contract_type(receiver, merged):
        return receiver
    return ""


_ERC_LIKE_METHODS = {"transfer", "transferFrom", "approve", "balanceOf", "allowance",
                     "mint", "burn", "burnFrom"}


def _target_kind(method, target_type, low_level, safe_erc20, merged) -> str:
    """interface|contract|library|erc_like|address_low_level|unknown."""
    if low_level:
        return "address_low_level"
    if target_type:
        base = target_type.rstrip("[]").strip()
        info = merged.get(base)
        if info is not None:
            if getattr(info, "is_library", False):
                return "library"
            if getattr(info, "is_interface", False):
                return "interface"
            return "contract"
        if len(base) >= 2 and base[0] == "I" and base[1].isupper():
            return "interface"
        if base and base[0].isupper():
            return "contract"
    if safe_erc20 or method in _ERC_LIKE_METHODS:
        return "erc_like"
    return "unknown"


def _call_is_cross(target_type, contract_name, merged) -> bool:
    """Receiver resolves to another contract present in the bundle (nhs.check_is_cross semantics)."""
    base = (target_type or "").rstrip("[]").strip()
    return bool(base) and base in merged and base != contract_name


def _is_reentrancy_guard(modifier_name: str) -> bool:
    m = modifier_name.lower()
    return "reentr" in m or m in ("lock", "locked")


def _is_return_checked(call_node) -> bool:
    """Whether a low-level call's return value is consumed (captured / required / branched)."""
    n = call_node.parent
    depth = 0
    while n is not None and depth < 8:
        t = n.type
        if t in ("variable_declaration_statement", "variable_declaration_tuple",
                 "assignment_expression"):
            return True                      # captured into a variable
        if t == "call_expression":
            callee = nhs._unwrap_expression(n.children[0]) if n.children else None
            name = nhs.node_text(callee) if callee is not None else ""
            if name in ("require", "assert"):
                return True
        if t in ("if_statement", "while_statement", "binary_expression", "unary_expression"):
            return True                      # used in a condition / negation
        if t == "expression_statement":
            return False                     # bare `x.call(...);` — discarded
        if t in ("function_body", "function_definition"):
            return False
        n = n.parent
        depth += 1
    return False


# `call`/`delegatecall`/`staticcall` are always low-level; `transfer`/`send` are only
# low-level (ETH) on an address receiver — on a token interface they are ERC-like.
_ALWAYS_LOW_LEVEL = {"call", "delegatecall", "staticcall"}
_ADDRESS_LOW_LEVEL = {"transfer", "send"}


def _is_low_level(method: str, target_type: str, merged) -> bool:
    if method in _ALWAYS_LOW_LEVEL:
        return True
    if method in _ADDRESS_LOW_LEVEL:
        return not (target_type and nhs._is_interface_or_contract_type(target_type, merged))
    return False


def _return_checked_map(func_node) -> dict[str, bool]:
    """call_text(<=120 chars) -> whether the call's return value is consumed.

    Keyed off the same call_expression node set / call_text convention that
    nhs.find_external_calls_ast uses, so options-syntax calls (`.call{value:..}()`) match.
    """
    out: dict[str, bool] = {}
    for call in nhs.find_descendants_by_type(func_node, "call_expression"):
        out[nhs.node_text(call)[:120]] = _is_return_checked(call)
    return out


def build_callee_nodes(func_node, state_var_types, merged, contract_name,
                       func_modifiers) -> list[dict]:
    ext_calls = nhs.find_external_calls_ast(func_node, state_var_types, merged,
                                            allow_fallback=False)
    local_var_types = _local_var_types(func_node)
    non_reentrant = any(_is_reentrancy_guard(m) for m in func_modifiers)
    checked_map = _return_checked_map(func_node)

    nodes = []
    for ec in ext_calls:
        receiver = ec["receiver"]
        method = ec["method"]
        reason = ec["reason"]
        target_type = _resolve_target_type(receiver, reason, state_var_types,
                                           local_var_types, merged)
        low_level = _is_low_level(method, target_type, merged)
        safe_erc20 = method in nhs.SAFE_TRANSFER_METHODS or "SafeERC20" in reason
        nodes.append({
            "target": receiver,
            "target_type": target_type,
            "target_kind": _target_kind(method, target_type, low_level, safe_erc20, merged),
            "method": method,
            "is_cross_contract": _call_is_cross(target_type, contract_name, merged),
            "security_context": {
                "nonReentrant": non_reentrant,
                "safe_erc20": safe_erc20,
                "low_level": low_level,
                "return_checked": checked_map.get(ec["call_text"], False) if low_level else False,
            },
        })
    return nodes


# ============================================================================
# FUNCTION HUB (signature only)
# ============================================================================

def _param_to_dict(param_node, all_contracts) -> dict:
    pname = ptype = None
    for ch in param_node.children:
        if ch.type == "identifier":
            pname = nhs.node_text(ch)
        elif ch.type == "type_name":
            ptype = nhs.node_text(ch)
    if ptype is None:                        # fallback: whole param text
        ptype = nhs.node_text(param_node)
    return {"name": pname, "type": ptype or "", "type_bucket": type_bucket(ptype, all_contracts)}


def build_function_hub(func_node, all_contracts) -> dict:
    name = nhs._get_function_name(func_node) or ""
    visibility = "default"
    state_mutability = "nonpayable"
    modifiers: list[str] = []
    args: list[dict] = []
    returns: list[dict] = []

    for c in func_node.children:
        if c.type == "visibility":
            visibility = nhs.node_text(c).strip()
        elif c.type == "state_mutability":
            state_mutability = nhs.node_text(c).strip()
        elif c.type == "modifier_invocation":
            nm = nhs.get_identifier_name(c)
            if nm:
                modifiers.append(nm)
        elif c.type == "parameter":          # direct children = the arguments
            args.append(_param_to_dict(c, all_contracts))
        elif c.type == "return_type_definition":
            for p in nhs.find_descendants_by_type(c, "parameter"):
                returns.append(_param_to_dict(p, all_contracts))

    return {
        "name": name,
        "visibility": visibility,
        "state_mutability": state_mutability,
        "modifiers": modifiers,
        "args": args,
        "returns": returns,
        "n_args": len(args),
        "signature_text": bsf.to_signature(nhs.node_text(func_node)),
    }


# ============================================================================
# SOURCE RESOLUTION (mirrors build_signature_features.locate_func_src, returns node+ctx)
# ============================================================================

def resolve_context(item):
    """Return (func_node, merged_contracts, contract_name) or None."""
    contract = item["contract"]
    func = item.get("function") or item.get("ast_function")
    fp = item.get("file") or item.get("filePath")
    src = item.get("source")
    if not src:
        low = str(fp).lower()
        if "openzeppelin" in low:
            src = "OpenZeppelin"
        elif "dappscan" in low or "project_root" in item:
            src = "DAppSCAN"
        else:
            src = "FORGE"
    try:
        if src == "OpenZeppelin":
            code = (bsf.PROJECT_ROOT / fp).read_text(encoding="utf-8", errors="ignore")
            merged = dict(ef.oz_contracts); merged.update(nhs.parse_contracts(code))
        elif src == "AaveV3":
            code = (bsf.AAVE_ROOT / fp).read_text(encoding="utf-8", errors="ignore")
            merged = dict(bsf.aave_contracts()); merged.update(nhs.parse_contracts(code))
        elif src == "DAppSCAN":
            code = (ef.DAPPSCAN_ROOT / fp).read_text(encoding="utf-8", errors="ignore")
            merged = dict(ef.get_dappscan_project_contracts(fp)); merged.update(nhs.parse_contracts(code))
        else:  # FORGE
            vid = item.get("vfp_id") or ef.find_forge_vfp_id(item)
            if not vid:
                return None
            merged = {}
            for _fn, fc in ef.vfp_data[vid]["affected_files"].items():
                merged.update(nhs.parse_contracts(fc))
        funcs = nhs.resolve_all_functions(contract, merged)
        if func in funcs:
            return funcs[func], merged, contract
    except Exception:
        return None
    return None


# Provenance keys carried straight through from the input item.
_PROVENANCE_KEYS = ("source", "label", "swc", "normalized_source_hash", "vfp_id",
                    "project_root", "tier", "source_id", "is_variant")


def build_bottleneck_item(item):
    ctx = resolve_context(item)
    if ctx is None:
        return None
    func_node, merged, contract = ctx

    all_state_vars = nhs.resolve_all_state_vars(contract, merged)
    state_var_types = nhs.resolve_all_state_var_types(contract, merged)
    local_vars = nhs.extract_local_vars(func_node)

    hub = build_function_hub(func_node, merged)
    state_nodes = classify_state_accesses(func_node, all_state_vars, local_vars,
                                          state_var_types, merged)
    callee_nodes = build_callee_nodes(func_node, state_var_types, merged, contract,
                                      hub["modifiers"])

    out = {
        "file": item.get("file") or item.get("filePath"),
        "contract": contract,
        "function": item.get("function") or item.get("ast_function"),
        "function_hub": hub,
        "state_nodes": state_nodes,
        "callee_nodes": callee_nodes,
    }
    for k in _PROVENANCE_KEYS:
        if k in item:
            out[k] = item[k]
    return out


# ============================================================================
# DRIVER
# ============================================================================

def process(in_path: Path, out_path: Path):
    data = json.load(open(in_path))
    print(f"\n{in_path.name}: {len(data)} items")
    out, n_state, n_callee, n_rw = [], 0, 0, 0
    for it in data:
        rec = build_bottleneck_item(it)
        if rec is None:
            continue
        out.append(rec)
        n_state += len(rec["state_nodes"])
        n_callee += len(rec["callee_nodes"])
        names = [s["name"] for s in rec["state_nodes"]]
        n_rw += len(names) - len(set(names))          # vars appearing as both read & write
    json.dump(out, open(out_path, "w"), indent=2)
    print(f"  resolved {len(out)}/{len(data)} | state_nodes={n_state} "
          f"(read+write vars={n_rw}) | callee_nodes={n_callee}")
    print(f"  wrote -> {out_path.name}")


if __name__ == "__main__":
    if len(sys.argv) >= 3:                              # CLI: in.json out.json
        process(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        splits = PROJECT_ROOT / "data" / "splits"
        res = PROJECT_ROOT / "experiments" / "results"
        jobs = [
            (splits / "train_augmented.json", splits / "train_augmented_bottleneck.json"),
            (splits / "val_features.json",    splits / "val_bottleneck.json"),
            (splits / "test_features.json",   splits / "test_bottleneck.json"),
            (res / "eval_clean_negatives_oz_features.json", res / "eval_clean_negatives_oz_bottleneck.json"),
            (res / "eval_clean_negatives_aave_split.json",  res / "eval_clean_negatives_aave_bottleneck.json"),
        ]
        for src, dst in jobs:
            if src.exists():
                process(src, dst)
            else:
                print(f"skip (missing): {src}")
        print("\nDone.")
