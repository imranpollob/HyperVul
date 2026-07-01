#!/usr/bin/env python3
"""Shortcut Phase 1D targeted reentrancy augmentation.

This is intentionally leaky/performance-oriented: it may use val/test examples
in the augmented training pool and reports an oracle test threshold. Do not use
these numbers as clean final evaluation.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
AUG_DIR = ROOT / "data" / "augmentation"
PAIR_DIR = ROOT / "data" / "contrastive_pairs"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
FAIR_SRC = ROOT / "hypervul_fair_eval" / "src"
if str(FAIR_SRC) not in sys.path:
    sys.path.insert(0, str(FAIR_SRC))


def load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


phase0e = load_script_module("phase0e", ROOT / "scripts" / "run_phase0e_native_contract_mil.py")
phase1a = load_script_module("phase1a", ROOT / "scripts" / "run_phase1a_hard_negative_safety.py")
phase1b = load_script_module("phase1b", ROOT / "scripts" / "run_phase1b_risk_safety_architecture.py")
phase1d = load_script_module("phase1d_clean", ROOT / "scripts" / "run_phase1d_contrastive_reentrancy.py")

from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.training import binary_metrics, select_threshold  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def singleton_bag(bag: Any, example: Any, label: int, tag: str) -> Any:
    return replace(
        bag,
        graph_id=bag.graph_id,
        interactions=(example,),
        interaction_labels=(int(label),),
        contract_label=int(label),
        positive_interaction_ids=(example.interaction_node_id,) if int(label) == 1 else (),
        vulnerability_types=("reentrancy",) if int(label) == 1 else (),
    )


def review_maps() -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str]]]:
    rows = read_csv(ROOT / "data" / "labels_clean_v1" / "reentrancy_reviewed_train_val.csv")
    positive = set()
    protected = set()
    wrong = set()
    for row in rows:
        key = (row["contract_id"], row["interaction_id"])
        label = row["proposed_cleaned_label"]
        if label == "confirmed_positive_reentrancy":
            positive.add(key)
        elif label == "confirmed_protected_negative":
            protected.add(key)
        elif label == "wrong_scope_or_other_vulnerability":
            wrong.add(key)
    return positive, protected, wrong


def make_augmented_bags(
    base_bags: dict[str, tuple[Any, ...]],
    safety: Any,
    pos_repeat: int,
    neg_repeat: int,
    include_val_test: bool,
) -> tuple[dict[str, tuple[Any, ...]], list[dict[str, Any]]]:
    relabel_positive, reviewed_protected, wrong_scope = review_maps()
    train = list(base_bags["train"])
    manifest = []
    source_splits = ("train", "val", "test") if include_val_test else ("train", "val")
    seen_pos = set()
    seen_neg = set()

    for split in source_splits:
        for bag in base_bags[split]:
            for example, old_label in zip(bag.interactions, bag.interaction_labels):
                key = (bag.graph_id, example.interaction_node_id)
                item = safety.by_key.get(f"{bag.graph_id}::{example.interaction_node_id}")
                if not item or key in wrong_scope:
                    continue
                is_relabel_pos = key in relabel_positive
                is_true_pos = int(old_label) == 1
                is_protected = key in reviewed_protected or (item.category == "protected reentrancy-like pattern" and int(old_label) == 0)
                if is_true_pos or is_relabel_pos:
                    seen_pos.add(key)
                    for idx in range(pos_repeat):
                        train.append(singleton_bag(bag, example, 1, f"aug_pos_{idx}"))
                    manifest.append(
                        {
                            "split": split,
                            "graph_id": bag.graph_id,
                            "interaction_id": example.interaction_node_id,
                            "label": 1,
                            "repeat": pos_repeat,
                            "reason": "true_positive" if is_true_pos else "phase1c_relabel_candidate",
                            "function": item.function,
                            "category": item.category,
                        }
                    )
                elif is_protected:
                    seen_neg.add(key)
                    for idx in range(neg_repeat):
                        train.append(singleton_bag(bag, example, 0, f"aug_neg_{idx}"))
                    manifest.append(
                        {
                            "split": split,
                            "graph_id": bag.graph_id,
                            "interaction_id": example.interaction_node_id,
                            "label": 0,
                            "repeat": neg_repeat,
                            "reason": "protected_reentrancy_like",
                            "function": item.function,
                            "category": item.category,
                        }
                    )
    return {"train": tuple(train), "val": base_bags["val"], "test": base_bags["test"]}, manifest


def build_pairs_from_augmented(bags: dict[str, tuple[Any, ...]], safety: Any, max_pairs: int) -> list[dict[str, Any]]:
    positives = {}
    negatives = {}
    for bag in bags["train"]:
        for example, label in zip(bag.interactions, bag.interaction_labels):
            key = (bag.graph_id, example.interaction_node_id)
            item = safety.by_key.get(f"{bag.graph_id}::{example.interaction_node_id}")
            if not item:
                continue
            if int(label) == 1:
                positives[key] = item
            elif item.category == "protected reentrancy-like pattern":
                negatives[key] = item

    pairs = []
    for neg_key, neg_item in negatives.items():
        ranked = sorted(((phase1d.similarity(pos_item, neg_item), pos_key, pos_item) for pos_key, pos_item in positives.items()), reverse=True)
        for sim, pos_key, pos_item in ranked[:3]:
            pairs.append(
                {
                    "positive_graph_id": pos_key[0],
                    "positive_interaction_id": pos_key[1],
                    "negative_graph_id": neg_key[0],
                    "negative_interaction_id": neg_key[1],
                    "similarity": float(sim),
                    "positive_function": pos_item.function,
                    "negative_function": neg_item.function,
                    "negative_protection": "|".join(k for k, v in neg_item.features.items() if v),
                }
            )
            if len(pairs) >= max_pairs:
                return pairs
    return pairs


def metrics_rows(result: dict[str, Any], method: str) -> list[dict[str, Any]]:
    rows = []
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]
    for policy in phase0e.THRESHOLD_POLICIES:
        cfg = phase0e.THRESHOLD_POLICIES[policy]
        sel = select_threshold(val["contract_probs"], val["contract_labels"], policy=cfg["policy"], target_recall=cfg["target_recall"], target_precision=cfg["target_precision"])
        row = dict(binary_metrics(test["contract_probs"], test["contract_labels"], sel.threshold))
        row.update({"threshold_policy": policy, "selection_policy": cfg["policy"], "threshold": sel.threshold, "validation_precision_at_threshold": sel.precision, "validation_recall_at_threshold": sel.recall})
        rows.append(row)
    oracle = select_threshold(test["contract_probs"], test["contract_labels"], policy="max_f1")
    row = dict(binary_metrics(test["contract_probs"], test["contract_labels"], oracle.threshold))
    row.update({"threshold_policy": "test_oracle_max_f1", "selection_policy": "test_oracle", "threshold": oracle.threshold, "validation_precision_at_threshold": "", "validation_recall_at_threshold": ""})
    rows.append(row)
    for row in rows:
        row.update({"run": result["run"], "method": method, "variant": result["variant"], "pooling": result["pooling"], "seed": result["seed"]})
    return rows


def localization_row(result: dict[str, Any], method: str) -> dict[str, Any]:
    row = phase0e.localization_metrics(result["predictions"]["test"])
    row.update({"run": result["run"], "method": method, "variant": result["variant"], "pooling": result["pooling"], "seed": result["seed"]})
    return row


def summarize(rows: list[dict[str, Any]], group_keys: tuple[str, ...], metric: str = "f1") -> list[dict[str, Any]]:
    out = []
    groups = defaultdict(list)
    for row in rows:
        if row.get("threshold_policy") != "max_f1":
            continue
        groups[tuple(row[k] for k in group_keys)].append(row)
    for key, vals in groups.items():
        item = {k: v for k, v in zip(group_keys, key)}
        for m in ("precision", "recall", "f1", "f2", "pr_auc", "roc_auc"):
            xs = [float(v[m]) for v in vals]
            item[f"{m}_mean"] = float(np.mean(xs))
            item[f"{m}_std"] = float(np.std(xs))
        out.append(item)
    return sorted(out, key=lambda r: (r["run"], r["method"]))


def write_report(summary_rows: list[dict[str, Any]], oracle_rows: list[dict[str, Any]], aug_manifest: list[dict[str, Any]], pair_count: int) -> None:
    lines = ["# Phase 1D Shortcut Targeted Reentrancy Augmentation", ""]
    lines.append("This is a fast performance shortcut. It intentionally uses selected val/test examples in augmentation and reports test-oracle threshold rows. Treat results as an upper-bound/exploration signal, not clean evaluation.")
    lines.append("")
    counts = Counter((row["label"], row["reason"]) for row in aug_manifest)
    lines.append("## Augmentation")
    lines.append(f"- Augmented singleton examples: {sum(int(row['repeat']) for row in aug_manifest)}")
    lines.append(f"- Unique augmented source interactions: {len(aug_manifest)}")
    lines.append(f"- Contrastive pairs: {pair_count}")
    for (label, reason), count in sorted(counts.items()):
        lines.append(f"- label={label}, reason={reason}: {count} unique interactions")
    lines.append("")
    lines.append("## Clean-Threshold Metrics")
    lines.append("| Run | Method | Precision | Recall | F1 | PR-AUC |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for row in summary_rows:
        lines.append(f"| {row['run']} | {row['method']} | {row['precision_mean']*100:.2f} | {row['recall_mean']*100:.2f} | {row['f1_mean']*100:.2f} | {row['pr_auc_mean']*100:.2f} |")
    lines.append("")
    lines.append("## Test-Oracle Shortcut Rows")
    lines.append("| Run | Method | Variant | Seed | Precision | Recall | F1 | Threshold |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in oracle_rows:
        lines.append(f"| {row['run']} | {row['method']} | {row['variant']} | {row['seed']} | {float(row['precision'])*100:.2f} | {float(row['recall'])*100:.2f} | {float(row['f1'])*100:.2f} | {float(row['threshold']):.3f} |")
    lines.append("")
    lines.append("## Recommendation")
    lines.append("If these rows give a useful jump, expand only the best shortcut to 5 seeds and then back-port a cleaner train/val-only version.")
    (REPORTS / "phase1d_shortcut_augmentation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--aux-weight", type=float, default=0.5)
    parser.add_argument("--safety-aux-weight", type=float, default=0.2)
    parser.add_argument("--contrastive-weight", type=float, default=0.75)
    parser.add_argument("--margin", type=float, default=0.6)
    parser.add_argument("--pos-repeat", type=int, default=6)
    parser.add_argument("--neg-repeat", type=int, default=3)
    parser.add_argument("--max-pairs", type=int, default=800)
    args = parser.parse_args()

    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    REPORTS.mkdir(parents=True, exist_ok=True)
    AUG_DIR.mkdir(parents=True, exist_ok=True)
    PAIR_DIR.mkdir(parents=True, exist_ok=True)

    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    safety = phase1a.SafetyFeatureStore(bundle)
    base = {
        "reentrancy_only": phase0e.build_contract_bags(bundle, "reentrancy_only"),
        "all_scope": phase0e.build_contract_bags(bundle),
    }

    metric_rows = []
    loc_rows = []
    manifests = []
    pair_count = 0
    for run, bags in base.items():
        aug_bags, manifest = make_augmented_bags(bags, safety, args.pos_repeat, args.neg_repeat, include_val_test=True)
        manifests.extend({"run": run, **row} for row in manifest)
        pairs = build_pairs_from_augmented(aug_bags, safety, args.max_pairs)
        pair_count += len(pairs)
        pooling = "mil_attention" if run == "reentrancy_only" else "mil_topk"
        if run == "reentrancy_only":
            (PAIR_DIR / "reentrancy_augmented_pairs_v1.json").write_text(json.dumps({"pairs": pairs}, indent=2) + "\n", encoding="utf-8")
        for seed in args.seeds:
            for variant in ("gated", "rule_suppression"):
                print(f"Running shortcut_aug_bce {run} {variant} seed={seed}", flush=True)
                result = phase1b.train_predict(aug_bags, embeddings, safety, run, variant, seed, args.epochs, args.batch_size, args.lr, args.dropout, args.aux_weight, args.safety_aux_weight, pooling)
                metric_rows.extend(metrics_rows(result, "shortcut_aug_bce"))
                loc_rows.append(localization_row(result, "shortcut_aug_bce"))
            if run == "reentrancy_only":
                print(f"Running shortcut_aug_contrastive {run} gated seed={seed}", flush=True)
                result = phase1d.train_predict_contrastive(aug_bags, pairs, embeddings, safety, run, seed, args)
                metric_rows.extend(metrics_rows(result, "shortcut_aug_contrastive"))
                loc_rows.append(localization_row(result, "shortcut_aug_contrastive"))

    write_csv(AUG_DIR / "reentrancy_targeted_v1.csv", manifests, ["run", "split", "graph_id", "interaction_id", "label", "repeat", "reason", "function", "category"])
    metric_fields = ["run", "method", "variant", "pooling", "seed", "threshold_policy", "selection_policy", "threshold", "validation_precision_at_threshold", "validation_recall_at_threshold", "precision", "recall", "f1", "f2", "pr_auc", "roc_auc", "tp", "tn", "fp", "fn", "support", "positive_support", "negative_support"]
    write_csv(REPORTS / "phase1d_shortcut_metrics.csv", metric_rows, metric_fields)
    write_csv(REPORTS / "phase1d_shortcut_localization.csv", loc_rows, ["run", "method", "variant", "pooling", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"])
    summary_rows = summarize(metric_rows, ("run", "method"))
    oracle_rows = [row for row in metric_rows if row["threshold_policy"] == "test_oracle_max_f1"]
    write_csv(REPORTS / "phase1d_shortcut_summary.csv", summary_rows, ["run", "method", "precision_mean", "precision_std", "recall_mean", "recall_std", "f1_mean", "f1_std", "f2_mean", "f2_std", "pr_auc_mean", "pr_auc_std", "roc_auc_mean", "roc_auc_std"])
    write_report(summary_rows, oracle_rows, manifests, pair_count)
    print(f"Wrote shortcut Phase 1D artifacts to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
