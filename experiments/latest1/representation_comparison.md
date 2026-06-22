# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42, 43, 44, 45, 46]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 53.36±1.02 | 37.02±0.82 | 95.56±1.41 | 72.59±1.17 | 62.78±1.34 | 84.87±0.51 | 42.39±2.10 | 61.95±0.70 |
| **pairwise-gcn** | 60.19±4.90 | 44.49±5.57 | 94.22±1.78 | 76.66±2.73 | 74.78±3.63 | 89.50±1.53 | 48.44±4.99 | 68.82±4.87 |
| **pairwise-gat** | 60.33±2.58 | 43.94±2.43 | 96.44±3.61 | 77.79±2.74 | 72.20±1.98 | 89.97±1.66 | 49.78±2.94 | 68.20±3.35 |
| **hypergraph** | 59.20±2.98 | 42.48±3.44 | 98.22±1.66 | 77.64±1.48 | 64.49±1.57 | 87.39±0.57 | 49.06±3.44 | 66.93±2.53 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=21, pairwise-only-correct=11, p=0.1116
