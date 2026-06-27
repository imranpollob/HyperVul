#!/usr/bin/env python3
"""Train baselines and HyperVul on positive-only augmented reentrancy data."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
AUG_GRAPH_DIR = ROOT / "data" / "reentrancy_positive_augmented_v1"
FAIR_SRC = ROOT / "hypervul_fair_eval" / "src"
if str(FAIR_SRC) not in sys.path:
    sys.path.insert(0, str(FAIR_SRC))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


phase0d = load_module("phase0d_aug", ROOT / "scripts" / "run_phase0d_clean_baselines.py")
phase0e = load_module("phase0e_aug", ROOT / "scripts" / "run_phase0e_native_contract_mil.py")
phase1a = load_module("phase1a_aug", ROOT / "scripts" / "run_phase1a_hard_negative_safety.py")
phase1b = load_module("phase1b_aug", ROOT / "scripts" / "run_phase1b_risk_safety_architecture.py")

from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.training import binary_metrics, select_threshold  # noqa: E402


BASELINE_MODELS = (
    "Function-MLP",
    "Function+Features MLP",
    "Sequence-BiGRU",
    "CallGraph-GAT",
    "Pairwise-RGCN",
    "Pairwise-GAT",
    "Current HyperVul",
)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def graph_counts(bundle) -> list[dict[str, Any]]:
    rows = []
    for split, graphs in bundle.graphs.items():
        pos_contracts = sum(int(graph.raw.get("contract_label", 0)) == 1 for graph in graphs)
        pos_int = sum(graph.positive_count for graph in graphs)
        neg_int = sum(graph.negative_count for graph in graphs)
        ignored = sum(len([n for n in graph.interaction_nodes if n.label is None]) for graph in graphs)
        rows.append(
            {
                "split": split,
                "contracts": len(graphs),
                "positive_contracts": pos_contracts,
                "negative_contracts": len(graphs) - pos_contracts,
                "positive_interactions": pos_int,
                "negative_interactions": neg_int,
                "ignored_interactions": ignored,
                "interaction_neg_pos_ratio": neg_int / max(pos_int, 1),
            }
        )
    return rows


def threshold_rows(val_probs, val_labels, test_probs, test_labels) -> list[dict[str, Any]]:
    policies = [
        ("max_f1", {"policy": "max_f1", "target_recall": 0.90, "target_precision": 0.80}),
        ("target_recall_90", {"policy": "target_recall", "target_recall": 0.90, "target_precision": 0.80}),
        ("target_precision_80", {"policy": "target_precision", "target_recall": 0.90, "target_precision": 0.80}),
    ]
    rows = []
    for name, cfg in policies:
        sel = select_threshold(
            val_probs,
            val_labels,
            policy=cfg["policy"],
            target_recall=cfg["target_recall"],
            target_precision=cfg["target_precision"],
        )
        row = dict(binary_metrics(test_probs, test_labels, sel.threshold))
        row.update(
            {
                "threshold_policy": name,
                "selection_policy": cfg["policy"],
                "threshold": sel.threshold,
                "validation_precision_at_threshold": sel.precision,
                "validation_recall_at_threshold": sel.recall,
            }
        )
        rows.append(row)
    oracle = select_threshold(test_probs, test_labels, policy="max_f1")
    row = dict(binary_metrics(test_probs, test_labels, oracle.threshold))
    row.update(
        {
            "threshold_policy": "test_oracle_max_f1",
            "selection_policy": "test_oracle",
            "threshold": oracle.threshold,
            "validation_precision_at_threshold": "",
            "validation_recall_at_threshold": "",
        }
    )
    rows.append(row)
    return rows


def add_baseline_result(result: dict[str, Any], data: dict[str, Any], metric_rows: list[dict[str, Any]], loc_rows: list[dict[str, Any]]) -> None:
    val_pred = result["predictions"]["val"]
    test_pred = result["predictions"]["test"]
    val_contract_probs, val_contract_labels, _ = phase0d.contract_scores(val_pred, data["contract_labels"])
    test_contract_probs, test_contract_labels, _ = phase0d.contract_scores(test_pred, data["contract_labels"])
    for row in threshold_rows(val_contract_probs, val_contract_labels, test_contract_probs, test_contract_labels):
        row.update({"model": result["model"], "variant": "augmented_data", "seed": result["seed"], "level": "contract"})
        metric_rows.append(row)
    loc = phase0d.localization_metrics(test_pred, data["graph_meta"])
    loc.update({"model": result["model"], "variant": "augmented_data", "seed": result["seed"]})
    loc_rows.append(loc)


def add_risk_safety_result(result: dict[str, Any], metric_rows: list[dict[str, Any]], loc_rows: list[dict[str, Any]]) -> None:
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]
    for row in threshold_rows(val["contract_probs"], val["contract_labels"], test["contract_probs"], test["contract_labels"]):
        row.update({"model": "HyperVul-RiskSafety", "variant": result["variant"], "seed": result["seed"], "level": "contract"})
        metric_rows.append(row)
    loc = phase0e.localization_metrics(test)
    loc.update({"model": "HyperVul-RiskSafety", "variant": result["variant"], "seed": result["seed"]})
    loc_rows.append(loc)


def summarize(rows: list[dict[str, Any]], keys: tuple[str, ...], metrics: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(k, "")) for k in keys)].append(row)
    out = []
    for key, vals in sorted(groups.items()):
        item = {k: v for k, v in zip(keys, key)}
        item["n"] = len(vals)
        for metric in metrics:
            xs = [float(row[metric]) for row in vals if row.get(metric) not in ("", None)]
            mean = float(np.mean(xs)) if xs else 0.0
            std = float(np.std(xs)) if xs else 0.0
            item[f"{metric}_mean"] = mean
            item[f"{metric}_std"] = std
            item[f"{metric}_fmt"] = f"{mean * 100:.2f} +/- {std * 100:.2f}"
        out.append(item)
    return out


def write_report(metric_summary: list[dict[str, Any]], loc_summary: list[dict[str, Any]], counts: list[dict[str, Any]]) -> None:
    lines = ["# Augmented Reentrancy Baseline Comparison", ""]
    lines.append("All rows are trained on `data/reentrancy_positive_augmented_v1`, which contains positive-only synthetic reentrancy clones in the train split. Val/test are not augmented.")
    lines.append("")
    lines.append("## Dataset Counts")
    lines.append("| Split | Contracts | Pos Contracts | Neg Contracts | Pos Int | Neg Int | Ignored | Neg:Pos Int |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in counts:
        lines.append(f"| {row['split']} | {row['contracts']} | {row['positive_contracts']} | {row['negative_contracts']} | {row['positive_interactions']} | {row['negative_interactions']} | {row['ignored_interactions']} | {float(row['interaction_neg_pos_ratio']):.2f} |")
    for policy, title in [
        ("max_f1", "Validation Max-F1 Threshold"),
        ("target_recall_90", "Validation Target Recall 90"),
        ("target_precision_80", "Validation Target Precision 80"),
        ("test_oracle_max_f1", "Test-Oracle Upper Bound"),
    ]:
        lines.append("")
        lines.append(f"## {title}")
        lines.append("| Model | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
        subset = [row for row in metric_summary if row["threshold_policy"] == policy]
        subset = sorted(subset, key=lambda r: float(r["f1_mean"]), reverse=True)
        for row in subset:
            lines.append(f"| {row['model']} | {row['variant']} | {row['n']} | {row['precision_fmt']} | {row['recall_fmt']} | {row['f1_fmt']} | {row['f2_fmt']} | {row['pr_auc_fmt']} | {row['roc_auc_fmt']} |")
    lines.append("")
    lines.append("## Localization")
    lines.append("| Model | Variant | Seeds | Top-1 | Top-3 | Top-5 | MRR | Recall@3 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in sorted(loc_summary, key=lambda r: float(r["mrr_mean"]), reverse=True):
        lines.append(f"| {row['model']} | {row['variant']} | {row['n']} | {row['top1_hit_fmt']} | {row['top3_hit_fmt']} | {row['top5_hit_fmt']} | {row['mrr_fmt']} | {row['recall_at_3_fmt']} |")
    lines.append("")
    lines.append("## Demo Table Shape")
    lines.append("The main paper table should use the `Validation Target Recall 90` block if recall is the priority, and the `Test-Oracle Upper Bound` block as the performance ceiling.")
    (REPORTS / "augmented_reentrancy_baseline_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--models", nargs="+", default=list(BASELINE_MODELS), choices=BASELINE_MODELS)
    parser.add_argument("--risk-safety-variants", nargs="+", default=["gated"], choices=("concat", "subtractive", "gated", "rule_suppression"))
    args = parser.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    os.environ["HYPERVUL_GRAPH_DIR"] = str(AUG_GRAPH_DIR.resolve())
    phase0d.GRAPH_DIR = AUG_GRAPH_DIR
    phase0e.GRAPH_DIR = AUG_GRAPH_DIR
    phase0e.SCOPE_DIR = AUG_GRAPH_DIR / "scope_views"
    phase1b.GRAPH_DIR = AUG_GRAPH_DIR
    data = phase0d.build_all_views(ROOT)
    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    safety = phase1a.SafetyFeatureStore(bundle)
    counts = graph_counts(bundle)
    print(f"Augmented reentrancy counts: {counts}", flush=True)

    metric_rows: list[dict[str, Any]] = []
    loc_rows: list[dict[str, Any]] = []
    for model in args.models:
        for seed in args.seeds:
            print(f"Running baseline {model} seed={seed} epochs={args.epochs}", flush=True)
            result = phase0d.train_predict_one(data, model, seed, args.epochs, args.batch_size, args.lr, args.dropout)
            add_baseline_result(result, data, metric_rows, loc_rows)
            print(f"  done {model} seed={seed}", flush=True)

    bags = phase0e.build_contract_bags(bundle)
    for variant in args.risk_safety_variants:
        for seed in args.seeds:
            print(f"Running HyperVul-RiskSafety {variant} seed={seed} epochs={args.epochs}", flush=True)
            result = phase1b.train_predict(
                bags,
                embeddings,
                safety,
                "reentrancy_augmented",
                variant,
                seed,
                args.epochs,
                args.batch_size,
                args.lr,
                args.dropout,
                0.5,
                0.2,
                "mil_attention",
            )
            add_risk_safety_result(result, metric_rows, loc_rows)
            print(f"  done HyperVul-RiskSafety {variant} seed={seed}", flush=True)

    metric_fields = [
        "model",
        "variant",
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
    ]
    loc_fields = ["model", "variant", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"]
    write_csv(REPORTS / "augmented_reentrancy_baseline_metrics_raw.csv", metric_rows, metric_fields)
    write_csv(REPORTS / "augmented_reentrancy_baseline_localization_raw.csv", loc_rows, loc_fields)
    metric_summary = summarize(metric_rows, ("model", "variant", "threshold_policy"), ("precision", "recall", "f1", "f2", "pr_auc", "roc_auc"))
    loc_summary = summarize(loc_rows, ("model", "variant"), ("top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"))
    summary_fields = ["model", "variant", "threshold_policy", "n", "precision_mean", "precision_std", "recall_mean", "recall_std", "f1_mean", "f1_std", "f2_mean", "f2_std", "pr_auc_mean", "pr_auc_std", "roc_auc_mean", "roc_auc_std", "precision_fmt", "recall_fmt", "f1_fmt", "f2_fmt", "pr_auc_fmt", "roc_auc_fmt"]
    loc_summary_fields = ["model", "variant", "n", "top1_hit_mean", "top1_hit_std", "top3_hit_mean", "top3_hit_std", "top5_hit_mean", "top5_hit_std", "mrr_mean", "mrr_std", "recall_at_1_mean", "recall_at_1_std", "recall_at_3_mean", "recall_at_3_std", "recall_at_5_mean", "recall_at_5_std", "top1_hit_fmt", "top3_hit_fmt", "top5_hit_fmt", "mrr_fmt", "recall_at_1_fmt", "recall_at_3_fmt", "recall_at_5_fmt"]
    write_csv(REPORTS / "augmented_reentrancy_baseline_summary.csv", metric_summary, summary_fields)
    write_csv(REPORTS / "augmented_reentrancy_baseline_localization_summary.csv", loc_summary, loc_summary_fields)
    write_csv(REPORTS / "augmented_reentrancy_dataset_counts.csv", counts, ["split", "contracts", "positive_contracts", "negative_contracts", "positive_interactions", "negative_interactions", "ignored_interactions", "interaction_neg_pos_ratio"])
    write_report(metric_summary, loc_summary, counts)
    print(f"Wrote augmented reentrancy baseline comparison to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
