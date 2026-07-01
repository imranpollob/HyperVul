#!/usr/bin/env python3
"""Run the selected advanced HyperVul tool configuration across seeds."""

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


def metric_cell(stats: dict[str, Any], metric: str) -> str:
    item = stats.get(metric)
    if not item:
        return "n/a"
    return f"{item['mean'] * 100:.2f} +/- {item['std'] * 100:.2f}"


def summarize(output_dir: Path, results: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[int, dict[str, Any]] = {}
    for path in output_dir.glob("hypervul-tool_seed*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if "seed" in item and "metrics" in item:
            merged[int(item["seed"])] = item
    for result in results:
        merged[int(result["seed"])] = result

    metrics = defaultdict(list)
    for result in merged.values():
        for key, value in result["metrics"].items():
            if isinstance(value, (int, float)) and value is not None:
                metrics[key].append(float(value))
    summary = {
        "model": "HyperVul-Tool",
        "seeds": sorted(merged),
        "runs": list(merged.values()),
        "metrics": {
            key: {"mean": float(np.mean(values)), "std": float(np.std(values)), "values": values}
            for key, values in metrics.items()
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# HyperVul Tool Evaluation",
        "",
        "This table reports the selected advanced HyperVul typed-hyperedge tool configuration.",
        "",
        "| Model | Uses Hyperedge | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| HyperVul-Tool | Yes | {metric_cell(summary['metrics'], 'precision')} | "
            f"{metric_cell(summary['metrics'], 'recall')} | {metric_cell(summary['metrics'], 'f1')} | "
            f"{metric_cell(summary['metrics'], 'f2')} | {metric_cell(summary['metrics'], 'pr_auc')} | "
            f"{metric_cell(summary['metrics'], 'roc_auc')} |"
        ),
        "",
        "## Per-Seed Runs",
        "",
        "| Seed | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Threshold |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for seed in sorted(merged):
        result = merged[seed]
        m = result["metrics"]
        threshold = result["threshold_selection"]["threshold"]
        lines.append(
            f"| {seed} | {m['precision'] * 100:.2f} | {m['recall'] * 100:.2f} | "
            f"{m['f1'] * 100:.2f} | {m['f2'] * 100:.2f} | {m['pr_auc'] * 100:.2f} | "
            f"{m['roc_auc'] * 100:.2f} | {threshold:.4f} |"
        )
    lines += ["", "Paste this file back for review after the run completes.", ""]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs" / "tool_eval")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--max-epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--symbolic-mode", choices=["legacy8", "none", "security", "full"], default="full")
    parser.add_argument("--loss", choices=["bce", "asl"], default="asl")
    parser.add_argument("--scl-pretrain-epochs", type=int, default=15)
    parser.add_argument("--scl-lambda", type=float, default=0.5)
    parser.add_argument("--scl-hard-neg-weight", type=float, default=3.0)
    parser.add_argument("--early-stop", action="store_true")
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--threshold-policy", choices=["target_recall", "target_precision", "max_f1", "max_f2"], default="max_f2")
    parser.add_argument("--target-recall", type=float, default=0.90)
    parser.add_argument("--target-precision", type=float, default=0.70)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = args.output_dir / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for seed in args.seeds:
        print(f"Running HyperVul-Tool seed={seed}")
        result = run_one(
            project_root=args.project_root,
            output_dir=run_dir,
            model_name="full",
            seed=seed,
            epochs=args.max_epochs,
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
        result["model"] = "HyperVul-Tool"
        result["variant"] = "hypervul-tool"
        (args.output_dir / f"hypervul-tool_seed{seed}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append(result)
        m = result["metrics"]
        print(f"  P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} F2={m['f2']:.3f}")
    summarize(args.output_dir, results)
    print(f"Wrote HyperVul tool summary to {args.output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
