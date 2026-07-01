#!/usr/bin/env python3
"""Phase 0B raw dataset coverage audit for HyperVul.

This script is intentionally read-only for existing datasets. It traces raw
DAppSCAN/FORGE findings into constructable positive hyperedges and then into the
current contract graph dataset. It writes derived audit artifacts under reports/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

sys.path.append(str(ROOT / "scripts"))
import negative_hyperedge_sampling as nhs  # noqa: E402


GRAPH_DIR = ROOT / "data" / "contract_graphs"
DAPPSCAN_ROOT = ROOT / "data" / "DAppSCAN"
SWC_SOURCE_DIR = DAPPSCAN_ROOT / "DAppSCAN-source" / "SWCsource"
FORGE_VULN_DIR = ROOT / "data" / "FORGE-Curated" / "flatten" / "vfp-vuln"
RESULTS_DIR = ROOT / "experiments" / "results"

TARGET_SWCS = {
    "SWC-107": "Reentrancy (SWC-107)",
    "SWC-104": "Unchecked Call Return (SWC-104)",
    "SWC-112": "Delegatecall (SWC-112)",
    "SWC-114": "Front-running / Tx Order (SWC-114)",
}


def norm_source(src: str) -> str:
    try:
        return nhs.normalize_source(src or "")
    except Exception:
        src = src or ""
        src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
        src = re.sub(r"//.*", " ", src)
        return re.sub(r"\s+", " ", src).strip()


def source_hash(src: str) -> str:
    return hashlib.sha256(norm_source(src).encode("utf-8")).hexdigest()


def short(text: Any, n: int = 160) -> str:
    s = "" if text is None else str(text).replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 3] + "..."


def find_project_root_for_rel(rel_path: str) -> Path:
    """DAppSCAN project root is the path under DAppSCAN-source/contracts/<audit>/<repo>."""
    p = DAPPSCAN_ROOT / rel_path
    contracts_root = DAPPSCAN_ROOT / "DAppSCAN-source" / "contracts"
    try:
        rel = p.relative_to(contracts_root)
    except ValueError:
        return p.parent
    parts = rel.parts
    if len(parts) >= 2:
        return contracts_root / parts[0] / parts[1]
    return p.parent


def parse_line_span(line: str) -> tuple[int | None, int | None]:
    nums = [int(x) for x in re.findall(r"L(\d+)", line or "")]
    if not nums:
        return None, None
    return min(nums), max(nums)


def extract_forge_loc(loc: str) -> tuple[str, str, str]:
    """Return (file basename, function, line-ish text) from FORGE location string."""
    loc = loc or ""
    file_part = loc
    func = ""
    if "::" in loc:
        file_part, rest = loc.split("::", 1)
        func = rest.split("#", 1)[0].strip()
    elif "#" in loc:
        file_part = loc.split("#", 1)[0]
    return Path(file_part.strip()).name, func, loc


def forge_heuristic_vtype(finding: dict[str, Any]) -> str:
    text = " ".join(
        str(finding.get(k, "")) for k in ["title", "description", "recommendation"]
    ).lower()
    cwes = {
        c
        for values in (finding.get("category") or {}).values()
        for c in values
        if isinstance(c, str)
    }
    if re.search(r"re-?entr|read.?only re-?entr|callback", text) or cwes & {
        "CWE-841",
        "CWE-1265",
    }:
        return "Reentrancy (heuristic)"
    if re.search(r"unchecked.*call|return value|low.?level call|\\.call", text):
        return "Unchecked Call Return (heuristic)"
    if "delegatecall" in text or "CWE-829" in cwes:
        return "Delegatecall (heuristic)"
    if re.search(r"front.?run|transaction order|sandwich|mev", text):
        return "Front-running / Tx Order (heuristic)"
    if cwes:
        return "CWE:" + ",".join(sorted(cwes))
    return ""


def scope_key(vtype: str) -> str:
    v = (vtype or "").lower()
    if "reentrancy" in v or "re-entr" in v or "swc-107" in v:
        return "reentrancy"
    if "unchecked" in v or "swc-104" in v:
        return "unchecked low-level call"
    if "delegatecall" in v or "swc-112" in v:
        return "delegatecall"
    if "front" in v or "tx order" in v or "transaction order" in v or "swc-114" in v:
        return "front-running"
    return "other"


def dapp_swc_code(category: str) -> str:
    m = re.match(r"(SWC-\d+)", category or "")
    return m.group(1) if m else ""


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return json.load(f)


def contract_hash_from_source(src: str, contract: str | None = None) -> str:
    """Hash parsed contract text if possible, otherwise whole source."""
    if not src:
        return ""
    if contract:
        try:
            parsed = nhs.parse_contracts(src)
            node = parsed.get(contract).node if contract in parsed else None
            if node is not None:
                return source_hash(nhs.node_text(node))
        except Exception:
            pass
    return source_hash(src)


@dataclass
class RawFinding:
    raw_id: str
    dataset: str
    project: str
    file_path: str
    contract: str
    function: str
    line_span: str
    finding_id: str
    title: str
    severity: str
    vulnerability_type: str
    scope: str
    source_available: bool
    vtype_recoverable: bool
    location_available: bool
    evidence_pointer: str
    normalized_source_hash: str = ""
    normalized_contract_hash: str = ""
    converted_to_hyperedge: bool = False
    included_in_graph: bool = False
    graph_id: str = ""
    graph_split: str = ""
    dropped_reason: str = ""


def build_dapp_raw_findings() -> list[RawFinding]:
    rows: list[RawFinding] = []
    for jf in sorted(SWC_SOURCE_DIR.glob("**/*.json")):
        try:
            data = load_json(jf)
        except Exception:
            continue
        rel_path = data.get("filePath", "")
        abs_path = DAPPSCAN_ROOT / rel_path
        project_root = ""
        try:
            project_root = str(find_project_root_for_rel(rel_path).relative_to(DAPPSCAN_ROOT))
        except Exception:
            project_root = str(find_project_root_for_rel(rel_path))
        src = abs_path.read_text(encoding="utf-8", errors="ignore") if abs_path.exists() else ""
        file_contracts = {}
        if src:
            try:
                file_contracts = nhs.parse_contracts(src)
            except Exception:
                file_contracts = {}
        for i, swc in enumerate(data.get("SWCs", [])):
            category = swc.get("category", "")
            code = dapp_swc_code(category)
            vtype = TARGET_SWCS.get(code, category)
            fn = swc.get("function") or ""
            contract = ""
            if fn and fn != "N/A":
                for cn, ci in file_contracts.items():
                    try:
                        funcs = nhs.resolve_all_functions(cn, file_contracts)
                    except Exception:
                        funcs = ci.functions
                    if fn in funcs:
                        contract = cn
                        break
            start, end = parse_line_span(swc.get("lineNumber", ""))
            rows.append(
                RawFinding(
                    raw_id=f"DAPP::{rel_path}::{i}",
                    dataset="DAppSCAN",
                    project=project_root,
                    file_path=rel_path,
                    contract=contract,
                    function=fn if fn != "N/A" else "",
                    line_span=swc.get("lineNumber", ""),
                    finding_id=str(i),
                    title=category,
                    severity="",
                    vulnerability_type=vtype,
                    scope=scope_key(vtype),
                    source_available=abs_path.exists(),
                    vtype_recoverable=bool(vtype),
                    location_available=bool(fn and fn != "N/A" and swc.get("lineNumber")),
                    evidence_pointer=f"{rel_path}:{start or ''}-{end or ''}",
                    normalized_contract_hash=contract_hash_from_source(src, contract) if contract else "",
                )
            )
    return rows


def build_forge_raw_findings() -> list[RawFinding]:
    rows: list[RawFinding] = []
    for vf in sorted(FORGE_VULN_DIR.glob("vfp_*.json")):
        try:
            data = load_json(vf)
        except Exception:
            continue
        vfp_id = data.get("vfp_id") or vf.stem
        affected = data.get("affected_files") or {}
        parsed_by_file: dict[str, dict[str, Any]] = {}
        merged_contracts: dict[str, Any] = {}
        for fname, src in affected.items():
            try:
                parsed = nhs.parse_contracts(src)
            except Exception:
                parsed = {}
            parsed_by_file[Path(fname).name] = parsed
            merged_contracts.update(parsed)
        for finding in data.get("findings", []):
            fid = str(finding.get("id", ""))
            vtype = forge_heuristic_vtype(finding)
            locations = finding.get("location") or []
            files = finding.get("files") or []
            if not locations:
                locations = [files[0] if files else ""]
            for li, loc in enumerate(locations):
                file_base, func, loc_text = extract_forge_loc(loc)
                if not file_base and files:
                    file_base = Path(files[0]).name
                source_key = next((k for k in affected if Path(k).name == file_base), file_base)
                src = affected.get(source_key, "")
                parsed = parsed_by_file.get(file_base, {})
                contract = ""
                if func:
                    for cn in merged_contracts:
                        try:
                            funcs = nhs.resolve_all_functions(cn, merged_contracts)
                        except Exception:
                            funcs = merged_contracts[cn].functions
                        if func in funcs:
                            contract = cn
                            break
                rows.append(
                    RawFinding(
                        raw_id=f"FORGE::{vfp_id}::{fid}::{li}",
                        dataset="FORGE",
                        project=vfp_id,
                        file_path=source_key,
                        contract=contract,
                        function=func,
                        line_span=loc_text,
                        finding_id=fid,
                        title=finding.get("title", ""),
                        severity=finding.get("severity", ""),
                        vulnerability_type=vtype,
                        scope=scope_key(vtype),
                        source_available=bool(src),
                        vtype_recoverable=bool(vtype),
                        location_available=bool(loc_text or func or files),
                        evidence_pointer=f"data/FORGE-Curated/flatten/vfp-vuln/{vfp_id}.json#{fid}",
                        normalized_contract_hash=contract_hash_from_source(src, contract) if contract else "",
                    )
                )
    return rows


def load_constructable_positives() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    rows = []
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in load_json(RESULTS_DIR / "dappscan_ast_constructable_hyperedges.json"):
        rec = dict(p)
        rec["dataset"] = "DAppSCAN"
        rec["project"] = p.get("project_root", "")
        rec["function"] = p.get("ast_function") or p.get("function") or p.get("annotated_function")
        rec["vulnerability_type"] = TARGET_SWCS.get(p.get("swc_code", ""), p.get("category", ""))
        rows.append(rec)
        key = f"DAppSCAN::{p.get('filePath','')}::{p.get('category','')}::{p.get('annotated_function') or p.get('ast_function') or ''}::{p.get('lineNumber','')}"
        by_key[key].append(rec)
        if p.get("normalized_source_hash"):
            by_key[f"HASH::{p['normalized_source_hash']}"].append(rec)
    for p in load_json(RESULTS_DIR / "forge_ast_constructable_hyperedges.json"):
        rec = dict(p)
        rec["dataset"] = "FORGE"
        rec["project"] = p.get("vfp_id", "")
        rec["function"] = p.get("function", "")
        rows.append(rec)
        key = f"FORGE::{p.get('vfp_id','')}::{p.get('finding_id','')}"
        by_key[key].append(rec)
    return rows, by_key


def load_graph_interactions() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    rows = []
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for split in ["train", "val", "test"]:
        for g in load_json(GRAPH_DIR / f"{split}.json"):
            for n in g.get("nodes", []):
                if n.get("kind") != "interaction":
                    continue
                h = source_hash(n.get("function_source", ""))
                rec = {
                    "split": split,
                    "graph_id": g.get("graph_id", ""),
                    "dataset": "FORGE" if g.get("source") == "FORGE" else "DAppSCAN",
                    "source": g.get("source", ""),
                    "project": g.get("project", ""),
                    "contract": g.get("contract", ""),
                    "function": n.get("function", ""),
                    "label": int(n.get("label", 0)),
                    "normalized_source_hash": h,
                    "state_vars_accessed": n.get("state_vars_accessed") or [],
                    "external_calls": n.get("external_calls") or [],
                    "function_source": n.get("function_source", ""),
                }
                rows.append(rec)
                by_key[f"{rec['dataset']}::{rec['project']}::{rec['contract']}::{rec['function']}"].append(rec)
                by_key[f"HASH::{h}"].append(rec)
    return rows, by_key


def raw_constructable_keys(raw: RawFinding) -> list[str]:
    if raw.dataset == "DAppSCAN":
        return [
            f"DAppSCAN::{raw.file_path}::{raw.title}::{raw.function}::{raw.line_span}",
        ]
    return [f"FORGE::{raw.project}::{raw.finding_id}"]


def determine_constructability_reason(raw: RawFinding) -> str:
    if raw.converted_to_hyperedge and not raw.included_in_graph:
        return "converted_but_not_in_current_graph_dataset"
    if raw.converted_to_hyperedge:
        return ""
    if not raw.source_available:
        return "missing_source_file"
    if not raw.vulnerability_type:
        return "missing_vulnerability_type"
    if raw.scope == "other":
        return "outside_priority_interaction_scope"
    if not raw.function:
        return "missing_or_NA_function_location"
    if not raw.contract:
        return "function_not_resolved_to_contract"
    return "not_constructable_as_state_plus_external_call_hyperedge"


def enrich_raw_rows(
    raw_rows: list[RawFinding],
    construct_by_key: dict[str, list[dict[str, Any]]],
    graph_by_key: dict[str, list[dict[str, Any]]],
) -> None:
    for raw in raw_rows:
        cons = []
        for k in raw_constructable_keys(raw):
            cons.extend(construct_by_key.get(k, []))
        if cons:
            raw.converted_to_hyperedge = True
            c = cons[0]
            raw.contract = raw.contract or c.get("contract", "")
            raw.function = raw.function or c.get("function", "")
            raw.normalized_source_hash = c.get("normalized_source_hash", "")
            if not raw.normalized_source_hash:
                # Forge constructable rows do not always carry the hash; graph join below can.
                raw.normalized_source_hash = ""
            if raw.dataset == "FORGE" and scope_key(raw.vulnerability_type) == "other":
                raw.vulnerability_type = c.get("vulnerability_type") or raw.vulnerability_type
                raw.scope = scope_key(raw.vulnerability_type)
        graph_matches = []
        if raw.converted_to_hyperedge:
            if raw.dataset == "DAppSCAN" and raw.normalized_source_hash:
                graph_matches.extend(graph_by_key.get(f"HASH::{raw.normalized_source_hash}", []))
            if raw.contract and raw.function:
                graph_matches.extend(
                    graph_by_key.get(f"{raw.dataset}::{raw.project}::{raw.contract}::{raw.function}", [])
                )
        graph_matches = [g for g in graph_matches if int(g.get("label", 0)) == 1]
        if graph_matches:
            g = graph_matches[0]
            raw.included_in_graph = True
            raw.graph_id = g["graph_id"]
            raw.graph_split = g["split"]
            raw.normalized_source_hash = raw.normalized_source_hash or g["normalized_source_hash"]
        raw.dropped_reason = determine_constructability_reason(raw)


def build_contract_metadata(
    graph_rows: list[dict[str, Any]],
    raw_rows: list[RawFinding],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return enriched contract rows, duplicate group rows, label conflict rows."""
    raw_by_positive_node: dict[tuple[str, str, str, str], RawFinding] = {}
    raw_by_hash: dict[str, RawFinding] = {}
    for r in raw_rows:
        if r.included_in_graph and r.contract and r.function:
            raw_by_positive_node[(r.dataset, r.project, r.contract, r.function)] = r
        if r.normalized_source_hash:
            raw_by_hash[r.normalized_source_hash] = r

    # Build per-graph aggregates.
    graphs = {}
    graph_nodes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for split in ["train", "val", "test"]:
        for g in load_json(GRAPH_DIR / f"{split}.json"):
            graphs[g["graph_id"]] = g | {"split": split}
    for r in graph_rows:
        graph_nodes[r["graph_id"]].append(r)

    contract_rows: list[dict[str, Any]] = []
    for gid, g in graphs.items():
        nodes = graph_nodes[gid]
        function_hashes = sorted(n["normalized_source_hash"] for n in nodes)
        contract_signature_hash = hashlib.sha256("|".join(function_hashes).encode()).hexdigest()
        pos_nodes = [n for n in nodes if n["label"] == 1]
        pos_raw = None
        for n in pos_nodes:
            pos_raw = raw_by_positive_node.get((n["dataset"], n["project"], n["contract"], n["function"]))
            if pos_raw:
                break
        vtypes = sorted(
            {
                raw_by_positive_node[(n["dataset"], n["project"], n["contract"], n["function"])].vulnerability_type
                for n in pos_nodes
                if (n["dataset"], n["project"], n["contract"], n["function"]) in raw_by_positive_node
            }
        )
        scopes = sorted({scope_key(v) for v in vtypes if v})
        source_file = pos_raw.file_path if pos_raw else ""
        line_span = pos_raw.line_span if pos_raw else ""
        contract_hash = pos_raw.normalized_contract_hash if pos_raw else ""
        if not contract_hash:
            # Fall back to graph interaction set hash; weaker than full contract hash.
            contract_hash = contract_signature_hash
        contract_rows.append(
            {
                "split": g["split"],
                "graph_id": gid,
                "dataset": "FORGE" if g.get("source") == "FORGE" else "DAppSCAN",
                "source": g.get("source", ""),
                "project": g.get("project", ""),
                "contract": g.get("contract", ""),
                "source_file": source_file,
                "contract_label": 1 if g.get("n_pos", 0) > 0 else 0,
                "n_pos": g.get("n_pos", 0),
                "n_neg": g.get("n_neg", 0),
                "interaction_count": g.get("n_pos", 0) + g.get("n_neg", 0),
                "vulnerability_types": "|".join(vtypes),
                "scopes": "|".join(scopes),
                "primary_line_span": line_span,
                "normalized_contract_hash": contract_hash,
                "contract_signature_hash": contract_signature_hash,
                "function_hashes": "|".join(function_hashes),
                "family_key": f"{g.get('source')}::{g.get('project')}",
            }
        )

    # Duplicate groups.
    dup_rows: list[dict[str, Any]] = []
    for kind, field in [
        ("exact_contract_hash", "normalized_contract_hash"),
        ("exact_interaction_set_hash", "contract_signature_hash"),
    ]:
        bucket = defaultdict(list)
        for r in contract_rows:
            if r[field]:
                bucket[r[field]].append(r)
        for key, members in bucket.items():
            if len(members) < 2:
                continue
            dup_rows.append(
                {
                    "group_kind": kind,
                    "group_key": key,
                    "member_count": len(members),
                    "splits": "|".join(sorted({m["split"] for m in members})),
                    "labels": "|".join(map(str, sorted({m["contract_label"] for m in members}))),
                    "members": " ; ".join(f"{m['split']}:{m['graph_id']}" for m in members[:30]),
                    "recommended_action": "same_split_or_merge; quarantine_if_labels_conflict",
                }
            )

    # Near duplicate by same contract name and Jaccard of function hashes.
    by_name = defaultdict(list)
    for r in contract_rows:
        by_name[r["contract"]].append(r)
    for cname, members in by_name.items():
        if len(members) < 2:
            continue
        seen = set()
        for i, a in enumerate(members):
            ah = set(a["function_hashes"].split("|")) if a["function_hashes"] else set()
            for b in members[i + 1 :]:
                bh = set(b["function_hashes"].split("|")) if b["function_hashes"] else set()
                if not ah or not bh:
                    continue
                j = len(ah & bh) / len(ah | bh)
                if j >= 0.80:
                    key = tuple(sorted([a["graph_id"], b["graph_id"]]))
                    if key in seen:
                        continue
                    seen.add(key)
                    dup_rows.append(
                        {
                            "group_kind": "near_duplicate_same_contract_name",
                            "group_key": f"{cname}:{j:.3f}",
                            "member_count": 2,
                            "splits": "|".join(sorted({a["split"], b["split"]})),
                            "labels": "|".join(map(str, sorted({a["contract_label"], b["contract_label"]}))),
                            "members": f"{a['split']}:{a['graph_id']} ; {b['split']}:{b['graph_id']}",
                            "recommended_action": "same_split_or_quarantine",
                        }
                    )

    # Exact function-source label conflicts.
    by_fhash = defaultdict(list)
    for n in graph_rows:
        by_fhash[n["normalized_source_hash"]].append(n)
    conflict_rows = []
    for h, members in by_fhash.items():
        labels = {m["label"] for m in members}
        if len(labels) > 1:
            conflict_rows.append(
                {
                    "conflict_kind": "exact_function_hash_conflicting_label",
                    "normalized_source_hash": h,
                    "member_count": len(members),
                    "splits": "|".join(sorted({m["split"] for m in members})),
                    "labels": "|".join(map(str, sorted(labels))),
                    "members": " ; ".join(
                        f"{m['split']}:{m['graph_id']}::{m['function']}[y={m['label']}]"
                        for m in members[:40]
                    ),
                    "recommended_action": "positive_wins_if_verified_else_quarantine_group",
                }
            )

    return contract_rows, dup_rows, conflict_rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("|" + "|".join(str(x).replace("|", "/") for x in row) + "|")
    return "\n".join(out)


