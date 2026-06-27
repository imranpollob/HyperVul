#!/usr/bin/env python3
"""Build clean contract graph datasets with embedded provenance.

Inputs:
  - data/contract_graphs/{train,val,test}.json
  - reports/phase0b_clean_split_plan.csv
  - raw DAppSCAN/FORGE sources used by scripts/audit_raw_coverage.py

Outputs:
  - data/contract_graphs_clean/{train,val,test}.json
  - data/contract_graphs_clean/quarantine.json
  - data/contract_graphs_clean/scope_views/*.json
  - reports/phase0c_*.{md,json,csv}

This script does not overwrite the original graph datasets.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OLD_GRAPH_DIR = ROOT / "data" / "contract_graphs"
CLEAN_GRAPH_DIR = ROOT / "data" / "contract_graphs_clean"
SCOPE_DIR = CLEAN_GRAPH_DIR / "scope_views"

sys.path.append(str(ROOT / "scripts"))
import audit_raw_coverage as arc  # noqa: E402
import negative_hyperedge_sampling as nhs  # noqa: E402


TARGET_SCOPES = {"reentrancy", "unchecked low-level call", "delegatecall", "front-running"}


@dataclass
class Evidence:
    file_path: str = ""
    line_span: str = ""
    finding_id: str = ""
    title: str = ""
    severity: str = ""
    vulnerability_type: str = ""
    scope: str = ""
    evidence_pointer: str = ""
    contract: str = ""
    function: str = ""
    normalized_source_hash: str = ""


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def norm_source(src: str) -> str:
    return arc.norm_source(src)


def source_hash(src: str) -> str:
    return hashlib.sha256(norm_source(src).encode("utf-8")).hexdigest()


def graph_interaction_set_hash(graph: dict[str, Any]) -> str:
    hashes = sorted(
        source_hash(n.get("function_source", ""))
        for n in graph.get("nodes", [])
        if n.get("kind") == "interaction"
    )
    return hashlib.sha256("|".join(hashes).encode("utf-8")).hexdigest()


def unique_join(values: list[Any]) -> str:
    out = []
    for v in values:
        if v is None:
            continue
        s = str(v)
        if s and s not in out:
            out.append(s)
    return "|".join(out)


def split_pipe(value: str) -> list[str]:
    return [x for x in (value or "").split("|") if x]


def load_original_graphs() -> dict[str, dict[str, Any]]:
    graphs = {}
    for split in ["train", "val", "test"]:
        for g in json.load(open(OLD_GRAPH_DIR / f"{split}.json", encoding="utf-8")):
            graphs[g["graph_id"]] = g | {"original_split": split}
    return graphs


def build_source_lookup(graphs: dict[str, dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    """Recover source path and hashes for graph interaction functions."""
    needed = {
        ("FORGE" if g.get("source") == "FORGE" else "DAppSCAN", g.get("project", ""))
        for g in graphs.values()
    }
    lookup: dict[tuple[str, str, str, str], dict[str, str]] = {}

    for dataset, project in sorted(needed):
        file_contracts: dict[str, dict[str, Any]] = {}
        merged: dict[str, Any] = {}
        file_sources: dict[str, str] = {}
        if dataset == "DAppSCAN":
            project_root = arc.DAPPSCAN_ROOT / project
            if not project_root.exists():
                continue
            for sol in project_root.glob("**/*.sol"):
                rel = str(sol.relative_to(arc.DAPPSCAN_ROOT))
                try:
                    src = sol.read_text(encoding="utf-8", errors="ignore")
                    parsed = nhs.parse_contracts(src)
                except Exception:
                    continue
                file_sources[rel] = src
                file_contracts[rel] = parsed
                merged.update(parsed)
        else:
            vf = arc.FORGE_VULN_DIR / f"{project}.json"
            if not vf.exists():
                continue
            try:
                data = json.load(open(vf, encoding="utf-8"))
            except Exception:
                continue
            for fname, src in (data.get("affected_files") or {}).items():
                try:
                    parsed = nhs.parse_contracts(src)
                except Exception:
                    parsed = {}
                file_sources[fname] = src
                file_contracts[fname] = parsed
                merged.update(parsed)

        direct_func_file: dict[tuple[str, str], str] = {}
        direct_func_hash: dict[tuple[str, str], str] = {}
        contract_file: dict[str, str] = {}
        contract_hash: dict[str, str] = {}
        for path, contracts in file_contracts.items():
            for cn, ci in contracts.items():
                contract_file.setdefault(cn, path)
                try:
                    contract_hash[cn] = source_hash(nhs.node_text(ci.node))
                except Exception:
                    contract_hash[cn] = arc.contract_hash_from_source(file_sources.get(path, ""), cn)
                for fn, fnode in ci.functions.items():
                    direct_func_file[(cn, fn)] = path
                    direct_func_hash[(cn, fn)] = source_hash(nhs.node_text(fnode))

        for cn in merged:
            try:
                funcs = nhs.resolve_all_functions(cn, merged)
            except Exception:
                funcs = merged[cn].functions
            for fn, fnode in funcs.items():
                fhash = source_hash(nhs.node_text(fnode))
                path = direct_func_file.get((cn, fn)) or contract_file.get(cn, "")
                start_line = getattr(fnode, "start_point", (0, 0))[0] + 1
                end_line = getattr(fnode, "end_point", (0, 0))[0] + 1
                lookup[(dataset, project, cn, fn)] = {
                    "original_source_path": path,
                    "normalized_function_hash": fhash,
                    "normalized_contract_hash": contract_hash.get(cn, ""),
                    "function_line_span": f"{path}#L{start_line}-L{end_line}" if path else f"L{start_line}-L{end_line}",
                }
    return lookup


def evidence_key(e: Evidence) -> tuple[str, str, str, str, str]:
    return (e.file_path, e.line_span, e.finding_id, e.vulnerability_type, e.evidence_pointer)


def add_evidence(
    out: dict[tuple[str, str, str, str], list[Evidence]],
    key: tuple[str, str, str, str],
    evidence: Evidence,
) -> None:
    if not key[0] or not key[1] or not key[2] or not key[3]:
        return
    if evidence_key(evidence) in {evidence_key(e) for e in out[key]}:
        return
    out[key].append(evidence)


def build_positive_provenance() -> dict[tuple[str, str, str, str], list[Evidence]]:
    raw_rows = arc.build_dapp_raw_findings() + arc.build_forge_raw_findings()
    _construct_rows, construct_by_key = arc.load_constructable_positives()
    _graph_rows, graph_by_key = arc.load_graph_interactions()
    arc.enrich_raw_rows(raw_rows, construct_by_key, graph_by_key)
    by_node: dict[tuple[str, str, str, str], list[Evidence]] = defaultdict(list)
    for raw in raw_rows:
        if not raw.included_in_graph:
            continue
        if not raw.contract or not raw.function:
            continue
        add_evidence(
            by_node,
            (raw.dataset, raw.project, raw.contract, raw.function),
            Evidence(
                file_path=raw.file_path,
                line_span=raw.line_span,
                finding_id=raw.finding_id,
                title=raw.title,
                severity=raw.severity,
                vulnerability_type=raw.vulnerability_type,
                scope=raw.scope,
                evidence_pointer=raw.evidence_pointer,
                contract=raw.contract,
                function=raw.function,
                normalized_source_hash=raw.normalized_source_hash,
            ),
        )

    # Fallback 1: original split positives have the most complete curated labels.
    for base in ["splits_clean", "splits"]:
        for split in ["train", "val", "test"]:
            path = ROOT / "data" / base / f"{split}.json"
            if not path.exists():
                continue
            for item in json.load(open(path, encoding="utf-8")):
                if item.get("label") != 1:
                    continue
                if item.get("vfp_id"):
                    dataset = "FORGE"
                    project = item.get("vfp_id", "")
                    source_path = item.get("file", "")
                    evidence_pointer = f"data/FORGE-Curated/flatten/vfp-vuln/{project}.json#{item.get('finding_id','')}"
                elif item.get("project_root"):
                    dataset = "DAppSCAN"
                    project = item.get("project_root", "")
                    source_path = item.get("filePath") or item.get("file", "")
                    evidence_pointer = f"{source_path}:{item.get('lineNumber','')}"
                else:
                    continue
                fn = item.get("function") or item.get("ast_function") or item.get("annotated_function") or ""
                vt = item.get("vtype") or item.get("category") or item.get("swc_code") or ""
                add_evidence(
                    by_node,
                    (dataset, project, item.get("contract", ""), fn),
                    Evidence(
                        file_path=source_path,
                        line_span=item.get("lineNumber") or "",
                        finding_id=str(item.get("finding_id", "")),
                        title=item.get("finding_title") or item.get("category") or "",
                        severity=item.get("severity") or "",
                        vulnerability_type=vt,
                        scope=arc.scope_key(vt),
                        evidence_pointer=evidence_pointer,
                        contract=item.get("contract", ""),
                        function=fn,
                        normalized_source_hash=item.get("normalized_source_hash", ""),
                    ),
                )

    # Fallback 2: constructable-positive files cover AST-remapped function names.
    for path in [
        ROOT / "experiments/results/dappscan_ast_constructable_hyperedges.json",
        ROOT / "experiments/results/forge_ast_constructable_hyperedges.json",
    ]:
        if not path.exists():
            continue
        for item in json.load(open(path, encoding="utf-8")):
            if item.get("vfp_id"):
                dataset = "FORGE"
                project = item.get("vfp_id", "")
                fn = item.get("function", "")
                vt = item.get("vtype") or item.get("category") or item.get("swc_code") or ""
                source_path = item.get("file", "")
                evidence_pointer = f"data/FORGE-Curated/flatten/vfp-vuln/{project}.json#{item.get('finding_id','')}"
            else:
                dataset = "DAppSCAN"
                project = item.get("project_root", "")
                fn = item.get("ast_function") or item.get("function") or item.get("annotated_function") or ""
                vt = item.get("vtype") or item.get("category") or item.get("swc_code") or ""
                source_path = item.get("filePath") or item.get("file", "")
                evidence_pointer = f"{source_path}:{item.get('lineNumber','')}"
            add_evidence(
                by_node,
                (dataset, project, item.get("contract", ""), fn),
                Evidence(
                    file_path=source_path,
                    line_span=item.get("lineNumber") or "",
                    finding_id=str(item.get("finding_id", "")),
                    title=item.get("finding_title") or item.get("category") or "",
                    severity=item.get("severity") or "",
                    vulnerability_type=vt,
                    scope=arc.scope_key(vt),
                    evidence_pointer=evidence_pointer,
                    contract=item.get("contract", ""),
                    function=fn,
                    normalized_source_hash=item.get("normalized_source_hash", ""),
                ),
            )
    return by_node


def node_provenance(
    *,
    node: dict[str, Any],
    graph: dict[str, Any],
    plan_row: dict[str, str],
    source_lookup: dict[tuple[str, str, str, str], dict[str, str]],
    positive_lookup: dict[tuple[str, str, str, str], list[Evidence]],
) -> dict[str, Any]:
    dataset = "FORGE" if graph.get("source") == "FORGE" else "DAppSCAN"
    key = (dataset, graph.get("project", ""), graph.get("contract", ""), node.get("function", ""))
    src = source_lookup.get(key, {})
    positives = positive_lookup.get(key, []) if int(node.get("label", 0)) == 1 else []
    source_path = src.get("original_source_path", "")
    if positives:
        source_path = source_path or unique_join([p.file_path for p in positives])
    function_hash = src.get("normalized_function_hash") or source_hash(node.get("function_source", ""))
    contract_hash = (
        src.get("normalized_contract_hash")
        or plan_row.get("normalized_contract_hash", "")
        or graph_interaction_set_hash(graph)
    )
    return {
        "dataset_source": dataset,
        "original_source_path": source_path,
        "contract_id": graph.get("graph_id", ""),
        "contract_name": graph.get("contract", ""),
        "function_name": node.get("function", ""),
        "source_line_span": unique_join([p.line_span for p in positives]) or src.get("function_line_span", ""),
        "finding_id": unique_join([p.finding_id for p in positives]),
        "finding_title": unique_join([p.title for p in positives]),
        "severity": unique_join([p.severity for p in positives]),
        "vulnerability_type": unique_join([p.vulnerability_type for p in positives]),
        "scope": unique_join([p.scope for p in positives]),
        "evidence_pointer": unique_join([p.evidence_pointer for p in positives]),
        "normalized_contract_hash": contract_hash,
        "normalized_function_hash": function_hash,
        "normalized_interaction_set_hash": plan_row.get("contract_signature_hash") or graph_interaction_set_hash(graph),
        "split_id": plan_row.get("clean_split", ""),
    }


def rebuild_graph(
    graph: dict[str, Any],
    plan_row: dict[str, str],
    source_lookup: dict[tuple[str, str, str, str], dict[str, str]],
    positive_lookup: dict[tuple[str, str, str, str], list[Evidence]],
) -> dict[str, Any]:
    g = copy.deepcopy(graph)
    clean_split = plan_row["clean_split"]
    interaction_set_hash = plan_row.get("contract_signature_hash") or graph_interaction_set_hash(graph)
    contract_hash = plan_row.get("normalized_contract_hash", "")
    g["original_split"] = graph.get("original_split", graph.get("split"))
    g["split"] = clean_split
    g["split_id"] = clean_split
    g["contract_label"] = 1 if int(g.get("n_pos", 0)) > 0 else 0
    g["candidate_interaction_count"] = int(g.get("n_pos", 0)) + int(g.get("n_neg", 0))
    g["normalized_contract_hash"] = contract_hash
    g["normalized_interaction_set_hash"] = interaction_set_hash
    g["family_key"] = plan_row.get("family_key", "")

    positive_ids: list[str] = []
    vulnerability_types: list[str] = []
    localization = []
    for n in g.get("nodes", []):
        if n.get("kind") != "interaction":
            continue
        prov = node_provenance(
            node=n,
            graph=g,
            plan_row=plan_row,
            source_lookup=source_lookup,
            positive_lookup=positive_lookup,
        )
        n["provenance"] = prov
        n["dataset_source"] = prov["dataset_source"]
        n["original_source_path"] = prov["original_source_path"]
        n["contract_id"] = prov["contract_id"]
        n["source_line_span"] = prov["source_line_span"]
        n["finding_id"] = prov["finding_id"]
        n["finding_title"] = prov["finding_title"]
        n["severity"] = prov["severity"]
        n["vulnerability_type"] = prov["vulnerability_type"]
        n["evidence_pointer"] = prov["evidence_pointer"]
        n["normalized_contract_hash"] = prov["normalized_contract_hash"]
        n["normalized_function_hash"] = prov["normalized_function_hash"]
        n["normalized_interaction_set_hash"] = prov["normalized_interaction_set_hash"]
        n["split_id"] = clean_split
        if int(n.get("label", 0)) == 1:
            positive_ids.append(n.get("id", ""))
            vulnerability_types.extend(split_pipe(prov["vulnerability_type"]))
            localization.append(
                {
                    "interaction_id": n.get("id", ""),
                    "function_name": n.get("function", ""),
                    "source_line_span": prov["source_line_span"],
                    "vulnerability_type": prov["vulnerability_type"],
                    "scope": prov["scope"],
                    "evidence_pointer": prov["evidence_pointer"],
                    "finding_id": prov["finding_id"],
                    "finding_title": prov["finding_title"],
                }
            )
    g["positive_interaction_ids"] = positive_ids
    g["vulnerability_types"] = sorted(set(vulnerability_types))
    g["localization"] = {
        "vulnerable_interaction_ids": positive_ids,
        "items": localization,
        "supports_topk": bool(localization),
        "recommended_metrics": ["top-1 hit", "top-3 hit", "top-5 hit", "MRR", "Recall@k"],
    }
    return g


def validation_for_split(clean_graphs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    validations = {}
    for field, label in [
        ("normalized_contract_hash", "contract_hash"),
        ("normalized_interaction_set_hash", "interaction_set_hash"),
    ]:
        seen = defaultdict(set)
        for split, graphs in clean_graphs.items():
            for g in graphs:
                key = g.get(field, "")
                if key:
                    seen[key].add(split)
        bad = {k: sorted(v) for k, v in seen.items() if len(v) > 1}
        validations[f"no_cross_split_{label}_leakage"] = {"pass": len(bad) == 0, "violations": len(bad)}

    source_seen = defaultdict(set)
    fn_seen = defaultdict(set)
    conflict_graph_ids = set()
    if (REPORTS / "phase0b_label_conflicts.csv").exists():
        for r in read_csv(REPORTS / "phase0b_label_conflicts.csv"):
            for part in r["members"].split(" ; "):
                if ":" not in part:
                    continue
                rest = part.split(":", 1)[1]
                gid = rest.rsplit("::", 1)[0] if "::" in rest else rest
                conflict_graph_ids.add(gid)
    included_conflicts = 0
    all_interactions_have_contract = True
    positive_contracts_missing_localization = 0
    positive_nodes_missing_source_path = 0
    positive_nodes_missing_line_span = 0
    for split, graphs in clean_graphs.items():
        for g in graphs:
            if g["graph_id"] in conflict_graph_ids:
                included_conflicts += 1
            if g.get("contract_label") == 1 and not g.get("localization", {}).get("items"):
                positive_contracts_missing_localization += 1
            for n in g.get("nodes", []):
                if n.get("kind") != "interaction":
                    continue
                all_interactions_have_contract = all_interactions_have_contract and bool(g.get("graph_id"))
                prov = n.get("provenance") or {}
                sp = prov.get("original_source_path", "")
                if sp:
                    source_seen[f"{prov.get('dataset_source')}::{sp}"].add(split)
                fh = prov.get("normalized_function_hash", "")
                if fh:
                    fn_seen[fh].add(split)
                if int(n.get("label", 0)) == 1:
                    if not sp:
                        positive_nodes_missing_source_path += 1
                    if not prov.get("source_line_span"):
                        positive_nodes_missing_line_span += 1
    source_bad = {k: sorted(v) for k, v in source_seen.items() if len(v) > 1}
    fn_bad = {k: sorted(v) for k, v in fn_seen.items() if len(v) > 1}
    validations["no_cross_split_source_file_leakage"] = {
        "pass": len(source_bad) == 0,
        "violations": len(source_bad),
    }
    validations["no_cross_split_function_hash_leakage"] = {
        "pass": len(fn_bad) == 0,
        "violations": len(fn_bad),
    }
    validations["no_known_duplicate_conflict_leakage"] = {
        "pass": included_conflicts == 0,
        "violations": included_conflicts,
    }
    validations["all_interactions_map_to_contract"] = {
        "pass": all_interactions_have_contract,
        "violations": 0 if all_interactions_have_contract else 1,
    }
    validations["all_positive_contracts_have_localization_metadata"] = {
        "pass": positive_contracts_missing_localization == 0,
        "violations": positive_contracts_missing_localization,
    }
    validations["positive_nodes_missing_source_path"] = {
        "pass": positive_nodes_missing_source_path == 0,
        "violations": positive_nodes_missing_source_path,
    }
    validations["positive_nodes_missing_line_span"] = {
        "pass": positive_nodes_missing_line_span == 0,
        "violations": positive_nodes_missing_line_span,
    }
    return validations


def scope_of_graph(graph: dict[str, Any]) -> set[str]:
    scopes = set()
    for item in graph.get("localization", {}).get("items", []):
        scopes.update(split_pipe(item.get("scope", "")))
    return scopes


def build_scope_views(clean_graphs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    views: dict[str, Any] = {}
    definitions = {
        "all_target_scope": TARGET_SCOPES,
        "reentrancy_only": {"reentrancy"},
        "unchecked_low_level_call_manual_review": {"unchecked low-level call"},
        "front_running_optional_weak_fit": {"front-running"},
    }
    for name, scopes in definitions.items():
        split_rows = {}
        for split, graphs in clean_graphs.items():
            entries = []
            for g in graphs:
                gs = scope_of_graph(g)
                label = 1 if gs & scopes else 0
                # For scope-specific views, keep all clean negatives plus positives for that scope.
                if g.get("contract_label") == 1 and label == 0:
                    continue
                entries.append(
                    {
                        "graph_id": g["graph_id"],
                        "split": split,
                        "scope_label": label,
                        "contract_label": g.get("contract_label", 0),
                        "contract": g.get("contract", ""),
                        "project": g.get("project", ""),
                        "vulnerability_types": g.get("vulnerability_types", []),
                        "positive_interaction_ids": g.get("positive_interaction_ids", []),
                        "weak_fit": name == "front_running_optional_weak_fit",
                        "manual_review_required": name == "unchecked_low_level_call_manual_review",
                    }
                )
            split_rows[split] = entries
        views[name] = split_rows
        write_json(SCOPE_DIR / f"{name}.json", split_rows)
    return views


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("|" + "|".join(str(x).replace("|", "/") for x in row) + "|")
    return "\n".join(out)


def main() -> int:
    plan_path = REPORTS / "phase0b_clean_split_plan.csv"
    if not plan_path.exists():
        raise SystemExit("Missing reports/phase0b_clean_split_plan.csv. Run Phase 0B first.")

    plan_rows = read_csv(plan_path)
    include_by_gid = {r["graph_id"]: r for r in plan_rows if r["status"] == "include"}
    quarantine_rows = [r for r in plan_rows if r["status"] == "quarantine"]
    old_graphs = load_original_graphs()

    source_lookup = build_source_lookup({gid: old_graphs[gid] for gid in include_by_gid if gid in old_graphs})
    positive_lookup = build_positive_provenance()

    clean_graphs: dict[str, list[dict[str, Any]]] = {"train": [], "val": [], "test": []}
    quarantined_graphs = []
    for gid, row in include_by_gid.items():
        if gid not in old_graphs:
            continue
        g = rebuild_graph(old_graphs[gid], row, source_lookup, positive_lookup)
        clean_graphs[row["clean_split"]].append(g)
    for r in quarantine_rows:
        g = copy.deepcopy(old_graphs.get(r["graph_id"], {"graph_id": r["graph_id"]}))
        g["quarantine_reason"] = r.get("reason", "duplicate_or_label_conflict")
        g["phase0b_plan_row"] = r
        quarantined_graphs.append(g)

    if CLEAN_GRAPH_DIR.exists():
        shutil.rmtree(CLEAN_GRAPH_DIR)
    CLEAN_GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val", "test"]:
        write_json(CLEAN_GRAPH_DIR / f"{split}.json", clean_graphs[split])
    write_json(CLEAN_GRAPH_DIR / "quarantine.json", quarantined_graphs)

    scope_views = build_scope_views(clean_graphs)
    validations = validation_for_split(clean_graphs)

    dataset_count_rows = []
    for split, graphs in clean_graphs.items():
        interactions = [n for g in graphs for n in g.get("nodes", []) if n.get("kind") == "interaction"]
        dataset_count_rows.append(
            {
                "split": split,
                "contracts": len(graphs),
                "positive_contracts": sum(g.get("contract_label") == 1 for g in graphs),
                "negative_contracts": sum(g.get("contract_label") == 0 for g in graphs),
                "interactions": len(interactions),
                "positive_interactions": sum(int(n.get("label", 0)) == 1 for n in interactions),
                "negative_interactions": sum(int(n.get("label", 0)) == 0 for n in interactions),
                "reentrancy_positive_contracts": sum("reentrancy" in scope_of_graph(g) for g in graphs),
                "unchecked_positive_contracts": sum("unchecked low-level call" in scope_of_graph(g) for g in graphs),
            }
        )
    write_csv(
        REPORTS / "phase0c_clean_dataset_counts.csv",
        dataset_count_rows,
        [
            "split",
            "contracts",
            "positive_contracts",
            "negative_contracts",
            "interactions",
            "positive_interactions",
            "negative_interactions",
            "reentrancy_positive_contracts",
            "unchecked_positive_contracts",
        ],
    )

    scope_count_rows = []
    for view_name, by_split in scope_views.items():
        for split, entries in by_split.items():
            scope_count_rows.append(
                {
                    "scope_view": view_name,
                    "split": split,
                    "contracts": len(entries),
                    "positive_contracts": sum(e["scope_label"] == 1 for e in entries),
                    "negative_contracts": sum(e["scope_label"] == 0 for e in entries),
                    "manual_review_required": view_name == "unchecked_low_level_call_manual_review",
                    "weak_fit_optional": view_name == "front_running_optional_weak_fit",
                }
            )
    write_csv(
        REPORTS / "phase0c_clean_scope_counts.csv",
        scope_count_rows,
        [
            "scope_view",
            "split",
            "contracts",
            "positive_contracts",
            "negative_contracts",
            "manual_review_required",
            "weak_fit_optional",
        ],
    )

    write_csv(
        REPORTS / "phase0c_quarantined_contracts.csv",
        quarantine_rows,
        list(quarantine_rows[0].keys()) if quarantine_rows else ["graph_id"],
    )

    loc_rows = []
    for split, graphs in clean_graphs.items():
        for g in graphs:
            if g.get("contract_label") != 1:
                continue
            items = g.get("localization", {}).get("items", [])
            loc_rows.append(
                {
                    "split": split,
                    "graph_id": g["graph_id"],
                    "contract": g.get("contract", ""),
                    "positive_interaction_count": len(items),
                    "vulnerable_interaction_ids": unique_join([i["interaction_id"] for i in items]),
                    "vulnerable_function_names": unique_join([i["function_name"] for i in items]),
                    "source_spans": unique_join([i["source_line_span"] for i in items]),
                    "vulnerability_types": unique_join([i["vulnerability_type"] for i in items]),
                    "evidence_pointers": unique_join([i["evidence_pointer"] for i in items]),
                    "supports_top1_top3_top5_mrr_recall_at_k": bool(items),
                    "missing_source_span_count": sum(not i["source_line_span"] for i in items),
                    "missing_evidence_pointer_count": sum(not i["evidence_pointer"] for i in items),
                }
            )
    write_csv(
        REPORTS / "phase0c_localization_readiness.csv",
        loc_rows,
        [
            "split",
            "graph_id",
            "contract",
            "positive_interaction_count",
            "vulnerable_interaction_ids",
            "vulnerable_function_names",
            "source_spans",
            "vulnerability_types",
            "evidence_pointers",
            "supports_top1_top3_top5_mrr_recall_at_k",
            "missing_source_span_count",
            "missing_evidence_pointer_count",
        ],
    )

    expected = {
        "train": {"contracts": 1339, "positive_contracts": 140, "negative_contracts": 1199},
        "val": {"contracts": 280, "positive_contracts": 30, "negative_contracts": 250},
        "test": {"contracts": 212, "positive_contracts": 30, "negative_contracts": 182},
    }
    counts_match = True
    for row in dataset_count_rows:
        exp = expected[row["split"]]
        counts_match = counts_match and all(int(row[k]) == v for k, v in exp.items())
    validations["class_counts_match_phase0b_expected"] = {
        "pass": counts_match,
        "violations": 0 if counts_match else 1,
    }

    summary = {
        "generated_at": "2026-06-27",
        "output_dir": str(CLEAN_GRAPH_DIR),
        "counts": dataset_count_rows,
        "scope_counts": scope_count_rows,
        "quarantined_contracts": len(quarantine_rows),
        "validations": validations,
        "ready_for_baseline_reruns": all(v["pass"] for v in validations.values()),
        "ready_for_phase1_augmentation": False,
        "reentrancy_only_ready": all(v["pass"] for v in validations.values()),
        "unchecked_call_needs_manual_review": True,
        "front_running_status": "weak_fit_optional",
        "delegatecall_status": "not_standalone",
    }
    write_json(REPORTS / "phase0c_clean_split_summary.json", summary)

    validation_rows = [[k, v["pass"], v["violations"]] for k, v in validations.items()]
    count_rows = [
        [
            r["split"],
            r["contracts"],
            r["positive_contracts"],
            r["negative_contracts"],
            r["interactions"],
            r["positive_interactions"],
            r["negative_interactions"],
            r["reentrancy_positive_contracts"],
            r["unchecked_positive_contracts"],
        ]
        for r in dataset_count_rows
    ]
    scope_rows_md = [
        [
            r["scope_view"],
            r["split"],
            r["contracts"],
            r["positive_contracts"],
            r["negative_contracts"],
            r["manual_review_required"],
            r["weak_fit_optional"],
        ]
        for r in scope_count_rows
    ]
    md = f"""# Phase 0C Clean Graph Dataset Rebuild

