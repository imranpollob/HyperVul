#!/usr/bin/env python3
"""Run RQ3 HyperVul component ablation."""

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

from fair_eval.builders.hyperedge_view import build_hyperedge_examples  # noqa: E402
from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.features.symbolic import SYMBOLIC_DIM  # noqa: E402
from fair_eval.models import HyperVulModel  # noqa: E402
from fair_eval.reporting import write_json_result, write_markdown_result  # noqa: E402
from fair_eval.training import (  # noqa: E402
    HyperVulTensorDataset,
    ProjectionHead,
    SupConLoss,
    AsymmetricLoss,
    bce_with_logits_for_labels,
    positive_weight,
    binary_metrics,
    collate_hypervul,
    hypervul_step_fn,
    predict,
    select_threshold,
    set_global_seed,
    train_one_epoch,
)


MODEL_NAMES = ("emb-only", "security", "full", "no-localize", "no-contrastive")


def variant_config(model_name: str) -> dict[str, Any]:
    if model_name == "emb-only":
        return {"use_symbolic": False, "use_localization": True, "use_contrastive": True}
    if model_name == "security":
        return {"use_symbolic": True, "use_localization": True, "use_contrastive": True}
    if model_name == "full":
        return {"use_symbolic": True, "use_localization": True, "use_contrastive": True}
    if model_name == "no-localize":
        return {"use_symbolic": True, "use_localization": False, "use_contrastive": True}
    if model_name == "no-contrastive":
        return {"use_symbolic": True, "use_localization": True, "use_contrastive": False}
    raise ValueError(model_name)


def build_loaders(project_root: Path, batch_size: int, symbolic_mode: str = "legacy8"):
    bundle = load_dataset_bundle(project_root)
    embeddings = EmbeddingStore(project_root)
    examples = {split: build_hyperedge_examples(graphs) for split, graphs in bundle.graphs.items()}
    datasets = {
        split: HyperVulTensorDataset(split_examples, embeddings, symbolic_mode=symbolic_mode)
        for split, split_examples in examples.items()
    }
    return {
        "train": DataLoader(datasets["train"], batch_size=batch_size, shuffle=True, collate_fn=collate_hypervul),
        "val": DataLoader(datasets["val"], batch_size=batch_size, shuffle=False, collate_fn=collate_hypervul),
        "test": DataLoader(datasets["test"], batch_size=batch_size, shuffle=False, collate_fn=collate_hypervul),
        "train_labels": torch.tensor([example.label for example in examples["train"]], dtype=torch.float32),
        "counts": {
            split: {
                "examples": len(split_examples),
                "positive": sum(1 for example in split_examples if example.label == 1),
                "negative": sum(1 for example in split_examples if example.label == 0),
            }
            for split, split_examples in examples.items()
        },
    }


