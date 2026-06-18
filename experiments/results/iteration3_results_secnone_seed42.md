# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secnone_seed42.pt`
> **Arm**: `secnone` (SCL=OFF, Localization=OFF) · **Seed**: `42`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.1112`  
> **Validation Recall**: `97.30%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.5668** | **0.1112** | **97.30%** | **4.30%** |

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
| **MakerDAO DSS** | External (DeFi Application) | 424 | 309 | 72.88% | [68.45%, 76.89%] |
| **Bancor V3** | External (DeFi Application) | 209 | 99 | 47.37% | [40.71%, 54.12%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 116 | 41.58% | [35.95%, 47.44%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (169 items: 44 positives, 125 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 51.28% |
| **Recall** | 90.91% |
| **F1-Score** | 65.57% |
| **F2-Score** | 78.74% |
| **PR-AUC** | 63.12% |
| **ROC-AUC** | 85.25% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 40.00% | 87.50% | 54.90% | 70.71% | 62.52% | 84.92% |
| **Intra-Contract** | 90 (28/62) | 60.47% | 92.86% | 73.24% | 83.87% | 65.55% | 86.35% |

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
> Single run: **seed=42**, arm=**secnone** (SCL=OFF, Localization=OFF), K_app=100 (fixed), threshold=0.1112.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 65.57%, Precision 51.28%, Recall 90.91%, PR-AUC 63.12%, ROC-AUC 85.25%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 25.40% [16.28%, 37.34%]
  - MakerDAO DSS: 72.88% [68.45%, 76.89%]
  - Bancor V3: 47.37% [40.71%, 54.12%]
  - Liquity V1: 41.58% [35.95%, 47.44%]
- **Cross- vs intra-contract (test)**: cross F1 54.90% (recall 87.50%), intra F1 73.24% (recall 92.86%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
