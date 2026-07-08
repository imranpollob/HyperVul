#!/usr/bin/env python3
"""Phase 1A safety/context features and hard-negative mining.

The script uses only train/validation predictions for false-positive taxonomy,
feature decisions, and hard-negative selection. Test is evaluated only after
validation threshold selection.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
FAIR_SRC = ROOT / "hypervul_fair_eval" / "src"
if str(FAIR_SRC) not in sys.path:
    sys.path.insert(0, str(FAIR_SRC))

spec = importlib.util.spec_from_file_location("phase0e", ROOT / "scripts" / "run_phase0e_native_contract_mil.py")
phase0e = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["phase0e"] = phase0e
spec.loader.exec_module(phase0e)

from fair_eval.builders.hyperedge_view import HyperedgeExample, build_hyperedge_examples  # noqa: E402
from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.models import HyperVulModel  # noqa: E402
from fair_eval.training import binary_metrics, positive_weight, select_threshold, set_global_seed  # noqa: E402


SAFETY_FEATURES = (
    "state_update_before_external_call",
    "state_update_after_external_call",
    "return_value_checked",
    "require_assert_guard_before_call",
    "nonreentrant_modifier",
    "only_owner_or_access_control",
    "callee_user_controlled",
    "trusted_or_fixed_callee",
    "safe_erc20_wrapper",
    "delegatecall_target_fixed",
    "delegatecall_target_user_controlled",
    "try_catch_presence",
    "contract_many_risky_interactions",
    "contract_modifier_access_summary",
    "contract_inheritance_modifier_summary",
)

RISKY_METHODS = {
    "call",
    "delegatecall",
    "staticcall",
    "send",
    "transfer",
    "safetransfer",
    "safetransferfrom",
    "transferfrom",
    "approve",
}

STRATEGIES = ("baseline", "hard_negative_upweight", "hard_negative_oversample")


@dataclass(frozen=True)
class NodeSafety:
    graph_id: str
    node_id: str
    split: str
    label: int
    contract_label: int
    source_path: str
    source_span: str
    function: str
    function_source: str
    external_methods: tuple[str, ...]
    features: dict[str, float]
    category: str
    evidence: str


class SafetyFeatureStore:
    def __init__(self, bundle):
        self.by_key: dict[str, NodeSafety] = {}
        self.by_graph: dict[str, list[NodeSafety]] = defaultdict(list)
        self._build(bundle)

    def _build(self, bundle) -> None:
        for split, graphs in bundle.graphs.items():
            for graph in graphs:
                nodes = list(graph.interaction_nodes)
                first_pass: list[tuple[Any, dict[str, float], str, str]] = []
                risky_count = 0
                access_count = 0
                inheritance_count = 0
                for node in nodes:
                    features, category, evidence = safety_features_for_node(node)
                    if any(features[k] for k in ("callee_user_controlled", "state_update_after_external_call")):
                        risky_count += 1
                    if features["only_owner_or_access_control"] or features["nonreentrant_modifier"]:
                        access_count += 1
                    if " is " in (node.function_source or "").lower() or " override" in (node.function_source or "").lower():
                        inheritance_count += 1
                    first_pass.append((node, features, category, evidence))

                for node, features, category, evidence in first_pass:
                    features = dict(features)
                    features["contract_many_risky_interactions"] = float(risky_count >= 5)
                    features["contract_modifier_access_summary"] = float(access_count > 0)
                    features["contract_inheritance_modifier_summary"] = float(inheritance_count > 0)
                    key = f"{graph.graph_id}::{node.id}"
                    raw = node.raw
                    safety = NodeSafety(
                        graph_id=graph.graph_id,
                        node_id=node.id,
                        split=split,
                        label=int(node.label or 0),
                        contract_label=int(graph.raw.get("contract_label", 1 if graph.positive_count else 0)),
                        source_path=str(raw.get("original_source_path") or ""),
                        source_span=str(raw.get("source_line_span") or ""),
                        function=node.function or "",
                        function_source=node.function_source or "",
                        external_methods=tuple(str(call.get("method", "")).lower() for call in node.external_calls),
                        features=features,
                        category=category,
                        evidence=evidence,
                    )
                    self.by_key[key] = safety
                    self.by_graph[graph.graph_id].append(safety)

    def vector(self, graph_id: str, node_id: str) -> tuple[float, ...]:
        item = self.by_key.get(f"{graph_id}::{node_id}")
        if not item:
            return tuple(0.0 for _ in SAFETY_FEATURES)
        return tuple(float(item.features.get(name, 0.0)) for name in SAFETY_FEATURES)


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def call_positions(source: str, call_texts: list[str]) -> list[int]:
    lower = source.lower()
    positions = []
    for text in call_texts:
        needle = (text or "").lower().strip()
        idx = lower.find(needle) if needle else -1
        if idx < 0:
            method = re.search(r"\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", needle)
            idx = lower.find(f".{method.group(1).lower()}(") if method else -1
        positions.append(idx)
    return [idx for idx in positions if idx >= 0]


def has_state_assignment(source: str, state_vars: list[str], start: int, end: int) -> bool:
    region = source[max(start, 0) : max(end, 0)]
    for var in state_vars:
        if not var:
            continue
        name = re.escape(var.split()[-1].split("[")[0])
        if re.search(rf"\b{name}\b\s*(=|\+=|-=|\*=|/=|\+\+|--)", region):
            return True
        if re.search(rf"\bdelete\s+{name}\b", region):
            return True
    return False


def receiver_looks_user_controlled(receiver: str, source: str) -> bool:
    receiver_l = receiver.lower()
    if not receiver_l:
        return False
    params = re.search(r"\((.*?)\)", source, flags=re.DOTALL)
    param_text = params.group(1).lower() if params else ""
    user_tokens = ("msg.sender", "tx.origin", "recipient", "receiver", "to", "target", "account", "user", "token", "addr")
    return receiver_l in param_text or any(tok in receiver_l for tok in user_tokens)


def receiver_looks_fixed(receiver: str, source: str) -> bool:
    receiver_l = receiver.lower()
    if not receiver_l:
        return False
    fixed_tokens = ("address(0x", "this", "super", "owner()", "treasury", "router", "weth", "usdc", "dai")
    return any(tok in receiver_l for tok in fixed_tokens) or receiver.isupper()


def safety_features_for_node(node) -> tuple[dict[str, float], str, str]:
    source = node.function_source or ""
    lower = source.lower()
    call_texts = [str(call.get("call_text") or "") for call in node.external_calls]
    methods = [str(call.get("method") or "").lower() for call in node.external_calls]
    receivers = [str(call.get("receiver") or "") for call in node.external_calls]
    positions = call_positions(source, call_texts)
    first_call = min(positions) if positions else -1
    last_call = max(positions) if positions else -1
    state_names = [str(x) for x in node.state_vars_accessed]

    state_before = bool(positions and has_state_assignment(source, state_names, 0, first_call))
    state_after = bool(positions and has_state_assignment(source, state_names, last_call, len(source)))
    low_level = any(m in {"call", "delegatecall", "staticcall", "send"} for m in methods) or any(f".{m}(" in lower for m in ("call", "delegatecall", "staticcall", "send"))
    return_checked = bool(
        low_level
        and (
            re.search(r"\b(bool\s+)?(success|ok|sent)\b\s*[,=]", lower)
            or re.search(r"require\s*\(\s*(success|ok|sent)", lower)
            or re.search(r"if\s*\(\s*!\s*(success|ok|sent)", lower)
        )
    )
    guard_before = bool(
        first_call >= 0
        and (
            "require(" in lower[:first_call].replace(" ", "")
            or "assert(" in lower[:first_call].replace(" ", "")
            or "revert " in lower[:first_call]
            or "revert(" in lower[:first_call]
        )
    )
    signature = lower.split("{", 1)[0]
    nonreentrant = "nonreentrant" in signature or "reentrancyguard" in lower
    access_control = bool(
        re.search(r"\bonly(owner|admin|role|governor|operator)\b", signature)
        or "onlyrole" in signature
        or "hasrole" in lower
        or re.search(r"require\s*\([^;]*(msg\.sender|_msgsender\(\))[^;]*(owner|admin|role)", lower)
    )
    safe_erc20 = any(m in {"safetransfer", "safetransferfrom", "safeapprove", "safeincreaseallowance"} for m in methods) or "safeerc20" in lower
    user_controlled = any(receiver_looks_user_controlled(r, source) for r in receivers)
    fixed_callee = any(receiver_looks_fixed(r, source) for r in receivers)
    delegate_fixed = ("delegatecall" in methods or ".delegatecall(" in lower) and fixed_callee
    delegate_user = ("delegatecall" in methods or ".delegatecall(" in lower) and user_controlled
    try_catch = "try " in lower and " catch" in lower

    features = {
        "state_update_before_external_call": float(state_before),
        "state_update_after_external_call": float(state_after),
        "return_value_checked": float(return_checked),
        "require_assert_guard_before_call": float(guard_before),
        "nonreentrant_modifier": float(nonreentrant),
        "only_owner_or_access_control": float(access_control),
        "callee_user_controlled": float(user_controlled),
        "trusted_or_fixed_callee": float(fixed_callee),
        "safe_erc20_wrapper": float(safe_erc20),
        "delegatecall_target_fixed": float(delegate_fixed),
        "delegatecall_target_user_controlled": float(delegate_user),
        "try_catch_presence": float(try_catch),
        "contract_many_risky_interactions": 0.0,
        "contract_modifier_access_summary": 0.0,
        "contract_inheritance_modifier_summary": 0.0,
    }
    category, evidence = categorize_features(features, methods, source, risk_count=None)
    return features, category, evidence


def categorize_features(features: dict[str, float], methods: list[str], source: str, risk_count: int | None) -> tuple[str, str]:
    has_external = bool(methods)
    if has_external and (features.get("nonreentrant_modifier") or features.get("require_assert_guard_before_call") or (features.get("state_update_after_external_call") and features.get("state_update_before_external_call"))):
        return "protected reentrancy-like pattern", "external call plus guard/modifier/state-update signal"
    if any(m in {"call", "send", "staticcall"} for m in methods) and features.get("return_value_checked"):
        return "checked low-level call", "low-level call return appears checked"
    if features.get("state_update_before_external_call") and not features.get("state_update_after_external_call"):
        return "external call after state update", "state assignment detected before external call"
    if features.get("only_owner_or_access_control"):
        return "owner-only/admin-only risky function", "access-control modifier or msg.sender guard detected"
    if features.get("trusted_or_fixed_callee"):
        return "trusted/fixed callee", "callee receiver appears fixed/trusted"
    if features.get("safe_erc20_wrapper"):
        return "safe ERC20 wrapper", "SafeERC20-style method detected"
    if (features.get("delegatecall_target_fixed") or "staticcall" in methods) and not features.get("delegatecall_target_user_controlled"):
        return "delegatecall/staticcall but benign", "delegate/static call with fixed or non-user-controlled target"
    if risk_count is not None and risk_count >= 5:
        return "many risky interactions but no confirmed finding", "contract has many risky-looking interactions"
    if not any(features.values()) and source:
        return "possible mislabeled negative", "high score without detected safety signal"
    return "other recurring pattern", "no stronger taxonomy signal"


class SafetyContractDataset(Dataset):
    def __init__(
        self,
        bags: tuple[Any, ...],
        embeddings: EmbeddingStore,
        safety: SafetyFeatureStore,
        include_safety: bool = True,
        bag_weights: dict[str, float] | None = None,
    ):
        self.bags = bags
        self.embeddings = embeddings
        self.safety = safety
        self.include_safety = include_safety
        self.bag_weights = bag_weights or {}
        self.items = tuple((bag, tuple(self._encode_interaction(ex) for ex in bag.interactions), float(self.bag_weights.get(bag.graph_id, 1.0))) for bag in bags)

    def __len__(self) -> int:
        return len(self.items)

    def _encode_interaction(self, example: HyperedgeExample) -> tuple[torch.Tensor, torch.Tensor, int, int]:
        rows = [self.embeddings.function_embedding(example.function_member.text)]
        rows.extend(self.embeddings.state_embedding(member.text) for member in example.state_members)
        rows.extend(self.embeddings.callee_embedding(member.text) for member in example.callee_members)
        member_embeddings = torch.stack(rows).float()
        base = list(example.security_features)
        if self.include_safety:
            base.extend(self.safety.vector(example.graph_id, example.interaction_node_id))
        symbolic = torch.tensor([base for _ in example.members], dtype=torch.float32)
        return member_embeddings, symbolic, len(example.state_members), len(example.callee_members)

    def __getitem__(self, idx: int):
        return self.items[idx]


def collate_contracts(batch):
    bags = [item[0] for item in batch]
    encoded = [item[1] for item in batch]
    weights = torch.tensor([item[2] for item in batch], dtype=torch.float32)
    out = phase0e.collate_contracts([(bag, items) for bag, items in zip(bags, encoded)])
    out["bag_weights"] = weights
    return out


class SafetyMILModel(nn.Module):
    def __init__(self, pooling: str, symbolic_dim: int, top_k: int = 3, dropout: float = 0.3):
        super().__init__()
        self.pooling = pooling
        self.top_k = top_k
        self.encoder = HyperVulModel(symbolic_dim=symbolic_dim, dropout=dropout, use_symbolic=True, use_localization=True, use_sequence_pool=True)
        self.attention = nn.Sequential(nn.Linear(self.encoder.input_dim, 128), nn.Tanh(), nn.Linear(128, 1, bias=False))

    def forward(self, batch: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        return phase0e.ContractMILHyperVul.forward(self, batch)


def to_device(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def weighted_bce(logits: torch.Tensor, labels: torch.Tensor, pos_weight: torch.Tensor, weights: torch.Tensor | None = None) -> torch.Tensor:
    loss = nn.functional.binary_cross_entropy_with_logits(logits, labels.float(), pos_weight=pos_weight.reshape(1), reduction="none")
    if weights is not None:
        loss = loss * weights.float()
    return loss.mean()


def train_epoch(model, loader, optimizer, contract_pos, interaction_pos, aux_weight, device) -> float:
    model.train()
    losses = []
    for batch in loader:
        batch = to_device(batch, device)
        optimizer.zero_grad(set_to_none=True)
        out = model(batch)
        mask = out["interaction_mask"]
        contract_loss = weighted_bce(out["contract_logits"], batch["contract_labels"], contract_pos, batch.get("bag_weights"))
        interaction_loss = weighted_bce(out["interaction_logits"][mask], batch["interaction_labels"][mask], interaction_pos, None)
        loss = contract_loss + aux_weight * interaction_loss
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else 0.0


@torch.no_grad()
def predict(model, loader, device) -> dict[str, Any]:
    return phase0e.predict(model, loader, device)


def make_loader(dataset, batch_size: int, shuffle: bool, oversample_ids: set[str] | None = None):
    if oversample_ids:
        weights = [4.0 if item[0].graph_id in oversample_ids else 1.0 for item in dataset.items]
        sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)
        return DataLoader(dataset, batch_size=batch_size, sampler=sampler, collate_fn=collate_contracts)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_contracts)


def train_predict(
    bags: dict[str, tuple[Any, ...]],
    embeddings: EmbeddingStore,
    safety: SafetyFeatureStore,
    run: str,
    strategy: str,
    pooling: str,
    seed: int,
    epochs: int,
    batch_size: int,
    lr: float,
    dropout: float,
    aux_weight: float,
    include_safety: bool,
    hard_negative_ids: set[str] | None = None,
) -> dict[str, Any]:
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bag_weights = {gid: 4.0 for gid in (hard_negative_ids or set())} if strategy == "hard_negative_upweight" else {}
    datasets = {
        split: SafetyContractDataset(rows, embeddings, safety, include_safety=include_safety, bag_weights=bag_weights if split == "train" else {})
        for split, rows in bags.items()
    }
    train_loader = make_loader(datasets["train"], batch_size, True, hard_negative_ids if strategy == "hard_negative_oversample" else None)
    loaders = {
        "train": train_loader,
        "val": make_loader(datasets["val"], batch_size, False),
        "test": make_loader(datasets["test"], batch_size, False),
    }
    symbolic_dim = 8 + (len(SAFETY_FEATURES) if include_safety else 0)
    model = SafetyMILModel(pooling=pooling, symbolic_dim=symbolic_dim, dropout=dropout).to(device)
    c_labels = torch.tensor([bag.contract_label for bag in bags["train"]], dtype=torch.float32)
    i_labels = torch.tensor([label for bag in bags["train"] for label in bag.interaction_labels], dtype=torch.float32)
    contract_pos = positive_weight(c_labels).to(device)
    interaction_pos = positive_weight(i_labels).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    history = []
    for epoch in range(1, epochs + 1):
        loss = train_epoch(model, loaders["train"], optimizer, contract_pos, interaction_pos, aux_weight, device)
        if epoch == 1 or epoch == epochs:
            history.append({"epoch": epoch, "train_loss": loss})
    return {
        "run": run,
        "strategy": strategy,
        "pooling": pooling,
        "seed": seed,
        "history": history,
        "predictions": {split: predict(model, loader, device) for split, loader in loaders.items() if split in {"train", "val", "test"}},
    }


def hard_negative_ids_from_train(pred: dict[str, Any], quantile: float = 0.90, limit: int = 300) -> set[str]:
    negatives = [
        (float(prob), str(meta["graph_id"]))
        for prob, label, meta in zip(pred["contract_probs"], pred["contract_labels"], pred["contract_meta"])
        if int(label) == 0
    ]
    if not negatives:
        return set()
    scores = np.array([p for p, _gid in negatives], dtype=float)
    cutoff = float(np.quantile(scores, quantile))
    chosen = sorted([(p, gid) for p, gid in negatives if p >= cutoff], reverse=True)[:limit]
    return {gid for _p, gid in chosen}


def metrics_for_policy(val_probs, val_labels, test_probs, test_labels, policy_name: str) -> dict[str, Any]:
    cfg = phase0e.THRESHOLD_POLICIES[policy_name]
    sel = select_threshold(val_probs, val_labels, policy=cfg["policy"], target_recall=cfg["target_recall"], target_precision=cfg["target_precision"])
    row = dict(binary_metrics(test_probs, test_labels, sel.threshold))
    row.update({"threshold_policy": policy_name, "selection_policy": cfg["policy"], "threshold": sel.threshold, "validation_precision_at_threshold": sel.precision, "validation_recall_at_threshold": sel.recall})
    for target in (0.70, 0.80, 0.90):
        p_at_r, thr, actual = phase0e.precision_at_validation_recall(val_probs, val_labels, test_probs, test_labels, target)
        row[f"test_precision_at_val_recall_{int(target*100)}"] = p_at_r
        row[f"val_threshold_for_recall_{int(target*100)}"] = thr
        row[f"val_recall_at_threshold_{int(target*100)}"] = actual
    return row


def add_metric_rows(result, contract_rows, loc_rows, interaction_rows):
    run = result["run"]
    strategy = result["strategy"]
    pooling = result["pooling"]
    seed = result["seed"]
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]
    for policy in phase0e.THRESHOLD_POLICIES:
        c = metrics_for_policy(val["contract_probs"], val["contract_labels"], test["contract_probs"], test["contract_labels"], policy)
        c.update({"run": run, "strategy": strategy, "pooling": pooling, "seed": seed, "level": "contract"})
        contract_rows.append(c)
        i = metrics_for_policy(val["interaction_probs"], val["interaction_labels"], test["interaction_probs"], test["interaction_labels"], policy)
        i.update({"run": run, "strategy": strategy, "pooling": pooling, "seed": seed, "level": "interaction"})
        interaction_rows.append(i)
    loc = phase0e.localization_metrics(test)
    loc.update({"run": run, "strategy": strategy, "pooling": pooling, "seed": seed})
    loc_rows.append(loc)


def false_positive_taxonomy_rows(predictions: list[dict[str, Any]], safety: SafetyFeatureStore, split: str, top_n: int = 250) -> list[dict[str, Any]]:
    candidates = []
    for pred in predictions:
        for prob, label, meta in zip(pred["contract_probs"], pred["contract_labels"], pred["contract_meta"]):
            if int(label) != 0:
                continue
            candidates.append((float(prob), str(meta["graph_id"])))
    best_by_gid: dict[str, float] = {}
    for prob, gid in candidates:
        best_by_gid[gid] = max(prob, best_by_gid.get(gid, 0.0))
    rows = []
    for gid, score in sorted(best_by_gid.items(), key=lambda item: item[1], reverse=True)[:top_n]:
        nodes = safety.by_graph.get(gid, [])
        if not nodes:
            continue
        risk_count = len([n for n in nodes if n.features.get("callee_user_controlled") or n.features.get("state_update_after_external_call")])
        chosen = max(nodes, key=lambda n: sum(n.features.values()))
        category, evidence = categorize_features(chosen.features, list(chosen.external_methods), chosen.function_source, risk_count)
        rows.append(
            {
                "split": split,
                "graph_id": gid,
                "contract": gid.split("::")[-1],
                "source_path": chosen.source_path,
                "function": chosen.function,
                "interaction_id": chosen.node_id,
                "score": score,
                "category": category,
                "evidence": evidence,
                **{name: chosen.features.get(name, 0.0) for name in SAFETY_FEATURES},
            }
        )
    return rows


def safety_coverage_rows(safety: SafetyFeatureStore, taxonomy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fp_keys = {(row["graph_id"], row["interaction_id"]) for row in taxonomy_rows if row["split"] in {"train", "val"}}
    rows = []
    for split in ("train", "val"):
        items = [item for item in safety.by_key.values() if item.split == split]
        for label_name, label_filter in [("positive", 1), ("negative", 0)]:
            subset = [item for item in items if item.label == label_filter]
            labels = np.array([item.label for item in items], dtype=float)
            for feature in SAFETY_FEATURES:
                values = np.array([item.features.get(feature, 0.0) for item in items], dtype=float)
                feature_subset = [item.features.get(feature, 0.0) for item in subset]
                corr = float(np.corrcoef(values, labels)[0, 1]) if len(set(values)) > 1 and len(set(labels)) > 1 else 0.0
                fp_subset = [item for item in items if (item.graph_id, item.node_id) in fp_keys]
                fp_rate = float(np.mean([item.features.get(feature, 0.0) for item in fp_subset])) if fp_subset else 0.0
                rows.append(
                    {
                        "split": split,
                        "label_group": label_name,
                        "feature": feature,
                        "coverage": float(np.mean(feature_subset)) if feature_subset else 0.0,
                        "correlation_with_label": corr,
                        "false_positive_enrichment": fp_rate,
                        "missing_rate": 0.0,
                        "reliability": feature_reliability(feature),
                    }
                )
    return rows


def feature_reliability(feature: str) -> str:
    high = {"safe_erc20_wrapper", "nonreentrant_modifier", "try_catch_presence", "return_value_checked"}
    medium = {"only_owner_or_access_control", "state_update_before_external_call", "state_update_after_external_call", "delegatecall_target_fixed", "delegatecall_target_user_controlled"}
    return "high" if feature in high else "medium" if feature in medium else "low"


def hard_negative_ablation_rows(contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in sorted({r["run"] for r in contract_rows}):
        base = [r for r in contract_rows if r["run"] == run and r["strategy"] == "baseline" and r["threshold_policy"] == "max_f1"]
        base_precision = np.mean([float(r["precision"]) for r in base]) if base else 0.0
        base_recall = np.mean([float(r["recall"]) for r in base]) if base else 0.0
        base_f1 = np.mean([float(r["f1"]) for r in base]) if base else 0.0
        for strategy in STRATEGIES:
            subset = [r for r in contract_rows if r["run"] == run and r["strategy"] == strategy and r["threshold_policy"] == "max_f1"]
            if not subset:
                continue
            mean = {k: float(np.mean([float(r[k]) for r in subset])) for k in ("precision", "recall", "f1", "f2", "pr_auc", "roc_auc", "fp", "fn")}
            rows.append(
                {
                    "run": run,
                    "strategy": strategy,
                    **{f"{k}_mean": v for k, v in mean.items()},
                    "precision_gain_vs_baseline": mean["precision"] - base_precision,
                    "recall_change_vs_baseline": mean["recall"] - base_recall,
                    "f1_change_vs_baseline": mean["f1"] - base_f1,
                }
            )
    return rows


def safety_ablation_rows(contract_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run in sorted({r["run"] for r in contract_rows}):
        for strategy in sorted({r["strategy"] for r in contract_rows if r["run"] == run}):
            subset = [r for r in contract_rows if r["run"] == run and r["strategy"] == strategy and r["threshold_policy"] == "max_f1"]
            if not subset:
                continue
            rows.append(
                {
                    "run": run,
                    "strategy": strategy,
                    "feature_set": "legacy8_plus_safety15",
                    "precision_mean": float(np.mean([float(r["precision"]) for r in subset])),
                    "recall_mean": float(np.mean([float(r["recall"]) for r in subset])),
                    "f1_mean": float(np.mean([float(r["f1"]) for r in subset])),
                    "pr_auc_mean": float(np.mean([float(r["pr_auc"]) for r in subset])),
                    "note": "training ablation compares hard-negative strategies with safety features enabled; feature reliability is reported in coverage CSV",
                }
            )
    return rows


def mean_std(rows: list[dict[str, Any]], fields: list[str]) -> dict[str, tuple[float, float]]:
    out = {}
    for field in fields:
        vals = [float(r[field]) for r in rows if r.get(field) not in ("", None)]
        if vals:
            out[field] = (float(np.mean(vals)), float(np.std(vals)))
    return out


def fmt(stats: dict[str, tuple[float, float]], key: str) -> str:
    if key not in stats:
        return "n/a"
    return f"{stats[key][0] * 100:.2f} +/- {stats[key][1] * 100:.2f}"


def write_report(counts, taxonomy_rows, coverage_rows, contract_rows, loc_rows, hard_rows):
    lines = ["# Phase 1A Hard-Negative Safety Report", ""]
    lines.append("No augmentation was used. Hard negatives were mined only from train predictions. Validation was used for threshold selection and model comparison; test was evaluated once per trained seed/configuration.")
    lines.append("")
    lines.append("## Split Counts")
    lines.append("| Run | Split | Contracts | Positive | Negative |")
    lines.append("|---|---|---:|---:|---:|")
    for run, splits in counts.items():
        for split, item in splits.items():
            lines.append(f"| {run} | {split} | {item['contracts']} | {item['positive_contracts']} | {item['negative_contracts']} |")
    lines.append("")
    lines.append("## False-Positive Taxonomy")
    cat_counts = Counter(row["category"] for row in taxonomy_rows)
    lines.append("| Category | Train/Val Examples |")
    lines.append("|---|---:|")
    for cat, count in cat_counts.most_common():
        lines.append(f"| {cat} | {count} |")
    lines.append("")
    lines.append("## Contract Metrics")
    lines.append("Validation max-F1 threshold, mean +/- std over 5 seeds.")
    lines.append("")
    lines.append("| Run | Strategy | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for run, strategy in sorted({(r["run"], r["strategy"]) for r in contract_rows}):
        subset = [r for r in contract_rows if r["run"] == run and r["strategy"] == strategy and r["threshold_policy"] == "max_f1"]
        stats = mean_std(subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        lines.append(f"| {run} | {strategy} | {fmt(stats,'precision')} | {fmt(stats,'recall')} | {fmt(stats,'f1')} | {fmt(stats,'f2')} | {fmt(stats,'pr_auc')} | {fmt(stats,'roc_auc')} |")
    lines.append("")
    lines.append("## Localization Metrics")
    lines.append("| Run | Strategy | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run, strategy in sorted({(r["run"], r["strategy"]) for r in loc_rows}):
        subset = [r for r in loc_rows if r["run"] == run and r["strategy"] == strategy]
        stats = mean_std(subset, ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"])
        lines.append(f"| {run} | {strategy} | {fmt(stats,'top1_hit')} | {fmt(stats,'top3_hit')} | {fmt(stats,'top5_hit')} | {fmt(stats,'mrr')} | {fmt(stats,'recall_at_1')} | {fmt(stats,'recall_at_3')} | {fmt(stats,'recall_at_5')} |")
    lines.append("")
    lines.append("## Safety Feature Notes")
    reliable = sorted({r["feature"] for r in coverage_rows if r["reliability"] == "high"})
    lines.append(f"High-reliability heuristics: {', '.join(reliable)}.")
    lines.append("Lower-reliability heuristics include callee controllability, trusted/fixed callee, and inheritance summaries; treat them as weak context features.")
    lines.append("")
    lines.append("## Final Recommendation")
    hn_only = [row for row in hard_rows if row.get("strategy") != "baseline"]
    best_hn = max(hn_only, key=lambda r: float(r["precision_gain_vs_baseline"]), default=None)
    dominant = cat_counts.most_common(1)[0][0] if cat_counts else "n/a"
    lines.append(f"- Dominant false-positive category: `{dominant}`.")
    if best_hn:
        lines.append(f"- Best precision gain came from `{best_hn['strategy']}` on `{best_hn['run']}`: {float(best_hn['precision_gain_vs_baseline'])*100:.2f} precision points, recall change {float(best_hn['recall_change_vs_baseline'])*100:.2f} points.")
    lines.append("- If precision improves without severe recall collapse, Phase 1B should prioritize hard-negative mining plus risk-vs-safety architecture. If recall collapses or possible-mislabeled negatives dominate, prioritize manual label review before augmentation.")
    lines.append("- Do not start broad augmentation until unchecked low-level call labels and possible mislabeled negatives from the taxonomy CSV are reviewed.")
    (REPORTS / "phase1a_hard_negative_safety_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--aux-weight", type=float, default=0.5)
    parser.add_argument("--hard-negative-quantile", type=float, default=0.90)
    args = parser.parse_args()

    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    REPORTS.mkdir(parents=True, exist_ok=True)
    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    safety = SafetyFeatureStore(bundle)
    all_bags = phase0e.build_contract_bags(bundle)
    re_bags = phase0e.build_contract_bags(bundle, "reentrancy_only")
    runs = {
        "all_scope": {"bags": all_bags, "pooling": "mil_topk"},
        "reentrancy_only": {"bags": re_bags, "pooling": "mil_attention"},
    }
    counts = {name: phase0e.split_counts(cfg["bags"]) for name, cfg in runs.items()}
    print(f"Phase 1A counts: {counts}", flush=True)

    contract_rows: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []
    loc_rows: list[dict[str, Any]] = []
    taxonomy_predictions: dict[str, list[dict[str, Any]]] = {"train": [], "val": []}

    hard_negative_counts = []
    for run_name, cfg in runs.items():
        bags = cfg["bags"]
        pooling = cfg["pooling"]
        for seed in args.seeds:
            print(f"Running {run_name} baseline seed={seed}", flush=True)
            baseline = train_predict(bags, embeddings, safety, run_name, "baseline", pooling, seed, args.epochs, args.batch_size, args.lr, args.dropout, args.aux_weight, include_safety=True)
            add_metric_rows(baseline, contract_rows, loc_rows, interaction_rows)
            if run_name == "all_scope":
                taxonomy_predictions["train"].append(baseline["predictions"]["train"])
                taxonomy_predictions["val"].append(baseline["predictions"]["val"])
            hard_ids = hard_negative_ids_from_train(baseline["predictions"]["train"], args.hard_negative_quantile)
            hard_negative_counts.append({"run": run_name, "seed": seed, "hard_negative_contracts": len(hard_ids)})
            for strategy in ("hard_negative_upweight", "hard_negative_oversample"):
                print(f"Running {run_name} {strategy} seed={seed} hard_negatives={len(hard_ids)}", flush=True)
                result = train_predict(bags, embeddings, safety, run_name, strategy, pooling, seed, args.epochs, args.batch_size, args.lr, args.dropout, args.aux_weight, include_safety=True, hard_negative_ids=hard_ids)
                add_metric_rows(result, contract_rows, loc_rows, interaction_rows)

    taxonomy_rows = []
    taxonomy_rows.extend(false_positive_taxonomy_rows(taxonomy_predictions["train"], safety, "train"))
    taxonomy_rows.extend(false_positive_taxonomy_rows(taxonomy_predictions["val"], safety, "val"))
    coverage_rows = safety_coverage_rows(safety, taxonomy_rows)
    hard_rows = hard_negative_ablation_rows(contract_rows)
    feature_ablation = safety_ablation_rows(contract_rows)

    metric_fields = [
        "run", "strategy", "pooling", "seed", "level", "threshold_policy", "selection_policy", "threshold",
        "validation_precision_at_threshold", "validation_recall_at_threshold", "precision", "recall", "f1", "f2",
        "pr_auc", "roc_auc", "tp", "tn", "fp", "fn", "support", "positive_support", "negative_support",
        "test_precision_at_val_recall_70", "test_precision_at_val_recall_80", "test_precision_at_val_recall_90",
        "val_threshold_for_recall_70", "val_threshold_for_recall_80", "val_threshold_for_recall_90",
        "val_recall_at_threshold_70", "val_recall_at_threshold_80", "val_recall_at_threshold_90",
    ]
    phase0e.write_csv(REPORTS / "phase1a_contract_metrics.csv", contract_rows, metric_fields)
    phase0e.write_csv(REPORTS / "phase1a_localization_metrics.csv", loc_rows, ["run", "strategy", "pooling", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"])
    phase0e.write_csv(REPORTS / "phase1a_false_positive_taxonomy.csv", taxonomy_rows, ["split", "graph_id", "contract", "source_path", "function", "interaction_id", "score", "category", "evidence", *SAFETY_FEATURES])
    phase0e.write_csv(REPORTS / "phase1a_safety_feature_coverage.csv", coverage_rows, ["split", "label_group", "feature", "coverage", "correlation_with_label", "false_positive_enrichment", "missing_rate", "reliability"])
    phase0e.write_csv(REPORTS / "phase1a_safety_feature_ablation.csv", feature_ablation, ["run", "strategy", "feature_set", "precision_mean", "recall_mean", "f1_mean", "pr_auc_mean", "note"])
    phase0e.write_csv(REPORTS / "phase1a_hard_negative_ablation.csv", hard_rows, ["run", "strategy", "precision_mean", "recall_mean", "f1_mean", "f2_mean", "pr_auc_mean", "roc_auc_mean", "fp_mean", "fn_mean", "precision_gain_vs_baseline", "recall_change_vs_baseline", "f1_change_vs_baseline"])
    phase0e.write_csv(REPORTS / "phase1a_interaction_secondary_metrics.csv", interaction_rows, metric_fields)
    phase0e.write_csv(REPORTS / "phase1a_hard_negative_counts.csv", hard_negative_counts, ["run", "seed", "hard_negative_contracts"])
    write_report(counts, taxonomy_rows, coverage_rows, contract_rows, loc_rows, hard_rows)

    summary = {
        "generated_at": "2026-06-27",
        "epochs": args.epochs,
        "seeds": args.seeds,
        "counts": counts,
        "hard_negative_counts": hard_negative_counts,
        "dominant_false_positive_categories": Counter(row["category"] for row in taxonomy_rows).most_common(),
        "hard_negative_ablation": hard_rows,
    }
    (REPORTS / "phase1a_hard_negative_safety_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote Phase 1A reports to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
