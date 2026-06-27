# Augmented Reentrancy Baseline Comparison

All rows are trained on `data/reentrancy_positive_augmented_v1`, which contains positive-only synthetic reentrancy clones in the train split. Val/test are not augmented.

## Dataset Counts
| Split | Contracts | Pos Contracts | Neg Contracts | Pos Int | Neg Int | Ignored | Neg:Pos Int |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 3989 | 2798 | 1191 | 2823 | 8467 | 85 | 3.00 |
| val | 264 | 23 | 241 | 35 | 1389 | 92 | 39.69 |
| test | 198 | 16 | 182 | 20 | 1051 | 0 | 52.55 |

## Validation Max-F1 Threshold
| Model | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Pairwise-GAT | augmented_data | 2 | 14.04 +/- 0.46 | 65.62 +/- 3.12 | 23.10 +/- 0.42 | 37.76 +/- 0.17 | 20.79 +/- 0.62 | 71.57 +/- 1.03 |
| Function+Features MLP | augmented_data | 2 | 12.92 +/- 0.02 | 71.88 +/- 3.12 | 21.90 +/- 0.12 | 37.56 +/- 0.65 | 24.70 +/- 1.82 | 71.57 +/- 0.03 |
| CallGraph-GAT | augmented_data | 2 | 13.51 +/- 1.01 | 56.25 +/- 0.00 | 21.77 +/- 1.31 | 34.40 +/- 1.31 | 22.64 +/- 5.51 | 70.42 +/- 2.46 |
| Current HyperVul | augmented_data | 2 | 12.31 +/- 1.20 | 62.50 +/- 0.00 | 20.55 +/- 1.68 | 34.35 +/- 1.88 | 13.23 +/- 0.01 | 65.41 +/- 0.37 |
| Function-MLP | augmented_data | 2 | 12.81 +/- 0.31 | 50.00 +/- 0.00 | 20.39 +/- 0.39 | 31.63 +/- 0.38 | 21.75 +/- 2.27 | 70.90 +/- 0.68 |
| Pairwise-RGCN | augmented_data | 2 | 10.97 +/- 1.53 | 62.50 +/- 0.00 | 18.61 +/- 2.22 | 32.07 +/- 2.66 | 13.85 +/- 0.24 | 64.80 +/- 1.44 |
| Sequence-BiGRU | augmented_data | 2 | 10.74 +/- 0.37 | 68.75 +/- 0.00 | 18.58 +/- 0.55 | 33.05 +/- 0.69 | 25.36 +/- 1.78 | 66.84 +/- 0.70 |
| HyperVul-RiskSafety | gated | 2 | 7.87 +/- 2.31 | 40.62 +/- 28.12 | 12.72 +/- 5.02 | 20.99 +/- 10.99 | 14.49 +/- 1.23 | 61.45 +/- 5.10 |

## Validation Target Recall 90
| Model | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Pairwise-GAT | augmented_data | 2 | 12.15 +/- 0.23 | 81.25 +/- 0.00 | 21.14 +/- 0.34 | 38.02 +/- 0.44 | 20.79 +/- 0.62 | 71.57 +/- 1.03 |
| Function-MLP | augmented_data | 2 | 11.78 +/- 0.37 | 81.25 +/- 0.00 | 20.57 +/- 0.57 | 37.26 +/- 0.75 | 21.75 +/- 2.27 | 70.90 +/- 0.68 |
| Function+Features MLP | augmented_data | 2 | 11.55 +/- 0.35 | 90.62 +/- 3.12 | 20.49 +/- 0.63 | 38.26 +/- 1.22 | 24.70 +/- 1.82 | 71.57 +/- 0.03 |
| CallGraph-GAT | augmented_data | 2 | 11.05 +/- 1.23 | 93.75 +/- 6.25 | 19.71 +/- 1.83 | 37.28 +/- 2.04 | 22.64 +/- 5.51 | 70.42 +/- 2.46 |
| Pairwise-RGCN | augmented_data | 2 | 10.30 +/- 0.10 | 90.62 +/- 9.38 | 18.47 +/- 0.03 | 35.30 +/- 0.90 | 13.85 +/- 0.24 | 64.80 +/- 1.44 |
| Sequence-BiGRU | augmented_data | 2 | 10.32 +/- 0.79 | 71.88 +/- 3.12 | 18.02 +/- 1.11 | 32.66 +/- 1.08 | 25.36 +/- 1.78 | 66.84 +/- 0.70 |
| Current HyperVul | augmented_data | 2 | 9.48 +/- 0.16 | 96.88 +/- 3.12 | 17.27 +/- 0.32 | 34.06 +/- 0.72 | 13.23 +/- 0.01 | 65.41 +/- 0.37 |
| HyperVul-RiskSafety | gated | 2 | 8.78 +/- 0.70 | 84.38 +/- 15.62 | 15.81 +/- 0.86 | 30.54 +/- 0.01 | 14.49 +/- 1.23 | 61.45 +/- 5.10 |

