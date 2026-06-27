# Phase 1C Protected Reentrancy Label Cleanup

No augmentation was used. Label decisions use only the Phase 1B protected-reentrancy review packet and train/validation source evidence. Test labels remain unchanged.

## Annotation Guideline
- `confirmed_positive_reentrancy`: external call before critical state update, attacker-controlled callee, missing effective reentrancy guard, repeated withdrawal/drain pattern, or balance/state update after call.
- `confirmed_protected_negative`: effective nonReentrant guard, CEI state update before external call, trusted/fixed callee with no attacker control, external call not affecting vulnerable state, or safe wrapper plus another protection signal.
- `ambiguous_quarantine`: risk and protection evidence conflict or protection is weak. Return-value check alone is not reentrancy protection.
- `wrong_scope_or_other_vulnerability`: not suitable as reentrancy supervision.
- `insufficient_evidence`: source evidence is missing or too weak.

## Label Summary
| Item | Type | Count |
|---|---|---:|
| confirmed_positive_reentrancy | proposed_label | 17 |
| confirmed_protected_negative | proposed_label | 158 |
| ambiguous_quarantine | proposed_label | 102 |
| wrong_scope_or_other_vulnerability | proposed_label | 71 |
| insufficient_evidence | proposed_label | 4 |
| ignore | reviewed_view_action | 435 |
| keep | reviewed_view_action | 20319 |
| set_negative | reviewed_view_action | 269 |
| positive_relabel_candidates | summary | 17 |
| high_confidence_positive_accepted | summary | 0 |
| high_confidence_protected_negative_accepted | summary | 99 |
| quarantined_or_insufficient | summary | 106 |

## Retrained Contract Metrics
Validation max-F1 threshold, mean +/- std over seeds.

| Run | Variant | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 29.42 +/- 2.55 | 44.67 +/- 9.57 | 34.79 +/- 1.89 | 39.80 +/- 5.31 | 38.47 +/- 4.41 | 74.44 +/- 1.35 |
| all_scope | gated | 26.05 +/- 2.53 | 57.33 +/- 5.33 | 35.55 +/- 1.66 | 45.83 +/- 1.13 | 29.42 +/- 3.30 | 71.98 +/- 1.01 |
| all_scope | rule_suppression | 26.23 +/- 0.96 | 66.00 +/- 3.27 | 37.51 +/- 1.09 | 50.59 +/- 1.64 | 31.15 +/- 1.98 | 73.09 +/- 0.42 |
| reentrancy_only | concat | 33.30 +/- 4.58 | 26.25 +/- 2.50 | 29.25 +/- 3.05 | 27.35 +/- 2.62 | 33.17 +/- 7.06 | 69.09 +/- 3.94 |
| reentrancy_only | gated | 26.83 +/- 12.17 | 36.25 +/- 19.92 | 24.98 +/- 3.95 | 28.27 +/- 7.68 | 26.40 +/- 4.37 | 68.64 +/- 1.04 |
| reentrancy_only | rule_suppression | 20.22 +/- 4.02 | 31.25 +/- 6.85 | 23.91 +/- 3.01 | 27.45 +/- 3.38 | 24.61 +/- 1.27 | 69.48 +/- 1.35 |

## Phase 1B vs Phase 1C
| Run | Variant | Phase 1B Precision | Phase 1C Precision | Phase 1B Recall | Phase 1C Recall | Phase 1B F1 | Phase 1C F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 29.26 +/- 2.12 | 29.42 +/- 2.55 | 46.00 +/- 6.46 | 44.67 +/- 9.57 | 35.56 +/- 2.58 | 34.79 +/- 1.89 |
| all_scope | gated | 29.20 +/- 1.33 | 26.05 +/- 2.53 | 50.00 +/- 4.22 | 57.33 +/- 5.33 | 36.75 +/- 0.89 | 35.55 +/- 1.66 |
| all_scope | rule_suppression | 29.37 +/- 5.72 | 26.23 +/- 0.96 | 55.33 +/- 14.08 | 66.00 +/- 3.27 | 36.54 +/- 3.21 | 37.51 +/- 1.09 |
| reentrancy_only | concat | 33.40 +/- 19.97 | 33.30 +/- 4.58 | 43.75 +/- 20.92 | 26.25 +/- 2.50 | 28.69 +/- 6.28 | 29.25 +/- 3.05 |
| reentrancy_only | gated | 39.82 +/- 6.70 | 26.83 +/- 12.17 | 23.75 +/- 2.50 | 36.25 +/- 19.92 | 29.51 +/- 3.00 | 24.98 +/- 3.95 |
| reentrancy_only | rule_suppression | 30.29 +/- 17.32 | 20.22 +/- 4.02 | 31.25 +/- 7.91 | 31.25 +/- 6.85 | 26.53 +/- 5.70 | 23.91 +/- 3.01 |

## Localization Metrics
| Run | Variant | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 54.00 +/- 2.49 | 83.33 +/- 2.98 | 92.00 +/- 2.67 | 70.77 +/- 0.82 | 41.89 +/- 2.67 | 78.00 +/- 2.95 | 88.89 +/- 2.11 |
| all_scope | gated | 53.33 +/- 4.71 | 79.33 +/- 2.49 | 90.00 +/- 0.00 | 69.32 +/- 2.00 | 41.89 +/- 3.81 | 75.00 +/- 2.68 | 87.22 +/- 0.00 |
| all_scope | rule_suppression | 40.67 +/- 5.73 | 84.67 +/- 4.52 | 96.67 +/- 0.00 | 63.38 +/- 2.50 | 31.00 +/- 4.56 | 76.11 +/- 3.50 | 89.67 +/- 0.44 |
| reentrancy_only | concat | 62.50 +/- 6.85 | 86.25 +/- 2.50 | 91.25 +/- 3.06 | 76.59 +/- 4.02 | 53.75 +/- 5.50 | 79.79 +/- 3.06 | 88.75 +/- 3.63 |
| reentrancy_only | gated | 55.00 +/- 2.50 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 73.38 +/- 1.22 | 50.00 +/- 1.98 | 80.62 +/- 0.83 | 91.67 +/- 0.00 |
| reentrancy_only | rule_suppression | 31.25 +/- 3.95 | 91.25 +/- 3.06 | 93.75 +/- 0.00 | 60.62 +/- 2.01 | 27.50 +/- 3.06 | 83.96 +/- 3.06 | 89.58 +/- 0.00 |

## Final Recommendation
- Confirmed positive relabel candidates: 17.
- Confirmed protected negatives: 158.
- Quarantined/insufficient examples: 106.
- The reviewed-label rerun does not clearly beat Phase 1B, so Phase 1D should be contrastive protected-vs-vulnerable reentrancy training only after the relabel candidates and quarantine set are manually accepted. Targeted augmentation is not safe to start until then.
