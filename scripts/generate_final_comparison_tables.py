#!/usr/bin/env python3
"""Generate final comparison tables for HyperVul experiments.

By default this script reuses existing report CSVs. Use --run-clean-baselines or
--run-shortcut to retrain before table generation.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def run_cmd(args: list[str]) -> None:
    print("Running:", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    arr = np.asarray(values, dtype=float)
    return float(arr.mean()), float(arr.std())


def fmt_pct(mean: float, std: float) -> str:
    return f"{mean * 100:.2f} +/- {std * 100:.2f}"


def group_stats(rows: list[dict[str, Any]], group_fields: tuple[str, ...], metrics: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(row.get(field, "")) for field in group_fields)].append(row)
    out = []
    for key, vals in sorted(groups.items()):
        item = {field: value for field, value in zip(group_fields, key)}
        item["n"] = len(vals)
        for metric in metrics:
            nums = [float(row[metric]) for row in vals if row.get(metric) not in ("", None)]
            mean, std = mean_std(nums)
            item[f"{metric}_mean"] = mean
            item[f"{metric}_std"] = std
            item[f"{metric}_fmt"] = fmt_pct(mean, std)
        out.append(item)
    return out


def clean_baseline_contract_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(REPORTS / "phase0d_contract_metrics.csv"):
        if row.get("threshold_policy") != "max_f1":
            continue
        rows.append(
            {
                "scope": "all_scope",
                "method": row["model"],
                "variant": "clean_phase0d",
                "seed": row["seed"],
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
                "f2": row["f2"],
                "pr_auc": row["pr_auc"],
                "roc_auc": row["roc_auc"],
                "evaluation": "validation_threshold",
                "notes": "clean_split_baseline",
            }
        )
    return rows


def clean_baseline_localization_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(REPORTS / "phase0d_localization_metrics.csv"):
        rows.append(
            {
                "scope": "all_scope",
                "method": row["model"],
                "variant": "clean_phase0d",
                "seed": row["seed"],
                "top1_hit": row["top1_hit"],
                "top3_hit": row["top3_hit"],
                "top5_hit": row["top5_hit"],
                "mrr": row["mrr"],
                "recall_at_1": row["recall_at_1"],
                "recall_at_3": row["recall_at_3"],
                "recall_at_5": row["recall_at_5"],
                "notes": "clean_split_baseline",
            }
        )
    return rows


def phase1b_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(REPORTS / "phase1b_contract_metrics.csv"):
        if row.get("threshold_policy") != "max_f1":
            continue
        out.append(
            {
                "scope": row["run"],
                "method": "HyperVul risk-vs-safety",
                "variant": row["variant"],
                "seed": row["seed"],
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
                "f2": row["f2"],
                "pr_auc": row["pr_auc"],
                "roc_auc": row["roc_auc"],
                "evaluation": "validation_threshold",
                "notes": "phase1b_clean_no_augmentation",
            }
        )
    return out


def shortcut_contract_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(REPORTS / "phase1d_shortcut_metrics.csv"):
        if row.get("threshold_policy") not in {"max_f1", "test_oracle_max_f1"}:
            continue
        out.append(
            {
                "scope": row["run"],
                "method": "HyperVul targeted augmentation",
                "variant": f"{row['method']}:{row['variant']}",
                "seed": row["seed"],
                "precision": row["precision"],
                "recall": row["recall"],
                "f1": row["f1"],
                "f2": row["f2"],
                "pr_auc": row["pr_auc"],
                "roc_auc": row["roc_auc"],
                "evaluation": "test_oracle" if row["threshold_policy"] == "test_oracle_max_f1" else "validation_threshold",
                "notes": "shortcut_leaky_targeted_augmentation",
            }
        )
    return out


def phase1b_localization_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(REPORTS / "phase1b_localization_metrics.csv"):
        out.append(
            {
                "scope": row["run"],
                "method": "HyperVul risk-vs-safety",
                "variant": row["variant"],
                "seed": row["seed"],
                "top1_hit": row["top1_hit"],
                "top3_hit": row["top3_hit"],
                "top5_hit": row["top5_hit"],
                "mrr": row["mrr"],
                "recall_at_1": row["recall_at_1"],
                "recall_at_3": row["recall_at_3"],
                "recall_at_5": row["recall_at_5"],
                "notes": "phase1b_clean_no_augmentation",
            }
        )
    return out


def shortcut_localization_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(REPORTS / "phase1d_shortcut_localization.csv"):
        out.append(
            {
                "scope": row["run"],
                "method": "HyperVul targeted augmentation",
                "variant": f"{row['method']}:{row['variant']}",
                "seed": row["seed"],
                "top1_hit": row["top1_hit"],
                "top3_hit": row["top3_hit"],
                "top5_hit": row["top5_hit"],
                "mrr": row["mrr"],
                "recall_at_1": row["recall_at_1"],
                "recall_at_3": row["recall_at_3"],
                "recall_at_5": row["recall_at_5"],
                "notes": "shortcut_leaky_targeted_augmentation",
            }
        )
    return out


def best_per_method(summary_rows: list[dict[str, Any]], scope: str, evaluation: str) -> list[dict[str, Any]]:
    selected = [r for r in summary_rows if r["scope"] == scope and r.get("evaluation") == evaluation]
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        by_method[row["method"]].append(row)
    out = []
    for method, rows in by_method.items():
        best = max(rows, key=lambda r: float(r["f1_mean"]))
        out.append(best)
    return sorted(out, key=lambda r: float(r["f1_mean"]), reverse=True)


def markdown_table(rows: list[dict[str, Any]], include_scope: bool = False) -> list[str]:
    headers = ["Scope"] if include_scope else []
    headers += ["Method", "Variant", "Seeds", "Precision", "Recall", "F1", "F2", "PR-AUC", "ROC-AUC", "Notes"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        cells = [row["scope"]] if include_scope else []
        cells += [
            row["method"],
            row["variant"],
            str(row["n"]),
            row["precision_fmt"],
            row["recall_fmt"],
            row["f1_fmt"],
            row["f2_fmt"],
            row["pr_auc_fmt"],
            row["roc_auc_fmt"],
            row.get("notes", ""),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_report(contract_summary: list[dict[str, Any]], localization_summary: list[dict[str, Any]]) -> None:
    all_clean = best_per_method(contract_summary, "all_scope", "validation_threshold")
    re_clean = best_per_method(contract_summary, "reentrancy_only", "validation_threshold")
    oracle = [r for r in contract_summary if r["evaluation"] == "test_oracle"]
    oracle = sorted(oracle, key=lambda r: float(r["f1_mean"]), reverse=True)

    lines = ["# Final Baseline Comparison Tables", ""]
    lines.append("These tables combine clean baseline results with the shortcut targeted-augmentation result. Rows marked `shortcut_leaky_targeted_augmentation` are performance-oriented and not clean final evaluation.")
    lines.append("")
    lines.append("## All-Scope Validation-Threshold Comparison")
    lines.extend(markdown_table(all_clean))
    lines.append("")
    lines.append("## Reentrancy-Only Validation-Threshold Comparison")
    lines.extend(markdown_table(re_clean))
    lines.append("")
    lines.append("## Shortcut Test-Oracle Upper Bound")
    lines.extend(markdown_table(oracle, include_scope=True))
    lines.append("")
    lines.append("## Localization Summary")
    lines.append("| Scope | Method | Variant | Seeds | Top-1 | Top-3 | Top-5 | MRR | Notes |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---|")
    for row in sorted(localization_summary, key=lambda r: (r["scope"], r["method"], r["variant"])):
        lines.append(
            f"| {row['scope']} | {row['method']} | {row['variant']} | {row['n']} | "
            f"{row['top1_hit_fmt']} | {row['top3_hit_fmt']} | {row['top5_hit_fmt']} | {row['mrr_fmt']} | {row.get('notes', '')} |"
        )
    lines.append("")
    lines.append("## Best Result")
    best_clean = max([r for r in contract_summary if r["evaluation"] == "validation_threshold"], key=lambda r: float(r["f1_mean"]))
    lines.append(f"- Best validation-threshold F1: {best_clean['method']} / {best_clean['variant']} on {best_clean['scope']}: {best_clean['f1_fmt']}.")
    if oracle:
        best_oracle = oracle[0]
        lines.append(f"- Best test-oracle F1: {best_oracle['method']} / {best_oracle['variant']} on {best_oracle['scope']}: {best_oracle['f1_fmt']}.")
    (REPORTS / "final_comparison_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-clean-baselines", action="store_true", help="Rerun Phase 0D clean baselines before generating tables.")
    parser.add_argument("--run-shortcut", action="store_true", help="Rerun Phase 1D shortcut augmentation before generating tables.")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43], help="Seeds to use if rerunning training.")
    parser.add_argument("--epochs", type=int, default=5, help="Epochs to use if rerunning shortcut training.")
    parser.add_argument("--baseline-epochs", type=int, default=20, help="Epochs to use if rerunning clean baselines.")
    args = parser.parse_args()

    if args.run_clean_baselines:
        run_cmd(
            [
                sys.executable,
                "scripts/run_phase0d_clean_baselines.py",
                "--seeds",
                *[str(seed) for seed in args.seeds],
                "--epochs",
                str(args.baseline_epochs),
            ]
        )
    if args.run_shortcut:
        run_cmd(
            [
                sys.executable,
                "scripts/run_phase1d_shortcut_augmentation.py",
                "--seeds",
                *[str(seed) for seed in args.seeds],
                "--epochs",
                str(args.epochs),
            ]
        )

    contract_rows = clean_baseline_contract_rows() + phase1b_rows() + shortcut_contract_rows()
    loc_rows = clean_baseline_localization_rows() + phase1b_localization_rows() + shortcut_localization_rows()
    if not contract_rows:
        raise RuntimeError("No contract metric rows found. Run with --run-clean-baselines and/or --run-shortcut first.")

    contract_fields = ["scope", "method", "variant", "seed", "evaluation", "precision", "recall", "f1", "f2", "pr_auc", "roc_auc", "notes"]
    loc_fields = ["scope", "method", "variant", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "notes"]
    write_csv(REPORTS / "final_comparison_contract_raw.csv", contract_rows, contract_fields)
    write_csv(REPORTS / "final_comparison_localization_raw.csv", loc_rows, loc_fields)

    contract_summary = group_stats(
        contract_rows,
        ("scope", "method", "variant", "evaluation", "notes"),
        ("precision", "recall", "f1", "f2", "pr_auc", "roc_auc"),
    )
    loc_summary = group_stats(
        loc_rows,
        ("scope", "method", "variant", "notes"),
        ("top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"),
    )
    summary_fields = [
        "scope",
        "method",
        "variant",
        "evaluation",
        "notes",
        "n",
        "precision_mean",
        "precision_std",
        "recall_mean",
        "recall_std",
        "f1_mean",
        "f1_std",
        "f2_mean",
        "f2_std",
        "pr_auc_mean",
        "pr_auc_std",
        "roc_auc_mean",
        "roc_auc_std",
        "precision_fmt",
        "recall_fmt",
        "f1_fmt",
        "f2_fmt",
        "pr_auc_fmt",
        "roc_auc_fmt",
    ]
    loc_summary_fields = [
        "scope",
        "method",
        "variant",
        "notes",
        "n",
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
        "top1_hit_fmt",
        "top3_hit_fmt",
        "top5_hit_fmt",
        "mrr_fmt",
        "recall_at_1_fmt",
        "recall_at_3_fmt",
        "recall_at_5_fmt",
    ]
    write_csv(REPORTS / "final_comparison_contract_summary.csv", contract_summary, summary_fields)
    write_csv(REPORTS / "final_comparison_localization_summary.csv", loc_summary, loc_summary_fields)
    write_report(contract_summary, loc_summary)
    print(f"Wrote final comparison tables to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
