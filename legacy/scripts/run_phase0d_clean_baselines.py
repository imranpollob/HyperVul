#!/usr/bin/env python3
"""Phase 0D clean-split baseline rerun.

Runs existing fair-eval model families on data/contract_graphs_clean without
augmentation or architecture changes. Captures interaction, contract, and
localization metrics for validation-selected thresholds.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTDIR = ROOT / "experiments" / "phase0d_clean"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"

FAIR_SRC = ROOT / "hypervul_fair_eval" / "src"
if str(FAIR_SRC) not in sys.path:
    sys.path.insert(0, str(FAIR_SRC))

from fair_eval.builders import (  # noqa: E402
    build_callgraph_views,
    build_function_examples,
    build_pairwise_graph_views,
    build_sequence_examples,
)
from fair_eval.builders.hyperedge_view import build_hyperedge_examples  # noqa: E402
from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.features.symbolic import SYMBOLIC_DIM  # noqa: E402
from fair_eval.models import (  # noqa: E402
    FunctionFeaturesMLP,
    FunctionMLP,
    FunctionSequenceModel,
    GraphNodeClassifier,
    HyperVulModel,
)
from fair_eval.training import (  # noqa: E402
    AsymmetricLoss,
    HyperVulTensorDataset,
    FunctionTensorDataset,
    GraphTensorDataset,
    SCALAR_FEATURE_KEYS,
    SequenceTensorDataset,
    bce_with_logits_for_labels,
    binary_metrics,
    collate_graphs,
    collate_hypervul,
    collate_sequences,
    function_features_step_fn,
    function_step_fn,
    graph_step_fn,
    hypervul_step_fn,
    positive_weight,
    scalar_standardizer,
    sequence_step_fn,
    select_threshold,
    set_global_seed,
    train_one_epoch,
)


REQUESTED_MODELS = (
    "Function-MLP",
    "Function+Features MLP",
    "Sequence-BiGRU",
    "CallGraph-GAT",
    "Pairwise-RGCN",
    "Pairwise-GAT",
    "Current HyperVul",
)

THRESHOLD_POLICIES = {
    "max_f1": {"policy": "max_f1", "target_recall": 0.90, "target_precision": 0.70},
    "high_recall": {"policy": "target_recall", "target_recall": 0.90, "target_precision": 0.70},
    "precision_focused": {"policy": "target_precision", "target_recall": 0.90, "target_precision": 0.70},
}


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def safe_auc(labels: np.ndarray, probs: np.ndarray, kind: str) -> float | None:
    if len(np.unique(labels)) < 2:
        return None
    from sklearn.metrics import average_precision_score, roc_auc_score

    return float(average_precision_score(labels, probs)) if kind == "pr" else float(roc_auc_score(labels, probs))


def threshold_for_precision_at_recall(probs: np.ndarray, labels: np.ndarray, target_recall: float) -> tuple[float, float, float]:
    best = None
    for threshold in np.linspace(0, 1, 1001):
        metrics = binary_metrics(probs, labels, float(threshold))
        if metrics["recall"] >= target_recall:
            cand = (metrics["precision"], float(threshold), metrics["recall"])
            if best is None or cand > best:
                best = cand
    if best is None:
        return 0.0, 1.0, 0.0
    return best


def graph_maps(bundle) -> tuple[dict[str, int], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    contract_labels = {}
    graph_meta = {}
    node_meta = {}
    for split, graphs in bundle.graphs.items():
        for graph in graphs:
            raw = graph.raw
            contract_labels[graph.graph_id] = int(raw.get("contract_label", 1 if graph.positive_count else 0))
            graph_meta[graph.graph_id] = {
                "split": split,
                "graph_id": graph.graph_id,
                "contract": graph.contract,
                "project": graph.project,
                "vulnerability_types": raw.get("vulnerability_types", []),
                "localization": raw.get("localization", {}),
            }
            for node in graph.interaction_nodes:
                node_meta[f"{graph.graph_id}::{node.id}"] = {
                    "split": split,
                    "graph_id": graph.graph_id,
                    "node_id": node.id,
                    "contract": graph.contract,
                    "function": node.function or "",
                    "label": int(node.label or 0),
                    "vulnerability_type": node.raw.get("vulnerability_type", ""),
                    "scope": (node.raw.get("provenance") or {}).get("scope", ""),
                    "external_methods": "|".join(str(x.get("method", "")) for x in node.external_calls),
                    "external_call_count": len(node.external_calls),
                    "state_var_count": len(node.state_vars_accessed),
                    "evidence_pointer": node.raw.get("evidence_pointer", ""),
                }
    return contract_labels, graph_meta, node_meta


def build_all_views(project_root: Path):
    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    bundle = load_dataset_bundle(project_root)
    embeddings = EmbeddingStore(project_root)
    function_examples = {split: build_function_examples(graphs) for split, graphs in bundle.graphs.items()}
    scalar_mean, scalar_std = scalar_standardizer(function_examples["train"])
    sequence_examples = {split: build_sequence_examples(graphs) for split, graphs in bundle.graphs.items()}
    callgraph_views = {split: build_callgraph_views(graphs) for split, graphs in bundle.graphs.items()}
    pairwise_views = {split: build_pairwise_graph_views(graphs) for split, graphs in bundle.graphs.items()}
    hyperedge_examples = {split: build_hyperedge_examples(graphs) for split, graphs in bundle.graphs.items()}
    contract_labels, graph_meta, node_meta = graph_maps(bundle)
    return {
        "bundle": bundle,
        "embeddings": embeddings,
        "function_examples": function_examples,
        "scalar_mean": scalar_mean,
        "scalar_std": scalar_std,
        "sequence_examples": sequence_examples,
        "callgraph_views": callgraph_views,
        "pairwise_views": pairwise_views,
        "hyperedge_examples": hyperedge_examples,
        "contract_labels": contract_labels,
        "graph_meta": graph_meta,
        "node_meta": node_meta,
    }


def check_counts(bundle) -> dict[str, dict[str, int]]:
    expected = {
        "train": {"contracts": 1339, "positive_contracts": 140, "negative_contracts": 1199},
        "val": {"contracts": 280, "positive_contracts": 30, "negative_contracts": 250},
        "test": {"contracts": 212, "positive_contracts": 30, "negative_contracts": 182},
    }
    counts = {}
    for split, graphs in bundle.graphs.items():
        pos = sum(int(g.raw.get("contract_label", 1 if g.positive_count else 0)) == 1 for g in graphs)
        counts[split] = {"contracts": len(graphs), "positive_contracts": pos, "negative_contracts": len(graphs) - pos}
    if counts != expected:
        raise RuntimeError(f"Clean split counts mismatch. expected={expected}, actual={counts}")
    return counts


def labels_from_function_examples(examples) -> torch.Tensor:
    return torch.tensor([x.label for x in examples], dtype=torch.float32)


def meta_function(examples) -> list[dict[str, str]]:
    return [
        {"graph_id": e.graph_id, "node_id": e.node_id, "function": e.function, "key": f"{e.graph_id}::{e.node_id}"}
        for e in examples
    ]


def meta_sequence(sequences) -> list[dict[str, str]]:
    out = []
    for seq in sequences:
        for node_id, fn, label in zip(seq.node_ids, seq.functions, seq.labels):
            if label in (0, 1):
                out.append({"graph_id": seq.graph_id, "node_id": node_id, "function": fn, "key": f"{seq.graph_id}::{node_id}"})
    return out


def meta_graph_views(views) -> list[dict[str, str]]:
    out = []
    for graph in views:
        for node in graph.nodes:
            if node.label in (0, 1):
                out.append({"graph_id": graph.graph_id, "node_id": node.node_id, "function": node.function or "", "key": f"{graph.graph_id}::{node.node_id}"})
    return out


def meta_hyperedges(examples) -> list[dict[str, str]]:
    return [
        {
            "graph_id": e.graph_id,
            "node_id": e.interaction_node_id,
            "function": e.function,
            "key": f"{e.graph_id}::{e.interaction_node_id}",
        }
        for e in examples
    ]


def make_loaders(data: dict[str, Any], model_name: str, batch_size: int):
    emb = data["embeddings"]
    if model_name == "Function-MLP":
        datasets = {
            s: FunctionTensorDataset(data["function_examples"][s], emb)
            for s in ["train", "val", "test"]
        }
        metas = {s: meta_function(data["function_examples"][s]) for s in ["train", "val", "test"]}
        return datasets, metas, None, labels_from_function_examples(data["function_examples"]["train"])
    if model_name == "Function+Features MLP":
        datasets = {
            s: FunctionTensorDataset(
                data["function_examples"][s],
                emb,
                scalar_mean=data["scalar_mean"],
                scalar_std=data["scalar_std"],
            )
            for s in ["train", "val", "test"]
        }
        metas = {s: meta_function(data["function_examples"][s]) for s in ["train", "val", "test"]}
        return datasets, metas, None, labels_from_function_examples(data["function_examples"]["train"])
    if model_name == "Sequence-BiGRU":
        datasets = {
            s: SequenceTensorDataset(
                data["sequence_examples"][s],
                emb,
                scalar_mean=data["scalar_mean"],
                scalar_std=data["scalar_std"],
            )
            for s in ["train", "val", "test"]
        }
        metas = {s: meta_sequence(data["sequence_examples"][s]) for s in ["train", "val", "test"]}
        return datasets, metas, collate_sequences, labels_from_function_examples(data["function_examples"]["train"])
    if model_name == "CallGraph-GAT":
        datasets = {
            s: GraphTensorDataset(
                data["callgraph_views"][s],
                emb,
                scalar_mean=data["scalar_mean"],
                scalar_std=data["scalar_std"],
            )
            for s in ["train", "val", "test"]
        }
        metas = {s: meta_graph_views(data["callgraph_views"][s]) for s in ["train", "val", "test"]}
        return datasets, metas, collate_graphs, labels_from_function_examples(data["function_examples"]["train"])
    if model_name in {"Pairwise-RGCN", "Pairwise-GAT"}:
        datasets = {
            s: GraphTensorDataset(
                data["pairwise_views"][s],
                emb,
                scalar_mean=data["scalar_mean"],
                scalar_std=data["scalar_std"],
            )
            for s in ["train", "val", "test"]
        }
        metas = {s: meta_graph_views(data["pairwise_views"][s]) for s in ["train", "val", "test"]}
        return datasets, metas, collate_graphs, labels_from_function_examples(data["function_examples"]["train"])
    if model_name == "Current HyperVul":
        datasets = {
            s: HyperVulTensorDataset(data["hyperedge_examples"][s], emb, symbolic_mode="legacy8")
            for s in ["train", "val", "test"]
        }
        metas = {s: meta_hyperedges(data["hyperedge_examples"][s]) for s in ["train", "val", "test"]}
        labels = torch.tensor([e.label for e in data["hyperedge_examples"]["train"]], dtype=torch.float32)
        return datasets, metas, collate_hypervul, labels
    raise ValueError(model_name)


def make_model_and_step(model_name: str, dropout: float, train_labels: torch.Tensor, device: torch.device):
    if model_name == "Function-MLP":
        return FunctionMLP(dropout=dropout), function_step_fn, bce_with_logits_for_labels(train_labels, device=device)
    if model_name == "Function+Features MLP":
        return FunctionFeaturesMLP(dropout=dropout), function_features_step_fn, bce_with_logits_for_labels(train_labels, device=device)
    if model_name == "Sequence-BiGRU":
        return FunctionSequenceModel(scalar_dim=len(SCALAR_FEATURE_KEYS), dropout=dropout), sequence_step_fn, bce_with_logits_for_labels(train_labels, device=device)
    if model_name == "CallGraph-GAT":
        return GraphNodeClassifier(scalar_dim=len(SCALAR_FEATURE_KEYS), conv="gat", dropout=dropout), graph_step_fn, bce_with_logits_for_labels(train_labels, device=device)
    if model_name == "Pairwise-RGCN":
        return GraphNodeClassifier(scalar_dim=len(SCALAR_FEATURE_KEYS), conv="rgcn", edge_types=3, dropout=dropout), graph_step_fn, bce_with_logits_for_labels(train_labels, device=device)
    if model_name == "Pairwise-GAT":
        return GraphNodeClassifier(scalar_dim=len(SCALAR_FEATURE_KEYS), conv="gat", dropout=dropout), graph_step_fn, bce_with_logits_for_labels(train_labels, device=device)
    if model_name == "Current HyperVul":
        model = HyperVulModel(symbolic_dim=8, dropout=dropout, use_symbolic=True, use_localization=True, use_sequence_pool=True)
        loss = AsymmetricLoss(pos_weight=positive_weight(train_labels).to(device))
        return model, hypervul_step_fn, loss
    raise ValueError(model_name)


@torch.no_grad()
def predict_with_meta(model, loader, step_fn, device, metas: list[dict[str, str]]) -> dict[str, Any]:
    model.eval()
    logits_list = []
    labels_list = []
    for batch in loader:
        logits, labels = step_fn(model, batch, device)
        logits_list.append(logits.detach().cpu().numpy())
        labels_list.append(labels.detach().cpu().numpy())
    logits = np.concatenate(logits_list) if logits_list else np.asarray([])
    labels = np.concatenate(labels_list).astype(int) if labels_list else np.asarray([], dtype=int)
    probs = 1.0 / (1.0 + np.exp(-logits))
    if len(metas) != len(labels):
        raise RuntimeError(f"Prediction/meta length mismatch: {len(labels)} vs {len(metas)}")
    return {"logits": logits, "probs": probs, "labels": labels, "meta": metas}


def train_predict_one(
    data: dict[str, Any],
    model_name: str,
    seed: int,
    epochs: int,
    batch_size: int,
    lr: float,
    dropout: float,
) -> dict[str, Any]:
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    datasets, metas, collate_fn, train_labels = make_loaders(data, model_name, batch_size)
    loaders = {
        "train": DataLoader(datasets["train"], batch_size=batch_size, shuffle=True, collate_fn=collate_fn),
        "val": DataLoader(datasets["val"], batch_size=batch_size, shuffle=False, collate_fn=collate_fn),
        "test": DataLoader(datasets["test"], batch_size=batch_size, shuffle=False, collate_fn=collate_fn),
    }
    model, step_fn, loss_fn = make_model_and_step(model_name, dropout, train_labels, device)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    history = []
    for epoch in range(1, epochs + 1):
        train_result = train_one_epoch(model, loaders["train"], optimizer, loss_fn, step_fn, device, grad_clip=5.0)
        if epoch == epochs or epoch == 1 or epoch % 5 == 0:
            val_pred = predict_with_meta(model, loaders["val"], step_fn, device, metas["val"])
            sel = select_threshold(val_pred["probs"], val_pred["labels"], policy="max_f1")
            vm = binary_metrics(val_pred["probs"], val_pred["labels"], sel.threshold)
            history.append({"epoch": epoch, "train_loss": train_result.loss, "val_f1": vm["f1"], "val_f2": vm["f2"]})
    return {
        "model": model_name,
        "seed": seed,
        "device": str(device),
        "history": history,
        "predictions": {
            "val": predict_with_meta(model, loaders["val"], step_fn, device, metas["val"]),
            "test": predict_with_meta(model, loaders["test"], step_fn, device, metas["test"]),
        },
    }


def metrics_for_policy(val_probs, val_labels, test_probs, test_labels, policy_name: str, level: str) -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = THRESHOLD_POLICIES[policy_name]
    sel = select_threshold(
        val_probs,
        val_labels,
        policy=cfg["policy"],
        target_recall=cfg["target_recall"],
        target_precision=cfg["target_precision"],
    )
    metrics = binary_metrics(test_probs, test_labels, sel.threshold)
    metrics = dict(metrics)
    metrics.update(
        {
            "threshold_policy": policy_name,
            "selection_policy": cfg["policy"],
            "threshold": sel.threshold,
            "validation_precision_at_threshold": sel.precision,
            "validation_recall_at_threshold": sel.recall,
            "level": level,
        }
    )
    return metrics, sel.__dict__


def contract_scores(pred: dict[str, Any], contract_labels: dict[str, int]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    by_graph = defaultdict(list)
    for prob, meta in zip(pred["probs"], pred["meta"]):
        by_graph[meta["graph_id"]].append(float(prob))
    gids = sorted(by_graph)
    probs = np.array([max(by_graph[g]) for g in gids], dtype=float)
    labels = np.array([contract_labels[g] for g in gids], dtype=int)
    return probs, labels, gids


def localization_metrics(pred: dict[str, Any], graph_meta: dict[str, dict[str, Any]], ks=(1, 3, 5)) -> dict[str, float]:
    by_graph = defaultdict(list)
    for prob, label, meta in zip(pred["probs"], pred["labels"], pred["meta"]):
        by_graph[meta["graph_id"]].append((float(prob), int(label), meta["node_id"]))
    pos_graphs = [gid for gid, rows in by_graph.items() if any(label == 1 for _p, label, _nid in rows)]
    out = {f"top{k}_hit": 0.0 for k in ks}
    out.update({f"recall_at_{k}": 0.0 for k in ks})
    rr = []
    for gid in pos_graphs:
        ranked = sorted(by_graph[gid], key=lambda x: x[0], reverse=True)
        pos_ids = {nid for _p, label, nid in ranked if label == 1}
        ranks = [idx + 1 for idx, (_p, label, _nid) in enumerate(ranked) if label == 1]
        rr.append(1.0 / min(ranks) if ranks else 0.0)
        for k in ks:
            top_ids = {nid for _p, _label, nid in ranked[:k]}
            hit_count = len(pos_ids & top_ids)
            out[f"top{k}_hit"] += 1.0 if hit_count > 0 else 0.0
            out[f"recall_at_{k}"] += hit_count / max(len(pos_ids), 1)
    denom = max(len(pos_graphs), 1)
    for k in ks:
        out[f"top{k}_hit"] /= denom
        out[f"recall_at_{k}"] /= denom
    out["mrr"] = float(np.mean(rr)) if rr else 0.0
    out["positive_contracts"] = len(pos_graphs)
    return out


def scope_performance(pred: dict[str, Any], node_meta: dict[str, dict[str, Any]], threshold: float) -> dict[str, dict[str, Any]]:
    rows = defaultdict(lambda: {"probs": [], "labels": []})
    for prob, label, meta in zip(pred["probs"], pred["labels"], pred["meta"]):
        nm = node_meta.get(meta["key"], {})
        scopes = [s for s in str(nm.get("scope", "")).split("|") if s]
        for scope in scopes:
            rows[scope]["probs"].append(float(prob))
            rows[scope]["labels"].append(int(label))
    out = {}
    for scope, vals in rows.items():
        if any(vals["labels"]):
            out[scope] = binary_metrics(np.array(vals["probs"]), np.array(vals["labels"]), threshold)
    return out


def error_rows_for_hypervul(test_pred: dict[str, Any], threshold: float, node_meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for prob, label, meta in zip(test_pred["probs"], test_pred["labels"], test_pred["meta"]):
        pred = int(float(prob) >= threshold)
        if pred == int(label):
            continue
        nm = node_meta.get(meta["key"], {})
        rows.append(
            {
                "error_type": "false_positive" if pred == 1 else "false_negative",
                "probability": float(prob),
                "threshold": threshold,
                "graph_id": meta["graph_id"],
                "contract": nm.get("contract", ""),
                "function": nm.get("function", meta.get("function", "")),
                "node_id": meta["node_id"],
                "label": int(label),
                "pred": pred,
                "vulnerability_type": nm.get("vulnerability_type", ""),
                "scope": nm.get("scope", ""),
                "external_methods": nm.get("external_methods", ""),
                "external_call_count": nm.get("external_call_count", ""),
                "state_var_count": nm.get("state_var_count", ""),
                "evidence_pointer": nm.get("evidence_pointer", ""),
            }
        )
    return sorted(rows, key=lambda r: (r["error_type"], -abs(float(r["probability"]) - threshold)))


def summarize_numeric(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, Any]:
    out = {}
    for key in keys:
        vals = [float(r[key]) for r in rows if r.get(key) not in (None, "")]
        if vals:
            out[key] = {"mean": float(np.mean(vals)), "std": float(np.std(vals)), "values": vals}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--models", nargs="+", default=list(REQUESTED_MODELS), choices=REQUESTED_MODELS)
    args = parser.parse_args()

    OUTDIR.mkdir(parents=True, exist_ok=True)
    data = build_all_views(ROOT)
    counts = check_counts(data["bundle"])
    print(f"Clean split counts confirmed: {counts}")

    model_metric_rows = []
    contract_metric_rows = []
    localization_rows = []
    error_rows = []
    raw_results = {}

    for model_name in args.models:
        raw_results[model_name] = {}
        for seed in args.seeds:
            print(f"Running {model_name} seed={seed} epochs={args.epochs}", flush=True)
            result = train_predict_one(data, model_name, seed, args.epochs, args.batch_size, args.lr, args.dropout)
            raw_results[model_name][seed] = {
                "history": result["history"],
                "device": result["device"],
            }
            val_pred = result["predictions"]["val"]
            test_pred = result["predictions"]["test"]
            val_contract_probs, val_contract_labels, _ = contract_scores(val_pred, data["contract_labels"])
            test_contract_probs, test_contract_labels, test_gids = contract_scores(test_pred, data["contract_labels"])

            for policy_name in THRESHOLD_POLICIES:
                im, _isel = metrics_for_policy(
                    val_pred["probs"],
                    val_pred["labels"],
                    test_pred["probs"],
                    test_pred["labels"],
                    policy_name,
                    "interaction",
                )
                im.update({"model": model_name, "seed": seed})
                model_metric_rows.append(im)

                cm, csel = metrics_for_policy(
                    val_contract_probs,
                    val_contract_labels,
                    test_contract_probs,
                    test_contract_labels,
                    policy_name,
                    "contract",
                )
                for target in [0.70, 0.80, 0.90]:
                    p_at_r, thr, actual_r = threshold_for_precision_at_recall(val_contract_probs, val_contract_labels, target)
                    test_m = binary_metrics(test_contract_probs, test_contract_labels, thr)
                    cm[f"test_precision_at_val_recall_{int(target*100)}"] = test_m["precision"]
                    cm[f"val_threshold_for_recall_{int(target*100)}"] = thr
                    cm[f"val_recall_at_threshold_{int(target*100)}"] = actual_r
                cm.update({"model": model_name, "seed": seed})
                contract_metric_rows.append(cm)

            loc = localization_metrics(test_pred, data["graph_meta"])
            loc.update({"model": model_name, "seed": seed})
            localization_rows.append(loc)

            if model_name == "Current HyperVul":
                # Use max-F1 interaction threshold for error analysis.
                hv_thr = [r for r in model_metric_rows if r["model"] == model_name and r["seed"] == seed and r["threshold_policy"] == "max_f1"][-1]["threshold"]
                seed_errors = error_rows_for_hypervul(test_pred, hv_thr, data["node_meta"])
                for row in seed_errors:
                    row["model"] = model_name
                    row["seed"] = seed
                error_rows.extend(seed_errors)
                scope_perf = scope_performance(test_pred, data["node_meta"], hv_thr)
                raw_results[model_name][seed]["scope_performance"] = scope_perf

            print(f"  done {model_name} seed={seed}", flush=True)

    metric_fields = [
        "model",
        "seed",
        "threshold_policy",
        "selection_policy",
        "level",
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
    ]
    write_csv(REPORTS / "phase0d_model_metrics.csv", model_metric_rows, metric_fields)
    contract_fields = metric_fields + [
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
    write_csv(REPORTS / "phase0d_contract_metrics.csv", contract_metric_rows, contract_fields)
    write_csv(
        REPORTS / "phase0d_localization_metrics.csv",
        localization_rows,
        ["model", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"],
    )
    write_csv(
        REPORTS / "phase0d_hypervul_errors.csv",
        error_rows,
        [
            "model",
            "seed",
            "error_type",
            "probability",
            "threshold",
            "graph_id",
            "contract",
            "function",
            "node_id",
            "label",
            "pred",
            "vulnerability_type",
            "scope",
            "external_methods",
            "external_call_count",
            "state_var_count",
            "evidence_pointer",
        ],
    )

    summary = {
        "generated_at": "2026-06-27",
        "graph_dir": str(GRAPH_DIR),
        "counts": counts,
        "seeds": args.seeds,
        "epochs": args.epochs,
        "models": {},
        "hypervul_scope_performance": raw_results.get("Current HyperVul", {}),
    }
    for model in args.models:
        summary["models"][model] = {
            "interaction_max_f1": summarize_numeric(
                [r for r in model_metric_rows if r["model"] == model and r["threshold_policy"] == "max_f1"],
                ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"],
            ),
            "contract_max_f1": summarize_numeric(
                [r for r in contract_metric_rows if r["model"] == model and r["threshold_policy"] == "max_f1"],
                ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"],
            ),
            "localization": summarize_numeric(
                [r for r in localization_rows if r["model"] == model],
                ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"],
            ),
        }
    (REPORTS / "phase0d_clean_baseline_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def cell(stats, metric):
        item = stats.get(metric)
        if not item:
            return "n/a"
        return f"{item['mean']*100:.2f} +/- {item['std']*100:.2f}"

    lines = ["# Phase 0D Clean Baseline Rerun", ""]
    lines.append("Clean split counts were confirmed before training.")
    lines.append("")
    lines.append("## Interaction Metrics (Test, Validation Max-F1 Threshold)")
    lines.append("| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for model in args.models:
        stats = summary["models"][model]["interaction_max_f1"]
        lines.append(f"| {model} | {cell(stats,'precision')} | {cell(stats,'recall')} | {cell(stats,'f1')} | {cell(stats,'f2')} | {cell(stats,'pr_auc')} | {cell(stats,'roc_auc')} |")
    lines.append("")
    lines.append("## Contract Metrics (Test, Validation Max-F1 Threshold)")
    lines.append("| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for model in args.models:
        stats = summary["models"][model]["contract_max_f1"]
        lines.append(f"| {model} | {cell(stats,'precision')} | {cell(stats,'recall')} | {cell(stats,'f1')} | {cell(stats,'f2')} | {cell(stats,'pr_auc')} | {cell(stats,'roc_auc')} |")
    lines.append("")
    lines.append("## Localization Metrics")
    lines.append("| Model | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for model in args.models:
        stats = summary["models"][model]["localization"]
        lines.append(f"| {model} | {cell(stats,'top1_hit')} | {cell(stats,'top3_hit')} | {cell(stats,'top5_hit')} | {cell(stats,'mrr')} | {cell(stats,'recall_at_1')} | {cell(stats,'recall_at_3')} | {cell(stats,'recall_at_5')} |")

    hv_contract = summary["models"].get("Current HyperVul", {}).get("contract_max_f1", {})
    hv_inter = summary["models"].get("Current HyperVul", {}).get("interaction_max_f1", {})
    lines += [
        "",
        "## Error Analysis",
        "",
        f"HyperVul error rows are in `reports/phase0d_hypervul_errors.csv` ({len(error_rows)} rows across seeds).",
        "",
        "## Final Recommendation",
        "",
        "- Clean baseline rerun is complete.",
        "- Contract-level metrics should be preferred for the redesigned task; compare the contract and interaction tables before claiming improvement.",
        "- Reentrancy-only remains the first main experiment candidate.",
        "- Phase 1 augmentation should wait until these results are reviewed and unchecked-call labels are manually audited.",
        "- Highest-priority next fix: adapt the training/evaluation pipeline natively to contract-level thresholding and top-k localization reporting.",
    ]
    (REPORTS / "phase0d_clean_baseline_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2)[:4000])
    print(f"Wrote Phase 0D reports to {REPORTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
