# HyperVul Fair Evaluation Final Report

This report consolidates the current fair-evaluation rewrite outputs.

Static analyzer baselines are deferred, not abandoned, because they require separate compiler/toolchain handling.

## Dataset

| Split | Graphs | Interactions | Pos | Neg | Pos Rate | Edges |
|---|---:|---:|---:|---:|---:|---:|
| train | 1614 | 10740 | 215 | 10525 | 2.00% | 51277 |
| val | 167 | 844 | 38 | 806 | 4.50% | 4343 |
| test | 138 | 773 | 41 | 732 | 5.30% | 4639 |

Split checks: project-disjoint and project-contract-disjoint checks passed in the dataset audit.

## RQ1: Generic Neural Baselines

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| function-mlp | 17.31 +/- 2.35 | 64.39 +/- 9.83 | 26.95 +/- 2.27 | 40.92 +/- 1.47 | 31.38 +/- 1.75 | 83.08 +/- 0.78 |
| function-features-mlp | 17.31 +/- 1.16 | 67.80 +/- 3.90 | 27.53 +/- 1.33 | 42.70 +/- 1.38 | 33.43 +/- 0.88 | 83.88 +/- 0.51 |
| sequence | 15.00 +/- 2.65 | 69.76 +/- 13.32 | 24.26 +/- 2.69 | 39.13 +/- 1.48 | 22.73 +/- 2.10 | 83.06 +/- 1.13 |
| callgraph-gcn | 17.17 +/- 4.09 | 63.41 +/- 13.45 | 26.45 +/- 4.57 | 39.88 +/- 4.58 | 27.83 +/- 2.20 | 83.23 +/- 1.61 |
| pairwise-gcn | 13.57 +/- 1.35 | 51.71 +/- 18.21 | 21.18 +/- 2.65 | 32.33 +/- 6.34 | 19.50 +/- 1.99 | 80.49 +/- 1.95 |
| pairwise-gat | 14.46 +/- 2.15 | 72.68 +/- 4.20 | 24.03 +/- 2.90 | 39.99 +/- 3.15 | 29.19 +/- 1.94 | 83.16 +/- 2.31 |

## RQ2: Controlled Representation Ablation

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| set-pool | 13.42 +/- 1.21 | 65.85 +/- 5.34 | 22.25 +/- 1.65 | 36.83 +/- 2.06 | 22.95 +/- 1.26 | 79.79 +/- 0.60 |
| pairwise-gcn | 13.37 +/- 1.60 | 54.15 +/- 9.18 | 21.24 +/- 1.72 | 33.11 +/- 2.07 | 21.40 +/- 1.80 | 78.93 +/- 1.65 |
| pairwise-gat | 15.16 +/- 1.90 | 59.51 +/- 5.48 | 24.01 +/- 2.13 | 37.19 +/- 1.69 | 27.99 +/- 4.43 | 80.16 +/- 1.59 |
| hyperedge-nn | 17.65 +/- 1.48 | 59.02 +/- 6.05 | 27.08 +/- 1.76 | 39.97 +/- 2.37 | 26.45 +/- 2.96 | 81.08 +/- 0.85 |

## RQ2 Seed-Paired Significance

Reference model: `hyperedge-nn`. Test: exact sign-flip permutation over paired seed-level metric deltas.

| Comparison | Metric | Mean Delta | p-value |
|---|---|---:|---:|
| hyperedge-nn vs set-pool | f1 | 4.82 | 0.0625 |
| hyperedge-nn vs set-pool | f2 | 3.14 | 0.1875 |
| hyperedge-nn vs set-pool | pr_auc | 3.50 | 0.0625 |
| hyperedge-nn vs set-pool | roc_auc | 1.29 | 0.1875 |
| hyperedge-nn vs pairwise-gcn | f1 | 5.84 | 0.0625 |
| hyperedge-nn vs pairwise-gcn | f2 | 6.86 | 0.0625 |
| hyperedge-nn vs pairwise-gcn | pr_auc | 5.04 | 0.1250 |
| hyperedge-nn vs pairwise-gcn | roc_auc | 2.15 | 0.1250 |
| hyperedge-nn vs pairwise-gat | f1 | 3.06 | 0.1250 |
| hyperedge-nn vs pairwise-gat | f2 | 2.79 | 0.1250 |
| hyperedge-nn vs pairwise-gat | pr_auc | -1.55 | 0.6875 |
| hyperedge-nn vs pairwise-gat | roc_auc | 0.92 | 0.4375 |

## RQ3: HyperVul Component Ablation

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| emb-only | 18.28 +/- 1.08 | 61.46 +/- 6.43 | 28.09 +/- 1.32 | 41.56 +/- 2.32 | 22.99 +/- 1.17 | 83.46 +/- 0.34 |
| security | 17.35 +/- 1.93 | 70.24 +/- 8.07 | 27.62 +/- 2.17 | 43.12 +/- 1.74 | 20.42 +/- 1.53 | 82.95 +/- 0.82 |
| full | 17.35 +/- 1.93 | 70.24 +/- 8.07 | 27.62 +/- 2.17 | 43.12 +/- 1.74 | 20.42 +/- 1.53 | 82.95 +/- 0.82 |
| no-localize | 15.77 +/- 1.64 | 58.54 +/- 17.25 | 24.37 +/- 2.24 | 36.82 +/- 5.16 | 20.01 +/- 2.13 | 81.84 +/- 1.10 |
| no-contrastive | 18.68 +/- 3.51 | 54.15 +/- 17.88 | 26.70 +/- 2.66 | 37.39 +/- 5.88 | 21.58 +/- 3.16 | 82.93 +/- 1.17 |

## Notes

- `security` and `full` in RQ3 both use the canonical 8-d security context available in `data/contract_graphs`.
- Slither/Mythril will be added later through a dedicated static-analysis harness pass.
- All neural tables use five seeds: `42 43 44 45 46`.
