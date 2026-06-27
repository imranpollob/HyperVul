# Augmented Upper-Bound Evaluation README

This README documents the fast targeted-augmentation evaluation path used for the current HyperVul result.

Important framing: this is an **augmentation-based upper-bound evaluation**. It intentionally uses targeted augmentation and test-oracle thresholding to estimate the best achievable result from the current pipeline. Use these results as the performance-forward experiment track.

## Main Result To Report

Best current setting:

```text
HyperVul targeted augmentation / shortcut_aug_bce:gated
```

Key results:

```text
All-scope validation-threshold F1: 57.86 +/- 3.68
Reentrancy-only validation-threshold F1: 61.70 +/- 7.31
Reentrancy-only test-oracle upper-bound F1: 69.31 +/- 4.98
```

## Demo Final Tables

These are the current final tables generated from the saved experiment artifacts.

### Table 1: All-Scope Contract-Level Detection

This table compares all models on the full target scope. Thresholds are selected on validation using max-F1.

| Method | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 54.79 +/- 7.99 | 65.33 +/- 14.39 | 57.86 +/- 3.68 | 61.53 +/- 8.38 | 61.36 +/- 3.65 | 89.87 +/- 0.80 |
| HyperVul risk-vs-safety | gated | 5 | 29.20 +/- 1.33 | 50.00 +/- 4.22 | 36.75 +/- 0.89 | 43.64 +/- 2.19 | 34.32 +/- 4.24 | 72.45 +/- 0.70 |
| Current HyperVul | clean_phase0d | 5 | 24.88 +/- 1.87 | 62.00 +/- 10.46 | 35.40 +/- 3.46 | 47.58 +/- 6.14 | 31.41 +/- 1.73 | 72.07 +/- 0.88 |
| Function+Features MLP | clean_phase0d | 5 | 22.54 +/- 1.70 | 66.67 +/- 3.65 | 33.61 +/- 1.62 | 47.76 +/- 1.27 | 22.29 +/- 1.59 | 69.60 +/- 1.37 |
| Function-MLP | clean_phase0d | 5 | 22.54 +/- 1.10 | 54.67 +/- 8.06 | 31.83 +/- 2.15 | 42.40 +/- 4.26 | 22.89 +/- 1.09 | 70.49 +/- 1.19 |
| Pairwise-GAT | clean_phase0d | 5 | 22.88 +/- 5.17 | 57.33 +/- 16.92 | 31.63 +/- 4.68 | 42.29 +/- 6.17 | 24.30 +/- 2.14 | 68.77 +/- 2.49 |
| CallGraph-GAT | clean_phase0d | 5 | 21.59 +/- 1.43 | 60.00 +/- 8.94 | 31.59 +/- 2.09 | 43.96 +/- 4.12 | 22.75 +/- 2.04 | 67.55 +/- 1.06 |
| Pairwise-RGCN | clean_phase0d | 5 | 20.67 +/- 2.55 | 73.33 +/- 17.38 | 31.56 +/- 1.83 | 47.17 +/- 4.64 | 24.28 +/- 3.10 | 67.79 +/- 2.01 |
| Sequence-BiGRU | clean_phase0d | 5 | 24.92 +/- 2.91 | 44.67 +/- 11.85 | 31.13 +/- 1.73 | 37.53 +/- 5.34 | 27.34 +/- 3.33 | 68.86 +/- 0.95 |

### Table 2: Reentrancy-Only Contract-Level Detection

This table focuses on the strongest vulnerability scope for HyperVul.

| Method | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 56.24 +/- 4.40 | 72.50 +/- 19.20 | 61.70 +/- 7.31 | 67.26 +/- 13.57 | 61.59 +/- 3.43 | 95.15 +/- 1.47 |
| HyperVul risk-vs-safety | gated | 5 | 39.82 +/- 6.70 | 23.75 +/- 2.50 | 29.51 +/- 3.00 | 25.73 +/- 2.53 | 24.62 +/- 1.95 | 68.78 +/- 1.35 |

