"""Contract-level function sequence views for generic baselines."""

from __future__ import annotations

from collections.abc import Iterable

from fair_eval.data.schemas import ContractGraph

from .common import SequenceExample
from .function_view import _call_degrees, generic_scalar_features


def build_sequence_examples(
    graphs: Iterable[ContractGraph],
    include_helpers: bool = False,
) -> tuple[SequenceExample, ...]:
    """Build one ordered function sequence per contract graph.

    The order follows the existing node order in `data/contract_graphs`. Labels
    are `None` for helper nodes and for any unlabeled node.
    """

    sequences: list[SequenceExample] = []
    for graph in graphs:
        in_degree, out_degree = _call_degrees(graph)
        nodes = [
            node
            for node in graph.nodes
            if node.is_interaction or (include_helpers and node.kind == "helper")
        ]
        if not nodes:
            continue
        sequences.append(
            SequenceExample(
                graph_id=graph.graph_id,
                project=graph.project,
                contract=graph.contract,
                source=graph.source,
                node_ids=tuple(node.id for node in nodes),
                functions=tuple(node.function or "" for node in nodes),
                labels=tuple(node.label if node.label in (0, 1) else None for node in nodes),
                function_sources=tuple(node.function_source or "" for node in nodes),
                scalar_features=tuple(
                    generic_scalar_features(
                        node,
                        in_degree=in_degree.get(node.id, 0),
                        out_degree=out_degree.get(node.id, 0),
                    )
                    for node in nodes
                ),
            )
        )
    return tuple(sequences)

