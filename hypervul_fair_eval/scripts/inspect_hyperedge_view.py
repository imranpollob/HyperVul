#!/usr/bin/env python3
"""Inspect the isolated HyperVul hyperedge view."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def add_src_to_path() -> None:
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


add_src_to_path()

from fair_eval.builders.hyperedge_view import build_hyperedge_examples  # noqa: E402
from fair_eval.data import load_dataset_bundle  # noqa: E402


def split_stats(examples: tuple[Any, ...]) -> dict[str, Any]:
    labels = Counter(example.label for example in examples)
    state_counts = [len(example.state_members) for example in examples]
    callee_counts = [len(example.callee_members) for example in examples]
    member_counts = [example.member_count for example in examples]
    sec_dims = Counter(len(example.security_features) for example in examples)
    missing_state = sum(1 for count in state_counts if count == 0)
    missing_callee = sum(1 for count in callee_counts if count == 0)
    return {
        "examples": len(examples),
        "positive": labels[1],
        "negative": labels[0],
        "missing_state_members": missing_state,
        "missing_callee_members": missing_callee,
        "avg_state_members": round(sum(state_counts) / len(state_counts), 4) if state_counts else 0.0,
        "avg_callee_members": round(sum(callee_counts) / len(callee_counts), 4) if callee_counts else 0.0,
        "avg_total_members": round(sum(member_counts) / len(member_counts), 4) if member_counts else 0.0,
        "security_feature_dims": dict(sec_dims.most_common()),
    }


def build_report(project_root: Path) -> dict[str, Any]:
    bundle = load_dataset_bundle(project_root)
    return {
        "project_root": str(project_root.resolve()),
        "description": "HyperVul hyperedge view for RQ2/RQ3 only; not used by RQ1 generic baselines.",
        "splits": {
            split: split_stats(build_hyperedge_examples(graphs))
            for split, graphs in bundle.graphs.items()
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Hyperedge View Inspection",
        "",
        "This view is reserved for RQ2 representation ablation and RQ3 HyperVul experiments.",
        "It should not be imported by RQ1 generic baseline scripts.",
        "",
        "| Split | Examples | Pos | Neg | Missing State | Missing Callee | Avg State | Avg Callee | Avg Members | Security Dims |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for split, stats in report["splits"].items():
        dims = ", ".join(f"{dim}:{count}" for dim, count in stats["security_feature_dims"].items())
        lines.append(
            f"| {split} | {stats['examples']} | {stats['positive']} | {stats['negative']} | "
            f"{stats['missing_state_members']} | {stats['missing_callee_members']} | "
            f"{stats['avg_state_members']} | {stats['avg_callee_members']} | "
            f"{stats['avg_total_members']} | {dims} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(args.project_root)
    json_path = args.output_dir / "hyperedge_view_inspection.json"
    md_path = args.output_dir / "hyperedge_view_inspection.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()

