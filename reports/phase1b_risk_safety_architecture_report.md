# Phase 1B Risk-vs-Safety Architecture

No broad augmentation was used. Architecture selection is based on train/validation behavior; test is reported only after validation threshold selection.

## Split Counts
| Run | Split | Contracts | Positive | Negative |
|---|---|---:|---:|---:|
| all_scope | train | 1339 | 140 | 1199 |
| all_scope | val | 280 | 30 | 250 |
| all_scope | test | 212 | 30 | 182 |
| reentrancy_only | train | 1274 | 75 | 1199 |
| reentrancy_only | val | 264 | 14 | 250 |
| reentrancy_only | test | 198 | 16 | 182 |

## Contract Metrics
Validation max-F1 threshold, mean +/- std over seeds.

| Run | Variant | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 29.26 +/- 2.12 | 46.00 +/- 6.46 | 35.56 +/- 2.58 | 41.08 +/- 4.26 | 37.96 +/- 2.40 | 74.63 +/- 0.82 |
| all_scope | gated | 29.20 +/- 1.33 | 50.00 +/- 4.22 | 36.75 +/- 0.89 | 43.64 +/- 2.19 | 34.32 +/- 4.24 | 72.45 +/- 0.70 |
| all_scope | rule_suppression | 29.37 +/- 5.72 | 55.33 +/- 14.08 | 36.54 +/- 3.21 | 45.08 +/- 7.12 | 28.95 +/- 1.83 | 72.04 +/- 0.79 |
| all_scope | subtractive | 26.61 +/- 2.17 | 57.33 +/- 4.90 | 36.26 +/- 2.32 | 46.45 +/- 3.05 | 32.12 +/- 1.73 | 72.10 +/- 0.35 |
| reentrancy_only | concat | 33.40 +/- 19.97 | 43.75 +/- 20.92 | 28.69 +/- 6.28 | 32.14 +/- 4.05 | 31.91 +/- 4.29 | 69.73 +/- 2.19 |
| reentrancy_only | gated | 39.82 +/- 6.70 | 23.75 +/- 2.50 | 29.51 +/- 3.00 | 25.73 +/- 2.53 | 24.62 +/- 1.95 | 68.78 +/- 1.35 |
| reentrancy_only | rule_suppression | 30.29 +/- 17.32 | 31.25 +/- 7.91 | 26.53 +/- 5.70 | 27.95 +/- 2.56 | 21.94 +/- 3.12 | 68.53 +/- 0.97 |
| reentrancy_only | subtractive | 29.69 +/- 4.33 | 28.75 +/- 3.06 | 29.18 +/- 3.55 | 28.91 +/- 3.22 | 29.08 +/- 4.09 | 70.01 +/- 0.94 |

## Localization Metrics
| Run | Variant | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 53.33 +/- 0.00 | 84.67 +/- 4.52 | 93.33 +/- 2.98 | 70.57 +/- 1.22 | 41.22 +/- 1.33 | 78.22 +/- 4.38 | 90.89 +/- 3.40 |
| all_scope | gated | 48.67 +/- 4.52 | 82.00 +/- 1.63 | 92.00 +/- 2.67 | 67.67 +/- 2.11 | 39.44 +/- 4.59 | 76.78 +/- 1.02 | 89.22 +/- 2.67 |
| all_scope | rule_suppression | 42.00 +/- 5.81 | 85.33 +/- 3.40 | 96.67 +/- 0.00 | 63.38 +/- 3.79 | 31.67 +/- 4.73 | 77.11 +/- 3.43 | 89.89 +/- 1.19 |
| all_scope | subtractive | 49.33 +/- 2.49 | 78.00 +/- 1.63 | 90.67 +/- 1.33 | 67.43 +/- 1.26 | 38.78 +/- 2.49 | 73.33 +/- 1.41 | 87.56 +/- 0.67 |
| reentrancy_only | concat | 61.25 +/- 4.68 | 87.50 +/- 0.00 | 92.50 +/- 2.50 | 76.43 +/- 2.49 | 52.50 +/- 3.06 | 81.04 +/- 1.02 | 90.42 +/- 2.50 |
| reentrancy_only | gated | 56.25 +/- 3.95 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 74.06 +/- 1.98 | 50.62 +/- 4.15 | 81.46 +/- 1.02 | 91.25 +/- 0.83 |
| reentrancy_only | rule_suppression | 35.00 +/- 5.00 | 87.50 +/- 3.95 | 93.75 +/- 0.00 | 61.99 +/- 2.40 | 31.25 +/- 3.95 | 80.83 +/- 4.15 | 88.96 +/- 1.25 |
| reentrancy_only | subtractive | 52.50 +/- 3.06 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 71.77 +/- 1.91 | 46.25 +/- 3.06 | 82.71 +/- 1.69 | 91.67 +/- 0.00 |

## Protected False-Positive Reduction
- all_scope: mean validation protected-FP reduction vs concat across variants/seeds = -2.95.
- reentrancy_only: mean validation protected-FP reduction vs concat across variants/seeds = 26.35.

All-scope protected reentrancy-like false positives did not decrease relative to the concat architecture. The safety-suppression variants improved some contract metrics, but they did not consistently suppress the dominant false-positive category on the all-scope validation split. Reentrancy-only suppression reduced protected false positives, especially for gated/subtractive variants, but this came with a substantial recall tradeoff for gated.

## Review Packet

- Full protected reentrancy-like review packet: `reports/phase1b_protected_reentrancy_review_packet.csv`.
- Prioritized review subset: `reports/phase1b_protected_reentrancy_prioritized_review_set.csv`.
- Priority tags include `top50_highest_score`, `top50_most_ambiguous`, and `top50_weak_or_no_safety`.

## Final Recommendation
- Risk-vs-safety architecture improves all-scope precision and F1 versus the Phase 1A safety-feature baseline. Phase 1A all-scope baseline precision/F1 was 23.43/32.40; Phase 1B reaches 29.37 precision with `rule_suppression` and 36.75 F1 with `gated`.
- Best all-scope F1 variant: `gated`. Best all-scope precision variant: `rule_suppression`. Best all-scope PR-AUC variant: `concat`.
- Protected reentrancy false positives did not decrease on all-scope; manual relabeling/review is still needed before claiming the safety branch solves the dominant error mode.
- Recall did not collapse on all-scope. Reentrancy-only gated improves precision but drops recall from 43.75% to 23.75% versus concat, so treat reentrancy-only gains cautiously.
- Phase 1C should be label cleanup first, focused on protected reentrancy-like false positives and possible mislabeled negatives. After review, run contrastive protected-vs-vulnerable reentrancy training. Targeted augmentation should wait until the review packet is resolved.
