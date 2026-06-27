#!/usr/bin/env python3
"""Run RQ1 generic baselines that do not use HyperVul hyperedges.

Implemented baselines:

* function-mlp
* function-features-mlp
* sequence
* callgraph-gcn
* pairwise-gcn
* pairwise-gat
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader


def add_src_to_path() -> None:
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


add_src_to_path()

from fair_eval.builders import (  # noqa: E402
    build_callgraph_views,
    build_function_examples,
    build_pairwise_graph_views,
    build_sequence_examples,
)
from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.models import FunctionFeaturesMLP, FunctionMLP, FunctionSequenceModel, GraphNodeClassifier  # noqa: E402
from fair_eval.reporting import write_json_result, write_markdown_result  # noqa: E402
from fair_eval.training import (  # noqa: E402
    FunctionTensorDataset,
    GraphTensorDataset,
    SCALAR_FEATURE_KEYS,
    SequenceTensorDataset,
    bce_with_logits_for_labels,
    binary_metrics,
    collate_graphs,
    collate_sequences,
    function_features_step_fn,
    function_step_fn,
    graph_step_fn,
    predict,
    scalar_standardizer,
    sequence_step_fn,
    select_threshold,
    set_global_seed,
    train_one_epoch,
)


MODEL_NAMES = (
    "function-mlp",
    "function-features-mlp",
    "sequence",
    "sequence-bigru",
    "callgraph-gcn",
    "callgraph-gat",
    "pairwise-gcn",
    "pairwise-rgcn",
    "pairwise-gat",
)


def build_loaders(project_root: Path, batch_size: int, model_name: str):
    bundle = load_dataset_bundle(project_root)
    embeddings = EmbeddingStore(project_root)
    function_examples = {split: build_function_examples(graphs) for split, graphs in bundle.graphs.items()}
    scalar_mean, scalar_std = scalar_standardizer(function_examples["train"])

    if model_name in {"function-mlp", "function-features-mlp"}:
        use_scalars = model_name == "function-features-mlp"
        train_data = FunctionTensorDataset(
            function_examples["train"],
            embeddings,
            scalar_mean=scalar_mean if use_scalars else None,
            scalar_std=scalar_std if use_scalars else None,
        )
        val_data = FunctionTensorDataset(
            function_examples["val"],
            embeddings,
            scalar_mean=scalar_mean if use_scalars else None,
            scalar_std=scalar_std if use_scalars else None,
        )
        test_data = FunctionTensorDataset(
            function_examples["test"],
            embeddings,
            scalar_mean=scalar_mean if use_scalars else None,
            scalar_std=scalar_std if use_scalars else None,
        )
        collate_fn = None
    elif model_name in {"sequence", "sequence-bigru"}:
        sequences = {split: build_sequence_examples(graphs) for split, graphs in bundle.graphs.items()}
        train_data = SequenceTensorDataset(sequences["train"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        val_data = SequenceTensorDataset(sequences["val"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        test_data = SequenceTensorDataset(sequences["test"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        collate_fn = collate_sequences
    elif model_name in {"callgraph-gcn", "callgraph-gat"}:
        views = {split: build_callgraph_views(graphs) for split, graphs in bundle.graphs.items()}
        train_data = GraphTensorDataset(views["train"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        val_data = GraphTensorDataset(views["val"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        test_data = GraphTensorDataset(views["test"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        collate_fn = collate_graphs
    elif model_name in {"pairwise-gcn", "pairwise-rgcn", "pairwise-gat"}:
        views = {split: build_pairwise_graph_views(graphs) for split, graphs in bundle.graphs.items()}
        train_data = GraphTensorDataset(views["train"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        val_data = GraphTensorDataset(views["val"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        test_data = GraphTensorDataset(views["test"], embeddings, scalar_mean=scalar_mean, scalar_std=scalar_std)
        collate_fn = collate_graphs
    else:
        raise ValueError(model_name)

    return {
        "train": DataLoader(train_data, batch_size=batch_size, shuffle=True, collate_fn=collate_fn),
        "val": DataLoader(val_data, batch_size=batch_size, shuffle=False, collate_fn=collate_fn),
        "test": DataLoader(test_data, batch_size=batch_size, shuffle=False, collate_fn=collate_fn),
        "train_labels": torch.tensor([example.label for example in function_examples["train"]], dtype=torch.float32),
        "counts": {
            split: {
                "examples": len(split_examples),
                "positive": sum(1 for example in split_examples if example.label == 1),
                "negative": sum(1 for example in split_examples if example.label == 0),
            }
            for split, split_examples in function_examples.items()
        },
    }


def make_model(model_name: str, dropout: float):
    if model_name == "function-mlp":
        return FunctionMLP(dropout=dropout), function_step_fn
    if model_name == "function-features-mlp":
        return FunctionFeaturesMLP(dropout=dropout), function_features_step_fn
    if model_name in {"sequence", "sequence-bigru"}:
        return FunctionSequenceModel(scalar_dim=len(SCALAR_FEATURE_KEYS), dropout=dropout), sequence_step_fn
    if model_name == "callgraph-gcn":
        return GraphNodeClassifier(scalar_dim=len(SCALAR_FEATURE_KEYS), conv="gcn", dropout=dropout), graph_step_fn
    if model_name == "callgraph-gat":
        return GraphNodeClassifier(scalar_dim=len(SCALAR_FEATURE_KEYS), conv="gat", dropout=dropout), graph_step_fn
    if model_name == "pairwise-gcn":
        return GraphNodeClassifier(
            scalar_dim=len(SCALAR_FEATURE_KEYS),
            conv="rgcn",
            edge_types=3,
            dropout=dropout,
        ), graph_step_fn
    if model_name == "pairwise-rgcn":
        return GraphNodeClassifier(
            scalar_dim=len(SCALAR_FEATURE_KEYS),
            conv="rgcn",
            edge_types=3,
            dropout=dropout,
        ), graph_step_fn
    if model_name == "pairwise-gat":
        return GraphNodeClassifier(scalar_dim=len(SCALAR_FEATURE_KEYS), conv="gat", dropout=dropout), graph_step_fn
    raise ValueError(model_name)


def run_one(
    project_root: Path,
    output_dir: Path,
    model_name: str,
    seed: int,
    epochs: int,
    batch_size: int,
    lr: float,
    dropout: float,
    threshold_policy: str,
    target_recall: float,
    target_precision: float,
) -> dict[str, Any]:
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loaders = build_loaders(project_root, batch_size, model_name)
    model, step_fn = make_model(model_name, dropout=dropout)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    loss_fn = bce_with_logits_for_labels(loaders["train_labels"], device=device)

    history = []
    for epoch in range(1, epochs + 1):
        train_result = train_one_epoch(
            model,
            loaders["train"],
            optimizer,
            loss_fn,
            step_fn,
            device,
            grad_clip=5.0,
        )
        val_pred = predict(model, loaders["val"], step_fn, device)
        selection = select_threshold(
            val_pred.probs,
            val_pred.labels,
            policy=threshold_policy,
            target_recall=target_recall,
            target_precision=target_precision,
        )
        val_metrics = binary_metrics(val_pred.probs, val_pred.labels, selection.threshold)
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_result.loss,
                "val_f1": val_metrics["f1"],
                "val_f2": val_metrics["f2"],
                "threshold": selection.threshold,
            }
        )

    val_pred = predict(model, loaders["val"], step_fn, device)
    selection = select_threshold(
        val_pred.probs,
        val_pred.labels,
        policy=threshold_policy,
        target_recall=target_recall,
        target_precision=target_precision,
    )
    test_pred = predict(model, loaders["test"], step_fn, device)
    metrics = binary_metrics(test_pred.probs, test_pred.labels, selection.threshold)
    val_metrics = binary_metrics(val_pred.probs, val_pred.labels, selection.threshold)

    result = {
        "title": f"RQ1 Generic Baseline: {model_name}",
        "rq": "RQ1",
        "model": model_name,
        "seed": seed,
        "device": str(device),
        "config": {
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "dropout": dropout,
            "threshold_policy": threshold_policy,
            "target_recall": target_recall,
            "target_precision": target_precision,
        },
        "counts": loaders["counts"],
        "threshold_selection": selection.__dict__,
        "validation_metrics": val_metrics,
        "metrics": metrics,
        "history": history,
    }

    stem = f"{model_name}_seed{seed}"
    write_json_result(result, output_dir / f"{stem}.json")
    write_markdown_result(result, output_dir / f"{stem}.md")
    return result


def summarize(results: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for path in output_dir.glob("*_seed*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if "model" in item and "seed" in item and "metrics" in item:
            merged[(str(item["model"]), int(item["seed"]))] = item
    for result in results:
        merged[(str(result["model"]), int(result["seed"]))] = result
    results = list(merged.values())

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[result["model"]].append(result)

    summary: dict[str, Any] = {"models": {}}
    for model_name, model_results in grouped.items():
        metrics = defaultdict(list)
        for result in model_results:
            for key, value in result["metrics"].items():
                if isinstance(value, (int, float)) and value is not None:
                    metrics[key].append(float(value))
        summary["models"][model_name] = {
            key: {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "values": values,
            }
            for key, values in metrics.items()
        }

    out = output_dir / "rq1_generic_baselines_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = ["# RQ1 Generic Baseline Summary", ""]
    lines.append("| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for model_name, stats in summary["models"].items():
        def cell(metric: str) -> str:
            item = stats.get(metric)
            if not item:
                return "n/a"
            return f"{item['mean'] * 100:.2f} +/- {item['std'] * 100:.2f}"

        lines.append(
            f"| {model_name} | {cell('precision')} | {cell('recall')} | {cell('f1')} | "
            f"{cell('f2')} | {cell('pr_auc')} | {cell('roc_auc')} |"
        )
    (output_dir / "rq1_generic_baselines_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs" / "rq1")
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(MODEL_NAMES))
    parser.add_argument("--seeds", nargs="+", type=int, default=[42])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--threshold-policy", choices=["target_recall", "target_precision", "max_f1", "max_f2"], default="target_recall")
    parser.add_argument("--target-recall", type=float, default=0.90)
    parser.add_argument("--target-precision", type=float, default=0.70)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for model_name in args.models:
        for seed in args.seeds:
            print(f"Running {model_name} seed={seed}")
            result = run_one(
                project_root=args.project_root,
                output_dir=args.output_dir,
                model_name=model_name,
                seed=seed,
                epochs=args.epochs,
                batch_size=args.batch_size,
                lr=args.lr,
                dropout=args.dropout,
                threshold_policy=args.threshold_policy,
                target_recall=args.target_recall,
                target_precision=args.target_precision,
            )
            metrics = result["metrics"]
            print(
                f"  P={metrics['precision']:.3f} R={metrics['recall']:.3f} "
                f"F1={metrics['f1']:.3f} F2={metrics['f2']:.3f}"
            )
            results.append(result)
    summarize(results, args.output_dir)
    print(f"Wrote RQ1 outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
