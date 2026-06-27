#!/usr/bin/env python3
"""Run quick one-seed HyperVul variants and write a paste-ready summary."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


def add_paths() -> None:
    here = Path(__file__).resolve().parent
    src = here.parents[0] / "src"
    for path in (here, src):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


add_paths()

from rq3_run_hypervul_ablation import run_one  # noqa: E402


VARIANTS: dict[str, dict[str, Any]] = {
    "current-full": {
        "symbolic_mode": "legacy8",
        "loss": "bce",
        "scl_pretrain_epochs": 0,
        "scl_lambda": 0.2,
        "scl_hard_neg_weight": 1.0,
        "early_stop": False,
    },
    "symbolic-full": {
        "symbolic_mode": "full",
        "loss": "bce",
        "scl_pretrain_epochs": 0,
        "scl_lambda": 0.2,
        "scl_hard_neg_weight": 1.0,
        "early_stop": False,
    },
    "symbolic-asl": {
        "symbolic_mode": "full",
        "loss": "asl",
        "scl_pretrain_epochs": 0,
        "scl_lambda": 0.2,
        "scl_hard_neg_weight": 1.0,
        "early_stop": False,
    },
    "symbolic-asl-earlystop": {
        "symbolic_mode": "full",
        "loss": "asl",
        "scl_pretrain_epochs": 0,
        "scl_lambda": 0.2,
        "scl_hard_neg_weight": 1.0,
        "early_stop": True,
    },
    "symbolic-asl-scl": {
        "symbolic_mode": "full",
        "loss": "asl",
        "scl_pretrain_epochs": 15,
        "scl_lambda": 0.5,
        "scl_hard_neg_weight": 1.0,
        "early_stop": True,
    },
    "symbolic-asl-scl-hardneg": {
        "symbolic_mode": "full",
        "loss": "asl",
        "scl_pretrain_epochs": 15,
        "scl_lambda": 0.5,
        "scl_hard_neg_weight": 3.0,
        "early_stop": True,
    },
}


def cell(stats: dict[str, Any], metric: str) -> str:
    value = stats["metrics"].get(metric)
    return "n/a" if value is None else f"{float(value) * 100:.2f}"


def summarize(output_dir: Path, results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"variants": results}
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# HyperVul Quick Sweep",
        "",
        "All rows use the HyperVul typed hyperedge representation. This is a one-seed search for promising tool configurations.",
        "",
        "| Variant | Symbolic | Loss | Early Stop | SCL Pretrain | Hard Neg Weight | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Threshold |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        cfg = result["config"]
        threshold = result["threshold_selection"]["threshold"]
        lines.append(
            f"| {result['variant']} | {cfg['symbolic_mode']} | {cfg['loss']} | {cfg['early_stop']} | "
            f"{cfg['scl_pretrain_epochs']} | {cfg['scl_hard_neg_weight']} | "
            f"{cell(result, 'precision')} | {cell(result, 'recall')} | {cell(result, 'f1')} | "
            f"{cell(result, 'f2')} | {cell(result, 'pr_auc')} | {cell(result, 'roc_auc')} | {threshold:.4f} |"
        )
    if results:
        best_f2 = max(results, key=lambda item: item["metrics"].get("f2", 0.0))
        best_pr = max(results, key=lambda item: item["metrics"].get("pr_auc", 0.0))
        lines += [
            "",
            f"Best by F2: `{best_f2['variant']}` ({best_f2['metrics'].get('f2', 0.0) * 100:.2f}).",
            f"Best by PR-AUC: `{best_pr['variant']}` ({best_pr['metrics'].get('pr_auc', 0.0) * 100:.2f}).",
            "",
        ]
    lines.append("Paste this file back for review after the run completes.")
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs" / "quick_sweep")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--variants", nargs="+", choices=sorted(VARIANTS), default=list(VARIANTS))
    parser.add_argument("--max-epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--early-stop", action="store_true", help="Force early stopping on variants that support it.")
    parser.add_argument("--threshold-policy", choices=["target_recall", "target_precision", "max_f1", "max_f2"], default="max_f2")
    parser.add_argument("--target-recall", type=float, default=0.90)
    parser.add_argument("--target-precision", type=float, default=0.70)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for variant in args.variants:
        cfg = dict(VARIANTS[variant])
        if args.early_stop:
            cfg["early_stop"] = True
        variant_dir = args.output_dir / "runs"
        variant_dir.mkdir(parents=True, exist_ok=True)
        print(f"Running HyperVul quick variant {variant} seed={args.seed}")
        result = run_one(
            project_root=args.project_root,
            output_dir=variant_dir,
            model_name="full",
            seed=args.seed,
            epochs=args.max_epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            dropout=args.dropout,
            threshold_policy=args.threshold_policy,
            target_recall=args.target_recall,
            target_precision=args.target_precision,
            scl_lambda=cfg["scl_lambda"],
            symbolic_mode=cfg["symbolic_mode"],
            loss_name=cfg["loss"],
            early_stop=cfg["early_stop"],
            patience=args.patience,
            scl_pretrain_epochs=cfg["scl_pretrain_epochs"],
            scl_hard_neg_weight=cfg["scl_hard_neg_weight"],
        )
        result["variant"] = variant
        (variant_dir / f"{variant}_seed{args.seed}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append(result)
        m = result["metrics"]
        print(f"  P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} F2={m['f2']:.3f}")
    summarize(args.output_dir, results)
    print(f"Wrote quick-sweep summary to {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
