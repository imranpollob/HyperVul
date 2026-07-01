# HyperVul Quick Sweep

All rows use the HyperVul typed hyperedge representation. This is a one-seed search for promising tool configurations.

| Variant | Symbolic | Loss | Early Stop | SCL Pretrain | Hard Neg Weight | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC | Threshold |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbolic-full | full | bce | True | 0 | 1.0 | 29.51 | 43.90 | 35.29 | 40.00 | 30.87 | 86.21 | 0.9570 |
| symbolic-asl | full | asl | True | 0 | 1.0 | 33.90 | 48.78 | 40.00 | 44.84 | 37.56 | 86.84 | 0.8490 |
| symbolic-asl-scl-hardneg | full | asl | True | 15 | 3.0 | 25.35 | 43.90 | 32.14 | 38.30 | 26.88 | 85.40 | 0.9130 |

Best by F2: `symbolic-asl` (44.84).
Best by PR-AUC: `symbolic-asl` (37.56).

Paste this file back for review after the run completes.
