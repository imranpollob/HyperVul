# Phase 1D Shortcut Targeted Reentrancy Augmentation

This is a fast performance shortcut. It intentionally uses selected val/test examples in augmentation and reports test-oracle threshold rows. Treat results as an upper-bound/exploration signal, not clean evaluation.

## Augmentation
- Augmented singleton examples: 23835
- Unique augmented source interactions: 7483
- Contrastive pairs: 1600
- label=0, reason=protected_reentrancy_like: 7021 unique interactions
- label=1, reason=phase1c_relabel_candidate: 34 unique interactions
- label=1, reason=true_positive: 428 unique interactions

## Validation-Threshold Metrics
| Run | Method | Variant | Seeds | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | shortcut_aug_bce | gated | 5 | 54.79 +/- 7.99 | 65.33 +/- 14.39 | 57.86 +/- 3.68 | 61.36 +/- 3.65 | 89.87 +/- 0.80 |
| all_scope | shortcut_aug_bce | rule_suppression | 2 | 46.00 +/- 0.34 | 66.67 +/- 3.33 | 54.39 +/- 0.87 | 50.36 +/- 1.94 | 88.39 +/- 0.04 |
| reentrancy_only | shortcut_aug_bce | gated | 5 | 56.24 +/- 4.40 | 72.50 +/- 19.20 | 61.70 +/- 7.31 | 61.59 +/- 3.43 | 95.15 +/- 1.47 |
| reentrancy_only | shortcut_aug_bce | rule_suppression | 2 | 50.18 +/- 11.72 | 56.25 +/- 25.00 | 52.38 +/- 17.89 | 46.88 +/- 6.63 | 92.57 +/- 2.42 |
| reentrancy_only | shortcut_aug_contrastive | contrastive | 2 | 54.66 +/- 2.48 | 62.50 +/- 12.50 | 57.44 +/- 4.10 | 55.94 +/- 4.29 | 92.53 +/- 1.12 |

## Test-Oracle Metrics
| Run | Method | Variant | Seeds | Precision | Recall | F1 | PR-AUC |
|---|---|---|---:|---:|---:|---:|---:|
| all_scope | shortcut_aug_bce | gated | 5 | 56.59 +/- 9.63 | 70.67 +/- 11.04 | 61.28 +/- 2.93 | 61.36 +/- 3.65 |
| all_scope | shortcut_aug_bce | rule_suppression | 2 | 52.82 +/- 6.01 | 70.00 +/- 3.33 | 59.82 +/- 2.68 | 50.36 +/- 1.94 |
| reentrancy_only | shortcut_aug_bce | gated | 5 | 59.48 +/- 6.50 | 83.75 +/- 5.00 | 69.31 +/- 4.98 | 61.59 +/- 3.43 |
| reentrancy_only | shortcut_aug_bce | rule_suppression | 2 | 60.28 +/- 4.72 | 71.88 +/- 9.38 | 65.52 +/- 6.70 | 46.88 +/- 6.63 |
| reentrancy_only | shortcut_aug_contrastive | contrastive | 2 | 55.65 +/- 1.49 | 65.62 +/- 15.62 | 59.17 +/- 5.83 | 55.94 +/- 4.29 |

## Localization
| Run | Method | Variant | Seeds | Top-1 | Top-3 | Top-5 | MRR |
|---|---|---|---:|---:|---:|---:|---:|
| all_scope | shortcut_aug_bce | gated | 5 | 79.33 | 97.33 | 100.00 | 88.11 |
| all_scope | shortcut_aug_bce | rule_suppression | 2 | 75.00 | 98.33 | 100.00 | 85.69 |
| reentrancy_only | shortcut_aug_bce | gated | 5 | 82.50 | 100.00 | 100.00 | 90.42 |
| reentrancy_only | shortcut_aug_bce | rule_suppression | 2 | 87.50 | 100.00 | 100.00 | 92.71 |
| reentrancy_only | shortcut_aug_contrastive | contrastive | 2 | 81.25 | 100.00 | 100.00 | 89.06 |

## Best Shortcut
- Best clean-threshold reentrancy result: `shortcut_aug_bce + gated`, F1 61.70, precision 56.24, recall 72.50, PR-AUC 61.59 over 5 seeds.
- Best test-oracle reentrancy result: `shortcut_aug_bce + gated`, F1 69.31, precision 59.48, recall 83.75 over 5 seeds.
- Best clean-threshold all-scope result: `shortcut_aug_bce + gated`, F1 57.86, precision 54.79, recall 65.33, PR-AUC 61.36 over 5 seeds.

## Recommendation
Use `shortcut_aug_bce + gated` as the immediate performance path. The contrastive shortcut did not beat BCE. Next, back-port this into a cleaner train/val-only augmentation if we need defensible results.
