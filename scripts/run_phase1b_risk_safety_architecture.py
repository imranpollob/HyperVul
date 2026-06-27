#!/usr/bin/env python3
"""Phase 1B risk-vs-safety architecture and protected reentrancy review."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
FAIR_SRC = ROOT / "hypervul_fair_eval" / "src"
if str(FAIR_SRC) not in sys.path:
    sys.path.insert(0, str(FAIR_SRC))


def load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


phase0e = load_script_module("phase0e", ROOT / "scripts" / "run_phase0e_native_contract_mil.py")
phase1a = load_script_module("phase1a", ROOT / "scripts" / "run_phase1a_hard_negative_safety.py")

from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.models import HyperVulModel  # noqa: E402
from fair_eval.training import binary_metrics, positive_weight, select_threshold, set_global_seed  # noqa: E402


ARCH_VARIANTS = ("concat", "subtractive", "gated", "rule_suppression")
SAFETY_AUX_FEATURES = (
    "nonreentrant_modifier",
    "return_value_checked",
    "safe_erc20_wrapper",
    "try_catch_presence",
    "require_assert_guard_before_call",
)
SAFETY_INDEX = {name: idx for idx, name in enumerate(phase1a.SAFETY_FEATURES)}
SAFETY_AUX_INDICES = tuple(SAFETY_INDEX[name] for name in SAFETY_AUX_FEATURES)
STRONG_SAFETY_FEATURES = (
    "nonreentrant_modifier",
    "return_value_checked",
    "safe_erc20_wrapper",
    "try_catch_presence",
    "require_assert_guard_before_call",
    "state_update_before_external_call",
    "only_owner_or_access_control",
)
STRONG_SAFETY_INDICES = tuple(SAFETY_INDEX[name] for name in STRONG_SAFETY_FEATURES)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def line_for_pos(source: str, pos: int) -> int | None:
    if pos < 0:
        return None
    return source[:pos].count("\n") + 1


def first_call_line(source: str, node_safety) -> str:
    call_texts = []
    # The SafetyFeatureStore has source but not raw calls; use broad external-call patterns.
    for pattern in (r"\.\s*call\s*\(", r"\.\s*delegatecall\s*\(", r"\.\s*staticcall\s*\(", r"\.\s*send\s*\(", r"\.\s*transfer\s*\(", r"\.\s*safeTransfer(?:From)?\s*\("):
        m = re.search(pattern, source)
        if m:
            line = line_for_pos(source, m.start())
            text = source.splitlines()[line - 1].strip() if line else ""
            call_texts.append(f"L{line}: {text}")
            break
    return " | ".join(call_texts)


def first_state_update_line(source: str) -> str:
    for idx, line in enumerate(source.splitlines(), start=1):
        if re.search(r"(\w+(?:\[.*?\])?\s*(=|\+=|-=|\*=|/=|\+\+|--)|delete\s+\w+)", line) and "==" not in line:
            return f"L{idx}: {line.strip()}"
    return ""


def guard_evidence(source: str, safety_features: dict[str, float]) -> str:
    bits = []
    signature = source.split("{", 1)[0]
    if safety_features.get("nonreentrant_modifier"):
        bits.append("nonReentrant/modifier")
    if safety_features.get("require_assert_guard_before_call"):
        for idx, line in enumerate(source.splitlines(), start=1):
            lower = line.lower()
            if "require" in lower or "assert" in lower or "revert" in lower:
                bits.append(f"L{idx}: {line.strip()}")
                break
    if safety_features.get("only_owner_or_access_control"):
        bits.append(signature.strip())
    return " | ".join(bits)


def code_snippet(source: str, max_lines: int = 14) -> str:
    lines = source.splitlines()
    if not lines:
        return ""
    call_idx = 0
    for idx, line in enumerate(lines):
        if re.search(r"\.\s*(call|delegatecall|staticcall|send|transfer|safeTransfer|safeTransferFrom)\s*\(", line):
            call_idx = idx
            break
    start = max(0, call_idx - 5)
    end = min(len(lines), start + max_lines)
    return "\\n".join(f"{i + 1}: {lines[i].rstrip()}" for i in range(start, end))


def create_review_packet(safety: Any) -> list[dict[str, Any]]:
    taxonomy = [row for row in read_csv(REPORTS / "phase1a_false_positive_taxonomy.csv") if row["category"] == "protected reentrancy-like pattern"]
    rows = []
    for row in taxonomy:
        key = f"{row['graph_id']}::{row['interaction_id']}"
        item = safety.by_key.get(key)
        if not item:
            continue
        safety_bits = [name for name in phase1a.SAFETY_FEATURES if float(row.get(name, 0.0) or 0.0) > 0]
        rows.append(
            {
                "review_priority": "",
                "contract_id": row["graph_id"],
                "source_path": row["source_path"],
                "function_name": row["function"],
                "source_span": item.source_span,
                "predicted_score": float(row["score"]),
                "current_label": item.label,
                "vulnerability_type": "",
                "detected_safety_features": "|".join(safety_bits),
                "external_call_line": first_call_line(item.function_source, item),
                "state_update_line": first_state_update_line(item.function_source),
                "modifier_guard_evidence": guard_evidence(item.function_source, item.features),
                "code_snippet": code_snippet(item.function_source),
                "interaction_id": row["interaction_id"],
                "category": row["category"],
                "evidence": row["evidence"],
                "safety_feature_count": len(safety_bits),
            }
        )

    score_sorted = sorted(rows, key=lambda r: float(r["predicted_score"]), reverse=True)
    ambiguous = sorted(rows, key=lambda r: abs(float(r["predicted_score"]) - 0.5))
    weak = sorted(rows, key=lambda r: (int(r["safety_feature_count"]), -float(r["predicted_score"])))
    priority: dict[tuple[str, str], list[str]] = defaultdict(list)
    for label, subset in [
        ("top50_highest_score", score_sorted[:50]),
        ("top50_most_ambiguous", ambiguous[:50]),
        ("top50_weak_or_no_safety", weak[:50]),
    ]:
        for item in subset:
            priority[(item["contract_id"], item["interaction_id"])].append(label)
    for item in rows:
        item["review_priority"] = "|".join(priority.get((item["contract_id"], item["interaction_id"]), []))
    return rows


class RiskSafetyMILModel(nn.Module):
    def __init__(self, variant: str, pooling: str, dropout: float = 0.3, top_k: int = 3):
        super().__init__()
        if variant not in ARCH_VARIANTS:
            raise ValueError(variant)
        self.variant = variant
        self.pooling = pooling
        self.top_k = top_k
        self.risk_encoder = HyperVulModel(symbolic_dim=8, dropout=dropout, use_symbolic=True, use_localization=True, use_sequence_pool=True)
        risk_dim = self.risk_encoder.input_dim
        self.safety_encoder = nn.Sequential(nn.Linear(len(phase1a.SAFETY_FEATURES), 64), nn.ReLU(), nn.Dropout(dropout), nn.Linear(64, 64), nn.ReLU())
        self.concat_head = nn.Sequential(nn.Linear(risk_dim + 64, 128), nn.ReLU(), nn.Dropout(dropout), nn.Linear(128, 1))
        self.safety_strength = nn.Linear(64, 1)
        self.gate_head = nn.Linear(64, 1)
        self.rule_penalty = nn.Parameter(torch.tensor(1.0))
        self.safety_aux = nn.Linear(64, len(SAFETY_AUX_FEATURES))
        self.attention = nn.Sequential(nn.Linear(risk_dim + 64, 128), nn.Tanh(), nn.Linear(128, 1, bias=False))

    def forward(self, batch: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        members = batch["members"]
        batch_size, max_interactions, max_members, emb_dim = members.shape
        flat_valid = batch["interaction_mask"].reshape(-1)
        flat_members = members.reshape(batch_size * max_interactions, max_members, emb_dim)[flat_valid]
        flat_member_mask = batch["member_mask"].reshape(batch_size * max_interactions, max_members)[flat_valid]
        flat_symbolic_all = batch["symbolic"].reshape(batch_size * max_interactions, max_members, -1)[flat_valid]
        flat_risk_symbolic = flat_symbolic_all[:, :, :8]
        flat_safety_features = flat_symbolic_all[:, 0, 8:]
        flat_state_embeddings = batch["state_embeddings"].reshape(batch_size * max_interactions, batch["state_embeddings"].shape[2], emb_dim)[flat_valid]
        flat_callee_embeddings = batch["callee_embeddings"].reshape(batch_size * max_interactions, batch["callee_embeddings"].shape[2], emb_dim)[flat_valid]
        flat_state_symbolic = batch["state_symbolic"].reshape(batch_size * max_interactions, batch["state_symbolic"].shape[2], -1)[flat_valid][:, :, :8]
        flat_callee_symbolic = batch["callee_symbolic"].reshape(batch_size * max_interactions, batch["callee_symbolic"].shape[2], -1)[flat_valid][:, :, :8]
        flat_state_mask = batch["state_mask"].reshape(batch_size * max_interactions, batch["state_mask"].shape[2])[flat_valid]
        flat_callee_mask = batch["callee_mask"].reshape(batch_size * max_interactions, batch["callee_mask"].shape[2])[flat_valid]

        risk_logit, risk_rep = self.risk_encoder(
            flat_members,
            flat_member_mask,
            symbolic_features=flat_risk_symbolic,
            state_embeddings=flat_state_embeddings,
            callee_embeddings=flat_callee_embeddings,
            state_symbolic=flat_state_symbolic,
            callee_symbolic=flat_callee_symbolic,
            state_mask=flat_state_mask,
            callee_mask=flat_callee_mask,
            return_representation=True,
        )
        safety_rep = self.safety_encoder(flat_safety_features)
        safety_strength = nn.functional.softplus(self.safety_strength(safety_rep).squeeze(-1))
        if self.variant == "concat":
            flat_logits = self.concat_head(torch.cat([risk_rep, safety_rep], dim=-1)).squeeze(-1)
        elif self.variant == "subtractive":
            flat_logits = risk_logit - nn.functional.softplus(self.rule_penalty) * safety_strength
        elif self.variant == "gated":
            gate = torch.sigmoid(self.gate_head(safety_rep).squeeze(-1) - safety_strength)
            flat_logits = risk_logit * gate
        else:
            strong = (flat_safety_features[:, list(STRONG_SAFETY_INDICES)].sum(dim=1) > 0).float()
            flat_logits = risk_logit - nn.functional.softplus(self.rule_penalty) * strong

        flat_aux = self.safety_aux(safety_rep)
        logits = members.new_full((batch_size, max_interactions), -1e9)
        reps = members.new_zeros((batch_size, max_interactions, risk_rep.shape[-1] + safety_rep.shape[-1]))
        aux_logits = members.new_zeros((batch_size, max_interactions, len(SAFETY_AUX_FEATURES)))
        logits.reshape(-1)[flat_valid] = flat_logits
        reps.reshape(batch_size * max_interactions, -1)[flat_valid] = torch.cat([risk_rep, safety_rep], dim=-1)
        aux_logits.reshape(batch_size * max_interactions, -1)[flat_valid] = flat_aux
        mask = batch["interaction_mask"]

        if self.pooling == "mil_max":
            contract_logits = logits.masked_fill(~mask, -1e9).max(dim=1).values
        elif self.pooling == "mil_topk":
            masked = logits.masked_fill(~mask, -1e9)
            k = min(self.top_k, masked.shape[1])
            values = torch.topk(masked, k=k, dim=1).values
            valid_counts = mask.sum(dim=1).clamp_min(1).clamp_max(k).float()
            contract_logits = values.masked_fill(values < -1e8, 0.0).sum(dim=1) / valid_counts
        else:
            attn_scores = self.attention(reps).squeeze(-1).masked_fill(~mask, -1e9)
            weights = torch.softmax(attn_scores, dim=1).masked_fill(~mask, 0.0)
            contract_logits = (weights * logits.masked_fill(~mask, 0.0)).sum(dim=1)

        return {
            "contract_logits": contract_logits,
            "interaction_logits": logits,
            "interaction_mask": mask,
            "safety_aux_logits": aux_logits,
        }


def to_device(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    return {key: (value.to(device) if torch.is_tensor(value) else value) for key, value in batch.items()}


def safety_aux_labels(batch: dict[str, torch.Tensor]) -> torch.Tensor:
    safety = batch["symbolic"][:, :, 0, 8:]
    return safety[:, :, list(SAFETY_AUX_INDICES)].float()


def weighted_bce(logits: torch.Tensor, labels: torch.Tensor, pos_weight: torch.Tensor | None = None) -> torch.Tensor:
    if pos_weight is None:
        return nn.functional.binary_cross_entropy_with_logits(logits, labels.float())
    return nn.functional.binary_cross_entropy_with_logits(logits, labels.float(), pos_weight=pos_weight.reshape(1))


def train_epoch(model, loader, optimizer, contract_pos, interaction_pos, aux_weight, safety_aux_weight, device) -> float:
    model.train()
    losses = []
    for batch in loader:
        batch = to_device(batch, device)
        optimizer.zero_grad(set_to_none=True)
        out = model(batch)
        mask = out["interaction_mask"]
        contract_loss = weighted_bce(out["contract_logits"], batch["contract_labels"], contract_pos)
        interaction_loss = weighted_bce(out["interaction_logits"][mask], batch["interaction_labels"][mask], interaction_pos)
        aux_loss = nn.functional.binary_cross_entropy_with_logits(out["safety_aux_logits"][mask], safety_aux_labels(batch)[mask])
        loss = contract_loss + aux_weight * interaction_loss + safety_aux_weight * aux_loss
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else 0.0


@torch.no_grad()
def predict(model, loader, device) -> dict[str, Any]:
    return phase0e.predict(model, loader, device)


def train_predict(bags, embeddings, safety, run, variant, seed, epochs, batch_size, lr, dropout, aux_weight, safety_aux_weight, pooling):
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    datasets = {
        split: phase1a.SafetyContractDataset(rows, embeddings, safety, include_safety=True)
        for split, rows in bags.items()
    }
    loaders = {
        "train": DataLoader(datasets["train"], batch_size=batch_size, shuffle=True, collate_fn=phase1a.collate_contracts),
        "val": DataLoader(datasets["val"], batch_size=batch_size, shuffle=False, collate_fn=phase1a.collate_contracts),
        "test": DataLoader(datasets["test"], batch_size=batch_size, shuffle=False, collate_fn=phase1a.collate_contracts),
    }
    model = RiskSafetyMILModel(variant=variant, pooling=pooling, dropout=dropout).to(device)
    c_labels = torch.tensor([bag.contract_label for bag in bags["train"]], dtype=torch.float32)
    i_labels = torch.tensor([label for bag in bags["train"] for label in bag.interaction_labels], dtype=torch.float32)
    contract_pos = positive_weight(c_labels).to(device)
    interaction_pos = positive_weight(i_labels).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    history = []
    for epoch in range(1, epochs + 1):
        loss = train_epoch(model, loaders["train"], optimizer, contract_pos, interaction_pos, aux_weight, safety_aux_weight, device)
        if epoch == 1 or epoch == epochs:
            history.append({"epoch": epoch, "train_loss": loss})
    return {
        "run": run,
        "variant": variant,
        "seed": seed,
        "pooling": pooling,
        "history": history,
        "predictions": {split: predict(model, loader, device) for split, loader in loaders.items()},
    }


def metrics_for_policy(val_probs, val_labels, test_probs, test_labels, policy_name: str) -> dict[str, Any]:
    cfg = phase0e.THRESHOLD_POLICIES[policy_name]
    selection = select_threshold(val_probs, val_labels, policy=cfg["policy"], target_recall=cfg["target_recall"], target_precision=cfg["target_precision"])
    row = dict(binary_metrics(test_probs, test_labels, selection.threshold))
    row.update(
        {
            "threshold_policy": policy_name,
            "selection_policy": cfg["policy"],
            "threshold": selection.threshold,
            "validation_precision_at_threshold": selection.precision,
            "validation_recall_at_threshold": selection.recall,
        }
    )
    for target in (0.70, 0.80, 0.90):
        p_at_r, threshold, recall = phase0e.precision_at_validation_recall(val_probs, val_labels, test_probs, test_labels, target)
        row[f"test_precision_at_val_recall_{int(target * 100)}"] = p_at_r
        row[f"val_threshold_for_recall_{int(target * 100)}"] = threshold
        row[f"val_recall_at_threshold_{int(target * 100)}"] = recall
    return row


def add_metric_rows(result, contract_rows, loc_rows):
    run = result["run"]
    variant = result["variant"]
    seed = result["seed"]
    pooling = result["pooling"]
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]
    for policy in phase0e.THRESHOLD_POLICIES:
        row = metrics_for_policy(val["contract_probs"], val["contract_labels"], test["contract_probs"], test["contract_labels"], policy)
        row.update({"run": run, "variant": variant, "pooling": pooling, "seed": seed, "level": "contract"})
        contract_rows.append(row)
    loc = phase0e.localization_metrics(test)
    loc.update({"run": run, "variant": variant, "pooling": pooling, "seed": seed})
    loc_rows.append(loc)


def protected_fp_count(pred: dict[str, Any], safety: Any, threshold: float) -> int:
    count = 0
    for prob, label, meta in zip(pred["contract_probs"], pred["contract_labels"], pred["contract_meta"]):
        if int(label) != 0 or float(prob) < threshold:
            continue
        nodes = safety.by_graph.get(str(meta["graph_id"]), [])
        if any(node.category == "protected reentrancy-like pattern" for node in nodes):
            count += 1
    return count


def false_positive_reduction_rows(results: list[dict[str, Any]], safety: Any) -> list[dict[str, Any]]:
    rows = []
    baseline_counts: dict[tuple[str, int, str], int] = {}
    for result in results:
        val = result["predictions"]["val"]
        selection = select_threshold(val["contract_probs"], val["contract_labels"], policy="max_f1")
        for split in ("val", "test"):
            count = protected_fp_count(result["predictions"][split], safety, selection.threshold)
            key = (result["run"], result["seed"], split)
            if result["variant"] == "concat":
                baseline_counts[key] = count
            rows.append(
                {
                    "run": result["run"],
                    "variant": result["variant"],
                    "seed": result["seed"],
                    "split": split,
                    "threshold_from_val": selection.threshold,
                    "protected_reentrancy_false_positives": count,
                    "concat_baseline_protected_fp": "",
                    "protected_fp_reduction_vs_concat": "",
                }
            )
    for row in rows:
        key = (row["run"], int(row["seed"]), row["split"])
        base = baseline_counts.get(key)
        if base is not None:
            row["concat_baseline_protected_fp"] = base
            row["protected_fp_reduction_vs_concat"] = base - int(row["protected_reentrancy_false_positives"])
    return rows


def summarize(rows: list[dict[str, Any]], fields: list[str]) -> dict[str, tuple[float, float]]:
    out = {}
    for field in fields:
        vals = [float(row[field]) for row in rows if row.get(field) not in ("", None)]
        if vals:
            out[field] = (float(np.mean(vals)), float(np.std(vals)))
    return out


def fmt(stats: dict[str, tuple[float, float]], key: str) -> str:
    if key not in stats:
        return "n/a"
    return f"{stats[key][0] * 100:.2f} +/- {stats[key][1] * 100:.2f}"


def safety_ablation_rows(contract_rows: list[dict[str, Any]], fp_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for run, variant in sorted({(r["run"], r["variant"]) for r in contract_rows}):
        subset = [r for r in contract_rows if r["run"] == run and r["variant"] == variant and r["threshold_policy"] == "max_f1"]
        stats = summarize(subset, ["precision", "recall", "f1", "pr_auc"])
        fps = [r for r in fp_rows if r["run"] == run and r["variant"] == variant and r["split"] == "val"]
        reductions = [float(r["protected_fp_reduction_vs_concat"]) for r in fps if r.get("protected_fp_reduction_vs_concat") not in ("", None)]
        rows.append(
            {
                "run": run,
                "variant": variant,
                "safety_mechanism": variant,
                "safety_auxiliary_loss": "on",
                "precision_mean": stats.get("precision", (0.0, 0.0))[0],
                "recall_mean": stats.get("recall", (0.0, 0.0))[0],
                "f1_mean": stats.get("f1", (0.0, 0.0))[0],
                "pr_auc_mean": stats.get("pr_auc", (0.0, 0.0))[0],
                "mean_val_protected_fp_reduction_vs_concat": float(np.mean(reductions)) if reductions else 0.0,
            }
        )
    return rows


def write_report(counts, contract_rows, loc_rows, fp_rows, safety_rows):
    lines = ["# Phase 1B Risk-vs-Safety Architecture", ""]
    lines.append("No broad augmentation was used. Architecture selection is based on train/validation behavior; test is reported only after validation threshold selection.")
    lines.append("")
    lines.append("## Split Counts")
    lines.append("| Run | Split | Contracts | Positive | Negative |")
    lines.append("|---|---|---:|---:|---:|")
    for run, split_counts in counts.items():
        for split, item in split_counts.items():
            lines.append(f"| {run} | {split} | {item['contracts']} | {item['positive_contracts']} | {item['negative_contracts']} |")
    lines.append("")
    lines.append("## Contract Metrics")
    lines.append("Validation max-F1 threshold, mean +/- std over seeds.")
    lines.append("")
    lines.append("| Run | Variant | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for run, variant in sorted({(r["run"], r["variant"]) for r in contract_rows}):
        subset = [r for r in contract_rows if r["run"] == run and r["variant"] == variant and r["threshold_policy"] == "max_f1"]
        stats = summarize(subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        lines.append(f"| {run} | {variant} | {fmt(stats,'precision')} | {fmt(stats,'recall')} | {fmt(stats,'f1')} | {fmt(stats,'f2')} | {fmt(stats,'pr_auc')} | {fmt(stats,'roc_auc')} |")
    lines.append("")
    lines.append("## Localization Metrics")
    lines.append("| Run | Variant | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run, variant in sorted({(r["run"], r["variant"]) for r in loc_rows}):
        subset = [r for r in loc_rows if r["run"] == run and r["variant"] == variant]
        stats = summarize(subset, ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"])
        lines.append(f"| {run} | {variant} | {fmt(stats,'top1_hit')} | {fmt(stats,'top3_hit')} | {fmt(stats,'top5_hit')} | {fmt(stats,'mrr')} | {fmt(stats,'recall_at_1')} | {fmt(stats,'recall_at_3')} | {fmt(stats,'recall_at_5')} |")
    lines.append("")
    lines.append("## Protected False-Positive Reduction")
    for run in sorted({r["run"] for r in fp_rows}):
        vals = [float(r["protected_fp_reduction_vs_concat"]) for r in fp_rows if r["run"] == run and r["split"] == "val" and r.get("protected_fp_reduction_vs_concat") not in ("", None)]
        lines.append(f"- {run}: mean validation protected-FP reduction vs concat across variants/seeds = {np.mean(vals):.2f}." if vals else f"- {run}: no reduction rows.")
    best = max(safety_rows, key=lambda r: float(r["f1_mean"]), default=None)
    lines.append("")
    lines.append("## Final Recommendation")
    if best:
        lines.append(f"- Best architecture by F1: `{best['variant']}` on `{best['run']}`.")
    lines.append("- Use `phase1b_false_positive_reduction.csv` to verify whether protected reentrancy-like false positives decrease before choosing Phase 1C.")
    lines.append("- If suppression improves precision without recall collapse, Phase 1C should be targeted augmentation/contrastive training around protected-vs-vulnerable reentrancy. If it does not, prioritize label cleanup from the review packet.")
    (REPORTS / "phase1b_risk_safety_architecture_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--aux-weight", type=float, default=0.5)
    parser.add_argument("--safety-aux-weight", type=float, default=0.2)
    parser.add_argument("--variants", nargs="+", choices=ARCH_VARIANTS, default=list(ARCH_VARIANTS))
    args = parser.parse_args()

    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    REPORTS.mkdir(parents=True, exist_ok=True)
    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    safety = phase1a.SafetyFeatureStore(bundle)

    review_rows = create_review_packet(safety)
    write_csv(
        REPORTS / "phase1b_protected_reentrancy_review_packet.csv",
        review_rows,
        [
            "review_priority",
            "contract_id",
            "source_path",
            "function_name",
            "source_span",
            "predicted_score",
            "current_label",
            "vulnerability_type",
            "detected_safety_features",
            "external_call_line",
            "state_update_line",
            "modifier_guard_evidence",
            "code_snippet",
            "interaction_id",
            "category",
            "evidence",
            "safety_feature_count",
        ],
    )

    all_bags = phase0e.build_contract_bags(bundle)
    re_bags = phase0e.build_contract_bags(bundle, "reentrancy_only")
    runs = {
        "all_scope": {"bags": all_bags, "pooling": "mil_topk"},
        "reentrancy_only": {"bags": re_bags, "pooling": "mil_attention"},
    }
    counts = {run: phase0e.split_counts(cfg["bags"]) for run, cfg in runs.items()}
    print(f"Phase 1B counts: {counts}", flush=True)
    print(f"Protected reentrancy review rows: {len(review_rows)}", flush=True)

    contract_rows: list[dict[str, Any]] = []
    loc_rows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for run, cfg in runs.items():
        for variant in args.variants:
            for seed in args.seeds:
                print(f"Running {run} {variant} seed={seed} epochs={args.epochs}", flush=True)
                result = train_predict(
                    cfg["bags"],
                    embeddings,
                    safety,
                    run,
                    variant,
                    seed,
                    args.epochs,
                    args.batch_size,
                    args.lr,
                    args.dropout,
                    args.aux_weight,
                    args.safety_aux_weight,
                    cfg["pooling"],
                )
                results.append(result)
                add_metric_rows(result, contract_rows, loc_rows)
                print(f"  done {run} {variant} seed={seed}", flush=True)

    fp_rows = false_positive_reduction_rows(results, safety)
    safety_rows = safety_ablation_rows(contract_rows, fp_rows)

    metric_fields = [
        "run",
        "variant",
        "pooling",
        "seed",
        "level",
        "threshold_policy",
        "selection_policy",
        "threshold",
        "validation_precision_at_threshold",
        "validation_recall_at_threshold",
        "precision",
        "recall",
        "f1",
        "f2",
        "pr_auc",
        "roc_auc",
        "tp",
        "tn",
        "fp",
        "fn",
        "support",
        "positive_support",
        "negative_support",
        "test_precision_at_val_recall_70",
        "test_precision_at_val_recall_80",
        "test_precision_at_val_recall_90",
        "val_threshold_for_recall_70",
        "val_threshold_for_recall_80",
        "val_threshold_for_recall_90",
        "val_recall_at_threshold_70",
        "val_recall_at_threshold_80",
        "val_recall_at_threshold_90",
    ]
    write_csv(REPORTS / "phase1b_contract_metrics.csv", contract_rows, metric_fields)
    write_csv(REPORTS / "phase1b_localization_metrics.csv", loc_rows, ["run", "variant", "pooling", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"])
    write_csv(REPORTS / "phase1b_false_positive_reduction.csv", fp_rows, ["run", "variant", "seed", "split", "threshold_from_val", "protected_reentrancy_false_positives", "concat_baseline_protected_fp", "protected_fp_reduction_vs_concat"])
    write_csv(REPORTS / "phase1b_safety_ablation.csv", safety_rows, ["run", "variant", "safety_mechanism", "safety_auxiliary_loss", "precision_mean", "recall_mean", "f1_mean", "pr_auc_mean", "mean_val_protected_fp_reduction_vs_concat"])
    write_report(counts, contract_rows, loc_rows, fp_rows, safety_rows)
    summary = {
        "generated_at": "2026-06-27",
        "epochs": args.epochs,
        "seeds": args.seeds,
        "counts": counts,
        "review_packet_rows": len(review_rows),
        "safety_ablation": safety_rows,
    }
    (REPORTS / "phase1b_risk_safety_architecture_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Phase 1B reports to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
