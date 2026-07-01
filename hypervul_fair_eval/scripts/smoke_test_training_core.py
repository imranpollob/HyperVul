#!/usr/bin/env python3
"""Synthetic smoke test for Step 6 training/evaluation core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def add_src_to_path() -> None:
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


add_src_to_path()

from fair_eval.reporting import write_json_result, write_markdown_result  # noqa: E402
from fair_eval.training import (  # noqa: E402
    AsymmetricLoss,
    bce_with_logits_for_labels,
    binary_metrics,
    clean_negative_metrics,
    predict,
    select_threshold,
    set_global_seed,
    train_one_epoch,
)


class TinyClassifier(nn.Module):
    def __init__(self, dim: int = 6):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(dim, 12), nn.ReLU(), nn.Linear(12, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def step_fn(model: nn.Module, batch, device: torch.device):
    x, y = batch
    return model(x.to(device)), y.to(device)


def run_smoke(output_dir: Path) -> dict[str, object]:
    set_global_seed(123)
    device = torch.device("cpu")
    x = torch.randn(80, 6)
    y = (x[:, 0] + 0.5 * x[:, 1] > 0.5).long()
    # Force imbalance like the real task.
    y[:50] = 0
    y[50:56] = 1

    train_loader = DataLoader(TensorDataset(x[:60], y[:60]), batch_size=16, shuffle=True)
    val_loader = DataLoader(TensorDataset(x[60:], y[60:]), batch_size=8, shuffle=False)

    model = TinyClassifier().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = bce_with_logits_for_labels(y[:60], device=device)
    asl = AsymmetricLoss(pos_weight=torch.tensor([3.0]))
    _ = float(asl(torch.zeros(4), torch.tensor([0.0, 0.0, 1.0, 1.0])).item())

    epoch = train_one_epoch(model, train_loader, optimizer, loss_fn, step_fn, device)
    preds = predict(model, val_loader, step_fn, device)
    selection = select_threshold(preds.probs, preds.labels, policy="max_f2", steps=101)
    metrics = binary_metrics(preds.probs, preds.labels, selection.threshold)
    clean_metrics = clean_negative_metrics(preds.probs[preds.labels == 0], selection.threshold)

    result = {
        "title": "Training Core Smoke Test",
        "model": "TinyClassifier",
        "seed": 123,
        "epoch": {"loss": epoch.loss, "examples": epoch.examples},
        "threshold_selection": selection.__dict__,
        "metrics": metrics,
        "clean_negative_metrics": clean_metrics,
    }
    write_json_result(result, output_dir / "training_core_smoke_result.json")
    write_markdown_result(result, output_dir / "training_core_smoke_result.md")
    return {
        "status": "pass",
        "epoch_examples": epoch.examples,
        "threshold": selection.threshold,
        "metrics_keys": sorted(metrics),
        "result_files": [
            "training_core_smoke_result.json",
            "training_core_smoke_result.md",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = run_smoke(args.output_dir)
    out = args.output_dir / "training_core_smoke_tests.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print("Training core smoke test passed.")


if __name__ == "__main__":
    main()