## Validation Target Precision 80
| Model | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CallGraph-GAT | augmented_data | 2 | 11.53 +/- 0.75 | 78.12 +/- 9.38 | 20.09 +/- 1.45 | 36.23 +/- 3.10 | 22.64 +/- 5.51 | 70.42 +/- 2.46 |
| Sequence-BiGRU | augmented_data | 2 | 10.74 +/- 0.37 | 68.75 +/- 0.00 | 18.58 +/- 0.55 | 33.05 +/- 0.69 | 25.36 +/- 1.78 | 66.84 +/- 0.70 |
| Pairwise-GAT | augmented_data | 2 | 18.46 +/- 6.54 | 43.75 +/- 37.50 | 15.40 +/- 5.40 | 22.46 +/- 15.11 | 20.79 +/- 0.62 | 71.57 +/- 1.03 |
| Pairwise-RGCN | augmented_data | 2 | 5.10 +/- 5.10 | 50.00 +/- 50.00 | 9.25 +/- 9.25 | 18.10 +/- 18.10 | 13.85 +/- 0.24 | 64.80 +/- 1.44 |
| Current HyperVul | augmented_data | 2 | 10.00 +/- 10.00 | 3.12 +/- 3.12 | 4.76 +/- 4.76 | 3.62 +/- 3.62 | 13.23 +/- 0.01 | 65.41 +/- 0.37 |
| Function+Features MLP | augmented_data | 2 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 24.70 +/- 1.82 | 71.57 +/- 0.03 |
| Function-MLP | augmented_data | 2 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 21.75 +/- 2.27 | 70.90 +/- 0.68 |
| HyperVul-RiskSafety | gated | 2 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 0.00 +/- 0.00 | 14.49 +/- 1.23 | 61.45 +/- 5.10 |

## Test-Oracle Upper Bound
| Model | Variant | Seeds | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Function+Features MLP | augmented_data | 2 | 41.43 +/- 1.43 | 37.50 +/- 0.00 | 39.35 +/- 0.65 | 38.22 +/- 0.24 | 24.70 +/- 1.82 | 71.57 +/- 0.03 |
| Function-MLP | augmented_data | 2 | 31.82 +/- 0.00 | 43.75 +/- 0.00 | 36.84 +/- 0.00 | 40.70 +/- 0.00 | 21.75 +/- 2.27 | 70.90 +/- 0.68 |
| Sequence-BiGRU | augmented_data | 2 | 36.12 +/- 10.03 | 37.50 +/- 0.00 | 36.07 +/- 5.31 | 36.72 +/- 2.24 | 25.36 +/- 1.78 | 66.84 +/- 0.70 |
| Pairwise-GAT | augmented_data | 2 | 33.44 +/- 1.86 | 37.50 +/- 0.00 | 35.32 +/- 1.04 | 36.59 +/- 0.45 | 20.79 +/- 0.62 | 71.57 +/- 1.03 |
| CallGraph-GAT | augmented_data | 2 | 33.84 +/- 11.62 | 34.38 +/- 3.12 | 32.47 +/- 4.57 | 33.15 +/- 0.18 | 22.64 +/- 5.51 | 70.42 +/- 2.46 |
| HyperVul-RiskSafety | gated | 2 | 17.28 +/- 4.34 | 59.38 +/- 9.38 | 25.99 +/- 4.20 | 38.26 +/- 1.35 | 14.49 +/- 1.23 | 61.45 +/- 5.10 |
| Current HyperVul | augmented_data | 2 | 15.53 +/- 1.45 | 59.38 +/- 3.12 | 24.54 +/- 1.55 | 37.75 +/- 0.71 | 13.23 +/- 0.01 | 65.41 +/- 0.37 |
| Pairwise-RGCN | augmented_data | 2 | 14.55 +/- 0.26 | 53.12 +/- 3.12 | 22.82 +/- 0.04 | 34.67 +/- 0.77 | 13.85 +/- 0.24 | 64.80 +/- 1.44 |

## Localization
| Model | Variant | Seeds | Top-1 | Top-3 | Top-5 | MRR | Recall@3 |
|---|---|---:|---:|---:|---:|---:|---:|
| Function-MLP | augmented_data | 2 | 59.38 +/- 3.12 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 74.01 +/- 1.04 | 85.42 +/- 0.00 |
| Pairwise-GAT | augmented_data | 2 | 62.50 +/- 0.00 | 75.00 +/- 0.00 | 93.75 +/- 0.00 | 72.65 +/- 0.00 | 70.83 +/- 0.00 |
| HyperVul-RiskSafety | gated | 2 | 56.25 +/- 0.00 | 87.50 +/- 6.25 | 87.50 +/- 6.25 | 70.98 +/- 2.50 | 85.42 +/- 6.25 |
| Current HyperVul | augmented_data | 2 | 53.12 +/- 9.38 | 84.38 +/- 3.12 | 93.75 +/- 0.00 | 70.71 +/- 5.50 | 82.29 +/- 3.12 |
| Sequence-BiGRU | augmented_data | 2 | 56.25 +/- 6.25 | 68.75 +/- 0.00 | 90.62 +/- 3.12 | 67.70 +/- 3.07 | 64.58 +/- 0.00 |
| CallGraph-GAT | augmented_data | 2 | 50.00 +/- 6.25 | 78.12 +/- 3.12 | 93.75 +/- 0.00 | 66.97 +/- 2.86 | 73.96 +/- 3.12 |
| Function+Features MLP | augmented_data | 2 | 50.00 +/- 0.00 | 75.00 +/- 0.00 | 93.75 +/- 0.00 | 66.56 +/- 0.16 | 70.83 +/- 0.00 |
| Pairwise-RGCN | augmented_data | 2 | 37.50 +/- 6.25 | 62.50 +/- 0.00 | 84.38 +/- 3.12 | 56.84 +/- 3.48 | 62.50 +/- 0.00 |

## Demo Table Shape
The main paper table should use the `Validation Target Recall 90` block if recall is the priority, and the `Test-Oracle Upper Bound` block as the performance ceiling.
