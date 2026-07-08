#!/usr/bin/env python3
"""Phase 0E native contract-level MIL training for HyperVul.

This runner keeps the existing HyperVul interaction encoder and changes the
training objective/evaluation unit to contracts. It does not augment data or
add new graph features.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
SCOPE_DIR = GRAPH_DIR / "scope_views"
OUTDIR = ROOT / "experiments" / "phase0e_native_mil"

FAIR_SRC = ROOT / "hypervul_fair_eval" / "src"
if str(FAIR_SRC) not in sys.path:
    sys.path.insert(0, str(FAIR_SRC))

from fair_eval.builders.hyperedge_view import HyperedgeExample, build_hyperedge_examples  # noqa: E402
from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore, example_symbolic_matrix  # noqa: E402
from fair_eval.models import HyperVulModel  # noqa: E402
from fair_eval.training import binary_metrics, positive_weight, select_threshold, set_global_seed  # noqa: E402


POOLING_VARIANTS = ("mil_max", "mil_topk", "mil_attention")
THRESHOLD_POLICIES = {
    "max_f1": {"policy": "max_f1", "target_recall": 0.90, "target_precision": 0.70},
    "high_recall": {"policy": "target_recall", "target_recall": 0.90, "target_precision": 0.70},
    "precision_focused": {"policy": "target_precision", "target_recall": 0.90, "target_precision": 0.70},
}


@dataclass(frozen=True)
class ContractBag:
    split: str
    graph_id: str
    contract: str
    project: str
    source: str
    contract_label: int
    interactions: tuple[HyperedgeExample, ...]
    interaction_labels: tuple[int, ...]
    positive_interaction_ids: tuple[str, ...]
    vulnerability_types: tuple[str, ...]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sigmoid_np(logits: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.asarray(logits, dtype=float)))


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}"


def mean_std(rows: list[dict[str, Any]], fields: list[str]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for field in fields:
        vals = [float(row[field]) for row in rows if row.get(field) not in ("", None)]
        if vals:
            out[field] = {"mean": float(np.mean(vals)), "std": float(np.std(vals))}
    return out


def format_mean_std(stats: dict[str, dict[str, float]], metric: str) -> str:
    item = stats.get(metric)
    if not item:
        return "n/a"
    return f"{item['mean'] * 100:.2f} +/- {item['std'] * 100:.2f}"


def precision_at_validation_recall(
    val_probs: np.ndarray,
    val_labels: np.ndarray,
    test_probs: np.ndarray,
    test_labels: np.ndarray,
    target_recall: float,
) -> tuple[float, float, float]:
    best: tuple[float, float, float] | None = None
    for threshold in np.linspace(0.0, 1.0, 1001):
        metrics = binary_metrics(val_probs, val_labels, float(threshold))
        if metrics["recall"] >= target_recall:
            cand = (float(metrics["precision"]), float(threshold), float(metrics["recall"]))
            if best is None or cand > best:
                best = cand
    if best is None:
        return 0.0, 1.0, 0.0
    val_precision, threshold, val_recall = best
    test_metrics = binary_metrics(test_probs, test_labels, threshold)
    return float(test_metrics["precision"]), threshold, val_recall


def scope_map(scope_name: str | None) -> dict[str, dict[str, dict[str, Any]]]:
    if not scope_name:
        return {}
    path = SCOPE_DIR / f"{scope_name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        split: {str(row["graph_id"]): row for row in rows}
        for split, rows in data.items()
    }


def build_contract_bags(bundle, scope_name: str | None = None) -> dict[str, tuple[ContractBag, ...]]:
    scope = scope_map(scope_name)
    out: dict[str, list[ContractBag]] = {"train": [], "val": [], "test": []}
    for split, graphs in bundle.graphs.items():
        by_graph: dict[str, list[HyperedgeExample]] = defaultdict(list)
        for example in build_hyperedge_examples(graphs):
            by_graph[example.graph_id].append(example)

        for graph in graphs:
            if scope_name and graph.graph_id not in scope.get(split, {}):
                continue
            examples = tuple(by_graph.get(graph.graph_id, []))
            if not examples:
                continue

            raw = graph.raw
            if scope_name:
                scope_row = scope[split][graph.graph_id]
                contract_label = int(scope_row.get("scope_label", 0))
                positive_ids = tuple(str(x) for x in scope_row.get("positive_interaction_ids", []))
                vulnerability_types = tuple(str(x) for x in scope_row.get("vulnerability_types", []))
                pos_set = set(positive_ids)
                interaction_labels = tuple(1 if ex.interaction_node_id in pos_set else 0 for ex in examples)
            else:
                contract_label = int(raw.get("contract_label", 1 if graph.positive_count else 0))
                positive_ids = tuple(str(x) for x in raw.get("positive_interaction_ids", []))
                vulnerability_types = tuple(str(x) for x in raw.get("vulnerability_types", []))
                interaction_labels = tuple(int(ex.label) for ex in examples)

            out[split].append(
                ContractBag(
                    split=split,
                    graph_id=graph.graph_id,
                    contract=graph.contract,
                    project=graph.project,
                    source=graph.source,
                    contract_label=contract_label,
                    interactions=examples,
                    interaction_labels=interaction_labels,
                    positive_interaction_ids=positive_ids,
                    vulnerability_types=vulnerability_types,
                )
            )
    return {split: tuple(rows) for split, rows in out.items()}


class ContractMILDataset(Dataset):
    def __init__(self, bags: tuple[ContractBag, ...], embeddings: EmbeddingStore, symbolic_mode: str = "legacy8"):
        self.bags = bags
        self.embeddings = embeddings
        self.symbolic_mode = symbolic_mode
        self.items = tuple((bag, tuple(self._encode_interaction(example) for example in bag.interactions)) for bag in bags)

    def __len__(self) -> int:
        return len(self.bags)

    def _encode_interaction(self, example: HyperedgeExample) -> tuple[torch.Tensor, torch.Tensor, int, int]:
        rows = [self.embeddings.function_embedding(example.function_member.text)]
        rows.extend(self.embeddings.state_embedding(member.text) for member in example.state_members)
        rows.extend(self.embeddings.callee_embedding(member.text) for member in example.callee_members)
        member_embeddings = torch.stack(rows).float()
        if self.symbolic_mode == "legacy8":
            symbolic = torch.tensor([example.security_features for _ in example.members], dtype=torch.float32)
        else:
            symbolic = torch.tensor(example_symbolic_matrix(example, self.symbolic_mode), dtype=torch.float32)
        return member_embeddings, symbolic, len(example.state_members), len(example.callee_members)

    def __getitem__(self, idx: int):
        return self.items[idx]


def collate_contracts(batch):
    bags = [item[0] for item in batch]
    encoded = [item[1] for item in batch]
    batch_size = len(batch)
    max_interactions = max(len(items) for items in encoded)
    max_members = max(member.shape[0] for items in encoded for member, _sym, _sc, _cc in items)
    max_states = max(1, max(int(state_count) for items in encoded for _m, _s, state_count, _cc in items))
    max_callees = max(1, max(int(callee_count) for items in encoded for _m, _s, _sc, callee_count in items))
    emb_dim = encoded[0][0][0].shape[1]
    symbolic_dim = encoded[0][0][1].shape[1]

    members = torch.zeros(batch_size, max_interactions, max_members, emb_dim)
    symbolic = torch.zeros(batch_size, max_interactions, max_members, symbolic_dim)
    member_mask = torch.zeros(batch_size, max_interactions, max_members, dtype=torch.bool)
    interaction_mask = torch.zeros(batch_size, max_interactions, dtype=torch.bool)
    state_embeddings = torch.zeros(batch_size, max_interactions, max_states, emb_dim)
    callee_embeddings = torch.zeros(batch_size, max_interactions, max_callees, emb_dim)
    state_symbolic = torch.zeros(batch_size, max_interactions, max_states, symbolic_dim)
    callee_symbolic = torch.zeros(batch_size, max_interactions, max_callees, symbolic_dim)
    state_mask = torch.zeros(batch_size, max_interactions, max_states, dtype=torch.bool)
    callee_mask = torch.zeros(batch_size, max_interactions, max_callees, dtype=torch.bool)
    contract_labels = torch.zeros(batch_size, dtype=torch.float32)
    interaction_labels = torch.zeros(batch_size, max_interactions, dtype=torch.float32)

    for bag_idx, (bag, items) in enumerate(zip(bags, encoded)):
        contract_labels[bag_idx] = float(bag.contract_label)
        for int_idx, (member_emb, sym, state_count, callee_count) in enumerate(items):
            n_members = member_emb.shape[0]
            interaction_mask[bag_idx, int_idx] = True
            interaction_labels[bag_idx, int_idx] = float(bag.interaction_labels[int_idx])
            members[bag_idx, int_idx, :n_members] = member_emb
            symbolic[bag_idx, int_idx, :n_members] = sym
            member_mask[bag_idx, int_idx, :n_members] = True
            if state_count:
                state_mask[bag_idx, int_idx, :state_count] = True
                state_embeddings[bag_idx, int_idx, :state_count] = member_emb[1 : 1 + state_count]
                state_symbolic[bag_idx, int_idx, :state_count] = sym[1 : 1 + state_count]
            if callee_count:
                start = 1 + state_count
                callee_mask[bag_idx, int_idx, :callee_count] = True
                callee_embeddings[bag_idx, int_idx, :callee_count] = member_emb[start : start + callee_count]
                callee_symbolic[bag_idx, int_idx, :callee_count] = sym[start : start + callee_count]

    return {
        "bags": bags,
        "members": members,
        "symbolic": symbolic,
        "member_mask": member_mask,
        "interaction_mask": interaction_mask,
        "state_embeddings": state_embeddings,
        "callee_embeddings": callee_embeddings,
        "state_symbolic": state_symbolic,
        "callee_symbolic": callee_symbolic,
        "state_mask": state_mask,
        "callee_mask": callee_mask,
        "contract_labels": contract_labels,
        "interaction_labels": interaction_labels,
    }


class ContractMILHyperVul(nn.Module):
    def __init__(self, pooling: str, top_k: int = 3, dropout: float = 0.3):
        super().__init__()
        if pooling not in POOLING_VARIANTS:
            raise ValueError(pooling)
        self.pooling = pooling
        self.top_k = top_k
        self.encoder = HyperVulModel(
            symbolic_dim=8,
            dropout=dropout,
            use_symbolic=True,
            use_localization=True,
            use_sequence_pool=True,
        )
        rep_dim = self.encoder.input_dim
        self.attention = nn.Sequential(nn.Linear(rep_dim, 128), nn.Tanh(), nn.Linear(128, 1, bias=False))

    def forward(self, batch: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        members = batch["members"]
        batch_size, max_interactions, max_members, emb_dim = members.shape
        flat_valid = batch["interaction_mask"].reshape(-1)
        flat_members = members.reshape(batch_size * max_interactions, max_members, emb_dim)[flat_valid]
        flat_member_mask = batch["member_mask"].reshape(batch_size * max_interactions, max_members)[flat_valid]
        flat_symbolic = batch["symbolic"].reshape(batch_size * max_interactions, max_members, -1)[flat_valid]
        flat_state_embeddings = batch["state_embeddings"].reshape(batch_size * max_interactions, batch["state_embeddings"].shape[2], emb_dim)[flat_valid]
        flat_callee_embeddings = batch["callee_embeddings"].reshape(batch_size * max_interactions, batch["callee_embeddings"].shape[2], emb_dim)[flat_valid]
        flat_state_symbolic = batch["state_symbolic"].reshape(batch_size * max_interactions, batch["state_symbolic"].shape[2], -1)[flat_valid]
        flat_callee_symbolic = batch["callee_symbolic"].reshape(batch_size * max_interactions, batch["callee_symbolic"].shape[2], -1)[flat_valid]
        flat_state_mask = batch["state_mask"].reshape(batch_size * max_interactions, batch["state_mask"].shape[2])[flat_valid]
        flat_callee_mask = batch["callee_mask"].reshape(batch_size * max_interactions, batch["callee_mask"].shape[2])[flat_valid]

        flat_logits, flat_reps = self.encoder(
            flat_members,
            flat_member_mask,
            symbolic_features=flat_symbolic,
            state_embeddings=flat_state_embeddings,
            callee_embeddings=flat_callee_embeddings,
            state_symbolic=flat_state_symbolic,
            callee_symbolic=flat_callee_symbolic,
            state_mask=flat_state_mask,
            callee_mask=flat_callee_mask,
            return_representation=True,
        )

        logits = members.new_full((batch_size, max_interactions), -1e9)
        reps = members.new_zeros((batch_size, max_interactions, flat_reps.shape[-1]))
        logits.reshape(-1)[flat_valid] = flat_logits
        reps.reshape(batch_size * max_interactions, -1)[flat_valid] = flat_reps
        mask = batch["interaction_mask"]

        if self.pooling == "mil_max":
            contract_logits = logits.masked_fill(~mask, -1e9).max(dim=1).values
        elif self.pooling == "mil_topk":
            masked = logits.masked_fill(~mask, -1e9)
            k = min(self.top_k, masked.shape[1])
            values = torch.topk(masked, k=k, dim=1).values
            valid_counts = mask.sum(dim=1).clamp_min(1).clamp_max(k).float()
            contract_logits = values.masked_fill(values < -1e8, 0.0).sum(dim=1) / valid_counts
        else:
            attn_scores = self.attention(reps).squeeze(-1).masked_fill(~mask, -1e9)
            weights = torch.softmax(attn_scores, dim=1).masked_fill(~mask, 0.0)
            contract_logits = (weights * logits.masked_fill(~mask, 0.0)).sum(dim=1)

        return {
            "contract_logits": contract_logits,
            "interaction_logits": logits,
            "interaction_mask": mask,
        }


def to_device(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    out = {}
    for key, value in batch.items():
        out[key] = value.to(device) if torch.is_tensor(value) else value
    return out


def contract_pos_weight(bags: tuple[ContractBag, ...], device: torch.device) -> torch.Tensor:
    labels = torch.tensor([bag.contract_label for bag in bags], dtype=torch.float32)
    return positive_weight(labels).to(device)


def interaction_pos_weight(bags: tuple[ContractBag, ...], device: torch.device) -> torch.Tensor:
    labels = torch.tensor([label for bag in bags for label in bag.interaction_labels], dtype=torch.float32)
    return positive_weight(labels).to(device)


def mil_loss(
    outputs: dict[str, torch.Tensor],
    batch: dict[str, torch.Tensor],
    contract_loss_fn: nn.Module,
    interaction_loss_fn: nn.Module,
    aux_weight: float,
) -> torch.Tensor:
    contract_loss = contract_loss_fn(outputs["contract_logits"], batch["contract_labels"])
    mask = outputs["interaction_mask"]
    interaction_loss = interaction_loss_fn(outputs["interaction_logits"][mask], batch["interaction_labels"][mask])
    return contract_loss + aux_weight * interaction_loss


def train_one_epoch(
    model: ContractMILHyperVul,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    contract_loss_fn: nn.Module,
    interaction_loss_fn: nn.Module,
    aux_weight: float,
    device: torch.device,
) -> float:
    model.train()
    losses = []
    for batch in loader:
        batch = to_device(batch, device)
        optimizer.zero_grad(set_to_none=True)
        outputs = model(batch)
        loss = mil_loss(outputs, batch, contract_loss_fn, interaction_loss_fn, aux_weight)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else 0.0


@torch.no_grad()
def predict(model: ContractMILHyperVul, loader: DataLoader, device: torch.device) -> dict[str, Any]:
    model.eval()
    contract_logits: list[float] = []
    contract_labels: list[int] = []
    interaction_logits: list[float] = []
    interaction_labels: list[int] = []
    interaction_meta: list[dict[str, Any]] = []
    contract_meta: list[dict[str, Any]] = []

    for batch in loader:
        batch = to_device(batch, device)
        outputs = model(batch)
        c_logits = outputs["contract_logits"].detach().cpu().numpy()
        c_labels = batch["contract_labels"].detach().cpu().numpy().astype(int)
        i_logits = outputs["interaction_logits"].detach().cpu()
        i_labels = batch["interaction_labels"].detach().cpu()
        i_mask = outputs["interaction_mask"].detach().cpu()

        for row_idx, bag in enumerate(batch["bags"]):
            contract_logits.append(float(c_logits[row_idx]))
            contract_labels.append(int(c_labels[row_idx]))
            contract_meta.append(
                {
                    "graph_id": bag.graph_id,
                    "contract": bag.contract,
                    "project": bag.project,
                    "source": bag.source,
                    "positive_interaction_ids": "|".join(bag.positive_interaction_ids),
                    "vulnerability_types": "|".join(bag.vulnerability_types),
                    "candidate_interactions": len(bag.interactions),
                }
            )
            for int_idx, example in enumerate(bag.interactions):
                if not bool(i_mask[row_idx, int_idx]):
                    continue
                interaction_logits.append(float(i_logits[row_idx, int_idx]))
                interaction_labels.append(int(i_labels[row_idx, int_idx]))
                interaction_meta.append(
                    {
                        "graph_id": bag.graph_id,
                        "contract": bag.contract,
                        "project": bag.project,
                        "source": bag.source,
                        "node_id": example.interaction_node_id,
                        "function": example.function,
                        "vulnerability_type": example.vulnerability_type or "",
                    }
                )

    return {
        "contract_logits": np.asarray(contract_logits, dtype=float),
        "contract_probs": sigmoid_np(np.asarray(contract_logits, dtype=float)),
        "contract_labels": np.asarray(contract_labels, dtype=int),
        "contract_meta": contract_meta,
        "interaction_logits": np.asarray(interaction_logits, dtype=float),
        "interaction_probs": sigmoid_np(np.asarray(interaction_logits, dtype=float)),
        "interaction_labels": np.asarray(interaction_labels, dtype=int),
        "interaction_meta": interaction_meta,
    }


def metrics_for_policy(
    val_probs: np.ndarray,
    val_labels: np.ndarray,
    test_probs: np.ndarray,
    test_labels: np.ndarray,
    policy_name: str,
) -> dict[str, Any]:
    cfg = THRESHOLD_POLICIES[policy_name]
    selection = select_threshold(
        val_probs,
        val_labels,
        policy=cfg["policy"],
        target_recall=cfg["target_recall"],
        target_precision=cfg["target_precision"],
    )
    metrics = dict(binary_metrics(test_probs, test_labels, selection.threshold))
    metrics.update(
        {
            "threshold_policy": policy_name,
            "selection_policy": cfg["policy"],
            "threshold": selection.threshold,
            "validation_precision_at_threshold": selection.precision,
            "validation_recall_at_threshold": selection.recall,
        }
    )
    return metrics


def localization_metrics(pred: dict[str, Any], ks=(1, 3, 5)) -> dict[str, Any]:
    by_graph: dict[str, list[tuple[float, int, str]]] = defaultdict(list)
    for prob, label, meta in zip(pred["interaction_probs"], pred["interaction_labels"], pred["interaction_meta"]):
        by_graph[str(meta["graph_id"])].append((float(prob), int(label), str(meta["node_id"])))

    positive_graphs = [gid for gid, rows in by_graph.items() if any(label == 1 for _p, label, _nid in rows)]
    out = {f"top{k}_hit": 0.0 for k in ks}
    out.update({f"recall_at_{k}": 0.0 for k in ks})
    reciprocal_ranks: list[float] = []
    for gid in positive_graphs:
        ranked = sorted(by_graph[gid], key=lambda row: row[0], reverse=True)
        pos_ids = {node_id for _prob, label, node_id in ranked if label == 1}
        ranks = [idx + 1 for idx, (_prob, label, _node_id) in enumerate(ranked) if label == 1]
        reciprocal_ranks.append(1.0 / min(ranks) if ranks else 0.0)
        for k in ks:
            top_ids = {node_id for _prob, _label, node_id in ranked[:k]}
            hits = len(pos_ids & top_ids)
            out[f"top{k}_hit"] += 1.0 if hits else 0.0
            out[f"recall_at_{k}"] += hits / max(len(pos_ids), 1)

    denom = max(len(positive_graphs), 1)
    for k in ks:
        out[f"top{k}_hit"] /= denom
        out[f"recall_at_{k}"] /= denom
    out["mrr"] = float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0
    out["positive_contracts"] = len(positive_graphs)
    return out


def error_analysis_rows(
    run_name: str,
    pooling: str,
    seed: int,
    pred: dict[str, Any],
    threshold: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contract_pred = pred["contract_probs"] >= threshold
    by_graph: dict[str, list[tuple[float, int, dict[str, Any]]]] = defaultdict(list)
    for prob, label, meta in zip(pred["interaction_probs"], pred["interaction_labels"], pred["interaction_meta"]):
        by_graph[str(meta["graph_id"])].append((float(prob), int(label), meta))

    for prob, label, pred_label, meta in zip(pred["contract_probs"], pred["contract_labels"], contract_pred, pred["contract_meta"]):
        if int(pred_label) == int(label):
            continue
        rows.append(
            {
                "run": run_name,
                "pooling": pooling,
                "seed": seed,
                "error_type": "false_positive_contract" if pred_label else "false_negative_contract",
                "graph_id": meta["graph_id"],
                "contract": meta["contract"],
                "contract_probability": float(prob),
                "threshold": threshold,
                "contract_label": int(label),
                "predicted_label": int(pred_label),
                "candidate_interactions": meta["candidate_interactions"],
                "top_wrong_node_id": "",
                "top_wrong_function": "",
                "top_wrong_probability": "",
                "true_positive_rank": "",
                "failure_category": "label_ambiguity_or_missing_context" if pred_label else "missing_safety_features_or_global_context",
                "vulnerability_types": meta["vulnerability_types"],
            }
        )

    for graph_id, rows_for_graph in by_graph.items():
        if not any(label == 1 for _prob, label, _meta in rows_for_graph):
            continue
        ranked = sorted(rows_for_graph, key=lambda row: row[0], reverse=True)
        positive_ranks = [idx + 1 for idx, (_prob, label, _meta) in enumerate(ranked) if label == 1]
        best_rank = min(positive_ranks) if positive_ranks else None
        if best_rank is not None and best_rank <= 3:
            continue
        top_prob, top_label, top_meta = ranked[0]
        cmeta = next((m for m in pred["contract_meta"] if m["graph_id"] == graph_id), {})
        rows.append(
            {
                "run": run_name,
                "pooling": pooling,
                "seed": seed,
                "error_type": "true_interaction_not_top3",
                "graph_id": graph_id,
                "contract": cmeta.get("contract", ""),
                "contract_probability": "",
                "threshold": threshold,
                "contract_label": 1,
                "predicted_label": "",
                "candidate_interactions": cmeta.get("candidate_interactions", ""),
                "top_wrong_node_id": top_meta.get("node_id", ""),
                "top_wrong_function": top_meta.get("function", ""),
                "top_wrong_probability": top_prob,
                "true_positive_rank": best_rank,
                "failure_category": "top_ranked_wrong_interaction",
                "vulnerability_types": cmeta.get("vulnerability_types", ""),
            }
        )
    return rows


def train_predict_variant(
    bags: dict[str, tuple[ContractBag, ...]],
    embeddings: EmbeddingStore,
    run_name: str,
    pooling: str,
    seed: int,
    epochs: int,
    batch_size: int,
    lr: float,
    dropout: float,
    aux_weight: float,
    top_k: int,
) -> dict[str, Any]:
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    datasets = {split: ContractMILDataset(rows, embeddings) for split, rows in bags.items()}
    loaders = {
        "train": DataLoader(datasets["train"], batch_size=batch_size, shuffle=True, collate_fn=collate_contracts),
        "val": DataLoader(datasets["val"], batch_size=batch_size, shuffle=False, collate_fn=collate_contracts),
        "test": DataLoader(datasets["test"], batch_size=batch_size, shuffle=False, collate_fn=collate_contracts),
    }
    model = ContractMILHyperVul(pooling=pooling, top_k=top_k, dropout=dropout).to(device)
    contract_loss_fn = nn.BCEWithLogitsLoss(pos_weight=contract_pos_weight(bags["train"], device).reshape(1))
    interaction_loss_fn = nn.BCEWithLogitsLoss(pos_weight=interaction_pos_weight(bags["train"], device).reshape(1))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    history = []
    for epoch in range(1, epochs + 1):
        loss = train_one_epoch(model, loaders["train"], optimizer, contract_loss_fn, interaction_loss_fn, aux_weight, device)
        if epoch == 1 or epoch == epochs or epoch % 5 == 0:
            history.append({"epoch": epoch, "train_loss": loss})
    return {
        "run": run_name,
        "pooling": pooling,
        "seed": seed,
        "device": str(device),
        "history": history,
        "predictions": {
            "val": predict(model, loaders["val"], device),
            "test": predict(model, loaders["test"], device),
        },
    }


def split_counts(bags: dict[str, tuple[ContractBag, ...]]) -> dict[str, dict[str, int]]:
    counts = {}
    for split, rows in bags.items():
        positives = sum(row.contract_label == 1 for row in rows)
        counts[split] = {
            "contracts": len(rows),
            "positive_contracts": positives,
            "negative_contracts": len(rows) - positives,
            "positive_interactions": sum(sum(row.interaction_labels) for row in rows),
        }
    return counts


def add_native_rows(
    result: dict[str, Any],
    run_name: str,
    contract_rows: list[dict[str, Any]],
    interaction_rows: list[dict[str, Any]],
    localization_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
) -> None:
    pooling = result["pooling"]
    seed = result["seed"]
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]

    for policy_name in THRESHOLD_POLICIES:
        c_metrics = metrics_for_policy(
            val["contract_probs"],
            val["contract_labels"],
            test["contract_probs"],
            test["contract_labels"],
            policy_name,
        )
        for target in (0.70, 0.80, 0.90):
            p_at_r, threshold, actual_recall = precision_at_validation_recall(
                val["contract_probs"],
                val["contract_labels"],
                test["contract_probs"],
                test["contract_labels"],
                target,
            )
            c_metrics[f"test_precision_at_val_recall_{int(target * 100)}"] = p_at_r
            c_metrics[f"val_threshold_for_recall_{int(target * 100)}"] = threshold
            c_metrics[f"val_recall_at_threshold_{int(target * 100)}"] = actual_recall
        c_metrics.update({"run": run_name, "model": "HyperVul native MIL", "pooling": pooling, "seed": seed, "level": "contract"})
        contract_rows.append(c_metrics)

        i_metrics = metrics_for_policy(
            val["interaction_probs"],
            val["interaction_labels"],
            test["interaction_probs"],
            test["interaction_labels"],
            policy_name,
        )
        i_metrics.update({"run": run_name, "model": "HyperVul native MIL", "pooling": pooling, "seed": seed, "level": "interaction"})
        interaction_rows.append(i_metrics)

    loc = localization_metrics(test)
    loc.update({"run": run_name, "model": "HyperVul native MIL", "pooling": pooling, "seed": seed})
    localization_rows.append(loc)

    max_f1_threshold = [
        row for row in contract_rows
        if row["run"] == run_name and row["pooling"] == pooling and row["seed"] == seed and row["threshold_policy"] == "max_f1"
    ][-1]["threshold"]
    error_rows.extend(error_analysis_rows(run_name, pooling, seed, test, float(max_f1_threshold)))


def append_wrapped_baseline(contract_rows: list[dict[str, Any]], localization_rows: list[dict[str, Any]], pooling_rows: list[dict[str, Any]]) -> None:
    phase0d_contract = [
        row for row in read_csv(REPORTS / "phase0d_contract_metrics.csv")
        if row.get("model") == "Current HyperVul"
    ]
    phase0d_loc = [
        row for row in read_csv(REPORTS / "phase0d_localization_metrics.csv")
        if row.get("model") == "Current HyperVul"
    ]
    for row in phase0d_contract:
        out = dict(row)
        out.update({"run": "all_scope", "model": "Current wrapped interaction HyperVul", "pooling": "wrapped_max", "level": "contract"})
        contract_rows.append(out)
    for row in phase0d_loc:
        out = dict(row)
        out.update({"run": "all_scope", "model": "Current wrapped interaction HyperVul", "pooling": "wrapped_max"})
        localization_rows.append(out)
    wrapped_max_f1 = [row for row in phase0d_contract if row.get("threshold_policy") == "max_f1"]
    if wrapped_max_f1:
        stats = mean_std(wrapped_max_f1, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        loc_stats = mean_std(phase0d_loc, ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"])
        pooling_rows.append(
            {
                "run": "all_scope",
                "model": "Current wrapped interaction HyperVul",
                "pooling": "wrapped_max",
                **{f"contract_{k}_mean": v["mean"] for k, v in stats.items()},
                **{f"contract_{k}_std": v["std"] for k, v in stats.items()},
                **{f"{k}_mean": v["mean"] for k, v in loc_stats.items()},
                **{f"{k}_std": v["std"] for k, v in loc_stats.items()},
            }
        )


def build_pooling_rows(contract_rows: list[dict[str, Any]], localization_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    keys = sorted({(row["run"], row["model"], row["pooling"]) for row in contract_rows})
    for run, model, pooling in keys:
        contract_subset = [
            row for row in contract_rows
            if row["run"] == run and row["model"] == model and row["pooling"] == pooling and row["threshold_policy"] == "max_f1"
        ]
        loc_subset = [
            row for row in localization_rows
            if row["run"] == run and row["model"] == model and row["pooling"] == pooling
        ]
        if not contract_subset:
            continue
        c_stats = mean_std(contract_subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        l_stats = mean_std(loc_subset, ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"])
        out = {"run": run, "model": model, "pooling": pooling}
        out.update({f"contract_{k}_mean": v["mean"] for k, v in c_stats.items()})
        out.update({f"contract_{k}_std": v["std"] for k, v in c_stats.items()})
        out.update({f"{k}_mean": v["mean"] for k, v in l_stats.items()})
        out.update({f"{k}_std": v["std"] for k, v in l_stats.items()})
        rows.append(out)
    return rows


def report_lines(
    counts: dict[str, dict[str, dict[str, int]]],
    contract_rows: list[dict[str, Any]],
    localization_rows: list[dict[str, Any]],
    pooling_rows: list[dict[str, Any]],
    reentrancy_rows: list[dict[str, Any]],
) -> list[str]:
    lines = ["# Phase 0E Native Contract-Level MIL Training", ""]
    lines.append("No augmentation, architecture feature additions, or test-threshold tuning were used. Thresholds are selected on validation only.")
    lines.append("")
    lines.append("## Split Counts")
    lines.append("| Run | Split | Contracts | Positive Contracts | Negative Contracts | Positive Interactions |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for run, split_counts_for_run in counts.items():
        for split in ("train", "val", "test"):
            item = split_counts_for_run[split]
            lines.append(f"| {run} | {split} | {item['contracts']} | {item['positive_contracts']} | {item['negative_contracts']} | {item['positive_interactions']} |")

    lines.append("")
    lines.append("## Contract Metrics")
    lines.append("Validation max-F1 threshold, mean +/- std over seeds.")
    lines.append("")
    lines.append("| Run | Model | Pooling | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")
    for run, model, pooling in sorted({(r["run"], r["model"], r["pooling"]) for r in contract_rows}):
        subset = [r for r in contract_rows if r["run"] == run and r["model"] == model and r["pooling"] == pooling and r["threshold_policy"] == "max_f1"]
        stats = mean_std(subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        lines.append(
            f"| {run} | {model} | {pooling} | {format_mean_std(stats,'precision')} | {format_mean_std(stats,'recall')} | "
            f"{format_mean_std(stats,'f1')} | {format_mean_std(stats,'f2')} | {format_mean_std(stats,'pr_auc')} | {format_mean_std(stats,'roc_auc')} |"
        )

    lines.append("")
    lines.append("## Localization Metrics")
    lines.append("| Run | Model | Pooling | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run, model, pooling in sorted({(r["run"], r["model"], r["pooling"]) for r in localization_rows}):
        subset = [r for r in localization_rows if r["run"] == run and r["model"] == model and r["pooling"] == pooling]
        stats = mean_std(subset, ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"])
        lines.append(
            f"| {run} | {model} | {pooling} | {format_mean_std(stats,'top1_hit')} | {format_mean_std(stats,'top3_hit')} | "
            f"{format_mean_std(stats,'top5_hit')} | {format_mean_std(stats,'mrr')} | {format_mean_std(stats,'recall_at_1')} | "
            f"{format_mean_std(stats,'recall_at_3')} | {format_mean_std(stats,'recall_at_5')} |"
        )

    best_all = max(
        [r for r in pooling_rows if r["run"] == "all_scope" and r["model"] == "HyperVul native MIL"],
        key=lambda r: float(r.get("contract_f1_mean", 0.0)),
        default=None,
    )
    best_re = max(
        [r for r in pooling_rows if r["run"] == "reentrancy_only" and r["model"] == "HyperVul native MIL"],
        key=lambda r: float(r.get("contract_f1_mean", 0.0)),
        default=None,
    )
    wrapped = next((r for r in pooling_rows if r["run"] == "all_scope" and r["model"] == "Current wrapped interaction HyperVul"), None)

    lines.append("")
    lines.append("## Error Analysis")
    lines.append("Detailed false-positive contracts, false-negative contracts, and positive contracts where the true interaction is not in Top-3 are in `reports/phase0e_error_analysis.csv`.")
    lines.append("")
    lines.append("## Final Recommendation")
    if best_all and wrapped:
        improves = float(best_all.get("contract_f1_mean", 0.0)) > float(wrapped.get("contract_f1_mean", 0.0))
        lines.append(f"- Native MIL {'improves' if improves else 'does not improve'} over the wrapped contract evaluation by contract F1 on the all-scope clean split.")
    if best_all:
        lines.append(f"- Best all-scope native pooling: `{best_all['pooling']}`.")
    if best_re:
        lines.append(f"- Best reentrancy-only native pooling: `{best_re['pooling']}`. Reentrancy test positives are small, so variance should be treated as high-confidence-warning material rather than final proof.")
    lines.append("- Keep reentrancy-only as the first focused experiment if it matches or exceeds all-scope stability; unchecked low-level call remains manual-review only.")
    lines.append("- Phase 1 augmentation should wait until these native MIL results are accepted; the next priority should be chosen from the observed errors: hard-negative mining for false positives, safety features/global context for false negatives.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--aux-weight", type=float, default=0.5)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--pooling", nargs="+", default=list(POOLING_VARIANTS), choices=POOLING_VARIANTS)
    parser.add_argument("--skip-reentrancy", action="store_true")
    args = parser.parse_args()

    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)

    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    all_scope_bags = build_contract_bags(bundle)
    reentrancy_bags = build_contract_bags(bundle, "reentrancy_only")
    counts = {
        "all_scope": split_counts(all_scope_bags),
        "reentrancy_only": split_counts(reentrancy_bags),
    }
    print(f"All-scope counts: {counts['all_scope']}", flush=True)
    print(f"Reentrancy counts: {counts['reentrancy_only']}", flush=True)

    contract_rows: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []
    localization_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for run_name, bags in [("all_scope", all_scope_bags)] + ([] if args.skip_reentrancy else [("reentrancy_only", reentrancy_bags)]):
        for pooling in args.pooling:
            for seed in args.seeds:
                print(f"Running {run_name} {pooling} seed={seed} epochs={args.epochs}", flush=True)
                result = train_predict_variant(
                    bags=bags,
                    embeddings=embeddings,
                    run_name=run_name,
                    pooling=pooling,
                    seed=seed,
                    epochs=args.epochs,
                    batch_size=args.batch_size,
                    lr=args.lr,
                    dropout=args.dropout,
                    aux_weight=args.aux_weight,
                    top_k=args.top_k,
                )
                add_native_rows(result, run_name, contract_rows, interaction_rows, localization_rows, error_rows)
                print(f"  done {run_name} {pooling} seed={seed}", flush=True)

    pooling_rows = build_pooling_rows(contract_rows, localization_rows)
    append_wrapped_baseline(contract_rows, localization_rows, pooling_rows)
    pooling_rows = build_pooling_rows(contract_rows, localization_rows)

    metric_fields = [
        "run",
        "model",
        "pooling",
        "seed",
        "level",
        "threshold_policy",
        "selection_policy",
        "threshold",
        "validation_precision_at_threshold",
        "validation_recall_at_threshold",
        "precision",
        "recall",
        "f1",
        "f2",
        "pr_auc",
        "roc_auc",
        "tp",
        "tn",
        "fp",
        "fn",
        "support",
        "positive_support",
        "negative_support",
        "test_precision_at_val_recall_70",
        "test_precision_at_val_recall_80",
        "test_precision_at_val_recall_90",
        "val_threshold_for_recall_70",
        "val_threshold_for_recall_80",
        "val_threshold_for_recall_90",
        "val_recall_at_threshold_70",
        "val_recall_at_threshold_80",
        "val_recall_at_threshold_90",
    ]
    loc_fields = ["run", "model", "pooling", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"]
    pool_fields = [
        "run",
        "model",
        "pooling",
        "contract_precision_mean",
        "contract_precision_std",
        "contract_recall_mean",
        "contract_recall_std",
        "contract_f1_mean",
        "contract_f1_std",
        "contract_f2_mean",
        "contract_f2_std",
        "contract_pr_auc_mean",
        "contract_pr_auc_std",
        "contract_roc_auc_mean",
        "contract_roc_auc_std",
        "top1_hit_mean",
        "top1_hit_std",
        "top3_hit_mean",
        "top3_hit_std",
        "top5_hit_mean",
        "top5_hit_std",
        "mrr_mean",
        "mrr_std",
        "recall_at_1_mean",
        "recall_at_1_std",
        "recall_at_3_mean",
        "recall_at_3_std",
        "recall_at_5_mean",
        "recall_at_5_std",
    ]
    error_fields = [
        "run",
        "pooling",
        "seed",
        "error_type",
        "graph_id",
        "contract",
        "contract_probability",
        "threshold",
        "contract_label",
        "predicted_label",
        "candidate_interactions",
        "top_wrong_node_id",
        "top_wrong_function",
        "top_wrong_probability",
        "true_positive_rank",
        "failure_category",
        "vulnerability_types",
    ]

    write_csv(REPORTS / "phase0e_native_contract_metrics.csv", contract_rows, metric_fields)
    write_csv(REPORTS / "phase0e_localization_metrics.csv", localization_rows, loc_fields)
    write_csv(REPORTS / "phase0e_pooling_ablation.csv", pooling_rows, pool_fields)
    write_csv(REPORTS / "phase0e_reentrancy_only_metrics.csv", [r for r in contract_rows if r["run"] == "reentrancy_only"], metric_fields)
    write_csv(REPORTS / "phase0e_error_analysis.csv", error_rows, error_fields)
    write_csv(REPORTS / "phase0e_interaction_secondary_metrics.csv", interaction_rows, metric_fields[:23])

    summary = {
        "generated_at": "2026-06-27",
        "graph_dir": str(GRAPH_DIR),
        "seeds": args.seeds,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "aux_weight": args.aux_weight,
        "top_k": args.top_k,
        "counts": counts,
        "pooling_ablation": pooling_rows,
    }
    (REPORTS / "phase0e_native_contract_mil_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (REPORTS / "phase0e_native_contract_mil_report.md").write_text(
        "\n".join(report_lines(counts, contract_rows, localization_rows, pooling_rows, [r for r in contract_rows if r["run"] == "reentrancy_only"])) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote Phase 0E reports to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
