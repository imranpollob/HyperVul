# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secsec_seed44.pt`
> **Arm**: `secsec` (SCL=OFF, Localization=OFF) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.2314`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6233** | **0.2314** | **97.30%** | **2.15%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 20 | 31.75% | [21.59%, 44.00%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 254 | 59.91% | [55.17%, 64.46%] |
| **Bancor V3** | External (DeFi Application) | 209 | 101 | 48.33% | [41.64%, 55.07%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 98 | 35.13% | [29.76%, 40.89%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 51.85% |
| **Recall** | 95.45% |
| **F1-Score** | 67.20% |
| **F2-Score** | 81.71% |
| **PR-AUC** | 68.95% |
| **ROC-AUC** | 89.15% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 40.54% | 93.75% | 56.60% | 74.26% | 66.53% | 87.50% |
| **Intra-Contract** | 90 (28/62) | 61.36% | 96.43% | 75.00% | 86.54% | 68.32% | 89.00% |

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
> Single run: **seed=44**, arm=**secsec** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.2314.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 67.20%, Precision 51.85%, Recall 95.45%, PR-AUC 68.95%, ROC-AUC 89.15%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 31.75% [21.59%, 44.00%]
  - MakerDAO DSS: 59.91% [55.17%, 64.46%]
  - Bancor V3: 48.33% [41.64%, 55.07%]
  - Liquity V1: 35.13% [29.76%, 40.89%]
- **Cross- vs intra-contract (test)**: cross F1 56.60% (recall 93.75%), intra F1 75.00% (recall 96.43%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
