#!/usr/bin/env python3
"""Synthetic forward-pass checks for Step 5 model implementations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch


def add_src_to_path() -> None:
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


add_src_to_path()

from fair_eval.models import (  # noqa: E402
    FunctionFeaturesMLP,
    FunctionMLP,
    FunctionSequenceModel,
    GraphNodeClassifier,
    HyperVulEmbOnly,
    HyperVulFull,
    HyperVulModel,
    HyperedgeNN,
)


def assert_shape(name: str, tensor: torch.Tensor, expected: tuple[int, ...]) -> dict[str, object]:
    actual = tuple(tensor.shape)
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")
    return {"name": name, "shape": list(actual), "status": "pass"}


def run_smoke_tests() -> dict[str, object]:
    torch.manual_seed(42)
    checks: list[dict[str, object]] = []

    batch = 4
    embed_dim = 768
    scalar_dim = 9
    sym_dim = 8

    function_embeddings = torch.randn(batch, embed_dim)
    scalar_features = torch.randn(batch, scalar_dim)
    checks.append(assert_shape("FunctionMLP", FunctionMLP()(function_embeddings), (batch,)))
    checks.append(
        assert_shape(
            "FunctionFeaturesMLP",
            FunctionFeaturesMLP(scalar_dim=scalar_dim)(function_embeddings, scalar_features),
            (batch,),
        )
    )

    seq_batch, seq_len = 3, 7
    seq_embeddings = torch.randn(seq_batch, seq_len, embed_dim)
    seq_scalars = torch.randn(seq_batch, seq_len, scalar_dim)
    seq_mask = torch.ones(seq_batch, seq_len, dtype=torch.bool)
    seq_mask[1, -2:] = False
    checks.append(
        assert_shape(
            "FunctionSequenceModel",
            FunctionSequenceModel(scalar_dim=scalar_dim)(seq_embeddings, seq_mask, seq_scalars),
            (seq_batch, seq_len),
        )
    )

    node_count = 9
    edge_index = torch.tensor(
        [
            [0, 1, 2, 3, 4, 5, 6, 7],
            [1, 2, 3, 4, 5, 6, 7, 8],
        ],
        dtype=torch.long,
    )
    node_embeddings = torch.randn(node_count, embed_dim)
    node_scalars = torch.randn(node_count, scalar_dim)
    edge_type = torch.tensor([0, 1, 2, 0, 1, 2, 0, 1], dtype=torch.long)
    checks.append(
        assert_shape(
            "GraphNodeClassifier-gcn",
            GraphNodeClassifier(scalar_dim=scalar_dim, conv="gcn")(node_embeddings, edge_index, node_scalars),
            (node_count,),
        )
    )
    checks.append(
        assert_shape(
            "GraphNodeClassifier-rgcn",
            GraphNodeClassifier(scalar_dim=scalar_dim, conv="rgcn", edge_types=3)(
                node_embeddings,
                edge_index,
                node_scalars,
                edge_type=edge_type,
            ),
            (node_count,),
        )
    )
    checks.append(
        assert_shape(
            "GraphNodeClassifier-gat",
            GraphNodeClassifier(scalar_dim=scalar_dim, conv="gat")(node_embeddings, edge_index, node_scalars),
            (node_count,),
        )
    )

    incidence_node = torch.tensor([0, 1, 2, 2, 3, 4, 4, 5, 6], dtype=torch.long)
    incidence_edge = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2], dtype=torch.long)
    checks.append(
        assert_shape(
            "HyperedgeNN",
            HyperedgeNN()(torch.randn(7, embed_dim), incidence_node, incidence_edge, num_edges=3),
            (3,),
        )
    )

    hv_batch, members, states, callees = 2, 6, 2, 3
    member_embeddings = torch.randn(hv_batch, members, embed_dim)
    member_mask = torch.ones(hv_batch, members, dtype=torch.bool)
    symbolic = torch.randn(hv_batch, members, sym_dim)
    state_mask = torch.ones(hv_batch, states, dtype=torch.bool)
    callee_mask = torch.ones(hv_batch, callees, dtype=torch.bool)

    checks.append(
        assert_shape(
            "HyperVulEmbOnly",
            HyperVulEmbOnly()(member_embeddings, member_mask),
            (hv_batch,),
        )
    )
    checks.append(
        assert_shape(
            "HyperVulFull",
            HyperVulFull()(
                member_embeddings,
                member_mask,
                symbolic_features=symbolic,
                state_mask=state_mask,
                callee_mask=callee_mask,
            ),
            (hv_batch,),
        )
    )
    logits, localization = HyperVulModel()(
        member_embeddings,
        member_mask,
        symbolic_features=symbolic,
        state_mask=state_mask,
        callee_mask=callee_mask,
        return_localization=True,
    )
    checks.append(assert_shape("HyperVulModel-logits", logits, (hv_batch,)))
    if localization is None:
        raise AssertionError("HyperVulModel localization output is None")
    checks.append(assert_shape("HyperVulModel-tuple_attention", localization["tuple_attention"], (hv_batch, states, callees)))

    return {"status": "pass", "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = run_smoke_tests()
    out = args.output_dir / "model_smoke_tests.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print("Model smoke tests passed.")


if __name__ == "__main__":
    main()

