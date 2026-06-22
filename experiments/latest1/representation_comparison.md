# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 45.12 | 31.09 | 82.22 | 61.87 | 36.13 | 65.45 | 42.25 | 47.31 |
| **pairwise-gcn** | 57.53 | 41.58 | 93.33 | 74.73 | 57.06 | 83.80 | 51.72 | 61.36 |
| **pairwise-gat** | 47.51 | 31.62 | 95.56 | 68.04 | 49.85 | 79.73 | 38.96 | 53.85 |
| **hypergraph** | 45.41 | 30.00 | 93.33 | 65.62 | 48.81 | 75.56 | 37.04 | 51.92 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=1, pairwise-only-correct=40, p=0.0000