def main() -> int:
    dapp_raw = build_dapp_raw_findings()
    forge_raw = build_forge_raw_findings()
    raw_rows = dapp_raw + forge_raw
    construct_rows, construct_by_key = load_constructable_positives()
    graph_rows, graph_by_key = load_graph_interactions()
    enrich_raw_rows(raw_rows, construct_by_key, graph_by_key)
    contract_rows, duplicate_rows, conflict_rows = build_contract_metadata(graph_rows, raw_rows)

    dropped = [asdict(r) for r in raw_rows if not r.included_in_graph]
    dropped_fields = list(asdict(raw_rows[0]).keys()) if raw_rows else []
    write_csv(REPORTS / "phase0b_dropped_findings.csv", dropped, dropped_fields)
    write_csv(
        REPORTS / "phase0b_label_conflicts.csv",
        conflict_rows,
        [
            "conflict_kind",
            "normalized_source_hash",
            "member_count",
            "splits",
            "labels",
            "members",
            "recommended_action",
        ],
    )
    write_csv(
        REPORTS / "phase0b_duplicate_groups.csv",
        duplicate_rows,
        [
            "group_kind",
            "group_key",
            "member_count",
            "splits",
            "labels",
            "members",
            "recommended_action",
        ],
    )

    # This contract metadata file is an implementation detail for the split builder.
    write_csv(
        REPORTS / "phase0b_contract_metadata.csv",
        contract_rows,
        [
            "split",
            "graph_id",
            "dataset",
            "source",
            "project",
            "contract",
            "source_file",
            "contract_label",
            "n_pos",
            "n_neg",
            "interaction_count",
            "vulnerability_types",
            "scopes",
            "primary_line_span",
            "normalized_contract_hash",
            "contract_signature_hash",
            "function_hashes",
            "family_key",
        ],
    )

    def raw_summary(dataset: str) -> dict[str, Any]:
        rows = [r for r in raw_rows if r.dataset == dataset]
        target = [r for r in rows if r.scope in {"reentrancy", "unchecked low-level call", "delegatecall", "front-running"}]
        return {
            "raw_finding_locations": len(rows),
            "raw_target_scope_locations": len(target),
            "source_files_available": sum(r.source_available for r in rows),
            "recoverable_vulnerability_type": sum(r.vtype_recoverable for r in rows),
            "source_location_or_evidence": sum(r.location_available for r in rows),
            "converted_to_constructable_hyperedge": sum(r.converted_to_hyperedge for r in rows),
            "included_in_current_graph_dataset": sum(r.included_in_graph for r in rows),
            "dropped_by_reason": dict(Counter(r.dropped_reason for r in rows if not r.included_in_graph)),
            "target_scope_by_type": dict(Counter(r.scope for r in target)),
            "constructable_by_type": dict(Counter(r.scope for r in rows if r.converted_to_hyperedge)),
            "graph_included_by_type": dict(Counter(r.scope for r in rows if r.included_in_graph)),
        }

    # Contract cleanup estimates after deterministic quarantines.
    duplicate_member_graphs = set()
    for r in duplicate_rows:
        if r["group_kind"] in {"exact_contract_hash", "exact_interaction_set_hash"} and "|" in r["splits"]:
            for part in r["members"].split(" ; "):
                if ":" in part:
                    duplicate_member_graphs.add(part.split(":", 1)[1])
    conflict_member_graphs = set()
    for r in conflict_rows:
        for part in r["members"].split(" ; "):
            if ":" not in part:
                continue
            rest = part.split(":", 1)[1]
            gid = rest.rsplit("::", 1)[0] if "::" in rest else rest
            conflict_member_graphs.add(gid)
    quarantined = duplicate_member_graphs | conflict_member_graphs
    clean_contracts = [r for r in contract_rows if r["graph_id"] not in quarantined]

    scope_contract_counts = {}
    for scope in ["reentrancy", "unchecked low-level call", "delegatecall", "front-running"]:
        pos = [r for r in clean_contracts if r["contract_label"] == 1 and scope in r["scopes"].split("|")]
        scope_contract_counts[scope] = {
            "positive_contracts_after_quarantine": len(pos),
            "train_current": sum(r["split"] == "train" for r in pos),
            "val_current": sum(r["split"] == "val" for r in pos),
            "test_current": sum(r["split"] == "test" for r in pos),
        }

    summary = {
        "generated_at": "2026-06-27",
        "raw_coverage": {
            "DAppSCAN": raw_summary("DAppSCAN"),
            "FORGE": raw_summary("FORGE"),
            "combined": {
                "raw_finding_locations": len(raw_rows),
                "converted_to_constructable_hyperedge": sum(r.converted_to_hyperedge for r in raw_rows),
                "included_in_current_graph_dataset": sum(r.included_in_graph for r in raw_rows),
            },
        },
        "current_graph_interactions": {
            "total": len(graph_rows),
            "positive": sum(r["label"] == 1 for r in graph_rows),
            "negative": sum(r["label"] == 0 for r in graph_rows),
        },
        "current_graph_contracts": {
            "total": len(contract_rows),
            "positive": sum(int(r["contract_label"]) == 1 for r in contract_rows),
            "negative": sum(int(r["contract_label"]) == 0 for r in contract_rows),
        },
        "duplicates_and_conflicts": {
            "duplicate_groups": len(duplicate_rows),
            "label_conflicts": len(conflict_rows),
            "quarantined_contracts_estimate": len(quarantined),
        },
        "after_quarantine_estimate": {
            "contracts_total": len(clean_contracts),
            "contracts_positive": sum(int(r["contract_label"]) == 1 for r in clean_contracts),
            "contracts_negative": sum(int(r["contract_label"]) == 0 for r in clean_contracts),
            "scope_positive_contracts": scope_contract_counts,
        },
        "cleanup_rules": [
            "Group all contracts connected by project/family, source file, normalized contract hash, exact interaction-set hash, or exact function hash before splitting.",
            "Merge exact duplicates within a group when labels agree and provenance points to the same finding.",
            "If exact normalized function source has conflicting labels, verified positive raw finding wins only when provenance is explicit; otherwise quarantine the full connected group.",
            "Do not allow the same normalized contract hash, source file, project/family, or function source hash across train/val/test.",
            "Prioritize reentrancy for the first clean split; run unchecked-call only after manual review of positives without explicit low-level-call evidence.",
        ],
    }
    with open(REPORTS / "phase0b_raw_coverage_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    cov_rows = []
    for dataset in ["DAppSCAN", "FORGE"]:
        s = summary["raw_coverage"][dataset]
        cov_rows.append(
            [
                dataset,
                s["raw_finding_locations"],
                s["raw_target_scope_locations"],
                s["source_files_available"],
                s["recoverable_vulnerability_type"],
                s["source_location_or_evidence"],
                s["converted_to_constructable_hyperedge"],
                s["included_in_current_graph_dataset"],
            ]
        )
    scope_rows = []
    for scope in ["reentrancy", "unchecked low-level call", "delegatecall", "front-running"]:
        d = scope_contract_counts[scope]
        scope_rows.append(
            [
                scope,
                d["positive_contracts_after_quarantine"],
                d["train_current"],
                d["val_current"],
                d["test_current"],
            ]
        )
    dropped_rows = []
    for dataset in ["DAppSCAN", "FORGE"]:
        for reason, count in summary["raw_coverage"][dataset]["dropped_by_reason"].items():
            dropped_rows.append([dataset, reason or "included", count])

    md = f"""# Phase 0B Raw Coverage Audit

## Executive Summary

This audit traces raw DAppSCAN and FORGE-Curated finding locations through the current HyperVul pipeline:

`raw finding -> source contract/function -> constructable state-plus-external-call hyperedge -> current graph positive node`.

The current graph dataset is still **not ready for Phase 1 augmentation**. The raw datasets do contain enough reentrancy positives to build a clean contract-level split, but duplicate/conflict quarantine and split rebuilding must happen first.

## Raw Coverage

{md_table(['dataset','raw finding locations','target-scope locations','source available','vtype recoverable','location/evidence','constructable hyperedges','included in current graphs'], cov_rows)}

Notes:

- DAppSCAN vulnerability type is recovered directly from SWC category.
- FORGE-Curated vulnerability type is recovered from finding text/CWE heuristics unless the finding already appears in a constructable positive record.
- Counts are location-level for FORGE when a single finding lists multiple vulnerable locations.

## Dropped Findings

{md_table(['dataset','drop reason','count'], dropped_rows)}

Full dropped finding rows are in `reports/phase0b_dropped_findings.csv`.

## Provenance Recovery

For graph positives, provenance can be recovered from raw records or constructable-positive records. Recovered fields include dataset, file path, contract, function, source line/location, finding id/title, severity, vulnerability type, evidence pointer, normalized function hash, and normalized contract/contract-signature hash.

The current `data/contract_graphs` files still do not store these fields natively, so regeneration with embedded provenance remains required.

## Duplicate and Conflict Resolution

Duplicate groups written: **{len(duplicate_rows)}** in `reports/phase0b_duplicate_groups.csv`.

Label conflicts written: **{len(conflict_rows)}** in `reports/phase0b_label_conflicts.csv`.

Recommended deterministic cleanup rules:

1. Group all contracts connected by project/family, source file, normalized contract hash, exact interaction-set hash, or exact function hash before splitting.
2. Merge exact duplicates within a group when labels agree and provenance points to the same finding.
3. If exact normalized function source has conflicting labels, verified positive raw finding wins only when provenance is explicit; otherwise quarantine the full connected group.
4. Do not allow the same normalized contract hash, source file, project/family, or function source hash across train/val/test.
5. Prioritize reentrancy for the first clean split; run unchecked-call only after manual review of positives without explicit low-level-call evidence.

Estimated quarantined contracts from exact duplicate/conflict rules: **{len(quarantined)}**.

## Clean-Split Readiness Estimate

After deterministic quarantine estimate:

- Contracts total: **{summary['after_quarantine_estimate']['contracts_total']}**
- Positive contracts: **{summary['after_quarantine_estimate']['contracts_positive']}**
- Negative contracts: **{summary['after_quarantine_estimate']['contracts_negative']}**

{md_table(['scope','positive contracts after quarantine','current train','current val','current test'], scope_rows)}

## Recommendation

- Reentrancy-only clean split: **ready to build, but not ready to use until the split plan is generated and graph provenance is regenerated**.
- Unchecked-call clean split: **needs manual review**, because many unchecked-call positives do not show explicit low-level-call evidence in the current graph text.
- Phase 1 augmentation: **do not proceed yet**. First apply the clean split strategy, quarantine ambiguous conflicts, and regenerate graph JSON with provenance fields.
"""
    with open(REPORTS / "phase0b_raw_coverage_audit.md", "w", encoding="utf-8") as f:
        f.write(md)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
