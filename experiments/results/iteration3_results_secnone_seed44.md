# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed44.pt`
> **Arm**: `secnone` (SCL=OFF, Localization=OFF) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1134`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5503** | **0.1134** | **97.30%** | **6.45%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 23 | 36.51% | [25.72%, 48.85%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 286 | 67.45% | [62.85%, 71.74%] |
| **Bancor V3** | External (DeFi Application) | 209 | 118 | 56.46% | [49.68%, 63.00%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 117 | 41.94% | [36.29%, 47.80%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 50.00% |
| **Recall** | 90.91% |
| **F1-Score** | 64.52% |
| **F2-Score** | 78.12% |
| **PR-AUC** | 68.98% |
| **ROC-AUC** | 88.22% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 36.84% | 87.50% | 51.85% | 68.63% | 66.30% | 85.52% |
| **Intra-Contract** | 90 (28/62) | 61.90% | 92.86% | 74.29% | 84.42% | 69.26% | 88.88% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 82.61% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=44**, arm=**secnone** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.1134.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 64.52%, Precision 50.00%, Recall 90.91%, PR-AUC 68.98%, ROC-AUC 88.22%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 36.51% [25.72%, 48.85%]
  - MakerDAO DSS: 67.45% [62.85%, 71.74%]
  - Bancor V3: 56.46% [49.68%, 63.00%]
  - Liquity V1: 41.94% [36.29%, 47.80%]
- **Cross- vs intra-contract (test)**: cross F1 51.85% (recall 87.50%), intra F1 74.29% (recall 92.86%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
