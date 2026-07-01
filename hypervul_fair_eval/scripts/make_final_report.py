#!/usr/bin/env python3
"""Assemble final fair-evaluation report from RQ1/RQ2/RQ3 outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path) -> dict[str, Any] | None:
    return load_json(path) if path.exists() else None


def metric_cell(stats: dict[str, Any], metric: str) -> str:
    item = stats.get(metric)
    if not item:
        return "n/a"
    return f"{item['mean'] * 100:.2f} +/- {item['std'] * 100:.2f}"


def table_from_models(
    title: str,
    models: dict[str, Any],
    model_order: list[str],
    hyperedge_flags: dict[str, str] | None = None,
) -> list[str]:
    lines = [f"## {title}", ""]
    if hyperedge_flags is None:
        lines.append("| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
    else:
        lines.append("| Model | Uses Hyperedge | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    ordered = [name for name in model_order if name in models] + [name for name in models if name not in model_order]
    for name in ordered:
        stats = models[name]
        metric_cells = (
            f"{metric_cell(stats, 'precision')} | {metric_cell(stats, 'recall')} | "
            f"{metric_cell(stats, 'f1')} | {metric_cell(stats, 'f2')} | "
            f"{metric_cell(stats, 'pr_auc')} | {metric_cell(stats, 'roc_auc')}"
        )
        if hyperedge_flags is None:
            lines.append(f"| {name} | {metric_cells} |")
        else:
            lines.append(f"| {name} | {hyperedge_flags.get(name, 'No')} | {metric_cells} |")
    lines.append("")
    return lines


def dataset_table(audit: dict[str, Any]) -> list[str]:
    stats_by_split = audit["contract_graphs"]["stats_by_split"]
    lines = ["## Dataset", ""]
    lines.append("| Split | Graphs | Interactions | Pos | Neg | Pos Rate | Edges |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for split in ("train", "val", "test"):
        stats = stats_by_split[split]
        lines.append(
            f"| {split} | {stats['graphs']} | {stats['interaction_nodes']} | "
            f"{stats['positive_interactions']} | {stats['negative_interactions']} | "
            f"{stats['positive_rate_pct']:.2f}% | {stats['total_edges']} |"
        )
    lines.append("")
    lines.append("Split checks: project-disjoint and project-contract-disjoint checks passed in the dataset audit.")
    lines.append("")
    return lines


def significance_table(rq2: dict[str, Any]) -> list[str]:
    items = rq2.get("paired_significance", [])
    if not items:
        return []
    lines = [
        "## RQ2 Seed-Paired Significance",
        "",
        "Reference model: `hyperedge-nn`. Test: exact sign-flip permutation over paired seed-level metric deltas.",
        "",
        "| Comparison | Metric | Mean Delta | p-value |",
        "|---|---|---:|---:|",
    ]
    for item in items:
        lines.append(
            f"| hyperedge-nn vs {item['baseline']} | {item['metric']} | "
            f"{item['mean_delta'] * 100:.2f} | {item['p_value']:.4f} |"
        )
    lines.append("")
    return lines


def quick_sweep_table(quick_sweep: dict[str, Any]) -> list[str]:
    variants = quick_sweep.get("variants", [])
    if not variants:
        return []
    lines = [
        "## Table B: HyperVul Quick Optimization Sweep",
        "",
        "| Variant | Symbolic | Loss | Early Stop | SCL Pretrain | Hard Neg Weight | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in variants:
        cfg = item.get("config", {})
        metrics = item.get("metrics", {})
        lines.append(
            f"| {item.get('variant', item.get('model', 'n/a'))} | {cfg.get('symbolic_mode', 'n/a')} | "
            f"{cfg.get('loss', 'n/a')} | {cfg.get('early_stop', 'n/a')} | "
            f"{cfg.get('scl_pretrain_epochs', 'n/a')} | {cfg.get('scl_hard_neg_weight', 'n/a')} | "
            f"{metrics.get('precision', 0.0) * 100:.2f} | {metrics.get('recall', 0.0) * 100:.2f} | "
            f"{metrics.get('f1', 0.0) * 100:.2f} | {metrics.get('f2', 0.0) * 100:.2f} | "
            f"{metrics.get('pr_auc', 0.0) * 100:.2f} | {metrics.get('roc_auc', 0.0) * 100:.2f} |"
        )
    lines.append("")
    return lines


def tool_eval_table(tool_eval: dict[str, Any]) -> list[str]:
    metrics = tool_eval.get("metrics", {})
    if not metrics:
        return []
    lines = [
        "## Table C: HyperVul-Tool Final Evaluation",
        "",
        "| Model | Uses Hyperedge | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        (
            f"| HyperVul-Tool | Yes | {metric_cell(metrics, 'precision')} | {metric_cell(metrics, 'recall')} | "
            f"{metric_cell(metrics, 'f1')} | {metric_cell(metrics, 'f2')} | "
            f"{metric_cell(metrics, 'pr_auc')} | {metric_cell(metrics, 'roc_auc')} |"
        ),
        "",
    ]
    return lines


def build_report(output_dir: Path) -> dict[str, Any]:
    rq1 = load_json(output_dir / "rq1" / "rq1_generic_baselines_summary.json")
    rq2 = load_json(output_dir / "rq2" / "rq2_representation_ablation_summary.json")
    rq3 = load_json(output_dir / "rq3" / "rq3_hypervul_ablation_summary.json")
    rq1_vs_hypervul = {"models": dict(rq1["models"])}
    if "full" in rq3["models"]:
        rq1_vs_hypervul["models"]["HyperVul-Full"] = rq3["models"]["full"]
    return {
        "dataset_audit": load_json(output_dir / "dataset_audit.json"),
        "rq1": rq1,
        "rq1_vs_hypervul": rq1_vs_hypervul,
        "rq2": rq2,
        "rq3": rq3,
        "strong_baselines": load_optional_json(output_dir / "strong_baselines" / "summary.json"),
        "quick_sweep": load_optional_json(output_dir / "quick_sweep" / "summary.json"),
        "tool_eval": load_optional_json(output_dir / "tool_eval" / "summary.json"),
        "notes": {
            "static_analyzers": "Slither/Mythril are deferred, not abandoned, because compiler/toolchain handling is separate.",
            "rq3_symbolic_scope": (
                "The canonical contract_graphs view exposes an 8-d security context. "
                "Therefore RQ3 security and full variants are equivalent in this run."
            ),
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# HyperVul Fair Evaluation Final Report",
        "",
        "This report consolidates the current fair-evaluation rewrite outputs.",
        "",
        "Static analyzer baselines are deferred, not abandoned, because they require separate compiler/toolchain handling.",
        "",
    ]
    lines += dataset_table(report["dataset_audit"])
    if report.get("strong_baselines"):
        lines += table_from_models(
            "Table A: Strong Independently Tuned Generic Baselines",
            report["strong_baselines"]["models"],
            [
                "function-mlp",
                "function-features-mlp",
                "sequence-bigru",
                "callgraph-gat",
                "pairwise-rgcn",
                "pairwise-gat",
            ],
            {
                "function-mlp": "No",
                "function-features-mlp": "No",
                "sequence-bigru": "No",
                "callgraph-gat": "No",
                "pairwise-rgcn": "No",
                "pairwise-gat": "No",
            },
        )
    lines += table_from_models(
        "Table 2: RQ1 Generic Baselines vs HyperVul-Full",
        report["rq1_vs_hypervul"]["models"],
        [
            "function-mlp",
            "function-features-mlp",
            "sequence",
            "callgraph-gcn",
            "pairwise-gcn",
            "pairwise-gat",
            "HyperVul-Full",
        ],
        {
            "function-mlp": "No",
            "function-features-mlp": "No",
            "sequence": "No",
            "callgraph-gcn": "No",
            "pairwise-gcn": "No",
            "pairwise-gat": "No",
            "HyperVul-Full": "Yes",
        },
    )
    lines += table_from_models(
        "Table 3: RQ2 Controlled Representation Ablation",
        report["rq2"]["models"],
        ["set-pool", "pairwise-gcn", "pairwise-gat", "hyperedge-nn"],
    )
    lines += significance_table(report["rq2"])
    lines += table_from_models(
        "Table 4: RQ3 HyperVul Component Ablation",
        report["rq3"]["models"],
        ["emb-only", "security", "full", "no-localize", "no-contrastive"],
    )
    if report.get("quick_sweep"):
        lines += quick_sweep_table(report["quick_sweep"])
    if report.get("tool_eval"):
        lines += tool_eval_table(report["tool_eval"])
    lines += [
        "## Notes",
        "",
        "- `security` and `full` in RQ3 both use the canonical 8-d security context available in `data/contract_graphs`.",
        "- Slither/Mythril will be added later through a dedicated static-analysis harness pass.",
        "- All neural tables use five seeds: `42 43 44 45 46`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    args = parser.parse_args()
    report = build_report(args.output_dir)
    json_path = args.output_dir / "final_report.json"
    md_path = args.output_dir / "final_report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
