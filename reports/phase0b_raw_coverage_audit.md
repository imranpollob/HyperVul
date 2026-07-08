# Phase 0B Raw Coverage Audit

## Executive Summary

This audit traces raw DAppSCAN and FORGE-Curated finding locations through the current HyperVul pipeline:

`raw finding -> source contract/function -> constructable state-plus-external-call hyperedge -> current graph positive node`.

The current graph dataset is still **not ready for Phase 1 augmentation**. The raw datasets do contain enough reentrancy positives to build a clean contract-level split, but duplicate/conflict quarantine and split rebuilding must happen first.

## Raw Coverage

|dataset|raw finding locations|target-scope locations|source available|vtype recoverable|location/evidence|constructable hyperedges|included in current graphs|
|---|---|---|---|---|---|---|---|
|DAppSCAN|1646|352|1646|1646|1224|227|222|
|FORGE|1492|257|1411|1492|1492|141|87|

Notes:

- DAppSCAN vulnerability type is recovered directly from SWC category.
- FORGE-Curated vulnerability type is recovered from finding text/CWE heuristics unless the finding already appears in a constructable positive record.
- Counts are location-level for FORGE when a single finding lists multiple vulnerable locations.

## Dropped Findings

|dataset|drop reason|count|
|---|---|---|
|DAppSCAN|outside_priority_interaction_scope|1294|
|DAppSCAN|not_constructable_as_state_plus_external_call_hyperedge|112|
|DAppSCAN|missing_or_NA_function_location|10|
|DAppSCAN|function_not_resolved_to_contract|3|
|DAppSCAN|converted_but_not_in_current_graph_dataset|5|
|FORGE|outside_priority_interaction_scope|1113|
|FORGE|not_constructable_as_state_plus_external_call_hyperedge|69|
|FORGE|converted_but_not_in_current_graph_dataset|54|
|FORGE|missing_or_NA_function_location|79|
|FORGE|missing_source_file|69|
|FORGE|function_not_resolved_to_contract|21|

Full dropped finding rows are in `reports/phase0b_dropped_findings.csv`.

## Provenance Recovery

For graph positives, provenance can be recovered from raw records or constructable-positive records. Recovered fields include dataset, file path, contract, function, source line/location, finding id/title, severity, vulnerability type, evidence pointer, normalized function hash, and normalized contract/contract-signature hash.

The current `data/contract_graphs` files still do not store these fields natively, so regeneration with embedded provenance remains required.

## Duplicate and Conflict Resolution

Duplicate groups written: **608** in `reports/phase0b_duplicate_groups.csv`.

Label conflicts written: **10** in `reports/phase0b_label_conflicts.csv`.

Recommended deterministic cleanup rules:

1. Group all contracts connected by project/family, source file, normalized contract hash, exact interaction-set hash, or exact function hash before splitting.
2. Merge exact duplicates within a group when labels agree and provenance points to the same finding.
3. If exact normalized function source has conflicting labels, verified positive raw finding wins only when provenance is explicit; otherwise quarantine the full connected group.
4. Do not allow the same normalized contract hash, source file, project/family, or function source hash across train/val/test.
5. Prioritize reentrancy for the first clean split; run unchecked-call only after manual review of positives without explicit low-level-call evidence.

Estimated quarantined contracts from exact duplicate/conflict rules: **88**.

## Clean-Split Readiness Estimate

After deterministic quarantine estimate:

- Contracts total: **1831**
- Positive contracts: **200**
- Negative contracts: **1631**

|scope|positive contracts after quarantine|current train|current val|current test|
|---|---|---|---|---|
|reentrancy|86|63|12|11|
|unchecked low-level call|47|35|8|4|
|delegatecall|2|2|0|0|
|front-running|49|38|4|7|

## Recommendation

- Reentrancy-only clean split: **ready to build, but not ready to use until the split plan is generated and graph provenance is regenerated**.
- Unchecked-call clean split: **needs manual review**, because many unchecked-call positives do not show explicit low-level-call evidence in the current graph text.
- Phase 1 augmentation: **do not proceed yet**. First apply the clean split strategy, quarantine ambiguous conflicts, and regenerate graph JSON with provenance fields.
