#!/usr/bin/env python3
"""Run independently tuned generic baselines and write a paste-ready summary."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch


def add_paths() -> None:
    here = Path(__file__).resolve().parent
    src = here.parents[0] / "src"
    for path in (here, src):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


add_paths()

from fair_eval.reporting import write_json_result, write_markdown_result  # noqa: E402
from fair_eval.training import (  # noqa: E402
    AsymmetricLoss,
    bce_with_logits_for_labels,
    binary_metrics,
    positive_weight,
    predict,
    select_threshold,
    set_global_seed,
    train_one_epoch,
)
from rq1_run_generic_baselines import MODEL_NAMES, build_loaders, make_model  # noqa: E402


DEFAULT_MODELS = (
    "function-mlp",
    "function-features-mlp",
    "sequence-bigru",
    "callgraph-gat",
    "pairwise-rgcn",
    "pairwise-gat",
)


def metric_cell(stats: dict[str, Any], metric: str) -> str:
    item = stats.get(metric)
    if not item:
        return "n/a"
    return f"{item['mean'] * 100:.2f} +/- {item['std'] * 100:.2f}"


def make_loss(name: str, labels: torch.Tensor, device: torch.device):
    if name == "bce":
        return bce_with_logits_for_labels(labels, device=device)
    if name == "asl":
        return AsymmetricLoss(pos_weight=positive_weight(labels).to(device))
    raise ValueError(name)


def run_one(
    project_root: Path,
    output_dir: Path,
    model_name: str,
    seed: int,
    max_epochs: int,
    batch_size: int,
    lr: float,
    dropout: float,
    loss_name: str,
    early_stop: bool,
    patience: int,
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
    loss_fn = make_loss(loss_name, loaders["train_labels"], device)

    history = []
    best_state = None
    best_val_loss = float("inf")
    epochs_without_improvement = 0
    for epoch in range(1, max_epochs + 1):
        train_result = train_one_epoch(model, loaders["train"], optimizer, loss_fn, step_fn, device, grad_clip=5.0)
        val_pred = predict(model, loaders["val"], step_fn, device)
        val_loss = float(loss_fn(torch.tensor(val_pred.logits, dtype=torch.float32, device=device), torch.tensor(val_pred.labels, dtype=torch.float32, device=device)).item())
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
                "val_loss": val_loss,
                "val_f1": val_metrics["f1"],
                "val_f2": val_metrics["f2"],
                "threshold": selection.threshold,
            }
        )
        if early_stop:
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                epochs_without_improvement = 0
                best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
            else:
                epochs_without_improvement += 1
                if epochs_without_improvement >= patience:
                    break

    if best_state is not None:
        model.load_state_dict({key: value.to(device) for key, value in best_state.items()})

    val_pred = predict(model, loaders["val"], step_fn, device)
    selection = select_threshold(
        val_pred.probs,
        val_pred.labels,
        policy=threshold_policy,
        target_recall=target_recall,
        target_precision=target_precision,
    )
    val_metrics = binary_metrics(val_pred.probs, val_pred.labels, selection.threshold)
    test_pred = predict(model, loaders["test"], step_fn, device)
    metrics = binary_metrics(test_pred.probs, test_pred.labels, selection.threshold)

    result = {
        "title": f"Strong Generic Baseline: {model_name}",
        "rq": "StrongBaselines",
        "model": model_name,
        "seed": seed,
        "device": str(device),
        "uses_hyperedge": False,
        "config": {
            "max_epochs": max_epochs,
            "epochs_ran": len(history),
            "batch_size": batch_size,
            "lr": lr,
            "dropout": dropout,
            "loss": loss_name,
            "early_stop": early_stop,
            "patience": patience,
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


def summarize(output_dir: Path, results: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for path in output_dir.glob("*_seed*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if item.get("rq") == "StrongBaselines" and "model" in item and "seed" in item:
            merged[(str(item["model"]), int(item["seed"]))] = item
    for result in results:
        merged[(str(result["model"]), int(result["seed"]))] = result

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in merged.values():
        grouped[str(result["model"])].append(result)

    summary: dict[str, Any] = {"models": {}, "results": list(merged.values())}
    for model_name, model_results in grouped.items():
        metrics = defaultdict(list)
        for result in model_results:
            for key, value in result["metrics"].items():
                if isinstance(value, (int, float)) and value is not None:
                    metrics[key].append(float(value))
        summary["models"][model_name] = {
            key: {"mean": float(np.mean(values)), "std": float(np.std(values)), "values": values}
            for key, values in metrics.items()
        }

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# Strong Generic Baseline Sweep",
        "",
        "All rows are generic non-hyperedge baselines. They are tuned independently but do not use HyperVul hyperedges.",
        "",
        "| Model | Uses Hyperedge | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    order = [name for name in DEFAULT_MODELS if name in summary["models"]] + [
        name for name in summary["models"] if name not in DEFAULT_MODELS
    ]
    for model_name in order:
        stats = summary["models"][model_name]
        lines.append(
            f"| {model_name} | No | {metric_cell(stats, 'precision')} | {metric_cell(stats, 'recall')} | "
            f"{metric_cell(stats, 'f1')} | {metric_cell(stats, 'f2')} | "
            f"{metric_cell(stats, 'pr_auc')} | {metric_cell(stats, 'roc_auc')} |"
        )
    lines += ["", "Paste this file back for review after the run completes.", ""]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs" / "strong_baselines")
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(DEFAULT_MODELS))
    parser.add_argument("--seeds", nargs="+", type=int, default=[42])
    parser.add_argument("--max-epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--loss", choices=["bce", "asl"], default="asl")
    parser.add_argument("--early-stop", action="store_true")
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--threshold-policy", choices=["target_recall", "target_precision", "max_f1", "max_f2"], default="max_f2")
    parser.add_argument("--target-recall", type=float, default=0.90)
    parser.add_argument("--target-precision", type=float, default=0.70)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for model_name in args.models:
        for seed in args.seeds:
            print(f"Running strong baseline {model_name} seed={seed}")
            result = run_one(
                project_root=args.project_root,
                output_dir=args.output_dir,
                model_name=model_name,
                seed=seed,
                max_epochs=args.max_epochs,
                batch_size=args.batch_size,
                lr=args.lr,
                dropout=args.dropout,
                loss_name=args.loss,
                early_stop=args.early_stop,
                patience=args.patience,
                threshold_policy=args.threshold_policy,
                target_recall=args.target_recall,
                target_precision=args.target_precision,
            )
            m = result["metrics"]
            print(f"  P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} F2={m['f2']:.3f}")
            results.append(result)
    summarize(args.output_dir, results)
    print(f"Wrote strong baseline summary to {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
