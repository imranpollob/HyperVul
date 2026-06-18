# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_full_seed43.pt`
> **Arm**: `full` (SCL=ON, Localization=ON) · **Seed**: `43`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1154`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6097** | **0.1154** | **97.30%** | **7.53%** |

---

## 2. Final Negative Training Set Composition
*   **Total Positives in Training**: 552 (Base Codebase Positives: 552)
*   **Total Negatives in Training**: 1029 (100% of negative class)
    *   *Codebase (Tier-A) Hard Negatives*: 829 (80.56%)
    *   *Clean Library (OpenZeppelin) Negatives*: 100 (9.72%)
    *   *Clean Application (Aave V3) Negatives*: 100 (9.72%)

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 26 | 41.27% | [29.96%, 53.58%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 268 | 63.21% | [58.52%, 67.66%] |
| **Bancor V3** | External (DeFi Application) | 209 | 89 | 42.58% | [36.07%, 49.36%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 126 | 45.16% | [39.43%, 51.03%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 46.43% |
| **Recall** | 88.64% |
| **F1-Score** | 60.94% |
| **F2-Score** | 75.00% |
| **PR-AUC** | 63.83% |
| **ROC-AUC** | 86.35% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 34.21% | 81.25% | 48.15% | 63.73% | 63.10% | 84.82% |
| **Intra-Contract** | 90 (28/62) | 56.52% | 92.86% | 70.27% | 82.28% | 60.43% | 85.94% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 82.61% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 83.33% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=43**, arm=**full** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.1154.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 60.94%, Precision 46.43%, Recall 88.64%, PR-AUC 63.83%, ROC-AUC 86.35%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 41.27% [29.96%, 53.58%]
  - MakerDAO DSS: 63.21% [58.52%, 67.66%]
  - Bancor V3: 42.58% [36.07%, 49.36%]
  - Liquity V1: 45.16% [39.43%, 51.03%]
- **Cross- vs intra-contract (test)**: cross F1 48.15% (recall 81.25%), intra F1 70.27% (recall 92.86%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
