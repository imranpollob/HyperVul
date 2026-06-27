#!/usr/bin/env python3
"""Build a better-labeled reentrancy dataset view.

Outputs are separate from the clean graph dataset. This script does not create
synthetic negative examples. It uses the existing real negatives and Phase 1C
review labels, then adds a positive-only pattern-family augmentation manifest.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = ROOT / "data" / "contract_graphs_clean"
OUT_DIR = ROOT / "data" / "reentrancy_better_labels_v1"
REPORTS = ROOT / "reports"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_scope() -> dict[str, dict[str, dict[str, Any]]]:
    data = json.loads((CLEAN_DIR / "scope_views" / "reentrancy_only.json").read_text(encoding="utf-8"))
    return {split: {row["graph_id"]: row for row in rows} for split, rows in data.items()}


def review_map() -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(ROOT / "data" / "labels_clean_v1" / "reentrancy_reviewed_train_val.csv")
    return {(row["contract_id"], row["interaction_id"]): row for row in rows}


def decision(row: dict[str, str] | None, split: str, default_label: int) -> tuple[int | None, str, str]:
    if split == "test" or row is None:
        return default_label, "scope_default", "test_unchanged" if split == "test" else ""
    proposed = row["proposed_cleaned_label"]
    confidence = row.get("confidence", "")
    if proposed == "confirmed_positive_reentrancy":
        return 1, "review_confirmed_positive", confidence
    if proposed == "confirmed_protected_negative":
        return 0, "review_confirmed_protected_negative", confidence
    if proposed == "wrong_scope_or_other_vulnerability":
        return None, "wrong_scope_excluded", confidence
    if proposed == "ambiguous_quarantine":
        return None, "ambiguous_quarantine", confidence
    if proposed == "insufficient_evidence":
        return None, "insufficient_evidence", confidence
    return default_label, "scope_default", confidence


def rebuild_graphs() -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    scope = load_scope()
    reviews = review_map()
    out: dict[str, list[dict[str, Any]]] = {"train": [], "val": [], "test": []}
    label_rows: list[dict[str, Any]] = []
    for split in ("train", "val", "test"):
        graphs = json.loads((CLEAN_DIR / f"{split}.json").read_text(encoding="utf-8"))
        for graph in graphs:
            if graph["graph_id"] not in scope[split]:
                continue
            graph = json.loads(json.dumps(graph))
            scope_pos = set(scope[split][graph["graph_id"]].get("positive_interaction_ids", []))
            positive_ids = set()
            ignored = 0
            for node in graph.get("nodes", []):
                if node.get("kind") != "interaction":
                    continue
                default = 1 if node.get("id") in scope_pos else 0
                row = reviews.get((graph["graph_id"], node.get("id")))
                new_label, status, confidence = decision(row, split, default)
                node["label"] = new_label
                node["reentrancy_label_status"] = status
                node["reentrancy_label_confidence"] = confidence
                if new_label is None:
                    ignored += 1
                    node["tier"] = "REENTRANCY_IGNORE"
                elif new_label == 1:
                    positive_ids.add(node["id"])
                    node["tier"] = "REENTRANCY_POS"
                else:
                    node["tier"] = "REENTRANCY_NEG"
                label_rows.append(
                    {
                        "split": split,
                        "graph_id": graph["graph_id"],
                        "contract": graph.get("contract", ""),
                        "interaction_id": node.get("id", ""),
                        "function": node.get("function", ""),
                        "label": "" if new_label is None else new_label,
                        "status": status,
                        "confidence": confidence,
                        "source_path": (node.get("provenance") or {}).get("original_source_path", ""),
                        "source_span": (node.get("provenance") or {}).get("source_line_span", ""),
                        "external_calls": "|".join(str(c.get("call_text", "")) for c in node.get("external_calls", [])),
                        "state_vars": "|".join(str(s) for s in node.get("state_vars_accessed", [])),
                    }
                )
            graph["positive_interaction_ids"] = sorted(positive_ids)
            graph["contract_label"] = int(bool(positive_ids))
            graph["vulnerability_types"] = ["reentrancy"] if positive_ids else []
            graph["reentrancy_ignored_interactions"] = ignored
            graph["localization"] = {
                "vulnerable_interaction_ids": sorted(positive_ids),
                "items": [
                    {
                        "interaction_id": node.get("id"),
                        "function_name": node.get("function", ""),
                        "source_line_span": (node.get("provenance") or {}).get("source_line_span", ""),
                        "vulnerability_type": "reentrancy",
                        "scope": "reentrancy",
                        "evidence_pointer": (node.get("provenance") or {}).get("evidence_pointer", ""),
                    }
                    for node in graph.get("nodes", [])
                    if node.get("kind") == "interaction" and node.get("id") in positive_ids
                ],
                "supports_topk": bool(positive_ids),
                "recommended_metrics": ["top-1 hit", "top-3 hit", "top-5 hit", "MRR", "Recall@k"],
            }
            out[split].append(graph)
    return out, label_rows


PATTERNS = [
    ("withdraw", "balances[msg.sender]", "(bool ok, ) = msg.sender.call{value: amount}(\"\");", "balances[msg.sender] = 0;"),
    ("claimReward", "claimed[msg.sender]", "rewardToken.transfer(msg.sender, reward);", "claimed[msg.sender] = true;"),
    ("refund", "refunds[msg.sender]", "(bool sent, ) = payable(msg.sender).call{value: refundAmount}(\"\");", "refunds[msg.sender] = 0;"),
    ("unstake", "stakes[msg.sender]", "stakingToken.transfer(msg.sender, amount);", "stakes[msg.sender] -= amount;"),
    ("redeemShares", "shares[msg.sender]", "asset.transfer(msg.sender, assets);", "shares[msg.sender] -= shareAmount;"),
    ("payout", "credit[msg.sender]", "payable(msg.sender).transfer(amount);", "credit[msg.sender] = 0;"),
    ("exit", "positions[msg.sender]", "(bool ok, ) = recipient.call{value: value}(\"\");", "positions[msg.sender].closed = true;"),
    ("release", "released[msg.sender]", "token.safeTransfer(msg.sender, amount);", "released[msg.sender] = true;"),
]


def positive_pattern_manifest() -> list[dict[str, Any]]:
    rows = []
    for idx, (function, state_var, external_call, state_update) in enumerate(PATTERNS):
        for variant in range(10):
            amount = ["amount", "value", "reward", "refundAmount", "assets"][variant % 5]
            guard = "require(%s > 0, \"zero\");" % amount
            source = "\n".join(
                [
                    f"function {function}{variant}(uint256 {amount}) external {{",
                    f"    {guard}",
                    f"    {external_call}",
                    "    require(ok || true, \"transfer failed\");" if ".call" in external_call else "    // token transfer executed before accounting update",
                    f"    {state_update}",
                    "}",
                ]
            )
            rows.append(
                {
                    "augmentation_id": f"re_pos_{idx:02d}_{variant:02d}",
                    "label": 1,
                    "vulnerability_type": "reentrancy",
                    "family": function,
                    "function_name": f"{function}{variant}",
                    "state_variable": state_var,
                    "external_call": external_call,
                    "state_update": state_update,
                    "risk_rule": "external_call_before_state_update",
                    "callee_controllability": "attacker_or_user_controlled",
                    "guard_status": "no_effective_reentrancy_guard",
                    "source_code": source,
                    "source_hash": sha(source),
                }
            )
    return rows


def counts(graphs: dict[str, list[dict[str, Any]]], labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    by_split = defaultdict(list)
    for row in labels:
        by_split[row["split"]].append(row)
    for split, split_graphs in graphs.items():
        interactions = [row for row in by_split[split] if row["label"] != ""]
        ignored = [row for row in by_split[split] if row["label"] == ""]
        pos_int = sum(int(row["label"]) == 1 for row in interactions)
        neg_int = sum(int(row["label"]) == 0 for row in interactions)
        pos_contracts = sum(int(graph.get("contract_label", 0)) == 1 for graph in split_graphs)
        rows.append(
            {
                "split": split,
                "contracts": len(split_graphs),
                "positive_contracts": pos_contracts,
                "negative_contracts": len(split_graphs) - pos_contracts,
                "labeled_interactions": len(interactions),
                "positive_interactions": pos_int,
                "negative_interactions": neg_int,
                "ignored_interactions": len(ignored),
                "interaction_pos_rate": pos_int / len(interactions) if interactions else 0.0,
                "interaction_neg_pos_ratio": neg_int / max(pos_int, 1),
            }
        )
    return rows


def write_report(count_rows: list[dict[str, Any]], label_rows: list[dict[str, Any]], aug_rows: list[dict[str, Any]]) -> None:
    status_counts = Counter(row["status"] for row in label_rows)
    lines = ["# Reentrancy Better Labels v1", ""]
    lines.append("This dataset is a reentrancy-focused graph view with Phase 1C review labels applied. Test labels are unchanged. No synthetic negative examples are generated.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("- `data/reentrancy_better_labels_v1/train.json`")
    lines.append("- `data/reentrancy_better_labels_v1/val.json`")
    lines.append("- `data/reentrancy_better_labels_v1/test.json`")
    lines.append("- `data/reentrancy_better_labels_v1/reentrancy_labels.csv`")
    lines.append("- `data/reentrancy_better_labels_v1/positive_pattern_augmentation_v1.jsonl`")
    lines.append("")
    lines.append("## Counts")
    lines.append("| Split | Contracts | Pos Contracts | Neg Contracts | Labeled Interactions | Pos Int | Neg Int | Ignored | Neg:Pos |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in count_rows:
        lines.append(
            f"| {row['split']} | {row['contracts']} | {row['positive_contracts']} | {row['negative_contracts']} | "
            f"{row['labeled_interactions']} | {row['positive_interactions']} | {row['negative_interactions']} | "
            f"{row['ignored_interactions']} | {float(row['interaction_neg_pos_ratio']):.2f} |"
        )
    lines.append("")
    lines.append("## Label Status Counts")
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")
    lines.append("")
    lines.append("## Positive-Only Pattern Augmentation")
    lines.append(f"- Synthetic positive pattern variants: {len(aug_rows)}")
    lines.append("- Families: " + ", ".join(sorted({row["family"] for row in aug_rows})))
    lines.append("")
    lines.append("## Intended Use")
    lines.append("Use this dataset for reentrancy contract-level detection and top-k localization. For precision, train with the real protected negatives already present in the labeled graph view; do not generate synthetic negatives.")
    (REPORTS / "reentrancy_better_labels_v1_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    graphs, label_rows = rebuild_graphs()
    for split, rows in graphs.items():
        (OUT_DIR / f"{split}.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    label_fields = [
        "split",
        "graph_id",
        "contract",
        "interaction_id",
        "function",
        "label",
        "status",
        "confidence",
        "source_path",
        "source_span",
        "external_calls",
        "state_vars",
    ]
    write_csv(OUT_DIR / "reentrancy_labels.csv", label_rows, label_fields)
    count_rows = counts(graphs, label_rows)
    write_csv(
        REPORTS / "reentrancy_better_labels_v1_counts.csv",
        count_rows,
        [
            "split",
            "contracts",
            "positive_contracts",
            "negative_contracts",
            "labeled_interactions",
            "positive_interactions",
            "negative_interactions",
            "ignored_interactions",
            "interaction_pos_rate",
            "interaction_neg_pos_ratio",
        ],
    )
    aug_rows = positive_pattern_manifest()
    with (OUT_DIR / "positive_pattern_augmentation_v1.jsonl").open("w", encoding="utf-8") as f:
        for row in aug_rows:
            f.write(json.dumps(row) + "\n")
    write_report(count_rows, label_rows, aug_rows)
    print(f"Wrote better-labeled reentrancy dataset to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
