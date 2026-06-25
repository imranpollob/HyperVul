"""HyperVul hyperedge view builder.

This module is intentionally isolated from the RQ1 generic builders. Import it
explicitly only for RQ2 representation ablation and RQ3 HyperVul experiments.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from fair_eval.data.schemas import ContractGraph, GraphNode


@dataclass(frozen=True)
class HyperedgeMember:
    member_type: str
    text: str
    node_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HyperedgeExample:
    graph_id: str
    project: str
    contract: str
    source: str
    interaction_node_id: str
    function: str
    label: int
    is_cross_contract: bool
    function_member: HyperedgeMember
    state_members: tuple[HyperedgeMember, ...]
    callee_members: tuple[HyperedgeMember, ...]
    security_features: tuple[float, ...]
    vulnerability_type: str | None = None

    @property
    def members(self) -> tuple[HyperedgeMember, ...]:
        return (self.function_member,) + self.state_members + self.callee_members

    @property
    def member_count(self) -> int:
        return len(self.members)


def _state_members(node: GraphNode) -> tuple[HyperedgeMember, ...]:
    state_names = node.state_vars_accessed
    state_texts = node.state_texts or state_names
    members = []
    for idx, text in enumerate(state_texts):
        name = state_names[idx] if idx < len(state_names) else text
        members.append(
            HyperedgeMember(
                member_type="state",
                text=text,
                metadata={"name": name},
            )
        )
    return tuple(members)


def _callee_members(node: GraphNode) -> tuple[HyperedgeMember, ...]:
    callee_texts = node.callee_texts
    calls = node.external_calls
    if not callee_texts:
        callee_texts = tuple(str(call.get("call_text") or call) for call in calls)

    members = []
    for idx, text in enumerate(callee_texts):
        call = calls[idx] if idx < len(calls) else {}
        metadata = {
            "method": str(call.get("method", "")),
            "receiver": str(call.get("receiver", "")),
        }
        members.append(
            HyperedgeMember(
                member_type="callee",
                text=text,
                metadata=metadata,
            )
        )
    return tuple(members)


def build_hyperedge_examples(graphs: Iterable[ContractGraph]) -> tuple[HyperedgeExample, ...]:
    """Build one HyperVul hyperedge example per labeled interaction node."""

    examples: list[HyperedgeExample] = []
    for graph in graphs:
        for node in graph.interaction_nodes:
            if node.label not in (0, 1):
                continue
            function_text = node.function_source or node.function or ""
            examples.append(
                HyperedgeExample(
                    graph_id=graph.graph_id,
                    project=graph.project,
                    contract=graph.contract,
                    source=graph.source,
                    interaction_node_id=node.id,
                    function=node.function or "",
                    label=node.label,
                    is_cross_contract=node.is_cross_contract,
                    function_member=HyperedgeMember(
                        member_type="function",
                        text=function_text,
                        node_id=node.id,
                        metadata={"function": node.function or ""},
                    ),
                    state_members=_state_members(node),
                    callee_members=_callee_members(node),
                    security_features=node.security_vector,
                    vulnerability_type=str(node.raw.get("vtype")) if node.raw.get("vtype") else None,
                )
            )
    return tuple(examples)

