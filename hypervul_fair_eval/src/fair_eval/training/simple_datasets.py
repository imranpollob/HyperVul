"""Small PyTorch datasets for initial RQ1 function baselines."""

from __future__ import annotations

from collections.abc import Sequence

import torch
from torch.utils.data import Dataset

from fair_eval.builders.common import FunctionExample, GraphView, SequenceExample
from fair_eval.features import EmbeddingStore


SCALAR_FEATURE_KEYS = (
    "state_var_count",
    "external_call_count",
    "has_state_var",
    "has_external_call",
    "is_cross_contract",
    "function_source_chars",
    "function_source_lines",
    "callgraph_in_degree",
    "callgraph_out_degree",
)


def scalar_matrix(examples: Sequence[FunctionExample]) -> torch.Tensor:
    return torch.tensor(
        [
            [example.scalar_features.get(key, 0.0) for key in SCALAR_FEATURE_KEYS]
            for example in examples
        ],
        dtype=torch.float32,
    )


def scalar_standardizer(examples: Sequence[FunctionExample]) -> tuple[torch.Tensor, torch.Tensor]:
    matrix = scalar_matrix(examples)
    mean = matrix.mean(dim=0)
    std = matrix.std(dim=0).clamp_min(1e-6)
    return mean, std


class FunctionTensorDataset(Dataset):
    def __init__(
        self,
        examples: Sequence[FunctionExample],
        embeddings: EmbeddingStore,
        scalar_mean: torch.Tensor | None = None,
        scalar_std: torch.Tensor | None = None,
    ):
        self.examples = tuple(examples)
        self.embeddings = embeddings
        self.scalar_mean = scalar_mean
        self.scalar_std = scalar_std

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int):
        example = self.examples[idx]
        embedding = self.embeddings.function_embedding(example.function_source)
        scalars = torch.tensor(
            [example.scalar_features.get(key, 0.0) for key in SCALAR_FEATURE_KEYS],
            dtype=torch.float32,
        )
        if self.scalar_mean is not None and self.scalar_std is not None:
            scalars = (scalars - self.scalar_mean) / self.scalar_std
        label = torch.tensor(float(example.label), dtype=torch.float32)
        return embedding, scalars, label


class SequenceTensorDataset(Dataset):
    def __init__(
        self,
        sequences: Sequence[SequenceExample],
        embeddings: EmbeddingStore,
        scalar_mean: torch.Tensor | None = None,
        scalar_std: torch.Tensor | None = None,
    ):
        self.sequences = tuple(sequences)
        self.embeddings = embeddings
        self.scalar_mean = scalar_mean
        self.scalar_std = scalar_std

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int):
        sequence = self.sequences[idx]
        embeddings = torch.stack(
            [self.embeddings.function_embedding(source) for source in sequence.function_sources]
        )
        scalars = torch.tensor(
            [
                [features.get(key, 0.0) for key in SCALAR_FEATURE_KEYS]
                for features in sequence.scalar_features
            ],
            dtype=torch.float32,
        )
        if self.scalar_mean is not None and self.scalar_std is not None:
            scalars = (scalars - self.scalar_mean) / self.scalar_std
        labels = torch.tensor([label if label is not None else -1 for label in sequence.labels], dtype=torch.float32)
        label_mask = labels >= 0
        return embeddings, scalars, labels, label_mask


def collate_sequences(batch):
    max_len = max(item[0].shape[0] for item in batch)
    embed_dim = batch[0][0].shape[1]
    scalar_dim = batch[0][1].shape[1]
    bsz = len(batch)
    embeddings = torch.zeros(bsz, max_len, embed_dim)
    scalars = torch.zeros(bsz, max_len, scalar_dim)
    labels = torch.full((bsz, max_len), -1.0)
    mask = torch.zeros(bsz, max_len, dtype=torch.bool)
    label_mask = torch.zeros(bsz, max_len, dtype=torch.bool)
    for idx, (emb, sca, lab, lmask) in enumerate(batch):
        n = emb.shape[0]
        embeddings[idx, :n] = emb
        scalars[idx, :n] = sca
        labels[idx, :n] = lab
        mask[idx, :n] = True
        label_mask[idx, :n] = lmask
    return embeddings, scalars, labels, mask, label_mask


