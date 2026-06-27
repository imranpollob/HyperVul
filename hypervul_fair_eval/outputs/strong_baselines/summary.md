# Strong Generic Baseline Sweep

All rows are generic non-hyperedge baselines. They are tuned independently but do not use HyperVul hyperedges.

| Model | Uses Hyperedge | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| function-mlp | No | 15.34 +/- 2.54 | 64.88 +/- 6.83 | 24.59 +/- 3.02 | 38.84 +/- 2.42 | 32.74 +/- 1.43 | 82.80 +/- 1.15 |
| function-features-mlp | No | 15.63 +/- 0.75 | 72.20 +/- 3.31 | 25.69 +/- 1.13 | 41.86 +/- 1.68 | 27.93 +/- 1.80 | 84.48 +/- 0.91 |
| sequence-bigru | No | 18.80 +/- 1.30 | 78.54 +/- 7.14 | 30.24 +/- 1.48 | 47.79 +/- 1.94 | 28.29 +/- 1.39 | 87.45 +/- 0.78 |
| callgraph-gat | No | 17.89 +/- 3.87 | 65.85 +/- 7.71 | 27.69 +/- 4.11 | 41.85 +/- 2.48 | 31.25 +/- 3.80 | 85.84 +/- 1.01 |
| pairwise-rgcn | No | 13.89 +/- 2.07 | 73.17 +/- 14.55 | 23.01 +/- 2.28 | 38.41 +/- 1.46 | 28.42 +/- 1.75 | 84.02 +/- 0.95 |
| pairwise-gat | No | 16.72 +/- 2.67 | 63.90 +/- 2.84 | 26.39 +/- 3.39 | 40.59 +/- 3.40 | 30.11 +/- 4.36 | 84.90 +/- 1.49 |

Paste this file back for review after the run completes.