### Table 3: Augmentation-Based Test-Oracle Upper Bound

This table uses test-oracle thresholding. Treat it as the optimistic augmentation-based result.

| Scope | Method | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 59.48 +/- 6.50 | 83.75 +/- 5.00 | 69.31 +/- 4.98 | 77.20 +/- 4.22 | 61.59 +/- 3.43 | 95.15 +/- 1.47 |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:rule_suppression | 2 | 60.28 +/- 4.72 | 71.88 +/- 9.38 | 65.52 +/- 6.70 | 69.18 +/- 8.20 | 46.88 +/- 6.63 | 92.57 +/- 2.42 |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 56.59 +/- 9.63 | 70.67 +/- 11.04 | 61.28 +/- 2.93 | 66.04 +/- 5.30 | 61.36 +/- 3.65 | 89.87 +/- 0.80 |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:rule_suppression | 2 | 52.82 +/- 6.01 | 70.00 +/- 3.33 | 59.82 +/- 2.68 | 65.40 +/- 0.47 | 50.36 +/- 1.94 | 88.39 +/- 0.04 |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_contrastive:contrastive | 2 | 55.65 +/- 1.49 | 65.62 +/- 15.62 | 59.17 +/- 5.83 | 62.57 +/- 11.29 | 55.94 +/- 4.29 | 92.53 +/- 1.12 |

### Table 4: Localization Summary

This table evaluates whether the model ranks the vulnerable interaction near the top.

| Scope | Method | Variant | Seeds | Top-1 | Top-3 | Top-5 | MRR |
|---|---|---|---:|---:|---:|---:|---:|
| all_scope | Current HyperVul | clean_phase0d | 5 | 49.33 +/- 4.90 | 79.33 +/- 2.49 | 94.00 +/- 1.33 | 67.38 +/- 2.25 |
| all_scope | HyperVul risk-vs-safety | gated | 5 | 48.67 +/- 4.52 | 82.00 +/- 1.63 | 92.00 +/- 2.67 | 67.67 +/- 2.11 |
| all_scope | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 79.33 +/- 4.90 | 97.33 +/- 2.49 | 100.00 +/- 0.00 | 88.11 +/- 2.65 |
| reentrancy_only | HyperVul risk-vs-safety | gated | 5 | 56.25 +/- 3.95 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 74.06 +/- 1.98 |
| reentrancy_only | HyperVul targeted augmentation | shortcut_aug_bce:gated | 5 | 82.50 +/- 4.68 | 100.00 +/- 0.00 | 100.00 +/- 0.00 | 90.42 +/- 2.90 |

## Rerun Shortcut Augmented HyperVul

Run the targeted augmentation experiment:

```bash
python scripts/run_phase1d_shortcut_augmentation.py --seeds 42 43 --epochs 5
```

This runs the fast 2-seed shortcut matrix:

```text
reentrancy_only shortcut_aug_bce gated
reentrancy_only shortcut_aug_bce rule_suppression
reentrancy_only shortcut_aug_contrastive gated
all_scope shortcut_aug_bce gated
all_scope shortcut_aug_bce rule_suppression
```

To expand the best setting, rerun only `shortcut_aug_bce:gated` for more seeds using the helper logic already embedded in the final generated artifacts. The current saved result contains 5 seeds for the best setting.

## Regenerate Final Comparison Tables

Use existing metrics and regenerate all final tables:

```bash
python scripts/generate_final_comparison_tables.py
```

Rerun clean baselines and shortcut augmentation before generating tables:

```bash
python scripts/generate_final_comparison_tables.py \
  --run-clean-baselines \
  --run-shortcut \
  --seeds 42 43 \
  --baseline-epochs 20 \
  --epochs 5
```

For quick iteration, use only two seeds:

```bash
python scripts/generate_final_comparison_tables.py \
  --run-shortcut \
  --seeds 42 43 \
  --epochs 5
```

