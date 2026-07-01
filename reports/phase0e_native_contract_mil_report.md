# Phase 0E Native Contract-Level MIL Training

No augmentation, architecture feature additions, or test-threshold tuning were used. Thresholds are selected on validation only. This run used 5 epochs per seed to keep the native MIL ablation tractable; treat the result as a clean objective/aggregation baseline, not a fully optimized training-budget comparison against Phase 0D.

## Split Counts
| Run | Split | Contracts | Positive Contracts | Negative Contracts | Positive Interactions |
|---|---|---:|---:|---:|---:|
| all_scope | train | 1339 | 140 | 1199 | 191 |
| all_scope | val | 280 | 30 | 250 | 51 |
| all_scope | test | 212 | 30 | 182 | 40 |
| reentrancy_only | train | 1274 | 75 | 1199 | 100 |
| reentrancy_only | val | 264 | 14 | 250 | 26 |
| reentrancy_only | test | 198 | 16 | 182 | 20 |

## Contract Metrics
Validation max-F1 threshold, mean +/- std over seeds.

| Run | Model | Pooling | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | Current wrapped interaction HyperVul | wrapped_max | 24.88 +/- 1.87 | 62.00 +/- 10.46 | 35.40 +/- 3.46 | 47.58 +/- 6.14 | 31.41 +/- 1.73 | 72.07 +/- 0.88 |
| all_scope | HyperVul native MIL | mil_attention | 25.03 +/- 1.43 | 48.00 +/- 8.06 | 32.61 +/- 2.36 | 40.24 +/- 4.92 | 27.42 +/- 2.15 | 70.67 +/- 0.69 |
| all_scope | HyperVul native MIL | mil_max | 24.02 +/- 2.09 | 62.00 +/- 4.52 | 34.57 +/- 2.52 | 47.02 +/- 3.06 | 33.43 +/- 2.76 | 72.82 +/- 1.03 |
| all_scope | HyperVul native MIL | mil_topk | 24.57 +/- 2.06 | 60.00 +/- 5.16 | 34.66 +/- 1.26 | 46.27 +/- 1.66 | 28.22 +/- 2.60 | 70.73 +/- 0.92 |
| reentrancy_only | HyperVul native MIL | mil_attention | 36.00 +/- 8.32 | 31.25 +/- 3.95 | 32.64 +/- 2.94 | 31.66 +/- 3.11 | 26.12 +/- 5.12 | 70.76 +/- 0.78 |
| reentrancy_only | HyperVul native MIL | mil_max | 16.03 +/- 2.83 | 42.50 +/- 4.68 | 23.06 +/- 3.14 | 31.58 +/- 3.24 | 33.44 +/- 2.72 | 70.16 +/- 0.56 |
| reentrancy_only | HyperVul native MIL | mil_topk | 13.33 +/- 26.67 | 5.00 +/- 10.00 | 7.27 +/- 14.55 | 5.71 +/- 11.43 | 30.24 +/- 2.91 | 70.33 +/- 0.37 |

## Localization Metrics
| Run | Model | Pooling | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| all_scope | Current wrapped interaction HyperVul | wrapped_max | 49.33 +/- 4.90 | 79.33 +/- 2.49 | 94.00 +/- 1.33 | 67.38 +/- 2.25 | 38.11 +/- 4.40 | 78.44 +/- 1.81 | 92.44 +/- 1.09 |
| all_scope | HyperVul native MIL | mil_attention | 49.33 +/- 2.49 | 78.00 +/- 1.63 | 91.33 +/- 1.63 | 67.17 +/- 1.15 | 38.33 +/- 1.86 | 72.67 +/- 1.51 | 88.56 +/- 1.63 |
| all_scope | HyperVul native MIL | mil_max | 46.00 +/- 4.90 | 81.33 +/- 1.63 | 90.67 +/- 1.33 | 65.73 +/- 2.83 | 36.11 +/- 4.35 | 76.44 +/- 2.13 | 87.89 +/- 1.33 |
| all_scope | HyperVul native MIL | mil_topk | 46.00 +/- 2.49 | 78.67 +/- 2.67 | 90.00 +/- 0.00 | 65.50 +/- 1.87 | 34.89 +/- 2.00 | 74.89 +/- 2.26 | 87.56 +/- 0.67 |
| reentrancy_only | HyperVul native MIL | mil_attention | 52.50 +/- 3.06 | 85.00 +/- 3.06 | 93.75 +/- 0.00 | 71.15 +/- 1.82 | 45.42 +/- 2.43 | 80.21 +/- 3.78 | 91.67 +/- 0.00 |
| reentrancy_only | HyperVul native MIL | mil_max | 51.25 +/- 6.12 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 71.56 +/- 3.06 | 45.62 +/- 5.45 | 82.29 +/- 2.55 | 91.67 +/- 0.00 |
| reentrancy_only | HyperVul native MIL | mil_topk | 50.00 +/- 0.00 | 86.25 +/- 2.50 | 93.75 +/- 0.00 | 70.62 +/- 0.62 | 43.75 +/- 0.00 | 81.46 +/- 3.19 | 91.67 +/- 0.00 |

## Error Analysis
Detailed false-positive contracts, false-negative contracts, and positive contracts where the true interaction is not in Top-3 are in `reports/phase0e_error_analysis.csv`.

Main observed failure modes:

- All-scope `mil_max`: 296 false-positive contract rows, 57 false-negative contract rows, and 28 positive-contract localization misses across seeds.
- All-scope `mil_topk`: 281 false-positive contract rows, 60 false-negative contract rows, and 32 localization misses across seeds.
- All-scope `mil_attention`: fewer false positives at 217 rows, but more false negatives at 78 rows and 33 localization misses.
- Reentrancy-only `mil_attention` is the best F1 operating point, but the test set has only 16 positive contracts; variance and threshold instability remain serious.

## Final Recommendation
- Native MIL does not beat the wrapped HyperVul baseline on all-scope contract F1 in this 5-epoch run: wrapped F1 is 35.40 +/- 3.46, best native F1 is `mil_topk` at 34.66 +/- 1.26.
- Native MIL does improve some ranking/localization signals: all-scope `mil_max` has higher contract PR-AUC than wrapped HyperVul, 33.43 +/- 2.76 vs 31.41 +/- 1.73, and higher Top-3 localization, 81.33 +/- 1.63 vs 79.33 +/- 2.49.
- Best all-scope pooling depends on the target: `mil_topk` is best by contract F1, while `mil_max` is best by PR-AUC and Top-3 localization.
- Best reentrancy-only contract F1 is `mil_attention` at 32.64 +/- 2.94, while best reentrancy PR-AUC/localization comes from `mil_max`. Reentrancy-only should remain the first focused experiment, but the 16-positive-contract test set requires a variance warning.
- Phase 1 augmentation should wait. The next priority should be hard-negative mining and safety/global-context features before synthetic augmentation, because the largest all-scope error bucket is false-positive contracts and false negatives still point to missing safety/context cues.
