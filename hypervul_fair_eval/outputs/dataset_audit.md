# HyperVul Fair Evaluation Dataset Audit

Generated: `2026-06-26T13:07:44`

## Readiness Checks

| Check | Status | Detail |
|---|---:|---|
| contract_graph_files_exist | pass | All train/val/test graph files exist. |
| project_disjoint_splits | pass | Project overlap count across pairwise splits: 0. |
| project_contract_disjoint_splits | pass | Project-contract overlap count across pairwise splits: 0. |
| train_has_both_classes | pass | pos=215, neg=10525, positive_rate=2.0019% |
| val_has_both_classes | pass | pos=38, neg=806, positive_rate=4.5024% |
| test_has_both_classes | pass | pos=41, neg=732, positive_rate=5.304% |
| member_embedding_coverage | pass | State/callee member embedding coverage is >=95%. |
| clean_negative_inventory | pass | Found 1803 canonical clean-negative records across 4 pools (8 candidate files including mirrors). |

## Contract Graph Split Statistics

| Split | Graphs | Interactions | Pos | Neg | Pos Rate | Edges | Sources |
|---|---:|---:|---:|---:|---:|---:|---|
| train | 1614 | 10740 | 215 | 10525 | 2.00% | 51277 | DAPP:1570, FORGE:44 |
| val | 167 | 844 | 38 | 806 | 4.50% | 4343 | DAPP:157, FORGE:10 |
| test | 138 | 773 | 41 | 732 | 5.30% | 4639 | DAPP:124, FORGE:14 |

## Split Overlaps

| Identity | train-val | train-test | val-test |
|---|---:|---:|---:|
| graph_id | 0 | 0 | 0 |
| project | 0 | 0 | 0 |
| project_contract | 0 | 0 | 0 |
| raw_contract_name | 30 | 27 | 20 |

## Interaction Feature Coverage

| Split | State Vars | External Calls | Security Vector | Function Source |
|---|---:|---:|---:|---:|
| train | 100.00% | 100.00% | 100.00% | 100.00% |
| val | 100.00% | 100.00% | 100.00% | 100.00% |
| test | 100.00% | 100.00% | 100.00% | 100.00% |

## Member Embedding Coverage

| Split | State Texts | State Coverage | Callee Texts | Callee Coverage |
|---|---:|---:|---:|---:|
| train | 29601 | 100.00% | 24639 | 100.00% |
| val | 2137 | 100.00% | 2218 | 100.00% |
| test | 2066 | 100.00% | 1989 | 100.00% |

## Clean-Negative Inventory

Canonical clean-negative pools: **4** files, **1803** records. The inventory may include mirrored copies under both `experiments/latest1` and `experiments/results`.

| File | Records | Pos | Neg | All Negative |
|---|---:|---:|---:|---:|
| `experiments/latest1/eval_clean_negatives_oz_features.json` | 600 | 0 | 600 | True |
| `experiments/latest1/eval_clean_negatives_aave_split.json` | 291 | 0 | 291 | True |
| `experiments/latest1/eval_clean_negatives_external.json` | 633 | 0 | 633 | True |
| `experiments/latest1/eval_clean_negatives_liquity.json` | 279 | 0 | 279 | True |
| `experiments/results/eval_clean_negatives_oz_features.json` | 600 | 0 | 600 | True |
| `experiments/results/eval_clean_negatives_aave_split.json` | 291 | 0 | 291 | True |
| `experiments/results/eval_clean_negatives_external.json` | 633 | 0 | 633 | True |
| `experiments/results/eval_clean_negatives_liquity.json` | 279 | 0 | 279 | True |

## Conclusion

The existing `data/contract_graphs` train/val/test files are suitable as the canonical project-disjoint splits for the new fair-evaluation codebase. New raw splits or graph extraction are not required before model implementation, but builders should be written to produce separate function, generic graph, pairwise graph, and hyperedge views.