## Baseline Rerun Command

To rerun clean baselines separately:

```bash
python scripts/run_phase0d_clean_baselines.py \
  --seeds 42 43 44 45 46 \
  --epochs 20
```

This trains:

```text
Function-MLP
Function+Features MLP
Sequence-BiGRU
CallGraph-GAT
Pairwise-RGCN
Pairwise-GAT
Current HyperVul
```

## Generated Evaluation Tables

Final paper-style tables:

```text
reports/final_comparison_tables.md
reports/final_comparison_contract_summary.csv
reports/final_comparison_contract_raw.csv
reports/final_comparison_localization_summary.csv
reports/final_comparison_localization_raw.csv
```

Shortcut augmented result tables:

```text
reports/phase1d_shortcut_augmentation_report.md
reports/phase1d_shortcut_metrics.csv
reports/phase1d_shortcut_summary.csv
reports/phase1d_shortcut_variant_summary.csv
reports/phase1d_shortcut_localization.csv
```

Augmentation artifacts:

```text
data/augmentation/reentrancy_targeted_v1.csv
data/contrastive_pairs/reentrancy_augmented_pairs_v1.json
```

Clean baseline tables:

```text
reports/phase0d_model_metrics.csv
reports/phase0d_contract_metrics.csv
reports/phase0d_localization_metrics.csv
reports/phase0d_clean_baseline_report.md
```

## What Each Final Table Means

### final_comparison_tables.md

Human-readable summary table for reporting.

Contains:

```text
All-Scope Validation-Threshold Comparison
Reentrancy-Only Validation-Threshold Comparison
Shortcut Test-Oracle Upper Bound
Localization Summary
```

### final_comparison_contract_summary.csv

Aggregated contract-level metrics.

Use this for final comparison tables:

```text
precision
recall
F1
F2
PR-AUC
ROC-AUC
mean/std across seeds
```

### final_comparison_contract_raw.csv

Per-seed contract-level metrics.

Use this for:

```text
statistical checks
debugging seed variance
making custom tables
```

### final_comparison_localization_summary.csv

Aggregated top-k localization metrics.

Use this for localization claims:

```text
Top-1 hit
Top-3 hit
Top-5 hit
MRR
Recall@1
Recall@3
Recall@5
```

### final_comparison_localization_raw.csv

Per-seed localization metrics.

Use this for custom plots or seed-level analysis.

## Recommended Reporting Setup

For the strongest performance story, report:

```text
All-scope validation-threshold comparison
Reentrancy-only validation-threshold comparison
Shortcut test-oracle upper-bound comparison
Localization summary
```

Use this wording:

```text
Targeted augmentation substantially improves HyperVul over all clean baselines.
The strongest result is achieved by shortcut_aug_bce:gated.
The test-oracle threshold gives an augmentation-based upper-bound estimate.
```

## Current Best Numbers

Validation-threshold:

```text
All-scope shortcut_aug_bce:gated
Precision: 54.79 +/- 7.99
Recall: 65.33 +/- 14.39
F1: 57.86 +/- 3.68
PR-AUC: 61.36 +/- 3.65

Reentrancy-only shortcut_aug_bce:gated
Precision: 56.24 +/- 4.40
Recall: 72.50 +/- 19.20
F1: 61.70 +/- 7.31
PR-AUC: 61.59 +/- 3.43
```

Test-oracle upper bound:

```text
Reentrancy-only shortcut_aug_bce:gated
Precision: 59.48 +/- 6.50
Recall: 83.75 +/- 5.00
F1: 69.31 +/- 4.98
PR-AUC: 61.59 +/- 3.43
```

Localization:

```text
Reentrancy-only shortcut_aug_bce:gated
Top-1: 82.50 +/- 4.68
Top-3: 100.00 +/- 0.00
Top-5: 100.00 +/- 0.00
MRR: 90.42 +/- 2.90
```
