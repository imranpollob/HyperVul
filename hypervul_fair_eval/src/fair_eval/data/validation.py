"""Dataset validation and statistics used by audits and future runners."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .schemas import ContractGraph
from .splits import split_overlap_report


def pct(numer: int, denom: int) -> float:
    return round((100.0 * numer / denom), 4) if denom else 0.0


def graph_split_stats(split: str, graphs: tuple[ContractGraph, ...]) -> dict[str, Any]:
    source_counts: Counter[str] = Counter()
    node_kinds: Counter[str] = Counter()
    edge_types: Counter[str] = Counter()
    positives = 0
    negatives = 0
    interactions_with_state = 0
    interactions_with_callee = 0
    interactions_with_sec = 0
    interactions_with_source = 0
    interactions = 0

    for graph in graphs:
        source_counts[graph.source] += 1
        for edge in graph.edges:
            edge_types[edge.etype] += 1
        for node in graph.nodes:
            node_kinds[node.kind] += 1
            if not node.is_interaction:
                continue
            interactions += 1
            if node.state_vars_accessed:
                interactions_with_state += 1
            if node.external_calls:
                interactions_with_callee += 1
            if node.security_vector:
                interactions_with_sec += 1
            if node.function_source:
                interactions_with_source += 1
            if node.label == 1:
                positives += 1
            elif node.label == 0:
                negatives += 1

    labeled = positives + negatives
    return {
        "split": split,
        "graphs": len(graphs),
        "total_nodes": sum(len(graph.nodes) for graph in graphs),
        "interaction_nodes": interactions,
        "helper_nodes": sum(1 for graph in graphs for node in graph.nodes if node.kind == "helper"),
        "total_edges": sum(len(graph.edges) for graph in graphs),
        "positive_interactions": positives,
        "negative_interactions": negatives,
        "labeled_interactions": labeled,
        "positive_rate_pct": pct(positives, labeled),
        "source_counts": dict(source_counts.most_common()),
        "node_kinds": dict(node_kinds.most_common()),
        "edge_types": dict(edge_types.most_common()),
        "interaction_feature_coverage": {
            "state_vars_pct": pct(interactions_with_state, interactions),
            "external_calls_pct": pct(interactions_with_callee, interactions),
            "security_vector_pct": pct(interactions_with_sec, interactions),
            "function_source_pct": pct(interactions_with_source, interactions),
        },
    }


def dataset_validation_report(
    graphs_by_split: dict[str, tuple[ContractGraph, ...]],
) -> dict[str, Any]:
    stats = {
        split: graph_split_stats(split, graphs)
        for split, graphs in graphs_by_split.items()
    }
    overlaps = split_overlap_report(graphs_by_split)
    project_overlap_count = sum(item["count"] for item in overlaps["project"].values())
    project_contract_overlap_count = sum(item["count"] for item in overlaps["project_contract"].values())

    checks = [
        {
            "check": "project_disjoint_splits",
            "status": "pass" if project_overlap_count == 0 else "fail",
            "detail": f"Project overlap count across pairwise splits: {project_overlap_count}.",
        },
        {
            "check": "project_contract_disjoint_splits",
            "status": "pass" if project_contract_overlap_count == 0 else "fail",
            "detail": f"Project-contract overlap count across pairwise splits: {project_contract_overlap_count}.",
        },
    ]
    for split, split_stats in stats.items():
        checks.append({
            "check": f"{split}_has_both_classes",
            "status": "pass"
            if split_stats["positive_interactions"] > 0 and split_stats["negative_interactions"] > 0
            else "fail",
            "detail": (
                f"pos={split_stats['positive_interactions']}, "
                f"neg={split_stats['negative_interactions']}, "
                f"positive_rate={split_stats['positive_rate_pct']}%"
            ),
        })

    return {
        "stats_by_split": stats,
        "overlaps": overlaps,
        "readiness_checks": checks,
    }

