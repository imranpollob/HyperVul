# HyperVul — Representation Comparison (Hyperedge vs Pairwise)

Seeds: [42, 43, 44, 45, 46]. Identical data (base + 100 OZ + 100 Aave), config (hidden=256, dropout=0.3, lr=0.001, layers=2), threshold rule (highest thr with >=95% val recall). Only the representation varies.

| Model | F1 | Precision | Recall | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **set** | 44.25±3.12 | 29.05±3.01 | 94.09±4.22 | 64.72±2.31 | 51.16±4.43 | 70.95±2.92 | 35.51±3.55 | 51.67±2.98 |
| **pairwise-gcn** | 55.18±4.76 | 40.30±5.11 | 89.09±4.41 | 71.26±3.23 | 54.33±4.20 | 80.56±1.05 | 48.70±6.99 | 60.38±4.70 |
| **pairwise-gat** | 52.46±2.73 | 37.38±3.29 | 89.09±5.64 | 69.49±2.43 | 57.86±10.38 | 80.55±3.38 | 44.96±5.68 | 58.78±1.67 |
| **hypergraph** | 50.43±2.54 | 35.96±2.93 | 85.00±2.73 | 66.62±1.55 | 52.61±3.17 | 76.45±0.98 | 41.88±4.02 | 58.38±2.30 |

**McNemar (hypergraph vs pairwise-gcn, seed 42)**: hypergraph-only-correct=3, pairwise-only-correct=20, p=0.0008
