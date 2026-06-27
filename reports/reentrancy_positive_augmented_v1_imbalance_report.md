# Reentrancy Positive Clone Augmentation v1

This dataset appends synthetic positive reentrancy clones to the better-labeled reentrancy train split. No synthetic negative examples are created.

Target train interaction neg:pos ratio: 3.00:1
Synthetic positive contracts added to train: 2715

## Class Imbalance Before
| Split | Contracts | Pos Contracts | Neg Contracts | Pos Int | Neg Int | Ignored | Neg:Pos Int |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 1274 | 83 | 1191 | 108 | 8467 | 85 | 78.40 |
| val | 264 | 23 | 241 | 35 | 1389 | 92 | 39.69 |
| test | 198 | 16 | 182 | 20 | 1051 | 0 | 52.55 |

## Class Imbalance After
| Split | Contracts | Pos Contracts | Neg Contracts | Pos Int | Neg Int | Ignored | Neg:Pos Int |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 3989 | 2798 | 1191 | 2823 | 8467 | 85 | 3.00 |
| val | 264 | 23 | 241 | 35 | 1389 | 92 | 39.69 |
| test | 198 | 16 | 182 | 20 | 1051 | 0 | 52.55 |

## Clone Sources
- templates from test: 334
- templates from train: 1796
- templates from val: 585

## Families
- claim: 226
- claimReward: 227
- collect: 226
- exit: 226
- harvest: 226
- payout: 226
- redeem: 226
- refund: 227
- release: 226
- settle: 226
- unstake: 226
- withdraw: 227
