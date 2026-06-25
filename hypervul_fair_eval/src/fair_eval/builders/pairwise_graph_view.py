"""Generic pairwise graph views for RQ1 baselines.

This builder uses existing binary relations in `data/contract_graphs`:
function calls, shared state, and shared callee edges. It does not construct or
flatten HyperVul hyperedges.
"""

from __future__ import annotations

from collections.abc import Iterable

from fair_eval.data.schemas import ContractGraph

from .common import GraphEdgeView, GraphNodeView, GraphView
from .function_view import _call_degrees, generic_scalar_features


DEFAULT_EDGE_TYPES = frozenset({"call", "shared_state", "shared_callee"})


def build_pairwise_graph_views(
    graphs: Iterable[ContractGraph],
    edge_types: frozenset[str] = DEFAULT_EDGE_TYPES,
    include_helpers: bool = True,
) -> tuple[GraphView, ...]:
    """Build generic binary-relation graph views."""

    views: list[GraphView] = []
    for graph in graphs:
        allowed_nodes = {
            node.id
            for node in graph.nodes
            if node.is_interaction or (include_helpers and node.kind == "helper")
        }
        if not allowed_nodes:
            continue
        in_degree, out_degree = _call_degrees(graph)
        nodes = tuple(
            GraphNodeView(
                node_id=node.id,
                kind=node.kind,
                function=node.function,
                label=node.label if node.label in (0, 1) else None,
                function_source=node.function_source or "",
                scalar_features=generic_scalar_features(
                    node,
                    in_degree=in_degree.get(node.id, 0),
                    out_degree=out_degree.get(node.id, 0),
                ),
            )
            for node in graph.nodes
            if node.id in allowed_nodes
        )
        edges = tuple(
            GraphEdgeView(src=edge.src, dst=edge.dst, etype=edge.etype, direction=edge.direction)
            for edge in graph.edges
            if edge.etype in edge_types and edge.src in allowed_nodes and edge.dst in allowed_nodes
        )
        views.append(
            GraphView(
                graph_id=graph.graph_id,
                project=graph.project,
                contract=graph.contract,
                source=graph.source,
                nodes=nodes,
                edges=edges,
            )
        )
    return tuple(views)

