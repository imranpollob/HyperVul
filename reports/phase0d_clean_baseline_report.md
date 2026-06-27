# Phase 0D Clean Baseline Rerun

Clean split counts were confirmed before training.

## Interaction Metrics (Test, Validation Max-F1 Threshold)
| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Function-MLP | 15.53 +/- 1.74 | 32.00 +/- 5.57 | 20.73 +/- 1.86 | 26.17 +/- 3.15 | 12.75 +/- 0.97 | 80.99 +/- 0.73 |
| Function+Features MLP | 14.47 +/- 1.55 | 46.50 +/- 4.64 | 21.94 +/- 1.68 | 31.98 +/- 1.78 | 12.17 +/- 0.91 | 81.23 +/- 0.65 |
| Sequence-BiGRU | 12.39 +/- 0.83 | 29.50 +/- 9.14 | 17.07 +/- 2.79 | 22.65 +/- 5.52 | 12.94 +/- 1.53 | 80.33 +/- 0.32 |
| CallGraph-GAT | 13.82 +/- 2.56 | 39.00 +/- 6.44 | 20.06 +/- 2.42 | 27.96 +/- 2.32 | 12.59 +/- 1.66 | 78.02 +/- 1.22 |
| Pairwise-RGCN | 13.31 +/- 4.96 | 40.50 +/- 18.33 | 18.00 +/- 4.59 | 24.74 +/- 4.62 | 13.48 +/- 2.54 | 77.84 +/- 1.50 |
| Pairwise-GAT | 13.55 +/- 3.02 | 33.00 +/- 19.52 | 16.54 +/- 5.40 | 22.05 +/- 9.84 | 14.08 +/- 1.00 | 80.21 +/- 1.90 |
| Current HyperVul | 12.38 +/- 1.63 | 44.00 +/- 11.14 | 19.05 +/- 2.03 | 28.49 +/- 3.38 | 19.02 +/- 1.14 | 80.95 +/- 1.00 |

## Contract Metrics (Test, Validation Max-F1 Threshold)
| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Function-MLP | 22.54 +/- 1.10 | 54.67 +/- 8.06 | 31.83 +/- 2.15 | 42.40 +/- 4.26 | 22.89 +/- 1.09 | 70.49 +/- 1.19 |
| Function+Features MLP | 22.54 +/- 1.70 | 66.67 +/- 3.65 | 33.61 +/- 1.62 | 47.76 +/- 1.27 | 22.29 +/- 1.59 | 69.60 +/- 1.37 |
| Sequence-BiGRU | 24.92 +/- 2.91 | 44.67 +/- 11.85 | 31.13 +/- 1.73 | 37.53 +/- 5.34 | 27.34 +/- 3.33 | 68.86 +/- 0.95 |
| CallGraph-GAT | 21.59 +/- 1.43 | 60.00 +/- 8.94 | 31.59 +/- 2.09 | 43.96 +/- 4.12 | 22.75 +/- 2.04 | 67.55 +/- 1.06 |
| Pairwise-RGCN | 20.67 +/- 2.55 | 73.33 +/- 17.38 | 31.56 +/- 1.83 | 47.17 +/- 4.64 | 24.28 +/- 3.10 | 67.79 +/- 2.01 |
| Pairwise-GAT | 22.88 +/- 5.17 | 57.33 +/- 16.92 | 31.63 +/- 4.68 | 42.29 +/- 6.17 | 24.30 +/- 2.14 | 68.77 +/- 2.49 |
| Current HyperVul | 24.88 +/- 1.87 | 62.00 +/- 10.46 | 35.40 +/- 3.46 | 47.58 +/- 6.14 | 31.41 +/- 1.73 | 72.07 +/- 0.88 |

