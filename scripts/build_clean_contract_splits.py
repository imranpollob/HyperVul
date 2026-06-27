#!/usr/bin/env python3
"""Build a leakage-safe contract split proposal from Phase 0B metadata.

This script does not overwrite any dataset files. It reads
reports/phase0b_contract_metadata.csv, groups contracts by leakage constraints,
quarantines ambiguous duplicate/conflict groups, and writes
reports/phase0b_clean_split_plan.csv.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


TARGET_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


class DSU:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, x: str) -> None:
        self.parent.setdefault(x, x)

    def find(self, x: str) -> str:
        self.add(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stable_float(key: str) -> float:
    h = hashlib.sha256(key.encode()).hexdigest()
    return int(h[:12], 16) / float(0xFFFFFFFFFFFF)


def load_quarantine_graphs() -> set[str]:
    q: set[str] = set()
    dup_path = REPORTS / "phase0b_duplicate_groups.csv"
    if dup_path.exists():
        for r in read_csv(dup_path):
            # Quarantine cross-split exact duplicates. Same-split duplicates can be merged later.
            if r["group_kind"] in {"exact_contract_hash", "exact_interaction_set_hash"} and "|" in r["splits"]:
                for part in r["members"].split(" ; "):
                    if ":" in part:
                        q.add(part.split(":", 1)[1])
    conflict_path = REPORTS / "phase0b_label_conflicts.csv"
    if conflict_path.exists():
        for r in read_csv(conflict_path):
            for part in r["members"].split(" ; "):
                # member format: split:graph_id::function[y=...]
                if ":" not in part:
                    continue
                rest = part.split(":", 1)[1]
                gid = rest.rsplit("::", 1)[0] if "::" in rest else rest
                q.add(gid)
    return q


def build_components(rows: list[dict[str, str]], quarantine: set[str]) -> dict[str, list[dict[str, str]]]:
    dsu = DSU()
    by_key: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        gid = r["graph_id"]
        if gid in quarantine:
            continue
        dsu.add(gid)
        keys = [
            f"family:{r['family_key']}",
            f"contract_hash:{r['normalized_contract_hash']}",
            f"signature:{r['contract_signature_hash']}",
        ]
        if r.get("source_file"):
            keys.append(f"file:{r['dataset']}:{r['source_file']}")
        for fh in (r.get("function_hashes") or "").split("|"):
            if fh:
                keys.append(f"function:{fh}")
        for k in keys:
            by_key[k].append(gid)
    for gids in by_key.values():
        if len(gids) < 2:
            continue
        head = gids[0]
        for gid in gids[1:]:
            dsu.union(head, gid)
    comps: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        if r["graph_id"] in quarantine:
            continue
        comps[dsu.find(r["graph_id"])].append(r)
    return comps


def component_stats(members: list[dict[str, str]]) -> dict[str, Any]:
    labels = [int(m["contract_label"]) for m in members]
    scopes = Counter()
    for m in members:
        if int(m["contract_label"]) != 1:
            continue
        for s in (m.get("scopes") or "").split("|"):
            if s:
                scopes[s] += 1
    return {
        "contracts": len(members),
        "positive_contracts": sum(labels),
        "negative_contracts": len(labels) - sum(labels),
        "reentrancy_positive_contracts": scopes["reentrancy"],
        "unchecked_positive_contracts": scopes["unchecked low-level call"],
        "front_running_positive_contracts": scopes["front-running"],
        "delegatecall_positive_contracts": scopes["delegatecall"],
    }


def assign_components(comps: dict[str, list[dict[str, str]]]) -> dict[str, str]:
    """Greedy deterministic assignment preserving whole leakage components."""
    comp_items = []
    for cid, members in comps.items():
        st = component_stats(members)
        comp_items.append((cid, members, st))
    comp_items.sort(
        key=lambda item: (
            -item[2]["positive_contracts"],
            -item[2]["reentrancy_positive_contracts"],
            -item[2]["contracts"],
            item[0],
        )
    )

    total = {
        "contracts": sum(st["contracts"] for _, _, st in comp_items),
        "positive_contracts": sum(st["positive_contracts"] for _, _, st in comp_items),
        "reentrancy_positive_contracts": sum(st["reentrancy_positive_contracts"] for _, _, st in comp_items),
    }
    targets = {
        split: {
            key: total[key] * ratio
            for key in ["contracts", "positive_contracts", "reentrancy_positive_contracts"]
        }
        for split, ratio in TARGET_RATIOS.items()
    }
    used = {
        split: {"contracts": 0, "positive_contracts": 0, "reentrancy_positive_contracts": 0}
        for split in TARGET_RATIOS
    }
    assignment: dict[str, str] = {}

    for cid, _members, st in comp_items:
        best_split = None
        best_score = None
        for split in ["train", "val", "test"]:
            score = 0.0
            for key, weight in [
                ("positive_contracts", 4.0),
                ("reentrancy_positive_contracts", 4.0),
                ("contracts", 1.0),
            ]:
                before = abs(used[split][key] - targets[split][key])
                after = abs((used[split][key] + st[key]) - targets[split][key])
                score += weight * (after - before)
            # stable tie-breaker, not random
            score += stable_float(f"{cid}:{split}") * 1e-6
            if best_score is None or score < best_score:
                best_score = score
                best_split = split
        assert best_split is not None
        assignment[cid] = best_split
        for key in used[best_split]:
            used[best_split][key] += st[key]
    return assignment


def main() -> int:
    meta_path = REPORTS / "phase0b_contract_metadata.csv"
    if not meta_path.exists():
        raise SystemExit("Missing reports/phase0b_contract_metadata.csv. Run scripts/audit_raw_coverage.py first.")
    rows = read_csv(meta_path)
    quarantine = load_quarantine_graphs()
    comps = build_components(rows, quarantine)
    assignment = assign_components(comps)

    out_rows: list[dict[str, Any]] = []
    comp_id_by_gid = {}
    comp_stats_by_id = {}
    for cid, members in comps.items():
        st = component_stats(members)
        comp_stats_by_id[cid] = st
        for m in members:
            comp_id_by_gid[m["graph_id"]] = cid
    for r in rows:
        gid = r["graph_id"]
        if gid in quarantine:
            status = "quarantine"
            clean_split = ""
            cid = ""
            st = {}
            reason = "duplicate_or_label_conflict"
        else:
            cid = comp_id_by_gid[gid]
            status = "include"
            clean_split = assignment[cid]
            st = comp_stats_by_id[cid]
            reason = "leakage_component_assigned_whole"
        out = {
            "status": status,
            "clean_split": clean_split,
            "component_id": cid,
            "component_contracts": st.get("contracts", ""),
            "component_positive_contracts": st.get("positive_contracts", ""),
            "component_reentrancy_positive_contracts": st.get("reentrancy_positive_contracts", ""),
            "reason": reason,
        }
        out.update(r)
        out_rows.append(out)

    fields = [
        "status",
        "clean_split",
        "component_id",
        "component_contracts",
        "component_positive_contracts",
        "component_reentrancy_positive_contracts",
        "reason",
        "split",
        "graph_id",
        "dataset",
        "project",
        "contract",
        "source_file",
        "contract_label",
        "n_pos",
        "n_neg",
        "interaction_count",
        "vulnerability_types",
        "scopes",
        "normalized_contract_hash",
        "contract_signature_hash",
        "family_key",
    ]
    out_path = REPORTS / "phase0b_clean_split_plan.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in out_rows:
            w.writerow({k: r.get(k, "") for k in fields})

    included = [r for r in out_rows if r["status"] == "include"]
    split_counts = {}
    for split in ["train", "val", "test"]:
        ss = [r for r in included if r["clean_split"] == split]
        split_counts[split] = {
            "contracts": len(ss),
            "positive_contracts": sum(int(r["contract_label"]) == 1 for r in ss),
            "negative_contracts": sum(int(r["contract_label"]) == 0 for r in ss),
            "reentrancy_positive_contracts": sum(
                int(r["contract_label"]) == 1 and "reentrancy" in r["scopes"].split("|") for r in ss
            ),
            "unchecked_positive_contracts": sum(
                int(r["contract_label"]) == 1 and "unchecked low-level call" in r["scopes"].split("|") for r in ss
            ),
        }
    summary = {
        "generated_at": "2026-06-27",
        "input_contracts": len(rows),
        "included_contracts": len(included),
        "quarantined_contracts": len(out_rows) - len(included),
        "components": len(comps),
        "split_counts": split_counts,
        "rules": [
            "No component is split across train/val/test.",
            "Components connect graph rows by project/family, source file, normalized contract hash, exact interaction-set hash, and exact function hashes.",
            "Cross-split exact duplicates and exact function-label conflicts are quarantined.",
            "This is a proposal only; no data/ files are modified.",
        ],
    }
    with open(REPORTS / "phase0b_clean_split_plan_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
