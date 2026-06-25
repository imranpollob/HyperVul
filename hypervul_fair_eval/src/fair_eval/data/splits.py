"""Split identity helpers and overlap checks."""

from __future__ import annotations

from collections.abc import Callable

from .schemas import ContractGraph


IdentityFn = Callable[[ContractGraph], str | None]


def graph_id(graph: ContractGraph) -> str:
    return graph.graph_id


def project(graph: ContractGraph) -> str:
    return graph.project


def project_contract(graph: ContractGraph) -> str:
    return f"{graph.project}::{graph.contract}"


def raw_contract_name(graph: ContractGraph) -> str:
    return graph.contract


IDENTITY_FUNCTIONS: dict[str, IdentityFn] = {
    "graph_id": graph_id,
    "project": project,
    "project_contract": project_contract,
    "raw_contract_name": raw_contract_name,
}


def identity_sets(
    graphs_by_split: dict[str, tuple[ContractGraph, ...]],
    identity_fn: IdentityFn,
) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for split, graphs in graphs_by_split.items():
        vals = set()
        for graph in graphs:
            value = identity_fn(graph)
            if value:
                vals.add(value)
        out[split] = vals
    return out


def pairwise_overlaps(groups: dict[str, set[str]]) -> dict[str, dict[str, object]]:
    names = list(groups)
    out: dict[str, dict[str, object]] = {}
    for idx, left in enumerate(names):
        for right in names[idx + 1 :]:
            overlap = sorted(groups[left] & groups[right])
            out[f"{left}_vs_{right}"] = {
                "count": len(overlap),
                "examples": overlap[:10],
            }
    return out


def split_overlap_report(
    graphs_by_split: dict[str, tuple[ContractGraph, ...]],
) -> dict[str, dict[str, dict[str, object]]]:
    return {
        name: pairwise_overlaps(identity_sets(graphs_by_split, fn))
        for name, fn in IDENTITY_FUNCTIONS.items()
    }