class GraphTensorDataset(Dataset):
    def __init__(
        self,
        graphs: Sequence[GraphView],
        embeddings: EmbeddingStore,
        scalar_mean: torch.Tensor | None = None,
        scalar_std: torch.Tensor | None = None,
    ):
        self.graphs = tuple(graphs)
        self.embeddings = embeddings
        self.scalar_mean = scalar_mean
        self.scalar_std = scalar_std

    def __len__(self) -> int:
        return len(self.graphs)

    def __getitem__(self, idx: int):
        graph = self.graphs[idx]
        node_index = {node.node_id: i for i, node in enumerate(graph.nodes)}
        embeddings = torch.stack(
            [self.embeddings.function_embedding(node.function_source) for node in graph.nodes]
        )
        scalars = torch.tensor(
            [
                [node.scalar_features.get(key, 0.0) for key in SCALAR_FEATURE_KEYS]
                for node in graph.nodes
            ],
            dtype=torch.float32,
        )
        if self.scalar_mean is not None and self.scalar_std is not None:
            scalars = (scalars - self.scalar_mean) / self.scalar_std
        labels = torch.tensor([node.label if node.label is not None else -1 for node in graph.nodes], dtype=torch.float32)
        label_mask = labels >= 0
        edges = [(node_index[e.src], node_index[e.dst], e.etype) for e in graph.edges if e.src in node_index and e.dst in node_index]
        if edges:
            edge_index = torch.tensor([[src for src, _, _ in edges], [dst for _, dst, _ in edges]], dtype=torch.long)
            edge_type = torch.tensor([EDGE_TYPE_IDS.get(etype, 0) for _, _, etype in edges], dtype=torch.long)
        else:
            edge_index = torch.zeros(2, 0, dtype=torch.long)
            edge_type = torch.zeros(0, dtype=torch.long)
        return embeddings, scalars, labels, label_mask, edge_index, edge_type


EDGE_TYPE_IDS = {"call": 0, "shared_state": 1, "shared_callee": 2}


def collate_graphs(batch):
    embeddings, scalars, labels, label_masks = [], [], [], []
    edge_indices, edge_types = [], []
    offset = 0
    for emb, sca, lab, lmask, edge_index, edge_type in batch:
        embeddings.append(emb)
        scalars.append(sca)
        labels.append(lab)
        label_masks.append(lmask)
        if edge_index.numel():
            edge_indices.append(edge_index + offset)
            edge_types.append(edge_type)
        offset += emb.shape[0]
    edge_index = torch.cat(edge_indices, dim=1) if edge_indices else torch.zeros(2, 0, dtype=torch.long)
    edge_type = torch.cat(edge_types) if edge_types else torch.zeros(0, dtype=torch.long)
    return (
        torch.cat(embeddings),
        torch.cat(scalars),
        torch.cat(labels),
        torch.cat(label_masks),
        edge_index,
        edge_type,
    )


def function_step_fn(model, batch, device):
    embedding, _scalars, labels = batch
    return model(embedding.to(device)), labels.to(device)


def function_features_step_fn(model, batch, device):
    embedding, scalars, labels = batch
    return model(embedding.to(device), scalars.to(device)), labels.to(device)


def sequence_step_fn(model, batch, device):
    embeddings, scalars, labels, mask, label_mask = batch
    logits = model(embeddings.to(device), mask.to(device), scalars.to(device))
    label_mask = label_mask.to(device)
    return logits[label_mask], labels.to(device)[label_mask]


def graph_step_fn(model, batch, device):
    embeddings, scalars, labels, label_mask, edge_index, edge_type = batch
    logits = model(
        embeddings.to(device),
        edge_index.to(device),
        scalars.to(device),
        edge_type=edge_type.to(device),
    )
    label_mask = label_mask.to(device)
    return logits[label_mask], labels.to(device)[label_mask]
