# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_full_seed46.pt`
> **Arm**: `full` (SCL=ON, Localization=ON) · **Seed**: `46`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.0355`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5837** | **0.0355** | **97.30%** | **13.98%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 30 | 47.62% | [35.78%, 59.73%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 357 | 84.20% | [80.42%, 87.36%] |
| **Bancor V3** | External (DeFi Application) | 209 | 112 | 53.59% | [46.82%, 60.22%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 167 | 59.86% | [54.01%, 65.44%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 41.51% |
| **Recall** | 100.00% |
| **F1-Score** | 58.67% |
| **F2-Score** | 78.01% |
| **PR-AUC** | 63.69% |
| **ROC-AUC** | 84.98% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 31.37% | 100.00% | 47.76% | 69.57% | 63.33% | 85.22% |
| **Intra-Contract** | 90 (28/62) | 50.91% | 100.00% | 67.47% | 83.83% | 63.31% | 84.91% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 100.00% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=46**, arm=**full** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.0355.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 58.67%, Precision 41.51%, Recall 100.00%, PR-AUC 63.69%, ROC-AUC 84.98%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 47.62% [35.78%, 59.73%]
  - MakerDAO DSS: 84.20% [80.42%, 87.36%]
  - Bancor V3: 53.59% [46.82%, 60.22%]
  - Liquity V1: 59.86% [54.01%, 65.44%]
- **Cross- vs intra-contract (test)**: cross F1 47.76% (recall 100.00%), intra F1 67.47% (recall 100.00%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
