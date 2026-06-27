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
| confirmed_positive_reentrancy | proposed_label | 21 |
| confirmed_protected_negative | proposed_label | 169 |
| ambiguous_quarantine | proposed_label | 118 |
| wrong_scope_or_other_vulnerability | proposed_label | 90 |
| insufficient_evidence | proposed_label | 4 |
| ignore | reviewed_view_action | 334 |
| keep | reviewed_view_action | 20221 |
| set_negative | reviewed_view_action | 426 |
| set_positive | reviewed_view_action | 42 |
| labels_changed_to_positive | summary | 21 |
| quarantined_or_insufficient | summary | 122 |

## Retrained Contract Metrics
Validation max-F1 threshold, mean +/- std over seeds.

| Run | Variant | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 25.54 +/- 3.01 | 60.00 +/- 10.95 | 35.23 +/- 1.97 | 46.29 +/- 3.00 | 36.58 +/- 3.25 | 73.41 +/- 0.76 |
| all_scope | gated | 24.24 +/- 3.15 | 58.00 +/- 13.43 | 33.37 +/- 2.41 | 44.11 +/- 5.00 | 32.62 +/- 2.48 | 71.54 +/- 0.61 |
| all_scope | rule_suppression | 23.90 +/- 2.31 | 61.33 +/- 4.52 | 34.23 +/- 2.12 | 46.42 +/- 1.47 | 29.19 +/- 3.60 | 71.00 +/- 1.41 |
| reentrancy_only | concat | 20.22 +/- 12.23 | 50.00 +/- 15.81 | 24.25 +/- 4.22 | 33.03 +/- 2.93 | 31.43 +/- 3.72 | 70.98 +/- 1.73 |
| reentrancy_only | gated | 27.73 +/- 13.74 | 41.25 +/- 17.05 | 27.18 +/- 3.79 | 32.28 +/- 7.69 | 25.14 +/- 2.06 | 70.54 +/- 0.98 |
| reentrancy_only | rule_suppression | 17.64 +/- 3.89 | 41.25 +/- 17.94 | 22.88 +/- 1.61 | 29.62 +/- 4.10 | 22.37 +/- 1.34 | 67.10 +/- 0.89 |

## Localization Metrics
| Run | Variant | Top-1 | Top-3 | Top-5 | MRR | Recall@1 | Recall@3 | Recall@5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all_scope | concat | 56.67 +/- 3.65 | 84.00 +/- 2.49 | 94.00 +/- 1.33 | 72.50 +/- 1.87 | 45.22 +/- 2.67 | 78.89 +/- 2.79 | 90.56 +/- 0.00 |
| all_scope | gated | 48.00 +/- 2.67 | 81.33 +/- 1.63 | 92.00 +/- 1.63 | 67.22 +/- 1.39 | 37.44 +/- 2.67 | 76.67 +/- 1.86 | 89.22 +/- 1.63 |
| all_scope | rule_suppression | 40.00 +/- 5.96 | 83.33 +/- 0.00 | 96.00 +/- 1.33 | 61.87 +/- 3.40 | 30.78 +/- 4.88 | 75.11 +/- 0.82 | 88.67 +/- 0.75 |
| reentrancy_only | concat | 65.00 +/- 5.00 | 87.50 +/- 0.00 | 92.50 +/- 2.50 | 78.23 +/- 2.51 | 56.25 +/- 3.23 | 81.88 +/- 0.83 | 90.42 +/- 2.50 |
| reentrancy_only | gated | 66.25 +/- 3.06 | 87.50 +/- 0.00 | 93.75 +/- 0.00 | 79.06 +/- 1.53 | 60.00 +/- 3.06 | 81.46 +/- 1.02 | 91.67 +/- 0.00 |
| reentrancy_only | rule_suppression | 37.50 +/- 3.95 | 92.50 +/- 2.50 | 93.75 +/- 0.00 | 63.44 +/- 1.97 | 33.75 +/- 3.06 | 85.21 +/- 2.50 | 87.71 +/- 1.53 |

## Final Recommendation
- Confirmed positive relabel candidates: 21.
- Confirmed protected negatives: 169.
- Quarantined/insufficient examples: 122.
- Wrong-scope or other-vulnerability examples: 90.
- Label cleanup did not improve precision versus Phase 1B in this automatic review pass. Phase 1B best all-scope precision was 29.37; Phase 1C best all-scope precision is 25.54 with `concat`.
- Protected false positives decreased modestly on validation after cleanup for the suppression variants: all-scope `gated` reduced reviewed-concat protected FPs by 3.0 on average, and `rule_suppression` by 3.6. This is not enough to claim the issue is solved.
- Reentrancy-only is cleaner as a training view because ambiguous/wrong-scope examples are now quarantined or ignored, but reentrancy-only metrics did not improve over Phase 1B.
- Phase 1D should be manual label acceptance/cleanup first, then contrastive protected-vs-vulnerable reentrancy training. Targeted augmentation is not safe to start until relabel candidates and quarantine decisions are resolved.
