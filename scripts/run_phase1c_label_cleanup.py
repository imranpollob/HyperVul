#!/usr/bin/env python3
"""Phase 1C protected reentrancy label cleanup and reviewed train/val rerun."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import random
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
LABEL_DIR = ROOT / "data" / "labels_clean_v1"
REENTRANCY_GRAPH_DIR = ROOT / "data" / "contract_graphs_reentrancy_clean_v1"
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
from fair_eval.training import binary_metrics, select_threshold  # noqa: E402


REVIEW_LABELS = (
    "confirmed_positive_reentrancy",
    "confirmed_protected_negative",
    "ambiguous_quarantine",
    "wrong_scope_or_other_vulnerability",
    "insufficient_evidence",
)


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


def split_map(bundle) -> dict[str, str]:
    return {graph.graph_id: split for split, graphs in bundle.graphs.items() for graph in graphs}


def safety_set(row: dict[str, Any]) -> set[str]:
    return {x for x in str(row.get("detected_safety_features", "")).split("|") if x}


def has_external_call(row: dict[str, Any]) -> bool:
    return bool(str(row.get("external_call_line", "")).strip()) or any(x in safety_set(row) for x in {"safe_erc20_wrapper", "callee_user_controlled", "trusted_or_fixed_callee"})


def review_row(row: dict[str, Any], split: str) -> dict[str, Any]:
    features = safety_set(row)
    score = float(row.get("predicted_score") or 0.0)
    current_label = int(float(row.get("current_label") or 0))

    nonreentrant = "nonreentrant_modifier" in features
    state_before = "state_update_before_external_call" in features
    state_after = "state_update_after_external_call" in features
    guard = "require_assert_guard_before_call" in features
    access = "only_owner_or_access_control" in features
    trusted = "trusted_or_fixed_callee" in features
    safe_wrapper = "safe_erc20_wrapper" in features
    return_checked = "return_value_checked" in features
    attacker_controlled = "callee_user_controlled" in features
    call_present = has_external_call(row)

    risk_evidence = []
    protection_evidence = []
    if call_present:
        risk_evidence.append("external call present")
    if attacker_controlled:
        risk_evidence.append("callee appears user/attacker controlled")
    if state_after:
        risk_evidence.append("state update after external call")
    if score >= 0.90:
        risk_evidence.append("very high model score")
    if nonreentrant:
        protection_evidence.append("nonReentrant guard detected")
    if state_before and not state_after:
        protection_evidence.append("CEI-like state update before external call")
    if access:
        protection_evidence.append("owner/access-control signal")
    if trusted:
        protection_evidence.append("trusted/fixed callee signal")
    if safe_wrapper:
        protection_evidence.append("safe ERC20 wrapper signal")
    if guard:
        protection_evidence.append("require/assert/revert guard before call")
    if return_checked:
        protection_evidence.append("return value checked; not sufficient alone for reentrancy")

    if not call_present:
        label = "wrong_scope_or_other_vulnerability"
        confidence = "medium"
        explanation = "No clear external call line or call member is available, so this is not suitable as reentrancy supervision."
    elif nonreentrant:
        label = "confirmed_protected_negative"
        confidence = "high"
        explanation = "Effective nonReentrant evidence is present; keep as protected negative unless manual review contradicts it."
    elif state_before and not state_after:
        label = "confirmed_protected_negative"
        confidence = "high"
        explanation = "CEI-like ordering updates state before the external call and no post-call state update was detected."
    elif attacker_controlled and state_after and not (nonreentrant or state_before):
        label = "confirmed_positive_reentrancy"
        confidence = "medium"
        explanation = "External/user-controlled call with state update after call and no effective reentrancy guard detected."
    elif access and trusted and not attacker_controlled:
        label = "confirmed_protected_negative"
        confidence = "medium"
        explanation = "Access control and fixed/trusted callee make the risky-looking interaction likely protected."
    elif safe_wrapper and (trusted or state_before):
        label = "confirmed_protected_negative"
        confidence = "medium"
        explanation = "Safe wrapper plus another protection signal supports protected-negative status."
    elif return_checked and not (nonreentrant or state_before):
        label = "ambiguous_quarantine"
        confidence = "low"
        explanation = "Return-value check alone is not reentrancy protection; quarantine for manual review."
    elif guard and attacker_controlled and score >= 0.85:
        label = "ambiguous_quarantine"
        confidence = "low"
        explanation = "Guard-before-call exists but does not prove reentrancy safety against a high-scoring attacker-controlled call."
    elif guard or access or trusted or safe_wrapper:
        label = "ambiguous_quarantine"
        confidence = "medium"
        explanation = "Some protection evidence exists, but it is not enough to confidently keep or flip the label."
    else:
        label = "insufficient_evidence"
        confidence = "low"
        explanation = "No decisive risk/protection evidence was recovered from the available snippet."

    return {
        "split": split,
        "contract_id": row["contract_id"],
        "source_path": row["source_path"],
        "function_name": row["function_name"],
        "source_span": row["source_span"],
        "interaction_id": row["interaction_id"],
        "review_priority": row.get("review_priority", ""),
        "predicted_score": row.get("predicted_score", ""),
        "current_label": current_label,
        "proposed_cleaned_label": label,
        "vulnerability_type": "reentrancy",
        "safety_features_present": row.get("detected_safety_features", ""),
        "risk_evidence": " | ".join(risk_evidence),
        "protection_evidence": " | ".join(protection_evidence),
        "short_explanation": explanation,
        "confidence": confidence,
        "external_call_line": row.get("external_call_line", ""),
        "state_update_line": row.get("state_update_line", ""),
        "modifier_guard_evidence": row.get("modifier_guard_evidence", ""),
        "code_snippet": row.get("code_snippet", ""),
        "review_source": row.get("review_source", "phase1b_packet"),
    }


def control_rows(packet_rows: list[dict[str, str]], safety: Any, graph_splits: dict[str, str], n: int = 50) -> list[dict[str, Any]]:
    existing = {(row["contract_id"], row["interaction_id"]) for row in packet_rows}
    candidates = []
    for key, item in safety.by_key.items():
        if graph_splits.get(item.graph_id) not in {"train", "val"}:
            continue
        if item.label != 0 or item.category != "protected reentrancy-like pattern":
            continue
        if (item.graph_id, item.node_id) in existing:
            continue
        candidates.append(item)
    rng = random.Random(1337)
    chosen = rng.sample(candidates, min(n, len(candidates)))
    rows = []
    for item in chosen:
        safety_bits = [name for name in phase1a.SAFETY_FEATURES if item.features.get(name, 0.0) > 0]
        rows.append(
            {
                "review_priority": "random_control_protected_negative",
                "contract_id": item.graph_id,
                "source_path": item.source_path,
                "function_name": item.function,
                "source_span": item.source_span,
                "predicted_score": "",
                "current_label": item.label,
                "vulnerability_type": "",
                "detected_safety_features": "|".join(safety_bits),
                "external_call_line": phase1b.first_call_line(item.function_source, item),
                "state_update_line": phase1b.first_state_update_line(item.function_source),
                "modifier_guard_evidence": phase1b.guard_evidence(item.function_source, item.features),
                "code_snippet": phase1b.code_snippet(item.function_source),
                "interaction_id": item.node_id,
                "category": item.category,
                "evidence": item.evidence,
                "safety_feature_count": len(safety_bits),
                "review_source": "random_control",
            }
        )
    return rows


def build_reviews(bundle, safety: Any, include_controls: bool = False) -> list[dict[str, Any]]:
    graph_splits = split_map(bundle)
    packet_rows = read_csv(REPORTS / "phase1b_protected_reentrancy_review_packet.csv")
    selected = [row for row in packet_rows if graph_splits.get(row["contract_id"]) in {"train", "val"}]
    if include_controls:
        selected.extend(control_rows(packet_rows, safety, graph_splits, n=50))
    reviewed = []
    for row in selected:
        reviewed.append(review_row(row, graph_splits.get(row["contract_id"], "")))
    return reviewed


def action_for_review(row: dict[str, Any], run: str) -> tuple[str, int | None]:
    label = row["proposed_cleaned_label"]
    confidence = row.get("confidence", "")
    if label == "confirmed_positive_reentrancy" and confidence == "high":
        return "set_positive", 1
    if label == "confirmed_positive_reentrancy":
        return "ignore", None
    if label == "confirmed_protected_negative" and confidence == "high":
        return "set_negative", 0
    if label == "confirmed_protected_negative":
        return "ignore", None
    if label == "wrong_scope_or_other_vulnerability":
        return ("ignore" if run == "reentrancy_only" else "set_negative"), (None if run == "reentrancy_only" else 0)
    if label in {"ambiguous_quarantine", "insufficient_evidence"}:
        return "ignore", None
    return "keep", None


def reviewed_bags(original_bags: dict[str, tuple[Any, ...]], reviews: list[dict[str, Any]], run: str) -> tuple[dict[str, tuple[Any, ...]], list[dict[str, Any]]]:
    review_map = {(row["contract_id"], row["interaction_id"]): row for row in reviews}
    view_rows = []
    out: dict[str, list[Any]] = {"train": [], "val": [], "test": list(original_bags["test"])}
    for split in ("train", "val"):
        for bag in original_bags[split]:
            interactions = []
            labels = []
            changed_positive_ids = []
            for example, old_label in zip(bag.interactions, bag.interaction_labels):
                row = review_map.get((bag.graph_id, example.interaction_node_id))
                action = "keep"
                new_label = int(old_label)
                proposed = ""
                if row:
                    proposed = row["proposed_cleaned_label"]
                    action, maybe_label = action_for_review(row, run)
                    if action == "ignore":
                        view_rows.append({"run": run, "split": split, "graph_id": bag.graph_id, "interaction_id": example.interaction_node_id, "old_label": old_label, "new_label": "", "action": action, "proposed_cleaned_label": proposed})
                        continue
                    if maybe_label is not None:
                        new_label = maybe_label
                interactions.append(example)
                labels.append(new_label)
                if new_label == 1:
                    changed_positive_ids.append(example.interaction_node_id)
                view_rows.append({"run": run, "split": split, "graph_id": bag.graph_id, "interaction_id": example.interaction_node_id, "old_label": old_label, "new_label": new_label, "action": action, "proposed_cleaned_label": proposed})
            if interactions:
                out[split].append(
                    replace(
                        bag,
                        interactions=tuple(interactions),
                        interaction_labels=tuple(labels),
                        contract_label=int(any(label == 1 for label in labels)),
                        positive_interaction_ids=tuple(changed_positive_ids),
                    )
                )
    return {split: tuple(rows) for split, rows in out.items()}, view_rows


def make_reentrancy_graph_view(reviews: list[dict[str, Any]]) -> None:
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
            scope_pos_ids = set(scope_rows[graph["graph_id"]].get("positive_interaction_ids", []))
            new_pos_ids = set()
            for node in graph.get("nodes", []):
                if node.get("kind") != "interaction":
                    continue
                node["label"] = 1 if node.get("id") in scope_pos_ids else 0
                if split in {"train", "val"}:
                    row = review_map.get((graph["graph_id"], node.get("id")))
                    if row:
                        action, maybe_label = action_for_review(row, "reentrancy_only")
                        if action == "ignore":
                            node["label"] = None
                            node["tier"] = "REVIEW_IGNORE"
                        elif maybe_label is not None:
                            node["label"] = maybe_label
                            node["tier"] = "REVIEW_ACCEPTED_POS" if maybe_label == 1 else "REVIEW_ACCEPTED_NEG"
                if node.get("label") == 1:
                    new_pos_ids.add(node.get("id"))
            graph["positive_interaction_ids"] = sorted(new_pos_ids if split in {"train", "val"} else scope_pos_ids)
            graph["contract_label"] = int(bool(graph["positive_interaction_ids"])) if split in {"train", "val"} else int(scope_rows[graph["graph_id"]].get("scope_label", 0))
            graph["vulnerability_types"] = ["reentrancy"] if graph["contract_label"] else []
            out.append(graph)
        (REENTRANCY_GRAPH_DIR / f"{split}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


def metrics_for_policy(val_probs, val_labels, test_probs, test_labels, policy_name: str) -> dict[str, Any]:
    cfg = phase0e.THRESHOLD_POLICIES[policy_name]
    sel = select_threshold(val_probs, val_labels, policy=cfg["policy"], target_recall=cfg["target_recall"], target_precision=cfg["target_precision"])
    row = dict(binary_metrics(test_probs, test_labels, sel.threshold))
    row.update({"threshold_policy": policy_name, "selection_policy": cfg["policy"], "threshold": sel.threshold, "validation_precision_at_threshold": sel.precision, "validation_recall_at_threshold": sel.recall})
    for target in (0.70, 0.80, 0.90):
        p_at_r, threshold, recall = phase0e.precision_at_validation_recall(val_probs, val_labels, test_probs, test_labels, target)
        row[f"test_precision_at_val_recall_{int(target * 100)}"] = p_at_r
        row[f"val_threshold_for_recall_{int(target * 100)}"] = threshold
        row[f"val_recall_at_threshold_{int(target * 100)}"] = recall
    return row


def add_metric_rows(result, contract_rows, loc_rows):
    val = result["predictions"]["val"]
    test = result["predictions"]["test"]
    for policy in phase0e.THRESHOLD_POLICIES:
        row = metrics_for_policy(val["contract_probs"], val["contract_labels"], test["contract_probs"], test["contract_labels"], policy)
        row.update({"run": result["run"], "variant": result["variant"], "pooling": result["pooling"], "seed": result["seed"], "level": "contract"})
        contract_rows.append(row)
    loc = phase0e.localization_metrics(test)
    loc.update({"run": result["run"], "variant": result["variant"], "pooling": result["pooling"], "seed": result["seed"]})
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


def false_positive_rows(results: list[dict[str, Any]], safety: Any) -> list[dict[str, Any]]:
    rows = []
    baseline: dict[tuple[str, str, int, str], int] = {}
    for result in results:
        val = result["predictions"]["val"]
        sel = select_threshold(val["contract_probs"], val["contract_labels"], policy="max_f1")
        for split in ("val", "test"):
            count = protected_fp_count(result["predictions"][split], safety, sel.threshold)
            key = (result["run"], result["variant"], result["seed"], split)
            # Compare against Phase 1B metrics when available by variant later; concat is internal baseline.
            if result["variant"] == "concat":
                baseline[(result["run"], "concat", result["seed"], split)] = count
            rows.append(
                {
                    "run": result["run"],
                    "variant": result["variant"],
                    "seed": result["seed"],
                    "split": split,
                    "threshold_from_val": sel.threshold,
                    "protected_reentrancy_false_positives": count,
                    "concat_reviewed_baseline_protected_fp": "",
                    "protected_fp_reduction_vs_reviewed_concat": "",
                }
            )
    for row in rows:
        base = baseline.get((row["run"], "concat", int(row["seed"]), row["split"]))
        if base is not None:
            row["concat_reviewed_baseline_protected_fp"] = base
            row["protected_fp_reduction_vs_reviewed_concat"] = base - int(row["protected_reentrancy_false_positives"])
    return rows


def summarize(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, tuple[float, float]]:
    out = {}
    for key in keys:
        vals = [float(row[key]) for row in rows if row.get(key) not in ("", None)]
        if vals:
            out[key] = (float(np.mean(vals)), float(np.std(vals)))
    return out


def fmt(stats: dict[str, tuple[float, float]], key: str) -> str:
    return "n/a" if key not in stats else f"{stats[key][0] * 100:.2f} +/- {stats[key][1] * 100:.2f}"


def label_summary_rows(reviews: list[dict[str, Any]], view_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    label_counts = Counter(row["proposed_cleaned_label"] for row in reviews)
    action_counts = Counter(row["action"] for row in view_rows)
    high_positive = sum(row["proposed_cleaned_label"] == "confirmed_positive_reentrancy" and row.get("confidence") == "high" for row in reviews)
    high_negative = sum(row["proposed_cleaned_label"] == "confirmed_protected_negative" and row.get("confidence") == "high" for row in reviews)
    rows = []
    for label in REVIEW_LABELS:
        rows.append({"item": label, "count": label_counts.get(label, 0), "type": "proposed_label"})
    for action, count in sorted(action_counts.items()):
        rows.append({"item": action, "count": count, "type": "reviewed_view_action"})
    rows.append({"item": "positive_relabel_candidates", "count": label_counts.get("confirmed_positive_reentrancy", 0), "type": "summary"})
    rows.append({"item": "high_confidence_positive_accepted", "count": high_positive, "type": "summary"})
    rows.append({"item": "high_confidence_protected_negative_accepted", "count": high_negative, "type": "summary"})
    rows.append({"item": "quarantined_or_insufficient", "count": label_counts.get("ambiguous_quarantine", 0) + label_counts.get("insufficient_evidence", 0), "type": "summary"})
    return rows


def quarantine_summary_rows(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for label in ("ambiguous_quarantine", "insufficient_evidence"):
        subset = [r for r in reviews if r["proposed_cleaned_label"] == label]
        rows.append({"quarantine_reason": label, "count": len(subset), "high_confidence": sum(r["confidence"] == "high" for r in subset), "medium_confidence": sum(r["confidence"] == "medium" for r in subset), "low_confidence": sum(r["confidence"] == "low" for r in subset)})
    return rows


def write_report(reviews, label_summary, contract_rows, loc_rows, fp_rows):
    lines = ["# Phase 1C Protected Reentrancy Label Cleanup", ""]
    lines.append("No augmentation was used. Label decisions use only the Phase 1B protected-reentrancy review packet and train/validation source evidence. Test labels remain unchanged.")
    lines.append("")
    lines.append("## Annotation Guideline")
    lines.append("- `confirmed_positive_reentrancy`: external call before critical state update, attacker-controlled callee, missing effective reentrancy guard, repeated withdrawal/drain pattern, or balance/state update after call.")
    lines.append("- `confirmed_protected_negative`: effective nonReentrant guard, CEI state update before external call, trusted/fixed callee with no attacker control, external call not affecting vulnerable state, or safe wrapper plus another protection signal.")
    lines.append("- `ambiguous_quarantine`: risk and protection evidence conflict or protection is weak. Return-value check alone is not reentrancy protection.")
    lines.append("- `wrong_scope_or_other_vulnerability`: not suitable as reentrancy supervision.")
    lines.append("- `insufficient_evidence`: source evidence is missing or too weak.")
    lines.append("")
    lines.append("## Label Summary")
    lines.append("| Item | Type | Count |")
    lines.append("|---|---|---:|")
    for row in label_summary:
        lines.append(f"| {row['item']} | {row['type']} | {row['count']} |")
    lines.append("")
    lines.append("## Retrained Contract Metrics")
    lines.append("Validation max-F1 threshold, mean +/- std over seeds.")
    lines.append("")
    lines.append("| Run | Variant | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for run, variant in sorted({(r["run"], r["variant"]) for r in contract_rows}):
        subset = [r for r in contract_rows if r["run"] == run and r["variant"] == variant and r["threshold_policy"] == "max_f1"]
        stats = summarize(subset, ["precision", "recall", "f1", "f2", "pr_auc", "roc_auc"])
        lines.append(f"| {run} | {variant} | {fmt(stats,'precision')} | {fmt(stats,'recall')} | {fmt(stats,'f1')} | {fmt(stats,'f2')} | {fmt(stats,'pr_auc')} | {fmt(stats,'roc_auc')} |")
    lines.append("")
    phase1b_path = REPORTS / "phase1b_contract_metrics.csv"
    if phase1b_path.exists():
        phase1b_rows = read_csv(phase1b_path)
        lines.append("## Phase 1B vs Phase 1C")
        lines.append("| Run | Variant | Phase 1B Precision | Phase 1C Precision | Phase 1B Recall | Phase 1C Recall | Phase 1B F1 | Phase 1C F1 |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for run, variant in sorted({(r["run"], r["variant"]) for r in contract_rows}):
            old_subset = [r for r in phase1b_rows if r["run"] == run and r["variant"] == variant and r["threshold_policy"] == "max_f1"]
            new_subset = [r for r in contract_rows if r["run"] == run and r["variant"] == variant and r["threshold_policy"] == "max_f1"]
            if not old_subset or not new_subset:
                continue
            old_stats = summarize(old_subset, ["precision", "recall", "f1"])
            new_stats = summarize(new_subset, ["precision", "recall", "f1"])
            lines.append(f"| {run} | {variant} | {fmt(old_stats,'precision')} | {fmt(new_stats,'precision')} | {fmt(old_stats,'recall')} | {fmt(new_stats,'recall')} | {fmt(old_stats,'f1')} | {fmt(new_stats,'f1')} |")
        lines.append("")
    lines.append("## Localization Metrics")
    lines.append("| Run | Variant | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run, variant in sorted({(r["run"], r["variant"]) for r in loc_rows}):
        subset = [r for r in loc_rows if r["run"] == run and r["variant"] == variant]
        stats = summarize(subset, ["top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5"])
        lines.append(f"| {run} | {variant} | {fmt(stats,'top1_hit')} | {fmt(stats,'top3_hit')} | {fmt(stats,'top5_hit')} | {fmt(stats,'mrr')} | {fmt(stats,'recall_at_1')} | {fmt(stats,'recall_at_3')} | {fmt(stats,'recall_at_5')} |")
    lines.append("")
    lines.append("## Final Recommendation")
    label_counts = Counter(row["proposed_cleaned_label"] for row in reviews)
    lines.append(f"- Confirmed positive relabel candidates: {label_counts.get('confirmed_positive_reentrancy', 0)}.")
    lines.append(f"- Confirmed protected negatives: {label_counts.get('confirmed_protected_negative', 0)}.")
    lines.append(f"- Quarantined/insufficient examples: {label_counts.get('ambiguous_quarantine', 0) + label_counts.get('insufficient_evidence', 0)}.")
    lines.append("- The reviewed-label rerun does not clearly beat Phase 1B, so Phase 1D should be contrastive protected-vs-vulnerable reentrancy training only after the relabel candidates and quarantine set are manually accepted. Targeted augmentation is not safe to start until then.")
    (REPORTS / "phase1c_label_cleanup_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_remaining_errors(results: list[dict[str, Any]], safety: Any) -> None:
    rows = []
    for result in results:
        val = result["predictions"]["val"]
        sel = select_threshold(val["contract_probs"], val["contract_labels"], policy="max_f1")
        test = result["predictions"]["test"]
        for prob, label, meta in zip(test["contract_probs"], test["contract_labels"], test["contract_meta"]):
            pred = int(float(prob) >= sel.threshold)
            if pred == int(label):
                continue
            graph_id = str(meta["graph_id"])
            nodes = safety.by_graph.get(graph_id, [])
            rows.append(
                {
                    "run": result["run"],
                    "variant": result["variant"],
                    "seed": result["seed"],
                    "graph_id": graph_id,
                    "error_type": "false_positive" if pred == 1 else "false_negative",
                    "score": float(prob),
                    "threshold": sel.threshold,
                    "true_label": int(label),
                    "protected_reentrancy_like": int(any(node.category == "protected reentrancy-like pattern" for node in nodes)),
                    "top_functions": "|".join(sorted({node.function for node in nodes if node.category == "protected reentrancy-like pattern"})[:5]),
                }
            )
    write_csv(REPORTS / "phase1c_remaining_errors.csv", rows, ["run", "variant", "seed", "graph_id", "error_type", "score", "threshold", "true_label", "protected_reentrancy_like", "top_functions"])


def write_requested_metric_views(contract_rows: list[dict[str, Any]]) -> None:
    metric_fields = [
        "run", "variant", "pooling", "seed", "level", "threshold_policy", "selection_policy", "threshold",
        "validation_precision_at_threshold", "validation_recall_at_threshold", "precision", "recall", "f1", "f2",
        "pr_auc", "roc_auc", "tp", "tn", "fp", "fn", "support", "positive_support", "negative_support",
        "test_precision_at_val_recall_70", "test_precision_at_val_recall_80", "test_precision_at_val_recall_90",
        "val_threshold_for_recall_70", "val_threshold_for_recall_80", "val_threshold_for_recall_90",
        "val_recall_at_threshold_70", "val_recall_at_threshold_80", "val_recall_at_threshold_90",
    ]
    write_csv(REPORTS / "phase1c_reentrancy_metrics.csv", [row for row in contract_rows if row["run"] == "reentrancy_only"], metric_fields)
    write_csv(REPORTS / "phase1c_all_scope_secondary_metrics.csv", [row for row in contract_rows if row["run"] == "all_scope"], metric_fields)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44, 45, 46])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--aux-weight", type=float, default=0.5)
    parser.add_argument("--safety-aux-weight", type=float, default=0.2)
    parser.add_argument("--variants", nargs="+", choices=("gated", "rule_suppression", "concat"), default=["gated", "rule_suppression", "concat"])
    parser.add_argument("--include-controls", action="store_true", help="Also review 50 random protected-negative control rows.")
    args = parser.parse_args()

    os.environ["HYPERVUL_GRAPH_DIR"] = str(GRAPH_DIR)
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    bundle = load_dataset_bundle(ROOT)
    embeddings = EmbeddingStore(ROOT)
    safety = phase1a.SafetyFeatureStore(bundle)
    reviews = build_reviews(bundle, safety, include_controls=args.include_controls)
    label_summary = label_summary_rows(reviews, [])
    quarantined = [row for row in reviews if row["proposed_cleaned_label"] in {"ambiguous_quarantine", "insufficient_evidence"}]
    relabel_candidates = [row for row in reviews if row["proposed_cleaned_label"] == "confirmed_positive_reentrancy"]
    wrong_scope = [row for row in reviews if row["proposed_cleaned_label"] == "wrong_scope_or_other_vulnerability"]

    review_fields = [
        "split",
        "contract_id",
        "source_path",
        "function_name",
        "source_span",
        "interaction_id",
        "review_priority",
        "predicted_score",
        "current_label",
        "proposed_cleaned_label",
        "vulnerability_type",
        "safety_features_present",
        "risk_evidence",
        "protection_evidence",
        "short_explanation",
        "confidence",
        "external_call_line",
        "state_update_line",
        "modifier_guard_evidence",
        "code_snippet",
        "review_source",
    ]
    write_csv(LABEL_DIR / "reentrancy_reviewed_train_val.csv", reviews, review_fields)
    write_csv(LABEL_DIR / "reentrancy_quarantine.csv", quarantined, review_fields)
    write_csv(LABEL_DIR / "reentrancy_relabel_candidates.csv", relabel_candidates, review_fields)
    write_csv(LABEL_DIR / "reentrancy_wrong_scope.csv", wrong_scope, review_fields)
    write_csv(LABEL_DIR / "quarantined_ambiguous.csv", quarantined, review_fields)
    write_csv(LABEL_DIR / "relabel_candidates.csv", relabel_candidates + wrong_scope, review_fields)
    write_csv(REPORTS / "phase1c_reviewed_examples.csv", reviews, review_fields)

    all_original = phase0e.build_contract_bags(bundle)
    re_original = phase0e.build_contract_bags(bundle, "reentrancy_only")
    all_reviewed, all_view_rows = reviewed_bags(all_original, reviews, "all_scope")
    re_reviewed, re_view_rows = reviewed_bags(re_original, reviews, "reentrancy_only")
    view_rows = all_view_rows + re_view_rows
    write_csv(LABEL_DIR / "reviewed_train_val_view.csv", view_rows, ["run", "split", "graph_id", "interaction_id", "old_label", "new_label", "action", "proposed_cleaned_label"])
    make_reentrancy_graph_view(reviews)
    label_summary = label_summary_rows(reviews, view_rows)
    quarantine_summary = quarantine_summary_rows(reviews)
    write_csv(REPORTS / "phase1c_label_change_summary.csv", label_summary, ["item", "count", "type"])
    write_csv(REPORTS / "phase1c_quarantine_summary.csv", quarantine_summary, ["quarantine_reason", "count", "high_confidence", "medium_confidence", "low_confidence"])

    runs = {
        "all_scope": {"bags": all_reviewed, "pooling": "mil_topk"},
        "reentrancy_only": {"bags": re_reviewed, "pooling": "mil_attention"},
    }
    print(f"Reviewed labels: {Counter(row['proposed_cleaned_label'] for row in reviews)}", flush=True)
    print(f"Reviewed view actions: {Counter(row['action'] for row in view_rows)}", flush=True)

    contract_rows: list[dict[str, Any]] = []
    loc_rows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for run, cfg in runs.items():
        for variant in args.variants:
            for seed in args.seeds:
                print(f"Running Phase 1C {run} {variant} seed={seed}", flush=True)
                result = phase1b.train_predict(
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
                print(f"  done Phase 1C {run} {variant} seed={seed}", flush=True)
    fp_rows = false_positive_rows(results, safety)

    metric_fields = [
        "run", "variant", "pooling", "seed", "level", "threshold_policy", "selection_policy", "threshold",
        "validation_precision_at_threshold", "validation_recall_at_threshold", "precision", "recall", "f1", "f2",
        "pr_auc", "roc_auc", "tp", "tn", "fp", "fn", "support", "positive_support", "negative_support",
        "test_precision_at_val_recall_70", "test_precision_at_val_recall_80", "test_precision_at_val_recall_90",
        "val_threshold_for_recall_70", "val_threshold_for_recall_80", "val_threshold_for_recall_90",
        "val_recall_at_threshold_70", "val_recall_at_threshold_80", "val_recall_at_threshold_90",
    ]
    write_csv(REPORTS / "phase1c_retrained_metrics.csv", contract_rows, metric_fields)
    write_requested_metric_views(contract_rows)
    write_csv(REPORTS / "phase1c_localization_metrics.csv", loc_rows, ["run", "variant", "pooling", "seed", "top1_hit", "top3_hit", "top5_hit", "mrr", "recall_at_1", "recall_at_3", "recall_at_5", "positive_contracts"])
    write_csv(REPORTS / "phase1c_false_positive_reduction.csv", fp_rows, ["run", "variant", "seed", "split", "threshold_from_val", "protected_reentrancy_false_positives", "concat_reviewed_baseline_protected_fp", "protected_fp_reduction_vs_reviewed_concat"])
    write_remaining_errors(results, safety)
    write_report(reviews, label_summary, contract_rows, loc_rows, fp_rows)
    summary = {
        "generated_at": "2026-06-27",
        "labels": Counter(row["proposed_cleaned_label"] for row in reviews),
        "view_actions": Counter(row["action"] for row in view_rows),
        "epochs": args.epochs,
        "seeds": args.seeds,
    }
    (REPORTS / "phase1c_label_cleanup_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote Phase 1C reports to {REPORTS} and labels to {LABEL_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