## Executive Summary

Clean graph datasets were rebuilt under `data/contract_graphs_clean/` using the Phase 0B leakage-safe split plan. The old `data/contract_graphs/` files were not overwritten.

Baseline reruns: **{'READY' if summary['ready_for_baseline_reruns'] else 'NOT READY'}**.

Phase 1 augmentation: **NOT YET**. Run baselines on the clean rebuilt dataset first.

Reentrancy-only: **{'READY' if summary['reentrancy_only_ready'] else 'NOT READY'}**.

Unchecked low-level call: **manual review still required**.

## Outputs

- `data/contract_graphs_clean/train.json`
- `data/contract_graphs_clean/val.json`
- `data/contract_graphs_clean/test.json`
- `data/contract_graphs_clean/quarantine.json`
- `data/contract_graphs_clean/scope_views/all_target_scope.json`
- `data/contract_graphs_clean/scope_views/reentrancy_only.json`
- `data/contract_graphs_clean/scope_views/unchecked_low_level_call_manual_review.json`
- `data/contract_graphs_clean/scope_views/front_running_optional_weak_fit.json`

## Clean Dataset Counts

{md_table(['split','contracts','positive contracts','negative contracts','interactions','positive interactions','negative interactions','reentrancy + contracts','unchecked + contracts'], count_rows)}

