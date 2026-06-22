# HyperVul — Iteration 3 Retrained Classifier Results

> **Model Checkpoint**: `model/iteration3_checkpoint_secfull_seed43.pt`
> **Arm**: `secfull` (SCL=ON, Localization=ON) · **Seed**: `43`
> **Clean Negative Training Count K_app**: `100` (fixed via --fix-k)
> **Chosen Decision Threshold**: `0.4776`  
> **Validation Recall**: `97.37%`

---

## 1. Clean Negative Ratio Sweep (Tuned on Validation Set Only)
These metrics show the validation performance across different ratios of clean negative Aave V3 contracts added to training (with a fixed $K_{oz}=100$ library negatives):

| K_app (Clean Negatives) | Validation Loss | Tuned Threshold | Validation Recall | Combined Val FPR |
| :--- | :--- | :--- | :--- | :--- |
| **100** | **0.1177** | **0.4776** | **97.37%** | **9.68%** |

---

## 2. Final Negative Training Set Composition
*   **Total Positives in Training**: 539 (Base Codebase Positives: 539)
*   **Total Negatives in Training**: 1019 (100% of negative class)
    *   *Codebase (Tier-A) Hard Negatives*: 819 (80.37%)
    *   *Clean Library (OpenZeppelin) Negatives*: 100 (9.81%)
    *   *Clean Application (Aave V3) Negatives*: 100 (9.81%)

---

## 3. Generalization on Disjoint Holdout Sets
These results represent the final, single-evaluation run on all mathematically isolated holdout sets. **FPRs are reported with 95% Wilson Score binomial confidence intervals**:

| Holdout Set | Type | Size | False Positives | FPR (Point Estimate) | 95% Wilson Confidence Interval |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OZ-Holdout** | Internal (Library) | 63 | 22 | 34.92% | [24.33%, 47.25%] |
| **MakerDAO DSS** | External (DeFi Application) | 424 | 337 | 79.48% | [75.38%, 83.05%] |
| **Bancor V3** | External (DeFi Application) | 209 | 95 | 45.45% | [38.85%, 52.23%] |
| **Liquity V1 (Fresh Probe)** | External (DeFi Application) | 279 | 137 | 49.10% | [43.29%, 54.94%] |

---

## 4. Overall Test Performance (at Tuned Decision Threshold)
These metrics are evaluated on the real, un-augmented test split (176 items: 45 positives, 131 negatives).

| Metric | Value |
| :--- | :--- |
| **Precision** | 40.00% |
| **Recall** | 97.78% |
| **F1-Score** | 56.77% |
| **F2-Score** | 75.86% |
| **PR-AUC** | 61.93% |
| **ROC-AUC** | 85.36% |

---

## 5. Subset Performance: Cross-Contract vs. Intra-Contract Test Hyperedges
We analyze the performance separately on cross-contract vs. intra-contract hyperedges to identify architectural gaps.

| Subset | Count (Pos/Neg) | Precision | Recall | F1-Score | F2-Score | PR-AUC | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cross-Contract** | 79 (16/63) | 30.00% | 93.75% | 45.45% | 65.79% | 64.50% | 82.14% |
| **Intra-Contract** | 97 (29/68) | 48.33% | 100.00% | 65.17% | 82.39% | 57.26% | 84.94% |

---

## 6. Per-Vulnerability-Type Recall on Test Set
> **[WARNING] INDICATIVE ONLY**: Positive sample counts are extremely small.

| Vulnerability Type | Test Positives | Recall |
| :--- | :--- | :--- |
| Reentrancy (SWC-107) | 24 | 95.83% |
| Front-running / Tx Order (SWC-114) | 15 | 100.00% |
| Unchecked Call Return (SWC-104) | 6 | 100.00% |
| Delegatecall (SWC-112) | 0 | Unevaluated |

---

## 7. Run Configuration & Measured Summary
> Single run: **seed=43**, arm=**secfull** (SCL=ON, Localization=ON), K_app=100 (fixed), threshold=0.4776.
> Numbers below are this single run only — **cross-arm comparison, multi-seed mean±σ, Wilson CIs and paired significance live in the aggregate report** (`experiments/aggregate_ablation.py`). Do not draw conclusions from a single seed.

- **Test (in-distribution)**: F1 56.77%, Precision 40.00%, Recall 97.78%, PR-AUC 61.93%, ROC-AUC 85.36%.
- **OOD holdout FPR (point [95% Wilson])**:
  - OZ-Holdout (library): 34.92% [24.33%, 47.25%]
  - MakerDAO DSS: 79.48% [75.38%, 83.05%]
  - Bancor V3: 45.45% [38.85%, 52.23%]
  - Liquity V1: 49.10% [43.29%, 54.94%]
- **Cross- vs intra-contract (test)**: cross F1 45.45% (recall 93.75%), intra F1 65.17% (recall 100.00%).
- **Caveat**: in-distribution `Aave-Val` FPR is optimistic (shares distribution with `Aave-Train`); the OZ/MakerDAO/Bancor/Liquity holdouts are the OOD generalization signal.
