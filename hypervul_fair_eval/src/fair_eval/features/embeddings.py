"""Embedding lookup helpers for existing encoded contract graph artifacts."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import torch


def normalize_source(source: str) -> str:
    """Match the normalization used when `node_embeddings.pt` was created."""

    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"//.*", "", source)
    source = "".join(source.split())
    return source.lower()


def source_hash(source: str) -> str:
    return hashlib.sha256(normalize_source(source).encode("utf-8")).hexdigest()


class EmbeddingStore:
    def __init__(self, project_root: Path | str):
        root = Path(project_root)
        graph_dir = root / "data" / "contract_graphs"
        node_obj = torch.load(graph_dir / "node_embeddings.pt", map_location="cpu", weights_only=False)
        member_obj = torch.load(graph_dir / "member_embeddings.pt", map_location="cpu", weights_only=False)
        self.dim = int(node_obj["dim"])
        self.by_hash: dict[str, torch.Tensor] = node_obj["by_hash"]
        self.state: dict[str, torch.Tensor] = member_obj["state"]
        self.callee: dict[str, torch.Tensor] = member_obj["callee"]
        self.zero = torch.zeros(self.dim, dtype=torch.float32)

    def function_embedding(self, source: str) -> torch.Tensor:
        return self.by_hash.get(source_hash(source), self.zero).float()

    def state_embedding(self, text: str) -> torch.Tensor:
        return self.state.get(text, self.zero).float()

    def callee_embedding(self, text: str) -> torch.Tensor:
        return self.callee.get(text, self.zero).float()

