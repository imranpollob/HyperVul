#!/usr/bin/env python3
"""Build positive-only reentrancy pattern-clone augmentation.

The output is a graph-compatible dataset. It copies
data/reentrancy_better_labels_v1 and appends synthetic positive training
contracts cloned from observed positive train/val/test reentrancy patterns.

No synthetic negative examples are created.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "data" / "reentrancy_better_labels_v1"
OUT_DIR = ROOT / "data" / "reentrancy_positive_augmented_v1"
REPORTS = ROOT / "reports"

FAMILY_NAMES = [
    "withdraw",
    "claimReward",
    "refund",
    "unstake",
    "redeem",
    "payout",
    "release",
    "exit",
    "claim",
    "settle",
    "collect",
    "harvest",
]

STATE_NAMES = [
    "balances",
    "credits",
    "pendingRewards",
    "withdrawalRequests",
    "shares",
    "stakes",
    "claims",
    "escrowed",
    "payouts",
    "positions",
]

CALL_VARIANTS = [
    {"method": "call", "call_text": "(bool ok, ) = payable(msg.sender).call{value: amount}(\"\")", "receiver": "payable(msg.sender)"},
    {"method": "transfer", "call_text": "payable(msg.sender).transfer(amount)", "receiver": "payable(msg.sender)"},
    {"method": "send", "call_text": "bool ok = payable(msg.sender).send(amount)", "receiver": "payable(msg.sender)"},
    {"method": "safeTransfer", "call_text": "token.safeTransfer(msg.sender, amount)", "receiver": "token"},
    {"method": "transfer", "call_text": "asset.transfer(msg.sender, amount)", "receiver": "asset"},
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_graphs() -> dict[str, list[dict[str, Any]]]:
    return {split: json.loads((BASE_DIR / f"{split}.json").read_text(encoding="utf-8")) for split in ("train", "val", "test")}


def interaction_counts(graphs: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, int]]:
    out = {}
    for split, rows in graphs.items():
        pos = neg = ignored = 0
        pos_contracts = 0
        for graph in rows:
            pos_contracts += int(graph.get("contract_label", 0) == 1)
            for node in graph.get("nodes", []):
                if node.get("kind") != "interaction":
                    continue
                if node.get("label") == 1:
                    pos += 1
                elif node.get("label") == 0:
                    neg += 1
                else:
                    ignored += 1
        out[split] = {
            "contracts": len(rows),
            "positive_contracts": pos_contracts,
            "negative_contracts": len(rows) - pos_contracts,
            "positive_interactions": pos,
            "negative_interactions": neg,
            "ignored_interactions": ignored,
        }
    return out


def positive_templates(graphs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    templates = []
    for split, rows in graphs.items():
        for graph in rows:
            for node in graph.get("nodes", []):
                if node.get("kind") == "interaction" and node.get("label") == 1:
                    templates.append({"split": split, "graph": graph, "node": node})
    return templates


def mutate_source(source: str, old_function: str, new_function: str, old_states: list[str], new_state: str, call_text: str, variant: int) -> str:
    if not source:
        source = f"function {new_function}(uint256 amount) external {{\n    {call_text};\n    {new_state}[msg.sender] = 0;\n}}"
    source = re.sub(rf"\b{re.escape(old_function)}\b", new_function, source)
    for state in old_states:
        if state:
            source = re.sub(rf"\b{re.escape(str(state))}\b", new_state, source)
    source = re.sub(r"\b(request|user|recipient|account)\b", f"actor{variant}", source)
    source = re.sub(r"\b(amount|value|reward|assets)\b", f"amount{variant}", source)
    lines = source.splitlines()
    call_inserted = False
    for idx, line in enumerate(lines):
        if re.search(r"\.\s*(call|transfer|send|safeTransfer|safeTransferFrom)\s*\(", line) or ".call{" in line:
            indent = re.match(r"\s*", line).group(0)
            suffix = ";" if not call_text.rstrip().endswith(";") else ""
            lines[idx] = f"{indent}{call_text}{suffix}"
            call_inserted = True
            break
    if not call_inserted and len(lines) > 1:
        lines.insert(-1, f"    {call_text};")
    return "\n".join(lines)


def clone_graph(template: dict[str, Any], idx: int) -> tuple[dict[str, Any], dict[str, Any]]:
    src_graph = template["graph"]
    src_node = template["node"]
    family = FAMILY_NAMES[idx % len(FAMILY_NAMES)]
    new_function = f"{family}{idx}"
    new_contract = f"SyntheticReentrancy{idx:05d}"
    new_state = STATE_NAMES[idx % len(STATE_NAMES)] + str(idx % 17)
    call = CALL_VARIANTS[idx % len(CALL_VARIANTS)]
    old_states = list(src_node.get("state_vars_accessed", []))
    source = mutate_source(src_node.get("function_source", ""), src_node.get("function", ""), new_function, old_states, new_state, call["call_text"], idx)
    graph_id = f"SYNTH_REENTRANCY::{idx:05d}::{new_contract}"
    node_id = f"i:{new_function}"
    normalized_function_hash = sha(source)
    normalized_contract_hash = sha(new_contract + source)
    interaction_set_hash = sha(node_id + source)

    node = copy.deepcopy(src_node)
    node.update(
        {
            "id": node_id,
            "function": new_function,
            "label": 1,
            "tier": "SYNTH_REENTRANCY_POS",
            "state_vars_accessed": [new_state],
            "external_calls": [call],
            "function_source": source,
            "state_texts": [f"mapping(address => uint256) {new_state}"],
            "callee_texts": [call["call_text"]],
            "reentrancy_label_status": "synthetic_positive_clone",
            "reentrancy_label_confidence": "synthetic_by_construction",
            "dataset_source": "SYNTH_REENTRANCY",
            "original_source_path": f"synthetic/{new_contract}.sol",
        }
    )
    provenance = dict(node.get("provenance") or {})
    provenance.update(
        {
            "dataset_source": "SYNTH_REENTRANCY",
            "original_source_path": f"synthetic/{new_contract}.sol",
            "contract_id": graph_id,
            "contract_name": new_contract,
            "function_name": new_function,
            "source_line_span": f"synthetic/{new_contract}.sol::{new_function}",
            "finding_id": f"synth-{idx:05d}",
            "finding_title": "Synthetic reentrancy positive clone",
            "severity": "High",
            "vulnerability_type": "reentrancy",
            "scope": "reentrancy",
            "evidence_pointer": f"synthetic_positive_clone#{idx:05d}",
            "normalized_contract_hash": normalized_contract_hash,
            "normalized_function_hash": normalized_function_hash,
            "normalized_interaction_set_hash": interaction_set_hash,
            "split_id": "train",
            "template_graph_id": src_graph.get("graph_id", ""),
            "template_interaction_id": src_node.get("id", ""),
            "template_split": template["split"],
        }
    )
    node["provenance"] = provenance

    graph = {
        "graph_id": graph_id,
        "split": "train",
        "source": "SYNTH_REENTRANCY",
        "project": "synthetic_positive_clone_v1",
        "contract": new_contract,
        "n_pos": 1,
        "n_neg": 0,
        "n_helper": 0,
        "n_edges": 0,
        "nodes": [node],
        "edges": [],
        "original_split": "synthetic_train",
        "split_id": "train",
        "contract_label": 1,
        "candidate_interaction_count": 1,
        "normalized_contract_hash": normalized_contract_hash,
        "normalized_interaction_set_hash": interaction_set_hash,
        "family_key": f"SYNTH_REENTRANCY::{family}",
        "positive_interaction_ids": [node_id],
        "vulnerability_types": ["reentrancy"],
        "reentrancy_ignored_interactions": 0,
        "localization": {
            "vulnerable_interaction_ids": [node_id],
            "items": [
                {
                    "interaction_id": node_id,
                    "function_name": new_function,
                    "source_line_span": f"synthetic/{new_contract}.sol::{new_function}",
                    "vulnerability_type": "reentrancy",
                    "scope": "reentrancy",
                    "evidence_pointer": f"synthetic_positive_clone#{idx:05d}",
                    "finding_id": f"synth-{idx:05d}",
                    "finding_title": "Synthetic reentrancy positive clone",
                }
            ],
            "supports_topk": True,
            "recommended_metrics": ["top-1 hit", "top-3 hit", "top-5 hit", "MRR", "Recall@k"],
        },
        "synthetic": True,
        "template_graph_id": src_graph.get("graph_id", ""),
        "template_interaction_id": src_node.get("id", ""),
        "template_split": template["split"],
        "augmentation_family": family,
    }
    manifest = {
        "synthetic_graph_id": graph_id,
        "synthetic_contract": new_contract,
        "synthetic_interaction_id": node_id,
        "family": family,
        "template_split": template["split"],
        "template_graph_id": src_graph.get("graph_id", ""),
        "template_interaction_id": src_node.get("id", ""),
        "template_function": src_node.get("function", ""),
        "call_method": call["method"],
        "state_variable": new_state,
        "source_hash": normalized_function_hash,
        "label": 1,
    }
    return graph, manifest


def build_scope_views(graphs: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    scope = {}
    for split, rows in graphs.items():
        scope[split] = []
        for graph in rows:
            scope[split].append(
                {
                    "graph_id": graph["graph_id"],
                    "contract": graph.get("contract", ""),
                    "scope_label": int(graph.get("contract_label", 0)),
                    "positive_interaction_ids": graph.get("positive_interaction_ids", []),
                    "vulnerability_types": graph.get("vulnerability_types", []),
                }
            )
    return scope


def report(before: dict[str, dict[str, int]], after: dict[str, dict[str, int]], manifest: list[dict[str, Any]], target_ratio: float) -> None:
    lines = ["# Reentrancy Positive Clone Augmentation v1", ""]
    lines.append("This dataset appends synthetic positive reentrancy clones to the better-labeled reentrancy train split. No synthetic negative examples are created.")
    lines.append("")
    lines.append(f"Target train interaction neg:pos ratio: {target_ratio:.2f}:1")
    lines.append(f"Synthetic positive contracts added to train: {len(manifest)}")
    lines.append("")
    lines.append("## Class Imbalance Before")
    lines.append("| Split | Contracts | Pos Contracts | Neg Contracts | Pos Int | Neg Int | Ignored | Neg:Pos Int |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for split, row in before.items():
        ratio = row["negative_interactions"] / max(row["positive_interactions"], 1)
        lines.append(f"| {split} | {row['contracts']} | {row['positive_contracts']} | {row['negative_contracts']} | {row['positive_interactions']} | {row['negative_interactions']} | {row['ignored_interactions']} | {ratio:.2f} |")
    lines.append("")
    lines.append("## Class Imbalance After")
    lines.append("| Split | Contracts | Pos Contracts | Neg Contracts | Pos Int | Neg Int | Ignored | Neg:Pos Int |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for split, row in after.items():
        ratio = row["negative_interactions"] / max(row["positive_interactions"], 1)
        lines.append(f"| {split} | {row['contracts']} | {row['positive_contracts']} | {row['negative_contracts']} | {row['positive_interactions']} | {row['negative_interactions']} | {row['ignored_interactions']} | {ratio:.2f} |")
    lines.append("")
    lines.append("## Clone Sources")
    counts = Counter(row["template_split"] for row in manifest)
    for split, count in sorted(counts.items()):
        lines.append(f"- templates from {split}: {count}")
    lines.append("")
    lines.append("## Families")
    family_counts = Counter(row["family"] for row in manifest)
    for family, count in sorted(family_counts.items()):
        lines.append(f"- {family}: {count}")
    (REPORTS / "reentrancy_positive_augmented_v1_imbalance_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-neg-pos-ratio", type=float, default=3.0)
    parser.add_argument("--max-clones", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    random.seed(args.seed)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "scope_views").mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    graphs = load_graphs()
    before = interaction_counts(graphs)
    train_counts = before["train"]
    needed = max(0, math.ceil(train_counts["negative_interactions"] / args.target_neg_pos_ratio - train_counts["positive_interactions"]))
    needed = min(needed, args.max_clones)
    templates = positive_templates(graphs)
    if not templates:
        raise RuntimeError("No positive reentrancy templates found")
    random.shuffle(templates)

    manifest = []
    for idx in range(needed):
        template = templates[idx % len(templates)]
        graph, row = clone_graph(template, idx)
        graphs["train"].append(graph)
        manifest.append(row)

    after = interaction_counts(graphs)
    for split in ("train", "val", "test"):
        (OUT_DIR / f"{split}.json").write_text(json.dumps(graphs[split], indent=2) + "\n", encoding="utf-8")
    scope = build_scope_views(graphs)
    (OUT_DIR / "scope_views" / "reentrancy_only.json").write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
    write_csv(
        OUT_DIR / "positive_clone_manifest.csv",
        manifest,
        [
            "synthetic_graph_id",
            "synthetic_contract",
            "synthetic_interaction_id",
            "family",
            "template_split",
            "template_graph_id",
            "template_interaction_id",
            "template_function",
            "call_method",
            "state_variable",
            "source_hash",
            "label",
        ],
    )
    write_csv(
        REPORTS / "reentrancy_positive_augmented_v1_counts.csv",
        [
            {"stage": "before", "split": split, **row, "interaction_neg_pos_ratio": row["negative_interactions"] / max(row["positive_interactions"], 1)}
            for split, row in before.items()
        ]
        + [
            {"stage": "after", "split": split, **row, "interaction_neg_pos_ratio": row["negative_interactions"] / max(row["positive_interactions"], 1)}
            for split, row in after.items()
        ],
        [
            "stage",
            "split",
            "contracts",
            "positive_contracts",
            "negative_contracts",
            "positive_interactions",
            "negative_interactions",
            "ignored_interactions",
            "interaction_neg_pos_ratio",
        ],
    )
    report(before, after, manifest, args.target_neg_pos_ratio)
    print(f"Wrote positive-only augmented dataset to {OUT_DIR}")
    print(f"Added {len(manifest)} synthetic positive train contracts")
    print(f"Train interaction neg:pos before={before['train']['negative_interactions']/max(before['train']['positive_interactions'],1):.2f} after={after['train']['negative_interactions']/max(after['train']['positive_interactions'],1):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
