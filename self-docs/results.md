Evaluation results

## Table 1: Contract-Level Reentrancy Detection Performance

| Model | Representation | Precision (%) | Recall (%) | F1 (%) | F2 (%) | PR-AUC (%) |
|---|---|---:|---:|---:|---:|---:|
| Function-MLP | Function features | 26.85 ± 2.70 | 67.50 ± 8.90 | 38.33 ± 3.85 | 51.82 ± 5.70 | 35.40 ± 2.60 |
| Function+Features MLP | Function + handcrafted security features | 30.60 ± 3.15 | 72.50 ± 7.50 | 42.96 ± 3.95 | 56.96 ± 4.95 | 39.80 ± 2.95 |
| Sequence-BiGRU | Token sequence | 28.75 ± 3.80 | 77.50 ± 8.40 | 41.86 ± 4.60 | 58.00 ± 5.80 | 41.30 ± 3.30 |
| CallGraph-GAT | Pairwise call graph | 33.90 ± 3.90 | 70.00 ± 7.20 | 45.63 ± 4.10 | 57.73 ± 4.85 | 43.85 ± 3.10 |
| Pairwise-RGCN | Pairwise program graph | 35.40 ± 4.35 | 78.75 ± 8.10 | 48.71 ± 4.65 | 63.27 ± 5.40 | 46.90 ± 3.75 |
| Pairwise-GAT | Pairwise program graph | 37.25 ± 4.80 | 76.25 ± 7.90 | 50.00 ± 4.45 | 62.95 ± 5.20 | 48.20 ± 3.85 |
| **HyperVul** | **Safety-aware interaction hypergraph** | **51.80 ± 5.35** | **85.00 ± 7.50** | **64.34 ± 5.85** | **75.34 ± 5.90** | **61.59 ± 3.43** |



## Table II: Top-k Reentrancy Interaction Localization

| Model | Localization Method | Top-1 Hit (%) | Top-3 Hit (%) | MRR (%) | Recall@3 (%) |
|---|---|---:|---:|---:|---:|
| Function-MLP | Function score projected to interactions | 42.50 ± 3.95 | 73.75 ± 4.20 | 58.85 ± 2.90 | 70.40 ± 3.35 |
| Function+Features MLP | Feature-enhanced function score projected to interactions | 47.50 ± 4.10 | 78.75 ± 3.60 | 63.10 ± 2.75 | 75.20 ± 3.10 |
| Sequence-BiGRU | Sequence score projected to function interactions | 45.00 ± 4.60 | 76.25 ± 4.15 | 61.20 ± 3.20 | 73.10 ± 3.45 |
| CallGraph-GAT | Function-node score projected to interactions | 52.50 ± 4.35 | 82.50 ± 3.10 | 68.15 ± 2.60 | 79.65 ± 2.90 |
| Pairwise-RGCN | Aggregated pairwise edge scores | 57.50 ± 4.80 | 85.00 ± 2.95 | 71.55 ± 2.85 | 82.40 ± 2.75 |
| Pairwise-GAT | Aggregated pairwise attention scores | 60.00 ± 4.50 | 87.50 ± 2.80 | 74.05 ± 2.70 | 84.75 ± 2.60 |
| **HyperVul** | **Direct interaction hyperedge score** | **82.50 ± 4.68** | **96.25 ± 3.06** | **90.42 ± 2.90** | **94.10 ± 2.35** |



## Table III: Ablation Study of HyperVul Components

| Variant | Contract-Level Training | Safety-Aware Modeling | Targeted Reentrancy Training | Precision (%) | Recall (%) | F1 (%) | PR-AUC (%) |
|---|---|---|---|---:|---:|---:|---:|
| HyperVul interaction classifier | No | No | No | 24.88 ± 1.87 | 62.00 ± 10.46 | 35.40 ± 3.46 | 31.41 ± 1.73 |
| Contract MIL | Yes | No | No | 39.60 ± 4.85 | 67.50 ± 8.40 | 49.79 ± 4.75 | 46.85 ± 3.55 |
| Contract MIL + attention pooling | Yes | No | No | 42.75 ± 5.10 | 65.00 ± 8.15 | 51.55 ± 4.60 | 49.20 ± 3.70 |
| Risk-vs-safety suppression | Yes | Yes | No | 48.90 ± 5.05 | 72.50 ± 7.60 | 58.32 ± 4.85 | 56.40 ± 3.50 |
| **HyperVul (Full)** | **Yes** | **Yes** | **Yes** | **51.80 ± 5.35** | **85.00 ± 7.50** | **64.34 ± 5.85** | **61.59 ± 3.43** |




