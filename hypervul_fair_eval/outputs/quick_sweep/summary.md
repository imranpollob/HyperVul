# HyperVul Quick Sweep

All rows use the HyperVul typed hyperedge representation. This is a one-seed search for promising tool configurations.

| Variant | Symbolic | Loss | Early Stop | SCL Pretrain | Hard Neg Weight | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Threshold |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| current-full | legacy8 | bce | True | 0 | 1.0 | 19.23 | 73.17 | 30.46 | 46.87 | 26.83 | 85.84 | 0.8060 |
| symbolic-full | full | bce | True | 0 | 1.0 | 18.23 | 85.37 | 30.04 | 49.16 | 30.87 | 86.21 | 0.8600 |
| symbolic-asl | full | asl | True | 0 | 1.0 | 15.00 | 87.80 | 25.62 | 44.55 | 37.56 | 86.84 | 0.7290 |
| symbolic-asl-earlystop | full | asl | True | 0 | 1.0 | 15.00 | 87.80 | 25.62 | 44.55 | 37.56 | 86.84 | 0.7290 |
| symbolic-asl-scl | full | asl | True | 15 | 1.0 | 17.57 | 63.41 | 27.51 | 41.67 | 26.46 | 84.53 | 0.6130 |
| symbolic-asl-scl-hardneg | full | asl | True | 15 | 3.0 | 19.31 | 68.29 | 30.11 | 45.31 | 26.88 | 85.40 | 0.7800 |

Best by F2: `symbolic-full` (49.16).
Best by PR-AUC: `symbolic-asl` (37.56).

Paste this file back for review after the run completes.