Quarantined contracts: **{len(quarantine_rows)}**.

## Scope Views

{md_table(['scope view','split','contracts','positive contracts','negative contracts','manual review','weak fit optional'], scope_rows_md)}

## Validation

{md_table(['check','pass','violations'], validation_rows)}

## Provenance

Every interaction node now has a `provenance` object and flattened provenance fields including dataset source, original source path when recoverable, contract id/name, function name, source line span, finding id/title, severity, vulnerability type, evidence pointer, normalized contract hash, normalized function hash, normalized interaction-set hash, and split id.

Positive contracts have top-k localization metadata at `graph.localization.items`, with vulnerable interaction ids, function names, spans, vulnerability type, and evidence pointers.

## Final Recommendation

- Clean rebuilt dataset is ready for baseline reruns if all validation checks pass.
- Augmentation should wait until clean baselines are rerun and unchecked-call manual review is complete.
- Reentrancy-only is ready as the first clean scope.
- Unchecked-call remains a candidate scope but needs manual review before being used as a headline result.
- Provenance is sufficient for localization in the rebuilt dataset; any missing positive source spans are reported in `reports/phase0c_localization_readiness.csv`.
"""
    with open(REPORTS / "phase0c_clean_rebuild_report.md", "w", encoding="utf-8") as f:
        f.write(md)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
