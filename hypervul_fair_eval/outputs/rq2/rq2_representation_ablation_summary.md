# RQ2 Representation Ablation Summary

| Model | Precision | Recall | F1 | F2 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| pairwise-gat | 15.16 +/- 1.90 | 59.51 +/- 5.48 | 24.01 +/- 2.13 | 37.19 +/- 1.69 | 27.99 +/- 4.43 | 80.16 +/- 1.59 |
| hyperedge-nn | 17.65 +/- 1.48 | 59.02 +/- 6.05 | 27.08 +/- 1.76 | 39.97 +/- 2.37 | 26.45 +/- 2.96 | 81.08 +/- 0.85 |
| pairwise-gcn | 13.37 +/- 1.60 | 54.15 +/- 9.18 | 21.24 +/- 1.72 | 33.11 +/- 2.07 | 21.40 +/- 1.80 | 78.93 +/- 1.65 |
| set-pool | 13.42 +/- 1.21 | 65.85 +/- 5.34 | 22.25 +/- 1.65 | 36.83 +/- 2.06 | 22.95 +/- 1.26 | 79.79 +/- 0.60 |

## Seed-Paired Significance

Reference model: `hyperedge-nn`. Test: exact sign-flip permutation over paired seed-level metric deltas.

| Comparison | Metric | Mean Delta | p-value |
|---|---|---:|---:|
| hyperedge-nn vs set-pool | f1 | 4.82 | 0.0625 |
| hyperedge-nn vs set-pool | f2 | 3.14 | 0.1875 |
| hyperedge-nn vs set-pool | pr_auc | 3.50 | 0.0625 |
| hyperedge-nn vs set-pool | roc_auc | 1.29 | 0.1875 |
| hyperedge-nn vs pairwise-gcn | f1 | 5.84 | 0.0625 |
| hyperedge-nn vs pairwise-gcn | f2 | 6.86 | 0.0625 |
| hyperedge-nn vs pairwise-gcn | pr_auc | 5.04 | 0.1250 |
| hyperedge-nn vs pairwise-gcn | roc_auc | 2.15 | 0.1250 |
| hyperedge-nn vs pairwise-gat | f1 | 3.06 | 0.1250 |
| hyperedge-nn vs pairwise-gat | f2 | 2.79 | 0.1250 |
| hyperedge-nn vs pairwise-gat | pr_auc | -1.55 | 0.6875 |
| hyperedge-nn vs pairwise-gat | roc_auc | 0.92 | 0.4375 |
