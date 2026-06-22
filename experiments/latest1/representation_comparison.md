# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 53.16 | 37.17 | 93.33 | 71.67 | 62.36 | 84.97 | 40.58 | 62.92 |
| **pairwise-gcn** | 56.76 | 40.78 | 93.33 | 74.20 | 74.23 | 88.94 | 42.42 | 68.29 |
| **pairwise-gat** | 61.64 | 44.55 | 100.00 | 80.07 | 77.46 | 91.91 | 50.00 | 70.73 |
| **hypergraph** | 64.66 | 48.86 | 95.56 | 80.22 | 66.39 | 87.75 | 54.55 | 71.79 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=25, pairwise-only-correct=8, p=0.0053
