# Final Baseline Comparison Tables

These tables combine clean baseline results with the shortcut targeted-augmentation result. Rows marked `shortcut_leaky_targeted_augmentation` are performance-oriented and not clean final evaluation.

## All-Scope Validation-Threshold Comparison
| Method | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Notes |
|---|---|---|---|---|---|---|---|---|---|
| HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 54.79 +/- 7.99 | 65.33 +/- 14.39 | 57.86 +/- 3.68 | 61.53 +/- 8.38 | 61.36 +/- 3.65 | 89.87 +/- 0.80 | shortcut_leaky_targeted_augmentation |
| HyperVul risk-vs-safety | gated | 5 | 29.20 +/- 1.33 | 50.00 +/- 4.22 | 36.75 +/- 0.89 | 43.64 +/- 2.19 | 34.32 +/- 4.24 | 72.45 +/- 0.70 | phase1b_clean_no_augmentation |
| Current HyperVul | clean_phase0d | 5 | 24.88 +/- 1.87 | 62.00 +/- 10.46 | 35.40 +/- 3.46 | 47.58 +/- 6.14 | 31.41 +/- 1.73 | 72.07 +/- 0.88 | clean_split_baseline |
| Function+Features MLP | clean_phase0d | 5 | 22.54 +/- 1.70 | 66.67 +/- 3.65 | 33.61 +/- 1.62 | 47.76 +/- 1.27 | 22.29 +/- 1.59 | 69.60 +/- 1.37 | clean_split_baseline |
| Function-MLP | clean_phase0d | 5 | 22.54 +/- 1.10 | 54.67 +/- 8.06 | 31.83 +/- 2.15 | 42.40 +/- 4.26 | 22.89 +/- 1.09 | 70.49 +/- 1.19 | clean_split_baseline |
| Pairwise-GAT | clean_phase0d | 5 | 22.88 +/- 5.17 | 57.33 +/- 16.92 | 31.63 +/- 4.68 | 42.29 +/- 6.17 | 24.30 +/- 2.14 | 68.77 +/- 2.49 | clean_split_baseline |
| CallGraph-GAT | clean_phase0d | 5 | 21.59 +/- 1.43 | 60.00 +/- 8.94 | 31.59 +/- 2.09 | 43.96 +/- 4.12 | 22.75 +/- 2.04 | 67.55 +/- 1.06 | clean_split_baseline |
| Pairwise-RGCN | clean_phase0d | 5 | 20.67 +/- 2.55 | 73.33 +/- 17.38 | 31.56 +/- 1.83 | 47.17 +/- 4.64 | 24.28 +/- 3.10 | 67.79 +/- 2.01 | clean_split_baseline |
| Sequence-BiGRU | clean_phase0d | 5 | 24.92 +/- 2.91 | 44.67 +/- 11.85 | 31.13 +/- 1.73 | 37.53 +/- 5.34 | 27.34 +/- 3.33 | 68.86 +/- 0.95 | clean_split_baseline |

## Reentrancy-Only Validation-Threshold Comparison
| Method | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Notes |
|---|---|---|---|---|---|---|---|---|---|
| HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 56.24 +/- 4.40 | 72.50 +/- 19.20 | 61.70 +/- 7.31 | 67.26 +/- 13.57 | 61.59 +/- 3.43 | 95.15 +/- 1.47 | shortcut_leaky_targeted_augmentation |
| HyperVul risk-vs-safety | gated | 5 | 39.82 +/- 6.70 | 23.75 +/- 2.50 | 29.51 +/- 3.00 | 25.73 +/- 2.53 | 24.62 +/- 1.95 | 68.78 +/- 1.35 | phase1b_clean_no_augmentation |

## Shortcut Test-Oracle Upper Bound
| Scope | Method | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 59.48 +/- 6.50 | 83.75 +/- 5.00 | 69.31 +/- 4.98 | 77.20 +/- 4.22 | 61.59 +/- 3.43 | 95.15 +/- 1.47 | shortcut_leaky_targeted_augmentation |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:rule_suppression | 2 | 60.28 +/- 4.72 | 71.88 +/- 9.38 | 65.52 +/- 6.70 | 69.18 +/- 8.20 | 46.88 +/- 6.63 | 92.57 +/- 2.42 | shortcut_leaky_targeted_augmentation |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 56.59 +/- 9.63 | 70.67 +/- 11.04 | 61.28 +/- 2.93 | 66.04 +/- 5.30 | 61.36 +/- 3.65 | 89.87 +/- 0.80 | shortcut_leaky_targeted_augmentation |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:rule_suppression | 2 | 52.82 +/- 6.01 | 70.00 +/- 3.33 | 59.82 +/- 2.68 | 65.40 +/- 0.47 | 50.36 +/- 1.94 | 88.39 +/- 0.04 | shortcut_leaky_targeted_augmentation |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_contrastive:contrastive | 2 | 55.65 +/- 1.49 | 65.62 +/- 15.62 | 59.17 +/- 5.83 | 62.57 +/- 11.29 | 55.94 +/- 4.29 | 92.53 +/- 1.12 | shortcut_leaky_targeted_augmentation |

