#!/usr/bin/env python3
"""Inspect RQ1 generic baseline views built from canonical contract graphs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def add_src_to_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


add_src_to_path()

from fair_eval.builders import (  # noqa: E402
    build_callgraph_views,
    build_function_examples,
    build_pairwise_graph_views,
    build_sequence_examples,
)
from fair_eval.builders.common import GraphView, positive_rate  # noqa: E402
from fair_eval.data import load_dataset_bundle  # noqa: E402


def function_stats(examples: tuple[Any, ...]) -> dict[str, Any]:
    labels = Counter(example.label for example in examples)
    sources = Counter(example.source for example in examples)
    return {
        "examples": len(examples),
        "positive": labels[1],
        "negative": labels[0],
        "positive_rate_pct": positive_rate(labels[1], labels[0]),
        "sources": dict(sources.most_common()),
    }


def sequence_stats(sequences: tuple[Any, ...]) -> dict[str, Any]:
    labels: Counter[int] = Counter()
    lengths = []
    for sequence in sequences:
        lengths.append(len(sequence.node_ids))
        labels.update(label for label in sequence.labels if label in (0, 1))
    return {
        "sequences": len(sequences),
        "tokens": sum(lengths),
        "avg_length": round(sum(lengths) / len(lengths), 4) if lengths else 0.0,
        "positive": labels[1],
        "negative": labels[0],
        "positive_rate_pct": positive_rate(labels[1], labels[0]),
    }


def graph_view_stats(views: tuple[GraphView, ...]) -> dict[str, Any]:
    edge_types: Counter[str] = Counter()
    pos = 0
    neg = 0
    nodes = 0
    edges = 0
    graphs_with_edges = 0
    for view in views:
        nodes += len(view.nodes)
        edges += len(view.edges)
        graphs_with_edges += int(bool(view.edges))
        pos += view.positive_count
        neg += view.negative_count
        edge_types.update(edge.etype for edge in view.edges)
    return {
        "graphs": len(views),
        "graphs_with_edges": graphs_with_edges,
        "nodes": nodes,
        "edges": edges,
        "positive": pos,
        "negative": neg,
        "positive_rate_pct": positive_rate(pos, neg),
        "edge_types": dict(edge_types.most_common()),
    }


def build_report(project_root: Path) -> dict[str, Any]:
    bundle = load_dataset_bundle(project_root)
    report: dict[str, Any] = {"project_root": str(project_root.resolve()), "splits": {}}
    for split, graphs in bundle.graphs.items():
        function_examples = build_function_examples(graphs)
        sequences = build_sequence_examples(graphs)
        callgraphs = build_callgraph_views(graphs)
        pairwise_graphs = build_pairwise_graph_views(graphs)
        report["splits"][split] = {
            "function_view": function_stats(function_examples),
            "sequence_view": sequence_stats(sequences),
            "callgraph_view": graph_view_stats(callgraphs),
            "pairwise_graph_view": graph_view_stats(pairwise_graphs),
        }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ["# Generic Baseline View Inspection", ""]
    lines.append("These views are for RQ1 generic baselines and do not use a HyperVul hyperedge builder.")
    lines.append("")

    lines.append("## Function And Sequence Views")
    lines.append("")
    lines.append("| Split | Function Examples | Function Pos | Function Neg | Sequence Graphs | Sequence Tokens |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for split, stats in report["splits"].items():
        fn = stats["function_view"]
        seq = stats["sequence_view"]
        lines.append(
            f"| {split} | {fn['examples']} | {fn['positive']} | {fn['negative']} | "
            f"{seq['sequences']} | {seq['tokens']} |"
        )
    lines.append("")

    lines.append("## Generic Graph Views")
    lines.append("")
    lines.append("| Split | View | Graphs | Nodes | Edges | Pos | Neg | Edge Types |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for split, stats in report["splits"].items():
        for key in ("callgraph_view", "pairwise_graph_view"):
            view = stats[key]
            edge_types = ", ".join(f"{name}:{count}" for name, count in view["edge_types"].items())
            lines.append(
                f"| {split} | {key} | {view['graphs']} | {view['nodes']} | {view['edges']} | "
                f"{view['positive']} | {view['negative']} | {edge_types} |"
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
    json_path = args.output_dir / "generic_view_inspection.json"
    md_path = args.output_dir / "generic_view_inspection.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()