def train_one_epoch_contrastive(
    model,
    projector,
    supcon,
    dataloader,
    optimizer,
    loss_fn,
    device,
    scl_lambda: float,
    hard_neg_weight: float,
):
    model.train()
    projector.train()
    total_loss = 0.0
    total_examples = 0
    for batch in dataloader:
        (
            members,
            member_mask,
            symbolic,
            state_embeddings,
            callee_embeddings,
            state_symbolic,
            callee_symbolic,
            state_mask,
            callee_mask,
            labels,
        ) = batch
        members = members.to(device)
        member_mask = member_mask.to(device)
        symbolic = symbolic.to(device)
        state_embeddings = state_embeddings.to(device)
        callee_embeddings = callee_embeddings.to(device)
        state_symbolic = state_symbolic.to(device)
        callee_symbolic = callee_symbolic.to(device)
        state_mask = state_mask.to(device)
        callee_mask = callee_mask.to(device)
        labels = labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits, pooled = model(
            members,
            member_mask,
            symbolic_features=symbolic,
            state_embeddings=state_embeddings,
            callee_embeddings=callee_embeddings,
            state_symbolic=state_symbolic,
            callee_symbolic=callee_symbolic,
            state_mask=state_mask,
            callee_mask=callee_mask,
            return_representation=True,
        )
        ce_loss = loss_fn(logits, labels)
        has_external = callee_mask.any(dim=1).to(device)
        weights = torch.where((labels == 0) & has_external, torch.full_like(labels, hard_neg_weight), torch.ones_like(labels))
        scl_loss = supcon(projector(pooled), labels, weights=weights)
        loss = ce_loss + scl_lambda * scl_loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(list(model.parameters()) + list(projector.parameters()), 5.0)
        optimizer.step()
        n = int(labels.numel())
        total_loss += float(loss.item()) * n
        total_examples += n
    return {"loss": total_loss / max(total_examples, 1), "examples": total_examples}


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
    scl_lambda: float,
    symbolic_mode: str = "legacy8",
    loss_name: str = "bce",
    early_stop: bool = False,
    patience: int = 20,
    scl_pretrain_epochs: int = 0,
    scl_hard_neg_weight: float = 1.0,
) -> dict[str, Any]:
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = variant_config(model_name)
    effective_symbolic_mode = symbolic_mode
    if symbolic_mode != "legacy8":
        if model_name == "emb-only":
            effective_symbolic_mode = "none"
        elif model_name == "security":
            effective_symbolic_mode = "security"
        else:
            effective_symbolic_mode = symbolic_mode
    loaders = build_loaders(project_root, batch_size, symbolic_mode=effective_symbolic_mode)
    symbolic_dim = 8 if effective_symbolic_mode == "legacy8" else SYMBOLIC_DIM
    model = HyperVulModel(
        symbolic_dim=symbolic_dim,
        dropout=dropout,
        use_symbolic=cfg["use_symbolic"],
        use_localization=cfg["use_localization"],
        use_sequence_pool=True,
    ).to(device)
    projector = ProjectionHead(model.input_dim).to(device) if cfg["use_contrastive"] else None
    supcon = SupConLoss().to(device) if cfg["use_contrastive"] else None
    params = list(model.parameters()) + (list(projector.parameters()) if projector is not None else [])
    optimizer = torch.optim.Adam(params, lr=lr, weight_decay=1e-5)
    if loss_name == "bce":
        loss_fn = bce_with_logits_for_labels(loaders["train_labels"], device=device)
    elif loss_name == "asl":
        loss_fn = AsymmetricLoss(pos_weight=positive_weight(loaders["train_labels"]).to(device))
    else:
        raise ValueError(f"Unknown loss: {loss_name}")

    history = []
    best_state = None
    best_val_loss = float("inf")
    epochs_without_improvement = 0
    if cfg["use_contrastive"] and scl_pretrain_epochs > 0:
        for _epoch in range(1, scl_pretrain_epochs + 1):
            train_one_epoch_contrastive(
                model,
                projector,
                supcon,
                loaders["train"],
                optimizer,
                loss_fn,
                device,
                scl_lambda=1.0,
                hard_neg_weight=scl_hard_neg_weight,
            )

    for epoch in range(1, epochs + 1):
        if cfg["use_contrastive"]:
            train_result = train_one_epoch_contrastive(
                model,
                projector,
                supcon,
                loaders["train"],
                optimizer,
                loss_fn,
                device,
                scl_lambda=scl_lambda,
                hard_neg_weight=scl_hard_neg_weight,
            )
            train_loss = train_result["loss"]
        else:
            train_result = train_one_epoch(model, loaders["train"], optimizer, loss_fn, hypervul_step_fn, device, grad_clip=5.0)
            train_loss = train_result.loss

        val_pred = predict(model, loaders["val"], hypervul_step_fn, device)
        val_logits = torch.tensor(val_pred.logits, dtype=torch.float32, device=device)
        val_labels = torch.tensor(val_pred.labels, dtype=torch.float32, device=device)
        val_loss = float(loss_fn(val_logits, val_labels).item()) if len(val_pred.labels) else 0.0
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
                "train_loss": train_loss,
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

    val_pred = predict(model, loaders["val"], hypervul_step_fn, device)
    selection = select_threshold(
        val_pred.probs,
        val_pred.labels,
        policy=threshold_policy,
        target_recall=target_recall,
        target_precision=target_precision,
    )
    test_pred = predict(model, loaders["test"], hypervul_step_fn, device)
    metrics = binary_metrics(test_pred.probs, test_pred.labels, selection.threshold)
    val_metrics = binary_metrics(val_pred.probs, val_pred.labels, selection.threshold)

    result = {
        "title": f"RQ3 HyperVul Ablation: {model_name}",
        "rq": "RQ3",
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
            "scl_lambda": scl_lambda,
            "scl_pretrain_epochs": scl_pretrain_epochs,
            "scl_hard_neg_weight": scl_hard_neg_weight,
            "symbolic_mode": effective_symbolic_mode,
            "symbolic_dim": symbolic_dim,
            "loss": loss_name,
            "early_stop": early_stop,
            "patience": patience,
            **cfg,
        },
        "data_note": (
            "Canonical contract_graphs provide an 8-d per-interaction security context. "
            "The security and full variants both consume this available context; wider old-style "
            "symbolic sidecars are outside this canonical graph view."
        ),
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

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in merged.values():
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

    (output_dir / "rq3_hypervul_ablation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# RQ3 HyperVul Component Ablation Summary", ""]
    lines.append(
        "Note: `security` and `full` both use the canonical 8-d security context available in `data/contract_graphs`."
    )
    lines.append("")
    lines.append("| Variant | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
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
    (output_dir / "rq3_hypervul_ablation_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs" / "rq3")
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(MODEL_NAMES))
    parser.add_argument("--seeds", nargs="+", type=int, default=[42])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--threshold-policy", choices=["target_recall", "target_precision", "max_f1", "max_f2"], default="max_f2")
    parser.add_argument("--target-recall", type=float, default=0.90)
    parser.add_argument("--target-precision", type=float, default=0.70)
    parser.add_argument("--scl-lambda", type=float, default=0.2)
    parser.add_argument("--scl-pretrain-epochs", type=int, default=0)
    parser.add_argument("--scl-hard-neg-weight", type=float, default=1.0)
    parser.add_argument("--symbolic-mode", choices=["legacy8", "none", "security", "full"], default="legacy8")
    parser.add_argument("--loss", choices=["bce", "asl"], default="bce")
    parser.add_argument("--early-stop", action="store_true")
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.summarize_only:
        summarize([], args.output_dir)
        print(f"Wrote RQ3 summary to {args.output_dir}")
        return

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
                scl_lambda=args.scl_lambda,
                symbolic_mode=args.symbolic_mode,
                loss_name=args.loss,
                early_stop=args.early_stop,
                patience=args.patience,
                scl_pretrain_epochs=args.scl_pretrain_epochs,
                scl_hard_neg_weight=args.scl_hard_neg_weight,
            )
            metrics = result["metrics"]
            print(
                f"  P={metrics['precision']:.3f} R={metrics['recall']:.3f} "
                f"F1={metrics['f1']:.3f} F2={metrics['f2']:.3f}"
            )
            results.append(result)
    summarize(results, args.output_dir)
    print(f"Wrote RQ3 outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
