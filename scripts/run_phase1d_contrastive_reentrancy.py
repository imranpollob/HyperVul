#!/usr/bin/env python3
"""Phase 1D manual acceptance packet and contrastive reentrancy training."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
REENTRANCY_GRAPH_DIR = ROOT / "data" / "contract_graphs_reentrancy_clean_v1"
PAIR_DIR = ROOT / "data" / "contrastive_pairs"
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
phase1b = load_script_module("phase1b", ROOT / "scripts" / "run_phase1b_risk_safety_architecture.py")

from fair_eval.data import load_dataset_bundle  # noqa: E402
from fair_eval.features import EmbeddingStore  # noqa: E402
from fair_eval.training import binary_metrics, positive_weight, select_threshold, set_global_seed  # noqa: E402


VARIANT = "gated"


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


def manual_action(row: dict[str, str]) -> str:
    label = row["proposed_cleaned_label"]
    if label == "confirmed_positive_reentrancy":
        return "accept_positive"
    if label == "confirmed_protected_negative":
        return "accept_negative"
    if label == "wrong_scope_or_other_vulnerability":
        return "wrong_scope"
    return "quarantine"


def create_manual_acceptance_packet() -> list[dict[str, Any]]:
    rows = read_csv(ROOT / "data" / "labels_clean_v1" / "reentrancy_reviewed_train_val.csv")
    keep_labels = {
        "confirmed_positive_reentrancy",
        "confirmed_protected_negative",
        "ambiguous_quarantine",
        "wrong_scope_or_other_vulnerability",
    }
    out = []
    for row in rows:
        if row["proposed_cleaned_label"] not in keep_labels:
            continue
        out.append(
            {
                "contract_id": row["contract_id"],
                "source_path": row["source_path"],
                "function_name": row["function_name"],
                "source_span": row["source_span"],
                "current_label": row["current_label"],
                "proposed_label": row["proposed_cleaned_label"],
                "risk_evidence": row["risk_evidence"],
                "protection_evidence": row["protection_evidence"],
                "code_snippet": row["code_snippet"],
                "confidence": row["confidence"],
                "recommended_action": manual_action(row),
                "interaction_id": row["interaction_id"],
                "split": row["split"],
            }
        )
    return out


def accepted_decision(row: dict[str, str], run: str) -> tuple[str, int | None]:
    label = row["proposed_cleaned_label"]
    confidence = row["confidence"]
    if label == "confirmed_positive_reentrancy" and confidence == "high":
        return "set_positive", 1
    if label == "confirmed_protected_negative" and confidence == "high":
        return "set_negative", 0
    if label == "wrong_scope_or_other_vulnerability":
        return ("ignore" if run == "reentrancy_only" else "set_negative"), (None if run == "reentrancy_only" else 0)
    if label in {"ambiguous_quarantine", "insufficient_evidence", "confirmed_positive_reentrancy", "confirmed_protected_negative"}:
        return "ignore", None
    return "keep", None


def accepted_bags(original_bags: dict[str, tuple[Any, ...]], reviews: list[dict[str, str]], run: str) -> tuple[dict[str, tuple[Any, ...]], list[dict[str, Any]]]:
    review_map = {(row["contract_id"], row["interaction_id"]): row for row in reviews}
    out: dict[str, list[Any]] = {"train": [], "val": [], "test": list(original_bags["test"])}
    view_rows = []
    for split in ("train", "val"):
        for bag in original_bags[split]:
            interactions = []
            labels = []
            pos_ids = []
            for example, old_label in zip(bag.interactions, bag.interaction_labels):
                row = review_map.get((bag.graph_id, example.interaction_node_id))
                action = "keep"
                new_label = int(old_label)
                proposed = ""
                confidence = ""
                if row:
                    proposed = row["proposed_cleaned_label"]
                    confidence = row["confidence"]
                    action, maybe_label = accepted_decision(row, run)
                    if action == "ignore":
                        view_rows.append({"run": run, "split": split, "graph_id": bag.graph_id, "interaction_id": example.interaction_node_id, "old_label": old_label, "new_label": "", "action": action, "proposed_label": proposed, "confidence": confidence})
                        continue
                    if maybe_label is not None:
                        new_label = maybe_label
                interactions.append(example)
                labels.append(new_label)
                if new_label == 1:
                    pos_ids.append(example.interaction_node_id)
                view_rows.append({"run": run, "split": split, "graph_id": bag.graph_id, "interaction_id": example.interaction_node_id, "old_label": old_label, "new_label": new_label, "action": action, "proposed_label": proposed, "confidence": confidence})
            if interactions:
                out[split].append(
                    replace(
                        bag,
                        interactions=tuple(interactions),
                        interaction_labels=tuple(labels),
                        contract_label=int(any(label == 1 for label in labels)),
                        positive_interaction_ids=tuple(pos_ids),
                    )
                )
    return {split: tuple(rows) for split, rows in out.items()}, view_rows


def make_scope_graph_files(reviews: list[dict[str, str]]) -> None:
    REENTRANCY_GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    scope = json.loads((GRAPH_DIR / "scope_views" / "reentrancy_only.json").read_text(encoding="utf-8"))
    review_map = {(row["contract_id"], row["interaction_id"]): row for row in reviews}
    for split in ("train", "val", "test"):
        original = json.loads((GRAPH_DIR / f"{split}.json").read_text(encoding="utf-8"))
        scope_rows = {row["graph_id"]: row for row in scope[split]}
        out = []
        for graph in original:
            if graph["graph_id"] not in scope_rows:
                continue
            graph = json.loads(json.dumps(graph))
            pos_ids = set(scope_rows[graph["graph_id"]].get("positive_interaction_ids", []))
            if split in {"train", "val"}:
                new_pos = set()
                for node in graph.get("nodes", []):
                    if node.get("kind") != "interaction":
                        continue
                    node["label"] = 1 if node.get("id") in pos_ids else 0
                    row = review_map.get((graph["graph_id"], node.get("id")))
                    if row:
                        action, maybe_label = accepted_decision(row, "reentrancy_only")
                        if action == "ignore":
                            node["label"] = None
                            node["tier"] = "REVIEW_IGNORE"
                        elif maybe_label is not None:
                            node["label"] = maybe_label
                            node["tier"] = "REVIEW_ACCEPTED_POS" if maybe_label == 1 else "REVIEW_ACCEPTED_NEG"
                    if node.get("label") == 1:
                        new_pos.add(node.get("id"))
                graph["positive_interaction_ids"] = sorted(new_pos)
                graph["contract_label"] = int(bool(new_pos))
            else:
                for node in graph.get("nodes", []):
                    if node.get("kind") == "interaction":
                        node["label"] = 1 if node.get("id") in pos_ids else 0
                graph["positive_interaction_ids"] = sorted(pos_ids)
                graph["contract_label"] = int(scope_rows[graph["graph_id"]].get("scope_label", 0))
            out.append(graph)
        (REENTRANCY_GRAPH_DIR / f"{split}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


def role_tokens(function: str) -> set[str]:
    function = function.lower()
    roles = set()
    for token in ("withdraw", "claim", "transfer", "send", "mint", "burn", "deposit", "stake", "unstake", "swap", "add", "remove"):
        if token in function:
            roles.add(token)
    return roles


def similarity(pos_item, neg_item) -> float:
    score = 0.0
    p_methods = set(pos_item.external_methods)
    n_methods = set(neg_item.external_methods)
    if p_methods & n_methods:
        score += 2.0
    p_risk = {k for k, v in pos_item.features.items() if v and k in {"state_update_after_external_call", "callee_user_controlled", "safe_erc20_wrapper", "return_value_checked"}}
    n_risk = {k for k, v in neg_item.features.items() if v and k in {"state_update_after_external_call", "callee_user_controlled", "safe_erc20_wrapper", "return_value_checked"}}
    score += len(p_risk & n_risk)
    score += len(role_tokens(pos_item.function) & role_tokens(neg_item.function))
    return score


def build_contrastive_pairs(bags: dict[str, tuple[Any, ...]], safety: Any, reviews: list[dict[str, str]], max_pairs: int = 500) -> list[dict[str, Any]]:
    accepted_neg_keys = {
        (row["contract_id"], row["interaction_id"])
        for row in reviews
        if row["proposed_cleaned_label"] == "confirmed_protected_negative" and row["confidence"] == "high" and row["split"] == "train"
    }
    positives = []
    negatives = []
    example_by_key = {}
    for bag in bags["train"]:
        for example, label in zip(bag.interactions, bag.interaction_labels):
            key = (bag.graph_id, example.interaction_node_id)
            item = safety.by_key.get(f"{bag.graph_id}::{example.interaction_node_id}")
            if not item:
                continue
            example_by_key[key] = {"bag": bag, "example": example, "safety": item}
            if int(label) == 1:
                positives.append(key)
            if key in accepted_neg_keys:
                negatives.append(key)
    pairs = []
    for neg_key in negatives:
        neg_item = example_by_key[neg_key]["safety"]
        ranked = sorted(
            ((similarity(example_by_key[pos_key]["safety"], neg_item), pos_key) for pos_key in positives),
            reverse=True,
        )
        for sim, pos_key in ranked[:3]:
            pairs.append(
                {
                    "positive_graph_id": pos_key[0],
                    "positive_interaction_id": pos_key[1],
                    "negative_graph_id": neg_key[0],
                    "negative_interaction_id": neg_key[1],
                    "similarity": sim,
                    "positive_function": example_by_key[pos_key]["safety"].function,
                    "negative_function": neg_item.function,
                    "negative_protection": "|".join(k for k, v in neg_item.features.items() if v),
                }
            )
            if len(pairs) >= max_pairs:
                return pairs
    return pairs


class PairDataset(Dataset):
    def __init__(self, pairs: list[dict[str, Any]], bags: dict[str, tuple[Any, ...]], embeddings: EmbeddingStore, safety: Any):
        self.pairs = pairs
        single_bags = {}
        for bag in bags["train"]:
            for example, label in zip(bag.interactions, bag.interaction_labels):
                single_bags[(bag.graph_id, example.interaction_node_id)] = replace(
                    bag,
                    interactions=(example,),
                    interaction_labels=(int(label),),
                    contract_label=int(label),
                    positive_interaction_ids=(example.interaction_node_id,) if int(label) == 1 else (),
                )
        self.pos_dataset = phase1a.SafetyContractDataset(tuple(single_bags[(p["positive_graph_id"], p["positive_interaction_id"])] for p in pairs), embeddings, safety, include_safety=True)
        self.neg_dataset = phase1a.SafetyContractDataset(tuple(single_bags[(p["negative_graph_id"], p["negative_interaction_id"])] for p in pairs), embeddings, safety, include_safety=True)

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int):
        return self.pos_dataset[idx], self.neg_dataset[idx]


def collate_pairs(batch):
    pos = [item[0] for item in batch]
    neg = [item[1] for item in batch]
    return phase1a.collate_contracts(pos), phase1a.collate_contracts(neg)


def to_device(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


def train_contrastive_epoch(model, contract_loader, pair_loader, optimizer, contract_pos, interaction_pos, aux_weight, safety_aux_weight, contrastive_weight, margin, device):
    model.train()
    losses = []
    for batch in contract_loader:
        batch = to_device(batch, device)
        optimizer.zero_grad(set_to_none=True)
        out = model(batch)
        mask = out["interaction_mask"]
        contract_loss = phase1b.weighted_bce(out["contract_logits"], batch["contract_labels"], contract_pos)
        interaction_loss = phase1b.weighted_bce(out["interaction_logits"][mask], batch["interaction_labels"][mask], interaction_pos)
        aux_loss = nn.functional.binary_cross_entropy_with_logits(out["safety_aux_logits"][mask], phase1b.safety_aux_labels(batch)[mask])
        loss = contract_loss + aux_weight * interaction_loss + safety_aux_weight * aux_loss
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    for pos_batch, neg_batch in pair_loader:
        pos_batch = to_device(pos_batch, device)
        neg_batch = to_device(neg_batch, device)
        optimizer.zero_grad(set_to_none=True)
        pos_out = model(pos_batch)
        neg_out = model(neg_batch)
        ranking = torch.relu(margin - pos_out["contract_logits"] + neg_out["contract_logits"]).mean()
        loss = contrastive_weight * ranking
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else 0.0


def train_predict_contrastive(bags, pairs, embeddings, safety, run, seed, args):
    set_global_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    datasets = {split: phase1a.SafetyContractDataset(rows, embeddings, safety, include_safety=True) for split, rows in bags.items()}
    loaders = {
        "train": DataLoader(datasets["train"], batch_size=args.batch_size, shuffle=True, collate_fn=phase1a.collate_contracts),
        "val": DataLoader(datasets["val"], batch_size=args.batch_size, shuffle=False, collate_fn=phase1a.collate_contracts),
        "test": DataLoader(datasets["test"], batch_size=args.batch_size, shuffle=False, collate_fn=phase1a.collate_contracts),
    }
    pair_dataset = PairDataset(pairs, bags, embeddings, safety)
    pair_loader = DataLoader(pair_dataset, batch_size=min(args.batch_size, 64), shuffle=True, collate_fn=collate_pairs)
    pooling = "mil_attention" if run == "reentrancy_only" else "mil_topk"
    model = phase1b.RiskSafetyMILModel(variant=VARIANT, pooling=pooling, dropout=args.dropout).to(device)
    c_labels = torch.tensor([bag.contract_label for bag in bags["train"]], dtype=torch.float32)
    i_labels = torch.tensor([label for bag in bags["train"] for label in bag.interaction_labels], dtype=torch.float32)
    contract_pos = positive_weight(c_labels).to(device)
    interaction_pos = positive_weight(i_labels).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    for _epoch in range(1, args.epochs + 1):
        train_contrastive_epoch(model, loaders["train"], pair_loader, optimizer, contract_pos, interaction_pos, args.aux_weight, args.safety_aux_weight, args.contrastive_weight, args.margin, device)
    return {
        "run": run,
        "variant": "contrastive",
        "seed": seed,
        "pooling": pooling,
        "predictions": {split: phase1b.predict(model, loader, device) for split, loader in loaders.items()},
    }


def metrics_for_policy(val_probs, val_labels, test_probs, test_labels, policy_name: str) -> dict[str, Any]:
    cfg = phase0e.THRESHOLD_POLICIES[policy_name]
    sel = select_threshold(val_probs, val_labels, policy=cfg["policy"], target_recall=cfg["target_recall"], target_precision=cfg["target_precision"])
    row = dict(binary_metrics(test_probs, test_labels, sel.threshold))
    row.update({"threshold_policy": policy_name, "selection_policy": cfg["policy"], "threshold": sel.threshold, "validation_precision_at_threshold": sel.precision, "validation_recall_at_threshold": sel.recall})
    return row


def add_rows(result, metric_rows, loc_rows):
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]
    for policy in phase0e.THRESHOLD_POLICIES:
        row = metrics_for_policy(val["contract_probs"], val["contract_labels"], test["contract_probs"], test["contract_labels"], policy)
        row.update({"run": result["run"], "method": result["variant"], "variant": VARIANT, "seed": result["seed"], "pooling": result["pooling"]})
        metric_rows.append(row)
    loc = phase0e.localization_metrics(test)
    loc.update({"run": result["run"], "method": result["variant"], "variant": VARIANT, "seed": result["seed"], "pooling": result["pooling"]})
    loc_rows.append(loc)


def add_phase1b_baseline(metric_rows, loc_rows):
    rows = read_csv(REPORTS / "phase1b_contract_metrics.csv")
    loc = read_csv(REPORTS / "phase1b_localization_metrics.csv")
    for row in rows:
        if row["variant"] == VARIANT and row["threshold_policy"] == "max_f1":
            out = dict(row)
            out["method"] = "phase1b_baseline"
            metric_rows.append(out)
    for row in loc:
        if row["variant"] == VARIANT:
            out = dict(row)
            out["method"] = "phase1b_baseline"
            loc_rows.append(out)


def protected_fp_count(pred, safety, threshold):
    count = 0
    for prob, label, meta in zip(pred["contract_probs"], pred["contract_labels"], pred["contract_meta"]):
        if int(label) != 0 or float(prob) < threshold:
            continue
        nodes = safety.by_graph.get(str(meta["graph_id"]), [])
        if any(node.category == "protected reentrancy-like pattern" for node in nodes):
            count += 1
    return count


def remaining_error_rows(results, safety):
    rows = []
    for result in results:
        val = result["predictions"]["val"]
        sel = select_threshold(val["contract_probs"], val["contract_labels"], policy="max_f1")
        for prob, label, meta in zip(result["predictions"]["test"]["contract_probs"], result["predictions"]["test"]["contract_labels"], result["predictions"]["test"]["contract_meta"]):
            pred = int(float(prob) >= sel.threshold)
            if pred == int(label):
                continue
            nodes = safety.by_graph.get(str(meta["graph_id"]), [])
            rows.append({
                "run": result["run"],
                "method": result["variant"],
                "seed": result["seed"],
                "error_type": "false_positive" if pred else "false_negative",
                "graph_id": meta["graph_id"],
                "contract": meta["contract"],
                "probability": float(prob),
                "threshold": sel.threshold,
                "protected_reentrancy_like": int(any(node.category == "protected reentrancy-like pattern" for node in nodes)),
            })
    return rows


def summarize(rows, keys):
    out = {}
    for key in keys:
        vals = [float(r[key]) for r in rows if r.get(key) not in ("", None)]
        if vals:
            out[key] = (float(np.mean(vals)), float(np.std(vals)))
    return out


def fmt(stats, key):
    return "n/a" if key not in stats else f"{stats[key][0] * 100:.2f} +/- {stats[key][1] * 100:.2f}"


def write_reports(reviews, pair_stats, re_metrics, all_metrics, loc_rows, errors):
    lines = ["# Phase 1D Manual Acceptance", ""]
    lines.append("No augmentation was used. The manual acceptance packet includes Phase 1C proposed labels, but the accepted training view only auto-accepts high-confidence decisions.")
    lines.append("")
    counts = Counter(row["recommended_action"] for row in reviews)
    lines.append("## Acceptance Packet")
    lines.append("| Recommended action | Count |")
    lines.append("|---|---:|")
    for action, count in counts.most_common():
        lines.append(f"| {action} | {count} |")
    lines.append("")
    lines.append("High-confidence accepted labels: protected negatives only. The 21 positive relabel candidates are medium confidence and remain manual-review candidates, not automatic training flips.")
    (REPORTS / "phase1d_manual_acceptance_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["# Phase 1D Contrastive Reentrancy Training", ""]
    lines.append("Comparison uses Phase 1B gated as the current best baseline, accepted-label training without contrastive loss, and accepted-label training with margin ranking loss.")
    lines.append("")
    lines.append("## Reentrancy Metrics")
    lines.append("| Method | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for method in sorted({r["method"] for r in re_metrics}):
        subset = [r for r in re_metrics if r["method"] == method and r.get("threshold_policy") == "max_f1"]
        stats = summarize(subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        lines.append(f"| {method} | {fmt(stats,'precision')} | {fmt(stats,'recall')} | {fmt(stats,'f1')} | {fmt(stats,'f2')} | {fmt(stats,'pr_auc')} | {fmt(stats,'roc_auc')} |")
    lines.append("")
    lines.append("## All-Scope Secondary Metrics")
    lines.append("| Method | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for method in sorted({r["method"] for r in all_metrics}):
        subset = [r for r in all_metrics if r["method"] == method and r.get("threshold_policy") == "max_f1"]
        stats = summarize(subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        lines.append(f"| {method} | {fmt(stats,'precision')} | {fmt(stats,'recall')} | {fmt(stats,'f1')} | {fmt(stats,'f2')} | {fmt(stats,'pr_auc')} | {fmt(stats,'roc_auc')} |")
    lines.append("")
    lines.append("## Pair Stats")
    for row in pair_stats:
        lines.append(f"- {row['split']}: {row['pairs']} pairs, {row['positive_examples']} vulnerable positives, {row['protected_negative_examples']} protected negatives.")
    lines.append("")
    lines.append("## Final Recommendation")
    lines.append("- Targeted augmentation is not safe until the 21 positive relabel candidates are manually accepted or rejected.")
    lines.append("- If contrastive training improves reentrancy precision without recall collapse, continue reentrancy-focused. Otherwise, stay in label cleanup/manual adjudication.")
    (REPORTS / "phase1d_contrastive_training_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--aux-weight", type=float, default=0.5)
    parser.add_argument("--safety-aux-weight", type=float, default=0.2)
    parser.add_argument("--contrastive-weight", type=float, default=0.5)
    parser.add_argument("--margin", type=float, default=0.5)
    args = parser.parse_args()

    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    REPORTS.mkdir(parents=True, exist_ok=True)
    PAIR_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    safety = phase1a.SafetyFeatureStore(bundle)
    review_rows = read_csv(ROOT / "data" / "labels_clean_v1" / "reentrancy_reviewed_train_val.csv")
    packet_rows = create_manual_acceptance_packet()
    write_csv(REPORTS / "phase1d_manual_acceptance_packet.csv", packet_rows, ["contract_id", "source_path", "function_name", "source_span", "current_label", "proposed_label", "risk_evidence", "protection_evidence", "code_snippet", "confidence", "recommended_action", "interaction_id", "split"])
    make_scope_graph_files(review_rows)

    re_original = phase0e.build_contract_bags(bundle, "reentrancy_only")
    all_original = phase0e.build_contract_bags(bundle)
    re_bags, re_view = accepted_bags(re_original, review_rows, "reentrancy_only")
    all_bags, all_view = accepted_bags(all_original, review_rows, "all_scope")
    pairs = build_contrastive_pairs(re_bags, safety, review_rows)
    (PAIR_DIR / "reentrancy_pairs_v1.json").write_text(json.dumps({"pairs": pairs}, indent=2), encoding="utf-8")
    pair_stats = [{
        "split": "train",
        "pairs": len(pairs),
        "positive_examples": len({(p["positive_graph_id"], p["positive_interaction_id"]) for p in pairs}),
        "protected_negative_examples": len({(p["negative_graph_id"], p["negative_interaction_id"]) for p in pairs}),
        "mean_similarity": float(np.mean([p["similarity"] for p in pairs])) if pairs else 0.0,
    }]
    write_csv(REPORTS / "phase1d_contrastive_pair_stats.csv", pair_stats, ["split", "pairs", "positive_examples", "protected_negative_examples", "mean_similarity"])

    metric_rows = []
    loc_rows = []
    add_phase1b_baseline(metric_rows, loc_rows)
    results = []
    for run, bags in {"reentrancy_only": re_bags, "all_scope": all_bags}.items():
        pooling = "mil_attention" if run == "reentrancy_only" else "mil_topk"
        for seed in args.seeds:
            print(f"Running accepted-label {run} seed={seed}", flush=True)
            accepted = phase1b.train_predict(bags, embeddings, safety, run, VARIANT, seed, args.epochs, args.batch_size, args.lr, args.dropout, args.aux_weight, args.safety_aux_weight, pooling)
            accepted["variant"] = "accepted_label_only"
            results.append(accepted)
            add_rows(accepted, metric_rows, loc_rows)
            print(f"Running contrastive {run} seed={seed}", flush=True)
            contrastive = train_predict_contrastive(bags, pairs, embeddings, safety, run, seed, args)
            results.append(contrastive)
            add_rows(contrastive, metric_rows, loc_rows)

    re_metrics = [r for r in metric_rows if r["run"] == "reentrancy_only"]
    all_metrics = [r for r in metric_rows if r["run"] == "all_scope"]
    metric_fields = ["run", "method", "variant", "pooling", "seed", "threshold_policy", "selection_policy", "threshold", "validation_precision_at_threshold", "validation_recall_at_threshold", "precision", "recall", "f1", "f2", "pr_auc", "roc_auc", "tp", "tn", "fp", "fn", "support", "positive_support", "negative_support"]
    write_csv(REPORTS / "phase1d_reentrancy_metrics.csv", re_metrics, metric_fields)
    write_csv(REPORTS / "phase1d_all_scope_secondary_metrics.csv", all_metrics, metric_fields)
    write_csv(REPORTS / "phase1d_localization_metrics.csv", loc_rows, ["run", "method", "variant", "pooling", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"])
    errors = remaining_error_rows(results, safety)
    write_csv(REPORTS / "phase1d_remaining_errors.csv", errors, ["run", "method", "seed", "error_type", "graph_id", "contract", "probability", "threshold", "protected_reentrancy_like"])
    write_reports(packet_rows, pair_stats, re_metrics, all_metrics, loc_rows, errors)
    summary = {
        "accepted_actions": Counter(row["recommended_action"] for row in packet_rows),
        "pair_stats": pair_stats,
        "accepted_view_actions": {"reentrancy_only": Counter(row["action"] for row in re_view), "all_scope": Counter(row["action"] for row in all_view)},
    }
    (REPORTS / "phase1d_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Phase 1D artifacts to {REPORTS}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
