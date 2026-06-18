# HyperVul — Multi-Seed Ablation Summary

Seeds per arm: **Sym:none**=[42, 43, 44, 45, 46], **Sym:security**=[42, 43, 44, 45, 46], **Sym:full**=[42, 43, 44, 45, 46]

## 1. OOD Holdout FPR (mean ± std across seeds; [pooled 95% Wilson CI])

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
| :-- | :--: | :--: | :--: | :--: |
| Sym:none | 31.1±7.8 [26,36] | 69.4±10.0 [67,71] | 51.9±6.6 [49,55] | 44.1±11.1 [42,47] |
| Sym:security | 26.7±6.3 [22,32] | 59.6±1.4 [58,62] | 46.2±4.6 [43,49] | 37.3±2.9 [35,40] |
| Sym:full | 22.2±6.2 [18,27] | 64.1±5.8 [62,66] | 40.5±3.7 [38,43] | 34.8±2.2 [32,37] |

## 2. Test Performance (mean ± std across seeds)

| Arm | F1 | PRECISION | RECALL | F2 | PR_AUC | ROC_AUC |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: |
| Sym:none | 64.2±1.2 | 48.9±1.9 | 93.6±2.5 | 79.1±0.9 | 64.4±2.6 | 86.8±1.2 |
| Sym:security | 65.6±2.3 | 50.0±2.6 | 95.5±0.0 | 80.7±1.4 | 68.2±1.8 | 88.4±1.0 |
| Sym:full | 66.0±1.8 | 50.4±2.0 | 95.5±1.6 | 81.0±1.5 | 69.6±1.8 | 88.6±0.9 |

## 3. Paired Significance — McNemar on holdout FP decisions (pooled over seeds)

`b` = first arm flags FP where second is clean; `c` = reverse. p < 0.05 ⇒ the two arms make significantly different clean-code FP decisions.

| Arm A vs Arm B | Holdout | b (A-only FP) | c (B-only FP) | p (McNemar) |
| :-- | :-- | :--: | :--: | :--: |
| Sym:none vs Sym:security | OZ-Holdout | 16 | 2 | 0.0013 **\*** |
| Sym:none vs Sym:security | MakerDAO | 177 | 11 | 0.0000 **\*** |
| Sym:none vs Sym:security | Bancor | 79 | 20 | 0.0000 **\*** |
| Sym:none vs Sym:security | Liquity | 126 | 32 | 0.0000 **\*** |
| Sym:none vs Sym:full | OZ-Holdout | 30 | 2 | 0.0000 **\*** |
| Sym:none vs Sym:full | MakerDAO | 144 | 59 | 0.0000 **\*** |
| Sym:none vs Sym:full | Bancor | 137 | 18 | 0.0000 **\*** |
| Sym:none vs Sym:full | Liquity | 152 | 23 | 0.0000 **\*** |
| Sym:security vs Sym:full | OZ-Holdout | 15 | 1 | 0.0005 **\*** |
| Sym:security vs Sym:full | MakerDAO | 14 | 95 | 0.0000 **\*** |
| Sym:security vs Sym:full | Bancor | 73 | 13 | 0.0000 **\*** |
| Sym:security vs Sym:full | Liquity | 61 | 26 | 0.0002 **\*** |

> Lower-FPR arm = the one with the smaller own-only-FP count. A significant p with c < b means Arm B fixed more clean-code false positives than it introduced.

## 4. OOD Holdout FPR at MATCHED test-recall (90%) — mean ± std

Fairer than §1: all-clean holdout FPR is threshold-driven, so each arm/seed is evaluated at the threshold that yields the same test recall. Removes the per-arm threshold-tuning confound.

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
| :-- | :--: | :--: | :--: | :--: |
| Sym:none | 25.4±11.1 | 60.9±14.1 | 45.5±10.7 | 33.5±11.7 |
| Sym:security | 14.9±4.3 | 45.8±5.4 | 34.3±6.1 | 18.2±7.5 |
| Sym:full | 14.0±3.3 | 49.8±5.6 | 28.8±3.7 | 16.5±5.4 |

> This is the operating-point-controlled view. Compare arms here, not in §1.