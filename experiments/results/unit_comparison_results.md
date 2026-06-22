# HyperVul — Controlled Prediction-Unit Comparison

> **Controlled experiment.** All variants trained on identical data
> (base 1358 + 100 OZ-train + 100 Aave-train negatives),
> identical fixed config (hidden_dim=256, dropout=0.3,
> lr=0.001), identical threshold rule (highest threshold with >=95% val recall),
> seed=42. The ONLY variable is which node types enter the hyperedge. "Ours" is
> re-trained and re-evaluated here, not copied from a previous iteration.

## 1. Interaction-Level Test Set (176 items: 45 pos)

| Model | Recall | Precision | F1 | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Function-only** | 95.56% | 37.72% | 54.09% | 73.13% | 62.38% | 85.51% | 41.79% | 63.04% |
| **{Function, State}** | 95.56% | 45.26% | 61.43% | 78.18% | 62.23% | 84.83% | 46.67% | 72.50% |
| **{Function, Callee}** | 97.78% | 31.43% | 47.57% | 68.75% | 60.83% | 84.72% | 37.65% | 56.00% |
| **Full {Function, State, Callee} (Ours)** | 95.56% | 46.24% | 62.32% | 78.75% | 62.99% | 86.11% | 49.18% | 72.73% |

## 2. Per-Vulnerability-Type Recall

| Model | Front-running / Tx Order (SWC-114) | Reentrancy (SWC-107) | Unchecked Call Return (SWC-104) |
| :--- | :---: | :---: | :---: |
| **Function-only** | 100.00% | 95.83% | 83.33% |
| **{Function, State}** | 100.00% | 95.83% | 83.33% |
| **{Function, Callee}** | 100.00% | 95.83% | 100.00% |
| **Full {Function, State, Callee} (Ours)** | 100.00% | 91.67% | 100.00% |

## 3. Tuned thresholds / val recall
- Function-only: threshold=0.4505, val_recall=97.37%, val_loss=0.1237
- {Function, State}: threshold=0.4717, val_recall=97.37%, val_loss=0.1184
- {Function, Callee}: threshold=0.4286, val_recall=97.37%, val_loss=0.1207
- Full {Function, State, Callee} (Ours): threshold=0.4999, val_recall=97.37%, val_loss=0.1133
