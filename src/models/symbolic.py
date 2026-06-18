"""Shared symbolic feature schema for the Stage-2 bottleneck nodes (Step 2).

One fixed-width vector layout is used for EVERY node; each node only populates the slots
for its own type (function / state / callee) plus a node-type one-hot. This keeps node
features homogeneous so the existing attention-pool / GNN models consume them unchanged
(a node = [768 SmartBERT embedding] ⊕ [SYM_DIM symbolic block]).

The same layout is imported by:
  - scripts/build_security_features.py  (encodes items -> *_secaug.json)
  - model/train.py                      (masks slot groups per --sym-mode)

Slot groups (so `sym_mode` can zero subsets for the component ablation):
  NODETYPE  : is_function / is_state / is_callee
  FUNC      : visibility, state_mutability, has_nonReentrant      (function hub only)
  STATE     : type_bucket one-hot, access (read/write/read_write) (state nodes)
  CALLEE_SEC: target_kind one-hot, security flags, is_cross       (callee nodes)  [SAFETY]
"""
from __future__ import annotations

# ---- vocabularies (fixed; unknown -> last/"other" bucket) ----
VISIBILITY = ["public", "private", "internal", "external", "default"]
MUTABILITY = ["view", "pure", "payable", "nonpayable"]
TYPE_BUCKETS = ["address", "uint", "int", "bool", "bytes", "string",
                "mapping", "array", "struct", "contract", "enum", "other"]
ACCESS = ["read", "write", "read_write"]
TARGET_KINDS = ["interface", "contract", "library", "erc_like", "address_low_level", "unknown"]
SECURITY_FLAGS = ["nonReentrant", "safe_erc20", "low_level", "return_checked"]


def _onehot(value, vocab):
    v = [0.0] * len(vocab)
    if value in vocab:
        v[vocab.index(value)] = 1.0
    else:
        v[-1] = 1.0  # fall into the trailing "default"/"other"/"unknown" bucket
    return v


# ---- ordered slot groups: (name, width) ----
SLOT_GROUPS = [
    ("nodetype", 3),
    ("func_visibility", len(VISIBILITY)),
    ("func_mutability", len(MUTABILITY)),
    ("func_nonreentrant", 1),
    ("state_typebucket", len(TYPE_BUCKETS)),
    ("state_access", len(ACCESS)),
    ("callee_targetkind", len(TARGET_KINDS)),
    ("callee_security", len(SECURITY_FLAGS)),
    ("callee_cross", 1),
]
# group -> (start, end) offsets in the flat vector
_OFF = {}
_c = 0
for _name, _w in SLOT_GROUPS:
    _OFF[_name] = (_c, _c + _w)
    _c += _w
SYM_DIM = _c

# Which slot groups belong to each ablation mode.
_SECURITY_GROUPS = {"nodetype", "func_nonreentrant",
                    "callee_targetkind", "callee_security", "callee_cross"}
_ALL_GROUPS = {g for g, _ in SLOT_GROUPS}


def _zeros():
    return [0.0] * SYM_DIM


def _put(vec, group, values):
    s, e = _OFF[group]
    assert len(values) == e - s, f"{group}: {len(values)} != {e - s}"
    vec[s:e] = list(values)


def encode_function(hub: dict) -> list:
    vec = _zeros()
    _put(vec, "nodetype", [1.0, 0.0, 0.0])
    _put(vec, "func_visibility", _onehot(hub.get("visibility", "default"), VISIBILITY))
    _put(vec, "func_mutability", _onehot(hub.get("state_mutability", "nonpayable"), MUTABILITY))
    mods = [m.lower() for m in hub.get("modifiers", [])]
    nonre = any("reentr" in m or m in ("lock", "locked") for m in mods)
    _put(vec, "func_nonreentrant", [1.0 if nonre else 0.0])
    return vec


def encode_state(node: dict) -> list:
    vec = _zeros()
    _put(vec, "nodetype", [0.0, 1.0, 0.0])
    _put(vec, "state_typebucket", _onehot(node.get("type_bucket", "other"), TYPE_BUCKETS))
    _put(vec, "state_access", _onehot(node.get("access", "read"), ACCESS))
    return vec


def encode_callee(node: dict) -> list:
    vec = _zeros()
    _put(vec, "nodetype", [0.0, 0.0, 1.0])
    _put(vec, "callee_targetkind", _onehot(node.get("target_kind", "unknown"), TARGET_KINDS))
    sec = node.get("security_context", {}) or {}
    _put(vec, "callee_security", [1.0 if sec.get(f) else 0.0 for f in SECURITY_FLAGS])
    _put(vec, "callee_cross", [1.0 if node.get("is_cross_contract") else 0.0])
    return vec


def merge_state_access(accesses) -> str:
    """A state var split into read/write nodes -> a single access label for its (named) node."""
    s = set(accesses)
    if "read" in s and "write" in s:
        return "read_write"
    return "write" if "write" in s else "read"


def sym_mask(mode: str):
    """Return a 0/1 list of length SYM_DIM zeroing slot groups not in `mode`.
    mode: 'none' (all zero -> baseline), 'security' (safety groups), 'full' (all)."""
    if mode == "full":
        keep = _ALL_GROUPS
    elif mode == "security":
        keep = _SECURITY_GROUPS
    elif mode == "none":
        keep = set()
    else:
        raise ValueError(f"unknown sym_mode: {mode}")
    mask = _zeros()
    for g in keep:
        s, e = _OFF[g]
        for i in range(s, e):
            mask[i] = 1.0
    return mask
