# Phase 1D Contrastive Reentrancy Training

Comparison uses Phase 1B gated as the current best baseline, accepted-label training without contrastive loss, and accepted-label training with margin ranking loss.

## Reentrancy Metrics
| Method | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| accepted_label_only | 35.73 +/- 4.72 | 20.00 +/- 4.68 | 25.34 +/- 4.31 | 21.81 +/- 4.58 | 24.09 +/- 1.51 | 70.34 +/- 1.33 |
| contrastive | 25.37 +/- 14.86 | 22.50 +/- 16.58 | 21.19 +/- 11.55 | 21.23 +/- 13.16 | 22.53 +/- 2.92 | 69.70 +/- 2.36 |
| phase1b_baseline | 39.82 +/- 6.70 | 23.75 +/- 2.50 | 29.51 +/- 3.00 | 25.73 +/- 2.53 | 24.62 +/- 1.95 | 68.78 +/- 1.35 |

## All-Scope Secondary Metrics
| Method | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| accepted_label_only | 27.69 +/- 1.47 | 48.00 +/- 5.42 | 34.98 +/- 1.83 | 41.71 +/- 3.32 | 32.80 +/- 2.18 | 72.21 +/- 0.71 |
| contrastive | 30.04 +/- 2.56 | 52.67 +/- 5.73 | 37.96 +/- 1.47 | 45.44 +/- 2.68 | 38.06 +/- 3.07 | 74.85 +/- 0.37 |
| phase1b_baseline | 29.20 +/- 1.33 | 50.00 +/- 4.22 | 36.75 +/- 0.89 | 43.64 +/- 2.19 | 34.32 +/- 4.24 | 72.45 +/- 0.70 |

## Pair Stats
- train: 228 pairs, 38 vulnerable positives, 76 protected negatives.

## Final Recommendation
- Accepted labels improve the training view but do not beat Phase 1B on reentrancy. Phase 1B reentrancy precision/F1 was 39.82/29.51; accepted-label training reaches 35.73/25.34.
- Contrastive training does not improve reentrancy precision in this run. It reaches 25.37 precision and 21.19 F1, with recall 22.50, so recall does not collapse but precision degrades.
- Contrastive training is promising only as an all-scope secondary signal: all-scope F1 improves from 36.75 to 37.96, PR-AUC from 34.32 to 38.06, and localization also improves.
- Targeted augmentation is not safe until the 21 medium-confidence positive relabel candidates are manually accepted or rejected.
- The project should remain reentrancy-focused for cleanup, but the next step should be manual adjudication plus a stricter protected-vs-vulnerable contrastive setup before any augmentation. Do not return to broad all-scope training as the main experiment yet.
