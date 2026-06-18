# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed45.pt`
> **Arm**: `secnone` (SCL=OFF, Localization=OFF) · **Seed**: `45`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.0726`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6083** | **0.0726** | **97.30%** | **12.90%** |

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
| **MakerDAO DSS** | External (DeFi Application) | 424 | 358 | 84.43% | [80.68%, 87.57%] |
| **Bancor V3** | External (DeFi Application) | 209 | 127 | 60.77% | [54.01%, 67.13%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 177 | 63.44% | [57.64%, 68.87%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 46.67% |
| **Recall** | 95.45% |
| **F1-Score** | 62.69% |
| **F2-Score** | 78.95% |
| **PR-AUC** | 63.56% |
| **ROC-AUC** | 86.02% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 36.59% | 93.75% | 52.63% | 71.43% | 65.07% | 86.51% |
| **Intra-Contract** | 90 (28/62) | 55.10% | 96.43% | 70.13% | 83.85% | 64.62% | 85.54% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 91.30% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=45**, arm=**secnone** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.0726.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 62.69%, Precision 46.67%, Recall 95.45%, PR-AUC 63.56%, ROC-AUC 86.02%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 41.27% [29.96%, 53.58%]
  - MakerDAO DSS: 84.43% [80.68%, 87.57%]
  - Bancor V3: 60.77% [54.01%, 67.13%]
  - Liquity V1: 63.44% [57.64%, 68.87%]
- **Cross- vs intra-contract (test)**: cross F1 52.63% (recall 93.75%), intra F1 70.13% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
