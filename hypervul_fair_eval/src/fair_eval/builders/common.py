"""Shared view records for generic baseline builders.

These records intentionally do not model HyperVul hyperedges. They expose
function-level and binary-graph views suitable for RQ1 generic baselines.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FunctionExample:
    graph_id: str
    project: str
    contract: str
    source: str
    node_id: str
    function: str
    label: int
    function_source: str
    scalar_features: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SequenceExample:
    graph_id: str
    project: str
    contract: str
    source: str
    node_ids: tuple[str, ...]
    functions: tuple[str, ...]
    labels: tuple[int | None, ...]
    function_sources: tuple[str, ...]
    scalar_features: tuple[dict[str, float], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GraphNodeView:
    node_id: str
    kind: str
    function: str | None
    label: int | None
    function_source: str
    scalar_features: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdgeView:
    src: str
    dst: str
    etype: str
    direction: str | None = None


@dataclass(frozen=True)
class GraphView:
    graph_id: str
    project: str
    contract: str
    source: str
    nodes: tuple[GraphNodeView, ...]
    edges: tuple[GraphEdgeView, ...]

    @property
    def labeled_node_count(self) -> int:
        return sum(1 for node in self.nodes if node.label in (0, 1))

    @property
    def positive_count(self) -> int:
        return sum(1 for node in self.nodes if node.label == 1)

    @property
    def negative_count(self) -> int:
        return sum(1 for node in self.nodes if node.label == 0)


def positive_rate(pos: int, neg: int) -> float:
    denom = pos + neg
    return round(100.0 * pos / denom, 4) if denom else 0.0

