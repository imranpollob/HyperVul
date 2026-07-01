# Phase 1A Hard-Negative Safety Report

No augmentation was used. Hard negatives were mined only from train predictions. Validation was used for threshold selection and model comparison; test was evaluated once per trained seed/configuration.

## Split Counts
| Run | Split | Contracts | Positive | Negative |
|---|---|---:|---:|---:|
| all_scope | train | 1339 | 140 | 1199 |
| all_scope | val | 280 | 30 | 250 |
| all_scope | test | 212 | 30 | 182 |
| reentrancy_only | train | 1274 | 75 | 1199 |
| reentrancy_only | val | 264 | 14 | 250 |
| reentrancy_only | test | 198 | 16 | 182 |

## False-Positive Taxonomy
| Category | Train/Val Examples |
|---|---:|
| protected reentrancy-like pattern | 352 |
| other recurring pattern | 54 |
| trusted/fixed callee | 28 |
| external call after state update | 22 |
| possible mislabeled negative | 19 |
| owner-only/admin-only risky function | 10 |
| safe ERC20 wrapper | 9 |
| checked low-level call | 4 |
| many risky interactions but no confirmed finding | 2 |

## Contract Metrics
Validation max-F1 threshold, mean +/- std over 5 seeds.

| Run | Strategy | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | baseline | 23.43 +/- 1.75 | 53.33 +/- 5.16 | 32.40 +/- 1.37 | 42.26 +/- 1.87 | 28.51 +/- 2.35 | 70.33 +/- 0.60 |
| all_scope | hard_negative_oversample | 22.81 +/- 3.75 | 67.33 +/- 9.98 | 33.47 +/- 3.09 | 47.32 +/- 2.23 | 24.34 +/- 3.83 | 68.84 +/- 5.20 |
| all_scope | hard_negative_upweight | 23.11 +/- 1.38 | 72.67 +/- 5.73 | 34.98 +/- 1.50 | 50.69 +/- 2.27 | 26.22 +/- 0.98 | 70.24 +/- 0.95 |
| reentrancy_only | baseline | 57.00 +/- 39.95 | 18.75 +/- 11.86 | 24.35 +/- 12.22 | 20.12 +/- 11.07 | 32.70 +/- 6.15 | 69.99 +/- 1.02 |
| reentrancy_only | hard_negative_oversample | 1.33 +/- 2.67 | 1.25 +/- 2.50 | 1.29 +/- 2.58 | 1.27 +/- 2.53 | 16.13 +/- 3.81 | 64.49 +/- 3.15 |
| reentrancy_only | hard_negative_upweight | 20.00 +/- 40.00 | 1.25 +/- 2.50 | 2.35 +/- 4.71 | 1.54 +/- 3.08 | 22.02 +/- 5.35 | 69.14 +/- 0.66 |

## Localization Metrics
| Run | Strategy | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all_scope | baseline | 46.00 +/- 2.49 | 77.33 +/- 2.49 | 92.00 +/- 1.63 | 64.89 +/- 0.89 | 35.78 +/- 1.63 | 70.89 +/- 1.94 | 89.56 +/- 1.70 |
| all_scope | hard_negative_oversample | 45.33 +/- 4.00 | 80.67 +/- 7.42 | 94.00 +/- 1.33 | 65.46 +/- 3.34 | 36.22 +/- 2.57 | 75.78 +/- 8.50 | 91.11 +/- 2.53 |
| all_scope | hard_negative_upweight | 46.00 +/- 8.27 | 82.67 +/- 2.49 | 93.33 +/- 0.00 | 66.58 +/- 3.85 | 36.78 +/- 5.40 | 75.22 +/- 2.21 | 91.22 +/- 0.82 |
| reentrancy_only | baseline | 58.75 +/- 5.00 | 88.75 +/- 2.50 | 93.75 +/- 0.00 | 74.34 +/- 2.70 | 51.67 +/- 3.33 | 85.42 +/- 3.42 | 91.67 +/- 0.00 |
| reentrancy_only | hard_negative_oversample | 56.25 +/- 9.68 | 91.25 +/- 5.00 | 93.75 +/- 0.00 | 72.89 +/- 6.05 | 49.79 +/- 8.08 | 87.71 +/- 5.45 | 91.67 +/- 0.00 |
| reentrancy_only | hard_negative_upweight | 58.75 +/- 3.06 | 90.00 +/- 5.00 | 93.75 +/- 0.00 | 74.65 +/- 2.52 | 49.17 +/- 2.83 | 87.92 +/- 5.00 | 92.08 +/- 0.83 |

## Safety Feature Notes
High-reliability heuristics: nonreentrant_modifier, return_value_checked, safe_erc20_wrapper, try_catch_presence.
Moderate-reliability heuristics: require/assert guard before call, state update before/after external call, and owner/access-control signals. These are useful for taxonomy but are not proof of safety.
Lower-reliability heuristics include callee controllability, trusted/fixed callee, many-risky-interaction count, and inheritance summaries; treat them as weak context features.

## Hard-Negative Outcome

- All-scope hard-negative upweighting improved recall and F1 but did not improve precision: precision changed from 23.43% to 23.11%, recall from 53.33% to 72.67%, and F1 from 32.40% to 34.98%.
- All-scope false positives increased under both hard-negative strategies at the validation-selected max-F1 operating point: mean FP count went from 53.0 to 73.0.
- Reentrancy-only hard-negative mining collapsed recall: baseline recall was 18.75%, while both hard-negative strategies averaged 1.25% recall.
- Safety features are useful for explaining false positives, but simple concatenation into the symbolic vector did not improve the Phase 0E no-safety F1 baselines.

## Final Recommendation
- Dominant false-positive category: `protected reentrancy-like pattern`.
- Hard-negative mining did not improve precision. All-scope upweighting improved F1 by trading into much higher recall, while reentrancy-only hard-negative mining produced a recall collapse.
- Reliable safety/context features: `nonreentrant_modifier`, `return_value_checked`, `safe_erc20_wrapper`, and `try_catch_presence`. Guard/state/access-control features are useful but need a model that can reason about risk versus safety rather than just consume them as extra scalars.
- Phase 1B should not be broad augmentation. The next priority should be a risk-vs-safety architecture and manual review of possible mislabeled negatives/protected reentrancy-like false positives. Contrastive training is a secondary option after label review; unchecked low-level call remains manual-review only.
