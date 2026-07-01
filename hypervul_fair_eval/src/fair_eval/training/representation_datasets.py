"""Datasets/collators for RQ2 representation ablation."""

from __future__ import annotations

from collections.abc import Sequence

import torch
from torch.utils.data import Dataset

from fair_eval.builders.hyperedge_view import HyperedgeExample
from fair_eval.features import EmbeddingStore


class HyperedgeTensorDataset(Dataset):
    def __init__(self, examples: Sequence[HyperedgeExample], embeddings: EmbeddingStore):
        self.examples = tuple(examples)
        self.embeddings = embeddings

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int):
        example = self.examples[idx]
        rows = [self.embeddings.function_embedding(example.function_member.text)]
        rows.extend(self.embeddings.state_embedding(member.text) for member in example.state_members)
        rows.extend(self.embeddings.callee_embedding(member.text) for member in example.callee_members)
        members = torch.stack(rows).float()
        label = torch.tensor(float(example.label), dtype=torch.float32)
        return members, label


def collate_set_pool(batch):
    max_members = max(members.shape[0] for members, _ in batch)
    dim = batch[0][0].shape[1]
    members_out = torch.zeros(len(batch), max_members, dim)
    mask = torch.zeros(len(batch), max_members, dtype=torch.bool)
    labels = torch.zeros(len(batch), dtype=torch.float32)
    for idx, (members, label) in enumerate(batch):
        n = members.shape[0]
        members_out[idx, :n] = members
        mask[idx, :n] = True
        labels[idx] = label
    return members_out, mask, labels


def _clique_edges(start: int, count: int) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for i in range(count):
        for j in range(count):
            if i != j:
                edges.append((start + i, start + j))
    return edges


def collate_pairwise(batch):
    node_features = []
    segment_ids = []
    labels = []
    edges: list[tuple[int, int]] = []
    offset = 0
    for edge_id, (members, label) in enumerate(batch):
        n = members.shape[0]
        node_features.append(members)
        segment_ids.extend([edge_id] * n)
        labels.append(label)
        edges.extend(_clique_edges(offset, n))
        offset += n
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.zeros(2, 0, dtype=torch.long)
    return (
        torch.cat(node_features),
        edge_index,
        torch.tensor(segment_ids, dtype=torch.long),
        torch.stack(labels).float(),
    )


def collate_hyperedge(batch):
    node_features = []
    incidence_node = []
    incidence_edge = []
    labels = []
    offset = 0
    for edge_id, (members, label) in enumerate(batch):
        n = members.shape[0]
        node_features.append(members)
        incidence_node.extend(range(offset, offset + n))
        incidence_edge.extend([edge_id] * n)
        labels.append(label)
        offset += n
    return (
        torch.cat(node_features),
        torch.tensor(incidence_node, dtype=torch.long),
        torch.tensor(incidence_edge, dtype=torch.long),
        torch.stack(labels).float(),
    )


def set_pool_step_fn(model, batch, device):
    members, mask, labels = batch
    return model(members.to(device), mask.to(device)), labels.to(device)


def pairwise_step_fn(model, batch, device):
    node_features, edge_index, segment_ids, labels = batch
    return (
        model(
            node_features.to(device),
            edge_index.to(device),
            segment_ids.to(device),
            int(labels.numel()),
        ),
        labels.to(device),
    )


def hyperedge_step_fn(model, batch, device):
    node_features, incidence_node, incidence_edge, labels = batch
    return (
        model(
            node_features.to(device),
            incidence_node.to(device),
            incidence_edge.to(device),
            int(labels.numel()),
        ),
        labels.to(device),
    )

