# HyperVul — Multi-Seed Ablation Summary

Seeds per arm: **Baseline**=[42, 43, 44, 45, 46], **+SCL**=[42, 43, 44, 45, 46], **+SCL+Loc**=[42, 43, 44, 45, 46]

## 1. OOD Holdout FPR (mean ± std across seeds; [pooled 95% Wilson CI])

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
| :-- | :--: | :--: | :--: | :--: |
| Baseline | 33.7±5.9 [29,39] | 55.8±9.4 [54,58] | 53.9±3.2 [51,57] | 41.6±8.7 [39,44] |
| +SCL | 34.6±6.0 [30,40] | 61.9±11.7 [60,64] | 54.3±6.4 [51,57] | 46.5±8.5 [44,49] |
| +SCL+Loc | 41.9±5.7 [37,47] | 68.4±12.9 [66,70] | 43.3±10.3 [40,46] | 45.3±14.8 [43,48] |

## 2. Test Performance (mean ± std across seeds)

| Arm | F1 | PRECISION | RECALL | F2 | PR_AUC | ROC_AUC |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: |
| Baseline | 61.5±3.1 | 45.3±3.1 | 95.9±2.5 | 78.4±2.6 | 64.0±1.9 | 87.0±1.6 |
| +SCL | 60.2±4.5 | 44.0±5.1 | 96.4±2.6 | 77.6±2.3 | 62.6±3.9 | 86.3±1.4 |
| +SCL+Loc | 62.0±4.8 | 46.5±5.8 | 94.1±4.1 | 77.8±2.8 | 65.6±2.0 | 86.5±1.1 |

## 3. Paired Significance — McNemar on holdout FP decisions (pooled over seeds)

`b` = first arm flags FP where second is clean; `c` = reverse. p < 0.05 ⇒ the two arms make significantly different clean-code FP decisions.

| Arm A vs Arm B | Holdout | b (A-only FP) | c (B-only FP) | p (McNemar) |
| :-- | :-- | :--: | :--: | :--: |
| Baseline vs +SCL | OZ-Holdout | 8 | 11 | 0.6476 |
| Baseline vs +SCL | MakerDAO | 41 | 139 | 0.0000 **\*** |
| Baseline vs +SCL | Bancor | 29 | 33 | 0.7035 |
| Baseline vs +SCL | Liquity | 44 | 112 | 0.0000 **\*** |
| Baseline vs +SCL+Loc | OZ-Holdout | 3 | 29 | 0.0000 **\*** |
| Baseline vs +SCL+Loc | MakerDAO | 75 | 287 | 0.0000 **\*** |
| Baseline vs +SCL+Loc | Bancor | 143 | 33 | 0.0000 **\*** |
| Baseline vs +SCL+Loc | Liquity | 125 | 177 | 0.0033 **\*** |
| +SCL vs +SCL+Loc | OZ-Holdout | 5 | 28 | 0.0001 **\*** |
| +SCL vs +SCL+Loc | MakerDAO | 116 | 230 | 0.0000 **\*** |
| +SCL vs +SCL+Loc | Bancor | 152 | 38 | 0.0000 **\*** |
| +SCL vs +SCL+Loc | Liquity | 201 | 185 | 0.4452 |

> Lower-FPR arm = the one with the smaller own-only-FP count. A significant p with c < b means Arm B fixed more clean-code false positives than it introduced.