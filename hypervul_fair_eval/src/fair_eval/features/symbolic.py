"""Per-member symbolic features for HyperVul-only experiments."""

from __future__ import annotations

import re
from collections.abc import Iterable

from fair_eval.builders.hyperedge_view import HyperedgeExample, HyperedgeMember


VISIBILITY = ("public", "private", "internal", "external", "default")
MUTABILITY = ("view", "pure", "payable", "nonpayable")
TYPE_BUCKETS = ("address", "uint", "int", "bool", "bytes", "string", "mapping", "array", "struct", "contract", "enum", "other")
ACCESS = ("read", "write", "read_write")
TARGET_KINDS = ("interface", "contract", "library", "erc_like", "address_low_level", "unknown")
SECURITY_FLAGS = ("nonReentrant", "safe_erc20", "low_level", "return_checked")

SLOT_GROUPS = (
    ("nodetype", 3),
    ("func_visibility", len(VISIBILITY)),
    ("func_mutability", len(MUTABILITY)),
    ("func_nonreentrant", 1),
    ("state_typebucket", len(TYPE_BUCKETS)),
    ("state_access", len(ACCESS)),
    ("callee_targetkind", len(TARGET_KINDS)),
    ("callee_security", len(SECURITY_FLAGS)),
    ("callee_cross", 1),
)

OFFSETS: dict[str, tuple[int, int]] = {}
_cursor = 0
for _name, _width in SLOT_GROUPS:
    OFFSETS[_name] = (_cursor, _cursor + _width)
    _cursor += _width

SYMBOLIC_DIM = _cursor
SECURITY_GROUPS = {"nodetype", "func_nonreentrant", "callee_targetkind", "callee_security", "callee_cross"}
FULL_GROUPS = set(OFFSETS)


def symbolic_mask(mode: str) -> tuple[float, ...]:
    if mode == "none":
        keep: set[str] = set()
    elif mode == "security":
        keep = SECURITY_GROUPS
    elif mode == "full":
        keep = FULL_GROUPS
    else:
        raise ValueError(f"Unknown symbolic mode: {mode}")
    out = [0.0] * SYMBOLIC_DIM
    for group in keep:
        start, end = OFFSETS[group]
        for idx in range(start, end):
            out[idx] = 1.0
    return tuple(out)


def _zeros() -> list[float]:
    return [0.0] * SYMBOLIC_DIM


def _put(vec: list[float], group: str, values: Iterable[float]) -> None:
    start, end = OFFSETS[group]
    values = list(values)
    if len(values) != end - start:
        raise ValueError(f"{group}: expected {end - start}, got {len(values)}")
    vec[start:end] = values


def _onehot(value: str | None, vocab: tuple[str, ...]) -> list[float]:
    out = [0.0] * len(vocab)
    normalized = (value or vocab[-1]).strip()
    out[vocab.index(normalized) if normalized in vocab else len(vocab) - 1] = 1.0
    return out


def _function_signature(source: str) -> str:
    return source.split("{", 1)[0] if "{" in source else source[:300]


def _function_visibility(source: str) -> str:
    signature = _function_signature(source)
    for visibility in VISIBILITY[:-1]:
        if re.search(rf"\b{visibility}\b", signature):
            return visibility
    return "default"


def _function_mutability(source: str) -> str:
    signature = _function_signature(source)
    for mutability in MUTABILITY[:-1]:
        if re.search(rf"\b{mutability}\b", signature):
            return mutability
    return "nonpayable"


def _has_nonreentrant(source: str) -> bool:
    signature = _function_signature(source).lower()
    return any(token in signature for token in ("nonreentrant", "non_reentrant", "lock", "locked"))


def _type_bucket(text: str) -> str:
    lowered = text.lower()
    for bucket in TYPE_BUCKETS[:-1]:
        if bucket in lowered:
            return bucket
    return "other"


def _state_access(text: str, function_source: str) -> str:
    name = text.split()[0] if text.split() else text
    if not name:
        return "read"
    writes = bool(re.search(rf"\b{name}\b\s*(=|\+=|-=|\*=|/=|\+\+|--)", function_source))
    reads = bool(re.search(rf"\b{name}\b", function_source))
    if writes and reads:
        return "read_write"
    return "write" if writes else "read"


def _target_kind(member: HyperedgeMember) -> str:
    receiver = member.metadata.get("receiver", "")
    method = member.metadata.get("method", "")
    text = member.text
    combined = f"{receiver} {method} {text}".lower()
    if any(x in combined for x in (".call", ".delegatecall", ".staticcall", ".send", ".transfer(")):
        return "address_low_level"
    if "safe" in method.lower() or "erc20" in combined or "ierc" in combined:
        return "erc_like"
    if receiver.startswith("I") or "interface" in combined:
        return "interface"
    if "library" in combined:
        return "library"
    if receiver:
        return "contract"
    return "unknown"


def _callee_security(member: HyperedgeMember, function_source: str) -> list[float]:
    text = f"{member.text} {member.metadata.get('method', '')} {member.metadata.get('receiver', '')}".lower()
    source = function_source.lower()
    low_level = any(token in text for token in (".call", ".delegatecall", ".staticcall", ".send", ".transfer("))
    return [
        1.0 if _has_nonreentrant(function_source) else 0.0,
        1.0 if "safe" in text or "safeerc20" in source else 0.0,
        1.0 if low_level else 0.0,
        1.0 if low_level and ("require(" in source or "success" in source or "return" in source) else 0.0,
    ]


def member_symbolic_vector(example: HyperedgeExample, member: HyperedgeMember, mode: str) -> tuple[float, ...]:
    mask = symbolic_mask(mode)
    function_source = example.function_member.text
    vec = _zeros()
    if member.member_type == "function":
        _put(vec, "nodetype", [1.0, 0.0, 0.0])
        _put(vec, "func_visibility", _onehot(_function_visibility(function_source), VISIBILITY))
        _put(vec, "func_mutability", _onehot(_function_mutability(function_source), MUTABILITY))
        _put(vec, "func_nonreentrant", [1.0 if _has_nonreentrant(function_source) else 0.0])
    elif member.member_type == "state":
        _put(vec, "nodetype", [0.0, 1.0, 0.0])
        _put(vec, "state_typebucket", _onehot(_type_bucket(member.text), TYPE_BUCKETS))
        _put(vec, "state_access", _onehot(_state_access(member.metadata.get("name", member.text), function_source), ACCESS))
    elif member.member_type == "callee":
        _put(vec, "nodetype", [0.0, 0.0, 1.0])
        _put(vec, "callee_targetkind", _onehot(_target_kind(member), TARGET_KINDS))
        _put(vec, "callee_security", _callee_security(member, function_source))
        _put(vec, "callee_cross", [1.0 if example.is_cross_contract else 0.0])
    return tuple(value * mask[idx] for idx, value in enumerate(vec))


def example_symbolic_matrix(example: HyperedgeExample, mode: str) -> tuple[tuple[float, ...], ...]:
    return tuple(member_symbolic_vector(example, member, mode) for member in example.members)
