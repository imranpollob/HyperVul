# Reentrancy Better Labels v1

This dataset is a reentrancy-focused graph view with Phase 1C review labels applied. Test labels are unchanged. No synthetic negative examples are generated.

## Output Files
- `data/reentrancy_better_labels_v1/train.json`
- `data/reentrancy_better_labels_v1/val.json`
- `data/reentrancy_better_labels_v1/test.json`
- `data/reentrancy_better_labels_v1/reentrancy_labels.csv`
- `data/reentrancy_better_labels_v1/positive_pattern_augmentation_v1.jsonl`

## Counts
| Split | Contracts | Pos Contracts | Neg Contracts | Labeled Interactions | Pos Int | Neg Int | Ignored | Neg:Pos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| train | 1274 | 83 | 1191 | 8575 | 108 | 8467 | 85 | 78.40 |
| val | 264 | 23 | 241 | 1424 | 35 | 1389 | 92 | 39.69 |
| test | 198 | 16 | 182 | 1071 | 20 | 1051 | 0 | 52.55 |

## Label Status Counts
- ambiguous_quarantine: 102
- insufficient_evidence: 4
- review_confirmed_positive: 17
- review_confirmed_protected_negative: 158
- scope_default: 10895
- wrong_scope_excluded: 71

## Positive-Only Pattern Augmentation
- Synthetic positive pattern variants: 80
- Families: claimReward, exit, payout, redeemShares, refund, release, unstake, withdraw

## Intended Use
Use this dataset for reentrancy contract-level detection and top-k localization. For precision, train with the real protected negatives already present in the labeled graph view; do not generate synthetic negatives.
