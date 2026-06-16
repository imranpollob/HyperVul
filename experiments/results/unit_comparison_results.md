# HyperVul — Controlled Prediction-Unit Comparison

> **Controlled experiment.** All variants trained on identical data
> (base 1381 + 100 OZ-train + 100 Aave-train negatives),
> identical fixed config (hidden_dim=256, dropout=0.3,
> lr=0.001), identical threshold rule (highest threshold with >=95% val recall),
> seed=42. The ONLY variable is which node types enter the hyperedge. "Ours" is
> re-trained and re-evaluated here, not copied from a previous iteration.

## 1. Interaction-Level Test Set (169 items: 44 pos)

| Model | Recall | Precision | F1 | F2 | PR-AUC | ROC-AUC | Cross-F1 | Intra-F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Function-only** | 90.91% | 40.40% | 55.94% | 72.73% | 59.39% | 84.93% | 44.44% | 65.00% |
| **{Function, State}** | 93.18% | 41.84% | 57.75% | 74.82% | 51.52% | 82.29% | 43.75% | 69.23% |
| **{Function, Callee}** | 95.45% | 43.30% | 59.57% | 76.92% | 69.27% | 87.98% | 45.45% | 72.00% |
| **Full {Function, State, Callee} (Ours)** | 93.18% | 47.67% | 63.08% | 78.24% | 63.81% | 86.71% | 52.63% | 71.23% |

## 2. Per-Vulnerability-Type Recall

| Model | Front-running / Tx Order (SWC-114) | Reentrancy (SWC-107) | Unchecked Call Return (SWC-104) |
| :--- | :---: | :---: | :---: |
| **Function-only** | 93.33% | 91.30% | 83.33% |
| **{Function, State}** | 100.00% | 86.96% | 100.00% |
| **{Function, Callee}** | 100.00% | 91.30% | 100.00% |
| **Full {Function, State, Callee} (Ours)** | 100.00% | 86.96% | 100.00% |

## 3. Tuned thresholds / val recall
- Function-only: threshold=0.1354, val_recall=97.30%, val_loss=0.6194
- {Function, State}: threshold=0.0995, val_recall=97.30%, val_loss=0.7292
- {Function, Callee}: threshold=0.1062, val_recall=97.30%, val_loss=0.5788
- Full {Function, State, Callee} (Ours): threshold=0.1573, val_recall=97.30%, val_loss=0.5573
