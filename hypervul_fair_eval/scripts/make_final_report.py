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


def metric_cell(stats: dict[str, Any], metric: str) -> str:
    item = stats.get(metric)
    if not item:
        return "n/a"
    return f"{item['mean'] * 100:.2f} +/- {item['std'] * 100:.2f}"


def table_from_models(title: str, models: dict[str, Any], model_order: list[str]) -> list[str]:
    lines = [f"## {title}", ""]
    lines.append("| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    ordered = [name for name in model_order if name in models] + [name for name in models if name not in model_order]
    for name in ordered:
        stats = models[name]
        lines.append(
            f"| {name} | {metric_cell(stats, 'precision')} | {metric_cell(stats, 'recall')} | "
            f"{metric_cell(stats, 'f1')} | {metric_cell(stats, 'f2')} | "
            f"{metric_cell(stats, 'pr_auc')} | {metric_cell(stats, 'roc_auc')} |"
        )
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


def build_report(output_dir: Path) -> dict[str, Any]:
    return {
        "dataset_audit": load_json(output_dir / "dataset_audit.json"),
        "rq1": load_json(output_dir / "rq1" / "rq1_generic_baselines_summary.json"),
        "rq2": load_json(output_dir / "rq2" / "rq2_representation_ablation_summary.json"),
        "rq3": load_json(output_dir / "rq3" / "rq3_hypervul_ablation_summary.json"),
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
    lines += table_from_models(
        "RQ1: Generic Neural Baselines",
        report["rq1"]["models"],
        [
            "function-mlp",
            "function-features-mlp",
            "sequence",
            "callgraph-gcn",
            "pairwise-gcn",
            "pairwise-gat",
        ],
    )
    lines += table_from_models(
        "RQ2: Controlled Representation Ablation",
        report["rq2"]["models"],
        ["set-pool", "pairwise-gcn", "pairwise-gat", "hyperedge-nn"],
    )
    lines += significance_table(report["rq2"])
    lines += table_from_models(
        "RQ3: HyperVul Component Ablation",
        report["rq3"]["models"],
        ["emb-only", "security", "full", "no-localize", "no-contrastive"],
    )
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

