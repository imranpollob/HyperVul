# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secfull_seed44.pt`
> **Arm**: `secfull` (SCL=OFF, Localization=OFF) · **Seed**: `44`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1915`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.6154** | **0.1915** | **97.30%** | **3.23%** |

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
| **OZ-Holdout** | Internal (Library) | 63 | 16 | 25.40% | [16.28%, 37.34%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 305 | 71.93% | [67.47%, 76.00%] |
| **Bancor V3** | External (DeFi Application) | 209 | 94 | 44.98% | [38.38%, 51.75%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 101 | 36.20% | [30.78%, 41.99%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 48.24% |
| **Recall** | 93.18% |
| **F1-Score** | 63.57% |
| **F2-Score** | 78.54% |
| **PR-AUC** | 69.45% |
| **ROC-AUC** | 89.15% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 38.46% | 93.75% | 54.55% | 72.82% | 64.95% | 86.01% |
| **Intra-Contract** | 90 (28/62) | 56.52% | 92.86% | 70.27% | 82.28% | 71.32% | 89.92% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 23 | 86.96% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=44**, arm=**secfull** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.1915.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 63.57%, Precision 48.24%, Recall 93.18%, PR-AUC 69.45%, ROC-AUC 89.15%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 25.40% [16.28%, 37.34%]
  - MakerDAO DSS: 71.93% [67.47%, 76.00%]
  - Bancor V3: 44.98% [38.38%, 51.75%]
  - Liquity V1: 36.20% [30.78%, 41.99%]
- **Cross- vs intra-contract (test)**: cross F1 54.55% (recall 93.75%), intra F1 70.27% (recall 92.86%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
