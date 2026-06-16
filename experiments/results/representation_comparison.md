# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42, 43, 44, 45, 46]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 46.00±2.53 | 30.41±2.01 | 94.55±2.32 | 66.46±2.73 | 51.66±2.87 | 75.41±4.08 | 36.77±1.87 | 53.61±3.36 |
| **pairwise-gcn** | 51.22±2.23 | 36.00±2.47 | 89.55±5.68 | 68.80±2.39 | 48.11±8.67 | 75.84±3.28 | 39.86±1.80 | 59.73±3.02 |
| **pairwise-gat** | 51.92±3.19 | 36.11±3.70 | 93.64±3.64 | 70.70±1.53 | 69.76±4.46 | 86.50±3.67 | 41.26±3.14 | 60.51±2.82 |
| **hypergraph** | 59.43±4.37 | 45.18±5.53 | 88.18±3.02 | 73.68±1.82 | 60.82±5.37 | 82.87±1.72 | 51.43±5.92 | 65.05±3.68 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=29, pairwise-only-correct=9, p=0.0021
