# HyperVul — Multi-Seed Ablation Summary

Seeds per arm: **Sym:none**=[42, 43, 44, 45, 46], **Sym:security**=[42, 43, 44, 45, 46], **Sym:full**=[42, 43, 44, 45, 46], **run**=[42]

## 1. OOD Holdout FPR (mean ± std across seeds; [pooled 95% Wilson CI])

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
| :-- | :--: | :--: | :--: | :--: |
| Sym:none | 38.4±8.7 [33,44] | 74.6±5.3 [73,76] | 53.0±4.3 [50,56] | 48.0±14.5 [45,51] |
| Sym:security | 38.1±7.7 [33,44] | 75.8±7.4 [74,78] | 57.5±2.6 [54,60] | 51.6±17.0 [49,54] |
| Sym:full | 33.0±8.3 [28,38] | 79.9±5.4 [78,82] | 46.9±4.8 [44,50] | 42.2±9.0 [40,45] |
| run | 46.0±0.0 [34,58] | 87.0±0.0 [83,90] | 63.2±0.0 [56,69] | 69.9±0.0 [64,75] |

## 2. Test Performance (mean ± std across seeds)

| Arm | F1 | PRECISION | RECALL | F2 | PR_AUC | ROC_AUC |
| :-- | :--: | :--: | :--: | :--: | :--: | :--: |
| Sym:none | 52.9±3.0 | 36.9±2.9 | 93.8±1.9 | 71.6±2.3 | 53.2±2.8 | 82.1±1.7 |
| Sym:security | 54.1±2.7 | 37.8±2.8 | 95.6±1.6 | 73.1±2.0 | 60.4±6.3 | 84.3±2.5 |
| Sym:full | 55.9±1.8 | 39.4±1.8 | 96.4±1.2 | 74.7±1.3 | 60.5±6.2 | 84.2±2.4 |
| run | 52.7±0.0 | 36.1±0.0 | 97.8±0.0 | 72.8±0.0 | 62.3±0.0 | 85.3±0.0 |

## 3. Paired Significance — McNemar on holdout FP decisions (pooled over seeds)

`b` = first arm flags FP where second is clean; `c` = reverse. p < 0.05 ⇒ the two arms make significantly different clean-code FP decisions.

| Arm A vs Arm B | Holdout | b (A-only FP) | c (B-only FP) | p (McNemar) |
| :-- | :-- | :--: | :--: | :--: |
| Sym:none vs Sym:security | OZ-Holdout | 12 | 11 | 1.0000 |
| Sym:none vs Sym:security | MakerDAO | 28 | 40 | 0.1818 |
| Sym:none vs Sym:security | Bancor | 11 | 58 | 0.0000 **\*** |
| Sym:none vs Sym:security | Liquity | 37 | 87 | 0.0000 **\*** |
| Sym:none vs Sym:full | OZ-Holdout | 22 | 5 | 0.0015 **\*** |
| Sym:none vs Sym:full | MakerDAO | 9 | 93 | 0.0000 **\*** |
| Sym:none vs Sym:full | Bancor | 97 | 33 | 0.0000 **\*** |
| Sym:none vs Sym:full | Liquity | 168 | 87 | 0.0000 **\*** |
| Sym:none vs run | OZ-Holdout | 0 | 6 | 0.0312 **\*** |
| Sym:none vs run | MakerDAO | 3 | 28 | 0.0000 **\*** |
| Sym:none vs run | Bancor | 2 | 28 | 0.0000 **\*** |
| Sym:none vs run | Liquity | 0 | 47 | 0.0000 **\*** |
| Sym:security vs Sym:full | OZ-Holdout | 23 | 7 | 0.0052 **\*** |
| Sym:security vs Sym:full | MakerDAO | 24 | 96 | 0.0000 **\*** |
| Sym:security vs Sym:full | Bancor | 119 | 8 | 0.0000 **\*** |
| Sym:security vs Sym:full | Liquity | 196 | 65 | 0.0000 **\*** |
| Sym:security vs run | OZ-Holdout | 0 | 3 | 0.2500 |
| Sym:security vs run | MakerDAO | 2 | 6 | 0.2891 |
| Sym:security vs run | Bancor | 4 | 10 | 0.1796 |
| Sym:security vs run | Liquity | 3 | 8 | 0.2266 |
| Sym:full vs run | OZ-Holdout | 0 | 10 | 0.0020 **\*** |
| Sym:full vs run | MakerDAO | 4 | 17 | 0.0072 **\*** |
| Sym:full vs run | Bancor | 0 | 34 | 0.0000 **\*** |
| Sym:full vs run | Liquity | 2 | 81 | 0.0000 **\*** |

> Lower-FPR arm = the one with the smaller own-only-FP count. A significant p with c < b means Arm B fixed more clean-code false positives than it introduced.

## 4. OOD Holdout FPR at MATCHED test-recall (90%) — mean ± std

Fairer than §1: all-clean holdout FPR is threshold-driven, so each arm/seed is evaluated at the threshold that yields the same test recall. Removes the per-arm threshold-tuning confound.

| Arm | OZ-Holdout | MakerDAO | Bancor | Liquity |
| :-- | :--: | :--: | :--: | :--: |
| Sym:none | 30.2±2.7 | 59.4±8.3 | 33.8±9.9 | 21.9±4.9 |
| Sym:security | 24.1±3.1 | 52.9±7.3 | 37.8±8.1 | 23.8±9.9 |
| Sym:full | 19.0±4.0 | 62.3±7.9 | 29.3±9.5 | 20.1±3.5 |
| run | 20.6±0.0 | 36.6±0.0 | 19.1±0.0 | 14.7±0.0 |

> This is the operating-point-controlled view. Compare arms here, not in §1.