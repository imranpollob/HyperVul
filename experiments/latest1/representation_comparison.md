# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42, 43, 44, 45, 46]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 51.09±5.06 | 34.81±4.36 | 96.89±2.27 | 71.19±4.64 | 61.12±2.73 | 83.99±4.72 | 40.26±4.96 | 59.54±5.23 |
| **pairwise-gcn** | 58.71±2.89 | 42.59±2.80 | 94.67±1.78 | 76.01±2.45 | 62.72±3.62 | 86.40±1.33 | 47.93±4.78 | 66.39±1.59 |
| **pairwise-gat** | 61.02±2.23 | 44.79±2.54 | 96.00±1.66 | 78.06±1.40 | 68.10±1.87 | 88.10±0.62 | 50.44±2.08 | 68.89±2.58 |
| **hypergraph** | 58.33±3.72 | 42.35±3.89 | 94.22±1.09 | 75.53±2.57 | 64.21±2.94 | 86.15±1.43 | 47.35±4.62 | 66.31±2.74 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=11, pairwise-only-correct=8, p=0.6464
