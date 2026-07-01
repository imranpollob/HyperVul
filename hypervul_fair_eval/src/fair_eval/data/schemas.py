"""Canonical data schemas for existing contract graph artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GraphEdge:
    src: str
    dst: str
    etype: str
    direction: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "GraphEdge":
        return cls(
            src=str(raw["src"]),
            dst=str(raw["dst"]),
            etype=str(raw["etype"]),
            direction=str(raw["direction"]) if raw.get("direction") is not None else None,
        )


@dataclass(frozen=True)
class GraphNode:
    id: str
    kind: str
    function: str | None
    label: int | None = None
    tier: str | None = None
    is_cross_contract: bool = False
    state_vars_accessed: tuple[str, ...] = field(default_factory=tuple)
    external_calls: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    function_source: str | None = None
    state_texts: tuple[str, ...] = field(default_factory=tuple)
    callee_texts: tuple[str, ...] = field(default_factory=tuple)
    security_vector: tuple[float, ...] = field(default_factory=tuple)
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "GraphNode":
        label = raw.get("label")
        return cls(
            id=str(raw["id"]),
            kind=str(raw["kind"]),
            function=str(raw["function"]) if raw.get("function") is not None else None,
            label=int(label) if label in (0, 1, 0.0, 1.0) else None,
            tier=str(raw["tier"]) if raw.get("tier") is not None else None,
            is_cross_contract=bool(raw.get("is_cross_contract", False)),
            state_vars_accessed=tuple(str(x) for x in raw.get("state_vars_accessed", [])),
            external_calls=tuple(dict(x) for x in raw.get("external_calls", [])),
            function_source=str(raw["function_source"]) if raw.get("function_source") else None,
            state_texts=tuple(str(x) for x in raw.get("state_texts", [])),
            callee_texts=tuple(str(x) for x in raw.get("callee_texts", [])),
            security_vector=tuple(float(x) for x in raw.get("sec", [])),
            raw=dict(raw),
        )

    @property
    def is_interaction(self) -> bool:
        return self.kind == "interaction"

    @property
    def is_labeled(self) -> bool:
        return self.label in (0, 1)


@dataclass(frozen=True)
class ContractGraph:
    graph_id: str
    split: str
    source: str
    project: str
    contract: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ContractGraph":
        return cls(
            graph_id=str(raw["graph_id"]),
            split=str(raw["split"]),
            source=str(raw["source"]),
            project=str(raw["project"]),
            contract=str(raw["contract"]),
            nodes=tuple(GraphNode.from_dict(node) for node in raw.get("nodes", [])),
            edges=tuple(GraphEdge.from_dict(edge) for edge in raw.get("edges", [])),
            raw=dict(raw),
        )

    @property
    def interaction_nodes(self) -> tuple[GraphNode, ...]:
        return tuple(node for node in self.nodes if node.is_interaction)

    @property
    def labeled_interactions(self) -> tuple[GraphNode, ...]:
        return tuple(node for node in self.interaction_nodes if node.is_labeled)

    @property
    def positive_count(self) -> int:
        return sum(1 for node in self.labeled_interactions if node.label == 1)

    @property
    def negative_count(self) -> int:
        return sum(1 for node in self.labeled_interactions if node.label == 0)

