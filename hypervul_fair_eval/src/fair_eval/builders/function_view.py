"""Function-level generic baseline views.

This builder is for RQ1 baselines that should not consume HyperVul hyperedges.
Each labeled interaction node becomes one function example.
"""

from __future__ import annotations

from collections.abc import Iterable

from fair_eval.data.schemas import ContractGraph, GraphNode

from .common import FunctionExample


def generic_scalar_features(node: GraphNode, in_degree: int = 0, out_degree: int = 0) -> dict[str, float]:
    """Generic, non-hyperedge scalar features for function baselines.

    Security-specific vectors are intentionally excluded from this baseline view.
    """

    external_calls = node.external_calls
    state_vars = node.state_vars_accessed
    source = node.function_source or ""
    return {
        "state_var_count": float(len(state_vars)),
        "external_call_count": float(len(external_calls)),
        "has_state_var": float(bool(state_vars)),
        "has_external_call": float(bool(external_calls)),
        "is_cross_contract": float(node.is_cross_contract),
        "function_source_chars": float(len(source)),
        "function_source_lines": float(source.count("\n") + 1 if source else 0),
        "callgraph_in_degree": float(in_degree),
        "callgraph_out_degree": float(out_degree),
    }


def _call_degrees(graph: ContractGraph) -> tuple[dict[str, int], dict[str, int]]:
    in_degree: dict[str, int] = {node.id: 0 for node in graph.nodes}
    out_degree: dict[str, int] = {node.id: 0 for node in graph.nodes}
    for edge in graph.edges:
        if edge.etype != "call":
            continue
        if edge.src in out_degree:
            out_degree[edge.src] += 1
        if edge.dst in in_degree:
            in_degree[edge.dst] += 1
    return in_degree, out_degree


def build_function_examples(graphs: Iterable[ContractGraph]) -> tuple[FunctionExample, ...]:
    examples: list[FunctionExample] = []
    for graph in graphs:
        in_degree, out_degree = _call_degrees(graph)
        for node in graph.interaction_nodes:
            if node.label not in (0, 1):
                continue
            examples.append(
                FunctionExample(
                    graph_id=graph.graph_id,
                    project=graph.project,
                    contract=graph.contract,
                    source=graph.source,
                    node_id=node.id,
                    function=node.function or "",
                    label=node.label,
                    function_source=node.function_source or "",
                    scalar_features=generic_scalar_features(
                        node,
                        in_degree=in_degree.get(node.id, 0),
                        out_degree=out_degree.get(node.id, 0),
                    ),
                )
            )
    return tuple(examples)

