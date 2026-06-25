"""Datasets and losses for RQ3 HyperVul component ablation."""

from __future__ import annotations

from collections.abc import Sequence

import torch
import torch.nn as nn
from torch.utils.data import Dataset

from fair_eval.builders.hyperedge_view import HyperedgeExample
from fair_eval.features import EmbeddingStore


class HyperVulTensorDataset(Dataset):
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
        member_embeddings = torch.stack(rows).float()
        security = torch.tensor(example.security_features, dtype=torch.float32)
        return (
            member_embeddings,
            security,
            torch.tensor(len(example.state_members), dtype=torch.long),
            torch.tensor(len(example.callee_members), dtype=torch.long),
            torch.tensor(float(example.label), dtype=torch.float32),
        )


def collate_hypervul(batch):
    max_members = max(item[0].shape[0] for item in batch)
    max_states = max(int(item[2]) for item in batch)
    max_callees = max(int(item[3]) for item in batch)
    dim = batch[0][0].shape[1]
    sec_dim = batch[0][1].shape[0]
    bsz = len(batch)

    members = torch.zeros(bsz, max_members, dim)
    member_mask = torch.zeros(bsz, max_members, dtype=torch.bool)
    symbolic = torch.zeros(bsz, max_members, sec_dim)
    state_embeddings = torch.zeros(bsz, max_states, dim)
    callee_embeddings = torch.zeros(bsz, max_callees, dim)
    state_symbolic = torch.zeros(bsz, max_states, sec_dim)
    callee_symbolic = torch.zeros(bsz, max_callees, sec_dim)
    state_mask = torch.zeros(bsz, max_states, dtype=torch.bool)
    callee_mask = torch.zeros(bsz, max_callees, dtype=torch.bool)
    labels = torch.zeros(bsz, dtype=torch.float32)

    for idx, (member_embeddings, security, state_count, callee_count, label) in enumerate(batch):
        n = member_embeddings.shape[0]
        members[idx, :n] = member_embeddings
        member_mask[idx, :n] = True
        symbolic[idx, :n] = security.unsqueeze(0).expand(n, -1)
        if int(state_count):
            state_mask[idx, : int(state_count)] = True
            state_embeddings[idx, : int(state_count)] = member_embeddings[1 : 1 + int(state_count)]
            state_symbolic[idx, : int(state_count)] = security.unsqueeze(0).expand(int(state_count), -1)
        if int(callee_count):
            callee_mask[idx, : int(callee_count)] = True
            callee_start = 1 + int(state_count)
            callee_embeddings[idx, : int(callee_count)] = member_embeddings[callee_start : callee_start + int(callee_count)]
            callee_symbolic[idx, : int(callee_count)] = security.unsqueeze(0).expand(int(callee_count), -1)
        labels[idx] = label

    return (
        members,
        member_mask,
        symbolic,
        state_embeddings,
        callee_embeddings,
        state_symbolic,
        callee_symbolic,
        state_mask,
        callee_mask,
        labels,
    )


def hypervul_step_fn(model, batch, device):
    (
        members,
        member_mask,
        symbolic,
        state_embeddings,
        callee_embeddings,
        state_symbolic,
        callee_symbolic,
        state_mask,
        callee_mask,
        labels,
    ) = batch
    logits = model(
        members.to(device),
        member_mask.to(device),
        symbolic_features=symbolic.to(device),
        state_embeddings=state_embeddings.to(device),
        callee_embeddings=callee_embeddings.to(device),
        state_symbolic=state_symbolic.to(device),
        callee_symbolic=callee_symbolic.to(device),
        state_mask=state_mask.to(device),
        callee_mask=callee_mask.to(device),
    )
    return logits, labels.to(device)


class ProjectionHead(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 256, output_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return nn.functional.normalize(self.net(x), dim=-1)


class SupConLoss(nn.Module):
    """Supervised contrastive loss over binary labels."""

    def __init__(self, temperature: float = 0.1):
        super().__init__()
        self.temperature = temperature

    def forward(self, z: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        labels = labels.reshape(-1, 1)
        mask = torch.eq(labels, labels.T).float().to(z.device)
        logits = torch.matmul(z, z.T) / self.temperature
        logits = logits - logits.max(dim=1, keepdim=True).values.detach()
        logits_mask = torch.ones_like(mask) - torch.eye(mask.shape[0], device=z.device)
        mask = mask * logits_mask
        exp_logits = torch.exp(logits) * logits_mask
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp_min(1e-12))
        positive_count = mask.sum(dim=1)
        valid = positive_count > 0
        if not valid.any():
            return z.new_tensor(0.0)
        mean_log_prob_pos = (mask * log_prob).sum(dim=1)[valid] / positive_count[valid]
        return -mean_log_prob_pos.mean()
