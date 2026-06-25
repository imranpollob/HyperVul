#!/usr/bin/env python3
"""Audit existing HyperVul datasets for the fair-evaluation rewrite.

This script does not create new splits or graphs. It checks whether the existing
project-disjoint contract graphs and related feature/clean-negative files are
ready to support the new RQ1/RQ2/RQ3 experiment plan.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SPLITS = ("train", "val", "test")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def pct(numer: int, denom: int) -> float:
    return round((100.0 * numer / denom), 4) if denom else 0.0


def pairwise_overlaps(groups: dict[str, set[str]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    names = list(groups)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            inter = sorted(groups[a] & groups[b])
            out[f"{a}_vs_{b}"] = {
                "count": len(inter),
                "examples": inter[:10],
            }
    return out


def graph_identity_sets(graphs_by_split: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, set[str]]]:
    keys: dict[str, dict[str, set[str]]] = {
        "graph_id": {},
        "project": {},
        "project_contract": {},
        "raw_contract_name": {},
    }
    for split, graphs in graphs_by_split.items():
        keys["graph_id"][split] = {str(g.get("graph_id")) for g in graphs if g.get("graph_id")}
        keys["project"][split] = {str(g.get("project")) for g in graphs if g.get("project")}
        keys["project_contract"][split] = {
            f"{g.get('project')}::{g.get('contract')}"
            for g in graphs
            if g.get("project") and g.get("contract")
        }
        keys["raw_contract_name"][split] = {str(g.get("contract")) for g in graphs if g.get("contract")}
    return keys


def graph_stats(split: str, graphs: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts: Counter[str] = Counter()
    node_kinds: Counter[str] = Counter()
    edge_types: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    graphs_with_edges = 0
    graphs_with_positive = 0
    missing_graph_fields: Counter[str] = Counter()
    missing_node_fields: Counter[str] = Counter()
    missing_edge_fields: Counter[str] = Counter()
    interaction_nodes = 0
    helper_nodes = 0
    total_nodes = 0
    total_edges = 0
    interactions_with_state = 0
    interactions_with_callee = 0
    interactions_with_sec = 0
    interactions_with_source = 0

    required_graph_fields = ("graph_id", "split", "source", "project", "contract", "nodes", "edges")
    required_node_fields = ("id", "kind", "function")
    required_edge_fields = ("src", "dst", "etype")

    for graph in graphs:
        for field in required_graph_fields:
            if field not in graph:
                missing_graph_fields[field] += 1
        source_counts[str(graph.get("source", "UNKNOWN"))] += 1
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []
        total_nodes += len(nodes)
        total_edges += len(edges)
        if edges:
            graphs_with_edges += 1
        has_positive = False

        for node in nodes:
            for field in required_node_fields:
                if field not in node:
                    missing_node_fields[field] += 1
            kind = str(node.get("kind", "UNKNOWN"))
            node_kinds[kind] += 1
            if kind == "interaction":
                interaction_nodes += 1
                if node.get("state_vars_accessed"):
                    interactions_with_state += 1
                if node.get("external_calls"):
                    interactions_with_callee += 1
                if node.get("sec") is not None:
                    interactions_with_sec += 1
                if node.get("function_source"):
                    interactions_with_source += 1
                label = node.get("label")
                if label in (0, 1, 0.0, 1.0):
                    label_counts[str(int(label))] += 1
                    has_positive = has_positive or int(label) == 1
            elif kind == "helper":
                helper_nodes += 1

        if has_positive:
            graphs_with_positive += 1

        for edge in edges:
            for field in required_edge_fields:
                if field not in edge:
                    missing_edge_fields[field] += 1
            edge_types[str(edge.get("etype", "UNKNOWN"))] += 1

    positives = label_counts["1"]
    negatives = label_counts["0"]
    labeled = positives + negatives

    return {
        "split": split,
        "graphs": len(graphs),
        "graphs_with_edges": graphs_with_edges,
        "graphs_with_positive": graphs_with_positive,
        "total_nodes": total_nodes,
        "interaction_nodes": interaction_nodes,
        "helper_nodes": helper_nodes,
        "total_edges": total_edges,
        "positive_interactions": positives,
        "negative_interactions": negatives,
        "labeled_interactions": labeled,
        "positive_rate_pct": pct(positives, labeled),
        "source_counts": dict(source_counts.most_common()),
        "node_kinds": dict(node_kinds.most_common()),
        "edge_types": dict(edge_types.most_common()),
        "interaction_feature_coverage": {
            "state_vars_pct": pct(interactions_with_state, interaction_nodes),
            "external_calls_pct": pct(interactions_with_callee, interaction_nodes),
            "security_vector_pct": pct(interactions_with_sec, interaction_nodes),
            "function_source_pct": pct(interactions_with_source, interaction_nodes),
        },
        "missing_graph_fields": dict(missing_graph_fields),
        "missing_node_fields": dict(missing_node_fields),
        "missing_edge_fields": dict(missing_edge_fields),
    }


def audit_split_files(project_root: Path) -> dict[str, Any]:
    groups = {
        "raw_splits": project_root / "data" / "splits",
        "clean_splits": project_root / "data" / "splits_clean",
    }
    report: dict[str, Any] = {}
    for group, base in groups.items():
        group_report: dict[str, Any] = {}
        for split in SPLITS:
            path = base / f"{split}.json"
            if not path.exists():
                group_report[split] = {"exists": False}
                continue
            data = load_json(path)
            labels = [item.get("label") for item in data if "label" in item]
            positives = sum(1 for y in labels if float(y) == 1.0)
            negatives = sum(1 for y in labels if float(y) == 0.0)
            hashes = {str(item.get("normalized_source_hash")) for item in data if item.get("normalized_source_hash")}
            group_report[split] = {
                "exists": True,
                "records": len(data),
                "positive": positives,
                "negative": negatives,
                "positive_rate_pct": pct(positives, positives + negatives),
                "normalized_source_hashes": len(hashes),
            }
        report[group] = group_report
    return report


def audit_clean_negatives(project_root: Path) -> dict[str, Any]:
    candidates = [
        project_root / "experiments" / "latest1" / "eval_clean_negatives_oz_features.json",
        project_root / "experiments" / "latest1" / "eval_clean_negatives_aave_split.json",
        project_root / "experiments" / "latest1" / "eval_clean_negatives_external.json",
        project_root / "experiments" / "latest1" / "eval_clean_negatives_liquity.json",
        project_root / "experiments" / "results" / "eval_clean_negatives_oz_features.json",
        project_root / "experiments" / "results" / "eval_clean_negatives_aave_split.json",
        project_root / "experiments" / "results" / "eval_clean_negatives_external.json",
        project_root / "experiments" / "results" / "eval_clean_negatives_liquity.json",
    ]
    report: dict[str, Any] = {}
    for path in candidates:
        if not path.exists():
            continue
        data = load_json(path)
        labels = [item.get("label", 0) for item in data]
        positives = sum(1 for y in labels if float(y) == 1.0)
        negatives = sum(1 for y in labels if float(y) == 0.0)
        report[str(path.relative_to(project_root))] = {
            "records": len(data),
            "positive": positives,
            "negative": negatives,
            "all_negative": positives == 0 and negatives == len(data),
        }
    return report


def summarize_clean_negatives(inventory: dict[str, Any]) -> dict[str, Any]:
    """Prefer experiments/latest1 copies when mirrored files exist."""
    preferred_by_name: dict[str, tuple[str, dict[str, Any]]] = {}
    for rel_path, stats in inventory.items():
        name = Path(rel_path).name
        old = preferred_by_name.get(name)
        if old is None or rel_path.startswith("experiments/latest1/"):
            preferred_by_name[name] = (rel_path, stats)

    canonical_files = {rel_path: stats for rel_path, stats in preferred_by_name.values()}
    return {
        "candidate_files": len(inventory),
        "canonical_files": len(canonical_files),
        "canonical_records": sum(stats["records"] for stats in canonical_files.values()),
        "canonical_negative": sum(stats["negative"] for stats in canonical_files.values()),
        "canonical_positive": sum(stats["positive"] for stats in canonical_files.values()),
        "canonical_all_negative": all(stats["all_negative"] for stats in canonical_files.values()) if canonical_files else False,
        "canonical_file_paths": sorted(canonical_files),
    }


def audit_embedding_coverage(project_root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {}
    node_path = project_root / "data" / "contract_graphs" / "node_embeddings.pt"
    member_path = project_root / "data" / "contract_graphs" / "member_embeddings.pt"
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"torch_available": False, "error": str(exc)}

    report["torch_available"] = True
    if node_path.exists():
        node_obj = torch.load(node_path, map_location="cpu")
        by_hash = node_obj.get("by_hash", {}) if isinstance(node_obj, dict) else {}
        report["node_embeddings"] = {
            "exists": True,
            "dim": node_obj.get("dim") if isinstance(node_obj, dict) else None,
            "by_hash_count": len(by_hash),
        }
        split_cov: dict[str, Any] = {}
        for path in [
            project_root / "data" / "splits" / "train.json",
            project_root / "data" / "splits" / "val.json",
            project_root / "data" / "splits" / "test.json",
            project_root / "data" / "splits" / "train_augmented.json",
            project_root / "data" / "splits" / "val_features.json",
            project_root / "data" / "splits" / "test_features.json",
        ]:
            if not path.exists():
                continue
            data = load_json(path)
            hashes = [item.get("normalized_source_hash") for item in data if item.get("normalized_source_hash")]
            covered = sum(1 for h in hashes if h in by_hash)
            split_cov[str(path.relative_to(project_root))] = {
                "hashes": len(hashes),
                "covered": covered,
                "coverage_pct": pct(covered, len(hashes)),
            }
        report["node_embeddings"]["split_hash_coverage"] = split_cov
    else:
        report["node_embeddings"] = {"exists": False}

    if member_path.exists():
        member_obj = torch.load(member_path, map_location="cpu")
        state_embeddings = member_obj.get("state", {}) if isinstance(member_obj, dict) else {}
        callee_embeddings = member_obj.get("callee", {}) if isinstance(member_obj, dict) else {}
        report["member_embeddings"] = {
            "exists": True,
            "state_count": len(state_embeddings),
            "callee_count": len(callee_embeddings),
        }

        graph_cov: dict[str, Any] = {}
        for split in SPLITS:
            path = project_root / "data" / "contract_graphs" / f"{split}.json"
            if not path.exists():
                continue
            graphs = load_json(path)
            state_texts: list[str] = []
            callee_texts: list[str] = []
            for graph in graphs:
                for node in graph.get("nodes", []):
                    if node.get("kind") != "interaction":
                        continue
                    state_texts.extend([str(x) for x in node.get("state_texts", [])])
                    callee_texts.extend([str(x) for x in node.get("callee_texts", [])])
            state_covered = sum(1 for text in state_texts if text in state_embeddings)
            callee_covered = sum(1 for text in callee_texts if text in callee_embeddings)
            graph_cov[split] = {
                "state_texts": len(state_texts),
                "state_covered": state_covered,
                "state_coverage_pct": pct(state_covered, len(state_texts)),
                "callee_texts": len(callee_texts),
                "callee_covered": callee_covered,
                "callee_coverage_pct": pct(callee_covered, len(callee_texts)),
            }
        report["member_embeddings"]["contract_graph_coverage"] = graph_cov
    else:
        report["member_embeddings"] = {"exists": False}

    return report


def readiness_checks(report: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    graph_stats_by_split = report["contract_graphs"]["stats_by_split"]
    missing_graph_files = [
        split for split, stats in graph_stats_by_split.items() if not stats.get("exists", True)
    ]
    checks.append({
        "check": "contract_graph_files_exist",
        "status": "fail" if missing_graph_files else "pass",
        "detail": f"Missing splits: {missing_graph_files}" if missing_graph_files else "All train/val/test graph files exist.",
    })

    overlap_project = report["contract_graphs"]["overlaps"]["project"]
    project_overlap_count = sum(v["count"] for v in overlap_project.values())
    checks.append({
        "check": "project_disjoint_splits",
        "status": "pass" if project_overlap_count == 0 else "fail",
        "detail": f"Project overlap count across pairwise splits: {project_overlap_count}.",
    })

    overlap_project_contract = report["contract_graphs"]["overlaps"]["project_contract"]
    project_contract_overlap_count = sum(v["count"] for v in overlap_project_contract.values())
    checks.append({
        "check": "project_contract_disjoint_splits",
        "status": "pass" if project_contract_overlap_count == 0 else "fail",
        "detail": f"Project-contract overlap count across pairwise splits: {project_contract_overlap_count}.",
    })

    for split, stats in graph_stats_by_split.items():
        if not stats.get("exists", True):
            continue
        positives = stats["positive_interactions"]
        negatives = stats["negative_interactions"]
        status = "pass" if positives > 0 and negatives > 0 else "fail"
        checks.append({
            "check": f"{split}_has_both_classes",
            "status": status,
            "detail": f"pos={positives}, neg={negatives}, positive_rate={stats['positive_rate_pct']}%",
        })

    member_cov = (
        report.get("embedding_coverage", {})
        .get("member_embeddings", {})
        .get("contract_graph_coverage", {})
    )
    low_cov = []
    for split, cov in member_cov.items():
        if cov["state_coverage_pct"] < 95.0 or cov["callee_coverage_pct"] < 95.0:
            low_cov.append(split)
    checks.append({
        "check": "member_embedding_coverage",
        "status": "warn" if low_cov else "pass",
        "detail": f"Coverage below 95% for splits: {low_cov}" if low_cov else "State/callee member embedding coverage is >=95%.",
    })

    clean_neg_summary = report.get("clean_negative_summary", {})
    total_clean = clean_neg_summary.get("canonical_records", 0)
    all_negative = clean_neg_summary.get("canonical_all_negative", False)
    checks.append({
        "check": "clean_negative_inventory",
        "status": "pass" if total_clean > 0 and all_negative else "warn",
        "detail": (
            f"Found {total_clean} canonical clean-negative records across "
            f"{clean_neg_summary.get('canonical_files', 0)} pools "
            f"({clean_neg_summary.get('candidate_files', 0)} candidate files including mirrors)."
        ),
    })

    return checks


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# HyperVul Fair Evaluation Dataset Audit")
    lines.append("")
    lines.append(f"Generated: `{report['generated_at']}`")
    lines.append("")

    lines.append("## Readiness Checks")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---:|---|")
    for check in report["readiness_checks"]:
        lines.append(f"| {check['check']} | {check['status']} | {check['detail']} |")
    lines.append("")

    lines.append("## Contract Graph Split Statistics")
    lines.append("")
    lines.append("| Split | Graphs | Interactions | Pos | Neg | Pos Rate | Edges | Sources |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for split in SPLITS:
        stats = report["contract_graphs"]["stats_by_split"].get(split)
        if not stats or not stats.get("exists", True):
            lines.append(f"| {split} | missing | | | | | | |")
            continue
        lines.append(
            "| {split} | {graphs} | {interactions} | {pos} | {neg} | {rate:.2f}% | {edges} | {sources} |".format(
                split=split,
                graphs=stats["graphs"],
                interactions=stats["interaction_nodes"],
                pos=stats["positive_interactions"],
                neg=stats["negative_interactions"],
                rate=stats["positive_rate_pct"],
                edges=stats["total_edges"],
                sources=", ".join(f"{k}:{v}" for k, v in stats["source_counts"].items()),
            )
        )
    lines.append("")

    lines.append("## Split Overlaps")
    lines.append("")
    lines.append("| Identity | train-val | train-test | val-test |")
    lines.append("|---|---:|---:|---:|")
    for identity, overlaps in report["contract_graphs"]["overlaps"].items():
        tv = overlaps.get("train_vs_val", {}).get("count", 0)
        tt = overlaps.get("train_vs_test", {}).get("count", 0)
        vt = overlaps.get("val_vs_test", {}).get("count", 0)
        lines.append(f"| {identity} | {tv} | {tt} | {vt} |")
    lines.append("")

    lines.append("## Interaction Feature Coverage")
    lines.append("")
    lines.append("| Split | State Vars | External Calls | Security Vector | Function Source |")
    lines.append("|---|---:|---:|---:|---:|")
    for split in SPLITS:
        stats = report["contract_graphs"]["stats_by_split"].get(split)
        if not stats or not stats.get("exists", True):
            continue
        cov = stats["interaction_feature_coverage"]
        lines.append(
            f"| {split} | {cov['state_vars_pct']:.2f}% | {cov['external_calls_pct']:.2f}% | "
            f"{cov['security_vector_pct']:.2f}% | {cov['function_source_pct']:.2f}% |"
        )
    lines.append("")

    member_cov = (
        report.get("embedding_coverage", {})
        .get("member_embeddings", {})
        .get("contract_graph_coverage", {})
    )
    if member_cov:
        lines.append("## Member Embedding Coverage")
        lines.append("")
        lines.append("| Split | State Texts | State Coverage | Callee Texts | Callee Coverage |")
        lines.append("|---|---:|---:|---:|---:|")
        for split in SPLITS:
            cov = member_cov.get(split)
            if not cov:
                continue
            lines.append(
                f"| {split} | {cov['state_texts']} | {cov['state_coverage_pct']:.2f}% | "
                f"{cov['callee_texts']} | {cov['callee_coverage_pct']:.2f}% |"
            )
        lines.append("")

    lines.append("## Clean-Negative Inventory")
    lines.append("")
    summary = report.get("clean_negative_summary", {})
    if summary:
        lines.append(
            f"Canonical clean-negative pools: **{summary['canonical_files']}** files, "
            f"**{summary['canonical_records']}** records. "
            f"The inventory may include mirrored copies under both `experiments/latest1` and `experiments/results`."
        )
        lines.append("")
    lines.append("| File | Records | Pos | Neg | All Negative |")
    lines.append("|---|---:|---:|---:|---:|")
    for file_name, stats in report["clean_negative_inventory"].items():
        lines.append(
            f"| `{file_name}` | {stats['records']} | {stats['positive']} | "
            f"{stats['negative']} | {stats['all_negative']} |"
        )
    lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    if all(c["status"] != "fail" for c in report["readiness_checks"]):
        lines.append(
            "The existing `data/contract_graphs` train/val/test files are suitable as the canonical "
            "project-disjoint splits for the new fair-evaluation codebase. New raw splits or graph "
            "extraction are not required before model implementation, but builders should be written "
            "to produce separate function, generic graph, pairwise graph, and hyperedge views."
        )
    else:
        lines.append(
            "At least one required check failed. Resolve the failed checks before implementing model training."
        )
    lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    graphs_by_split: dict[str, list[dict[str, Any]]] = {}
    stats_by_split: dict[str, Any] = {}
    for split in SPLITS:
        path = project_root / "data" / "contract_graphs" / f"{split}.json"
        if not path.exists():
            stats_by_split[split] = {"exists": False}
            graphs_by_split[split] = []
            continue
        graphs = load_json(path)
        graphs_by_split[split] = graphs
        stats_by_split[split] = graph_stats(split, graphs)

    identity_sets = graph_identity_sets(graphs_by_split)
    overlaps = {name: pairwise_overlaps(groups) for name, groups in identity_sets.items()}

    report: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(project_root),
        "contract_graphs": {
            "stats_by_split": stats_by_split,
            "overlaps": overlaps,
        },
        "split_file_inventory": audit_split_files(project_root),
        "embedding_coverage": audit_embedding_coverage(project_root),
    }
    report["clean_negative_inventory"] = audit_clean_negatives(project_root)
    report["clean_negative_summary"] = summarize_clean_negatives(report["clean_negative_inventory"])
    report["readiness_checks"] = readiness_checks(report)

    json_path = output_dir / "dataset_audit.json"
    md_path = output_dir / "dataset_audit.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, md_path)

    failures = [c for c in report["readiness_checks"] if c["status"] == "fail"]
    warnings = [c for c in report["readiness_checks"] if c["status"] == "warn"]
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Readiness: {len(failures)} failed, {len(warnings)} warnings")
    if failures:
        for failure in failures:
            print(f"FAIL {failure['check']}: {failure['detail']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
