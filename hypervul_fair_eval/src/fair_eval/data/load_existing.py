"""Load existing HyperVul artifacts into canonical typed structures."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schemas import ContractGraph


SPLITS = ("train", "val", "test")


@dataclass(frozen=True)
class DatasetBundle:
    project_root: Path
    graphs: dict[str, tuple[ContractGraph, ...]]
    clean_negatives: dict[str, tuple[dict[str, Any], ...]]

    @property
    def train_graphs(self) -> tuple[ContractGraph, ...]:
        return self.graphs["train"]

    @property
    def val_graphs(self) -> tuple[ContractGraph, ...]:
        return self.graphs["val"]

    @property
    def test_graphs(self) -> tuple[ContractGraph, ...]:
        return self.graphs["test"]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_contract_graph_split(path: Path) -> tuple[ContractGraph, ...]:
    raw_graphs = load_json(path)
    if not isinstance(raw_graphs, list):
        raise TypeError(f"Expected list in {path}, got {type(raw_graphs).__name__}")
    return tuple(ContractGraph.from_dict(graph) for graph in raw_graphs)


def load_contract_graph_splits(project_root: Path) -> dict[str, tuple[ContractGraph, ...]]:
    override = os.environ.get("HYPERVUL_GRAPH_DIR")
    base = Path(override).resolve() if override else project_root / "data" / "contract_graphs"
    graphs: dict[str, tuple[ContractGraph, ...]] = {}
    for split in SPLITS:
        path = base / f"{split}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        graphs[split] = load_contract_graph_split(path)
    return graphs


def canonical_clean_negative_paths(project_root: Path) -> dict[str, Path]:
    base = project_root / "experiments" / "latest1"
    return {
        "openzeppelin": base / "eval_clean_negatives_oz_features.json",
        "aave": base / "eval_clean_negatives_aave_split.json",
        "external_maker_bancor": base / "eval_clean_negatives_external.json",
        "liquity": base / "eval_clean_negatives_liquity.json",
    }


def load_clean_negatives(project_root: Path) -> dict[str, tuple[dict[str, Any], ...]]:
    pools: dict[str, tuple[dict[str, Any], ...]] = {}
    for name, path in canonical_clean_negative_paths(project_root).items():
        if not path.exists():
            pools[name] = tuple()
            continue
        records = load_json(path)
        if not isinstance(records, list):
            raise TypeError(f"Expected list in {path}, got {type(records).__name__}")
        pools[name] = tuple(dict(record) for record in records)
    return pools


def load_dataset_bundle(project_root: Path | str) -> DatasetBundle:
    root = Path(project_root).resolve()
    return DatasetBundle(
        project_root=root,
        graphs=load_contract_graph_splits(root),
        clean_negatives=load_clean_negatives(root),
    )
