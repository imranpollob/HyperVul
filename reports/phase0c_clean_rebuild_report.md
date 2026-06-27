# Phase 0C Clean Graph Dataset Rebuild

## Executive Summary

Clean graph datasets were rebuilt under `data/contract_graphs_clean/` using the Phase 0B leakage-safe split plan. The old `data/contract_graphs/` files were not overwritten.

Baseline reruns: **READY**.

Phase 1 augmentation: **NOT YET**. Run baselines on the clean rebuilt dataset first.

Reentrancy-only: **READY**.

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

|split|contracts|positive contracts|negative contracts|interactions|positive interactions|negative interactions|reentrancy + contracts|unchecked + contracts|
|---|---|---|---|---|---|---|---|---|
|train|1339|140|1199|9173|191|8982|75|31|
|val|280|30|250|1674|51|1623|14|11|
|test|212|30|182|1220|40|1180|16|6|

Quarantined contracts: **88**.

## Scope Views

|scope view|split|contracts|positive contracts|negative contracts|manual review|weak fit optional|
|---|---|---|---|---|---|---|
|all_target_scope|train|1339|140|1199|False|False|
|all_target_scope|val|280|30|250|False|False|
|all_target_scope|test|212|30|182|False|False|
|reentrancy_only|train|1274|75|1199|False|False|
|reentrancy_only|val|264|14|250|False|False|
|reentrancy_only|test|198|16|182|False|False|
|unchecked_low_level_call_manual_review|train|1230|31|1199|True|False|
|unchecked_low_level_call_manual_review|val|261|11|250|True|False|
|unchecked_low_level_call_manual_review|test|188|6|182|True|False|
|front_running_optional_weak_fit|train|1238|39|1199|False|True|
|front_running_optional_weak_fit|val|255|5|250|False|True|
|front_running_optional_weak_fit|test|191|9|182|False|True|

## Validation

|check|pass|violations|
|---|---|---|
|no_cross_split_contract_hash_leakage|True|0|
|no_cross_split_interaction_set_hash_leakage|True|0|
|no_cross_split_source_file_leakage|True|0|
|no_cross_split_function_hash_leakage|True|0|
|no_known_duplicate_conflict_leakage|True|0|
|all_interactions_map_to_contract|True|0|
|all_positive_contracts_have_localization_metadata|True|0|
|positive_nodes_missing_source_path|True|0|
|positive_nodes_missing_line_span|True|0|
|class_counts_match_phase0b_expected|True|0|

## Provenance

Every interaction node now has a `provenance` object and flattened provenance fields including dataset source, original source path when recoverable, contract id/name, function name, source line span, finding id/title, severity, vulnerability type, evidence pointer, normalized contract hash, normalized function hash, normalized interaction-set hash, and split id.

Positive contracts have top-k localization metadata at `graph.localization.items`, with vulnerable interaction ids, function names, spans, vulnerability type, and evidence pointers.

## Final Recommendation

- Clean rebuilt dataset is ready for baseline reruns if all validation checks pass.
- Augmentation should wait until clean baselines are rerun and unchecked-call manual review is complete.
- Reentrancy-only is ready as the first clean scope.
- Unchecked-call remains a candidate scope but needs manual review before being used as a headline result.
- Provenance is sufficient for localization in the rebuilt dataset; any missing positive source spans are reported in `reports/phase0c_localization_readiness.csv`.