## Localization Metrics
| Model | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Function-MLP | 54.00 +/- 1.33 | 89.33 +/- 1.33 | 96.67 +/- 0.00 | 72.11 +/- 0.70 | 43.44 +/- 1.33 | 85.44 +/- 1.33 | 93.89 +/- 0.00 |
| Function+Features MLP | 50.67 +/- 2.49 | 83.33 +/- 0.00 | 96.67 +/- 0.00 | 68.61 +/- 1.08 | 40.11 +/- 2.49 | 81.11 +/- 0.00 | 93.89 +/- 0.00 |
| Sequence-BiGRU | 53.33 +/- 2.11 | 78.67 +/- 2.67 | 87.33 +/- 1.33 | 68.27 +/- 1.85 | 43.56 +/- 2.21 | 75.33 +/- 2.95 | 85.89 +/- 1.63 |
| CallGraph-GAT | 58.67 +/- 2.67 | 84.00 +/- 1.33 | 92.00 +/- 1.63 | 71.80 +/- 1.21 | 47.22 +/- 2.43 | 79.44 +/- 1.83 | 89.22 +/- 1.63 |
| Pairwise-RGCN | 53.33 +/- 5.58 | 74.67 +/- 1.63 | 82.00 +/- 1.63 | 66.75 +/- 3.27 | 40.56 +/- 5.58 | 70.78 +/- 1.94 | 80.22 +/- 1.94 |
| Pairwise-GAT | 50.00 +/- 4.71 | 71.33 +/- 4.99 | 87.33 +/- 4.90 | 65.01 +/- 3.18 | 38.89 +/- 4.63 | 69.11 +/- 6.25 | 85.22 +/- 4.99 |
| Current HyperVul | 49.33 +/- 4.90 | 79.33 +/- 2.49 | 94.00 +/- 1.33 | 67.38 +/- 2.25 | 38.11 +/- 4.40 | 78.44 +/- 1.81 | 92.44 +/- 1.09 |

## Error Analysis

HyperVul error rows are in `reports/phase0d_hypervul_errors.csv` (753 rows across seeds).

## Interpretation

- True clean-split baseline performance is materially lower than the original leaky setting should be expected to report. The best interaction-level F1 is Function+Features MLP at 21.94 +/- 1.68, while Current HyperVul reaches 19.05 +/- 2.03 but has the best interaction PR-AUC at 19.02 +/- 1.14.
- Contract-level evaluation improves the operating point for every model. For Current HyperVul, F1 increases from 19.05 +/- 2.03 interaction-level to 35.40 +/- 3.46 contract-level, and PR-AUC increases from 19.02 +/- 1.14 to 31.41 +/- 1.73.
- Current HyperVul is the strongest contract-level model by F1, PR-AUC, and ROC-AUC. It is not a clean winner across all metrics: Function+Features MLP has slightly higher contract F2, Pairwise-RGCN has higher contract recall, and CallGraph-GAT/Function-MLP have stronger Top-1 or MRR localization.
- Localization is usable on the clean rebuilt dataset. Current HyperVul reaches Top-1 49.33 +/- 4.90, Top-3 79.33 +/- 2.49, Top-5 94.00 +/- 1.33, and MRR 67.38 +/- 2.25.
- Scope-specific error fields are present in `reports/phase0d_hypervul_errors.csv`. Reentrancy remains the right first focused experiment, but a dedicated reentrancy-only rerun should be run before claiming scope-specific model performance. Unchecked low-level call remains marked for manual review.

## Final Recommendation

- Clean baseline rerun is complete on `data/contract_graphs_clean/` with validation-only threshold selection.
- Contract-level detection + top-k localization is supported and should replace strict interaction-level classification as the main evaluation framing.
- HyperVul still beats the baselines on the main contract-level ranking/classification metrics, but it does not dominate interaction-level F1 or localization Top-1/MRR.
- Phase 1 augmentation should not begin until the clean contract-level baseline and the dedicated reentrancy-only baseline are accepted as the reference results.
- Highest-priority next fix: make the training/evaluation pipeline natively contract-level, with first-class top-k localization reporting and a dedicated reentrancy-only clean rerun.