## Localization Summary
| Scope | Method | Variant | Seeds | Top-1 | Top-3 | Top-5 | MRR | Notes |
|---|---|---|---:|---:|---:|---:|---:|---|
| all_scope | CallGraph-GAT | clean_phase0d | 5 | 58.67 +/- 2.67 | 84.00 +/- 1.33 | 92.00 +/- 1.63 | 71.80 +/- 1.21 | clean_split_baseline |
| all_scope | Current HyperVul | clean_phase0d | 5 | 49.33 +/- 4.90 | 79.33 +/- 2.49 | 94.00 +/- 1.33 | 67.38 +/- 2.25 | clean_split_baseline |
| all_scope | Function+Features MLP | clean_phase0d | 5 | 50.67 +/- 2.49 | 83.33 +/- 0.00 | 96.67 +/- 0.00 | 68.61 +/- 1.08 | clean_split_baseline |
| all_scope | Function-MLP | clean_phase0d | 5 | 54.00 +/- 1.33 | 89.33 +/- 1.33 | 96.67 +/- 0.00 | 72.11 +/- 0.70 | clean_split_baseline |
| all_scope | HyperVul risk-vs-safety | concat | 5 | 53.33 +/- 0.00 | 84.67 +/- 4.52 | 93.33 +/- 2.98 | 70.57 +/- 1.22 | phase1b_clean_no_augmentation |
| all_scope | HyperVul risk-vs-safety | gated | 5 | 48.67 +/- 4.52 | 82.00 +/- 1.63 | 92.00 +/- 2.67 | 67.67 +/- 2.11 | phase1b_clean_no_augmentation |
| all_scope | HyperVul risk-vs-safety | rule_suppression | 5 | 42.00 +/- 5.81 | 85.33 +/- 3.40 | 96.67 +/- 0.00 | 63.38 +/- 3.79 | phase1b_clean_no_augmentation |
| all_scope | HyperVul risk-vs-safety | subtractive | 5 | 49.33 +/- 2.49 | 78.00 +/- 1.63 | 90.67 +/- 1.33 | 67.43 +/- 1.26 | phase1b_clean_no_augmentation |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 79.33 +/- 4.90 | 97.33 +/- 2.49 | 100.00 +/- 0.00 | 88.11 +/- 2.65 | shortcut_leaky_targeted_augmentation |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:rule_suppression | 2 | 75.00 +/- 1.67 | 98.33 +/- 1.67 | 100.00 +/- 0.00 | 85.69 +/- 0.97 | shortcut_leaky_targeted_augmentation |
| all_scope | Pairwise-GAT | clean_phase0d | 5 | 50.00 +/- 4.71 | 71.33 +/- 4.99 | 87.33 +/- 4.90 | 65.01 +/- 3.18 | clean_split_baseline |
| all_scope | Pairwise-RGCN | clean_phase0d | 5 | 53.33 +/- 5.58 | 74.67 +/- 1.63 | 82.00 +/- 1.63 | 66.75 +/- 3.27 | clean_split_baseline |
| all_scope | Sequence-BiGRU | clean_phase0d | 5 | 53.33 +/- 2.11 | 78.67 +/- 2.67 | 87.33 +/- 1.33 | 68.27 +/- 1.85 | clean_split_baseline |
| reentrancy_only | HyperVul risk-vs-safety | concat | 5 | 61.25 +/- 4.68 | 87.50 +/- 0.00 | 92.50 +/- 2.50 | 76.43 +/- 2.49 | phase1b_clean_no_augmentation |
| reentrancy_only | HyperVul risk-vs-safety | gated | 5 | 56.25 +/- 3.95 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 74.06 +/- 1.98 | phase1b_clean_no_augmentation |
| reentrancy_only | HyperVul risk-vs-safety | rule_suppression | 5 | 35.00 +/- 5.00 | 87.50 +/- 3.95 | 93.75 +/- 0.00 | 61.99 +/- 2.40 | phase1b_clean_no_augmentation |
| reentrancy_only | HyperVul risk-vs-safety | subtractive | 5 | 52.50 +/- 3.06 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 71.77 +/- 1.91 | phase1b_clean_no_augmentation |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 82.50 +/- 4.68 | 100.00 +/- 0.00 | 100.00 +/- 0.00 | 90.42 +/- 2.90 | shortcut_leaky_targeted_augmentation |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:rule_suppression | 2 | 87.50 +/- 6.25 | 100.00 +/- 0.00 | 100.00 +/- 0.00 | 92.71 +/- 3.12 | shortcut_leaky_targeted_augmentation |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_contrastive:contrastive | 2 | 81.25 +/- 6.25 | 100.00 +/- 0.00 | 100.00 +/- 0.00 | 89.06 +/- 2.60 | shortcut_leaky_targeted_augmentation |

## Best Result
- Best validation-threshold F1: HyperVul targeted augmentation / shortcut_aug_bce:gated on reentrancy_only: 61.70 +/- 7.31.
- Best test-oracle F1: HyperVul targeted augmentation / shortcut_aug_bce:gated on reentrancy_only: 69.31 +/- 4.98.
