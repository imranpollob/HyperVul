# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42, 43, 44, 45, 46]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 53.42±1.15 | 37.22±1.24 | 94.67±1.09 | 72.31±0.68 | 62.82±0.70 | 84.80±0.38 | 41.74±1.29 | 62.54±1.59 |
| **pairwise-gcn** | 59.76±5.31 | 43.80±6.09 | 95.56±1.99 | 76.88±2.99 | 73.50±2.66 | 89.47±1.49 | 49.04±6.01 | 67.81±4.76 |
| **pairwise-gat** | 57.66±6.24 | 41.43±6.27 | 96.44±3.01 | 75.75±4.62 | 71.79±3.05 | 89.55±2.67 | 46.60±5.47 | 66.30±6.78 |
| **hypergraph** | 56.68±1.31 | 39.80±1.59 | 98.67±1.78 | 76.09±0.41 | 65.72±1.16 | 87.32±0.52 | 45.48±1.59 | 65.62±1.03 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=17, pairwise-only-correct=17, p=0.8638
