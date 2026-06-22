# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42, 43, 44, 45, 46]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 51.09±5.06 | 34.81±4.36 | 96.89±2.27 | 71.19±4.64 | 61.12±2.73 | 83.99±4.72 | 40.26±4.96 | 59.54±5.23 |
| **pairwise-gcn** | 59.00±2.97 | 42.67±3.11 | 96.00±2.18 | 76.69±2.28 | 61.88±2.62 | 87.36±1.03 | 46.73±4.37 | 68.00±2.05 |
| **pairwise-gat** | 58.86±3.04 | 42.35±3.63 | 97.33±2.59 | 77.05±1.20 | 63.01±1.78 | 87.68±0.71 | 48.67±3.65 | 66.64±2.34 |
| **hypergraph** | 59.11±1.23 | 42.99±1.33 | 94.67±2.27 | 76.29±1.25 | 66.09±2.70 | 86.72±0.46 | 49.40±2.41 | 66.05±1.16 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=13, pairwise-only-correct=7, p=0.2636
